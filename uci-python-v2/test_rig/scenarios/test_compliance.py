"""
UCI Compliance Suite  —  test_rig/scenarios/test_compliance.py
==============================================================
Patch 6 — Formal protocol compliance verification.

This suite is different from the unit tests. It verifies that this
UCI implementation exhibits the BEHAVIOURS required by the v0.1 spec,
not just that individual classes work correctly.

Compliance rule IDs follow the pattern:
  C-MAN-NNN  Manifest compliance
  C-GOV-NNN  Governance compliance
  C-HSK-NNN  Handshake compliance
  C-RSP-NNN  Response compliance
  C-AUD-NNN  Audit compliance
  C-SCH-NNN  Schema compliance

A conformant UCI implementation MUST pass every test in this file.
"""

import copy
import json
import pytest

from uci.core.audit import AuditLog, AuditEvent, UCIAuditSession, GENESIS_HASH
from uci.core.errors import UCIError
from uci.core.governance import PolicyEngine, GovernanceOutcome
from uci.core.handshake import HandshakeEngine, HandshakeStage
from uci.core.manifest import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta,
    VALID_EXECUTION_MODES, VALID_NODE_TYPES, VALID_TRANSPORT_TYPES,
    VALID_CAPABILITY_CATEGORIES, VALID_RISK_LEVELS,
)
from uci.core.registry import UCIRegistry
from uci.core.response import UCIResponse, ResponseState, UCIErrorCode, RESPONSE_VERSION
from uci.core.schema_validator import (
    validate_manifest_schema, validate_response_schema,
    validate_audit_session_schema,
)
from uci.core.trust import TrustRecord, TrustState, EXECUTABLE_STATES
from uci.sdk.provider import UCIOrchestrator, UCIProvider


# ═════════════════════════════════════════════════════════════════════════════
# C-MAN — Manifest Compliance
# ═════════════════════════════════════════════════════════════════════════════

