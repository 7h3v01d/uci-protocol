#!/usr/bin/env python3
"""
UCI HTTP Provider Example — Document Search Service
====================================================
A real UCI provider exposing document search over HTTP.

Run with:
    python provider.py
    python provider.py --port 8000

Then from another terminal:
    curl http://localhost:8000/uci/manifest
    curl http://localhost:8000/uci/health

Or run the full TypeScript client:
    cd ../http_client_typescript && npm install && npm run demo
"""

import sys
import os
import argparse

# Path setup
_HERE = os.path.dirname(os.path.abspath(__file__))
_PY   = os.path.join(_HERE, "..", "..", "uci-python-v2")
sys.path.insert(0, _PY)

from uci.sdk.provider    import UCIProvider
from uci.transport.http  import UCIHttpServer
from uci.core.manifest   import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta, UCIHealth,
)

# ── Simulated document store ──────────────────────────────────────────────────

DOCUMENTS = [
    {"id": "doc_001", "title": "UCI Protocol Overview",      "content": "The Universal Capability Interface defines how nodes discover, negotiate, and invoke capabilities.", "tags": ["protocol", "overview"]},
    {"id": "doc_002", "title": "Governance Model v0.1",       "content": "UCI governance enforces fail-closed policy evaluation before every action execution.", "tags": ["governance", "policy"]},
    {"id": "doc_003", "title": "Trust State Machine",         "content": "Nodes progress through trust states: unknown, discovered, verified, trusted, restricted.", "tags": ["trust", "security"]},
    {"id": "doc_004", "title": "Handshake Lifecycle",         "content": "The UCI handshake completes in nine stages from pending to ready, fail-closed at each stage.", "tags": ["handshake", "lifecycle"]},
    {"id": "doc_005", "title": "Audit Chain Integrity",       "content": "Every audit record is sealed with a SHA-256 hash chaining it to the previous record.", "tags": ["audit", "integrity"]},
    {"id": "doc_006", "title": "HTTP Transport Guide",        "content": "UCI over HTTP exposes three endpoints: GET /uci/manifest, POST /uci/invoke, GET /uci/audit/session.", "tags": ["transport", "http"]},
    {"id": "doc_007", "title": "Response Envelope Spec",      "content": "Every UCI invocation returns exactly one UCIResponse — never raises, always enveloped.", "tags": ["response", "spec"]},
    {"id": "doc_008", "title": "Cross-Language Interop",      "content": "Python and TypeScript implementations pass 87/87 interoperability checks.", "tags": ["interop", "typescript", "python"]},
]


