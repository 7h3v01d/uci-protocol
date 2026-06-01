"""
Mock Provider Gamma — Malformed / Bad Actor Node
Used to prove UCI's fail-closed behaviour. Provides multiple
broken manifest variants that the handshake should reject cleanly.
"""

from uci.sdk.provider import UCIProvider
from uci.core.manifest import UCIManifest, UCINode


class ProviderGammaMissingNodeId(UCIProvider):
    """Missing required node_id — should fail at manifest validation."""

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "",          # ← MISSING — should trigger UCIManifestError
                instance_id  = "gamma_001",
                display_name = "Bad Actor No ID",
                node_type    = "service",
                version      = "0.1.0",
            ),
        )


class ProviderGammaUnsupportedVersion(UCIProvider):
    """Declares an unsupported manifest version — should fail compatibility."""

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "99.0",   # ← UNSUPPORTED
            node = UCINode(
                node_id      = "provider_gamma_version",
                instance_id  = "gamma_002",
                display_name = "Bad Actor Bad Version",
                node_type    = "service",
                version      = "0.1.0",
            ),
        )


class ProviderGammaInvalidRisk(UCIProvider):
    """Contains an action with an invalid risk level — should fail validation."""

    def build_manifest(self) -> UCIManifest:
        from uci.core.manifest import (
            UCICapability, UCIAction, UCIExecution, UCIRisk, UCIPermissions,
        )
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "provider_gamma_risk",
                instance_id  = "gamma_003",
                display_name = "Bad Actor Invalid Risk",
                node_type    = "service",
                version      = "0.1.0",
            ),
            capabilities = [
                UCICapability(
                    capability_id = "bad_capability",
                    actions = [
                        UCIAction(
                            action_id = "bad_action",
                            risk      = UCIRisk(level="catastrophic"),  # ← INVALID
                        ),
                    ],
                )
            ],
        )


class ProviderGammaInvalidNodeType(UCIProvider):
    """Declares an invalid node_type — should fail semantic validation."""

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "provider_gamma_type",
                instance_id  = "gamma_004",
                display_name = "Bad Actor Invalid Type",
                node_type    = "malware",     # ← INVALID
                version      = "0.1.0",
            ),
        )


class ProviderGammaNoCaps(UCIProvider):
    """
    Structurally valid manifest but declares zero capabilities.
    Should handshake cleanly but mount nothing — edge case.
    """

    def build_manifest(self) -> UCIManifest:
        from uci.core.manifest import UCITransport, UCIGovernanceMeta
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "provider_gamma_empty",
                instance_id  = "gamma_005",
                display_name = "Empty Provider",
                node_type    = "service",
                version      = "0.1.0",
            ),
            capabilities = [],              # ← invalid under locked v0.1
            transports = [UCITransport(transport_id="local_ipc", type="ipc", endpoint="uci://local/provider_gamma_empty")],
            governance = UCIGovernanceMeta(
                operator_authority_required = False,
                default_action_policy       = "deny",
            ),
        )
