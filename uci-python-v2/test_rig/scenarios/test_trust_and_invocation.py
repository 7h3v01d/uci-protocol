"""
Trust lifecycle and invocation tests — updated for UCIResponse envelope.
"""

import pytest
from uci.core.governance import PolicyEngine, GovernanceOutcome
from uci.core.trust import TrustRecord, TrustState
from uci.core.errors import UCITrustError, UCIInvocationError, UCIGovernanceError
from uci.core.response import UCIResponse, ResponseState, UCIErrorCode


class TestTrustStateMachine:
    def test_unknown_to_discovered(self):
        t = TrustRecord(node_id="test")
        t.transition(TrustState.DISCOVERED)
        assert t.state == TrustState.DISCOVERED

    def test_discovered_to_verified(self):
        t = TrustRecord(node_id="test")
        t.transition(TrustState.DISCOVERED)
        t.transition(TrustState.VERIFIED)
        assert t.state == TrustState.VERIFIED

    def test_verified_to_trusted(self):
        t = TrustRecord(node_id="test")
        t.transition(TrustState.DISCOVERED)
        t.transition(TrustState.VERIFIED)
        t.transition(TrustState.TRUSTED)
        assert t.state == TrustState.TRUSTED
        assert t.can_execute()

    def test_trusted_to_restricted(self):
        t = TrustRecord(node_id="test")
        t.transition(TrustState.DISCOVERED)
        t.transition(TrustState.VERIFIED)
        t.transition(TrustState.TRUSTED)
        t.transition(TrustState.RESTRICTED)
        assert t.state == TrustState.RESTRICTED
        assert t.can_execute()

    def test_any_state_to_revoked(self):
        for from_state in [TrustState.DISCOVERED, TrustState.VERIFIED,
                           TrustState.TRUSTED, TrustState.RESTRICTED]:
            t = TrustRecord(node_id="test")
            t.transition(TrustState.DISCOVERED)
            if from_state in {TrustState.VERIFIED, TrustState.TRUSTED, TrustState.RESTRICTED}:
                t.transition(TrustState.VERIFIED)
            if from_state in {TrustState.TRUSTED, TrustState.RESTRICTED}:
                t.transition(TrustState.TRUSTED)
            if from_state == TrustState.RESTRICTED:
                t.transition(TrustState.RESTRICTED)
            t.transition(TrustState.REVOKED)
            assert t.state == TrustState.REVOKED
            assert not t.can_execute()
            assert t.is_terminal()

    def test_revoked_is_terminal(self):
        t = TrustRecord(node_id="test")
        t.transition(TrustState.DISCOVERED)
        t.transition(TrustState.REVOKED)
        with pytest.raises(UCITrustError):
            t.transition(TrustState.VERIFIED)

    def test_illegal_transition_raises(self):
        t = TrustRecord(node_id="test")
        with pytest.raises(UCITrustError):
            t.transition(TrustState.TRUSTED)

    def test_unknown_cannot_execute(self):
        t = TrustRecord(node_id="test")
        assert not t.can_execute()

    def test_history_tracked(self):
        t = TrustRecord(node_id="test")
        t.transition(TrustState.DISCOVERED, granted_by="engine", reason="test")
        t.transition(TrustState.VERIFIED)
        t.transition(TrustState.TRUSTED)
        assert len(t.history) == 3
        assert t.history[0]["from"] == "unknown"
        assert t.history[0]["to"] == "discovered"


class TestInvocation:
    def test_search_returns_uci_response(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test query", "limit": 3})
        assert isinstance(r, UCIResponse)
        assert r.success
        assert r.state == ResponseState.COMPLETED

    def test_search_output_correct(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test query", "limit": 3})
        assert r.output["query"] == "test query"
        assert isinstance(r.output["results"], list)

    def test_get_document_returns_document(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "get_document",
                                {"document_id": "doc_001"})
        assert r.success
        assert r.output["document"]["id"] == "doc_001"

    def test_response_provider_fields_populated(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test"})
        assert r.provider.node_id == "provider_alpha"
        assert r.provider.capability_id == "document_search"
        assert r.provider.action_id == "search_index"

    def test_response_has_invocation_id(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r.invocation_id
        assert len(r.invocation_id) == 36  # UUID format

    def test_response_has_timestamp(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r.timestamp
        assert "T" in r.timestamp  # ISO-8601

    def test_response_governance_snapshot(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test"})
        assert r.governance.trust_state in {"trusted", "restricted"}
        assert r.governance.outcome in {"allow", "allow_with_restrictions"}

    def test_assert_success_returns_output(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        output = r.assert_success()
        assert output["status"] == "healthy"

    def test_unconnected_node_returns_failure(self, orchestrator):
        r = orchestrator.invoke("nonexistent_node", "some_cap", "some_action")
        assert isinstance(r, UCIResponse)
        assert not r.success
        assert r.error is not None

    def test_invocation_audit_trail(self, orchestrator, audit, alpha):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        event_types = [r.event_type for r in audit.all()]
        assert "invocation_requested" in event_types
        assert "invocation_completed" in event_types

    def test_operator_override_allows_high_risk(self, registry, audit, beta):
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        from uci.core.handshake import HandshakeEngine
        from uci.sdk.provider import UCIOrchestrator
        full_perms = DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"])
        p = PolicyEngine(orchestrator_permissions=full_perms, audit=audit)
        orch = UCIOrchestrator(policy=p, registry=registry, audit=audit)
        he = HandshakeEngine(policy=p, registry=registry, audit=audit)
        he.run("provider_beta", beta.manifest_dict())
        orch._providers["provider_beta"] = beta

        entry = registry.require("provider_beta")
        entry.trust.transition(TrustState.TRUSTED, granted_by="test_operator")
        registry.mount_capability("provider_beta", "file_operations")

        r = orch.invoke("provider_beta", "file_operations", "delete_file",
                        {"path": "/tmp/test.txt"},
                        operator_override="leon")
        assert r.success
        assert r.output["deleted"] is True
        assert r.governance.operator_id == "leon"

    def test_response_serialises_to_dict(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        d = r.to_dict()
        for key in ["uci_response_version", "invocation_id", "correlation_id",
                    "timestamp", "state", "success", "provider",
                    "output", "error", "governance", "audit"]:
            assert key in d, f"Missing key in response dict: {key}"

    def test_response_roundtrips_from_dict(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        d = r.to_dict()
        r2 = UCIResponse.from_dict(d)
        assert r2.invocation_id == r.invocation_id
        assert r2.success == r.success
        assert r2.state == r.state
        assert r2.provider.node_id == r.provider.node_id


class TestAuditLog:
    def test_events_are_ordered(self, orchestrator, audit, alpha):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        records = audit.all()
        sequences = [r.sequence for r in records]
        assert sequences == sorted(sequences)

    def test_can_filter_by_node(self, orchestrator, audit, alpha, beta, handshake):
        orchestrator.connect(alpha)
        handshake.run("provider_beta", beta.manifest_dict())
        alpha_events = audit.for_node("provider_alpha")
        assert all(r.node_id == "provider_alpha" for r in alpha_events)
        assert len(alpha_events) > 0

    def test_summary_counts_correctly(self, orchestrator, audit, alpha):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "document_search", "search_index",
                            {"query": "test"})
        summary = audit.summary()
        assert summary["total_events"] > 0
        assert "provider_alpha" in summary["nodes_seen"]

    def test_denials_queryable(self, orchestrator, audit, alpha):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "document_search", "nonexistent")
        assert audit.count() > 0
