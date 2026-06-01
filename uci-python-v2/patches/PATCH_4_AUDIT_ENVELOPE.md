# UCI Patch 4 — Canonical Audit Envelope

## Purpose

Promote the audit log to a first-class protocol object alongside
UCIManifest (identity) and UCIResponse (answer). The audit is now
the verifiable, portable record of everything that happened.

## New Capabilities

### Chain hashing
Every AuditRecord is sealed on append with a SHA-256 hash that
covers its own fields plus the previous record's hash — forming
a tamper-evident chain. Modifying any field after the fact breaks
the chain at that point, detectable via verify_integrity().

### UCIAuditSession
A canonical serialisable envelope for an entire audit session:
- Exports to / imports from JSON
- Carries a session-level hash (SHA-256 of session_id + tail record hash)
- Survives a full wire round-trip with chain intact
- Queryable: for_node(), by_event(), denials(), summary()

### IntegrityReport
Returned by AuditLog.verify_integrity() — structured report
of any chain breaks, with sequence number and reason.

## API

```python
# Export session
session = audit.export(seal=True)   # UCIAuditSession
json_str = session.to_json()

# Import / verify
session2 = UCIAuditSession.from_json(json_str)
assert session2.verify_session_hash()

# Check integrity
report = audit.verify_integrity()   # IntegrityReport
assert report.valid
```

## Changed Files

- `uci/core/audit.py` — AuditRecord gains chain_hash, seal(), verify();
  AuditLog gains verify_integrity(), export(); UCIAuditSession added

## New Files

- `test_rig/scenarios/test_audit_envelope.py` — 38 new tests

## Test Result

```
179 passed (141 existing + 38 new)
0 failed
```