class TestManifestCompliance:
    """
    C-MAN: A compliant manifest MUST correctly declare its identity,
    capabilities, transports, and governance requirements.
    """

    def test_C_MAN_001_manifest_version_must_be_supported(self):
        """C-MAN-001: uci_manifest_version must be in SUPPORTED_MANIFEST_VERSIONS."""
        from uci.core.manifest import SUPPORTED_MANIFEST_VERSIONS
        assert "0.1" in SUPPORTED_MANIFEST_VERSIONS

    def test_C_MAN_002_node_id_must_be_non_empty(self):
        """C-MAN-002: node.node_id must be a non-empty string."""
        node = UCINode(node_id="", instance_id="i", node_type="service", version="1.0.0")
        from uci.core.errors import UCIManifestError
        with pytest.raises(UCIManifestError):
            node.validate()

    def test_C_MAN_003_node_type_must_be_canonical(self):
        """C-MAN-003: node.node_type must be one of the locked v0.1 node types."""
        from uci.core.errors import UCIValidationError
        node = UCINode(node_id="n", instance_id="i", display_name="N", node_type="plugin", version="1.0.0")
        with pytest.raises(UCIValidationError):
            node.validate()
        assert "plugin" not in VALID_NODE_TYPES

    def test_C_MAN_004_manifest_requires_at_least_one_capability(self):
        """C-MAN-004: A manifest with zero capabilities MUST be rejected."""
        from uci.core.errors import UCIManifestError
        m = UCIManifest(
            node=UCINode(node_id="n", instance_id="i", node_type="service", version="1.0.0"),
            capabilities=[],
            transports=[UCITransport(transport_id="t", type="ipc", endpoint="uci://n")],
        )
        with pytest.raises(UCIManifestError):
            m.validate()

    def test_C_MAN_005_manifest_requires_at_least_one_transport(self):
        """C-MAN-005: A manifest with zero transports MUST be rejected."""
        from uci.core.errors import UCIManifestError
        m = UCIManifest(
            node=UCINode(node_id="n", instance_id="i", node_type="service", version="1.0.0"),
            capabilities=[UCICapability(
                capability_id="c", version="1.0", category="retrieval",
                actions=[UCIAction(action_id="a")],
            )],
            transports=[],
        )
        with pytest.raises(UCIManifestError):
            m.validate()

    def test_C_MAN_006_capability_requires_at_least_one_action(self):
        """C-MAN-006: A capability with zero actions MUST be rejected."""
        from uci.core.errors import UCIManifestError
        cap = UCICapability(capability_id="c", category="retrieval", actions=[])
        with pytest.raises(UCIManifestError):
            cap.validate()

    def test_C_MAN_007_execution_mode_must_be_canonical(self):
        """C-MAN-007: execution.mode must be a canonical v0.1 value. 'stream' is not valid."""
        from uci.core.errors import UCIValidationError
        exe = UCIExecution(mode="stream")
        with pytest.raises(UCIValidationError):
            exe.validate()
        assert "stream" not in VALID_EXECUTION_MODES
        assert "streaming" in VALID_EXECUTION_MODES

    def test_C_MAN_008_transport_type_must_be_canonical(self):
        """C-MAN-008: transport.type must be canonical. 'local' is not valid."""
        from uci.core.errors import UCIValidationError
        t = UCITransport(transport_id="t", type="local", endpoint="x")
        with pytest.raises(UCIValidationError):
            t.validate()
        assert "local" not in VALID_TRANSPORT_TYPES
        assert "ipc" in VALID_TRANSPORT_TYPES

    def test_C_MAN_009_risk_level_must_be_canonical(self):
        """C-MAN-009: risk.level must be one of the five canonical values."""
        from uci.core.errors import UCIValidationError
        risk = UCIRisk(level="catastrophic")
        with pytest.raises(UCIValidationError):
            risk.validate()

    def test_C_MAN_010_manifest_serialises_and_deserialises(self, alpha):
        """C-MAN-010: A manifest MUST round-trip through to_dict/from_dict without loss."""
        original = alpha.build_manifest()
        d = original.to_dict()
        restored = UCIManifest.from_dict(d)
        assert restored.node.node_id == original.node.node_id
        assert restored.node.node_type == original.node.node_type
        assert len(restored.capabilities) == len(original.capabilities)
        assert len(restored.transports) == len(original.transports)

    def test_C_MAN_011_manifest_to_dict_includes_required_v01_blocks(self, alpha):
        """C-MAN-011: to_dict() MUST include all v0.1 top-level blocks."""
        d = alpha.manifest_dict()
        for block in ["uci_manifest_version", "node", "capabilities",
                      "transports", "governance", "compliance", "audit", "extensions"]:
            assert block in d, f"Missing block: {block}"

    def test_C_MAN_012_governance_default_action_policy_must_be_canonical(self):
        """C-MAN-012: governance.default_action_policy must be allow, deny, or defer."""
        from uci.core.errors import UCIValidationError
        gov = UCIGovernanceMeta(default_action_policy="always_allow_everything")
        with pytest.raises(UCIValidationError):
            gov.validate()


# ═════════════════════════════════════════════════════════════════════════════
# C-GOV — Governance Compliance
# ═════════════════════════════════════════════════════════════════════════════

