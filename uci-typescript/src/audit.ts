/**
 * UCI Audit Log
 * Chain-hashed, append-only event log with portable session export.
 */

import { createHash, randomUUID } from "crypto";

export const AUDIT_EVENT_VERSION = "0.1";
export const GENESIS_HASH = "0".repeat(64);

export const AuditEvent = {
  NODE_DISCOVERED:            "node_discovered",
  MANIFEST_RETRIEVED:         "manifest_retrieved",
  MANIFEST_VALIDATION_PASSED: "manifest_validation_passed",
  MANIFEST_VALIDATION_FAILED: "manifest_validation_failed",
  COMPATIBILITY_ACCEPTED:     "compatibility_accepted",
  COMPATIBILITY_REJECTED:     "compatibility_rejected",
  TRUST_ASSIGNED:             "trust_assigned",
  CAPABILITY_MOUNTED:         "capability_mounted",
  CAPABILITY_REVOKED:         "capability_revoked",
  NODE_READY:                 "node_ready",
  HANDSHAKE_FAILED:           "handshake_failed",
  POLICY_EVALUATED:           "policy_evaluated",
  PERMISSION_DENIED:          "permission_denied",
  TRUST_REJECTED:             "trust_rejected",
  CONFIRMATION_REQUESTED:     "confirmation_requested",
  CONFIRMATION_APPROVED:      "confirmation_approved",
  EXECUTION_ALLOWED:          "execution_allowed",
  EXECUTION_DENIED:           "execution_denied",
  EXECUTION_RESTRICTED:       "execution_restricted",
  INVOCATION_REQUESTED:       "invocation_requested",
  INVOCATION_COMPLETED:       "invocation_completed",
  INVOCATION_FAILED:          "invocation_failed",
} as const;

// ── AuditRecord ─────────────────────────────────────────────

export interface AuditRecordData {
  audit_event_version: string;
  event_id:            string;
  sequence:            number;
  event_type:          string;
  node_id:             string;
  timestamp:           string;
  actor:               string;
  outcome:             string;
  severity:            string;
  correlation_id:      string;
  source:              Record<string, unknown>;
  detail:              Record<string, unknown>;
  previous_hash:       string;
  chain_hash:          string;
}

/**
 * Canonical JSON serialisation — sorted keys, no whitespace.
 * Must match Python: json.dumps(obj, sort_keys=True, separators=(',', ':'))
 */
function canonicalJSON(obj: unknown): string {
  if (obj === null || typeof obj !== "object" || Array.isArray(obj)) {
    return JSON.stringify(obj);
  }
  const o = obj as Record<string, unknown>;
  const keys = Object.keys(o).sort();
  return "{" + keys.map(k => JSON.stringify(k) + ":" + canonicalJSON(o[k])).join(",") + "}";
}

function computeHash(record: AuditRecordData, previousHash: string): string {
  const payload = canonicalJSON({
    previous_hash: previousHash,
    sequence:      record.sequence,
    event_id:      record.event_id,
    event_type:    record.event_type,
    node_id:       record.node_id,
    timestamp:     record.timestamp,
    actor:         record.actor,
    outcome:       record.outcome,
    detail:        record.detail,
  });
  return createHash("sha256").update(payload).digest("hex");
}

export class AuditRecord {
  constructor(public data: AuditRecordData) {}

  seal(previousHash: string): void {
    this.data.previous_hash = previousHash;
    this.data.chain_hash    = computeHash(this.data, previousHash);
  }

  verify(previousHash: string): boolean {
    const expected = computeHash(this.data, previousHash);
    return this.data.chain_hash === expected;
  }

  toDict(): AuditRecordData { return structuredClone(this.data); }

  static fromDict(data: AuditRecordData): AuditRecord {
    return new AuditRecord(structuredClone(data));
  }
}

// ── UCIAuditSession ─────────────────────────────────────────

export interface IntegrityReport {
  valid:        boolean;
  totalRecords: number;
  breaks:       { sequence: number; eventId: string; reason: string }[];
  checkedAt:    string;
}

export class UCIAuditSession {
  public sessionHash: string = "";
  public closedAt:    string | null = null;

  constructor(
    public readonly sessionId:      string,
    public readonly orchestratorId: string,
    public readonly openedAt:       string,
    public readonly records:        AuditRecord[],
  ) {}

