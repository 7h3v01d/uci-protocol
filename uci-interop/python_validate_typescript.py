#!/usr/bin/env python3
"""
UCI Interoperability Test — Python Validator
============================================
Validates JSON produced by the TypeScript implementation.
Uses Python's UCI stack — schema validator, manifest parser,
response parser, audit session importer, chain verifier.

Pass criteria:
  - All objects pass JSON Schema (uci-spec.org)
  - All objects deserialise without error
  - Manifest passes semantic validation
  - Audit session chain hash is intact
  - Audit session session hash is valid
  - Response objects have correct structure
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "uci-python-v2"))

from uci.core.schema_validator import (
    validate_manifest_schema,
    validate_response_schema,
    validate_audit_session_schema,
)
from uci.core.manifest  import UCIManifest
from uci.core.response  import UCIResponse
from uci.core.audit     import UCIAuditSession, AuditRecord, GENESIS_HASH

EXCHANGE_DIR = os.path.join(os.path.dirname(__file__), "exchange")

# ── Colours ──────────────────────────────────────────────────────────────────

PASS = "\033[32m PASS \033[0m"
FAIL = "\033[31m FAIL \033[0m"
HEAD = "\033[36m"
RST  = "\033[0m"

results: list[tuple[str, bool, str]] = []

def check(name: str, passed: bool, detail: str = "") -> None:
    results.append((name, passed, detail))
    tag = PASS if passed else FAIL
    print(f"  [{tag}] {name}" + (f"  — {detail}" if detail and not passed else ""))

def load(filename: str) -> dict:
    path = os.path.join(EXCHANGE_DIR, filename)
    with open(path) as f:
        return json.load(f)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{HEAD}── Python validates TypeScript output ──────────────────{RST}")

    # ── Manifest ─────────────────────────────────────────────
    print(f"\n{HEAD}[1] UCIManifest (typescript_manifest.json){RST}")
    try:
        data = load("typescript_manifest.json")

        schema_result = validate_manifest_schema(data)
        check("Schema validation passes",
              schema_result.valid,
              "; ".join(i.message for i in schema_result.issues if i.severity == "error"))

        try:
            manifest = UCIManifest.from_dict(data)
            manifest.validate()
            check("Semantic validation passes", True)
            check("node_id is non-empty",     bool(manifest.node.node_id))
            check("display_name is non-empty",bool(manifest.node.display_name))
            check("Has capabilities",         len(manifest.capabilities) > 0)
            check("Has transports",           len(manifest.transports) > 0)
            check("node_type is canonical",
                  manifest.node.node_type in {
                      "application","service","agent","daemon","adapter",
                      "hardware_bridge","orchestrator","policy_engine","registry"
                  })
        except Exception as e:
            check("Semantic validation passes", False, str(e))

    except FileNotFoundError:
        print(f"  [SKIP] typescript_manifest.json not found — run TypeScript producer first")

    # ── Invocation ───────────────────────────────────────────
    print(f"\n{HEAD}[2] UCIInvocation (typescript_invocation.json){RST}")
    try:
        data = load("typescript_invocation.json")
        check("Has uci_invocation_version",  "uci_invocation_version" in data)
        check("Has invocation_id",           bool(data.get("invocation_id")))
        check("Has correlation_id",          bool(data.get("correlation_id")))
        check("Has timestamp",               bool(data.get("timestamp")))
        check("Has caller block",            "caller" in data and bool(data["caller"].get("node_id")))
        check("Has target block",            "target" in data and bool(data["target"].get("node_id")))
        check("Has payload",                 "payload" in data)
    except FileNotFoundError:
        print(f"  [SKIP] typescript_invocation.json not found")

    # ── Response (success) ───────────────────────────────────
    print(f"\n{HEAD}[3] UCIResponse success (typescript_response_success.json){RST}")
    try:
        data = load("typescript_response_success.json")

        schema_result = validate_response_schema(data)
        check("Schema validation passes",
              schema_result.valid,
              "; ".join(i.message for i in schema_result.issues if i.severity == "error"))

        r = UCIResponse.from_dict(data)
        check("success == True",             r.success is True)
        check("state == 'completed'",        r.state == "completed")
        check("output is present",           r.output is not None)
        check("error is None",               r.error is None)
        check("Has invocation_id",           bool(r.invocation_id))
        check("Has correlation_id",          bool(r.correlation_id))
        check("provider.node_id non-empty",  bool(r.provider.node_id))
        check("governance.outcome present",  bool(r.governance.outcome))
        check("audit snapshot present",      bool(r.audit.invocation_id))

    except FileNotFoundError:
        print(f"  [SKIP] typescript_response_success.json not found")

    # ── Response (failure) ───────────────────────────────────
    print(f"\n{HEAD}[4] UCIResponse failure (typescript_response_failure.json){RST}")
    try:
        data = load("typescript_response_failure.json")

        schema_result = validate_response_schema(data)
        check("Schema validation passes",
              schema_result.valid,
              "; ".join(i.message for i in schema_result.issues if i.severity == "error"))

        r = UCIResponse.from_dict(data)
        check("success == False",            r.success is False)
        check("state == 'denied'",           r.state == "denied")
        check("error is present",            r.error is not None)
        check("error.code is lowercase",     r.error.code == r.error.code.lower())
        check("error.code is canonical",     r.error.code == "permission_denied")
        check("error.retryable is bool",     isinstance(r.error.retryable, bool))
        check("error.severity is present",   bool(r.error.severity))
        check("output is None",              r.output is None)

    except FileNotFoundError:
        print(f"  [SKIP] typescript_response_failure.json not found")

    # ── Audit session ────────────────────────────────────────
    print(f"\n{HEAD}[5] UCIAuditSession (typescript_audit_session.json){RST}")
    try:
        data = load("typescript_audit_session.json")

        schema_result = validate_audit_session_schema(data)
        check("Schema validation passes",
              schema_result.valid,
              "; ".join(i.message for i in schema_result.issues if i.severity == "error"))

        session = UCIAuditSession.from_dict(data)
        check("Has records",                 len(session.records) > 0)
        check("Session hash is present",     bool(session.session_hash))
        check("Session hash verifies",       session.verify_session_hash())

        # Walk the chain manually
        prev_hash = GENESIS_HASH
        chain_ok  = True
        for record in session.records:
            if not record.verify(prev_hash):
                chain_ok = False
                break
            prev_hash = record.chain_hash
        check("Chain integrity intact",      chain_ok)

        # Check key events are present
        event_types = {r.event_type for r in session.records}
        check("Contains node_discovered",    "node_discovered" in event_types)
        check("Contains trust_assigned",     "trust_assigned" in event_types)
        check("Contains node_ready",         "node_ready" in event_types)
        check("Contains invocation records", any(
            e in event_types for e in
            ["invocation_requested", "invocation_completed"]
        ))

    except FileNotFoundError:
        print(f"  [SKIP] typescript_audit_session.json not found")

    # ── Summary ──────────────────────────────────────────────
    total   = len(results)
    passed  = sum(1 for _, p, _ in results if p)
    failed  = total - passed
    skipped = sum(1 for name, _, _ in results if "SKIP" in name)

    print(f"\n{'─'*56}")
    if failed == 0:
        print(f"\033[32m  ✓ Python validates TypeScript: {passed}/{total} checks passed\033[0m")
    else:
        print(f"\033[31m  ✗ Python validates TypeScript: {passed}/{total} passed, {failed} failed\033[0m")
    print(f"{'─'*56}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
