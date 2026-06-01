/**
 * UCI Invocation
 * Canonical request object — the first-class way to invoke a UCI action.
 */

import { randomUUID } from "crypto";

export const INVOCATION_VERSION = "0.1";

export interface UCIInvocationCaller {
  node_id:     string;
  instance_id: string;
  actor_type:  string;
}

export interface UCIInvocationTarget {
  node_id:       string;
  capability_id: string;
  action_id:     string;
}

export interface UCIInvocationContext {
  session_id:     string;
  operator_id:    string;
  risk_posture:   string;
  policy_profile: string;
  network_zone:   string;
  environment:    string;
  tags:           Record<string, string>;
}

export interface UCIInvocationData {
  uci_invocation_version: string;
  invocation_id:          string;
  correlation_id:         string;
  timestamp:              string;
  caller:                 UCIInvocationCaller;
  target:                 UCIInvocationTarget;
  payload:                Record<string, unknown>;
  context:                UCIInvocationContext;
  operator_override:      string | null;
  require_confirmation:   boolean;
}

export class UCIInvocation {
  constructor(public readonly data: UCIInvocationData) {}

  get nodeId():          string { return this.data.target.node_id; }
  get capabilityId():    string { return this.data.target.capability_id; }
  get actionId():        string { return this.data.target.action_id; }
  get payload():         Record<string, unknown> { return this.data.payload; }
  get correlationId():   string { return this.data.correlation_id; }
  get operatorOverride(): string | null { return this.data.operator_override; }

  toDict(): UCIInvocationData { return structuredClone(this.data); }
  toJSON(): string            { return JSON.stringify(this.toDict(), null, 2); }

  static fromDict(data: UCIInvocationData): UCIInvocation {
    return new UCIInvocation(structuredClone(data));
  }

  static create(params: {
    nodeId:           string;
    capabilityId:     string;
    actionId:         string;
    payload?:         Record<string, unknown>;
    callerNodeId?:    string;
    callerInstance?:  string;
    correlationId?:   string;
    operatorOverride?: string;
    sessionId?:       string;
    riskPosture?:     string;
  }): UCIInvocation {
    return new UCIInvocation({
      uci_invocation_version: INVOCATION_VERSION,
      invocation_id:          randomUUID(),
      correlation_id:         params.correlationId ?? randomUUID(),
      timestamp:              new Date().toISOString(),
      caller: {
        node_id:     params.callerNodeId   ?? "orchestrator",
        instance_id: params.callerInstance ?? "",
        actor_type:  "orchestrator",
      },
      target: {
        node_id:       params.nodeId,
        capability_id: params.capabilityId,
        action_id:     params.actionId,
      },
      payload:             params.payload ?? {},
      context: {
        session_id:     params.sessionId   ?? "",
        operator_id:    "",
        risk_posture:   params.riskPosture ?? "normal",
        policy_profile: "",
        network_zone:   "",
        environment:    "",
        tags:           {},
      },
      operator_override:    params.operatorOverride ?? null,
      require_confirmation: false,
    });
  }
}
