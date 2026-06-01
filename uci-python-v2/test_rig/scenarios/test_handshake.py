"""
Handshake lifecycle tests.
Verifies that the 9-stage handshake progresses correctly for
compliant, restricted, and malformed nodes.
"""

import pytest
from uci.core.handshake import HandshakeStage
from uci.core.trust import TrustState


class TestHandshakeAlpha:
    """Happy path — fully compliant provider."""

    def test_handshake_succeeds(self, handshake, alpha):
        result = handshake.run("provider_alpha", alpha.manifest_dict())
        assert result.success, result.failure_reason

    def test_reaches_ready_stage(self, handshake, alpha):
        result = handshake.run("provider_alpha", alpha.manifest_dict())
        assert result.stage_reached == HandshakeStage.READY

    def test_trust_is_trusted(self, handshake, alpha):
        result = handshake.run("provider_alpha", alpha.manifest_dict())
        assert result.trust_state == TrustState.TRUSTED.value

    def test_capabilities_mounted(self, handshake, alpha):
        result = handshake.run("provider_alpha", alpha.manifest_dict())
        assert "document_search" in result.mounted_capabilities
        assert "system_health" in result.mounted_capabilities

    def test_node_registered(self, handshake, registry, alpha):
        handshake.run("provider_alpha", alpha.manifest_dict())
        entry = registry.get("provider_alpha")
        assert entry is not None
        assert entry.is_ready()

    def test_audit_events_generated(self, handshake, audit, alpha):
        handshake.run("provider_alpha", alpha.manifest_dict())
        event_types = [r.event_type for r in audit.all()]
        assert "node_discovered"            in event_types
        assert "manifest_validation_passed" in event_types
        assert "compatibility_accepted"     in event_types
        assert "trust_assigned"             in event_types
        assert "capability_mounted"         in event_types
        assert "node_ready"                 in event_types


class TestHandshakeBeta:
    """Restricted trust — operator_authority_required = True."""

    def test_handshake_succeeds(self, handshake, beta):
        result = handshake.run("provider_beta", beta.manifest_dict())
        assert result.success, result.failure_reason

    def test_trust_is_restricted(self, handshake, beta):
        result = handshake.run("provider_beta", beta.manifest_dict())
        assert result.trust_state == TrustState.RESTRICTED.value

    def test_low_risk_capability_mounted(self, handshake, beta):
        result = handshake.run("provider_beta", beta.manifest_dict())
        assert "voice_tts" in result.mounted_capabilities

    def test_high_risk_capability_not_mounted(self, handshake, beta):
        result = handshake.run("provider_beta", beta.manifest_dict())
        assert "file_operations" not in result.mounted_capabilities

    def test_warning_issued_for_unmounted_capability(self, handshake, beta):
        result = handshake.run("provider_beta", beta.manifest_dict())
        assert any("file_operations" in w for w in result.warnings)


class TestHandshakeGamma:
    """Fail-closed behaviour on malformed / bad-actor nodes."""

    def test_missing_node_id_fails(self, handshake, gamma_missing_id):
        result = handshake.run("gamma_missing_id", gamma_missing_id.manifest_dict())
        assert not result.success
        assert result.stage_reached == HandshakeStage.MANIFEST_VALIDATED

    def test_unsupported_version_fails(self, handshake, gamma_bad_version):
        result = handshake.run("gamma_bad_version", gamma_bad_version.manifest_dict())
        assert not result.success
        # Version is checked inside validate() which runs at MANIFEST_VALIDATED stage
        assert result.stage_reached in {HandshakeStage.MANIFEST_VALIDATED, HandshakeStage.COMPATIBILITY_CHECKED}

    def test_invalid_risk_level_fails(self, handshake, gamma_invalid_risk):
        result = handshake.run("gamma_invalid_risk", gamma_invalid_risk.manifest_dict())
        assert not result.success

    def test_invalid_node_type_fails(self, handshake, gamma_invalid_type):
        result = handshake.run("gamma_invalid_type", gamma_invalid_type.manifest_dict())
        assert not result.success

    def test_failed_nodes_not_registered(self, handshake, registry, gamma_missing_id):
        handshake.run("gamma_missing_id", gamma_missing_id.manifest_dict())
        assert registry.get("gamma_missing_id") is None

    def test_failure_generates_audit_denial(self, handshake, audit, gamma_missing_id):
        handshake.run("gamma_missing_id", gamma_missing_id.manifest_dict())
        denials = [r for r in audit.all() if r.outcome == "deny"]
        assert len(denials) > 0

    def test_empty_capabilities_node_fails_closed(self, handshake, gamma_no_caps):
        result = handshake.run("provider_gamma_empty", gamma_no_caps.manifest_dict())
        assert not result.success
        assert result.stage_reached == HandshakeStage.MANIFEST_VALIDATED
        assert "at least one capability" in result.failure_reason
