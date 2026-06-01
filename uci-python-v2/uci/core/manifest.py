"""
UCI Manifest
Canonical structure for a UCI capability manifest (v0.1).

A manifest is the self-description a node presents during handshake.
It declares identity, capabilities, governance requirements, transport
endpoints, and compatibility metadata.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any
from .errors import UCIManifestError, UCIValidationError

SUPPORTED_MANIFEST_VERSIONS = {"0.1"}

# ─────────────────────────────────────────────
# Risk levels
# ─────────────────────────────────────────────

VALID_RISK_LEVELS = {"none", "low", "medium", "high", "critical"}
VALID_CONFIRMATION = {"none", "recommended", "required", "required_with_reason", "multi_party_required"}
VALID_EXECUTION_MODES = {"sync", "async", "streaming", "scheduled", "event_driven"}
VALID_NODE_TYPES = {"application", "service", "agent", "daemon", "adapter", "hardware_bridge", "orchestrator", "policy_engine", "registry"}
VALID_TRANSPORT_TYPES = {"http", "https", "websocket", "ipc", "grpc", "message_bus", "local_socket", "custom"}
VALID_CAPABILITY_CATEGORIES = {"retrieval", "storage", "generation", "analysis", "transformation", "communication", "execution", "governance", "monitoring", "vision", "audio", "identity", "network", "security", "utility", "other"}
VALID_RISK_CATEGORIES = {"read_only", "state_modifying", "destructive", "external_communication", "sensitive_data_access", "financial", "legal", "security_sensitive", "network_access", "filesystem_access", "code_execution", "operator_visible", "irreversible"}
VALID_TRUST_STATES = {"unknown", "discovered", "verified", "trusted", "restricted", "suspended", "revoked"}


# ─────────────────────────────────────────────
# Sub-structures
# ─────────────────────────────────────────────

@dataclass
class UCIRisk:
    level: str = "low"
    categories: list[str] = field(default_factory=list)
    description: str = ""

    def validate(self) -> None:
        if self.level not in VALID_RISK_LEVELS:
            raise UCIValidationError(
                f"Invalid risk level '{self.level}'. Must be one of {VALID_RISK_LEVELS}."
            )
        invalid_categories = [c for c in self.categories if c not in VALID_RISK_CATEGORIES]
        if invalid_categories:
            raise UCIValidationError(
                f"Invalid risk categories {invalid_categories}. Must be from {VALID_RISK_CATEGORIES}."
            )


@dataclass
class UCIPermissions:
    required_permissions: list[str] = field(default_factory=list)
    operator_confirmation: str = "none"
    minimum_trust_state: str = "trusted"

    def validate(self) -> None:
        if self.operator_confirmation not in VALID_CONFIRMATION:
            raise UCIValidationError(
                f"Invalid operator_confirmation '{self.operator_confirmation}'."
            )
        if self.minimum_trust_state not in VALID_TRUST_STATES:
            raise UCIValidationError(
                f"Invalid minimum_trust_state '{self.minimum_trust_state}'."
            )


@dataclass
class UCIExecution:
    mode: str = "sync"
    timeout_ms: int = 10000
    idempotent: bool = False
    side_effects: bool = False
    rollback_supported: bool = False
    requires_confirmation: bool = False

    def validate(self) -> None:
        if self.mode not in VALID_EXECUTION_MODES:
            raise UCIValidationError(
                f"Invalid execution mode '{self.mode}'. Must be one of {VALID_EXECUTION_MODES}."
            )
        if self.timeout_ms < 1:
            raise UCIValidationError("timeout_ms must be >= 1.")


@dataclass
class UCIAction:
    action_id: str = ""
    description: str = ""
    execution: UCIExecution = field(default_factory=UCIExecution)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    risk: UCIRisk = field(default_factory=UCIRisk)
    permissions: UCIPermissions = field(default_factory=UCIPermissions)
    errors: list[dict] = field(default_factory=list)

    def validate(self) -> None:
        if not self.action_id:
            raise UCIManifestError("UCIAction requires a non-empty action_id.")
        self.execution.validate()
        self.risk.validate()
        self.permissions.validate()


@dataclass
class UCICapability:
    capability_id: str = ""
    version: str = "1.0"
    category: str = ""
    description: str = ""
    actions: list[UCIAction] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.capability_id:
            raise UCIManifestError("UCICapability requires a non-empty capability_id.")
        if self.category not in VALID_CAPABILITY_CATEGORIES:
            raise UCIValidationError(
                f"Invalid capability category '{self.category}'. Must be one of {VALID_CAPABILITY_CATEGORIES}."
            )
        if not self.actions:
            raise UCIManifestError("UCICapability requires at least one action.")
        for action in self.actions:
            action.validate()

    def get_action(self, action_id: str) -> Optional[UCIAction]:
        for a in self.actions:
            if a.action_id == action_id:
                return a
        return None


@dataclass
class UCITransport:
    transport_id: str = ""
    type: str = "ipc"            # http | https | websocket | ipc | grpc | message_bus | local_socket | custom
    endpoint: str = ""
    security: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.transport_id:
            raise UCIManifestError("UCITransport requires a non-empty transport_id.")
        if self.type not in VALID_TRANSPORT_TYPES:
            raise UCIValidationError(
                f"Invalid transport type '{self.type}'. Must be one of {VALID_TRANSPORT_TYPES}."
            )
        if not self.endpoint:
            raise UCIManifestError("UCITransport requires a non-empty endpoint.")


@dataclass
class UCIGovernanceMeta:
    requires_policy_check: bool = True
    audit_required: bool = True
    operator_authority_required: bool = True
    default_action_policy: str = "deny"
    sandbox_required: bool = False
    allow_remote_execution: bool = False
    requires_signed_requests: bool = False

    def validate(self) -> None:
        if self.default_action_policy not in {"allow", "deny", "defer"}:
            raise UCIValidationError(
                f"default_action_policy must be 'allow', 'deny', or 'defer', "
                f"got '{self.default_action_policy}'."
            )


@dataclass
class UCIHealth:
    """
    Runtime health and status declaration (spec §4 — required top-level block).
    Allows orchestrators to evaluate node liveness and operational state.
    """
    health_endpoint: str  = ""         # transport endpoint for health checks
    check_interval_ms: int = 30000     # recommended polling interval
    timeout_ms: int = 5000
    expose_metrics: bool = False
    expose_uptime:  bool = True

    def to_dict(self) -> dict:
        return {
            "health_endpoint":    self.health_endpoint,
            "check_interval_ms":  self.check_interval_ms,
            "timeout_ms":         self.timeout_ms,
            "expose_metrics":     self.expose_metrics,
            "expose_uptime":      self.expose_uptime,
        }


@dataclass
class UCINode:
    node_id: str = ""
    instance_id: str = ""
    display_name: str = ""
    node_type: str = "service"
    version: str = "0.1.0"
    vendor: str = ""
    description: str = ""

    def validate(self) -> None:
        if not self.node_id:
            raise UCIManifestError("UCINode requires a non-empty node_id.")
        if not self.instance_id:
            raise UCIManifestError("UCINode requires a non-empty instance_id.")
        if not self.display_name:
            raise UCIManifestError("UCINode requires a non-empty display_name.")
        if self.node_type not in VALID_NODE_TYPES:
            raise UCIValidationError(
                f"Invalid node_type '{self.node_type}'. Must be one of {VALID_NODE_TYPES}."
            )


# ─────────────────────────────────────────────
# Root manifest
# ─────────────────────────────────────────────

@dataclass
class UCIManifest:
    """
    The root UCI manifest document.
    A node exposes exactly one manifest describing itself completely.
    """
    uci_manifest_version: str = "0.1"
    node: UCINode = field(default_factory=UCINode)
    capabilities: list[UCICapability] = field(default_factory=list)
    transports: list[UCITransport] = field(default_factory=list)
    governance: UCIGovernanceMeta = field(default_factory=UCIGovernanceMeta)
    compatibility: dict[str, Any] = field(default_factory=lambda: {
        "supported_manifest_versions": ["0.1"]
    })
    compliance: dict[str, Any] = field(default_factory=lambda: {"profile": "minimal"})
    audit: dict[str, Any] = field(default_factory=lambda: {"audit_enabled": True})
    extensions: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    health: UCIHealth = field(default_factory=UCIHealth)

    # ── Validation ──────────────────────────────────

    def validate(self) -> None:
        """
        Full structural and semantic validation.
        Raises UCIManifestError or UCIValidationError on failure.
        """
        self._check_version()
        self.node.validate()
        self.governance.validate()
        if not self.capabilities:
            raise UCIManifestError("UCIManifest requires at least one capability.")
        if not self.transports:
            raise UCIManifestError("UCIManifest requires at least one transport.")
        for cap in self.capabilities:
            cap.validate()
        for transport in self.transports:
            transport.validate()

    def _validate_health(self) -> None:
        """Health block exists — no validation errors possible in v0.1."""
        pass

    def _check_version(self) -> None:
        if self.uci_manifest_version not in SUPPORTED_MANIFEST_VERSIONS:
            raise UCIValidationError(
                f"Unsupported manifest version '{self.uci_manifest_version}'. "
                f"Supported: {SUPPORTED_MANIFEST_VERSIONS}."
            )

    # ── Accessors ───────────────────────────────────

    def get_capability(self, capability_id: str) -> Optional[UCICapability]:
        for cap in self.capabilities:
            if cap.capability_id == capability_id:
                return cap
        return None

    def get_action(self, capability_id: str, action_id: str) -> Optional[UCIAction]:
        cap = self.get_capability(capability_id)
        if cap:
            return cap.get_action(action_id)
        return None

    def capability_ids(self) -> list[str]:
        return [c.capability_id for c in self.capabilities]

    def is_compatible_with(self, orchestrator_versions: list[str]) -> bool:
        """Check if this manifest's version is in the orchestrator's supported list."""
        return self.uci_manifest_version in orchestrator_versions

    # ── Serialisation ───────────────────────────────

    def to_dict(self) -> dict:
        """Shallow dict representation suitable for JSON serialisation."""
        return {
            "uci_manifest_version": self.uci_manifest_version,
            "node": {
                "node_id":      self.node.node_id,
                "instance_id":  self.node.instance_id,
                "display_name": self.node.display_name,
                "node_type":    self.node.node_type,
                "version":      self.node.version,
                "vendor":       self.node.vendor,
            },
            "capabilities": [
                {
                    "capability_id": c.capability_id,
                    "version":       c.version,
                    "category":      c.category,
                    "description":   c.description,
                    "actions": [
                        {
                            "action_id":   a.action_id,
                            "description": a.description,
                            "execution": {
                                "mode":                  a.execution.mode,
                                "timeout_ms":            a.execution.timeout_ms,
                                "idempotent":            a.execution.idempotent,
                                "side_effects":          a.execution.side_effects,
                                "rollback_supported":    a.execution.rollback_supported,
                                "requires_confirmation": a.execution.requires_confirmation,
                            },
                            "risk": {
                                "level":       a.risk.level,
                                "categories":  a.risk.categories,
                                "description": a.risk.description,
                            },
                            "permissions": {
                                "required_permissions":  a.permissions.required_permissions,
                                "operator_confirmation": a.permissions.operator_confirmation,
                                "minimum_trust_state":   a.permissions.minimum_trust_state,
                            },
                            "input_schema":  a.input_schema,
                            "output_schema": a.output_schema,
                            "errors":        a.errors,
                        }
                        for a in c.actions
                    ],
                }
                for c in self.capabilities
            ],
            "governance": {
                "requires_policy_check":    self.governance.requires_policy_check,
                "audit_required":           self.governance.audit_required,
                "default_action_policy":    self.governance.default_action_policy,
                "operator_authority_required": self.governance.operator_authority_required,
                "signed_invocations_required": self.governance.requires_signed_requests,
            },
            "transports": [
                {
                    "transport_id": t.transport_id,
                    "type":         t.type,
                    "endpoint":     t.endpoint,
                    "security":     t.security,
                    "options":      t.options,
                }
                for t in self.transports
            ],
            "compatibility": self.compatibility,
            "compliance":    self.compliance,
            "audit":         self.audit,
            "extensions":    self.extensions,
            "health":         self.health.to_dict() if self.health else {},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UCIManifest":
        """
        Deserialise a manifest from a plain dict (e.g. from JSON).
        Performs structural checks but does NOT call validate() — caller must do that.
        """
        if not isinstance(data, dict):
            raise UCIManifestError("Manifest must be a dict.")

        version = data.get("uci_manifest_version", "")
        if not version:
            raise UCIManifestError("Manifest missing 'uci_manifest_version'.")

        raw_node = data.get("node", {})
        if not raw_node:
            raise UCIManifestError("Manifest missing 'node' section.")

        node = UCINode(
            node_id      = raw_node.get("node_id", ""),
            instance_id  = raw_node.get("instance_id", ""),
            display_name = raw_node.get("display_name", ""),
            node_type    = raw_node.get("node_type", "service"),
            version      = raw_node.get("version", "0.1.0"),
            vendor       = raw_node.get("vendor", ""),
            description  = raw_node.get("description", ""),
        )

        capabilities = []
        for raw_cap in data.get("capabilities", []):
            actions = []
            for raw_act in raw_cap.get("actions", []):
                raw_exec = raw_act.get("execution", {})
                raw_risk = raw_act.get("risk", {})
                raw_perm = raw_act.get("permissions", {})
                actions.append(UCIAction(
                    action_id   = raw_act.get("action_id", ""),
                    description = raw_act.get("description", ""),
                    execution   = UCIExecution(
                        mode                  = raw_exec.get("mode", "sync"),
                        timeout_ms            = raw_exec.get("timeout_ms", 10000),
                        idempotent            = raw_exec.get("idempotent", False),
                        side_effects          = raw_exec.get("side_effects", False),
                        rollback_supported    = raw_exec.get("rollback_supported", False),
                        requires_confirmation = raw_exec.get("requires_confirmation", False),
                    ),
                    risk        = UCIRisk(
                        level       = raw_risk.get("level", "low"),
                        categories  = raw_risk.get("categories", []),
                        description = raw_risk.get("description", ""),
                    ),
                    permissions = UCIPermissions(
                        required_permissions  = raw_perm.get("required_permissions", []),
                        operator_confirmation = raw_perm.get("operator_confirmation", "none"),
                        minimum_trust_state   = raw_perm.get("minimum_trust_state", "trusted"),
                    ),
                    input_schema  = raw_act.get("input_schema", {}),
                    output_schema = raw_act.get("output_schema", {}),
                    errors        = raw_act.get("errors", []),
                ))
            capabilities.append(UCICapability(
                capability_id = raw_cap.get("capability_id", ""),
                version       = raw_cap.get("version", "1.0"),
                category      = raw_cap.get("category", ""),
                description   = raw_cap.get("description", ""),
                actions       = actions,
                tags          = raw_cap.get("tags", []),
            ))

        raw_gov = data.get("governance", {})
        governance = UCIGovernanceMeta(
            requires_policy_check      = raw_gov.get("requires_policy_check", True),
            audit_required             = raw_gov.get("audit_required", True),
            operator_authority_required= raw_gov.get("operator_authority_required", True),
            default_action_policy      = raw_gov.get("default_action_policy", "deny"),
            sandbox_required           = raw_gov.get("sandbox_required", False),
            allow_remote_execution     = raw_gov.get("allow_remote_execution", False),
            requires_signed_requests   = raw_gov.get("signed_invocations_required", raw_gov.get("requires_signed_requests", False)),
        )

        transports = []
        for raw_t in data.get("transports", []):
            transports.append(UCITransport(
                transport_id = raw_t.get("transport_id", ""),
                type         = raw_t.get("type", "ipc"),
                endpoint     = raw_t.get("endpoint", ""),
                security     = raw_t.get("security", {}),
                options      = raw_t.get("options", {}),
            ))

        return cls(
            uci_manifest_version = version,
            node                 = node,
            capabilities         = capabilities,
            transports           = transports,
            governance           = governance,
            compatibility        = data.get("compatibility", {"supported_manifest_versions": ["0.1"]}),
            compliance           = data.get("compliance", {"profile": "minimal"}),
            audit                = data.get("audit", {"audit_enabled": True}),
            extensions           = data.get("extensions", {}),
            metadata             = data.get("metadata", {}),
            health               = UCIHealth(
                **{k: v for k, v in data.get("health", {}).items()
                   if k in {"health_endpoint", "check_interval_ms",
                            "timeout_ms", "expose_metrics", "expose_uptime"}}
            ),
        )
