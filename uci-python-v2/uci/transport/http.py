"""
UCI HTTP Transport  —  uci/transport/http.py
=============================================
FastAPI-based HTTP transport for UCI providers.

Exposes three canonical endpoints:

    GET  /uci/manifest        → UCIManifest (JSON)
    POST /uci/invoke          → UCIInvocation → UCIResponse (JSON)
    GET  /uci/audit/session   → UCIAuditSession (JSON)

Wire format is plain JSON — the canonical UCI protocol objects.
Any UCI client in any language can call these endpoints.

UCI transport contract:
  - MUST preserve governance semantics
  - MUST preserve trust semantics
  - MUST preserve correlation identifiers
  - MUST preserve canonical response structure
  - MUST NOT redefine protocol behaviour

Usage:
    from uci.transport.http import UCIHttpServer
    server = UCIHttpServer(provider=MyProvider(), port=8000)
    server.run()
"""

from __future__ import annotations

import sys
import os
import uvicorn
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Path setup
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from uci.core.audit      import AuditLog, AuditEvent
from uci.core.governance import PolicyEngine, DEFAULT_ORCHESTRATOR_PERMISSIONS
from uci.core.handshake  import HandshakeEngine
from uci.core.invocation import UCIInvocation
from uci.core.registry   import UCIRegistry
from uci.core.response   import UCIResponse, UCIResponseError, UCIErrorCode, UCIErrorSeverity
from uci.core.trust      import TrustState
from uci.sdk.provider    import UCIProvider, UCIOrchestrator


class UCIHttpServer:
    """
    Wraps a UCIProvider and exposes it over HTTP.

    The server runs the full UCI handshake on startup (self-connecting),
    then serves the three canonical endpoints.
    """

    def __init__(
        self,
        provider:   UCIProvider,
        port:       int  = 8000,
        host:       str  = "0.0.0.0",
        cors:       bool = True,
        log_level:  str  = "info",
    ) -> None:
        self.provider  = provider
        self.port      = port
        self.host      = host
        self.log_level = log_level

        # Build the UCI engine stack — include all standard permissions
        # plus any permissions declared in the provider manifest
        self.audit      = AuditLog(orchestrator_id="uci_http_server")
        self.registry   = UCIRegistry()

        # Collect permissions from the provider manifest
        manifest_data = provider.manifest_dict()
        declared_perms: set[str] = set()
        for cap in manifest_data.get("capabilities", []):
            for action in cap.get("actions", []):
                perms = action.get("permissions", {}).get("required_permissions", [])
                declared_perms.update(perms)

        all_permissions = DEFAULT_ORCHESTRATOR_PERMISSIONS | declared_perms
        self.policy     = PolicyEngine(
            orchestrator_permissions=all_permissions,
            audit=self.audit,
        )
        self.orch       = UCIOrchestrator(
            policy   = self.policy,
            registry = self.registry,
            audit    = self.audit,
            name     = "uci_http_server",
        )

        # Connect the provider — runs full handshake
        result = self.orch.connect(provider)
        if not result.success:
            raise RuntimeError(
                f"UCI handshake failed on startup: {result.failure_reason}"
            )

        self._node_id = result.node_id
        self._app     = self._build_app(cors)

    def _build_app(self, cors: bool) -> FastAPI:
        manifest_data = self.provider.manifest_dict()
        node          = manifest_data.get("node", {})

        app = FastAPI(
            title       = node.get("display_name", "UCI Provider"),
            description = node.get("description", ""),
            version     = node.get("version", "0.1.0"),
            docs_url    = "/uci/docs",
            redoc_url   = "/uci/redoc",
        )

        if cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins     = ["*"],
                allow_methods     = ["GET", "POST"],
                allow_headers     = ["*"],
            )

        # ── GET /uci/manifest ─────────────────────────────────────
        @app.get("/uci/manifest", tags=["UCI Protocol"])
        async def get_manifest() -> dict:
            """
            Return this node's UCIManifest.
            The calling orchestrator uses this to discover capabilities,
            governance requirements, and transport details.
            """
            self.audit.append(
                AuditEvent.MANIFEST_RETRIEVED,
                self._node_id,
                actor="http_client",
            )
            return self.provider.manifest_dict()

        # ── POST /uci/invoke ──────────────────────────────────────
        @app.post("/uci/invoke", tags=["UCI Protocol"])
        async def invoke(request: Request) -> dict:
            """
            Execute a UCI action.
            Body: UCIInvocation JSON
            Returns: UCIResponse JSON
            """
            try:
                body = await request.json()
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON body")

            # Deserialise the invocation
            try:
                inv = UCIInvocation.from_dict(body)
            except Exception as exc:
                return UCIResponse.from_exception(
                    exc,
                    node_id       = self._node_id,
                    capability_id = body.get("target", {}).get("capability_id", ""),
                    action_id     = body.get("target", {}).get("action_id", ""),
                    code          = UCIErrorCode.INVALID_INVOCATION,
                    correlation_id= body.get("correlation_id"),
                ).to_dict()

            # Route through the governance-gated orchestrator
            response = self.orch.invoke(
                node_id           = inv.node_id,
                capability_id     = inv.capability_id,
                action_id         = inv.action_id,
                payload           = inv.payload,
                operator_override = inv.operator_override,
                correlation_id    = inv.correlation_id,
            )

            # HTTP status reflects UCI state
            status = 200
            if response.state == "denied":
                status = 403
            elif response.state == "deferred":
                status = 202
            elif not response.success:
                status = 500

            return JSONResponse(content=response.to_dict(), status_code=status)

        # ── GET /uci/audit/session ────────────────────────────────
        @app.get("/uci/audit/session", tags=["UCI Protocol"])
        async def get_audit_session() -> dict:
            """
            Export the current UCI audit session.
            Returns a sealed UCIAuditSession with chain hash verification.
            Callers can independently verify the chain hash and session hash.
            """
            session = self.audit.export(seal=True)
            return session.to_dict()

        # ── GET /uci/health ───────────────────────────────────────
        @app.get("/uci/health", tags=["UCI Protocol"])
        async def health() -> dict:
            """Quick liveness check — returns node identity and trust state."""
            entry = self.registry.get(self._node_id)
            return {
                "status":     "healthy",
                "node_id":    self._node_id,
                "trust_state": entry.trust.state.value if entry else "unknown",
                "capabilities": self.registry.get(self._node_id).mounted_capabilities
                                 if self.registry.get(self._node_id) else [],
                "audit_events": self.audit.count(),
            }

        # ── GET / ─────────────────────────────────────────────────
        @app.get("/", include_in_schema=False)
        async def root() -> dict:
            return {
                "protocol":  "UCI — Universal Capability Interface",
                "version":   "0.1",
                "node_id":   self._node_id,
                "endpoints": {
                    "manifest":      "GET  /uci/manifest",
                    "invoke":        "POST /uci/invoke",
                    "audit_session": "GET  /uci/audit/session",
                    "health":        "GET  /uci/health",
                    "docs":          "GET  /uci/docs",
                },
            }

        return app

    @property
    def app(self) -> FastAPI:
        return self._app

    def run(self) -> None:
        """Start the server (blocking)."""
        uvicorn.run(
            self._app,
            host      = self.host,
            port      = self.port,
            log_level = self.log_level,
        )
