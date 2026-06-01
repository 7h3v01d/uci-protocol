"""
JSON Schema validator tests — Patch 5.

Covers: schema loading, manifest/response/audit_session validation,
        precise path reporting, integration with uci_validate.py,
        and cross-schema consistency checks.
"""

import json
import copy
import pytest

from uci.core.schema_validator import (
    validate_manifest_schema,
    validate_response_schema,
    validate_audit_session_schema,
    validate_against_schema,
    get_schema,
    SchemaIssue,
    SchemaValidationResult,
)
from uci.core.audit import AuditLog, AuditEvent
from uci.core.response import UCIResponse, UCIResponseError


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_MANIFEST = {
    "uci_manifest_version": "0.1",
    "node": {
        "node_id": "schema_test_node",
        "instance_id": "schema_001",
        "display_name": "Schema Test Node",
        "node_type": "service",
        "version": "1.0.0",
        "vendor": "KeystoneAI",
        "description": "A node for schema testing.",
    },
    "capabilities": [
        {
            "capability_id": "test_cap",
            "version": "1.0",
            "category": "retrieval",
            "description": "Test capability.",
            "actions": [
                {
                    "action_id": "test_action",
                    "description": "A test action.",
                    "execution": {"mode": "sync", "timeout_ms": 1000},
                    "risk": {"level": "low", "categories": ["read_only"]},
                    "permissions": {
                        "required_permissions": [],
                        "operator_confirmation": "none",
                        "minimum_trust_state": "trusted",
                    },
                    "input_schema": {},
                    "output_schema": {},
                    "errors": [],
                }
            ],
        }
    ],
    "transports": [
        {
            "transport_id": "local_ipc",
            "type": "ipc",
            "endpoint": "uci://local/schema_test_node",
        }
    ],
    "governance": {
        "requires_policy_check": True,
        "audit_required": True,
        "default_action_policy": "deny",
    },
    "compliance": {"profile": "minimal"},
    "audit": {"audit_enabled": True},
    "extensions": {},
    "health": {},
}


# ── Schema loading ────────────────────────────────────────────────────────────

class TestSchemaLoading:
    def test_manifest_schema_loads(self):
        schema = get_schema("manifest")
        assert schema["title"] == "UCI Manifest v0.1"

    def test_response_schema_loads(self):
        schema = get_schema("response")
        assert schema["title"] == "UCI Response Envelope v0.1"

    def test_audit_session_schema_loads(self):
        schema = get_schema("audit_session")
        assert schema["title"] == "UCI Audit Session v0.1"

    def test_unknown_schema_returns_invalid_result(self):
        result = validate_against_schema({}, "nonexistent_schema")
        assert not result.valid
        assert result.issues[0].path == "$"

    def test_schema_cached_on_second_load(self):
        s1 = get_schema("manifest")
        s2 = get_schema("manifest")
        assert s1 is s2  # same object — cached


# ── Manifest schema validation ────────────────────────────────────────────────

