"""
UCIResponse envelope tests.
Covers factories, fields, serialisation, roundtrip, assert_success, and edge cases.
"""

import pytest
from uci.core.response import (
    UCIResponse, UCIResponseError, UCIResponseProvider,
    UCIResponseGovernance, UCIResponseAudit, ResponseState,
    UCIErrorCode, UCIErrorSeverity,
    RESPONSE_VERSION,
)
from uci.core.errors import UCIError


# ── Factory: success_response ─────────────────────────────────────────────────

class TestSuccessFactory:
    def _make(self, **kwargs):
        defaults = dict(
            output        = {"result": "ok"},
            node_id       = "test_node",
            instance_id   = "test_001",
            capability_id = "test_cap",
            action_id     = "test_action",
        )
        defaults.update(kwargs)
        return UCIResponse.success_response(**defaults)

    def test_state_is_completed(self):
        r = self._make()
        assert r.state == ResponseState.COMPLETED

    def test_success_is_true(self):
        r = self._make()
        assert r.success is True

    def test_error_is_none(self):
        r = self._make()
        assert r.error is None

    def test_output_preserved(self):
        r = self._make(output={"foo": "bar"})
        assert r.output == {"foo": "bar"}

    def test_provider_fields(self):
        r = self._make()
        assert r.provider.node_id == "test_node"
        assert r.provider.capability_id == "test_cap"
        assert r.provider.action_id == "test_action"

    def test_invocation_id_is_uuid(self):
        r = self._make()
        assert len(r.invocation_id) == 36
        assert r.invocation_id.count("-") == 4

    def test_timestamp_is_iso(self):
        r = self._make()
        assert "T" in r.timestamp
        assert r.timestamp.endswith("+00:00") or r.timestamp.endswith("Z") or "+" in r.timestamp

    def test_version_field(self):
        r = self._make()
        assert r.uci_response_version == RESPONSE_VERSION

    def test_governance_snapshot(self):
        r = self._make(trust_state="trusted", governance_outcome="allow")
        assert r.governance.trust_state == "trusted"
        assert r.governance.outcome == "allow"

    def test_audit_snapshot_node_id(self):
        r = self._make()
        assert r.audit.node_id == "test_node"
        assert r.audit.capability_id == "test_cap"
        assert r.audit.action_id == "test_action"

    def test_two_responses_have_different_ids(self):
        r1 = self._make()
        r2 = self._make()
        assert r1.invocation_id != r2.invocation_id

    def test_correlation_id_passthrough(self):
        r = self._make(correlation_id="my-corr-123")
        assert r.correlation_id == "my-corr-123"

    def test_operator_id_in_governance(self):
        r = self._make(operator_id="leon")
        assert r.governance.operator_id == "leon"

    def test_restrictions_in_governance(self):
        r = self._make(restrictions=["rate_limited"])
        assert "rate_limited" in r.governance.restrictions


# ── Factory: failure_response ─────────────────────────────────────────────────

class TestFailureFactory:
    def _make(self, **kwargs):
        defaults = dict(
            error         = UCIResponseError(code="TEST_ERR", message="test error"),
            node_id       = "test_node",
            capability_id = "test_cap",
            action_id     = "test_action",
        )
        defaults.update(kwargs)
        return UCIResponse.failure_response(**defaults)

    def test_state_is_failed(self):
        assert self._make().state == ResponseState.FAILED

    def test_success_is_false(self):
        assert self._make().success is False

    def test_output_is_none(self):
        assert self._make().output is None

    def test_error_code_preserved(self):
        r = self._make(error=UCIResponseError(code="MY_CODE", message="oops"))
        assert r.error.code == "MY_CODE"
        assert r.error.message == "oops"


# ── Factory: deferred_response ────────────────────────────────────────────────

class TestDeferredFactory:
    def _make(self, **kwargs):
        defaults = dict(
            node_id       = "test_node",
            instance_id   = "test_001",
            capability_id = "test_cap",
            action_id     = "test_action",
            reason        = "High-risk action requires confirmation.",
        )
        defaults.update(kwargs)
        return UCIResponse.deferred_response(**defaults)

    def test_state_is_deferred(self):
        assert self._make().state == ResponseState.DEFERRED

    def test_success_is_false(self):
        assert self._make().success is False

    def test_error_code_is_governance_deferred(self):
        r = self._make()
        assert r.error.code == UCIErrorCode.CONFIRMATION_REQUIRED

    def test_reason_in_error_message(self):
        r = self._make(reason="Needs operator.")
        assert "Needs operator." in r.error.message

    def test_governance_outcome_is_defer(self):
        r = self._make()
        assert r.governance.outcome == "defer"


# ── Factory: from_exception ───────────────────────────────────────────────────

