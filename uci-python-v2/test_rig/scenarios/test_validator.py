"""
CLI Validator tests.
Covers: file loading, JSON parse errors, spec validation,
        warning generation, strict mode, JSON output, exit codes.
"""

import json
import os
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from uci_validate import UCIValidator, ValidationIssue, ManifestReport, collect_paths


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_MANIFEST = {
    "uci_manifest_version": "0.1",
    "node": {
        "node_id": "test_node",
        "instance_id": "test_001",
        "display_name": "Test Node",
        "node_type": "service",
        "version": "1.0.0",
        "vendor": "KeystoneAI",
        "description": "A test service.",
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
                    "input_schema": {"query": "string"},
                    "output_schema": {"result": "string"},
                    "risk": {"level": "low", "categories": ["read_only"]},
                    "permissions": {
                        "required_permissions": [],
                        "operator_confirmation": "none",
                        "minimum_trust_state": "trusted",
                    },
                    "errors": [],
                }
            ],
        }
    ],
    "transports": [
        {
            "transport_id": "local_ipc",
            "type": "ipc",
            "endpoint": "uci://local/test_node",
            "security": {},
            "options": {},
        }
    ],
    "governance": {
        "requires_policy_check": True,
        "audit_required": True,
        "operator_authority_required": False,
        "default_action_policy": "deny",
        "signed_invocations_required": False,
    },
    "compliance": {"profile": "minimal"},
    "audit": {"audit_enabled": True},
    "extensions": {},
    "health": {},
}


def make_manifest(**overrides):
    """Deep-copy VALID_MANIFEST and apply top-level overrides."""
    import copy
    m = copy.deepcopy(VALID_MANIFEST)
    m.update(overrides)
    return m


