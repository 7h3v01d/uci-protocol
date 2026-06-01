/**
 * UCI Governance Model
 * Policy engine — deterministic, stateless, fail-closed.
 */

import { AuditLog, AuditEvent } from "./audit.js";
import { UCIManifest }          from "./manifest.js";
import { TrustRecord, TrustState, EXECUTABLE_STATES } from "./trust.js";
import { UCIGovernanceError }   from "./errors.js";

export const GovernanceOutcome = {
  ALLOW:            "allow",
  ALLOW_RESTRICTED: "allow_with_restrictions",
  DEFER:            "defer",
  DENY:             "deny",
} as const;

export type GovernanceOutcomeValue = typeof GovernanceOutcome[keyof typeof GovernanceOutcome];

const RISK_CONFIRMATION_THRESHOLD = new Set(["high", "critical"]);

export const DEFAULT_ORCHESTRATOR_PERMISSIONS = new Set([
  "documents.read", "system.health",
  "search.query",   "voice.tts", "voice.stt",
]);

export interface PolicyDecision {
  outcome:              GovernanceOutcomeValue;
  nodeId:               string;
  capabilityId:         string;
  actionId:             string;
  reason:               string;
  restrictions:         string[];
  requiresConfirmation: boolean;
}

export function isPermitted(d: PolicyDecision): boolean {
  return d.outcome === GovernanceOutcome.ALLOW ||
         d.outcome === GovernanceOutcome.ALLOW_RESTRICTED;
}

export class PolicyEngine {
  constructor(
    private readonly orchestratorPermissions: Set<string> = DEFAULT_ORCHESTRATOR_PERMISSIONS,
    private readonly audit?: AuditLog,
    private readonly requireOperatorForHighRisk = true,
    private readonly strictMode = true,
  ) {}

  evaluateManifest(manifest: UCIManifest, trust: TrustRecord): PolicyDecision {
    const nodeId = manifest.nodeId;

    if (trust.state === TrustState.REVOKED) {
      return this._deny(nodeId, "", "", "Node is revoked.");
    }
    if (trust.state === TrustState.SUSPENDED) {
      return this._deny(nodeId, "", "", "Node is suspended.");
    }
    if (trust.state === TrustState.UNKNOWN) {
      return this.strictMode
        ? this._deny(nodeId, "", "", "Node trust state is unknown.")
        : this._defer(nodeId, "", "", "Node trust state is unknown — awaiting operator.");
    }
    if (manifest.data.governance?.operator_authority_required) {
      return {
        outcome:              GovernanceOutcome.ALLOW_RESTRICTED,
        nodeId, capabilityId: "", actionId: "",
        reason:               "Operator authority required — capabilities mounted with restrictions.",
        restrictions:         ["operator_confirmation_required_for_high_risk_actions"],
        requiresConfirmation: false,
      };
    }
    return this._allow(nodeId, "", "", "Manifest governance requirements satisfied.");
  }