class TestGovernanceCompliance:
    """
    C-GOV: A compliant UCI implementation MUST enforce governance fail-closed,
    deny by default, and never permit execution of untrusted nodes.
    """

    def test_C_GOV_001_unknown_trust_state_must_be_denied(self, policy, registry, audit, alpha):
        """C-GOV-001: Nodes in UNKNOWN trust state MUST be denied execution."""
        trust = TrustRecord(node_id="test", state=TrustState.UNKNOWN)
        alpha_manifest = alpha.build_manifest()
        decision = policy.evaluate_action(
            manifest=alpha_manifest,
            capability_id="document_search",
            action_id="search_index",
            trust=trust,
        )
        assert decision.outcome == GovernanceOutcome.DENY

    def test_C_GOV_002_revoked_node_must_be_denied(self, orchestrator, registry, alpha):
        """C-GOV-002: Revoked nodes MUST NOT execute actions under any circumstances."""
        orchestrator.connect(alpha)
        entry = registry.require("provider_alpha")
        entry.trust.transition(TrustState.REVOKED, reason="compliance test")

        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test"})
        assert not r.success
        assert r.state in {ResponseState.FAILED, ResponseState.DENIED}

    def test_C_GOV_003_suspended_node_must_be_denied(self, orchestrator, registry, alpha):
        """C-GOV-003: Suspended nodes MUST NOT execute actions."""
        orchestrator.connect(alpha)
        entry = registry.require("provider_alpha")
        entry.trust.transition(TrustState.SUSPENDED, reason="compliance test")

        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "test"})
        assert not r.success

    def test_C_GOV_004_missing_permissions_must_be_denied(self, policy, registry, audit, alpha, handshake):
        """C-GOV-004: Missing required permissions MUST produce a DENY outcome."""
        handshake.run("provider_alpha", alpha.manifest_dict())
        no_perms_policy = PolicyEngine(orchestrator_permissions=frozenset(), audit=audit)
        entry = registry.require("provider_alpha")
        decision = no_perms_policy.evaluate_action(
            manifest=entry.manifest,
            capability_id="document_search",
            action_id="search_index",
            trust=entry.trust,
        )
        assert decision.outcome == GovernanceOutcome.DENY

    def test_C_GOV_005_high_risk_action_must_be_deferred_without_confirmation(
        self, registry, audit, beta
    ):
        """C-GOV-005: High-risk actions without operator confirmation MUST be deferred."""
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        full_perms = DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"])
        p = PolicyEngine(orchestrator_permissions=full_perms, audit=audit)
        he = HandshakeEngine(policy=p, registry=registry, audit=audit)
        he.run("provider_beta", beta.manifest_dict())

        entry = registry.require("provider_beta")
        if entry.trust.state == TrustState.RESTRICTED:
            entry.trust.transition(TrustState.TRUSTED, granted_by="compliance_test")
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

    def test_C_GOV_006_governance_outcome_baked_into_response(self, orchestrator, alpha):
        """C-GOV-006: Every response MUST carry a governance snapshot."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r.governance is not None
        assert r.governance.outcome in {
            "allow", "allow_with_restrictions", "defer", "deny"
        }
        assert r.governance.trust_state in {s.value for s in TrustState}

    def test_C_GOV_007_invoke_never_raises_always_returns_envelope(
        self, orchestrator, alpha
    ):
        """C-GOV-007: orchestrator.invoke() MUST never raise — all outcomes are envelopes."""
        orchestrator.connect(alpha)
        # Trigger governance deny path
        r1 = orchestrator.invoke("provider_alpha", "nonexistent", "action")
        assert isinstance(r1, UCIResponse)

        # Trigger node-not-found path
        r2 = orchestrator.invoke("ghost_node", "cap", "act")
        assert isinstance(r2, UCIResponse)

        # Both are failures, but envelopes
        assert not r1.success
        assert not r2.success

    def test_C_GOV_008_operator_approval_elevates_deferred_to_allow(
        self, registry, audit, beta
    ):
        """C-GOV-008: Operator approval MUST convert DEFER to ALLOW."""
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        full_perms = DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"])
        p = PolicyEngine(orchestrator_permissions=full_perms, audit=audit)
        he = HandshakeEngine(policy=p, registry=registry, audit=audit)
        he.run("provider_beta", beta.manifest_dict())

        entry = registry.require("provider_beta")
        if entry.trust.state == TrustState.RESTRICTED:
            entry.trust.transition(TrustState.TRUSTED, granted_by="compliance_test")
        registry.mount_capability("provider_beta", "file_operations")

        deferred = p.evaluate_action(
            manifest=entry.manifest,
            capability_id="file_operations",
            action_id="delete_file",
            trust=entry.trust,
            caller_permissions=full_perms,
        )
        assert deferred.outcome == GovernanceOutcome.DEFER

        approved = p.operator_approve(deferred, operator_id="compliance_officer")
        assert approved.outcome == GovernanceOutcome.ALLOW

    def test_C_GOV_009_restricted_trust_allows_low_risk_actions(
        self, orchestrator, beta
    ):
        """C-GOV-009: RESTRICTED trust MUST permit low-risk actions."""
        orchestrator.connect(beta)
        r = orchestrator.invoke("provider_beta", "voice_tts", "synthesize",
                                {"text": "compliance test", "voice_id": "default"})
        assert r.success

    def test_C_GOV_010_every_governance_decision_generates_audit_event(
        self, orchestrator, audit, alpha
    ):
        """C-GOV-010: Every governance evaluation MUST produce at least one audit event."""
        count_before = audit.count()
        orchestrator.connect(alpha)
        count_after_connect = audit.count()
        assert count_after_connect > count_before

        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        count_after_invoke = audit.count()
        assert count_after_invoke > count_after_connect


# ═════════════════════════════════════════════════════════════════════════════
# C-HSK — Handshake Compliance
# ═════════════════════════════════════════════════════════════════════════════

class TestHandshakeCompliance:
    """
    C-HSK: A compliant UCI handshake MUST execute all stages in order,
    fail-closed on any error, and never mount an unvalidated node.
    """

    def test_C_HSK_001_compliant_node_reaches_ready(self, handshake, alpha):
        """C-HSK-001: A fully compliant node MUST reach HandshakeStage.READY."""
        result = handshake.run("provider_alpha", alpha.manifest_dict())
        assert result.success
        assert result.stage_reached == HandshakeStage.READY

    def test_C_HSK_002_malformed_manifest_fails_at_validation(self, handshake):
        """C-HSK-002: A malformed manifest MUST fail at manifest_validated stage."""
        result = handshake.run("bad_node", {"uci_manifest_version": "0.1",
                                            "node": {"node_id": ""}})
        assert not result.success
        assert result.stage_reached in {
            HandshakeStage.MANIFEST_VALIDATED, HandshakeStage.FAILED
        }

    def test_C_HSK_003_failed_node_must_not_be_registered(self, handshake, registry):
        """C-HSK-003: A node that fails handshake MUST NOT appear in the registry."""
        handshake.run("ghost", {"uci_manifest_version": "0.1",
                                "node": {"node_id": ""}})
        assert registry.get("ghost") is None

    def test_C_HSK_004_trust_must_be_verified_before_mounting(
        self, handshake, registry, alpha
    ):
        """C-HSK-004: Trust MUST reach at least VERIFIED before capabilities are mounted."""
        handshake.run("provider_alpha", alpha.manifest_dict())
        entry = registry.require("provider_alpha")
        assert entry.trust.state in EXECUTABLE_STATES

    def test_C_HSK_005_restricted_node_withholds_high_risk_capabilities(
        self, handshake, registry, beta
    ):
        """C-HSK-005: RESTRICTED trust MUST NOT mount capabilities with high-risk actions."""
        result = handshake.run("provider_beta", beta.manifest_dict())
        assert result.success
        assert result.trust_state == TrustState.RESTRICTED.value
        assert "file_operations" not in result.mounted_capabilities

    def test_C_HSK_006_handshake_generates_discovery_audit_event(
        self, handshake, audit, alpha
    ):
        """C-HSK-006: Handshake MUST emit node_discovered as its first event."""
        handshake.run("provider_alpha", alpha.manifest_dict())
        events = [r.event_type for r in audit.for_node("provider_alpha")]
        assert events[0] == AuditEvent.NODE_DISCOVERED

    def test_C_HSK_007_ready_node_emits_node_ready_event(
        self, handshake, audit, alpha
    ):
        """C-HSK-007: A successfully completed handshake MUST emit node_ready."""
        handshake.run("provider_alpha", alpha.manifest_dict())
        events = [r.event_type for r in audit.for_node("provider_alpha")]
        assert AuditEvent.NODE_READY in events

    def test_C_HSK_008_failed_handshake_emits_handshake_failed_event(
        self, handshake, audit
    ):
        """C-HSK-008: A failed handshake MUST emit handshake_failed."""
        handshake.run("bad_node", {"uci_manifest_version": "0.1",
                                   "node": {"node_id": ""}})
        events = [r.event_type for r in audit.all()]
        assert AuditEvent.HANDSHAKE_FAILED in events

    def test_C_HSK_009_handshake_result_never_raises(self, handshake):
        """C-HSK-009: HandshakeEngine.run() MUST never raise — all outcomes in result."""
        # Totally malformed input
        result = handshake.run("x", {"garbage": True})
        assert isinstance(result.success, bool)
        assert result.stage_reached is not None


# ═════════════════════════════════════════════════════════════════════════════
# C-RSP — Response Compliance
# ═════════════════════════════════════════════════════════════════════════════

class TestResponseCompliance:
    """
    C-RSP: Every UCI invocation MUST return a UCIResponse envelope.
    The envelope MUST carry identity, governance, and audit snapshots.
    """

    def test_C_RSP_001_every_invocation_returns_uci_response(
        self, orchestrator, alpha
    ):
        """C-RSP-001: orchestrator.invoke() MUST always return a UCIResponse."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert isinstance(r, UCIResponse)

    def test_C_RSP_002_response_version_is_correct(self, orchestrator, alpha):
        """C-RSP-002: uci_response_version MUST be '0.1'."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r.uci_response_version == RESPONSE_VERSION
        assert r.uci_response_version == "0.1"

    def test_C_RSP_003_successful_response_has_output_and_no_error(
        self, orchestrator, alpha
    ):
        """C-RSP-003: success=True MUST have output populated and error=None."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r.success is True
        assert r.output is not None
        assert r.error is None

    def test_C_RSP_004_failed_response_has_error_and_no_output(
        self, orchestrator, alpha
    ):
        """C-RSP-004: success=False MUST have error populated and output=None."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "nonexistent_cap", "act")
        assert r.success is False
        assert r.error is not None
        assert r.error.code
        assert r.output is None

    def test_C_RSP_005_deferred_response_has_deferred_state(
        self, registry, audit, beta
    ):
        """C-RSP-005: Governance-deferred invocation MUST produce state=deferred."""
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        full_perms = DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"])
        p = PolicyEngine(orchestrator_permissions=full_perms, audit=audit)
        orch = UCIOrchestrator(policy=p, registry=registry, audit=audit)
        he = HandshakeEngine(policy=p, registry=registry, audit=audit)
        he.run("provider_beta", beta.manifest_dict())
        orch._providers["provider_beta"] = beta

        entry = registry.require("provider_beta")
        entry.trust.transition(TrustState.TRUSTED, granted_by="compliance_test")
        registry.mount_capability("provider_beta", "file_operations")

        r = orch.invoke("provider_beta", "file_operations", "delete_file",
                        {"path": "/tmp/test.txt"})
        assert r.state == ResponseState.DEFERRED
        assert r.error.code == UCIErrorCode.CONFIRMATION_REQUIRED

    def test_C_RSP_006_response_carries_provider_identity(self, orchestrator, alpha):
        """C-RSP-006: Response MUST identify the node, capability, and action."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "document_search", "search_index",
                                {"query": "compliance"})
        assert r.provider.node_id == "provider_alpha"
        assert r.provider.capability_id == "document_search"
        assert r.provider.action_id == "search_index"

    def test_C_RSP_007_response_carries_invocation_id(self, orchestrator, alpha):
        """C-RSP-007: Response MUST have a unique invocation_id (UUID format)."""
        orchestrator.connect(alpha)
        r1 = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        r2 = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r1.invocation_id != r2.invocation_id
        assert len(r1.invocation_id) == 36

    def test_C_RSP_008_response_carries_timestamp(self, orchestrator, alpha):
        """C-RSP-008: Response MUST have a non-empty ISO-8601 timestamp."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert r.timestamp
        assert "T" in r.timestamp

    def test_C_RSP_009_assert_success_returns_output_on_success(
        self, orchestrator, alpha
    ):
        """C-RSP-009: assert_success() MUST return output on successful response."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        output = r.assert_success()
        assert output["status"] == "healthy"

    def test_C_RSP_010_assert_success_raises_on_failure(self, orchestrator, alpha):
        """C-RSP-010: assert_success() MUST raise UCIError on failed response."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "nonexistent", "act")
        with pytest.raises(UCIError):
            r.assert_success()

    def test_C_RSP_011_correlation_id_passthrough(self, orchestrator, alpha):
        """C-RSP-011: Caller-supplied correlation_id MUST appear in the response."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check",
                                correlation_id="trace-abc-123")
        assert r.correlation_id == "trace-abc-123"

    def test_C_RSP_012_response_roundtrips_through_json(self, orchestrator, alpha):
        """C-RSP-012: Response MUST survive a JSON wire trip with all fields intact."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        wire = r.to_json()
        r2 = UCIResponse.from_dict(json.loads(wire))
        assert r2.invocation_id == r.invocation_id
        assert r2.success == r.success
        assert r2.provider.node_id == r.provider.node_id
        assert r2.governance.outcome == r.governance.outcome


# ═════════════════════════════════════════════════════════════════════════════
# C-AUD — Audit Compliance
# ═════════════════════════════════════════════════════════════════════════════

class TestAuditCompliance:
    """
    C-AUD: A compliant UCI implementation MUST maintain an append-only,
    chain-hashed audit log that covers all lifecycle and governance events.
    """

    def test_C_AUD_001_audit_log_is_append_only(self, audit):
        """C-AUD-001: Records MUST be ordered by sequence and never removed mid-session."""
        audit.append(AuditEvent.NODE_DISCOVERED, "n1")
        audit.append(AuditEvent.TRUST_ASSIGNED, "n1")
        audit.append(AuditEvent.INVOCATION_COMPLETED, "n1")
        seqs = [r.sequence for r in audit.all()]
        assert seqs == sorted(seqs)
        assert seqs == list(range(1, len(seqs) + 1))

    def test_C_AUD_002_every_record_has_chain_hash(self, audit):
        """C-AUD-002: Every appended record MUST have a non-empty chain_hash."""
        for event in [AuditEvent.NODE_DISCOVERED, AuditEvent.TRUST_ASSIGNED,
                      AuditEvent.INVOCATION_COMPLETED]:
            audit.append(event, "node")
        for r in audit.all():
            assert r.chain_hash, f"Record {r.sequence} missing chain_hash"
            assert len(r.chain_hash) == 64

    def test_C_AUD_003_chain_integrity_passes_on_unmodified_log(
        self, orchestrator, audit, alpha
    ):
        """C-AUD-003: An unmodified audit log MUST pass integrity verification."""
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        report = audit.verify_integrity()
        assert report.valid
        assert report.breaks == []

    def test_C_AUD_004_chain_integrity_fails_on_tampered_record(self, audit):
        """C-AUD-004: Tampered records MUST be detected by verify_integrity()."""
        audit.append(AuditEvent.NODE_DISCOVERED, "n")
        r = audit.append(AuditEvent.TRUST_ASSIGNED, "n", outcome="allow")
        audit.append(AuditEvent.NODE_READY, "n")

        r.outcome = "deny"  # post-hoc tamper

        report = audit.verify_integrity()
        assert not report.valid
        assert len(report.breaks) >= 1

    def test_C_AUD_005_first_record_chains_from_genesis(self, audit):
        """C-AUD-005: The first record's previous_hash MUST equal GENESIS_HASH."""
        r = audit.append(AuditEvent.NODE_DISCOVERED, "n")
        assert r.previous_hash == GENESIS_HASH

    def test_C_AUD_006_consecutive_records_chain_correctly(self, audit):
        """C-AUD-006: Each record's previous_hash MUST equal the prior record's chain_hash."""
        records = []
        for event in [AuditEvent.NODE_DISCOVERED, AuditEvent.TRUST_ASSIGNED,
                      AuditEvent.NODE_READY, AuditEvent.INVOCATION_COMPLETED]:
            records.append(audit.append(event, "n"))

        for i in range(1, len(records)):
            assert records[i].previous_hash == records[i - 1].chain_hash

    def test_C_AUD_007_session_export_produces_canonical_envelope(
        self, orchestrator, audit, alpha
    ):
        """C-AUD-007: audit.export() MUST produce a UCIAuditSession."""
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        session = audit.export(seal=True)
        assert isinstance(session, UCIAuditSession)
        assert session.session_hash
        assert session.verify_session_hash()

    def test_C_AUD_008_session_survives_wire_round_trip(
        self, orchestrator, audit, alpha
    ):
        """C-AUD-008: A sealed session MUST survive JSON serialisation/deserialisation."""
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        session = audit.export(seal=True)
        wire = session.to_json()
        session2 = UCIAuditSession.from_json(wire)
        assert session2.verify_session_hash()
        assert len(session2.records) == len(session.records)

    def test_C_AUD_009_handshake_events_are_audited(self, handshake, audit, alpha):
        """C-AUD-009: Handshake lifecycle MUST generate a complete audit trail."""
        handshake.run("provider_alpha", alpha.manifest_dict())
        event_types = {r.event_type for r in audit.for_node("provider_alpha")}
        required = {
            AuditEvent.NODE_DISCOVERED,
            AuditEvent.MANIFEST_VALIDATION_PASSED,
            AuditEvent.TRUST_ASSIGNED,
            AuditEvent.NODE_READY,
        }
        assert required <= event_types, f"Missing events: {required - event_types}"

    def test_C_AUD_010_invocation_events_are_audited(
        self, orchestrator, audit, alpha
    ):
        """C-AUD-010: Every invocation MUST generate requested and completed events."""
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        event_types = {r.event_type for r in audit.all()}
        assert AuditEvent.INVOCATION_REQUESTED in event_types
        assert AuditEvent.INVOCATION_COMPLETED in event_types


