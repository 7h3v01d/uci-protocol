/**
 * UCI Manifest
 * Canonical structure for a UCI capability manifest (v0.1).
 */

import { UCIManifestError, UCIValidationError } from "./errors.js";

export const SUPPORTED_MANIFEST_VERSIONS = new Set(["0.1"]);

export const VALID_NODE_TYPES = new Set([
  "application", "service", "agent", "daemon",
  "adapter", "hardware_bridge", "orchestrator",
  "policy_engine", "registry",
]);

export const VALID_EXECUTION_MODES = new Set([
  "sync", "async", "streaming", "scheduled", "event_driven",
]);

export const VALID_TRANSPORT_TYPES = new Set([
  "http", "https", "websocket", "ipc",
  "grpc", "message_bus", "local_socket", "custom",
]);

export const VALID_RISK_LEVELS = new Set([
  "none", "low", "medium", "high", "critical",
]);

export const VALID_CAPABILITY_CATEGORIES = new Set([
  "retrieval", "storage", "generation", "analysis",
  "transformation", "communication", "execution",
  "governance", "monitoring", "vision", "audio",
  "identity", "network", "security", "utility", "other",
]);

export const VALID_CONFIRMATION_LEVELS = new Set([
  "none", "recommended", "required",
  "required_with_reason", "multi_party_required",
]);

export const VALID_TRUST_STATES = new Set([
  "unknown", "discovered", "verified",
  "trusted", "restricted", "suspended", "revoked",
]);

// ── Sub-structures ──────────────────────────────────────────

export interface UCIRisk {
  level:       string;
  categories?: string[];
  description?: string;
}

export interface UCIPermissions {
  required_permissions?:  string[];
  operator_confirmation?: string;
  minimum_trust_state?:   string;
}

export interface UCIExecution {
  mode:                   string;
  timeout_ms:             number;
  idempotent?:            boolean;
  side_effects?:          boolean;
  rollback_supported?:    boolean;
  requires_confirmation?: boolean;
}

export interface UCIAction {
  action_id:     string;
  description?:  string;
  execution:     UCIExecution;
  risk:          UCIRisk;
  permissions?:  UCIPermissions;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  errors?:       unknown[];
}

export interface UCICapability {
  capability_id: string;
  version:       string;
  category:      string;
  description?:  string;
  tags?:         string[];
  actions:       UCIAction[];
}

export interface UCITransport {
  transport_id: string;
  type:         string;
  endpoint:     string;
  security?:    Record<string, unknown>;
  options?:     Record<string, unknown>;
}

export interface UCINode {
  node_id:       string;
  instance_id:   string;
  display_name:  string;
  node_type:     string;
  version:       string;
  vendor?:       string;
  description?:  string;
}

export interface UCIGovernanceMeta {
  requires_policy_check?:       boolean;
  audit_required?:              boolean;
  operator_authority_required?: boolean;
  default_action_policy?:       string;
  sandbox_required?:            boolean;
  allow_remote_execution?:      boolean;
  signed_invocations_required?: boolean;
}

export interface UCIHealth {
  health_endpoint?:    string;
  check_interval_ms?:  number;
  timeout_ms?:         number;
  expose_metrics?:     boolean;
  expose_uptime?:      boolean;
}

// ── Root manifest ───────────────────────────────────────────

export interface UCIManifestData {
  uci_manifest_version: string;
  node:                 UCINode;
  capabilities:         UCICapability[];
  transports:           UCITransport[];
  governance:           UCIGovernanceMeta;
  health:               UCIHealth;
  compliance?:          Record<string, unknown>;
  audit?:               Record<string, unknown>;
  extensions?:          Record<string, unknown>;
  metadata?:            Record<string, unknown>;
  compatibility?:       Record<string, unknown>;
}

export class UCIManifest {
  constructor(public readonly data: UCIManifestData) {}

  // ── Validation ────────────────────────────────────────────

  validate(): void {
    this._checkVersion();
    this._validateNode();
    this._validateCapabilities();
    this._validateTransports();
    this._validateGovernance();
  }

  private _checkVersion(): void {
    if (!SUPPORTED_MANIFEST_VERSIONS.has(this.data.uci_manifest_version)) {
      throw new UCIValidationError(
        `Unsupported manifest version '${this.data.uci_manifest_version}'. ` +
        `Supported: ${[...SUPPORTED_MANIFEST_VERSIONS].join(", ")}`
      );
    }
  }

