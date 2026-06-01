"""
UCIAuditSession and chain integrity tests — Patch 4.

Covers: record serialisation, chain hashing, tamper detection,
        session export/import, session hash, querying on sessions.
"""

import json
import copy
import pytest

from uci.core.audit import (
    AuditLog, AuditRecord, AuditEvent,
    UCIAuditSession, IntegrityReport,
    GENESIS_HASH, _compute_record_hash,
)


# ── AuditRecord serialisation ─────────────────────────────────────────────────

class TestAuditRecordSerialisation:
    def _record(self):
        log = AuditLog()
        return log.append(AuditEvent.NODE_DISCOVERED, "test_node",
                          actor="engine", outcome="")

    def test_to_dict_has_required_keys(self):
        r = self._record()
        d = r.to_dict()
        for key in ["event_id", "sequence", "event_type", "node_id",
                    "timestamp", "actor", "outcome", "detail",
                    "previous_hash", "chain_hash"]:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_values_correct(self):
        r = self._record()
        d = r.to_dict()
        assert d["event_type"] == AuditEvent.NODE_DISCOVERED
        assert d["node_id"] == "test_node"
        assert d["actor"] == "engine"
        assert d["sequence"] == 1

    def test_from_dict_roundtrip(self):
        r = self._record()
        d = r.to_dict()
        r2 = AuditRecord.from_dict(d)
        assert r2.event_id    == r.event_id
        assert r2.sequence    == r.sequence
        assert r2.event_type  == r.event_type
        assert r2.node_id     == r.node_id
        assert r2.chain_hash  == r.chain_hash
        assert r2.previous_hash == r.previous_hash


# ── Chain hashing ─────────────────────────────────────────────────────────────

