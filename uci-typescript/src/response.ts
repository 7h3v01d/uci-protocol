/**
 * UCI Response Envelope
 * Every invocation returns exactly one UCIResponse — never throws.
 */

import { UCIError } from "./errors.js";
import { randomUUID } from "crypto";

export const RESPONSE_VERSION = "0.1";

export const UCIErrorSeverity = {
  INFO:     "info",
  LOW:      "low",
  MEDIUM:   "medium",
  HIGH:     "high",
  CRITICAL: "critical",
} as const;

export const UCIErrorCode = {
  // Validation
  VALIDATION_ERROR:      "validation_error",
  SCHEMA_ERROR:          "schema_error",
  UNSUPPORTED_VERSION:   "unsupported_version",
  INVALID_INVOCATION:    "invalid_invocation",
  // Governance
  PERMISSION_DENIED:     "permission_denied",
  POLICY_DENIED:         "policy_denied",
  TRUST_FAILURE:         "trust_failure",
  CONFIRMATION_REQUIRED: "confirmation_required",
  NODE_REVOKED:          "node_revoked",
  NODE_SUSPENDED:        "node_suspended",
  // Execution
  EXECUTION_ERROR:       "execution_error",
  TIMEOUT_ERROR:         "timeout_error",
  PROVIDER_UNAVAILABLE:  "provider_unavailable",
  TRANSPORT_ERROR:       "transport_error",
  PARTIAL_FAILURE:       "partial_failure",
  // Compatibility
  UNSUPPORTED_ACTION:    "unsupported_action",
  VERSION_MISMATCH:      "version_mismatch",
  // Internal
  NODE_NOT_FOUND:        "node_not_found",
  GOVERNANCE_ERROR:      "governance_error",
} as const;

export const ResponseState = {
  COMPLETED:           "completed",
  FAILED:              "failed",
  DENIED:              "denied",
  CANCELLED:           "cancelled",
  TIMED_OUT:           "timed_out",
  PARTIALLY_COMPLETED: "partially_completed",
  DEFERRED:            "deferred",
  QUEUED:              "queued",
  EXECUTING:           "executing",
  ROLLED_BACK:         "rolled_back",
} as const;

export type ResponseStateValue = typeof ResponseState[keyof typeof ResponseState];

// ── Sub-structures ──────────────────────────────────────────

export interface UCIResponseError {
  code:      string;
  severity:  string;
  message:   string;
  retryable: boolean;
  detail?:   Record<string, unknown>;
}

export interface UCIResponseProvider {
  node_id:       string;
  instance_id:   string;
  capability_id: string;
  action_id:     string;
}

export interface UCIResponseGovernance {
  outcome:      string;
  trust_state:  string;
  restrictions: string[];
  operator_id:  string | null;
}

export interface UCIResponseAudit {
  invocation_id: string;
  node_id:       string;
  capability_id: string;
  action_id:     string;
  timestamp:     string;
  outcome:       string;
  actor:         string;
}

export interface UCIResponseData {
  uci_response_version: string;
  invocation_id:        string;
  correlation_id:       string;
  timestamp:            string;
  state:                ResponseStateValue;
  success:              boolean;
  provider:             UCIResponseProvider;
  output:               unknown;
  error:                UCIResponseError | null;
  governance:           UCIResponseGovernance;
  audit:                UCIResponseAudit;
}

// ── UCIResponse class ───────────────────────────────────────

export class UCIResponse {
  constructor(public readonly data: UCIResponseData) {}

  get success():       boolean            { return this.data.success; }
  get state():         ResponseStateValue { return this.data.state; }
  get output():        unknown            { return this.data.output; }
  get error():         UCIResponseError | null { return this.data.error; }
  get provider():      UCIResponseProvider     { return this.data.provider; }
  get governance():    UCIResponseGovernance   { return this.data.governance; }
  get audit():         UCIResponseAudit        { return this.data.audit; }
  get invocationId():  string { return this.data.invocation_id; }
  get correlationId(): string { return this.data.correlation_id; }
  get timestamp():     string { return this.data.timestamp; }

  isCompleted():  boolean { return this.state === ResponseState.COMPLETED; }
  isFailed():     boolean { return this.state === ResponseState.FAILED || this.state === ResponseState.DENIED; }
  isDeferred():   boolean { return this.state === ResponseState.DEFERRED; }
  isDenied():     boolean { return this.state === ResponseState.DENIED; }

  assertSuccess(): unknown {
    if (this.success && this.output !== null && this.output !== undefined) {
      return this.output;
    }
    if (this.error) {
      throw new UCIError(`[${this.error.code}] ${this.error.message}`);
    }
    throw new UCIError(`Response state='${this.state}' success=${this.success} — no output.`);
  }

  toDict(): UCIResponseData { return structuredClone(this.data); }

  toJSON(): string { return JSON.stringify(this.toDict(), null, 2); }

  static fromDict(data: unknown): UCIResponse {
    return new UCIResponse(data as UCIResponseData);
  }

