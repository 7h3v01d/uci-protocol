"""
UCI Response Envelope  —  uci/core/response.py
===============================================
Patch 7: Aligned to spec.

Changes from Patch 3:
- UCIResponseError gains severity and retryable (spec-required fields)
- UCIResponseError uses canonical lowercase_snake_case error codes
- ResponseState gains all spec-defined states:
    denied, cancelled, timed_out, partially_completed,
    queued, executing, rolled_back
- UCIErrorCode canonical constants class added
- UCIErrorSeverity canonical constants class added
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .errors import UCIError


RESPONSE_VERSION = "0.1"


# ─────────────────────────────────────────────
# Canonical error severity levels (spec §14)
# ─────────────────────────────────────────────

class UCIErrorSeverity:
    INFO     = "info"
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

VALID_ERROR_SEVERITIES = {
    UCIErrorSeverity.INFO, UCIErrorSeverity.LOW, UCIErrorSeverity.MEDIUM,
    UCIErrorSeverity.HIGH, UCIErrorSeverity.CRITICAL,
}


# ─────────────────────────────────────────────
# Canonical error codes (spec §13)
# ─────────────────────────────────────────────

class UCIErrorCode:
    # Validation
    VALIDATION_ERROR      = "validation_error"
    SCHEMA_ERROR          = "schema_error"
    UNSUPPORTED_VERSION   = "unsupported_version"
    INVALID_INVOCATION    = "invalid_invocation"

    # Governance
    PERMISSION_DENIED     = "permission_denied"
    POLICY_DENIED         = "policy_denied"
    TRUST_FAILURE         = "trust_failure"
    CONFIRMATION_REQUIRED = "confirmation_required"
    NODE_REVOKED          = "node_revoked"
    NODE_SUSPENDED        = "node_suspended"

    # Execution
    EXECUTION_ERROR       = "execution_error"
    TIMEOUT_ERROR         = "timeout_error"
    PROVIDER_UNAVAILABLE  = "provider_unavailable"
    TRANSPORT_ERROR       = "transport_error"
    CANCELLATION_ERROR    = "cancellation_error"
    ROLLBACK_ERROR        = "rollback_error"
    PARTIAL_FAILURE       = "partial_failure"

    # Compatibility
    UNSUPPORTED_ACTION     = "unsupported_action"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    UNSUPPORTED_TRANSPORT  = "unsupported_transport"
    VERSION_MISMATCH       = "version_mismatch"
    INCOMPATIBLE_SCHEMA    = "incompatible_schema"

    # Internal / runtime (implementation-specific, not in core spec)
    NODE_NOT_FOUND         = "node_not_found"
    PROVIDER_NOT_CONNECTED = "provider_not_connected"
    GOVERNANCE_ERROR       = "governance_error"
    INVOCATION_RUNTIME_ERROR = "invocation_runtime_error"


# ─────────────────────────────────────────────
# Response state values (spec §6)
# ─────────────────────────────────────────────

class ResponseState:
    COMPLETED           = "completed"
    FAILED              = "failed"
    DENIED              = "denied"
    CANCELLED           = "cancelled"
    TIMED_OUT           = "timed_out"
    PARTIALLY_COMPLETED = "partially_completed"
    DEFERRED            = "deferred"
    QUEUED              = "queued"
    EXECUTING           = "executing"
    ROLLED_BACK         = "rolled_back"

VALID_RESPONSE_STATES = {
    ResponseState.COMPLETED, ResponseState.FAILED, ResponseState.DENIED,
    ResponseState.CANCELLED, ResponseState.TIMED_OUT,
    ResponseState.PARTIALLY_COMPLETED, ResponseState.DEFERRED,
    ResponseState.QUEUED, ResponseState.EXECUTING, ResponseState.ROLLED_BACK,
}


# ─────────────────────────────────────────────
# Sub-structures
# ─────────────────────────────────────────────

@dataclass
class UCIResponseProvider:
    """Identity of the node and action that produced this response."""
    node_id:       str = ""
    instance_id:   str = ""
    capability_id: str = ""
    action_id:     str = ""

    def to_dict(self) -> dict:
        return {
            "node_id":       self.node_id,
            "instance_id":   self.instance_id,
            "capability_id": self.capability_id,
            "action_id":     self.action_id,
        }


@dataclass
class UCIResponseError:
    """
    Canonical UCI error object (spec §11).
    Required fields: code, severity, message, retryable, details.
    """
    code:      str  = ""
    severity:  str  = UCIErrorSeverity.MEDIUM    # ← spec-required
    message:   str  = ""
    retryable: bool = False                       # ← spec-required
    detail:    dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "code":      self.code,
            "severity":  self.severity,
            "message":   self.message,
            "retryable": self.retryable,
            "detail":    self.detail,
        }

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        code: str = "",
        severity: str = UCIErrorSeverity.MEDIUM,
        retryable: bool = False,
    ) -> "UCIResponseError":
        error_code = code or UCIErrorCode.EXECUTION_ERROR
        return cls(
            code      = error_code,
            severity  = severity,
            message   = str(exc),
            retryable = retryable,
            detail    = {"exception_type": type(exc).__name__},
        )


@dataclass
class UCIResponseGovernance:
    outcome:      str = "allow"
    trust_state:  str = "trusted"
    restrictions: list[str] = field(default_factory=list)
    operator_id:  Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "outcome":      self.outcome,
            "trust_state":  self.trust_state,
            "restrictions": self.restrictions,
            "operator_id":  self.operator_id,
        }


@dataclass
class UCIResponseAudit:
    invocation_id: str = ""
    node_id:       str = ""
    capability_id: str = ""
    action_id:     str = ""
    timestamp:     str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    outcome:       str = ""
    actor:         str = "uci_engine"

    def to_dict(self) -> dict:
        return {
            "invocation_id": self.invocation_id,
            "node_id":       self.node_id,
            "capability_id": self.capability_id,
            "action_id":     self.action_id,
            "timestamp":     self.timestamp,
            "outcome":       self.outcome,
            "actor":         self.actor,
        }


# ─────────────────────────────────────────────
# Root response envelope
# ─────────────────────────────────────────────

@dataclass
class UCIResponse:
    """
    Canonical UCI response envelope (spec §4).
    Every invocation produces exactly one UCIResponse.
    """
    uci_response_version: str  = RESPONSE_VERSION
    invocation_id:  str  = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str  = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:      str  = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state:          str  = ResponseState.COMPLETED
    success:        bool = True
    provider:       UCIResponseProvider   = field(default_factory=UCIResponseProvider)
    output:         Optional[Any]         = None
    error:          Optional[UCIResponseError] = None
    governance:     UCIResponseGovernance = field(default_factory=UCIResponseGovernance)
    audit:          UCIResponseAudit      = field(default_factory=UCIResponseAudit)

    # ── Factories ────────────────────────────

    @classmethod
    def success_response(
        cls,
        output:        Any,
        node_id:       str,
        instance_id:   str,
        capability_id: str,
        action_id:     str,
        trust_state:   str    = "trusted",
        governance_outcome: str = "allow",
        restrictions:  list[str] = None,
        operator_id:   Optional[str] = None,
        correlation_id: Optional[str] = None,
        actor:         str    = "uci_engine",
    ) -> "UCIResponse":
        invocation_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        return cls(
            invocation_id  = invocation_id,
            correlation_id = correlation_id or str(uuid.uuid4()),
            timestamp      = ts,
            state          = ResponseState.COMPLETED,
            success        = True,
            provider       = UCIResponseProvider(
                node_id=node_id, instance_id=instance_id,
                capability_id=capability_id, action_id=action_id,
            ),
            output         = output,
            error          = None,
            governance     = UCIResponseGovernance(
                outcome=governance_outcome, trust_state=trust_state,
                restrictions=restrictions or [], operator_id=operator_id,
            ),
            audit          = UCIResponseAudit(
                invocation_id=invocation_id, node_id=node_id,
                capability_id=capability_id, action_id=action_id,
                timestamp=ts, outcome=governance_outcome, actor=actor,
            ),
        )

    @classmethod
    def failure_response(
        cls,
        error:         UCIResponseError,
        node_id:       str   = "",
        instance_id:   str   = "",
        capability_id: str   = "",
        action_id:     str   = "",
        trust_state:   str   = "trusted",
        governance_outcome: str = "allow",
        correlation_id: Optional[str] = None,
        actor:         str   = "uci_engine",
    ) -> "UCIResponse":
        invocation_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        # Map governance deny to denied state
        state = (ResponseState.DENIED
                 if governance_outcome == "deny"
                 else ResponseState.FAILED)
        return cls(
            invocation_id  = invocation_id,
            correlation_id = correlation_id or str(uuid.uuid4()),
            timestamp      = ts,
            state          = state,
            success        = False,
            provider       = UCIResponseProvider(
                node_id=node_id, instance_id=instance_id,
                capability_id=capability_id, action_id=action_id,
            ),
            output         = None,
            error          = error,
            governance     = UCIResponseGovernance(
                outcome=governance_outcome, trust_state=trust_state,
            ),
            audit          = UCIResponseAudit(
                invocation_id=invocation_id, node_id=node_id,
                capability_id=capability_id, action_id=action_id,
                timestamp=ts, outcome="error", actor=actor,
            ),
        )

    @classmethod
    def deferred_response(
        cls,
        node_id:       str,
        instance_id:   str,
        capability_id: str,
        action_id:     str,
        trust_state:   str   = "trusted",
        reason:        str   = "",
        correlation_id: Optional[str] = None,
    ) -> "UCIResponse":
        invocation_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        return cls(
            invocation_id  = invocation_id,
            correlation_id = correlation_id or str(uuid.uuid4()),
            timestamp      = ts,
            state          = ResponseState.DEFERRED,
            success        = False,
            provider       = UCIResponseProvider(
                node_id=node_id, instance_id=instance_id,
                capability_id=capability_id, action_id=action_id,
            ),
            output         = None,
            error          = UCIResponseError(
                code      = UCIErrorCode.CONFIRMATION_REQUIRED,
                severity  = UCIErrorSeverity.LOW,
                message   = reason or "Operator confirmation required.",
                retryable = True,
            ),
            governance     = UCIResponseGovernance(
                outcome="defer", trust_state=trust_state,
            ),
            audit          = UCIResponseAudit(
                invocation_id=invocation_id, node_id=node_id,
                capability_id=capability_id, action_id=action_id,
                timestamp=ts, outcome="defer",
            ),
        )

    @classmethod
    def from_exception(
        cls,
        exc:           Exception,
        node_id:       str   = "",
        instance_id:   str   = "",
        capability_id: str   = "",
        action_id:     str   = "",
        code:          str   = "",
        correlation_id: Optional[str] = None,
    ) -> "UCIResponse":
        return cls.failure_response(
            error          = UCIResponseError.from_exception(exc, code=code),
            node_id        = node_id,
            instance_id    = instance_id,
            capability_id  = capability_id,
            action_id      = action_id,
            correlation_id = correlation_id,
        )

    # ── Accessors ────────────────────────────

    def is_completed(self) -> bool:
        return self.state == ResponseState.COMPLETED

    def is_failed(self) -> bool:
        return self.state in {ResponseState.FAILED, ResponseState.DENIED}

    def is_deferred(self) -> bool:
        return self.state == ResponseState.DEFERRED

    def is_denied(self) -> bool:
        return self.state == ResponseState.DENIED

    def assert_success(self) -> Any:
        if self.success and self.output is not None:
            return self.output
        if self.error:
            raise UCIError(f"[{self.error.code}] {self.error.message}")
        raise UCIError(
            f"Response state='{self.state}' success={self.success} — no output."
        )

    # ── Serialisation ────────────────────────

    def to_dict(self) -> dict:
        return {
            "uci_response_version": self.uci_response_version,
            "invocation_id":        self.invocation_id,
            "correlation_id":       self.correlation_id,
            "timestamp":            self.timestamp,
            "state":                self.state,
            "success":              self.success,
            "provider":             self.provider.to_dict(),
            "output":               self.output,
            "error":                self.error.to_dict() if self.error else None,
            "governance":           self.governance.to_dict(),
            "audit":                self.audit.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> "UCIResponse":
        from .errors import UCIManifestError
        if not isinstance(data, dict):
            raise UCIManifestError("UCIResponse.from_dict requires a dict.")
        raw_prov = data.get("provider", {})
        raw_gov  = data.get("governance", {})
        raw_aud  = data.get("audit", {})
        raw_err  = data.get("error")
        return cls(
            uci_response_version = data.get("uci_response_version", RESPONSE_VERSION),
            invocation_id        = data.get("invocation_id", ""),
            correlation_id       = data.get("correlation_id", ""),
            timestamp            = data.get("timestamp", ""),
            state                = data.get("state", ResponseState.FAILED),
            success              = data.get("success", False),
            provider             = UCIResponseProvider(
                node_id=raw_prov.get("node_id", ""),
                instance_id=raw_prov.get("instance_id", ""),
                capability_id=raw_prov.get("capability_id", ""),
                action_id=raw_prov.get("action_id", ""),
            ),
            output               = data.get("output"),
            error                = UCIResponseError(
                code      = raw_err.get("code", ""),
                severity  = raw_err.get("severity", UCIErrorSeverity.MEDIUM),
                message   = raw_err.get("message", ""),
                retryable = raw_err.get("retryable", False),
                detail    = raw_err.get("detail", {}),
            ) if raw_err else None,
            governance           = UCIResponseGovernance(
                outcome=raw_gov.get("outcome", "allow"),
                trust_state=raw_gov.get("trust_state", "trusted"),
                restrictions=raw_gov.get("restrictions", []),
                operator_id=raw_gov.get("operator_id"),
            ),
            audit                = UCIResponseAudit(
                invocation_id=raw_aud.get("invocation_id", ""),
                node_id=raw_aud.get("node_id", ""),
                capability_id=raw_aud.get("capability_id", ""),
                action_id=raw_aud.get("action_id", ""),
                timestamp=raw_aud.get("timestamp", ""),
                outcome=raw_aud.get("outcome", ""),
                actor=raw_aud.get("actor", "uci_engine"),
            ),
        )
