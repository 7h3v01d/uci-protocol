"""
UCI Registry
In-memory node registry — tracks all known nodes, their manifests,
trust records, and mounted capabilities.

Registries are advisory only. They MUST NOT override governance policy.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from .manifest import UCIManifest
from .trust import TrustRecord, TrustState
from .errors import UCIRegistryError


@dataclass
class NodeEntry:
    """A single registered node and everything the registry knows about it."""
    node_id: str
    manifest: UCIManifest
    trust: TrustRecord
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_seen: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    mounted_capabilities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def touch(self) -> None:
        self.last_seen = datetime.now(timezone.utc).isoformat()

    def is_ready(self) -> bool:
        return (
            self.trust.can_execute()
            and bool(self.mounted_capabilities)
        )


@dataclass
class UCIRegistry:
    """
    Central index of all UCI nodes the orchestrator has encountered.
    Thread-safety is the caller's responsibility in this v0.1 implementation.
    """
    _nodes: dict[str, NodeEntry] = field(default_factory=dict, repr=False)

    # ── Registration ─────────────────────────────────

    def register(
        self,
        manifest: UCIManifest,
        trust: TrustRecord,
        tags: Optional[list[str]] = None,
    ) -> NodeEntry:
        node_id = manifest.node.node_id
        if node_id in self._nodes:
            raise UCIRegistryError(
                f"Node '{node_id}' is already registered. Use update() to refresh."
            )
        entry = NodeEntry(
            node_id    = node_id,
            manifest   = manifest,
            trust      = trust,
            tags       = tags or [],
        )
        self._nodes[node_id] = entry
        return entry

    def update(self, manifest: UCIManifest, trust: TrustRecord) -> NodeEntry:
        """Re-register an existing node (e.g. after revalidation)."""
        node_id = manifest.node.node_id
        if node_id not in self._nodes:
            return self.register(manifest, trust)
        entry = self._nodes[node_id]
        entry.manifest = manifest
        entry.trust    = trust
        entry.touch()
        return entry

    def deregister(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise UCIRegistryError(f"Node '{node_id}' not found in registry.")
        del self._nodes[node_id]

    # ── Capability mounting ──────────────────────────

    def mount_capability(self, node_id: str, capability_id: str) -> None:
        entry = self._get(node_id)
        if capability_id not in entry.mounted_capabilities:
            entry.mounted_capabilities.append(capability_id)

    def revoke_capability(self, node_id: str, capability_id: str) -> None:
        entry = self._get(node_id)
        entry.mounted_capabilities = [
            c for c in entry.mounted_capabilities if c != capability_id
        ]

    # ── Lookups ──────────────────────────────────────

    def get(self, node_id: str) -> Optional[NodeEntry]:
        return self._nodes.get(node_id)

    def require(self, node_id: str) -> NodeEntry:
        entry = self.get(node_id)
        if entry is None:
            raise UCIRegistryError(f"Node '{node_id}' not found in registry.")
        return entry

    def all_nodes(self) -> list[NodeEntry]:
        return list(self._nodes.values())

    def ready_nodes(self) -> list[NodeEntry]:
        return [e for e in self._nodes.values() if e.is_ready()]

    def nodes_with_capability(self, capability_id: str) -> list[NodeEntry]:
        return [
            e for e in self._nodes.values()
            if capability_id in e.mounted_capabilities
        ]

    def nodes_by_trust(self, state: TrustState) -> list[NodeEntry]:
        return [e for e in self._nodes.values() if e.trust.state == state]

    def count(self) -> int:
        return len(self._nodes)

    def _get(self, node_id: str) -> NodeEntry:
        entry = self._nodes.get(node_id)
        if entry is None:
            raise UCIRegistryError(f"Node '{node_id}' not found.")
        return entry

    # ── Summary ──────────────────────────────────────

    def summary(self) -> dict:
        return {
            "total_nodes":   self.count(),
            "ready":         len(self.ready_nodes()),
            "nodes": [
                {
                    "node_id":    e.node_id,
                    "trust":      e.trust.state.value,
                    "capabilities": e.mounted_capabilities,
                    "is_ready":   e.is_ready(),
                }
                for e in self._nodes.values()
            ],
        }
