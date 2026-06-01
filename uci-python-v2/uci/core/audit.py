"""
UCI Audit Log  —  uci/core/audit.py
=====================================
Append-only, ordered event trace for all governance and lifecycle decisions.

Patch 4 additions
-----------------
- AuditRecord.to_dict() / from_dict()  — records are now portable
- Chain hashing — each record seals itself against the previous,
  making post-hoc tampering detectable via verify_integrity()
- UCIAuditSession — canonical serialisable envelope for an entire
  audit session, exportable to / importable from JSON
- AuditLog.export() — produces a UCIAuditSession
- AuditLog.verify_integrity() — walks the chain and reports breaks
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ─────────────────────────────────────────────
# Canonical event type constants
# ─────────────────────────────────────────────

class AuditEvent:
    # Discovery / handshake
    NODE_DISCOVERED             = "node_discovered"
    MANIFEST_RETRIEVED          = "manifest_retrieved"
    MANIFEST_VALIDATION_PASSED  = "manifest_validation_passed"
    MANIFEST_VALIDATION_FAILED  = "manifest_validation_failed"
    COMPATIBILITY_ACCEPTED      = "compatibility_accepted"
    COMPATIBILITY_REJECTED      = "compatibility_rejected"
    TRUST_ASSIGNED              = "trust_assigned"
    TRUST_TRANSITION            = "trust_transition"
    CAPABILITY_MOUNTED          = "capability_mounted"
    CAPABILITY_REVOKED          = "capability_revoked"
    NODE_READY                  = "node_ready"
    NODE_SUSPENDED              = "node_suspended"
    NODE_REVOKED                = "node_revoked"
    HANDSHAKE_FAILED            = "handshake_failed"

    # Governance
    POLICY_EVALUATED            = "policy_evaluated"
    PERMISSION_DENIED           = "permission_denied"
    TRUST_REJECTED              = "trust_rejected"
    CONFIRMATION_REQUESTED      = "confirmation_requested"
    CONFIRMATION_APPROVED       = "confirmation_approved"
    CONFIRMATION_DENIED         = "confirmation_denied"
    EXECUTION_ALLOWED           = "execution_allowed"
    EXECUTION_DENIED            = "execution_denied"
    EXECUTION_RESTRICTED        = "execution_restricted"

    # Invocation
    INVOCATION_REQUESTED        = "invocation_requested"
    INVOCATION_COMPLETED        = "invocation_completed"
    INVOCATION_FAILED           = "invocation_failed"

    # Session
    SESSION_OPENED              = "session_opened"
    SESSION_CLOSED              = "session_closed"


AUDIT_VERSION = "0.1"

# ─────────────────────────────────────────────
# Chain hashing helpers
# ─────────────────────────────────────────────

GENESIS_HASH = "0" * 64   # sentinel hash for the first record


def _compute_record_hash(record_dict: dict, previous_hash: str) -> str:
    """
    SHA-256 of (previous_hash + canonical JSON of record fields).
    The hash covers: sequence, event_id, event_type, node_id,
    timestamp, actor, outcome, detail — not the hash field itself.
    """
    payload = {
        "previous_hash": previous_hash,
        "sequence":      record_dict["sequence"],
        "event_id":      record_dict["event_id"],
        "event_type":    record_dict["event_type"],
        "node_id":       record_dict["node_id"],
        "timestamp":     record_dict["timestamp"],
        "actor":         record_dict["actor"],
        "outcome":       record_dict["outcome"],
        "detail":        record_dict["detail"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ─────────────────────────────────────────────
# AuditRecord
# ─────────────────────────────────────────────

AUDIT_EVENT_VERSION = "0.1"


@dataclass
class AuditRecord:
    event_type:          str
    node_id:             str
    timestamp:           str  = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id:            str  = field(default_factory=lambda: str(uuid.uuid4()))
    actor:               str  = ""
    outcome:             str  = ""
    detail:              dict[str, Any] = field(default_factory=dict)
    sequence:            int  = 0
    chain_hash:          str  = ""
    previous_hash:       str  = ""
    # Spec-required fields (uci_audit_observability_model_v0_1 §7)
    audit_event_version: str  = AUDIT_EVENT_VERSION
    correlation_id:      str  = ""
    severity:            str  = "info"
    source:              dict[str, Any] = field(default_factory=dict)

    def seal(self, previous_hash: str) -> None:
        """Compute and store this record's chain hash."""
        self.previous_hash = previous_hash
        self.chain_hash = _compute_record_hash(self.to_dict(), previous_hash)

    def verify(self, previous_hash: str) -> bool:
        """Return True if this record's hash is consistent with previous_hash."""
        expected = _compute_record_hash(self.to_dict(), previous_hash)
        return self.chain_hash == expected

    # ── Serialisation ────────────────────────────

    def to_dict(self) -> dict:
        return {
            "audit_event_version": self.audit_event_version,
            "event_id":            self.event_id,
            "sequence":            self.sequence,
            "event_type":          self.event_type,
            "node_id":             self.node_id,
            "timestamp":           self.timestamp,
            "actor":               self.actor,
            "outcome":             self.outcome,
            "severity":            self.severity,
            "correlation_id":      self.correlation_id,
            "source":              self.source,
            "detail":              self.detail,
            "previous_hash":       self.previous_hash,
            "chain_hash":          self.chain_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditRecord":
        return cls(
            audit_event_version = data.get("audit_event_version", AUDIT_EVENT_VERSION),
            event_id            = data.get("event_id", str(uuid.uuid4())),
            sequence            = data.get("sequence", 0),
            event_type          = data.get("event_type", ""),
            node_id             = data.get("node_id", ""),
            timestamp           = data.get("timestamp", ""),
            actor               = data.get("actor", ""),
            outcome             = data.get("outcome", ""),
            severity            = data.get("severity", "info"),
            correlation_id      = data.get("correlation_id", ""),
            source              = data.get("source", {}),
            detail              = data.get("detail", {}),
            previous_hash       = data.get("previous_hash", ""),
            chain_hash          = data.get("chain_hash", ""),
        )


# ─────────────────────────────────────────────
# Chain integrity report
# ─────────────────────────────────────────────

@dataclass
class IntegrityReport:
    valid:        bool
    total_records: int
    breaks:       list[dict]   # list of {sequence, event_id, reason}
    checked_at:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "valid":         self.valid,
            "total_records": self.total_records,
            "breaks":        self.breaks,
            "checked_at":    self.checked_at,
        }

    def __str__(self) -> str:
        if self.valid:
            return f"Integrity OK — {self.total_records} records verified."
        return (
            f"Integrity FAILED — {len(self.breaks)} break(s) "
            f"in {self.total_records} records."
        )