class TestChainHashing:
    def test_first_record_uses_genesis_hash(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n")
        assert r.previous_hash == GENESIS_HASH

    def test_second_record_uses_first_hash(self):
        log = AuditLog()
        r1 = log.append(AuditEvent.NODE_DISCOVERED, "n")
        r2 = log.append(AuditEvent.MANIFEST_RETRIEVED, "n")
        assert r2.previous_hash == r1.chain_hash

    def test_chain_hashes_are_unique(self):
        log = AuditLog()
        hashes = set()
        for i in range(10):
            r = log.append(AuditEvent.INVOCATION_COMPLETED, f"node_{i}")
            hashes.add(r.chain_hash)
        assert len(hashes) == 10  # all distinct

    def test_chain_hash_is_64_chars(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n")
        assert len(r.chain_hash) == 64

    def test_record_verify_passes_on_untampered(self):
        log = AuditLog()
        log.append(AuditEvent.NODE_DISCOVERED, "n")
        r2 = log.append(AuditEvent.MANIFEST_RETRIEVED, "n")
        assert r2.verify(r2.previous_hash)

    def test_record_verify_fails_on_wrong_prev_hash(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n")
        assert not r.verify("wrong_hash_" + "0" * 53)


# ── Integrity verification ────────────────────────────────────────────────────

class TestIntegrityVerification:
    def test_empty_log_is_valid(self):
        log = AuditLog()
        report = log.verify_integrity()
        assert report.valid
        assert report.total_records == 0
        assert report.breaks == []

    def test_unmodified_log_passes(self):
        log = AuditLog()
        for i in range(5):
            log.append(AuditEvent.NODE_DISCOVERED, f"node_{i}")
        report = log.verify_integrity()
        assert report.valid
        assert report.total_records == 5

    def test_tampered_record_fails(self):
        log = AuditLog()
        log.append(AuditEvent.NODE_DISCOVERED, "node_a")
        r2 = log.append(AuditEvent.MANIFEST_RETRIEVED, "node_a")
        log.append(AuditEvent.NODE_READY, "node_a")

        # Tamper with r2 after the fact
        r2.outcome = "forged_outcome"
        # chain_hash is now stale — verify should catch it

        report = log.verify_integrity()
        assert not report.valid
        assert len(report.breaks) >= 1

    def test_tampered_node_id_fails(self):
        log = AuditLog()
        r1 = log.append(AuditEvent.NODE_DISCOVERED, "real_node")
        r1.node_id = "attacker_node"  # tamper

        report = log.verify_integrity()
        assert not report.valid

    def test_integrity_report_to_dict(self):
        log = AuditLog()
        log.append(AuditEvent.NODE_DISCOVERED, "n")
        report = log.verify_integrity()
        d = report.to_dict()
        assert "valid" in d
        assert "total_records" in d
        assert "breaks" in d
        assert "checked_at" in d

    def test_integrity_report_str_valid(self):
        log = AuditLog()
        log.append(AuditEvent.NODE_DISCOVERED, "n")
        report = log.verify_integrity()
        assert "OK" in str(report)

    def test_integrity_report_str_invalid(self):
        log = AuditLog()
        r = log.append(AuditEvent.NODE_DISCOVERED, "n")
        r.outcome = "tampered"
        report = log.verify_integrity()
        assert "FAILED" in str(report)


# ── UCIAuditSession ───────────────────────────────────────────────────────────

class TestUCIAuditSession:
    def _populated_log(self) -> AuditLog:
        log = AuditLog(orchestrator_id="test_orchestrator")
        log.append(AuditEvent.NODE_DISCOVERED, "provider_alpha", actor="engine")
        log.append(AuditEvent.MANIFEST_VALIDATION_PASSED, "provider_alpha", actor="engine")
        log.append(AuditEvent.TRUST_ASSIGNED, "provider_alpha", actor="policy_engine",
                   outcome="", trust_state="trusted")
        log.append(AuditEvent.INVOCATION_COMPLETED, "provider_alpha", actor="orchestrator",
                   outcome="success", capability_id="doc_search", action_id="search")
        return log

    def test_export_produces_session(self):
        log = self._populated_log()
        session = log.export()
        assert isinstance(session, UCIAuditSession)

    def test_session_has_correct_record_count(self):
        log = self._populated_log()
        session = log.export()
        assert len(session.records) == 4

    def test_session_id_matches_log(self):
        log = self._populated_log()
        session = log.export()
        assert session.session_id == log.session_id

    def test_orchestrator_id_preserved(self):
        log = self._populated_log()
        session = log.export()
        assert session.orchestrator_id == "test_orchestrator"

    def test_sealed_session_has_hash(self):
        session = self._populated_log().export(seal=True)
        assert session.session_hash
        assert len(session.session_hash) == 64

    def test_sealed_session_has_closed_at(self):
        session = self._populated_log().export(seal=True)
        assert session.closed_at is not None

    def test_unsealed_session_has_no_hash(self):
        session = self._populated_log().export(seal=False)
        assert not session.session_hash

    def test_session_hash_verifies(self):
        session = self._populated_log().export(seal=True)
        assert session.verify_session_hash()

    def test_tampered_session_hash_fails(self):
        session = self._populated_log().export(seal=True)
        session.session_hash = "a" * 64   # forge it
        assert not session.verify_session_hash()


# ── UCIAuditSession serialisation ────────────────────────────────────────────

class TestSessionSerialisation:
    def _session(self) -> UCIAuditSession:
        log = AuditLog(orchestrator_id="orch_001")
        log.append(AuditEvent.NODE_DISCOVERED, "provider_alpha")
        log.append(AuditEvent.INVOCATION_COMPLETED, "provider_alpha",
                   outcome="success", capability_id="cap", action_id="act")
        return log.export(seal=True)

    def test_to_dict_top_level_keys(self):
        d = self._session().to_dict()
        for key in ["uci_audit_version", "session_id", "orchestrator_id",
                    "opened_at", "closed_at", "session_hash",
                    "record_count", "records"]:
            assert key in d, f"Missing key: {key}"

    def test_record_count_matches_records(self):
        d = self._session().to_dict()
        assert d["record_count"] == len(d["records"])

    def test_to_json_is_valid_json(self):
        j = self._session().to_json()
        parsed = json.loads(j)
        assert parsed["uci_audit_version"] == "0.1"

    def test_from_dict_roundtrip(self):
        s = self._session()
        s2 = UCIAuditSession.from_dict(s.to_dict())
        assert s2.session_id == s.session_id
        assert s2.session_hash == s.session_hash
        assert len(s2.records) == len(s.records)
        assert s2.records[0].event_id == s.records[0].event_id

    def test_from_json_roundtrip(self):
        s = self._session()
        j = s.to_json()
        s2 = UCIAuditSession.from_json(j)
        assert s2.session_id == s.session_id
        assert s2.verify_session_hash()

    def test_chain_survives_roundtrip(self):
        """After roundtrip, the original chain hashes should still verify."""
        s = self._session()
        s2 = UCIAuditSession.from_dict(s.to_dict())
        prev = GENESIS_HASH
        for r in s2.records:
            assert r.verify(prev), f"Chain broken at sequence {r.sequence}"
            prev = r.chain_hash


# ── Session querying ──────────────────────────────────────────────────────────

class TestSessionQuerying:
    def _session(self) -> UCIAuditSession:
        log = AuditLog()
        log.append(AuditEvent.NODE_DISCOVERED, "node_a")
        log.append(AuditEvent.NODE_DISCOVERED, "node_b")
        log.append(AuditEvent.INVOCATION_COMPLETED, "node_a",
                   outcome="success")
        log.append(AuditEvent.PERMISSION_DENIED, "node_b",
                   outcome="deny")
        return log.export()

    def test_for_node(self):
        s = self._session()
        records = s.for_node("node_a")
        assert all(r.node_id == "node_a" for r in records)
        assert len(records) == 2

    def test_by_event(self):
        s = self._session()
        records = s.by_event(AuditEvent.NODE_DISCOVERED)
        assert len(records) == 2

    def test_denials(self):
        s = self._session()
        denials = s.denials()
        assert len(denials) == 1
        assert denials[0].node_id == "node_b"

    def test_summary_keys(self):
        s = self._session()
        summary = s.summary()
        for key in ["session_id", "record_count", "events",
                    "outcomes", "nodes_seen", "session_hash"]:
            assert key in summary


# ── Integration: full orchestrator session ────────────────────────────────────

class TestAuditSessionIntegration:
    def test_orchestrator_session_exports_and_verifies(
        self, orchestrator, audit, alpha
    ):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "document_search", "search_index",
                            {"query": "UCI"})
        orchestrator.invoke("provider_alpha", "system_health", "health_check")

        session = audit.export(seal=True)
        assert len(session.records) > 0
        assert session.verify_session_hash()

    def test_exported_session_chain_is_intact(
        self, orchestrator, audit, alpha
    ):
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "document_search", "search_index",
                            {"query": "test"})

        integrity = audit.verify_integrity()
        assert integrity.valid

        session = audit.export(seal=True)
        prev = GENESIS_HASH
        for r in session.records:
            assert r.verify(prev), f"Chain broken at seq {r.sequence}"
            prev = r.chain_hash

    def test_session_json_survives_wire_trip(
        self, orchestrator, audit, alpha
    ):
        """Simulate exporting, sending over wire (JSON), and reimporting."""
        orchestrator.connect(alpha)
        orchestrator.invoke("provider_alpha", "system_health", "health_check")

        session = audit.export(seal=True)
        wire = session.to_json()

        session2 = UCIAuditSession.from_json(wire)
        assert session2.verify_session_hash()
        assert len(session2.records) == len(session.records)
