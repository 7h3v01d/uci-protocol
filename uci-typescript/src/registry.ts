/**
 * UCI Registry & Handshake
 */

import { UCIManifest }    from "./manifest.js";
import { TrustRecord, TrustState } from "./trust.js";
import { UCIRegistryError }        from "./errors.js";
import { AuditLog, AuditEvent }    from "./audit.js";
import { PolicyEngine, GovernanceOutcome } from "./governance.js";

// ── Registry ────────────────────────────────────────────────

export interface NodeEntry {
  nodeId:               string;
  manifest:             UCIManifest;
  trust:                TrustRecord;
  registeredAt:         string;
  mountedCapabilities:  string[];
}

export class UCIRegistry {
  private readonly _nodes = new Map<string, NodeEntry>();

  register(manifest: UCIManifest, trust: TrustRecord): NodeEntry {
    const nodeId = manifest.nodeId;
    if (this._nodes.has(nodeId)) {
      throw new UCIRegistryError(`Node '${nodeId}' is already registered.`);
    }
    const entry: NodeEntry = {
      nodeId,
      manifest,
      trust,
      registeredAt:        new Date().toISOString(),
      mountedCapabilities: [],
    };
    this._nodes.set(nodeId, entry);
    return entry;
  }

  update(manifest: UCIManifest, trust: TrustRecord): NodeEntry {
    const nodeId = manifest.nodeId;
    if (!this._nodes.has(nodeId)) return this.register(manifest, trust);
    const entry = this._nodes.get(nodeId)!;
    entry.manifest = manifest;
    entry.trust    = trust;
    return entry;
  }

  get(nodeId: string):     NodeEntry | undefined { return this._nodes.get(nodeId); }
  require(nodeId: string): NodeEntry {
    const e = this._nodes.get(nodeId);
    if (!e) throw new UCIRegistryError(`Node '${nodeId}' not found in registry.`);
    return e;
  }

  mountCapability(nodeId: string, capabilityId: string): void {
    const e = this.require(nodeId);
    if (!e.mountedCapabilities.includes(capabilityId)) {
      e.mountedCapabilities.push(capabilityId);
    }
  }

  allNodes():   NodeEntry[] { return [...this._nodes.values()]; }
  readyNodes(): NodeEntry[] {
    return this.allNodes().filter(
      e => e.trust.canExecute() && e.mountedCapabilities.length > 0
    );
  }

  count(): number { return this._nodes.size; }

  summary() {
    return {
      total_nodes: this.count(),
      ready:       this.readyNodes().length,
      nodes:       this.allNodes().map(e => ({
        node_id:      e.nodeId,
        trust:        e.trust.state,
        capabilities: e.mountedCapabilities,
        is_ready:     e.trust.canExecute() && e.mountedCapabilities.length > 0,
      })),
    };
  }
}

// ── Handshake ───────────────────────────────────────────────

export const HandshakeStage = {
  PENDING:               "pending",
  DISCOVERED:            "discovered",
  MANIFEST_RETRIEVED:    "manifest_retrieved",
  MANIFEST_VALIDATED:    "manifest_validated",
  COMPATIBILITY_CHECKED: "compatibility_checked",
  GOVERNANCE_EVALUATED:  "governance_evaluated",
  TRUST_ASSIGNED:        "trust_assigned",
  CAPABILITIES_MOUNTED:  "capabilities_mounted",
  READY:                 "ready",
  FAILED:                "failed",
} as const;

export type HandshakeStageValue = typeof HandshakeStage[keyof typeof HandshakeStage];

export interface HandshakeResult {
  success:              boolean;
  nodeId:               string;
  stageReached:         HandshakeStageValue;
  trustState:           string;
  mountedCapabilities:  string[];
  failureReason:        string;
  warnings:             string[];
}

const SUPPORTED_VERSIONS = ["0.1"];

export class HandshakeEngine {
  constructor(
    private readonly policy:   PolicyEngine,
    private readonly registry: UCIRegistry,
    private readonly audit:    AuditLog,
  ) {}