class TestFromException:
    def test_state_is_failed(self):
        r = UCIResponse.from_exception(ValueError("boom"))
        assert r.state == ResponseState.FAILED
        assert not r.success

    def test_message_from_exception(self):
        r = UCIResponse.from_exception(RuntimeError("something went wrong"))
        assert "something went wrong" in r.error.message

    def test_custom_code(self):
        r = UCIResponse.from_exception(Exception("err"), code="MY_CODE")
        assert r.error.code == "MY_CODE"

    def test_exception_type_in_detail(self):
        r = UCIResponse.from_exception(ValueError("bad"))
        assert r.error.detail.get("exception_type") == "ValueError"


# ── UCIResponseError ──────────────────────────────────────────────────────────

class TestResponseError:
    def test_from_exception_uses_canonical_code(self):
        err = UCIResponseError.from_exception(KeyError("missing"))
        assert err.code == UCIErrorCode.EXECUTION_ERROR

    def test_from_exception_custom_code(self):
        err = UCIResponseError.from_exception(Exception("x"), code="CUSTOM")
        assert err.code == "CUSTOM"

    def test_to_dict(self):
        err = UCIResponseError(code="X", message="y", detail={"k": "v"})
        d = err.to_dict()
        assert d["code"] == "X"
        assert d["message"] == "y"
        assert d["detail"]["k"] == "v"


# ── assert_success ────────────────────────────────────────────────────────────

class TestAssertSuccess:
    def test_returns_output_on_success(self):
        r = UCIResponse.success_response(
            output={"data": 42}, node_id="n", instance_id="i",
            capability_id="c", action_id="a",
        )
        assert r.assert_success() == {"data": 42}

    def test_raises_on_failure(self):
        r = UCIResponse.failure_response(
            error=UCIResponseError(code="FAIL", message="it failed"),
            node_id="n",
        )
        with pytest.raises(UCIError) as exc_info:
            r.assert_success()
        assert "it failed" in str(exc_info.value)

    def test_raises_on_deferred(self):
        r = UCIResponse.deferred_response(
            node_id="n", instance_id="i",
            capability_id="c", action_id="a",
        )
        with pytest.raises(UCIError):
            r.assert_success()


# ── State helpers ─────────────────────────────────────────────────────────────

class TestStateHelpers:
    def test_is_completed(self):
        r = UCIResponse.success_response(
            output={}, node_id="n", instance_id="i",
            capability_id="c", action_id="a",
        )
        assert r.is_completed()
        assert not r.is_failed()
        assert not r.is_deferred()

    def test_is_failed(self):
        r = UCIResponse.failure_response(
            error=UCIResponseError(code="E", message="e"), node_id="n"
        )
        assert r.is_failed()
        assert not r.is_completed()

    def test_is_deferred(self):
        r = UCIResponse.deferred_response(
            node_id="n", instance_id="i", capability_id="c", action_id="a"
        )
        assert r.is_deferred()


# ── Serialisation ─────────────────────────────────────────────────────────────

class TestSerialisation:
    def _success(self):
        return UCIResponse.success_response(
            output={"result": "ok"},
            node_id="test_node", instance_id="test_001",
            capability_id="test_cap", action_id="test_action",
            trust_state="trusted", governance_outcome="allow",
        )

    def test_to_dict_has_all_top_level_keys(self):
        d = self._success().to_dict()
        for key in ["uci_response_version", "invocation_id", "correlation_id",
                    "timestamp", "state", "success", "provider",
                    "output", "error", "governance", "audit"]:
            assert key in d

    def test_to_dict_error_is_none_on_success(self):
        assert self._success().to_dict()["error"] is None

    def test_to_json_is_valid_json(self):
        import json
        j = self._success().to_json()
        d = json.loads(j)
        assert d["success"] is True

    def test_from_dict_roundtrip(self):
        r = self._success()
        r2 = UCIResponse.from_dict(r.to_dict())
        assert r2.invocation_id  == r.invocation_id
        assert r2.success        == r.success
        assert r2.state          == r.state
        assert r2.provider.node_id       == r.provider.node_id
        assert r2.provider.capability_id == r.provider.capability_id
        assert r2.governance.outcome     == r.governance.outcome
        assert r2.governance.trust_state == r.governance.trust_state
        assert r2.audit.node_id          == r.audit.node_id

    def test_failure_roundtrip(self):
        r = UCIResponse.failure_response(
            error=UCIResponseError(code="ERR", message="bad", detail={"k": "v"}),
            node_id="n", capability_id="c", action_id="a",
        )
        r2 = UCIResponse.from_dict(r.to_dict())
        assert not r2.success
        assert r2.error.code == "ERR"
        assert r2.error.detail["k"] == "v"

    def test_deferred_roundtrip(self):
        r = UCIResponse.deferred_response(
            node_id="n", instance_id="i", capability_id="c", action_id="a",
            reason="needs confirmation",
        )
        r2 = UCIResponse.from_dict(r.to_dict())
        assert r2.state == ResponseState.DEFERRED
        assert r2.governance.outcome == "defer"