  // ── Factories ─────────────────────────────────────────────

  static successResponse(params: {
    output:             unknown;
    nodeId:             string;
    instanceId:         string;
    capabilityId:       string;
    actionId:           string;
    trustState?:        string;
    governanceOutcome?: string;
    restrictions?:      string[];
    operatorId?:        string | null;
    correlationId?:     string;
    actor?:             string;
  }): UCIResponse {
    const id = randomUUID();
    const ts = new Date().toISOString();
    return new UCIResponse({
      uci_response_version: RESPONSE_VERSION,
      invocation_id:        id,
      correlation_id:       params.correlationId ?? randomUUID(),
      timestamp:            ts,
      state:                ResponseState.COMPLETED,
      success:              true,
      provider: {
        node_id:       params.nodeId,
        instance_id:   params.instanceId,
        capability_id: params.capabilityId,
        action_id:     params.actionId,
      },
      output:      params.output,
      error:       null,
      governance: {
        outcome:      params.governanceOutcome ?? "allow",
        trust_state:  params.trustState ?? "trusted",
        restrictions: params.restrictions ?? [],
        operator_id:  params.operatorId ?? null,
      },
      audit: {
        invocation_id: id,
        node_id:       params.nodeId,
        capability_id: params.capabilityId,
        action_id:     params.actionId,
        timestamp:     ts,
        outcome:       params.governanceOutcome ?? "allow",
        actor:         params.actor ?? "uci_engine",
      },
    });
  }

  static failureResponse(params: {
    error:              UCIResponseError;
    nodeId?:            string;
    instanceId?:        string;
    capabilityId?:      string;
    actionId?:          string;
    trustState?:        string;
    governanceOutcome?: string;
    correlationId?:     string;
  }): UCIResponse {
    const id    = randomUUID();
    const ts    = new Date().toISOString();
    const state = params.governanceOutcome === "deny"
      ? ResponseState.DENIED
      : ResponseState.FAILED;
    return new UCIResponse({
      uci_response_version: RESPONSE_VERSION,
      invocation_id:        id,
      correlation_id:       params.correlationId ?? randomUUID(),
      timestamp:            ts,
      state,
      success:              false,
      provider: {
        node_id:       params.nodeId ?? "",
        instance_id:   params.instanceId ?? "",
        capability_id: params.capabilityId ?? "",
        action_id:     params.actionId ?? "",
      },
      output:  null,
      error:   params.error,
      governance: {
        outcome:      params.governanceOutcome ?? "deny",
        trust_state:  params.trustState ?? "unknown",
        restrictions: [],
        operator_id:  null,
      },
      audit: {
        invocation_id: id,
        node_id:       params.nodeId ?? "",
        capability_id: params.capabilityId ?? "",
        action_id:     params.actionId ?? "",
        timestamp:     ts,
        outcome:       "error",
        actor:         "uci_engine",
      },
    });
  }

  static deferredResponse(params: {
    nodeId:        string;
    instanceId:    string;
    capabilityId:  string;
    actionId:      string;
    trustState?:   string;
    reason?:       string;
    correlationId?: string;
  }): UCIResponse {
    const id = randomUUID();
    const ts = new Date().toISOString();
    return new UCIResponse({
      uci_response_version: RESPONSE_VERSION,
      invocation_id:        id,
      correlation_id:       params.correlationId ?? randomUUID(),
      timestamp:            ts,
      state:                ResponseState.DEFERRED,
      success:              false,
      provider: {
        node_id:       params.nodeId,
        instance_id:   params.instanceId,
        capability_id: params.capabilityId,
        action_id:     params.actionId,
      },
      output: null,
      error: {
        code:      UCIErrorCode.CONFIRMATION_REQUIRED,
        severity:  UCIErrorSeverity.LOW,
        message:   params.reason ?? "Operator confirmation required.",
        retryable: true,
      },
      governance: {
        outcome:      "defer",
        trust_state:  params.trustState ?? "trusted",
        restrictions: [],
        operator_id:  null,
      },
      audit: {
        invocation_id: id,
        node_id:       params.nodeId,
        capability_id: params.capabilityId,
        action_id:     params.actionId,
        timestamp:     ts,
        outcome:       "defer",
        actor:         "uci_engine",
      },
    });
  }

  static fromException(params: {
    error:         unknown;
    nodeId?:       string;
    capabilityId?: string;
    actionId?:     string;
    code?:         string;
    correlationId?: string;
  }): UCIResponse {
    const message = params.error instanceof Error
      ? params.error.message
      : String(params.error);
    return UCIResponse.failureResponse({
      error: {
        code:      params.code ?? UCIErrorCode.EXECUTION_ERROR,
        severity:  UCIErrorSeverity.MEDIUM,
        message,
        retryable: false,
        detail:    { exceptionType: params.error instanceof Error ? params.error.name : "unknown" },
      },
      nodeId:        params.nodeId,
      capabilityId:  params.capabilityId,
      actionId:      params.actionId,
      correlationId: params.correlationId,
    });
  }
}
