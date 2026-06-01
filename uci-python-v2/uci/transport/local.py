"""
UCI Local Transport  —  uci/transport/local.py
===============================================
In-process transport for the UCI test rig and local-first deployments.

The local transport connects UCI nodes running in the same Python process.
It is the default transport used by the test rig and is suitable for:
  - local-first applications where all nodes run in the same process
  - testing and development
  - embedded UCI deployments (e.g. desktop applications)

It is NOT suitable for:
  - cross-process communication (use HTTP or IPC transport)
  - distributed deployments
  - production multi-node environments

This transport is intentionally simple. It holds a reference to the
provider object and invokes it directly — there is no serialisation
or network overhead. The UCI protocol semantics are preserved fully.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..sdk.provider import UCIProvider


class LocalTransport:
    """
    In-process UCI transport.

    Connects an orchestrator directly to a provider object in the same
    Python process. All UCI semantics are preserved — handshake, governance,
    audit — only the wire is elided.

    Usage is handled automatically by UCIOrchestrator.connect().
    Direct use is not normally required.
    """

    TRANSPORT_TYPE = "local"

    def __init__(self, provider: "UCIProvider") -> None:
        self._provider = provider

    def get_manifest(self) -> dict[str, Any]:
        """Retrieve the provider's manifest — no network hop required."""
        return self._provider.manifest_dict()

    def invoke(
        self,
        capability_id: str,
        action_id: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Invoke an action directly on the provider."""
        return self._provider.invoke(capability_id, action_id, payload)

    @property
    def transport_id(self) -> str:
        manifest = self._provider.build_manifest()
        for t in manifest.transports:
            if t.type in {"local", "ipc", "local_socket"}:
                return t.transport_id
        return "local"

    def __repr__(self) -> str:
        return f"LocalTransport(provider={self._provider.__class__.__name__})"