  run(nodeId: string, manifestData: unknown, preTrusted = false): HandshakeResult {
    let   stage    = HandshakeStage.PENDING as HandshakeStageValue;
    const trust    = new TrustRecord(nodeId);
    const warnings: string[] = [];

    const fail = (reason: string): HandshakeResult => {
      this.audit.append({
        eventType: AuditEvent.HANDSHAKE_FAILED, nodeId,
        actor: "handshake_engine", outcome: "deny",
        detail: { stage, reason },
      });
      return { success: false, nodeId, stageReached: stage,
               trustState: trust.state, mountedCapabilities: [],
               failureReason: reason, warnings };
    };

    try {
      // Stage 1: Discovered
      stage = HandshakeStage.DISCOVERED;
      trust.transition(TrustState.DISCOVERED, "handshake_engine", "Node endpoint reached");
      this.audit.append({ eventType: AuditEvent.NODE_DISCOVERED, nodeId, actor: "handshake_engine" });

      // Stage 2: Manifest retrieved
      stage = HandshakeStage.MANIFEST_RETRIEVED;
      this.audit.append({ eventType: AuditEvent.MANIFEST_RETRIEVED, nodeId, actor: "handshake_engine" });

      // Stage 3: Manifest validated
      stage = HandshakeStage.MANIFEST_VALIDATED;
      let manifest: UCIManifest;
      try {
        manifest = UCIManifest.fromDict(manifestData);
        manifest.validate();
      } catch (err) {
        this.audit.append({
          eventType: AuditEvent.MANIFEST_VALIDATION_FAILED, nodeId,
          actor: "handshake_engine", outcome: "deny",
          detail: { reason: String(err) },
        });
        return fail(`Manifest validation failed: ${err}`);
      }
      this.audit.append({
        eventType: AuditEvent.MANIFEST_VALIDATION_PASSED, nodeId,
        actor: "handshake_engine",
        detail: { capabilities: manifest.capabilityIds() },
      });

      // Stage 4: Compatibility
      stage = HandshakeStage.COMPATIBILITY_CHECKED;
      if (!manifest.isCompatibleWith(SUPPORTED_VERSIONS)) {
        this.audit.append({
          eventType: AuditEvent.COMPATIBILITY_REJECTED, nodeId,
          actor: "handshake_engine", outcome: "deny",
          detail: { manifest_version: manifest.version },
        });
        return fail(`Manifest version '${manifest.version}' not in supported ${SUPPORTED_VERSIONS}.`);
      }
      this.audit.append({ eventType: AuditEvent.COMPATIBILITY_ACCEPTED, nodeId, actor: "handshake_engine" });
      trust.transition(TrustState.VERIFIED, "handshake_engine", "Manifest validated and compatible");

      // Stage 5: Governance
      stage = HandshakeStage.GOVERNANCE_EVALUATED;
      const govDecision = this.policy.evaluateManifest(manifest, trust);
      this.audit.append({
        eventType: AuditEvent.POLICY_EVALUATED, nodeId,
        actor: "policy_engine", outcome: govDecision.outcome,
        detail: { reason: govDecision.reason },
      });
      if (govDecision.outcome === GovernanceOutcome.DENY) {
        return fail(`Governance denied: ${govDecision.reason}`);
      }

      // Stage 6: Trust assigned
      stage = HandshakeStage.TRUST_ASSIGNED;
      const newTrust = (preTrusted || govDecision.outcome === GovernanceOutcome.ALLOW)
        ? TrustState.TRUSTED
        : TrustState.RESTRICTED;
      trust.transition(newTrust, "policy_engine", govDecision.reason);
      this.audit.append({
        eventType: AuditEvent.TRUST_ASSIGNED, nodeId,
        actor: "policy_engine",
        detail: { trust_state: newTrust },
      });

      // Stage 7: Mount capabilities
      stage = HandshakeStage.CAPABILITIES_MOUNTED;
      const mounted: string[] = [];
      try { this.registry.register(manifest, trust); }
      catch { this.registry.update(manifest, trust); }

      for (const cap of manifest.data.capabilities) {
        if (newTrust === TrustState.RESTRICTED) {
          const hasHighRisk = cap.actions.some(
            a => ["high", "critical"].includes(a.risk?.level ?? "")
          );
          if (hasHighRisk) {
            warnings.push(
              `Capability '${cap.capability_id}' not mounted — contains high-risk actions and node is restricted.`
            );
            this.audit.append({
              eventType: AuditEvent.CAPABILITY_REVOKED, nodeId,
              actor: "handshake_engine", outcome: "deny",
              detail: { capability_id: cap.capability_id },
            });
            continue;
          }
        }
        this.registry.mountCapability(nodeId, cap.capability_id);
        mounted.push(cap.capability_id);
        this.audit.append({
          eventType: AuditEvent.CAPABILITY_MOUNTED, nodeId,
          actor: "handshake_engine",
          detail: { capability_id: cap.capability_id },
        });
      }

      // Stage 8: Ready
      stage = HandshakeStage.READY;
      this.audit.append({
        eventType: AuditEvent.NODE_READY, nodeId,
        actor: "handshake_engine",
        detail: { mounted_capabilities: mounted, trust_state: newTrust },
      });

      return {
        success:             true,
        nodeId,
        stageReached:        HandshakeStage.READY,
        trustState:          newTrust,
        mountedCapabilities: mounted,
        failureReason:       "",
        warnings,
      };

    } catch (err) {
      return fail(`Unexpected failure at stage '${stage}': ${err}`);
    }
  }
}
