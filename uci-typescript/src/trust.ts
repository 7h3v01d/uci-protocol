/**
 * UCI Trust Model
 * Canonical trust states and enforced transition rules.
 */

import { UCITrustError } from "./errors.js";

export enum TrustState {
  UNKNOWN     = "unknown",
  DISCOVERED  = "discovered",
  VERIFIED    = "verified",
  TRUSTED     = "trusted",
  RESTRICTED  = "restricted",
  SUSPENDED   = "suspended",
  REVOKED     = "revoked",
}

/** Legal forward transitions */
const ALLOWED_TRANSITIONS: Record<TrustState, Set<TrustState>> = {
  [TrustState.UNKNOWN]:    new Set([TrustState.DISCOVERED, TrustState.REVOKED]),
  [TrustState.DISCOVERED]: new Set([TrustState.VERIFIED, TrustState.SUSPENDED, TrustState.REVOKED]),
  [TrustState.VERIFIED]:   new Set([TrustState.TRUSTED, TrustState.RESTRICTED, TrustState.SUSPENDED, TrustState.REVOKED]),
  [TrustState.TRUSTED]:    new Set([TrustState.RESTRICTED, TrustState.SUSPENDED, TrustState.REVOKED]),
  [TrustState.RESTRICTED]: new Set([TrustState.TRUSTED, TrustState.SUSPENDED, TrustState.REVOKED]),
  [TrustState.SUSPENDED]:  new Set([TrustState.VERIFIED, TrustState.TRUSTED, TrustState.RESTRICTED, TrustState.REVOKED]),
  [TrustState.REVOKED]:    new Set(),
};

export const EXECUTABLE_STATES = new Set<TrustState>([
  TrustState.TRUSTED,
  TrustState.RESTRICTED,
]);

export interface TrustTransition {
  from:       string;
  to:         string;
  grantedBy:  string;
  reason:     string;
  timestamp:  string;
}

export class TrustRecord {
  public state:     TrustState;
  public grantedBy: string;
  public notes:     string;
  public readonly history: TrustTransition[] = [];

  constructor(
    public readonly nodeId: string,
    state: TrustState = TrustState.UNKNOWN,
  ) {
    this.state     = state;
    this.grantedBy = "";
    this.notes     = "";
  }

  transition(
    newState:  TrustState,
    grantedBy  = "policy_engine",
    reason     = "",
  ): this {
    const allowed = ALLOWED_TRANSITIONS[this.state];
    if (!allowed.has(newState)) {
      throw new UCITrustError(
        `Trust transition '${this.state}' → '${newState}' is not permitted for node '${this.nodeId}'.`,
        this.state,
        newState,
      );
    }
    this.history.push({
      from:      this.state,
      to:        newState,
      grantedBy,
      reason,
      timestamp: new Date().toISOString(),
    });
    this.state     = newState;
    this.grantedBy = grantedBy;
    if (reason) this.notes = reason;
    return this;
  }

  canExecute():      boolean { return EXECUTABLE_STATES.has(this.state); }
  isTerminal():      boolean { return this.state === TrustState.REVOKED; }
  canExposeManifest(): boolean {
    return [
      TrustState.DISCOVERED, TrustState.VERIFIED,
      TrustState.TRUSTED,    TrustState.RESTRICTED,
    ].includes(this.state);
  }

  assertExecutable(): void {
    if (!this.canExecute()) {
      throw new UCITrustError(
        `Node '${this.nodeId}' cannot execute in trust state '${this.state}'.`,
        this.state,
        "trusted",
      );
    }
  }

  summary() {
    return {
      nodeId:     this.nodeId,
      state:      this.state,
      canExecute: this.canExecute(),
      grantedBy:  this.grantedBy,
      transitions: this.history.length,
    };
  }
}