# ─────────────────────────────────────────────
# UCIAuditSession — canonical session envelope
# ─────────────────────────────────────────────

@dataclass
class UCIAuditSession:
    """
    Canonical serialisable envelope for a complete audit session.
    Equivalent role to UCIManifest (identity) and UCIResponse (answer)
    — this is the portable, verifiable record of everything that happened.
    """
    uci_audit_version:  str = AUDIT_VERSION
    session_id:         str = field(default_factory=lambda: str(uuid.uuid4()))
    orchestrator_id:    str = ""
    opened_at:          str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at:          Optional[str] = None
    records:            list[AuditRecord] = field(default_factory=list)
    session_hash:       str = ""   # SHA-256 of the final chain_hash + session_id

    # ── Session hash ─────────────────────────────

    def seal_session(self) -> None:
        """Compute and store the session-level hash."""
        tail_hash = self.records[-1].chain_hash if self.records else GENESIS_HASH
        payload = f"{self.session_id}:{tail_hash}"
        self.session_hash = hashlib.sha256(payload.encode()).hexdigest()
        self.closed_at = datetime.now(timezone.utc).isoformat()

    def verify_session_hash(self) -> bool:
        if not self.records:
            return True
        tail_hash = self.records[-1].chain_hash
        payload = f"{self.session_id}:{tail_hash}"
        expected = hashlib.sha256(payload.encode()).hexdigest()
        return self.session_hash == expected

    # ── Serialisation ────────────────────────────

    def to_dict(self) -> dict:
        return {
            "uci_audit_version": self.uci_audit_version,
            "session_id":        self.session_id,
            "orchestrator_id":   self.orchestrator_id,
            "opened_at":         self.opened_at,
            "closed_at":         self.closed_at,
            "session_hash":      self.session_hash,
            "record_count":      len(self.records),
            "records":           [r.to_dict() for r in self.records],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> "UCIAuditSession":
        records = [AuditRecord.from_dict(r) for r in data.get("records", [])]
        return cls(
            uci_audit_version = data.get("uci_audit_version", AUDIT_VERSION),
            session_id        = data.get("session_id", str(uuid.uuid4())),
            orchestrator_id   = data.get("orchestrator_id", ""),
            opened_at         = data.get("opened_at", ""),
            closed_at         = data.get("closed_at"),
            records           = records,
            session_hash      = data.get("session_hash", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "UCIAuditSession":
        return cls.from_dict(json.loads(json_str))

    # ── Querying ─────────────────────────────────

    def for_node(self, node_id: str) -> list[AuditRecord]:
        return [r for r in self.records if r.node_id == node_id]

    def by_event(self, event_type: str) -> list[AuditRecord]:
        return [r for r in self.records if r.event_type == event_type]

    def denials(self) -> list[AuditRecord]:
        return [r for r in self.records if r.outcome == "deny"]

    def summary(self) -> dict:
        event_counts   = Counter(r.event_type for r in self.records)
        outcome_counts = Counter(r.outcome for r in self.records if r.outcome)
        return {
            "session_id":    self.session_id,
            "record_count":  len(self.records),
            "events":        dict(event_counts),
            "outcomes":      dict(outcome_counts),
            "nodes_seen":    list({r.node_id for r in self.records}),
            "session_hash":  self.session_hash[:12] + "..." if self.session_hash else "",
        }


# ─────────────────────────────────────────────
# AuditLog — upgraded
# ─────────────────────────────────────────────

@dataclass
class AuditLog:
    """
    Append-only ordered log of all UCI lifecycle and governance events.

    Patch 4: records are now chain-hashed on append, the log can export
    a portable UCIAuditSession, and integrity can be verified at any time.
    """
    _records:      list[AuditRecord] = field(default_factory=list)
    _counter:      int               = field(default=0, repr=False)
    _last_hash:    str               = field(default=GENESIS_HASH, repr=False)
    session_id:    str               = field(default_factory=lambda: str(uuid.uuid4()))
    orchestrator_id: str             = ""

    def append(
        self,
        event_type: str,
        node_id: str,
        actor: str = "uci_engine",
        outcome: str = "",
        severity: str = "info",
        correlation_id: str = "",
        source: Optional[dict] = None,
        **detail: Any,
    ) -> AuditRecord:
        self._counter += 1
        record = AuditRecord(
            event_type     = event_type,
            node_id        = node_id,
            actor          = actor,
            outcome        = outcome,
            severity       = severity,
            correlation_id = correlation_id,
            source         = source or {"node_id": actor},
            detail         = dict(detail),
            sequence       = self._counter,
        )
        record.seal(self._last_hash)
        self._last_hash = record.chain_hash
        self._records.append(record)
        return record

    # ── Integrity ────────────────────────────────

    def verify_integrity(self) -> IntegrityReport:
        """
        Walk every record and verify the chain hash is unbroken.
        Returns an IntegrityReport — does not raise.
        """
        breaks = []
        prev_hash = GENESIS_HASH

        for record in self._records:
            if not record.verify(prev_hash):
                breaks.append({
                    "sequence":  record.sequence,
                    "event_id":  record.event_id,
                    "reason":    "chain_hash mismatch — record may have been tampered with",
                })
            prev_hash = record.chain_hash

        return IntegrityReport(
            valid         = len(breaks) == 0,
            total_records = len(self._records),
            breaks        = breaks,
        )

    # ── Session export ───────────────────────────

    def export(self, seal: bool = True) -> UCIAuditSession:
        """
        Export the current log as a portable UCIAuditSession.
        If seal=True, computes and stores the session-level hash.
        """
        session = UCIAuditSession(
            session_id      = self.session_id,
            orchestrator_id = self.orchestrator_id,
            records         = list(self._records),
        )
        if seal:
            session.seal_session()
        return session

    # ── Accessors (unchanged API) ────────────────

    def all(self) -> list[AuditRecord]:
        return list(self._records)

    def for_node(self, node_id: str) -> list[AuditRecord]:
        return [r for r in self._records if r.node_id == node_id]

    def by_event(self, event_type: str) -> list[AuditRecord]:
        return [r for r in self._records if r.event_type == event_type]

    def count(self) -> int:
        return len(self._records)

    def last(self, n: int = 10) -> list[AuditRecord]:
        return self._records[-n:]

    def denials(self) -> list[AuditRecord]:
        return [r for r in self._records if r.outcome == "deny"]

    def summary(self) -> dict:
        event_counts   = Counter(r.event_type for r in self._records)
        outcome_counts = Counter(r.outcome for r in self._records if r.outcome)
        return {
            "total_events": self.count(),
            "events":       dict(event_counts),
            "outcomes":     dict(outcome_counts),
            "nodes_seen":   list({r.node_id for r in self._records}),
        }

    def render(self, last_n: Optional[int] = None) -> str:
        """Human-readable audit trail for the terminal demo."""
        records = self._records if last_n is None else self._records[-last_n:]
        lines = []
        for r in records:
            outcome_tag = f" [{r.outcome.upper()}]" if r.outcome else ""
            detail_str = ""
            if r.detail:
                parts = [f"{k}={v!r}" for k, v in r.detail.items()]
                detail_str = "  " + " | ".join(parts)
            lines.append(
                f"  #{r.sequence:03d} {r.timestamp[11:19]}  "
                f"{r.event_type:<38} node={r.node_id!r:<30}{outcome_tag}{detail_str}"
            )
        return "\n".join(lines)