  evaluateAction(
    manifest:           UCIManifest,
    capabilityId:       string,
    actionId:           string,
    trust:              TrustRecord,
    callerPermissions?: Set<string>,
  ): PolicyDecision {
    const nodeId = manifest.nodeId;
    const perms  = callerPermissions ?? this.orchestratorPermissions;

    // ① Trust check
    if (!EXECUTABLE_STATES.has(trust.state)) {
      this.audit?.append({
        eventType: AuditEvent.TRUST_REJECTED, nodeId,
        actor: "policy_engine", outcome: "deny",
        detail: { capability_id: capabilityId, action_id: actionId, trust_state: trust.state },
      });
      return this._deny(nodeId, capabilityId, actionId,
        `Trust state '${trust.state}' does not permit execution.`);
    }

    // ② Capability check
    const cap = manifest.getCapability(capabilityId);
    if (!cap) {
      return this._deny(nodeId, capabilityId, actionId,
        `Capability '${capabilityId}' not found in manifest.`);
    }

    // ③ Action check
    const action = cap.actions.find(a => a.action_id === actionId);
    if (!action) {
      return this._deny(nodeId, capabilityId, actionId,
        `Action '${actionId}' not found in capability '${capabilityId}'.`);
    }

    // ④ Permission check
    const required = new Set(action.permissions?.required_permissions ?? []);
    const missing  = [...required].filter(p => !perms.has(p));
    if (missing.length) {
      this.audit?.append({
        eventType: AuditEvent.PERMISSION_DENIED, nodeId,
        actor: "policy_engine", outcome: "deny",
        detail: { capability_id: capabilityId, action_id: actionId, missing_permissions: missing },
      });
      return this._deny(nodeId, capabilityId, actionId,
        `Missing required permissions: ${missing.join(", ")}.`);
    }

    // ⑤ Risk / confirmation check
    const riskLevel = action.risk?.level ?? "low";
    const requiresConfirmation =
      action.execution?.requires_confirmation === true ||
      ["required", "required_with_reason", "multi_party_required"]
        .includes(action.permissions?.operator_confirmation ?? "") ||
      (this.requireOperatorForHighRisk && RISK_CONFIRMATION_THRESHOLD.has(riskLevel));

    if (requiresConfirmation) {
      this.audit?.append({
        eventType: AuditEvent.CONFIRMATION_REQUESTED, nodeId,
        actor: "policy_engine", outcome: "defer",
        detail: { capability_id: capabilityId, action_id: actionId, risk_level: riskLevel },
      });
      return this._defer(nodeId, capabilityId, actionId,
        `Risk level '${riskLevel}' requires operator confirmation.`);
    }

    // ⑥ Restricted trust
    if (trust.state === TrustState.RESTRICTED) {
      this.audit?.append({
        eventType: AuditEvent.EXECUTION_RESTRICTED, nodeId,
        actor: "policy_engine", outcome: GovernanceOutcome.ALLOW_RESTRICTED,
        detail: { capability_id: capabilityId, action_id: actionId },
      });
      return {
        outcome:              GovernanceOutcome.ALLOW_RESTRICTED,
        nodeId, capabilityId, actionId,
        reason:               "Node is restricted — execution permitted with limitations.",
        restrictions:         ["rate_limited", "no_side_effects_permitted"],
        requiresConfirmation: false,
      };
    }

    // ⑦ Allow
    this.audit?.append({
      eventType: AuditEvent.EXECUTION_ALLOWED, nodeId,
      actor: "policy_engine", outcome: GovernanceOutcome.ALLOW,
      detail: { capability_id: capabilityId, action_id: actionId, risk_level: riskLevel },
    });
    return this._allow(nodeId, capabilityId, actionId, "All governance checks passed.");
  }

  operatorApprove(decision: PolicyDecision, operatorId: string): PolicyDecision {
    if (decision.outcome !== GovernanceOutcome.DEFER) {
      throw new UCIGovernanceError(
        "operatorApprove called on a non-deferred decision.", decision.outcome
      );
    }
    this.audit?.append({
      eventType: AuditEvent.CONFIRMATION_APPROVED,
      nodeId:    decision.nodeId, actor: operatorId, outcome: GovernanceOutcome.ALLOW,
      detail: { capability_id: decision.capabilityId, action_id: decision.actionId, operator: operatorId },
    });
    return {
      outcome:              GovernanceOutcome.ALLOW,
      nodeId:               decision.nodeId,
      capabilityId:         decision.capabilityId,
      actionId:             decision.actionId,
      reason:               `Approved by operator '${operatorId}'.`,
      restrictions:         [],
      requiresConfirmation: false,
    };
  }

  private _allow(nodeId: string, capabilityId: string, actionId: string, reason: string): PolicyDecision {
    return { outcome: GovernanceOutcome.ALLOW, nodeId, capabilityId, actionId, reason, restrictions: [], requiresConfirmation: false };
  }
  private _deny(nodeId: string, capabilityId: string, actionId: string, reason: string): PolicyDecision {
    return { outcome: GovernanceOutcome.DENY, nodeId, capabilityId, actionId, reason, restrictions: [], requiresConfirmation: false };
  }
  private _defer(nodeId: string, capabilityId: string, actionId: string, reason: string): PolicyDecision {
    return { outcome: GovernanceOutcome.DEFER, nodeId, capabilityId, actionId, reason, restrictions: [], requiresConfirmation: true };
  }
}
