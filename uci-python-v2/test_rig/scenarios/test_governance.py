"""
Governance engine tests.
invoke() now returns UCIResponse — tests updated accordingly.
"""

import pytest
from uci.core.governance import GovernanceOutcome, PolicyEngine
from uci.core.trust import TrustRecord, TrustState
from uci.core.errors import UCIGovernanceError
from uci.core.response import UCIResponse, ResponseState, UCIErrorCode


class TestGovernanceAllow:
    def test_search_action_allowed(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "UCI spec", "limit": 5})
        assert isinstance(r, UCIResponse)
        assert r.success
        assert r.output["count"] >= 0

    def test_health_check_allowed(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r.success
        assert r.output["status"] == "healthy"

    def test_restricted_node_low_risk_allowed(self, orchestrator, beta):
        orchestrator.connect(beta)
        r = orchestrator.invoke("provider_beta", "voice_tts", "synthesize",
                                {"text": "Hello UCI", "voice_id": "default"})
        assert r.success
        assert "audio_url" in r.output


class TestGovernanceDeny:
    def test_unknown_capability_returns_failure_response(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "nonexistent_capability", "some_action")
        assert isinstance(r, UCIResponse)
        assert not r.success
        assert r.state in {ResponseState.FAILED, ResponseState.DENIED}

    def test_unknown_action_returns_failure_response(self, orchestrator, alpha):
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "nonexistent_action")
        assert not r.success
        assert r.error is not None
        assert r.error.code == "GOVERNANCE_DENIED"

    def test_missing_permission_denied(self, policy, registry, audit, alpha, handshake):
        handshake.run("provider_alpha", alpha.manifest_dict())
        restricted_policy = PolicyEngine(
            orchestrator_permissions=frozenset(),
            audit=audit,
        )
        entry = registry.require("provider_alpha")
        decision = restricted_policy.evaluate_action(
            manifest=entry.manifest,
            capability_id="document_search",
            action_id="search_index",
            trust=entry.trust,
        )
        assert decision.outcome == GovernanceOutcome.DENY
        assert "Missing required permissions" in decision.reason

    def test_revoked_node_returns_failure(self, orchestrator, registry, alpha):
        orchestrator.connect(alpha)
        entry = registry.require("provider_alpha")
        entry.trust.transition(TrustState.REVOKED, reason="Test revocation")
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test"})
        assert not r.success
        assert r.error is not None

    def test_suspended_node_returns_failure(self, orchestrator, registry, alpha):
        orchestrator.connect(alpha)
        entry = registry.require("provider_alpha")
        entry.trust.transition(TrustState.SUSPENDED, reason="Test suspension")
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test"})
        assert not r.success


class TestGovernanceDefer:
    def test_high_risk_action_deferred(self, registry, audit, beta):
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        from uci.core.handshake import HandshakeEngine
        full_perms = DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"])
        p = PolicyEngine(orchestrator_permissions=full_perms, audit=audit)
        he = HandshakeEngine(policy=p, registry=registry, audit=audit)
        he.run("provider_beta", beta.manifest_dict())

        entry = registry.require("provider_beta")
        if entry.trust.state == TrustState.RESTRICTED:
            entry.trust.transition(TrustState.TRUSTED, granted_by="test_operator")
        registry.mount_capability("provider_beta", "file_operations")

        decision = p.evaluate_action(
            manifest=entry.manifest,
            capability_id="file_operations",
            action_id="delete_file",
            trust=entry.trust,
            caller_permissions=full_perms,
        )
        assert decision.outcome == GovernanceOutcome.DEFER
        assert decision.requires_confirmation is True

    def test_operator_can_approve_deferred(self, registry, audit, beta):
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        from uci.core.handshake import HandshakeEngine
        full_perms = DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"])
        p = PolicyEngine(orchestrator_permissions=full_perms, audit=audit)
        he = HandshakeEngine(policy=p, registry=registry, audit=audit)
        he.run("provider_beta", beta.manifest_dict())

        entry = registry.require("provider_beta")
        if entry.trust.state == TrustState.RESTRICTED:
            entry.trust.transition(TrustState.TRUSTED, granted_by="test_operator")
        registry.mount_capability("provider_beta", "file_operations")

        decision = p.evaluate_action(
            manifest=entry.manifest,
            capability_id="file_operations",
            action_id="delete_file",
            trust=entry.trust,
            caller_permissions=full_perms,
        )
        assert decision.outcome == GovernanceOutcome.DEFER
        approved = p.operator_approve(decision, operator_id="leon")
        assert approved.outcome == GovernanceOutcome.ALLOW
        assert "leon" in approved.reason

    def test_deferred_without_operator_returns_deferred_response(self, registry, audit, beta):
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
                        {"path": "/tmp/test.txt"})
        assert isinstance(r, UCIResponse)
        assert not r.success
        assert r.state == ResponseState.DEFERRED
        assert r.error.code == UCIErrorCode.CONFIRMATION_REQUIRED


class TestGovernanceAuditTrail:
    def test_allow_generates_audit(self, orchestrator, audit, alpha):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "document_search", "search_index",
                            {"query": "test"})
        allowed = [r for r in audit.all() if r.event_type == "execution_allowed"]
        assert len(allowed) >= 1

    def test_deny_generates_audit(self, orchestrator, audit, alpha):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "nonexistent", "action")
        assert audit.count() > 0
