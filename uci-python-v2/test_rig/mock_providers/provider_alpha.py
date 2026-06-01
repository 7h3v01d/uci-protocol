"""
Mock Provider Alpha — Fully Compliant, Trusted Node
Represents a well-behaved Keystone service exposing document search
and health check capabilities. Should always reach TRUSTED state.
"""

from uci.sdk.provider import UCIProvider
from uci.core.manifest import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta,
)


class ProviderAlpha(UCIProvider):
    """
    A model UCI provider.
    - Two capabilities: document_search and system_health
    - All actions are low-risk
    - No confirmation requirements
    - Expects to be mounted as TRUSTED
    """

    def __init__(self) -> None:
        super().__init__()
        # Register action handlers
        self.register_action("document_search", "search_index", self._search_index)
        self.register_action("document_search", "get_document", self._get_document)
        self.register_action("system_health",   "health_check", self._health_check)

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "provider_alpha",
                instance_id  = "alpha_local_001",
                display_name = "Keystone Document Service (Alpha)",
                node_type    = "service",
                version      = "1.2.0",
                vendor       = "KeystoneAI",
                description  = "Indexes and retrieves documents with semantic search.",
            ),
            capabilities = [
                UCICapability(
                    capability_id = "document_search",
                    version       = "1.0",
                    category      = "retrieval",
                    description   = "Search and retrieve indexed documents.",
                    tags          = ["search", "retrieval", "documents"],
                    actions = [
                        UCIAction(
                            action_id   = "search_index",
                            description = "Search the document index by query string.",
                            execution   = UCIExecution(
                                mode         = "sync",
                                timeout_ms   = 5000,
                                idempotent   = True,
                                side_effects = False,
                            ),
                            input_schema  = {"query": "string", "limit": "integer"},
                            output_schema = {"results": "array", "count": "integer"},
                            risk = UCIRisk(
                                level       = "low",
                                categories  = ["read_only"],
                                description = "Read-only search — no data modification.",
                            ),
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
                                mode         = "sync",
                                timeout_ms   = 3000,
                                idempotent   = True,
                                side_effects = False,
                            ),
                            input_schema  = {"document_id": "string"},
                            output_schema = {"document": "object"},
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
                    description   = "Exposes health and status information.",
                    actions = [
                        UCIAction(
                            action_id   = "health_check",
                            description = "Return current health and uptime status.",
                            execution   = UCIExecution(
                                mode       = "sync",
                                timeout_ms = 1000,
                                idempotent = True,
                                side_effects = False,
                            ),
                            risk = UCIRisk(level="none"),
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
                    transport_id = "local_ipc",
                    type         = "ipc",
                    endpoint     = "uci://local/provider_alpha",
                )
            ],
            governance = UCIGovernanceMeta(
                requires_policy_check       = True,
                audit_required              = True,
                operator_authority_required = False,  # ← no operator gate
                default_action_policy       = "deny",
            ),
        )

    # ── Action handlers ──────────────────────────────

    def _search_index(self, query: str = "", limit: int = 10) -> dict:
        # Simulated document search results
        return {
            "results": [
                {"id": "doc_001", "title": f"Result for '{query}' #1", "score": 0.95},
                {"id": "doc_002", "title": f"Result for '{query}' #2", "score": 0.87},
            ][:limit],
            "count": min(2, limit),
            "query": query,
        }

    def _get_document(self, document_id: str = "") -> dict:
        return {
            "document": {
                "id":      document_id,
                "title":   f"Document {document_id}",
                "content": "Lorem ipsum content for test document.",
                "tags":    ["test", "demo"],
            }
        }

    def _health_check(self) -> dict:
        return {
            "status":        "healthy",
            "uptime_seconds": 99999,
            "version":        "1.2.0",
            "load":           0.12,
        }
