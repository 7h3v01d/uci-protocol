"""
UCI Invocation  —  uci/core/invocation.py
==========================================
Patch 7: UCIInvocation as a first-class protocol object.

The spec (uci_invocation_execution_v0_1 §3-4) defines the canonical
invocation structure. Previously orchestrator.invoke() accepted loose
args. UCIInvocation is now the canonical request object.

The three protocol objects are now fully symmetric:
  UCIManifest   — identity (who am I, what can I do)
  UCIInvocation — request  (do this, for this caller, with this payload)
  UCIResponse   — answer   (here is what happened)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


INVOCATION_VERSION = "0.1"


@dataclass
class UCIInvocationCaller:
    """Identity of the entity initiating the invocation."""
    node_id:     str = ""
    instance_id: str = ""
    actor_type:  str = "orchestrator"   # orchestrator | operator | agent | service

    def to_dict(self) -> dict:
        return {
            "node_id":     self.node_id,
            "instance_id": self.instance_id,
            "actor_type":  self.actor_type,
        }


@dataclass
class UCIInvocationTarget:
    """Identifies the node, capability, and action being invoked."""
    node_id:       str = ""
    capability_id: str = ""
    action_id:     str = ""

    def to_dict(self) -> dict:
        return {
            "node_id":       self.node_id,
            "capability_id": self.capability_id,
            "action_id":     self.action_id,
        }


@dataclass
class UCIInvocationContext:
    """
    Surrounding runtime metadata for the invocation (spec §19).
    Provides governance and audit context without coupling to transport.
    """
    session_id:     str = ""
    operator_id:    str = ""
    risk_posture:   str = "normal"    # normal | elevated | restricted
    policy_profile: str = ""
    network_zone:   str = ""
    environment:    str = ""
    tags:           dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "session_id":     self.session_id,
            "operator_id":    self.operator_id,
            "risk_posture":   self.risk_posture,
            "policy_profile": self.policy_profile,
            "network_zone":   self.network_zone,
            "environment":    self.environment,
            "tags":           self.tags,
        }


@dataclass
class UCIInvocation:
    """
    Canonical UCI invocation object (spec §3-4).

    Represents a request to execute a declared action.
    An invocation MUST reference:
      - target node, capability, action
      - caller identity
      - input payload
      - execution context
      - governance metadata (correlation_id, operator_override)

    Usage:
        inv = UCIInvocation.create(
            caller_node_id = "niles",
            node_id        = "librarian_pro",
            capability_id  = "document_search",
            action_id      = "search_index",
            payload        = {"query": "UCI spec"},
        )
        response = orchestrator.invoke_with(inv)
    """
    uci_invocation_version: str = INVOCATION_VERSION
    invocation_id:    str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id:   str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:        str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    caller:           UCIInvocationCaller  = field(default_factory=UCIInvocationCaller)
    target:           UCIInvocationTarget  = field(default_factory=UCIInvocationTarget)
    payload:          dict[str, Any]       = field(default_factory=dict)
    context:          UCIInvocationContext = field(default_factory=UCIInvocationContext)

    # Governance hints
    operator_override: Optional[str] = None    # operator identity if pre-approved
    require_confirmation: bool       = False   # caller explicitly requesting confirmation

    # ── Factory ──────────────────────────────

    @classmethod
    def create(
        cls,
        node_id:          str,
        capability_id:    str,
        action_id:        str,
        payload:          Optional[dict[str, Any]] = None,
        caller_node_id:   str = "orchestrator",
        caller_instance:  str = "",
        correlation_id:   Optional[str] = None,
        operator_override: Optional[str] = None,
        session_id:       str = "",
        risk_posture:     str = "normal",
    ) -> "UCIInvocation":
        return cls(
            correlation_id    = correlation_id or str(uuid.uuid4()),
            caller            = UCIInvocationCaller(
                node_id=caller_node_id,
                instance_id=caller_instance,
            ),
            target            = UCIInvocationTarget(
                node_id=node_id,
                capability_id=capability_id,
                action_id=action_id,
            ),
            payload           = payload or {},
            context           = UCIInvocationContext(
                session_id=session_id,
                risk_posture=risk_posture,
            ),
            operator_override = operator_override,
        )

    # ── Accessors ────────────────────────────

    @property
    def node_id(self) -> str:
        return self.target.node_id

    @property
    def capability_id(self) -> str:
        return self.target.capability_id

    @property
    def action_id(self) -> str:
        return self.target.action_id

    # ── Serialisation ────────────────────────

    def to_dict(self) -> dict:
        return {
            "uci_invocation_version": self.uci_invocation_version,
            "invocation_id":          self.invocation_id,
            "correlation_id":         self.correlation_id,
            "timestamp":              self.timestamp,
            "caller":                 self.caller.to_dict(),
            "target":                 self.target.to_dict(),
            "payload":                self.payload,
            "context":                self.context.to_dict(),
            "operator_override":      self.operator_override,
            "require_confirmation":   self.require_confirmation,
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> "UCIInvocation":
        raw_caller  = data.get("caller", {})
        raw_target  = data.get("target", {})
        raw_context = data.get("context", {})
        return cls(
            uci_invocation_version = data.get("uci_invocation_version", INVOCATION_VERSION),
            invocation_id          = data.get("invocation_id", str(uuid.uuid4())),
            correlation_id         = data.get("correlation_id", str(uuid.uuid4())),
            timestamp              = data.get("timestamp", ""),
            caller                 = UCIInvocationCaller(
                node_id     = raw_caller.get("node_id", ""),
                instance_id = raw_caller.get("instance_id", ""),
                actor_type  = raw_caller.get("actor_type", "orchestrator"),
            ),
            target                 = UCIInvocationTarget(
                node_id       = raw_target.get("node_id", ""),
                capability_id = raw_target.get("capability_id", ""),
                action_id     = raw_target.get("action_id", ""),
            ),
            payload                = data.get("payload", {}),
            context                = UCIInvocationContext(
                session_id     = raw_context.get("session_id", ""),
                operator_id    = raw_context.get("operator_id", ""),
                risk_posture   = raw_context.get("risk_posture", "normal"),
                policy_profile = raw_context.get("policy_profile", ""),
                network_zone   = raw_context.get("network_zone", ""),
                environment    = raw_context.get("environment", ""),
                tags           = raw_context.get("tags", {}),
            ),
            operator_override      = data.get("operator_override"),
            require_confirmation   = data.get("require_confirmation", False),
        )
