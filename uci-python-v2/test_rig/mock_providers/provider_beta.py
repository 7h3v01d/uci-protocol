"""
Mock Provider Beta — Restricted Trust Node
Represents a partially trusted service. Valid manifest, but:
- Has high-risk actions requiring operator confirmation
- Sets operator_authority_required = True
- Should reach RESTRICTED trust state
- High-risk capabilities should NOT be mounted without operator approval
"""

from uci.sdk.provider import UCIProvider
from uci.core.manifest import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta,
)


class ProviderBeta(UCIProvider):
    """
    A partially trusted UCI provider.
    - voice_tts: low risk — should mount fine
    - file_operations: contains a 'delete_file' action (high risk)
      → should be deferred / not auto-mounted under restricted trust
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_action("voice_tts",      "synthesize",   self._synthesize)
        self.register_action("file_operations", "read_file",   self._read_file)
        self.register_action("file_operations", "delete_file", self._delete_file)

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "provider_beta",
                instance_id  = "beta_local_001",
                display_name = "Example Voice & File Service (Beta)",
                node_type    = "service",
                version      = "0.9.0",
                vendor       = "Leon Priest",
                description  = "Voice synthesis and file management — requires operator authority.",
            ),
            capabilities = [
                UCICapability(
                    capability_id = "voice_tts",
                    version       = "1.0",
                    category      = "audio",
                    description   = "Text-to-speech synthesis.",
                    actions = [
                        UCIAction(
                            action_id   = "synthesize",
                            description = "Convert text to audio output.",
                            execution   = UCIExecution(
                                mode         = "sync",
                                timeout_ms   = 8000,
                                side_effects = True,      # plays audio
                            ),
                            input_schema  = {"text": "string", "voice_id": "string"},
                            output_schema = {"audio_url": "string", "duration_ms": "integer"},
                            risk = UCIRisk(
                                level       = "low",
                                categories  = ["operator_visible"],
                                description = "Produces audio — no data written.",
                            ),
                            permissions = UCIPermissions(
                                required_permissions  = ["voice.tts"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "restricted",   # works under restricted
                            ),
                        ),
                    ],
                ),
                UCICapability(
                    capability_id = "file_operations",
                    version       = "1.0",
                    category      = "storage",
                    description   = "Read and manage local files.",
                    actions = [
                        UCIAction(
                            action_id   = "read_file",
                            description = "Read a file from the local filesystem.",
                            execution   = UCIExecution(
                                mode         = "sync",
                                timeout_ms   = 2000,
                                idempotent   = True,
                                side_effects = False,
                            ),
                            input_schema  = {"path": "string"},
                            output_schema = {"content": "string"},
                            risk = UCIRisk(level="medium", categories=["filesystem_access"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["documents.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),
                        UCIAction(
                            action_id   = "delete_file",
                            description = "Permanently delete a file.",
                            execution   = UCIExecution(
                                mode                  = "sync",
                                timeout_ms            = 3000,
                                side_effects          = True,
                                rollback_supported    = False,
                                requires_confirmation = True,      # ← explicit flag
                            ),
                            input_schema  = {"path": "string"},
                            output_schema = {"deleted": "boolean"},
                            risk = UCIRisk(
                                level       = "high",
                                categories  = ["destructive", "filesystem_access"],
                                description = "Permanent deletion — not reversible.",
                            ),
                            permissions = UCIPermissions(
                                required_permissions  = ["documents.write"],
                                operator_confirmation = "required",   # must confirm
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
                    endpoint     = "uci://local/provider_beta",
                )
            ],
            governance = UCIGovernanceMeta(
                requires_policy_check       = True,
                audit_required              = True,
                operator_authority_required = True,    # ← triggers restricted mount
                default_action_policy       = "deny",
            ),
        )

    # ── Action handlers ──────────────────────────────

    def _synthesize(self, text: str = "", voice_id: str = "default") -> dict:
        return {
            "audio_url":   f"local://tts_output_{hash(text) % 9999:04d}.wav",
            "duration_ms": len(text) * 60,
            "voice_id":    voice_id,
        }

    def _read_file(self, path: str = "") -> dict:
        return {
            "content": f"[Simulated content of file: {path}]",
            "path":    path,
            "size":    512,
        }

    def _delete_file(self, path: str = "") -> dict:
        # In the test rig this never actually deletes anything
        return {"deleted": True, "path": path}
