"""Spec-alignment checks for locked UCI v0.1 constants and manifest shape."""

import pytest
from uci.core.errors import UCIManifestError, UCIValidationError
from uci.core.manifest import (
    UCIAction,
    UCICapability,
    UCIExecution,
    UCIManifest,
    UCINode,
    UCITransport,
    VALID_EXECUTION_MODES,
    VALID_NODE_TYPES,
    VALID_TRANSPORT_TYPES,
)


def _minimal_valid_manifest() -> UCIManifest:
    return UCIManifest(
        node=UCINode(
            node_id="spec_node",
            instance_id="spec_node_001",
            display_name="Spec Node",
            node_type="service",
            version="0.1.0",
        ),
        capabilities=[
            UCICapability(
                capability_id="document_search",
                version="1.0",
                category="retrieval",
                description="Search documents.",
                actions=[
                    UCIAction(
                        action_id="search_index",
                        description="Search an index.",
                        execution=UCIExecution(mode="sync", timeout_ms=1000),
                    )
                ],
            )
        ],
        transports=[
            UCITransport(
                transport_id="local_ipc",
                type="ipc",
                endpoint="uci://local/spec_node",
            )
        ],
    )


def test_locked_execution_modes_include_spec_values_not_stream_alias():
    assert {"sync", "async", "streaming", "scheduled", "event_driven"} <= VALID_EXECUTION_MODES
    assert "stream" not in VALID_EXECUTION_MODES


def test_locked_node_types_match_v0_1_family():
    assert "plugin" not in VALID_NODE_TYPES
    assert "tool" not in VALID_NODE_TYPES
    assert {"application", "service", "adapter", "policy_engine", "registry"} <= VALID_NODE_TYPES


def test_locked_transport_types_use_ipc_not_local_alias():
    assert "local" not in VALID_TRANSPORT_TYPES
    assert {"http", "https", "websocket", "ipc", "grpc", "message_bus", "local_socket", "custom"} <= VALID_TRANSPORT_TYPES


def test_manifest_requires_at_least_one_capability():
    manifest = _minimal_valid_manifest()
    manifest.capabilities = []
    with pytest.raises(UCIManifestError):
        manifest.validate()


def test_manifest_requires_at_least_one_transport():
    manifest = _minimal_valid_manifest()
    manifest.transports = []
    with pytest.raises(UCIManifestError):
        manifest.validate()


def test_stream_alias_is_rejected_in_execution_mode():
    manifest = _minimal_valid_manifest()
    manifest.capabilities[0].actions[0].execution.mode = "stream"
    with pytest.raises(UCIValidationError):
        manifest.validate()


def test_manifest_to_dict_includes_v0_1_top_level_blocks():
    manifest = _minimal_valid_manifest()
    data = manifest.to_dict()
    assert "transports" in data
    assert "compliance" in data
    assert "audit" in data
    assert "extensions" in data