  sealSession(): void {
    const tailHash = this.records.length > 0
      ? this.records[this.records.length - 1].data.chain_hash
      : GENESIS_HASH;
    const payload = `${this.sessionId}:${tailHash}`;
    this.sessionHash = createHash("sha256").update(payload).digest("hex");
    this.closedAt    = new Date().toISOString();
  }

  verifySessionHash(): boolean {
    if (!this.records.length) return true;
    const tailHash = this.records[this.records.length - 1].data.chain_hash;
    const payload  = `${this.sessionId}:${tailHash}`;
    const expected = createHash("sha256").update(payload).digest("hex");
    return this.sessionHash === expected;
  }

  forNode(nodeId: string):       AuditRecord[] { return this.records.filter(r => r.data.node_id === nodeId); }
  byEvent(eventType: string):    AuditRecord[] { return this.records.filter(r => r.data.event_type === eventType); }
  denials():                     AuditRecord[] { return this.records.filter(r => r.data.outcome === "deny"); }

  toDict() {
    return {
      uci_audit_version: AUDIT_EVENT_VERSION,
      session_id:        this.sessionId,
      orchestrator_id:   this.orchestratorId,
      opened_at:         this.openedAt,
      closed_at:         this.closedAt,
      session_hash:      this.sessionHash,
      record_count:      this.records.length,
      records:           this.records.map(r => r.toDict()),
    };
  }

  toJSON(): string { return JSON.stringify(this.toDict(), null, 2); }

  static fromDict(data: ReturnType<UCIAuditSession["toDict"]>): UCIAuditSession {
    const records  = data.records.map(r => AuditRecord.fromDict(r as AuditRecordData));
    const session  = new UCIAuditSession(
      data.session_id, data.orchestrator_id, data.opened_at, records
    );
    session.sessionHash = data.session_hash;
    session.closedAt    = data.closed_at;
    return session;
  }

  static fromJSON(json: string): UCIAuditSession {
    return UCIAuditSession.fromDict(JSON.parse(json));
  }
}

// ── AuditLog ────────────────────────────────────────────────

export class AuditLog {
  private readonly _records: AuditRecord[] = [];
  private _counter    = 0;
  private _lastHash   = GENESIS_HASH;
  public readonly sessionId: string;

  constructor(public readonly orchestratorId = "") {
    this.sessionId = randomUUID();
  }

  append(params: {
    eventType:      string;
    nodeId:         string;
    actor?:         string;
    outcome?:       string;
    severity?:      string;
    correlationId?: string;
    source?:        Record<string, unknown>;
    detail?:        Record<string, unknown>;
  }): AuditRecord {
    this._counter++;
    const record = new AuditRecord({
      audit_event_version: AUDIT_EVENT_VERSION,
      event_id:            randomUUID(),
      sequence:            this._counter,
      event_type:          params.eventType,
      node_id:             params.nodeId,
      timestamp:           new Date().toISOString(),
      actor:               params.actor         ?? "uci_engine",
      outcome:             params.outcome        ?? "",
      severity:            params.severity       ?? "info",
      correlation_id:      params.correlationId  ?? "",
      source:              params.source         ?? { node_id: params.actor ?? "uci_engine" },
      detail:              params.detail         ?? {},
      previous_hash:       "",
      chain_hash:          "",
    });
    record.seal(this._lastHash);
    this._lastHash = record.data.chain_hash;
    this._records.push(record);
    return record;
  }

  all():            AuditRecord[] { return [...this._records]; }
  count():          number        { return this._records.length; }
  forNode(id: string): AuditRecord[] { return this._records.filter(r => r.data.node_id === id); }
  denials():        AuditRecord[] { return this._records.filter(r => r.data.outcome === "deny"); }

  verifyIntegrity(): IntegrityReport {
    const breaks: IntegrityReport["breaks"] = [];
    let prevHash = GENESIS_HASH;
    for (const record of this._records) {
      if (!record.verify(prevHash)) {
        breaks.push({
          sequence: record.data.sequence,
          eventId:  record.data.event_id,
          reason:   "chain_hash mismatch — record may have been tampered with",
        });
      }
      prevHash = record.data.chain_hash;
    }
    return {
      valid:        breaks.length === 0,
      totalRecords: this._records.length,
      breaks,
      checkedAt:    new Date().toISOString(),
    };
  }

  export(seal = true): UCIAuditSession {
    const session = new UCIAuditSession(
      this.sessionId,
      this.orchestratorId,
      this._records[0]?.data.timestamp ?? new Date().toISOString(),
      [...this._records],
    );
    if (seal) session.sealSession();
    return session;
  }
}
