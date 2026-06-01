"""
UCI Governance Model
Policy engine that evaluates invocations and produces governance outcomes.

Outcome ladder:
  allow → allow_with_restrictions → defer → deny

The engine is intentionally stateless and deterministic — same inputs,
same output, every time. Context (trust state, permissions, risk) is
passed in explicitly.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any
from .trust import TrustState, TrustRecord, EXECUTABLE_STATES
from .manifest import UCIAction, UCIManifest
from .audit import AuditLog, AuditEvent
from .errors import UCIGovernanceError


# ─────────────────────────────────────────────
# Outcome
# ─────────────────────────────────────────────

class GovernanceOutcome:
    ALLOW               = "allow"
    ALLOW_RESTRICTED    = "allow_with_restrictions"
    DEFER               = "defer"
    DENY                = "deny"


@dataclass
class PolicyDecision:
    outcome: str                              # GovernanceOutcome constant
    node_id: str = ""
    capability_id: str = ""
    action_id: str = ""
    reason: str = ""
    restrictions: list[str] = field(default_factory=list)
    requires_confirmation: bool = False
    evaluated_by: str = "policy_engine"

    def is_permitted(self) -> bool:
        return self.outcome in {GovernanceOutcome.ALLOW, GovernanceOutcome.ALLOW_RESTRICTED}

    def __str__(self) -> str:
        tag = f"[{self.outcome.upper()}]"
        r = f" — {self.reason}" if self.reason else ""
        return f"{tag} {self.node_id}/{self.capability_id}/{self.action_id}{r}"


# ─────────────────────────────────────────────
# Policy Engine
# ─────────────────────────────────────────────

RISK_CONFIRMATION_THRESHOLD = {"high", "critical"}

# Permissions the orchestrator holds by default in the test rig
DEFAULT_ORCHESTRATOR_PERMISSIONS: frozenset[str] = frozenset({
    "documents.read",
    "system.health",
    "search.query",
    "voice.tts",
    "voice.stt",
})


@dataclass
class PolicyEngine:
    """
    Evaluates whether a node/action invocation should be permitted.

    In the test rig the engine uses simple rule-based logic.
    A production implementation would plug in an external policy store.
    """
    orchestrator_permissions: frozenset[str] = field(
        default_factory=lambda: DEFAULT_ORCHESTRATOR_PERMISSIONS
    )
    audit: Optional[AuditLog] = None
    require_operator_for_high_risk: bool = True
    strict_mode: bool = True          # if True, unknown trust → deny; False → defer

    # ── Manifest-level governance check ─────────────

    def evaluate_manifest(
        self,
        manifest: UCIManifest,
        trust: TrustRecord,
    ) -> PolicyDecision:
        """
        Evaluate whether a node's manifest is acceptable for mounting.
        Called during handshake after manifest validation.
        """
        node_id = manifest.node.node_id

        # Revoked nodes are never permitted
        if trust.state == TrustState.REVOKED:
            return self._deny(node_id, "", "", "Node is revoked.")

        # Suspended nodes cannot proceed
        if trust.state == TrustState.SUSPENDED:
            return self._deny(node_id, "", "", "Node is suspended.")

        # Unknown nodes → deny (strict) or defer
        if trust.state == TrustState.UNKNOWN:
            if self.strict_mode:
                return self._deny(node_id, "", "", "Node trust state is unknown.")
            return self._defer(node_id, "", "", "Node trust state is unknown — awaiting operator.")

        # Governance meta: if node requires operator authority, flag it
        if manifest.governance.operator_authority_required:
            return PolicyDecision(
                outcome     = GovernanceOutcome.ALLOW_RESTRICTED,
                node_id     = node_id,
                reason      = "Operator authority required — capabilities mounted with restrictions.",
                restrictions= ["operator_confirmation_required_for_high_risk_actions"],
                evaluated_by= "policy_engine",
            )

        return self._allow(node_id, "", "", "Manifest governance requirements satisfied.")

    # ── Action invocation check ──────────────────────

    def evaluate_action(
        self,
        manifest: UCIManifest,
        capability_id: str,
        action_id: str,
        trust: TrustRecord,
        caller_permissions: Optional[frozenset[str]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> PolicyDecision:
        """
        Full governance evaluation for a specific action invocation.
        Returns a PolicyDecision — caller decides whether to proceed.
        """
        node_id = manifest.node.node_id
        caller_perms = caller_permissions or self.orchestrator_permissions

        # ① Trust check
        if trust.state not in EXECUTABLE_STATES:
            decision = self._deny(
                node_id, capability_id, action_id,
                f"Trust state '{trust.state.value}' does not permit execution.",
            )
            self._audit(AuditEvent.TRUST_REJECTED, node_id, "deny",
                        capability_id=capability_id, action_id=action_id,
                        trust_state=trust.state.value)
            return decision

        # ② Capability existence check
        cap = manifest.get_capability(capability_id)
        if cap is None:
            return self._deny(node_id, capability_id, action_id,
                              f"Capability '{capability_id}' not found in manifest.")

        # ③ Action existence check
        action = cap.get_action(action_id)
        if action is None:
            return self._deny(node_id, capability_id, action_id,
                              f"Action '{action_id}' not found in capability '{capability_id}'.")

        # ④ Permission check
        missing = set(action.permissions.required_permissions) - caller_perms
        if missing:
            decision = self._deny(
                node_id, capability_id, action_id,
                f"Missing required permissions: {missing}.",
            )
            self._audit(AuditEvent.PERMISSION_DENIED, node_id, "deny",
                        capability_id=capability_id, action_id=action_id,
                        missing_permissions=list(missing))
            return decision

        # ⑤ Trust minimum check
        min_trust = action.permissions.minimum_trust_state
        trust_order = [
            TrustState.UNKNOWN, TrustState.DISCOVERED, TrustState.VERIFIED,
            TrustState.TRUSTED, TrustState.RESTRICTED,
        ]
        try:
            required_idx = trust_order.index(TrustState(min_trust))
            current_idx  = trust_order.index(trust.state)
            if current_idx < required_idx:
                return self._deny(
                    node_id, capability_id, action_id,
                    f"Trust '{trust.state.value}' below required '{min_trust}'.",
                )
        except ValueError:
            pass  # non-standard trust state in manifest — allow policy to handle

        # ⑥ Risk evaluation
        risk_level = action.risk.level
        requires_confirmation = (
            action.execution.requires_confirmation
            or action.permissions.operator_confirmation in {"required", "required_with_reason", "multi_party_required"}
            or (self.require_operator_for_high_risk and risk_level in RISK_CONFIRMATION_THRESHOLD)
        )

        if requires_confirmation:
            self._audit(AuditEvent.CONFIRMATION_REQUESTED, node_id, "defer",
                        capability_id=capability_id, action_id=action_id,
                        risk_level=risk_level)
            return PolicyDecision(
                outcome               = GovernanceOutcome.DEFER,
                node_id               = node_id,
                capability_id         = capability_id,
                action_id             = action_id,
                reason                = f"Risk level '{risk_level}' requires operator confirmation.",
                requires_confirmation = True,
            )

        # ⑦ Restricted trust — allow with restrictions
        if trust.state == TrustState.RESTRICTED:
            self._audit(AuditEvent.EXECUTION_RESTRICTED, node_id, GovernanceOutcome.ALLOW_RESTRICTED,
                        capability_id=capability_id, action_id=action_id)
            return PolicyDecision(
                outcome       = GovernanceOutcome.ALLOW_RESTRICTED,
                node_id       = node_id,
                capability_id = capability_id,
                action_id     = action_id,
                reason        = "Node is restricted — execution permitted with limitations.",
                restrictions  = ["rate_limited", "no_side_effects_permitted"],
            )

        # ⑧ All checks passed — allow
        self._audit(AuditEvent.EXECUTION_ALLOWED, node_id, GovernanceOutcome.ALLOW,
                    capability_id=capability_id, action_id=action_id, risk_level=risk_level)
        return self._allow(node_id, capability_id, action_id,
                           f"All governance checks passed.")

    # ── Operator override ────────────────────────────

    def operator_approve(
        self,
        decision: PolicyDecision,
        operator_id: str = "operator",
    ) -> PolicyDecision:
        """Operator explicitly approves a deferred decision."""
        if decision.outcome != GovernanceOutcome.DEFER:
            raise UCIGovernanceError(
                "operator_approve called on a non-deferred decision.",
                outcome=decision.outcome,
            )
        self._audit(
            AuditEvent.CONFIRMATION_APPROVED, decision.node_id, GovernanceOutcome.ALLOW,
            capability_id=decision.capability_id, action_id=decision.action_id,
            operator=operator_id,
        )
        return PolicyDecision(
            outcome       = GovernanceOutcome.ALLOW,
            node_id       = decision.node_id,
            capability_id = decision.capability_id,
            action_id     = decision.action_id,
            reason        = f"Approved by operator '{operator_id}'.",
            evaluated_by  = operator_id,
        )

    def operator_deny(
        self,
        decision: PolicyDecision,
        operator_id: str = "operator",
        reason: str = "",
    ) -> PolicyDecision:
        """Operator explicitly denies a deferred decision."""
        self._audit(
            AuditEvent.CONFIRMATION_DENIED, decision.node_id, GovernanceOutcome.DENY,
            capability_id=decision.capability_id, action_id=decision.action_id,
            operator=operator_id, reason=reason,
        )
        return PolicyDecision(
            outcome       = GovernanceOutcome.DENY,
            node_id       = decision.node_id,
            capability_id = decision.capability_id,
            action_id     = decision.action_id,
            reason        = reason or f"Denied by operator '{operator_id}'.",
            evaluated_by  = operator_id,
        )

    # ── Helpers ──────────────────────────────────────

    def _allow(self, node_id, cap_id, act_id, reason) -> PolicyDecision:
        return PolicyDecision(
            outcome=GovernanceOutcome.ALLOW, node_id=node_id,
            capability_id=cap_id, action_id=act_id, reason=reason,
        )

    def _deny(self, node_id, cap_id, act_id, reason) -> PolicyDecision:
        return PolicyDecision(
            outcome=GovernanceOutcome.DENY, node_id=node_id,
            capability_id=cap_id, action_id=act_id, reason=reason,
        )

    def _defer(self, node_id, cap_id, act_id, reason) -> PolicyDecision:
        return PolicyDecision(
            outcome=GovernanceOutcome.DEFER, node_id=node_id,
            capability_id=cap_id, action_id=act_id, reason=reason,
            requires_confirmation=True,
        )

    def _audit(self, event_type: str, node_id: str, outcome: str, **detail: Any) -> None:
        if self.audit:
            self.audit.append(event_type, node_id, actor="policy_engine",
                              outcome=outcome, **detail)