  private _validateNode(): void {
    const n = this.data.node;
    if (!n?.node_id)      throw new UCIManifestError("UCINode requires a non-empty node_id.");
    if (!n.instance_id)   throw new UCIManifestError("UCINode requires a non-empty instance_id.");
    if (!n.display_name)  throw new UCIManifestError("UCINode requires a non-empty display_name.");
    if (!VALID_NODE_TYPES.has(n.node_type)) {
      throw new UCIValidationError(
        `Invalid node_type '${n.node_type}'. Must be one of: ${[...VALID_NODE_TYPES].join(", ")}`
      );
    }
  }

  private _validateCapabilities(): void {
    if (!this.data.capabilities?.length) {
      throw new UCIManifestError("Manifest must declare at least one capability.");
    }
    for (const cap of this.data.capabilities) {
      if (!cap.capability_id) {
        throw new UCIManifestError("UCICapability requires a non-empty capability_id.");
      }
      if (!VALID_CAPABILITY_CATEGORIES.has(cap.category)) {
        throw new UCIValidationError(
          `Invalid capability category '${cap.category}'.`
        );
      }
      if (!cap.actions?.length) {
        throw new UCIManifestError(
          `Capability '${cap.capability_id}' must declare at least one action.`
        );
      }
      for (const action of cap.actions) {
        this._validateAction(action, cap.capability_id);
      }
    }
  }

  private _validateAction(action: UCIAction, capId: string): void {
    if (!action.action_id) {
      throw new UCIManifestError(`Action in capability '${capId}' requires a non-empty action_id.`);
    }
    if (!VALID_EXECUTION_MODES.has(action.execution?.mode)) {
      throw new UCIValidationError(
        `Invalid execution mode '${action.execution?.mode}' in action '${capId}/${action.action_id}'.`
      );
    }
    if ((action.execution?.timeout_ms ?? 0) < 1) {
      throw new UCIValidationError(
        `timeout_ms must be >= 1 in action '${capId}/${action.action_id}'.`
      );
    }
    if (!VALID_RISK_LEVELS.has(action.risk?.level)) {
      throw new UCIValidationError(
        `Invalid risk level '${action.risk?.level}' in action '${capId}/${action.action_id}'.`
      );
    }
    if (action.permissions?.operator_confirmation &&
        !VALID_CONFIRMATION_LEVELS.has(action.permissions.operator_confirmation)) {
      throw new UCIValidationError(
        `Invalid operator_confirmation '${action.permissions.operator_confirmation}'.`
      );
    }
  }

  private _validateTransports(): void {
    if (!this.data.transports?.length) {
      throw new UCIManifestError("Manifest must declare at least one transport.");
    }
    for (const t of this.data.transports) {
      if (!t.transport_id) {
        throw new UCIManifestError("UCITransport requires a non-empty transport_id.");
      }
      if (!VALID_TRANSPORT_TYPES.has(t.type)) {
        throw new UCIValidationError(
          `Invalid transport type '${t.type}'. Must be one of: ${[...VALID_TRANSPORT_TYPES].join(", ")}`
        );
      }
      if (!t.endpoint) {
        throw new UCIManifestError(`UCITransport '${t.transport_id}' requires a non-empty endpoint.`);
      }
    }
  }

  private _validateGovernance(): void {
    const policy = this.data.governance?.default_action_policy;
    if (policy && !["allow", "deny", "defer"].includes(policy)) {
      throw new UCIValidationError(
        `Invalid default_action_policy '${policy}'. Must be allow, deny, or defer.`
      );
    }
  }

  // ── Accessors ─────────────────────────────────────────────

  get nodeId():      string { return this.data.node.node_id; }
  get displayName(): string { return this.data.node.display_name; }
  get version():     string { return this.data.uci_manifest_version; }

  capabilityIds(): string[] {
    return this.data.capabilities.map(c => c.capability_id);
  }

  getCapability(capabilityId: string): UCICapability | undefined {
    return this.data.capabilities.find(c => c.capability_id === capabilityId);
  }

  getAction(capabilityId: string, actionId: string): UCIAction | undefined {
    return this.getCapability(capabilityId)?.actions.find(a => a.action_id === actionId);
  }

  isCompatibleWith(versions: string[]): boolean {
    return versions.includes(this.data.uci_manifest_version);
  }

  toDict(): UCIManifestData {
    return structuredClone(this.data);
  }

  static fromDict(data: unknown): UCIManifest {
    if (typeof data !== "object" || data === null) {
      throw new UCIManifestError("Manifest must be a JSON object.");
    }
    const d = data as Record<string, unknown>;
    if (!d.uci_manifest_version) {
      throw new UCIManifestError("Manifest missing 'uci_manifest_version'.");
    }
    if (!d.node) {
      throw new UCIManifestError("Manifest missing 'node' section.");
    }
    return new UCIManifest(d as unknown as UCIManifestData);
  }
}
