"""
UCI SDK — Base Classes
UCIProvider: any node that exposes capabilities via a UCI manifest.
UCIOrchestrator: discovers providers and invokes their capabilities.

v0.1 — invoke() now returns UCIResponse envelopes, not raw dicts.
       Raw exceptions are no longer raised — all outcomes are envelopes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from ..core.manifest import UCIManifest
from ..core.governance import PolicyEngine, GovernanceOutcome
from ..core.handshake import HandshakeEngine, HandshakeResult
from ..core.registry import UCIRegistry
from ..core.audit import AuditLog, AuditEvent
from ..core.trust import TrustRecord, TrustState
from ..core.errors import UCIInvocationError, UCIGovernanceError
from ..core.response import UCIResponse, UCIResponseError, ResponseState, UCIErrorCode
from ..core.invocation import UCIInvocation


# ─────────────────────────────────────────────
# Provider base
# ─────────────────────────────────────────────

class UCIProvider(ABC):
    """
    Base class for any UCI-compatible service node.
    Subclasses implement build_manifest() and register action handlers.
    """

    def __init__(self) -> None:
        self._action_handlers: dict[str, dict[str, Callable]] = {}

    @abstractmethod
    def build_manifest(self) -> UCIManifest:
        """Return this provider's fully populated UCIManifest."""
        ...

    def manifest_dict(self) -> dict[str, Any]:
        return self.build_manifest().to_dict()

    def register_action(
        self,
        capability_id: str,
        action_id: str,
        handler: Callable[..., Any],
    ) -> None:
        if capability_id not in self._action_handlers:
            self._action_handlers[capability_id] = {}
        self._action_handlers[capability_id][action_id] = handler

    def invoke(
        self,
        capability_id: str,
        action_id: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> Any:
        cap_handlers = self._action_handlers.get(capability_id)
        if not cap_handlers:
            raise UCIInvocationError(
                f"No handlers registered for capability '{capability_id}'.",
                action_id=action_id,
                error_code="capability_not_found",
            )
        handler = cap_handlers.get(action_id)
        if not handler:
            raise UCIInvocationError(
                f"No handler registered for action '{capability_id}/{action_id}'.",
                action_id=action_id,
                error_code="action_not_found",
            )
        return handler(**(payload or {}))


# ─────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────

@dataclass
class UCIOrchestrator:
    """
    Discovers UCI providers, runs the handshake, and invokes capabilities
    through the governance layer.

    invoke() always returns a UCIResponse — never raises.
    Use response.assert_success() if you want the raw output or an exception.
    """
    policy: PolicyEngine
    registry: UCIRegistry
    audit: AuditLog
    name: str = "orchestrator"

    def __post_init__(self) -> None:
        self._providers: dict[str, UCIProvider] = {}
        self._handshake_engine = HandshakeEngine(
            policy   = self.policy,
            registry = self.registry,
            audit    = self.audit,
        )

    def connect(
        self,
        provider: UCIProvider,
        pre_trusted: bool = False,
    ) -> HandshakeResult:
        """
        Register a provider and run the full UCI handshake.
        Returns HandshakeResult — caller should check result.success.
        """
        manifest_data = provider.manifest_dict()
        node_id = manifest_data.get("node", {}).get("node_id", "unknown")

        result = self._handshake_engine.run(
            node_id       = node_id,
            manifest_data = manifest_data,
            pre_trusted   = pre_trusted,
        )

        if result.success:
            self._providers[node_id] = provider

        return result

    def invoke(
        self,
        node_id: str,
        capability_id: str,
        action_id: str,
        payload: Optional[dict[str, Any]] = None,
        operator_override: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> UCIResponse:
        """
        Governance-gated capability invocation.
        Always returns a UCIResponse — never raises.

        Check response.success to determine outcome.
        Call response.assert_success() to get output or raise on failure.
        """
        correlation_id = correlation_id or None

        # ── Registry lookup ──────────────────────────────
        try:
            entry = self.registry.require(node_id)
        except Exception as exc:
            return UCIResponse.from_exception(
                exc,
                node_id       = node_id,
                capability_id = capability_id,
                action_id     = action_id,
                code          = "NODE_NOT_FOUND",
                correlation_id= correlation_id,
            )

        instance_id = entry.manifest.node.instance_id

        # ── Governance check ─────────────────────────────
        try:
            decision = self.policy.evaluate_action(
                manifest      = entry.manifest,
                capability_id = capability_id,
                action_id     = action_id,
                trust         = entry.trust,
            )
        except Exception as exc:
            return UCIResponse.from_exception(
                exc,
                node_id       = node_id,
                instance_id   = instance_id,
                capability_id = capability_id,
                action_id     = action_id,
                code          = "GOVERNANCE_ERROR",
                correlation_id= correlation_id,
            )

        # ── Deferred — awaiting operator ─────────────────
        if decision.outcome == GovernanceOutcome.DEFER:
            if operator_override:
                decision = self.policy.operator_approve(
                    decision, operator_id=operator_override
                )
            else:
                return UCIResponse.deferred_response(
                    node_id       = node_id,
                    instance_id   = instance_id,
                    capability_id = capability_id,
                    action_id     = action_id,
                    trust_state   = entry.trust.state.value,
                    reason        = decision.reason,
                    correlation_id= correlation_id,
                )

        # ── Hard deny ────────────────────────────────────
        if not decision.is_permitted():
            return UCIResponse.failure_response(
                error          = UCIResponseError(
                    code    = "GOVERNANCE_DENIED",
                    message = decision.reason,
                    detail  = {"governance_outcome": decision.outcome},
                ),
                node_id        = node_id,
                instance_id    = instance_id,
                capability_id  = capability_id,
                action_id      = action_id,
                trust_state    = entry.trust.state.value,
                governance_outcome = decision.outcome,
                correlation_id = correlation_id,
            )

        # ── Provider lookup ──────────────────────────────
        provider = self._providers.get(node_id)
        if not provider:
            return UCIResponse.failure_response(
                error         = UCIResponseError(
                    code    = "PROVIDER_NOT_CONNECTED",
                    message = f"Provider '{node_id}' not connected to orchestrator.",
                ),
                node_id       = node_id,
                instance_id   = instance_id,
                capability_id = capability_id,
                action_id     = action_id,
                correlation_id= correlation_id,
            )

        # ── Execute ──────────────────────────────────────
        self.audit.append(
            AuditEvent.INVOCATION_REQUESTED, node_id,
            actor=self.name, outcome="",
            capability_id=capability_id, action_id=action_id,
        )

        try:
            raw_output = provider.invoke(capability_id, action_id, payload)

            self.audit.append(
                AuditEvent.INVOCATION_COMPLETED, node_id,
                actor=self.name, outcome="success",
                capability_id=capability_id, action_id=action_id,
            )

            return UCIResponse.success_response(
                output             = raw_output,
                node_id            = node_id,
                instance_id        = instance_id,
                capability_id      = capability_id,
                action_id          = action_id,
                trust_state        = entry.trust.state.value,
                governance_outcome = decision.outcome,
                restrictions       = decision.restrictions,
                operator_id        = operator_override,
                correlation_id     = correlation_id,
                actor              = self.name,
            )

        except Exception as exc:
            self.audit.append(
                AuditEvent.INVOCATION_FAILED, node_id,
                actor=self.name, outcome="error",
                capability_id=capability_id, action_id=action_id,
                error=str(exc),
            )
            return UCIResponse.from_exception(
                exc,
                node_id       = node_id,
                capability_id = capability_id,
                action_id     = action_id,
                code          = "INVOCATION_RUNTIME_ERROR",
                correlation_id= correlation_id,
            )

    def invoke_with(self, invocation: UCIInvocation) -> UCIResponse:
        """
        Governance-gated invocation using a UCIInvocation object.
        This is the canonical path per the spec.
        invoke() remains available as a convenience wrapper.
        """
        return self.invoke(
            node_id           = invocation.target.node_id,
            capability_id     = invocation.target.capability_id,
            action_id         = invocation.target.action_id,
            payload           = invocation.payload or {},
            operator_override = invocation.operator_override,
            correlation_id    = invocation.correlation_id,
        )

    def connected_nodes(self) -> list[str]:
        return list(self._providers.keys())

    def ready_nodes(self) -> list[str]:
        return [e.node_id for e in self.registry.ready_nodes()]
