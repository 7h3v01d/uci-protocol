#!/usr/bin/env python3
"""
UCI Test Rig — Demo Runner
Run with: python run_rig.py

Shows the full UCI lifecycle in a readable terminal demo:
  - Three providers connecting (compliant, restricted, bad actors)
  - Handshake outcomes with stage-by-stage detail
  - Governance decisions for allowed, deferred, and denied actions
  - Live audit trail
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# ── Windows ANSI colour support ──────────────────────────────────────────────
if sys.platform == "win32":
    import ctypes
    _k32 = ctypes.windll.kernel32
    _h = _k32.GetStdHandle(-11)
    _m = ctypes.c_ulong()
    if _k32.GetConsoleMode(_h, ctypes.byref(_m)):
        _k32.SetConsoleMode(_h, _m.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING

from uci.core.audit import AuditLog
from uci.core.registry import UCIRegistry
from uci.core.governance import PolicyEngine
from uci.core.trust import TrustState
from uci.core.errors import UCIGovernanceError
from uci.sdk.provider import UCIOrchestrator
from test_rig.mock_providers.provider_alpha import ProviderAlpha
from test_rig.mock_providers.provider_beta import ProviderBeta
from test_rig.mock_providers.provider_gamma import (
    ProviderGammaMissingNodeId,
    ProviderGammaUnsupportedVersion,
    ProviderGammaInvalidRisk,
    ProviderGammaNoCaps,
)

# ─────────────────────────────────────────────
# Colour helpers (no dependencies)
# ─────────────────────────────────────────────

USE_COLOUR = True  # ANSI enabled above for Windows; always on

def c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOUR else text

def green(t):  return c("32", t)
def red(t):    return c("31", t)
def yellow(t): return c("33", t)
def cyan(t):   return c("36", t)
def bold(t):   return c("1",  t)
def dim(t):    return c("2",  t)
def magenta(t):return c("35", t)

def header(title: str) -> None:
    width = 64
    print()
    print(bold(cyan("─" * width)))
    print(bold(cyan(f"  {title}")))
    print(bold(cyan("─" * width)))

def section(title: str) -> None:
    print()
    print(bold(f"  ▸ {title}"))

def ok(msg):    print(f"    {green('✓')} {msg}")
def fail(msg):  print(f"    {red('✗')} {msg}")
def warn(msg):  print(f"    {yellow('⚠')} {msg}")
def info(msg):  print(f"    {dim('·')} {msg}")

def result_line(result) -> None:
    if result.success:
        caps = ", ".join(result.mounted_capabilities) or "none"
        ok(f"Node {bold(result.node_id)} — trust={cyan(result.trust_state)}, "
           f"caps=[{cyan(caps)}]")
        for w in result.warnings:
            warn(w)
    else:
        fail(f"Node {bold(result.node_id)} — failed at "
             f"{yellow(result.stage_reached.value)}: {result.failure_reason}")

# ─────────────────────────────────────────────
# Main demo
# ─────────────────────────────────────────────

def main() -> None:
    print()
    print(bold(magenta("  ╔══════════════════════════════════════════════╗")))
    print(bold(magenta("  ║   UCI — Universal Capability Interface       ║")))
    print(bold(magenta("  ║   Reference Test Rig  v0.1                   ║")))
    print(bold(magenta("  ║   Author: Leon Priest / KeystoneAI           ║")))
    print(bold(magenta("  ╚══════════════════════════════════════════════╝")))

    # ── Build the engine stack ──────────────────
    audit      = AuditLog()
    registry   = UCIRegistry()
    policy     = PolicyEngine(audit=audit)
    orch       = UCIOrchestrator(policy=policy, registry=registry,
                                 audit=audit, name="mock_orchestrator")

    # ════════════════════════════════════════════
    header("PHASE 1 — Handshake Lifecycle")
    # ════════════════════════════════════════════

    section("Provider Alpha — Fully Compliant (expect: TRUSTED, all caps mounted)")
    result_alpha = orch.connect(ProviderAlpha())
    result_line(result_alpha)

    section("Provider Beta — Operator Authority Required (expect: RESTRICTED, high-risk cap withheld)")
    result_beta = orch.connect(ProviderBeta())
    result_line(result_beta)

    section("Provider Gamma — Bad Actor Variants (all should fail-closed)")
    for Provider, name in [
        (ProviderGammaMissingNodeId,    "missing node_id"),
        (ProviderGammaUnsupportedVersion, "unsupported manifest version"),
        (ProviderGammaInvalidRisk,      "invalid risk level"),
        (ProviderGammaNoCaps,           "empty capabilities (edge case)"),
    ]:
        p = Provider()
        manifest = p.manifest_dict()
        node_id  = manifest.get("node", {}).get("node_id") or f"gamma_{name.replace(' ','_')}"
        from uci.core.handshake import HandshakeEngine
        he = HandshakeEngine(policy=policy, registry=registry, audit=audit)
        r  = he.run(node_id, manifest)
        result_line(r)

    # ════════════════════════════════════════════
    header("PHASE 2 — Governance in Action")
    # ════════════════════════════════════════════

    section("Invoking low-risk actions on Alpha (expect: ALLOWED)")
    try:
        r = orch.invoke("provider_alpha", "document_search", "search_index",
                        {"query": "UCI standard", "limit": 3})
        ok(f"search_index → {r['count']} result(s) for query '{r['query']}'")
    except Exception as e:
        fail(str(e))

    try:
        r = orch.invoke("provider_alpha", "system_health", "health_check")
        ok(f"health_check → status={green(r['status'])}, uptime={r['uptime_seconds']}s")
    except Exception as e:
        fail(str(e))

    section("Invoking synthesize on Beta (restricted, low-risk — expect: ALLOWED)")
    try:
        r = orch.invoke("provider_beta", "voice_tts", "synthesize",
                        {"text": "UCI is live.", "voice_id": "niles"})
        ok(f"synthesize → {r['audio_url']} ({r['duration_ms']}ms)")
    except Exception as e:
        fail(str(e))

    section("Attempting nonexistent capability (expect: DENIED)")
    try:
        orch.invoke("provider_alpha", "does_not_exist", "some_action")
        fail("Should have been denied — this is a bug.")
    except UCIGovernanceError as e:
        ok(f"Correctly denied: {dim(str(e)[:80])}")

    section("Attempting high-risk delete_file without operator override (expect: DEFERRED → error)")
    # Manually elevate beta's trust and mount file_operations for demo purposes
    entry = registry.get("provider_beta")
    if entry:
        try:
            entry.trust.transition(TrustState.TRUSTED, granted_by="demo_operator",
                                   reason="Demo elevation")
        except Exception:
            pass
        registry.mount_capability("provider_beta", "file_operations")

    try:
        orch.invoke("provider_beta", "file_operations", "delete_file",
                    {"path": "/tmp/demo.txt"})
        fail("Should have been deferred — this is a bug.")
    except UCIGovernanceError as e:
        ok(f"Correctly deferred (requires operator): {dim(str(e)[:80])}")

    section("Same action WITH operator override (expect: ALLOWED)")
    try:
        # Need a policy with documents.write for this demo step
        from uci.core.governance import DEFAULT_ORCHESTRATOR_PERMISSIONS
        from uci.sdk.provider import UCIOrchestrator as _O
        elevated_policy = PolicyEngine(
            orchestrator_permissions=DEFAULT_ORCHESTRATOR_PERMISSIONS | frozenset(["documents.write"]),
            audit=audit,
        )
        elevated_orch = _O(policy=elevated_policy, registry=registry, audit=audit)
        elevated_orch._providers["provider_beta"] = ProviderBeta()
        r = elevated_orch.invoke("provider_beta", "file_operations", "delete_file",
                                 {"path": "/tmp/demo.txt"},
                                 operator_override="leon")
        ok(f"delete_file approved by operator → deleted={r['deleted']}")
    except Exception as e:
        fail(str(e))

    # ════════════════════════════════════════════
    header("PHASE 3 — Trust Lifecycle")
    # ════════════════════════════════════════════

    section("Revoking Alpha — subsequent invocations must fail")
    entry = registry.get("provider_alpha")
    if entry:
        entry.trust.transition(TrustState.REVOKED, granted_by="demo_operator",
                               reason="Demo revocation test")
        ok(f"provider_alpha trust → {red('REVOKED')}")
    try:
        orch.invoke("provider_alpha", "document_search", "search_index", {"query": "test"})
        fail("Revoked node was invoked — governance failure.")
    except UCIGovernanceError:
        ok("Invocation correctly denied after revocation.")

    # ════════════════════════════════════════════
    header("PHASE 4 — Audit Trail")
    # ════════════════════════════════════════════

    summary = audit.summary()
    print()
    info(f"Total events:  {bold(str(summary['total_events']))}")
    info(f"Nodes seen:    {', '.join(bold(n) for n in summary['nodes_seen'])}")
    info(f"Denials:       {bold(str(len(audit.denials())))}")
    print()
    print(dim("  Last 15 audit events:"))
    print(dim(audit.render(last_n=15)))

    # ════════════════════════════════════════════
    header("PHASE 5 — Registry State")
    # ════════════════════════════════════════════

    reg_summary = registry.summary()
    print()
    info(f"Registered nodes: {bold(str(reg_summary['total_nodes']))}")
    info(f"Ready nodes:      {bold(str(reg_summary['ready']))}")
    for node in reg_summary["nodes"]:
        status = green("READY") if node["is_ready"] else red("NOT READY")
        caps   = ", ".join(node["capabilities"]) or "none"
        print(f"    {bold(node['node_id']):<35} trust={cyan(node['trust']):<20} "
              f"caps=[{caps}]  [{status}]")

    print()
    print(bold(green("  UCI Test Rig complete.")))
    print()


if __name__ == "__main__":
    main()