def write_json(data: dict, suffix=".json") -> str:
    """Write data to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    json.dump(data, f)
    f.close()
    return f.name


# ── Valid manifest ─────────────────────────────────────────────────────────────

class TestValidManifest:
    def test_valid_manifest_passes(self):
        v = UCIValidator()
        r = v.validate_dict(VALID_MANIFEST)
        assert r.valid, [i.message for i in r.errors]

    def test_valid_manifest_has_no_errors(self):
        v = UCIValidator()
        r = v.validate_dict(VALID_MANIFEST)
        assert r.errors == []

    def test_metadata_populated(self):
        v = UCIValidator()
        r = v.validate_dict(VALID_MANIFEST)
        assert r.node_id == "test_node"
        assert r.manifest_version == "0.1"
        assert "test_cap" in r.capabilities_found
        assert "local_ipc" in r.transports_found

    def test_valid_file_passes(self):
        path = write_json(VALID_MANIFEST)
        try:
            v = UCIValidator()
            r = v.validate_file(path)
            assert r.valid
        finally:
            os.unlink(path)


# ── File errors ────────────────────────────────────────────────────────────────

class TestFileErrors:
    def test_missing_file_reported(self):
        v = UCIValidator()
        r = v.validate_file("/nonexistent/path/manifest.json")
        assert not r.valid
        assert any(i.code == "FILE_NOT_FOUND" for i in r.issues)

    def test_invalid_json_reported(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        f.write("{ this is not json !!!")
        f.close()
        try:
            v = UCIValidator()
            r = v.validate_file(f.name)
            assert not r.valid
            assert any(i.code == "JSON_PARSE_ERROR" for i in r.issues)
        finally:
            os.unlink(f.name)

    def test_non_dict_json_reported(self):
        v = UCIValidator()
        r = v.validate_dict(["not", "a", "dict"])
        assert not r.valid
        assert any(i.code == "NOT_A_DICT" for i in r.issues)


# ── Missing blocks ─────────────────────────────────────────────────────────────

class TestMissingBlocks:
    def test_missing_version_reported(self):
        m = make_manifest()
        del m["uci_manifest_version"]
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_missing_node_reported(self):
        m = make_manifest()
        del m["node"]
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid
        assert any("node" in i.message.lower() for i in r.errors)

    def test_missing_capabilities_block_reported(self):
        m = make_manifest()
        del m["capabilities"]
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_missing_transports_block_reported(self):
        m = make_manifest()
        del m["transports"]
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_missing_compliance_is_warning_not_error(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        del m["compliance"]
        v = UCIValidator()
        r = v.validate_dict(m)
        assert r.valid   # still valid
        assert any(i.code == "MISSING_RECOMMENDED_BLOCK" and "compliance" in i.location
                   for i in r.warnings)


# ── Spec violations ────────────────────────────────────────────────────────────

class TestSpecViolations:
    def test_unsupported_version_rejected(self):
        m = make_manifest(**{"uci_manifest_version": "99.0"})
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid
        assert any(i.code == "UNSUPPORTED_VERSION" for i in r.errors)

    def test_empty_node_id_rejected(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_id"] = ""
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_invalid_node_type_rejected(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["node_type"] = "malware"
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_empty_capabilities_rejected(self):
        m = make_manifest(capabilities=[])
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_empty_transports_rejected(self):
        m = make_manifest(transports=[])
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_stream_execution_mode_rejected(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["execution"]["mode"] = "stream"
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_invalid_risk_level_rejected(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["risk"]["level"] = "catastrophic"
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_invalid_transport_type_rejected(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["transports"][0]["type"] = "telepathy"
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid

    def test_empty_transport_endpoint_rejected(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["transports"][0]["endpoint"] = ""
        v = UCIValidator()
        r = v.validate_dict(m)
        assert not r.valid


# ── Warnings ───────────────────────────────────────────────────────────────────

class TestWarnings:
    def test_missing_vendor_is_warning(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["vendor"] = ""
        v = UCIValidator()
        r = v.validate_dict(m)
        assert r.valid
        assert any(i.code == "MISSING_VENDOR" for i in r.warnings)

    def test_missing_node_description_is_warning(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["description"] = ""
        v = UCIValidator()
        r = v.validate_dict(m)
        assert r.valid
        assert any(i.code == "MISSING_NODE_DESCRIPTION" for i in r.warnings)

    def test_permissive_default_policy_is_warning(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["governance"]["default_action_policy"] = "allow"
        v = UCIValidator()
        r = v.validate_dict(m)
        assert r.valid
        assert any(i.code == "PERMISSIVE_DEFAULT_POLICY" for i in r.warnings)

    def test_high_risk_no_confirmation_is_warning(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["capabilities"][0]["actions"][0]["risk"]["level"] = "high"
        m["capabilities"][0]["actions"][0]["permissions"]["operator_confirmation"] = "none"
        v = UCIValidator()
        r = v.validate_dict(m)
        assert r.valid
        assert any(i.code == "HIGH_RISK_NO_CONFIRMATION" for i in r.warnings)

    def test_audit_disabled_is_warning(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["governance"]["audit_required"] = False
        v = UCIValidator()
        r = v.validate_dict(m)
        assert r.valid
        assert any(i.code == "AUDIT_DISABLED" for i in r.warnings)


# ── Strict mode ────────────────────────────────────────────────────────────────

class TestStrictMode:
    def test_strict_promotes_warnings_to_errors(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["vendor"] = ""   # produces MISSING_VENDOR warning
        v = UCIValidator(strict=True)
        r = v.validate_dict(m)
        assert not r.valid
        assert any(i.code == "MISSING_VENDOR" and i.severity == "error" for i in r.issues)

    def test_non_strict_warning_does_not_fail(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["vendor"] = ""
        v = UCIValidator(strict=False)
        r = v.validate_dict(m)
        assert r.valid

    def test_strict_permissive_policy_fails(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["governance"]["default_action_policy"] = "allow"
        v = UCIValidator(strict=True)
        r = v.validate_dict(m)
        assert not r.valid


# ── JSON output ────────────────────────────────────────────────────────────────

class TestJsonOutput:
    def test_to_dict_has_required_keys(self):
        v = UCIValidator()
        r = v.validate_dict(VALID_MANIFEST)
        d = r.to_dict()
        for key in ["path", "valid", "node_id", "manifest_version",
                    "capabilities", "transports", "issues", "summary"]:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_summary_counts(self):
        import copy
        m = copy.deepcopy(VALID_MANIFEST)
        m["node"]["vendor"] = ""     # 1 warning
        v = UCIValidator()
        r = v.validate_dict(m)
        d = r.to_dict()
        assert d["summary"]["warnings"] >= 1
        assert d["summary"]["errors"] == 0

    def test_issue_to_dict(self):
        issue = ValidationIssue(
            severity="error", code="TEST_CODE",
            message="Test message", location="node.vendor"
        )
        d = issue.to_dict()
        assert d["severity"] == "error"
        assert d["code"] == "TEST_CODE"
        assert d["location"] == "node.vendor"


# ── collect_paths ──────────────────────────────────────────────────────────────

class TestCollectPaths:
    def test_single_file(self):
        path = write_json(VALID_MANIFEST)
        try:
            paths = collect_paths([path])
            assert path in paths
        finally:
            os.unlink(path)

    def test_directory_collects_json(self):
        with tempfile.TemporaryDirectory() as d:
            p1 = os.path.join(d, "a.json")
            p2 = os.path.join(d, "b.json")
            p3 = os.path.join(d, "c.txt")
            for p in [p1, p2, p3]:
                with open(p, "w") as f:
                    f.write("{}")
            paths = collect_paths([d])
            assert p1 in paths
            assert p2 in paths
            assert p3 not in paths  # .txt excluded

    def test_nonexistent_path_skipped(self, capsys):
        paths = collect_paths(["/nonexistent/path.json"])
        assert paths == []
