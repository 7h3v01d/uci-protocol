#!/usr/bin/env node
/**
 * UCI HTTP Transport Demo — TypeScript Client
 * =============================================
 * Connects to the Python UCI provider over HTTP and demonstrates
 * the full protocol conversation:
 *
 *   1. Discover  — fetch and validate the manifest
 *   2. Invoke    — search_index (allow)
 *   3. Invoke    — get_document (allow)
 *   4. Invoke    — health_check (allow)
 *   5. Audit     — fetch session, verify chain and session hash
 *
 * Run the Python provider first:
 *   cd examples/http_provider_python && python provider.py
 *
 * Then run this demo:
 *   npm run demo
 */

import { UCIHttpClient } from "./client.js";

const ResponseState = { COMPLETED: "completed", FAILED: "failed", DENIED: "denied" } as const;

const GREEN  = "\x1b[32m";
const RED    = "\x1b[31m";
const CYAN   = "\x1b[36m";
const BOLD   = "\x1b[1m";
const DIM    = "\x1b[2m";
const YELLOW = "\x1b[33m";
const RST    = "\x1b[0m";

const BASE_URL = process.env.UCI_PROVIDER_URL ?? "http://localhost:8000";

function ok(msg: string)   { console.log(`  ${GREEN}✓${RST} ${msg}`); }
function fail(msg: string) { console.log(`  ${RED}✗${RST} ${msg}`); }
function info(msg: string) { console.log(`  ${DIM}·${RST} ${msg}`); }
function section(msg: string) { console.log(`\n${BOLD}  ▸ ${msg}${RST}`); }

