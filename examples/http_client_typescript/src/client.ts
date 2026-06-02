/**
 * UCI HTTP Client
 * ===============
 * Connects to a UCI provider over HTTP.
 */

import { createHash } from "crypto";

// ── Types (mirrored from uci-typescript) ─────────────────────────────────────

export interface UCIHttpClientOptions {
  baseUrl:        string;
  correlationId?: string;
  callerNodeId?:  string;
  timeoutMs?:     number;
}

// ── UCI HTTP Client ───────────────────────────────────────────────────────────

export class UCIHttpClient {
  private readonly baseUrl:      string;
  private readonly callerNodeId: string;
  private readonly timeoutMs:    number;
  private _manifest:             Record<string, unknown> | null = null;

  constructor(options: UCIHttpClientOptions) {
    this.baseUrl      = options.baseUrl.replace(/\/$/, "");
    this.callerNodeId = options.callerNodeId ?? "uci_http_client";
    this.timeoutMs    = options.timeoutMs    ?? 10000;
  }

  async fetchManifest(): Promise<Record<string, unknown>> {
    const data = await this._get("/uci/manifest") as Record<string, unknown>;
    this._manifest = data;
    return data;
  }

  get manifest(): Record<string, unknown> | null { return this._manifest; }

  async invoke(params: {
    capabilityId:      string;
    actionId:          string;
    payload?:          Record<string, unknown>;
    correlationId?:    string;
    operatorOverride?: string;
  }): Promise<Record<string, unknown>> {
    if (!this._manifest) await this.fetchManifest();
    const nodeId = (this._manifest!.node as Record<string, unknown>)?.node_id as string;

    const inv = {
      uci_invocation_version: "0.1",
      invocation_id:  crypto.randomUUID(),
      correlation_id: params.correlationId ?? crypto.randomUUID(),
      timestamp:      new Date().toISOString(),
      caller:  { node_id: this.callerNodeId, instance_id: "", actor_type: "orchestrator" },
      target:  { node_id: nodeId, capability_id: params.capabilityId, action_id: params.actionId },
      payload: params.payload ?? {},
      context: { session_id: "", operator_id: "", risk_posture: "normal", policy_profile: "", network_zone: "", environment: "", tags: {} },
      operator_override:    params.operatorOverride ?? null,
      require_confirmation: false,
    };

    return await this._post("/uci/invoke", inv) as Record<string, unknown>;
  }

  async fetchAuditSession(): Promise<{
    session:      Record<string, unknown>;
    chainValid:   boolean;
    sessionValid: boolean;
  }> {
    const data = await this._get("/uci/audit/session") as Record<string, unknown>;

    const GENESIS = "0".repeat(64);

    function canonicalJSON(obj: unknown): string {
      if (obj === null || typeof obj !== "object" || Array.isArray(obj)) return JSON.stringify(obj);
      const o = obj as Record<string, unknown>;
      const keys = Object.keys(o).sort();
      return "{" + keys.map(k => JSON.stringify(k) + ":" + canonicalJSON(o[k])).join(",") + "}";
    }

    function hashRecord(rec: Record<string, unknown>, prev: string): string {
      const payload = canonicalJSON({
        previous_hash: prev,
        sequence:      rec.sequence,
        event_id:      rec.event_id,
        event_type:    rec.event_type,
        node_id:       rec.node_id,
        timestamp:     rec.timestamp,
        actor:         rec.actor,
        outcome:       rec.outcome,
        detail:        rec.detail,
      });
      return createHash("sha256").update(payload).digest("hex");
    }

    const records = (data.records as Record<string, unknown>[]) ?? [];
    let prev = GENESIS, chainValid = true;
    for (const rec of records) {
      const expected = hashRecord(rec, prev);
      if (rec.chain_hash !== expected) { chainValid = false; break; }
      prev = rec.chain_hash as string;
    }

    const tail     = records[records.length - 1]?.chain_hash as string;
    const shPayload = `${data.session_id}:${tail}`;
    const expected  = createHash("sha256").update(shPayload).digest("hex");
    const sessionValid = data.session_hash === expected;

    return { session: data, chainValid, sessionValid };
  }

  async health(): Promise<Record<string, unknown>> {
    return this._get("/uci/health") as Promise<Record<string, unknown>>;
  }

  private async _get(path: string): Promise<unknown> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method:  "GET",
      headers: { "Accept": "application/json" },
      signal:  AbortSignal.timeout(this.timeoutMs),
    });
    if (!res.ok) throw new Error(`GET ${path} → ${res.status} ${res.statusText}`);
    return res.json();
  }

  private async _post(path: string, body: unknown): Promise<unknown> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method:  "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body:    JSON.stringify(body),
      signal:  AbortSignal.timeout(this.timeoutMs),
    });
    return res.json();
  }
}
