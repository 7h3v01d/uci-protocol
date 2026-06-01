"""
UCI Trust Model
Canonical trust states and the rules governing transitions between them.

State ladder (ascending trust):
  unknown → discovered → verified → trusted
                                  ↘ restricted

Lateral / terminal:
  any → suspended   (reversible)
  any → revoked     (permanent)
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from .errors import UCITrustError


class TrustState(str, Enum):
    UNKNOWN     = "unknown"      # No validation performed
    DISCOVERED  = "discovered"   # Node visible, manifest not yet retrieved
    VERIFIED    = "verified"     # Manifest retrieved and structurally valid
    TRUSTED     = "trusted"      # Policy-approved for standard operation
    RESTRICTED  = "restricted"   # Limited operation — explicit capability subset
    SUSPENDED   = "suspended"    # Temporarily disabled — MAY be restored
    REVOKED     = "revoked"      # Permanently denied — MUST NOT be restored automatically


# Legal forward transitions (from → set of allowed next states)
_ALLOWED_TRANSITIONS: dict[TrustState, set[TrustState]] = {
    TrustState.UNKNOWN:     {TrustState.DISCOVERED, TrustState.REVOKED},
    TrustState.DISCOVERED:  {TrustState.VERIFIED, TrustState.SUSPENDED, TrustState.REVOKED},
    TrustState.VERIFIED:    {TrustState.TRUSTED, TrustState.RESTRICTED, TrustState.SUSPENDED, TrustState.REVOKED},
    TrustState.TRUSTED:     {TrustState.RESTRICTED, TrustState.SUSPENDED, TrustState.REVOKED},
    TrustState.RESTRICTED:  {TrustState.TRUSTED, TrustState.SUSPENDED, TrustState.REVOKED},
    TrustState.SUSPENDED:   {TrustState.VERIFIED, TrustState.TRUSTED, TrustState.RESTRICTED, TrustState.REVOKED},
    TrustState.REVOKED:     set(),  # Terminal — no transitions out
}

# States that permit action execution
EXECUTABLE_STATES: frozenset[TrustState] = frozenset({
    TrustState.TRUSTED,
    TrustState.RESTRICTED,
})

# States that may expose manifests
MANIFEST_VISIBLE_STATES: frozenset[TrustState] = frozenset({
    TrustState.DISCOVERED,
    TrustState.VERIFIED,
    TrustState.TRUSTED,
    TrustState.RESTRICTED,
})


@dataclass
class TrustRecord:
    """Tracks the current trust state of a node and its transition history."""
    node_id: str
    state: TrustState = TrustState.UNKNOWN
    history: list[dict] = field(default_factory=list)
    granted_by: Optional[str] = None       # operator id or "policy_engine"
    notes: str = ""

    def transition(
        self,
        new_state: TrustState,
        granted_by: str = "policy_engine",
        reason: str = "",
    ) -> "TrustRecord":
        """
        Transition to a new trust state.
        Raises UCITrustError if the transition is not permitted.
        Returns self for chaining.
        """
        allowed = _ALLOWED_TRANSITIONS.get(self.state, set())

        if new_state not in allowed:
            raise UCITrustError(
                f"Trust transition {self.state.value!r} → {new_state.value!r} "
                f"is not permitted for node '{self.node_id}'.",
                current_state=self.state.value,
                required_state=new_state.value,
            )

        self.history.append({
            "from":       self.state.value,
            "to":         new_state.value,
            "granted_by": granted_by,
            "reason":     reason,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        })

        self.state = new_state
        self.granted_by = granted_by
        if reason:
            self.notes = reason

        return self

    def can_execute(self) -> bool:
        return self.state in EXECUTABLE_STATES

    def can_expose_manifest(self) -> bool:
        return self.state in MANIFEST_VISIBLE_STATES

    def is_terminal(self) -> bool:
        return self.state == TrustState.REVOKED

    def assert_executable(self) -> None:
        """Raise UCITrustError if node cannot execute actions."""
        if not self.can_execute():
            raise UCITrustError(
                f"Node '{self.node_id}' cannot execute actions in trust state "
                f"'{self.state.value}'. Required: trusted or restricted.",
                current_state=self.state.value,
                required_state="trusted",
            )

    def summary(self) -> dict:
        return {
            "node_id":    self.node_id,
            "state":      self.state.value,
            "can_execute": self.can_execute(),
            "granted_by": self.granted_by,
            "transitions": len(self.history),
        }
