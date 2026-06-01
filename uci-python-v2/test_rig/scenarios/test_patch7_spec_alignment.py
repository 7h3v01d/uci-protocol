"""
Spec Alignment Tests — Patch 7
Verifies that the implementation now matches the spec documents precisely.
"""

import json
import pytest

from uci.core.response import (
    UCIResponse, UCIResponseError, UCIErrorCode, UCIErrorSeverity,
    ResponseState, VALID_RESPONSE_STATES,
)
from uci.core.invocation import UCIInvocation, INVOCATION_VERSION
from uci.core.manifest import UCIManifest, UCINode, UCIHealth, UCICapability, UCIAction, UCITransport, UCIGovernanceMeta
from uci.core.audit import AuditLog, AuditEvent, AUDIT_EVENT_VERSION
from uci.core.errors import UCIManifestError
from uci.core.schema_validator import (
    validate_manifest_schema, validate_response_schema, validate_audit_session_schema,
)


# ── Canonical error codes ──────────────────────────────────────────────────────

class TestCanonicalErrorCodes:
    """Error codes must be lowercase_snake_case per spec taxonomy (§10)."""

    def test_all_validation_codes_are_lowercase_snake(self):
        codes = [
            UCIErrorCode.VALIDATION_ERROR, UCIErrorCode.SCHEMA_ERROR,
            UCIErrorCode.UNSUPPORTED_VERSION, UCIErrorCode.INVALID_INVOCATION,
        ]
        for code in codes:
            assert code == code.lower(), f"{code} is not lowercase"
            assert " " not in code

    def test_all_governance_codes_are_lowercase_snake(self):
        codes = [
            UCIErrorCode.PERMISSION_DENIED, UCIErrorCode.POLICY_DENIED,
            UCIErrorCode.TRUST_FAILURE, UCIErrorCode.CONFIRMATION_REQUIRED,
            UCIErrorCode.NODE_REVOKED, UCIErrorCode.NODE_SUSPENDED,
        ]
        for code in codes:
            assert code == code.lower()

    def test_all_execution_codes_are_lowercase_snake(self):
        codes = [
            UCIErrorCode.EXECUTION_ERROR, UCIErrorCode.TIMEOUT_ERROR,
            UCIErrorCode.PROVIDER_UNAVAILABLE, UCIErrorCode.TRANSPORT_ERROR,
            UCIErrorCode.PARTIAL_FAILURE,
        ]
        for code in codes:
            assert code == code.lower()

    def test_all_compatibility_codes_are_lowercase_snake(self):
        codes = [
            UCIErrorCode.UNSUPPORTED_ACTION, UCIErrorCode.UNSUPPORTED_CAPABILITY,
            UCIErrorCode.VERSION_MISMATCH, UCIErrorCode.INCOMPATIBLE_SCHEMA,
        ]
        for code in codes:
            assert code == code.lower()


# ── Response state completeness ───────────────────────────────────────────────

class TestResponseStateCompleteness:
    """ResponseState must include all spec-defined states (error_response_model §6)."""

    def test_all_spec_states_present(self):
        spec_states = {
            "completed", "failed", "denied", "cancelled", "timed_out",
            "partially_completed", "deferred", "queued", "executing", "rolled_back",
        }
        assert spec_states <= VALID_RESPONSE_STATES

    def test_denied_state_exists(self):
        assert ResponseState.DENIED == "denied"

    def test_cancelled_state_exists(self):
        assert ResponseState.CANCELLED == "cancelled"

    def test_timed_out_state_exists(self):
        assert ResponseState.TIMED_OUT == "timed_out"

    def test_partially_completed_state_exists(self):
        assert ResponseState.PARTIALLY_COMPLETED == "partially_completed"

    def test_queued_state_exists(self):
        assert ResponseState.QUEUED == "queued"

    def test_executing_state_exists(self):
        assert ResponseState.EXECUTING == "executing"

    def test_rolled_back_state_exists(self):
        assert ResponseState.ROLLED_BACK == "rolled_back"


# ── UCIResponseError spec fields ──────────────────────────────────────────────