async function main(): Promise<number> {
  console.log(`
${BOLD}${CYAN}  ╔══════════════════════════════════════════════════╗${RST}
${BOLD}${CYAN}  ║   UCI HTTP Transport Demo                        ║${RST}
${BOLD}${CYAN}  ║   TypeScript Client ↔ Python Provider            ║${RST}
${BOLD}${CYAN}  ║   Author: Leon Priest                            ║${RST}
${BOLD}${CYAN}  ╚══════════════════════════════════════════════════╝${RST}

  Provider: ${BOLD}${BASE_URL}${RST}
`);

  const client = new UCIHttpClient({
    baseUrl:     BASE_URL,
    callerNodeId:"ts_demo_client",
  });

  const results: boolean[] = [];
  const check = (name: string, passed: boolean, detail = "") => {
    results.push(passed);
    passed ? ok(name) : fail(name + (detail ? `  — ${detail}` : ""));
  };

  // ── Phase 1: Discovery ───────────────────────────────────────────────────
  section("Phase 1 — Discovery (GET /uci/manifest)");
  try {
    const manifest = await client.fetchManifest();

    check("Manifest received",           !!manifest);
    check("Version is 0.1",             (manifest as any).uci_manifest_version === "0.1");
    check("node_id is non-empty",        !!(manifest as any).node?.node_id);
    check("display_name is non-empty",   !!(manifest as any).node?.display_name);
    check("Has capabilities",            (manifest as any).capabilities?.length > 0);
    check("Has transports",              (manifest as any).transports?.length > 0);
    check("health block present",        "health" in (manifest as any));
    check("transport type is http",      (manifest as any).transports?.[0]?.type === "http");

    info(`node_id:      ${(manifest as any).node?.node_id}`);
    info(`display_name: ${(manifest as any).node?.display_name}`);
    info(`capabilities: ${((manifest as any).capabilities?.map((c: any) => c.capability_id) ?? []).join(", ")}`);

  } catch (e) {
    fail(`Could not reach provider at ${BASE_URL}: ${e}`);
    console.log(`\n  ${YELLOW}Is the Python provider running?${RST}`);
    console.log(`  Run: cd examples/http_provider_python && python provider.py\n`);
    return 1;
  }

  // ── Phase 2: Invocation — search ─────────────────────────────────────────
  section("Phase 2 — Invoke search_index (POST /uci/invoke)");
  try {
    const r = await client.invoke({
      capabilityId: "document_search",
      actionId:     "search_index",
      payload:      { query: "governance", limit: 3 },
    });

    check("Response received",           !!r);
    check("success == true",             (r as any).success === true);
    check("state == completed",          (r as any).state   === ResponseState.COMPLETED);
    check("output has results",          Array.isArray(((r as any).output as any)?.results));
    check("error is null",               (r as any).error   === null);
    check("invocation_id present",       !!(r as any).invocation_id);
    check("correlation_id present",      !!(r as any).correlation_id);
    check("provider.node_id present",    !!(r as any).provider?.node_id);
    check("governance.outcome = allow",  (r as any).governance?.outcome.startsWith("allow"));

    const results_arr = ((r as any).output as any)?.results ?? [];
    info(`query: 'governance' → ${results_arr.length} result(s)`);
    for (const res of results_arr.slice(0, 2)) {
      info(`  • ${res.title} (score: ${res.score.toFixed(2)})`);
    }

  } catch (e) {
    fail(`Invocation failed: ${e}`);
  }

  // ── Phase 3: Invocation — get document ───────────────────────────────────
  section("Phase 3 — Invoke get_document (POST /uci/invoke)");
  try {
    const r = await client.invoke({
      capabilityId: "document_search",
      actionId:     "get_document",
      payload:      { document_id: "doc_001" },
      correlationId: "demo-corr-001",
    });

    check("Response received",            !!r);
    check("success == true",              (r as any).success === true);
    check("document present in output",   !!((r as any).output as any)?.document);
    check("correlation_id preserved",     (r as any).correlation_id === "demo-corr-001");

    const doc = ((r as any).output as any)?.document;
    info(`retrieved: "${doc?.title}"`);

  } catch (e) {
    fail(`get_document failed: ${e}`);
  }

  // ── Phase 4: Invocation — health check ───────────────────────────────────
  section("Phase 4 — Invoke health_check (POST /uci/invoke)");
  try {
    const r = await client.invoke({
      capabilityId: "system_health",
      actionId:     "health_check",
    });

    check("Response received",            !!r);
    check("success == true",              (r as any).success === true);
    check("status == healthy",            ((r as any).output as any)?.status === "healthy");
    check("transport == http",            ((r as any).output as any)?.transport === "http");

    info(`status: ${((r as any).output as any)?.status} · docs: ${((r as any).output as any)?.document_count}`);

  } catch (e) {
    fail(`health_check failed: ${e}`);
  }

  // ── Phase 5: Audit session ────────────────────────────────────────────────
  section("Phase 5 — Audit session (GET /uci/audit/session)");
  try {
    const { session, chainValid, sessionValid } = await client.fetchAuditSession();

    check("Session received",            !!session);
    check("Has records",                 ((session as any).records?.length ?? 0) > 0);
    check("Session hash present",        !!(session as any).session_hash);
    check("Session hash verifies",       sessionValid);
    check("Chain integrity intact",      chainValid);

    const types = new Set(((session as any).records ?? []).map((r: any) => r.event_type));
    check("node_discovered in audit",    types.has("node_discovered"));
    check("node_ready in audit",         types.has("node_ready"));
    check("invocation records present",
          types.has("invocation_requested") || types.has("invocation_completed"));

    info(`records: ${((session as any).records?.length ?? 0)} · events: ${types.size} distinct types`);

  } catch (e) {
    fail(`Audit session failed: ${e}`);
  }

  // ── Summary ───────────────────────────────────────────────────────────────
  const passed = results.filter(Boolean).length;
  const total  = results.length;
  const allOk  = passed === total;

  console.log(`\n${BOLD}${CYAN}  ${"─".repeat(50)}${RST}`);
  if (allOk) {
    console.log(`${BOLD}${GREEN}  ✓ HTTP transport demo: ${passed}/${total} checks passed${RST}`);
    console.log(`${DIM}  TypeScript client ↔ Python provider over HTTP: PASS${RST}`);
  } else {
    console.log(`${BOLD}${RED}  ✗ ${passed}/${total} checks passed${RST}`);
  }
  console.log(`${BOLD}${CYAN}  ${"─".repeat(50)}${RST}\n`);

  return allOk ? 0 : 1;
}

main().then(process.exit).catch(e => { console.error(e); process.exit(1); });
