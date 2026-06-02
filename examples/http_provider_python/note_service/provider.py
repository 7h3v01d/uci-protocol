"""
uci_note_service.py
───────────────────
A local note-taking UCI provider.

Capabilities
------------
  note_management
    • create_note  (risk=low,  perms=notes.write, side_effects=True)
    • search_notes (risk=low,  perms=notes.read,  idempotent=True)
    • get_note     (risk=low,  perms=notes.read,  idempotent=True)
    • delete_note  (risk=high, perms=notes.write, operator_confirmation=required)

Run standalone:
    python uci_note_service.py
    python uci_note_service.py --port 8001
"""

from __future__ import annotations

import sys
import os
import uuid
import argparse
from datetime import datetime, timezone
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..", "..", "uci-python-v2")
sys.path.insert(0, _ROOT)

# ── UCI imports ───────────────────────────────────────────────────────────────
from uci.sdk.provider   import UCIProvider
from uci.transport.http import UCIHttpServer
from uci.core.manifest  import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta, UCIHealth,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _make_note(title: str, content: str) -> dict[str, Any]:
    now = _now()
    return {
        "id":         str(uuid.uuid4()),
        "title":      title,
        "content":    content,
        "created_at": now,
        "updated_at": now,
    }


# ── Provider ──────────────────────────────────────────────────────────────────

class NoteServiceProvider(UCIProvider):
    """
    UCI provider that exposes in-memory note management as a governed service.

    Demonstrates the full UCI governance spectrum:
      create / search / get  → allow (low risk, read or side-effect write)
      delete                 → defer (high risk, operator confirmation required)
    """

    def __init__(self) -> None:
        super().__init__()
        self._store: dict[str, dict[str, Any]] = {}

        self.register_action("note_management", "create_note",  self._create)
        self.register_action("note_management", "search_notes", self._search)
        self.register_action("note_management", "get_note",     self._get)
        self.register_action("note_management", "delete_note",  self._delete)

    # ── Manifest ──────────────────────────────────────────────────────────────

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "uci_note_service",
                instance_id  = "note_service_001",
                display_name = "UCI Note Service",
                node_type    = "service",
                version      = "1.0.0",
                vendor       = "Leon Priest",
                description  = "In-memory note management with UCI governance.",
            ),
            capabilities = [
                UCICapability(
                    capability_id = "note_management",
                    version       = "1.0",
                    category      = "storage",
                    description   = (
                        "Create, retrieve, search, and delete plain-text notes. "
                        "Delete requires operator confirmation."
                    ),
                    tags = ["notes", "storage", "crud"],
                    actions = [

                        UCIAction(
                            action_id   = "create_note",
                            description = "Persist a new note with a title and body.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=3000,
                                idempotent=False, side_effects=True,
                            ),
                            input_schema  = {
                                "title":   {"type": "string", "description": "Note title"},
                                "content": {"type": "string", "description": "Note body"},
                            },
                            output_schema = {
                                "ok":   {"type": "boolean"},
                                "note": {"type": "object"},
                            },
                            risk = UCIRisk(level="low"),
                            permissions = UCIPermissions(
                                required_permissions  = ["notes.write"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),

                        UCIAction(
                            action_id   = "search_notes",
                            description = "Search note titles and content by query string.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=3000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {
                                "query": {"type": "string"},
                                "limit": {"type": "integer", "default": 20},
                            },
                            output_schema = {
                                "ok":      {"type": "boolean"},
                                "results": {"type": "array"},
                                "total":   {"type": "integer"},
                            },
                            risk = UCIRisk(level="low", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["notes.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),

                        UCIAction(
                            action_id   = "get_note",
                            description = "Fetch a single note by its UUID.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=3000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {"note_id": {"type": "string"}},
                            output_schema = {
                                "ok":   {"type": "boolean"},
                                "note": {"type": "object"},
                            },
                            risk = UCIRisk(level="low", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["notes.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),

                        UCIAction(
                            action_id   = "delete_note",
                            description = (
                                "Permanently delete a note. Irreversible. "
                                "Requires operator confirmation before execution."
                            ),
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=5000,
                                idempotent=False, side_effects=True,
                                rollback_supported=False,
                                requires_confirmation=True,
                            ),
                            input_schema  = {"note_id": {"type": "string"}},
                            output_schema = {
                                "ok":         {"type": "boolean"},
                                "deleted_id": {"type": "string"},
                            },
                            risk = UCIRisk(
                                level="high",
                                categories=["state_modifying", "destructive", "irreversible"],
                                description="Permanent deletion — cannot be undone.",
                            ),
                            permissions = UCIPermissions(
                                required_permissions  = ["notes.write"],
                                operator_confirmation = "required",
                                minimum_trust_state   = "trusted",
                            ),
                        ),
                    ],
                )
            ],
            transports = [
                UCITransport(
                    transport_id = "http",
                    type         = "http",
                    endpoint     = "http://localhost:8001",
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
            ),
            compliance = {"profile": "minimal"},
            audit      = {"audit_enabled": True},
            extensions = {},
        )

    # ── Action handlers ───────────────────────────────────────────────────────

    def _create(self, title: str = "", content: str = "", **_) -> dict:
        if not title:
            return {"ok": False, "error": "title is required"}
        note = _make_note(title=title, content=content)
        self._store[note["id"]] = note
        return {"ok": True, "note": note}

    def _search(self, query: str = "", limit: int = 20, **_) -> dict:
        q = query.lower()
        matches = [
            n for n in self._store.values()
            if q in n["title"].lower() or q in n["content"].lower()
        ]
        matches.sort(key=lambda n: n["updated_at"], reverse=True)
        results = matches[:int(limit)]
        return {"ok": True, "results": results, "total": len(results)}

    def _get(self, note_id: str = "", **_) -> dict:
        note = self._store.get(note_id)
        if note is None:
            return {"ok": False, "error": "not_found", "note_id": note_id}
        return {"ok": True, "note": note}

    def _delete(self, note_id: str = "", **_) -> dict:
        if note_id not in self._store:
            return {"ok": False, "error": "not_found", "note_id": note_id}
        del self._store[note_id]
        return {"ok": True, "deleted_id": note_id}


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UCI Note Service")
    parser.add_argument("--port",      type=int, default=8001)
    parser.add_argument("--host",      type=str, default="0.0.0.0")
    parser.add_argument("--log-level", type=str, default="info")
    args = parser.parse_args()

    print(f"""
  ╔══════════════════════════════════════════════════╗
  ║   UCI Note Service                               ║
  ║   HTTP Transport · v1.0.0                        ║
  ║   Author: Leon Priest                            ║
  ╚══════════════════════════════════════════════════╝

  Endpoints:
    GET  http://{args.host}:{args.port}/uci/manifest
    POST http://{args.host}:{args.port}/uci/invoke
    GET  http://{args.host}:{args.port}/uci/audit/session
    GET  http://{args.host}:{args.port}/uci/health

  delete_note requires operator confirmation (risk=high).
  Press Ctrl+C to stop.
""")

    provider = NoteServiceProvider()
    server   = UCIHttpServer(
        provider  = provider,
        port      = args.port,
        host      = args.host,
        log_level = args.log_level,
    )
    server.run()


if __name__ == "__main__":
    main()
