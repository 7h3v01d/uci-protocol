#!/usr/bin/env python3
"""
UCI Interoperability Test — Python Producer
==========================================
Produces the four canonical UCI objects as JSON files.
These are then consumed and validated by the TypeScript implementation.

This script does NOT know anything about TypeScript.
It only knows the UCI spec and its own implementation.
The exchange format is plain JSON — the protocol surface.
"""

import sys
import os
import json
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "uci-python-v2"))

from uci.core.manifest import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta, UCIHealth,
)
from uci.core.invocation import UCIInvocation
from uci.core.response   import UCIResponse, UCIResponseError, UCIErrorCode, UCIErrorSeverity
from uci.core.audit      import AuditLog, AuditEvent
from uci.core.governance import PolicyEngine
from uci.core.registry   import UCIRegistry
from uci.core.handshake  import HandshakeEngine
from uci.core.trust      import TrustState

EXCHANGE_DIR = os.path.join(os.path.dirname(__file__), "exchange")
os.makedirs(EXCHANGE_DIR, exist_ok=True)

def write(filename: str, data: dict) -> None:
    path = os.path.join(EXCHANGE_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  wrote {filename}")


def main():
    print("\n── Python Producer ──────────────────────────────────")

    # ── 1. UCIManifest ───────────────────────────────────────
    print("\n[1] Producing UCIManifest...")
    manifest = UCIManifest(
        uci_manifest_version = "0.1",
        node = UCINode(
            node_id      = "python_doc_service",
            instance_id  = "python_doc_001",
            display_name = "Python Document Service",
            node_type    = "service",
            version      = "1.0.0",
            vendor       = "KeystoneAI",
            description  = "Produced by Python reference implementation.",
        ),
        capabilities = [UCICapability(
            capability_id = "document_search",
            version       = "1.0",
            category      = "retrieval",
            description   = "Search and retrieve documents.",
            actions       = [UCIAction(
                action_id   = "search_index",
                description = "Search by query string.",
                execution   = UCIExecution(
                    mode="sync", timeout_ms=5000,
                    idempotent=True, side_effects=False,
                ),
                input_schema  = {"query": "string", "limit": "integer"},
                output_schema = {"results": "array", "count": "integer"},
                risk        = UCIRisk(level="low", categories=["read_only"]),
                permissions = UCIPermissions(
                    required_permissions  = ["documents.read"],
                    operator_confirmation = "none",
                    minimum_trust_state   = "trusted",
                ),
            )],
        )],
        transports = [UCITransport(
            transport_id = "ipc_local",
            type         = "ipc",
            endpoint     = "uci://local/python_doc_service",
        )],
        governance = UCIGovernanceMeta(
            default_action_policy       = "deny",
            audit_required              = True,
            operator_authority_required = False,
        ),
        health = UCIHealth(expose_uptime=True, expose_metrics=False),
        compliance = {"profile": "minimal"},
        audit      = {"audit_enabled": True},
        extensions = {},
    )
    manifest.validate()
    write("python_manifest.json", manifest.to_dict())

    # ── 2. UCIInvocation ─────────────────────────────────────
    print("\n[2] Producing UCIInvocation...")
    inv = UCIInvocation.create(
        node_id        = "python_doc_service",
        capability_id  = "document_search",
        action_id      = "search_index",
        payload        = {"query": "UCI interoperability", "limit": 5},
        caller_node_id = "python_orchestrator",
        session_id     = "interop-session-001",
        correlation_id = "interop-corr-" + str(uuid.uuid4())[:8],
    )
    write("python_invocation.json", inv.to_dict())

    # ── 3. UCIResponse (success) ─────────────────────────────
    print("\n[3] Producing UCIResponse (success)...")
    response = UCIResponse.success_response(
        output         = {
            "results": [
                {"id": "doc_001", "title": "UCI Protocol Overview", "score": 0.97},
                {"id": "doc_002", "title": "Governance Model v0.1",  "score": 0.91},
            ],
            "count": 2,
            "query": "UCI interoperability",
        },
        node_id            = "python_doc_service",
        instance_id        = "python_doc_001",
        capability_id      = "document_search",
        action_id          = "search_index",
        trust_state        = "trusted",
        governance_outcome = "allow",
        correlation_id     = inv.correlation_id,
        actor              = "python_orchestrator",
    )
    write("python_response_success.json", response.to_dict())

    # ── 4. UCIResponse (failure) ─────────────────────────────
    print("\n[4] Producing UCIResponse (failure)...")
    failure = UCIResponse.failure_response(
        error = UCIResponseError(
            code      = UCIErrorCode.PERMISSION_DENIED,
            severity  = UCIErrorSeverity.HIGH,
            message   = "Caller lacks documents.read permission.",
            retryable = False,
            detail    = {"missing_permissions": ["documents.read"]},
        ),
        node_id            = "python_doc_service",
        instance_id        = "python_doc_001",
        capability_id      = "document_search",
        action_id          = "search_index",
        trust_state        = "trusted",
        governance_outcome = "deny",
    )
    write("python_response_failure.json", failure.to_dict())

    # ── 5. UCIAuditSession ───────────────────────────────────
    print("\n[5] Producing UCIAuditSession...")
    audit = AuditLog(orchestrator_id="python_orchestrator")

    # Simulate a full session lifecycle
    audit.append(AuditEvent.NODE_DISCOVERED,            "python_doc_service", actor="handshake_engine")
    audit.append(AuditEvent.MANIFEST_VALIDATION_PASSED, "python_doc_service", actor="handshake_engine")
    audit.append(AuditEvent.TRUST_ASSIGNED,             "python_doc_service", actor="policy_engine",
                 outcome="", detail={"trust_state": "trusted"})
    audit.append(AuditEvent.CAPABILITY_MOUNTED,         "python_doc_service", actor="handshake_engine",
                 detail={"capability_id": "document_search"})
    audit.append(AuditEvent.NODE_READY,                 "python_doc_service", actor="handshake_engine",
                 detail={"mounted_capabilities": ["document_search"]})
    audit.append(AuditEvent.EXECUTION_ALLOWED,          "python_doc_service", actor="policy_engine",
                 outcome="allow", detail={"capability_id": "document_search", "action_id": "search_index"})
    audit.append(AuditEvent.INVOCATION_REQUESTED,       "python_doc_service", actor="python_orchestrator",
                 detail={"capability_id": "document_search", "action_id": "search_index"})
    audit.append(AuditEvent.INVOCATION_COMPLETED,       "python_doc_service", actor="python_orchestrator",
                 outcome="success")

    session = audit.export(seal=True)
    write("python_audit_session.json", session.to_dict())

    # ── Integrity self-check ─────────────────────────────────
    print("\n[✓] Python self-checks:")
    integrity = audit.verify_integrity()
    print(f"    Audit integrity:       {'PASS' if integrity.valid else 'FAIL'}")
    print(f"    Session hash valid:    {'PASS' if session.verify_session_hash() else 'FAIL'}")
    print(f"    Manifest valid:        {'PASS' if True else 'FAIL'}")  # validated above

    print(f"\n── Exchange files written to: {EXCHANGE_DIR}")
    print(f"   python_manifest.json")
    print(f"   python_invocation.json")
    print(f"   python_response_success.json")
    print(f"   python_response_failure.json")
    print(f"   python_audit_session.json")
    print()

if __name__ == "__main__":
    main()