class TestResponseErrorSpecFields:
    """error_response_model §12 requires: code, severity, message, retryable, details."""

    def test_error_has_severity_field(self):
        err = UCIResponseError(code="test", message="test", severity="medium")
        assert err.severity == "medium"

    def test_error_has_retryable_field(self):
        err = UCIResponseError(code="test", message="test", retryable=True)
        assert err.retryable is True

    def test_error_to_dict_includes_severity(self):
        err = UCIResponseError(code="c", message="m", severity="high", retryable=False)
        d = err.to_dict()
        assert "severity" in d
        assert "retryable" in d

    def test_default_severity_is_medium(self):
        err = UCIResponseError(code="c", message="m")
        assert err.severity == UCIErrorSeverity.MEDIUM

    def test_retryable_transport_error(self):
        err = UCIResponseError(
            code=UCIErrorCode.TRANSPORT_ERROR,
            message="connection failed",
            retryable=True,
            severity=UCIErrorSeverity.MEDIUM,
        )
        assert err.retryable is True

    def test_non_retryable_permission_denied(self):
        err = UCIResponseError(
            code=UCIErrorCode.PERMISSION_DENIED,
            message="access denied",
            retryable=False,
            severity=UCIErrorSeverity.HIGH,
        )
        assert err.retryable is False

    def test_governance_denial_produces_denied_state(self):
        r = UCIResponse.failure_response(
            error=UCIResponseError(code=UCIErrorCode.POLICY_DENIED, message="denied"),
            governance_outcome="deny",
        )
        assert r.state == ResponseState.DENIED

    def test_response_schema_validates_with_severity_retryable(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "nonexistent", "action")
        result = validate_response_schema(r.to_dict())
        assert result.valid, [i.message for i in result.issues]


# ── UCIInvocation first-class object ──────────────────────────────────────────