class TestManifestSchema:
    def test_valid_manifest_passes(self):
        result = validate_manifest_schema(VALID_MANIFEST)
        assert result.valid
        assert result.issues == []

    def test_result_is_truthy_on_valid(self):
        result = validate_manifest_schema(VALID_MANIFEST)
        assert bool(result) is True

    def test_result_is_falsy_on_invalid(self):
        result = validate_manifest_schema({"wrong": "data"})
        assert bool(result) is False

    def test_missing_version_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        del m["uci_manifest_version"]
        result = validate_manifest_schema(m)
        assert not result.valid
        assert any("uci_manifest_version" in i.message for i in result.issues)

    def test_wrong_version_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["uci_manifest_version"] = "99.0"
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_invalid_node_type_reported_with_path(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_type"] = "malware"
        result = validate_manifest_schema(m)
        assert not result.valid
        paths = [i.path for i in result.issues]
        assert any("node_type" in p for p in paths)

    def test_invalid_execution_mode_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["execution"]["mode"] = "stream"
        result = validate_manifest_schema(m)
        assert not result.valid
        paths = [i.path for i in result.issues]
        assert any("mode" in p for p in paths)

    def test_invalid_risk_level_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["risk"]["level"] = "catastrophic"
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_invalid_transport_type_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["transports"][0]["type"] = "telepathy"
        result = validate_manifest_schema(m)
        assert not result.valid
        paths = [i.path for i in result.issues]
        assert any("type" in p for p in paths)

    def test_empty_node_id_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_id"] = ""
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_zero_timeout_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["execution"]["timeout_ms"] = 0
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_empty_capabilities_array_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"] = []
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_empty_transports_array_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["transports"] = []
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_empty_actions_array_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"] = []
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_invalid_risk_category_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["risk"]["categories"] = ["not_a_real_category"]
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_invalid_capability_category_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["category"] = "hacking"
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_node_id_pattern_enforced(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_id"] = "bad node id with spaces!"
        result = validate_manifest_schema(m)
        assert not result.valid


# ── Response schema validation ────────────────────────────────────────────────

class TestResponseSchema:
    def _valid_response_dict(self) -> dict:
        r = UCIResponse.success_response(
            output={"result": "ok"},
            node_id="test_node", instance_id="test_001",
            capability_id="test_cap", action_id="test_action",
        )
        return r.to_dict()

    def test_valid_response_passes(self):
        result = validate_response_schema(self._valid_response_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_missing_invocation_id_fails(self):
        d = self._valid_response_dict()
        del d["invocation_id"]
        result = validate_response_schema(d)
        assert not result.valid

    def test_invalid_state_fails(self):
        d = self._valid_response_dict()
        d["state"] = "exploded"
        result = validate_response_schema(d)
        assert not result.valid

    def test_invalid_governance_outcome_fails(self):
        d = self._valid_response_dict()
        d["governance"]["outcome"] = "maybe"
        result = validate_response_schema(d)
        assert not result.valid

    def test_error_null_on_success(self):
        d = self._valid_response_dict()
        assert d["error"] is None
        result = validate_response_schema(d)
        assert result.valid

    def test_error_object_on_failure(self):
        r = UCIResponse.failure_response(
            error=UCIResponseError(code="TEST", message="test error"),
            node_id="n", capability_id="c", action_id="a",
        )
        result = validate_response_schema(r.to_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_deferred_response_passes_schema(self):
        r = UCIResponse.deferred_response(
            node_id="n", instance_id="i",
            capability_id="c", action_id="a",
        )
        result = validate_response_schema(r.to_dict())
        assert result.valid, [i.message for i in result.issues]


# ── Audit session schema validation ───────────────────────────────────────────

class TestAuditSessionSchema:
    def _valid_session_dict(self) -> dict:
        log = AuditLog(orchestrator_id="test_orch")
        log.append(AuditEvent.NODE_DISCOVERED, "test_node", actor="engine")
        log.append(AuditEvent.INVOCATION_COMPLETED, "test_node",
                   outcome="success", capability_id="cap", action_id="act")
        return log.export(seal=True).to_dict()

    def test_valid_session_passes(self):
        result = validate_audit_session_schema(self._valid_session_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_missing_session_id_fails(self):
        d = self._valid_session_dict()
        del d["session_id"]
        result = validate_audit_session_schema(d)
        assert not result.valid

    def test_short_chain_hash_fails(self):
        d = self._valid_session_dict()
        d["records"][0]["chain_hash"] = "tooshort"
        result = validate_audit_session_schema(d)
        assert not result.valid

    def test_record_count_field_present(self):
        d = self._valid_session_dict()
        assert "record_count" in d
        result = validate_audit_session_schema(d)
        assert result.valid


# ── SchemaValidationResult ────────────────────────────────────────────────────

class TestSchemaValidationResult:
    def test_to_dict_keys(self):
        result = validate_manifest_schema(VALID_MANIFEST)
        d = result.to_dict()
        assert "valid" in d
        assert "schema_name" in d
        assert "issue_count" in d
        assert "issues" in d

    def test_issue_count_matches(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_type"] = "bad_type"
        result = validate_manifest_schema(m)
        d = result.to_dict()
        assert d["issue_count"] == len(d["issues"])

    def test_schema_issue_to_dict(self):
        issue = SchemaIssue(
            path="node.node_type",
            message="'bad_type' is not valid",
            value="bad_type",
            schema_path="properties > node > node_type > enum",
        )
        d = issue.to_dict()
        assert d["path"] == "node.node_type"
        assert d["message"] == "'bad_type' is not valid"
        assert d["schema_path"] == "properties > node > node_type > enum"


# ── Path reporting accuracy ───────────────────────────────────────────────────

class TestPathReporting:
    def test_nested_path_reported_correctly(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["execution"]["mode"] = "stream"
        result = validate_manifest_schema(m)
        assert not result.valid
        # Should report something like capabilities[0].actions[0].execution.mode
        paths = [i.path for i in result.issues]
        assert any("capabilities" in p and "execution" in p for p in paths)

    def test_multiple_errors_all_reported(self):
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_type"] = "bad_type"
        m["capabilities"][0]["actions"][0]["execution"]["mode"] = "stream"
        m["transports"][0]["type"] = "telepathy"
        result = validate_manifest_schema(m)
        assert not result.valid
        assert len(result.issues) >= 3


# ── Integration: schema + semantic validation together ────────────────────────

class TestSchemaSemanticIntegration:
    def test_schema_errors_appear_in_validator_report(self):
        """Schema violations surface in the CLI validator as SCHEMA_VIOLATION codes."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from uci_validate import UCIValidator

        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_type"] = "malware"

        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid
        codes = [i.code for i in r.issues]
        assert "SCHEMA_VIOLATION" in codes or "SPEC_VALIDATION_ERROR" in codes

    def test_valid_manifest_passes_both_layers(self):
        from uci_validate import UCIValidator
        v = UCIValidator()
        r = v.validate_dict(VALID_MANIFEST)
        assert r.valid, [i.message for i in r.errors]

    def test_schema_result_name_preserved(self):
        result = validate_manifest_schema(VALID_MANIFEST)
        assert result.schema_name == "manifest"

    def test_all_three_canonical_objects_validate_cleanly(
        self, orchestrator, audit, alpha
    ):
        """End-to-end: manifest + response + audit all pass their schemas."""
        # Manifest
        manifest_dict = alpha.manifest_dict()
        m_result = validate_manifest_schema(manifest_dict)
        assert m_result.valid, [i.message for i in m_result.issues]

        # Response
        orchestrator.connect(alpha)
        resp = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        r_result = validate_response_schema(resp.to_dict())
        assert r_result.valid, [i.message for i in r_result.issues]

        # Audit session
        session = audit.export(seal=True)
        a_result = validate_audit_session_schema(session.to_dict())
        assert a_result.valid, [i.message for i in a_result.issues]