# ═════════════════════════════════════════════════════════════════════════════
# C-SCH — Schema Compliance
# ═════════════════════════════════════════════════════════════════════════════

class TestSchemaCompliance:
    """
    C-SCH: All three canonical UCI objects MUST validate against their
    respective JSON Schemas. Schema compliance is language-agnostic —
    these schemas are the portable spec contract.
    """

    def test_C_SCH_001_compliant_manifest_passes_json_schema(self, alpha):
        """C-SCH-001: A compliant manifest MUST pass the UCI manifest JSON schema."""
        result = validate_manifest_schema(alpha.manifest_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_C_SCH_002_successful_response_passes_json_schema(
        self, orchestrator, alpha
    ):
        """C-SCH-002: A successful UCIResponse MUST pass the UCI response JSON schema."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        result = validate_response_schema(r.to_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_C_SCH_003_failure_response_passes_json_schema(
        self, orchestrator, alpha
    ):
        """C-SCH-003: A failure UCIResponse MUST pass the UCI response JSON schema."""
        orchestrator.connect(alpha)
        r = orchestrator.invoke("provider_alpha", "nonexistent", "act")
        result = validate_response_schema(r.to_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_C_SCH_004_deferred_response_passes_json_schema(
        self, registry, audit, beta
    ):
        """C-SCH-004: A deferred UCIResponse MUST pass the UCI response JSON schema."""
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        full_perms = DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"])
        p = PolicyEngine(orchestrator_permissions=full_perms, audit=audit)
        orch = UCIOrchestrator(policy=p, registry=registry, audit=audit)
        he = HandshakeEngine(policy=p, registry=registry, audit=audit)
        he.run("provider_beta", beta.manifest_dict())
        orch._providers["provider_beta"] = beta

        entry = registry.require("provider_beta")
        entry.trust.transition(TrustState.TRUSTED, granted_by="compliance_test")
        registry.mount_capability("provider_beta", "file_operations")

        r = orch.invoke("provider_beta", "file_operations", "delete_file",
                        {"path": "/tmp/test.txt"})
        result = validate_response_schema(r.to_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_C_SCH_005_audit_session_passes_json_schema(
        self, orchestrator, audit, alpha
    ):
        """C-SCH-005: A sealed UCIAuditSession MUST pass the UCI audit session JSON schema."""
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")
        session = audit.export(seal=True)
        result = validate_audit_session_schema(session.to_dict())
        assert result.valid, [i.message for i in result.issues]

    def test_C_SCH_006_all_three_objects_pass_in_single_session(
        self, orchestrator, audit, alpha
    ):
        """C-SCH-006: All three canonical objects MUST pass schema in a live session."""
        manifest_result  = validate_manifest_schema(alpha.manifest_dict())
        orchestrator.connect(alpha)
        resp             = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        response_result  = validate_response_schema(resp.to_dict())
        session          = audit.export(seal=True)
        audit_result     = validate_audit_session_schema(session.to_dict())

        assert manifest_result.valid,  [i.message for i in manifest_result.issues]
        assert response_result.valid,  [i.message for i in response_result.issues]
        assert audit_result.valid,     [i.message for i in audit_result.issues]

    def test_C_SCH_007_schema_rejects_legacy_execution_mode(self):
        """C-SCH-007: JSON Schema MUST reject 'stream' execution mode."""
        m = {
            "uci_manifest_version": "0.1",
            "node": {"node_id": "n", "instance_id": "i",
                     "node_type": "service", "version": "1.0.0"},
            "capabilities": [{"capability_id": "c", "version": "1.0",
                               "category": "retrieval",
                               "actions": [{"action_id": "a",
                                            "execution": {"mode": "stream", "timeout_ms": 1000},
                                            "risk": {"level": "low"},
                                            "permissions": {}}]}],
            "transports": [{"transport_id": "t", "type": "ipc", "endpoint": "x"}],
            "governance": {},
        }
        result = validate_manifest_schema(m)
        assert not result.valid

    def test_C_SCH_008_schema_rejects_legacy_transport_type(self):
        """C-SCH-008: JSON Schema MUST reject 'local' transport type."""
        m = {
            "uci_manifest_version": "0.1",
            "node": {"node_id": "n", "instance_id": "i",
                     "node_type": "service", "version": "1.0.0"},
            "capabilities": [{"capability_id": "c", "version": "1.0",
                               "category": "retrieval",
                               "actions": [{"action_id": "a",
                                            "execution": {"mode": "sync", "timeout_ms": 1000},
                                            "risk": {"level": "low"},
                                            "permissions": {}}]}],
            "transports": [{"transport_id": "t", "type": "local", "endpoint": "x"}],
            "governance": {},
        }
        result = validate_manifest_schema(m)
        assert not result.valid


# ═════════════════════════════════════════════════════════════════════════════
# C-INT — Integration (cross-cutting compliance)
# ═════════════════════════════════════════════════════════════════════════════

class TestIntegrationCompliance:
    """
    C-INT: Full end-to-end compliance — all three protocol objects working
    together in a live session, all constraints satisfied simultaneously.
    """

    def test_C_INT_001_full_session_all_constraints_satisfied(
        self, orchestrator, audit, alpha, beta
    ):
        """
        C-INT-001: A complete UCI session MUST satisfy all compliance
        constraints simultaneously:
        - Manifest validates
        - Handshake completes
        - Governance enforces correctly
        - Responses are enveloped
        - Audit is complete and chain-intact
        - All three objects pass JSON Schema
        """
        # 1. Manifest compliance
        assert validate_manifest_schema(alpha.manifest_dict()).valid

        # 2. Handshake compliance
        result = orchestrator.connect(alpha)
        assert result.success
        assert result.stage_reached == HandshakeStage.READY
        assert result.trust_state == TrustState.TRUSTED.value

        # 3. Governance compliance — allowed action
        r_ok = orchestrator.invoke("provider_alpha", "system_health", "health_check")
        assert isinstance(r_ok, UCIResponse)
        assert r_ok.success
        assert r_ok.governance.outcome in {"allow", "allow_with_restrictions"}

        # 4. Governance compliance — denied action
        r_denied = orchestrator.invoke("provider_alpha", "nonexistent", "act")
        assert isinstance(r_denied, UCIResponse)
        assert not r_denied.success
        assert r_denied.error is not None

        # 5. Response schema compliance
        assert validate_response_schema(r_ok.to_dict()).valid
        assert validate_response_schema(r_denied.to_dict()).valid

        # 6. Audit compliance
        integrity = audit.verify_integrity()
        assert integrity.valid

        # 7. Audit session schema compliance
        session = audit.export(seal=True)
        assert validate_audit_session_schema(session.to_dict()).valid
        assert session.verify_session_hash()

        # 8. Wire-trip survival
        wire = session.to_json()
        session2 = UCIAuditSession.from_json(wire)
        assert session2.verify_session_hash()
        assert len(session2.records) == len(session.records)

    def test_C_INT_002_restricted_node_session_compliant(
        self, orchestrator, audit, beta
    ):
        """
        C-INT-002: A restricted-trust node session MUST also satisfy all
        compliance constraints — restricted is a valid operating state,
        not a failure state.
        """
        # Manifest valid
        assert validate_manifest_schema(beta.manifest_dict()).valid

        # Handshake: reaches READY as RESTRICTED
        result = orchestrator.connect(beta)
        assert result.success
        assert result.trust_state == TrustState.RESTRICTED.value
        assert "file_operations" not in result.mounted_capabilities  # high-risk withheld

        # Allowed low-risk action
        r = orchestrator.invoke("provider_beta", "voice_tts", "synthesize",
                                {"text": "compliance", "voice_id": "default"})
        assert r.success
        assert validate_response_schema(r.to_dict()).valid

        # Audit intact
        assert audit.verify_integrity().valid