class TestUCIInvocation:
    """Invocation is now a first-class protocol object (invocation_execution §3-4)."""

    def test_invocation_version_field(self):
        inv = UCIInvocation.create(
            node_id="test", capability_id="cap", action_id="act"
        )
        assert inv.uci_invocation_version == INVOCATION_VERSION

    def test_invocation_has_invocation_id(self):
        inv = UCIInvocation.create(node_id="n", capability_id="c", action_id="a")
        assert len(inv.invocation_id) == 36

    def test_invocation_has_correlation_id(self):
        inv = UCIInvocation.create(node_id="n", capability_id="c", action_id="a")
        assert inv.correlation_id

    def test_invocation_has_timestamp(self):
        inv = UCIInvocation.create(node_id="n", capability_id="c", action_id="a")
        assert "T" in inv.timestamp

    def test_invocation_caller_identity(self):
        inv = UCIInvocation.create(
            node_id="provider_alpha",
            capability_id="document_search",
            action_id="search_index",
            caller_node_id="niles",
        )
        assert inv.caller.node_id == "niles"

    def test_invocation_target_identity(self):
        inv = UCIInvocation.create(
            node_id="provider_alpha",
            capability_id="document_search",
            action_id="search_index",
        )
        assert inv.target.node_id == "provider_alpha"
        assert inv.target.capability_id == "document_search"
        assert inv.target.action_id == "search_index"

    def test_invocation_payload(self):
        inv = UCIInvocation.create(
            node_id="n", capability_id="c", action_id="a",
            payload={"query": "UCI spec"},
        )
        assert inv.payload["query"] == "UCI spec"

    def test_invocation_context(self):
        inv = UCIInvocation.create(
            node_id="n", capability_id="c", action_id="a",
            session_id="sess-001", risk_posture="elevated",
        )
        assert inv.context.session_id == "sess-001"
        assert inv.context.risk_posture == "elevated"

    def test_invocation_operator_override(self):
        inv = UCIInvocation.create(
            node_id="n", capability_id="c", action_id="a",
            operator_override="leon",
        )
        assert inv.operator_override == "leon"

    def test_invocation_to_dict(self):
        inv = UCIInvocation.create(node_id="n", capability_id="c", action_id="a")
        d = inv.to_dict()
        for key in ["uci_invocation_version", "invocation_id", "correlation_id",
                    "timestamp", "caller", "target", "payload", "context"]:
            assert key in d

    def test_invocation_roundtrip(self):
        inv = UCIInvocation.create(
            node_id="provider_alpha",
            capability_id="document_search",
            action_id="search_index",
            payload={"query": "UCI"},
            caller_node_id="niles",
            session_id="sess-001",
        )
        inv2 = UCIInvocation.from_dict(inv.to_dict())
        assert inv2.invocation_id == inv.invocation_id
        assert inv2.target.node_id == inv.target.node_id
        assert inv2.payload == inv.payload
        assert inv2.context.session_id == inv.context.session_id

    def test_invoke_with_uses_invocation_object(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        inv = UCIInvocation.create(
            node_id="provider_alpha",
            capability_id="system_health",
            action_id="health_check",
            caller_node_id="niles",
        )
        r = orchestrator.invoke_with(inv)
        assert r.success
        assert r.output["status"] == "healthy"

    def test_invoke_with_preserves_correlation_id(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        inv = UCIInvocation.create(
            node_id="provider_alpha",
            capability_id="system_health",
            action_id="health_check",
            correlation_id="my-trace-123",
        )
        r = orchestrator.invoke_with(inv)
        assert r.correlation_id == "my-trace-123"


# ── Health block ──────────────────────────────────────────────────────────────

class TestHealthBlock:
    """Health is a required top-level manifest block (capability_schema §4)."""

    def test_ucihealth_dataclass_exists(self):
        h = UCIHealth()
        assert hasattr(h, 'health_endpoint')
        assert hasattr(h, 'expose_metrics')
        assert hasattr(h, 'expose_uptime')

    def test_health_in_manifest_to_dict(self, alpha):
        d = alpha.manifest_dict()
        assert "health" in d

    def test_health_schema_required(self):
        m = {
            "uci_manifest_version": "0.1",
            "node": {"node_id": "n", "instance_id": "i", "display_name": "N",
                     "node_type": "service", "version": "1.0.0"},
            "capabilities": [{"capability_id": "c", "version": "1.0",
                               "category": "retrieval",
                               "actions": [{"action_id": "a",
                                            "execution": {"mode": "sync", "timeout_ms": 1000},
                                            "risk": {"level": "low"}, "permissions": {}}]}],
            "transports": [{"transport_id": "t", "type": "ipc", "endpoint": "x"}],
            "governance": {}, "compliance": {}, "audit": {}, "extensions": {},
            # health deliberately omitted
        }
        result = validate_manifest_schema(m)
        assert not result.valid
        assert any("health" in i.message.lower() for i in result.issues)

    def test_display_name_required_in_node(self):
        with pytest.raises(UCIManifestError):
            node = UCINode(
                node_id="n", instance_id="i",
                display_name="",   # empty — should fail
                node_type="service", version="1.0.0",
            )
            node.validate()


# ── Audit spec fields ─────────────────────────────────────────────────────────

class TestAuditSpecFields:
    """AuditRecord must include all spec-required fields (audit_observability §7)."""

    def test_audit_record_has_audit_event_version(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n")
        assert r.audit_event_version == AUDIT_EVENT_VERSION
        assert r.audit_event_version == "0.1"

    def test_audit_record_has_correlation_id_field(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n", correlation_id="corr-001")
        assert r.correlation_id == "corr-001"

    def test_audit_record_has_severity_field(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n", severity="info")
        assert r.severity == "info"

    def test_audit_record_has_source_field(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n",
                       actor="engine", source={"node_id": "engine"})
        assert r.source == {"node_id": "engine"}

    def test_audit_to_dict_includes_spec_fields(self):
        log = AuditLog()
        r = log.append(AuditEvent.INVOCATION_COMPLETED, "provider_alpha",
                       severity="info", correlation_id="c-001")
        d = r.to_dict()
        for field in ["audit_event_version", "correlation_id", "severity", "source"]:
            assert field in d, f"Missing spec field: {field}"

    def test_audit_record_roundtrip_preserves_spec_fields(self):
        from uci.core.audit import AuditRecord
        log = AuditLog()
        r = log.append(AuditEvent.NODE_READY, "node_x",
                       severity="info", correlation_id="trace-xyz")
        r2 = AuditRecord.from_dict(r.to_dict())
        assert r2.audit_event_version == r.audit_event_version
        assert r2.correlation_id == r.correlation_id
        assert r2.severity == r.severity

    def test_audit_session_schema_validates_with_new_fields(
        self, orchestrator, audit, alpha
    ):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        session = audit.export(seal=True)
        result = validate_audit_session_schema(session.to_dict())
        assert result.valid, [i.message for i in result.issues]


# ── Schema $id alignment ──────────────────────────────────────────────────────

class TestSchemaIdAlignment:
    """Schema $id URIs must reference uci-spec.org (spec's canonical URI)."""

    def test_manifest_schema_id(self):
        from uci.core.schema_validator import get_schema
        schema = get_schema("manifest")
        assert "uci-spec.org" in schema["$id"]

    def test_response_schema_id(self):
        from uci.core.schema_validator import get_schema
        schema = get_schema("response")
        assert "uci-spec.org" in schema["$id"]

    def test_audit_session_schema_id(self):
        from uci.core.schema_validator import get_schema
        schema = get_schema("audit_session")
        assert "uci-spec.org" in schema["$id"]
