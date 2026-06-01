"""
UCI Handshake Protocol
Canonical lifecycle: discover → retrieve → validate → compatibility →
                     governance → trust → mount → ready

Fail-closed at every stage. No stage may be skipped.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from .manifest import UCIManifest
from .trust import TrustRecord, TrustState
from .governance import PolicyEngine, GovernanceOutcome
from .registry import UCIRegistry
from .audit import AuditLog, AuditEvent
from .errors import UCIHandshakeError, UCIManifestError, UCIValidationError


class HandshakeStage(str, Enum):
    PENDING              = "pending"
    DISCOVERED           = "discovered"
    MANIFEST_RETRIEVED   = "manifest_retrieved"
    MANIFEST_VALIDATED   = "manifest_validated"
    COMPATIBILITY_CHECKED= "compatibility_checked"
    GOVERNANCE_EVALUATED = "governance_evaluated"
    TRUST_ASSIGNED       = "trust_assigned"
    CAPABILITIES_MOUNTED = "capabilities_mounted"
    READY                = "ready"
    FAILED               = "failed"
    REJECTED             = "rejected"


ORCHESTRATOR_SUPPORTED_VERSIONS = ["0.1"]


@dataclass
class HandshakeResult:
    success: bool
    node_id: str
    stage_reached: HandshakeStage
    trust_state: str = ""
    mounted_capabilities: list[str] = field(default_factory=list)
    failure_reason: str = ""
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.success:
            caps = ", ".join(self.mounted_capabilities) or "none"
            return (
                f"[OK] Handshake complete for '{self.node_id}' — "
                f"trust={self.trust_state}, capabilities=[{caps}]"
            )
        return (
            f"[FAIL] Handshake failed for '{self.node_id}' "
            f"at stage '{self.stage_reached.value}': {self.failure_reason}"
        )


@dataclass
class HandshakeEngine:
    """
    Executes the full UCI handshake lifecycle for a single node.

    Usage:
        engine = HandshakeEngine(policy=policy_engine, registry=registry, audit=audit_log)
        result = engine.run(node_id="my_service", manifest_data={...})
    """
    policy: PolicyEngine
    registry: UCIRegistry
    audit: AuditLog
    strict_compatibility: bool = True     # reject unknown manifest versions

    def run(
        self,
        node_id: str,
        manifest_data: dict[str, Any],
        initial_trust: TrustState = TrustState.UNKNOWN,
        pre_trusted: bool = False,        # operator already trusts this node
    ) -> HandshakeResult:
        """
        Execute the full handshake. Returns HandshakeResult regardless of outcome.
        Never raises — all failures are captured in the result.
        """
        stage = HandshakeStage.PENDING
        trust = TrustRecord(node_id=node_id, state=initial_trust)
        warnings: list[str] = []

        def _fail(reason: str, stage_reached=None) -> HandshakeResult:
            """Emit handshake_failed and return a failure result."""
            self.audit.append(AuditEvent.HANDSHAKE_FAILED, node_id,
                              actor="handshake_engine", outcome="deny",
                              stage=(stage_reached or stage).value, reason=reason)
            return HandshakeResult(
                success=False, node_id=node_id,
                stage_reached=stage_reached or stage,
                failure_reason=reason,
                warnings=warnings,
            )

        try:
            # ── Stage 1: Discovered ─────────────────────
            stage = HandshakeStage.DISCOVERED
            trust.transition(TrustState.DISCOVERED, granted_by="handshake_engine",
                             reason="Node endpoint reached")
            self.audit.append(AuditEvent.NODE_DISCOVERED, node_id,
                              actor="handshake_engine", outcome="")

            # ── Stage 2: Manifest retrieved ─────────────
            stage = HandshakeStage.MANIFEST_RETRIEVED
            self.audit.append(AuditEvent.MANIFEST_RETRIEVED, node_id,
                              actor="handshake_engine", outcome="")

            # ── Stage 3: Manifest validated ─────────────
            stage = HandshakeStage.MANIFEST_VALIDATED
            try:
                manifest = UCIManifest.from_dict(manifest_data)
                manifest.validate()
            except (UCIManifestError, UCIValidationError) as exc:
                self.audit.append(AuditEvent.MANIFEST_VALIDATION_FAILED, node_id,
                                  actor="handshake_engine", outcome="deny",
                                  reason=str(exc))
                return _fail(f"Manifest validation failed: {exc}")

            self.audit.append(AuditEvent.MANIFEST_VALIDATION_PASSED, node_id,
                              actor="handshake_engine", outcome="",
                              capabilities=manifest.capability_ids())

            # ── Stage 4: Compatibility ───────────────────
            stage = HandshakeStage.COMPATIBILITY_CHECKED
            compatible = manifest.is_compatible_with(ORCHESTRATOR_SUPPORTED_VERSIONS)
            if not compatible:
                self.audit.append(AuditEvent.COMPATIBILITY_REJECTED, node_id,
                                  actor="handshake_engine", outcome="deny",
                                  manifest_version=manifest.uci_manifest_version)
                if self.strict_compatibility:
                    return _fail(
                        f"Manifest version '{manifest.uci_manifest_version}' "
                        f"not in supported {ORCHESTRATOR_SUPPORTED_VERSIONS}."
                    )
                warnings.append(
                    f"Manifest version '{manifest.uci_manifest_version}' "
                    f"may have limited support."
                )

            self.audit.append(AuditEvent.COMPATIBILITY_ACCEPTED, node_id,
                              actor="handshake_engine", outcome="",
                              manifest_version=manifest.uci_manifest_version)

            # ── Stage 5: Trust elevation to verified ────
            trust.transition(TrustState.VERIFIED, granted_by="handshake_engine",
                             reason="Manifest validated and compatible")

            # ── Stage 6: Governance evaluation ──────────
            stage = HandshakeStage.GOVERNANCE_EVALUATED
            gov_decision = self.policy.evaluate_manifest(manifest, trust)
            self.audit.append(AuditEvent.POLICY_EVALUATED, node_id,
                              actor="policy_engine", outcome=gov_decision.outcome,
                              reason=gov_decision.reason)

            if gov_decision.outcome == GovernanceOutcome.DENY:
                return _fail(f"Governance denied: {gov_decision.reason}")

            # ── Stage 7: Trust assignment ────────────────
            stage = HandshakeStage.TRUST_ASSIGNED
            if pre_trusted or gov_decision.outcome == GovernanceOutcome.ALLOW:
                new_trust = TrustState.TRUSTED
            else:
                new_trust = TrustState.RESTRICTED

            trust.transition(new_trust, granted_by="policy_engine",
                             reason=gov_decision.reason)
            self.audit.append(AuditEvent.TRUST_ASSIGNED, node_id,
                              actor="policy_engine", outcome="",
                              trust_state=new_trust.value)

            # ── Stage 8: Mount capabilities ──────────────
            stage = HandshakeStage.CAPABILITIES_MOUNTED
            mounted: list[str] = []

            # Register (or update) in registry
            try:
                entry = self.registry.register(manifest, trust)
            except Exception:
                entry = self.registry.update(manifest, trust)

            for cap in manifest.capabilities:
                # In restricted trust, only mount capabilities without high-risk actions
                if new_trust == TrustState.RESTRICTED:
                    high_risk = any(
                        a.risk.level in {"high", "critical"}
                        for a in cap.actions
                    )
                    if high_risk:
                        self.audit.append(AuditEvent.CAPABILITY_REVOKED, node_id,
                                          actor="handshake_engine", outcome="deny",
                                          capability_id=cap.capability_id,
                                          reason="High-risk capability not mounted under restricted trust")
                        warnings.append(
                            f"Capability '{cap.capability_id}' not mounted — "
                            f"contains high-risk actions and node is restricted."
                        )
                        continue

                self.registry.mount_capability(node_id, cap.capability_id)
                mounted.append(cap.capability_id)
                self.audit.append(AuditEvent.CAPABILITY_MOUNTED, node_id,
                                  actor="handshake_engine", outcome="",
                                  capability_id=cap.capability_id)

            # ── Stage 9: Ready ───────────────────────────
            stage = HandshakeStage.READY
            self.audit.append(AuditEvent.NODE_READY, node_id,
                              actor="handshake_engine", outcome="",
                              mounted_capabilities=mounted,
                              trust_state=new_trust.value)

            return HandshakeResult(
                success              = True,
                node_id              = node_id,
                stage_reached        = HandshakeStage.READY,
                trust_state          = new_trust.value,
                mounted_capabilities = mounted,
                warnings             = warnings,
            )

        except Exception as exc:
            # Unexpected failure — fail closed
            self.audit.append(AuditEvent.HANDSHAKE_FAILED, node_id,
                              actor="handshake_engine", outcome="deny",
                              stage=stage.value, error=str(exc))
            return HandshakeResult(
                success       = False,
                node_id       = node_id,
                stage_reached = HandshakeStage.FAILED,
                failure_reason= f"Unexpected failure at stage '{stage.value}': {exc}",
                warnings      = warnings,
            )