class DocumentSearchProvider(UCIProvider):
    """
    A real UCI provider — document search with semantic ranking.
    Exposes two capabilities: document_search and system_health.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_action("document_search", "search_index",  self._search)
        self.register_action("document_search", "get_document",  self._get_doc)
        self.register_action("system_health",   "health_check",  self._health)

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "uci_doc_service",
                instance_id  = "uci_doc_http_001",
                display_name = "UCI Document Search Service",
                node_type    = "service",
                version      = "0.2.0",
                vendor       = "Leon Priest",
                description  = "Document search and retrieval via UCI HTTP transport.",
            ),
            capabilities = [
                UCICapability(
                    capability_id = "document_search",
                    version       = "1.0",
                    category      = "retrieval",
                    description   = "Full-text search and retrieval over a document index.",
                    tags          = ["search", "retrieval", "documents"],
                    actions       = [
                        UCIAction(
                            action_id   = "search_index",
                            description = "Search the document index by query string.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=5000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {
                                "query": {"type": "string", "description": "Search query"},
                                "limit": {"type": "integer", "default": 5, "description": "Max results"},
                            },
                            output_schema = {
                                "results": {"type": "array"},
                                "count":   {"type": "integer"},
                                "query":   {"type": "string"},
                            },
                            risk = UCIRisk(level="low", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["documents.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),
                        UCIAction(
                            action_id   = "get_document",
                            description = "Retrieve a specific document by ID.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=3000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {"document_id": {"type": "string"}},
                            output_schema = {"document": {"type": "object"}},
                            risk = UCIRisk(level="low", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["documents.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),
                    ],
                ),
                UCICapability(
                    capability_id = "system_health",
                    version       = "1.0",
                    category      = "monitoring",
                    description   = "System health and uptime reporting.",
                    actions       = [
                        UCIAction(
                            action_id   = "health_check",
                            description = "Return system health and uptime.",
                            execution   = UCIExecution(mode="sync", timeout_ms=1000),
                            risk        = UCIRisk(level="none"),
                            permissions = UCIPermissions(
                                required_permissions  = ["system.health"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),
                    ],
                ),
            ],
            transports = [
                UCITransport(
                    transport_id = "http",
                    type         = "http",
                    endpoint     = "http://localhost:8000",
                    security     = {},
                    options      = {"content_type": "application/json"},
                )
            ],
            governance = UCIGovernanceMeta(
                default_action_policy       = "deny",
                audit_required              = True,
                operator_authority_required = False,
            ),
            health = UCIHealth(
                health_endpoint   = "/uci/health",
                check_interval_ms = 30000,
                expose_uptime     = True,
                expose_metrics    = False,
            ),
            compliance = {"profile": "minimal"},
            audit      = {"audit_enabled": True},
            extensions = {},
        )

    # ── Action handlers ───────────────────────────────────────────────────────

    def _search(self, query: str = "", limit: int = 5) -> dict:
        q = query.lower()
        scored = []
        for doc in DOCUMENTS:
            score = 0
            if q in doc["title"].lower():   score += 10
            if q in doc["content"].lower(): score += 5
            for tag in doc["tags"]:
                if q in tag: score += 3
            if score > 0:
                scored.append({
                    "id":      doc["id"],
                    "title":   doc["title"],
                    "score":   score / 15,
                    "snippet": doc["content"][:120] + "...",
                    "tags":    doc["tags"],
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[:limit]

        return {
            "results": results,
            "count":   len(results),
            "query":   query,
            "total_docs": len(DOCUMENTS),
        }

    def _get_doc(self, document_id: str = "") -> dict:
        for doc in DOCUMENTS:
            if doc["id"] == document_id:
                return {"document": doc}
        return {"document": None, "error": f"Document '{document_id}' not found"}

    def _health(self) -> dict:
        return {
            "status":       "healthy",
            "version":      "0.2.0",
            "uptime_seconds": 99999,
            "document_count": len(DOCUMENTS),
            "transport":    "http",
        }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="UCI Document Search Provider — HTTP transport example"
    )
    parser.add_argument("--port",      type=int, default=8000)
    parser.add_argument("--host",      type=str, default="0.0.0.0")
    parser.add_argument("--log-level", type=str, default="info",
                        choices=["debug", "info", "warning", "error"])
    args = parser.parse_args()

    print(f"""
  ╔══════════════════════════════════════════════════╗
  ║   UCI Document Search Provider                   ║
  ║   HTTP Transport · v0.2.0                        ║
  ║   Author: Leon Priest                            ║
  ╚══════════════════════════════════════════════════╝

  Endpoints:
    GET  http://{args.host}:{args.port}/uci/manifest
    POST http://{args.host}:{args.port}/uci/invoke
    GET  http://{args.host}:{args.port}/uci/audit/session
    GET  http://{args.host}:{args.port}/uci/health
    GET  http://{args.host}:{args.port}/uci/docs

  Press Ctrl+C to stop.
""")

    provider = DocumentSearchProvider()
    server   = UCIHttpServer(
        provider  = provider,
        port      = args.port,
        host      = args.host,
        log_level = args.log_level,
    )
    server.run()


if __name__ == "__main__":
    main()
