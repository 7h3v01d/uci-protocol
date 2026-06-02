from __future__ import annotations

"""
uci_system_monitor.py
─────────────────────
A local system diagnostics UCI provider.

Capabilities
────────────
  system_monitor
    • get_cpu_info      (risk=none, perms=system.read)
    • get_memory_info   (risk=none, perms=system.read)
    • get_disk_info     (risk=none, perms=system.read)
    • get_process_list  (risk=low,  perms=system.read)

Run standalone:
    python uci_system_monitor.py
    python uci_system_monitor.py --port 8002

Dependencies:
    pip install psutil
"""

# ── psutil guard ──────────────────────────────────────────────────────────────
try:
    import psutil
except ImportError as _err:
    raise ImportError(
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        " uci_system_monitor requires the 'psutil' library.\n"
        " Install it with:\n"
        "\n"
        "     pip install psutil\n"
        "\n"
        " Then re-run this script.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ) from _err

import sys
import os
import logging
import argparse
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..", "..", "uci-python-v2")
sys.path.insert(0, _ROOT)

# ── UCI imports ───────────────────────────────────────────────────────────────
from uci.sdk.provider   import UCIProvider
from uci.transport.http import UCIHttpServer
from uci.core.manifest  import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta, UCIHealth,
)

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("uci_system_monitor")


# ── Provider ──────────────────────────────────────────────────────────────────

class SystemMonitorProvider(UCIProvider):
    """
    UCI provider that exposes live system diagnostics.
    All actions are read-only — risk level none or low.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_action("system_monitor", "get_cpu_info",     self._cpu)
        self.register_action("system_monitor", "get_memory_info",  self._memory)
        self.register_action("system_monitor", "get_disk_info",    self._disk)
        self.register_action("system_monitor", "get_process_list", self._processes)

    # ── Manifest ──────────────────────────────────────────────────────────────

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "uci_system_monitor",
                instance_id  = "system_monitor_001",
                display_name = "UCI System Monitor",
                node_type    = "service",
                version      = "1.0.0",
                vendor       = "Leon Priest",
                description  = (
                    "Local system diagnostics. Exposes CPU, memory, "
                    "disk, and process metrics over UCI-HTTP."
                ),
            ),
            capabilities = [
                UCICapability(
                    capability_id = "system_monitor",
                    version       = "1.0",
                    category      = "monitoring",
                    description   = (
                        "Real-time diagnostics for CPU, memory, disk, "
                        "and running processes on the local host."
                    ),
                    tags = ["monitoring", "diagnostics", "system"],
                    actions = [

                        UCIAction(
                            action_id   = "get_cpu_info",
                            description = "Current CPU utilisation % and logical core count.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=5000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {},
                            output_schema = {
                                "cpu_percent": {"type": "number"},
                                "core_count":  {"type": "integer"},
                            },
                            risk = UCIRisk(level="none", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["system.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),

                        UCIAction(
                            action_id   = "get_memory_info",
                            description = "Total, available, and used RAM in MB plus % used.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=3000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {},
                            output_schema = {
                                "total_mb":     {"type": "number"},
                                "available_mb": {"type": "number"},
                                "used_mb":      {"type": "number"},
                                "percent":      {"type": "number"},
                            },
                            risk = UCIRisk(level="none", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["system.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),

                        UCIAction(
                            action_id   = "get_disk_info",
                            description = "Root partition disk usage in GB and %.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=3000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {},
                            output_schema = {
                                "total_gb":   {"type": "number"},
                                "used_gb":    {"type": "number"},
                                "free_gb":    {"type": "number"},
                                "percent":    {"type": "number"},
                            },
                            risk = UCIRisk(level="none", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["system.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),

                        UCIAction(
                            action_id   = "get_process_list",
                            description = "Top N running processes by CPU usage.",
                            execution   = UCIExecution(
                                mode="sync", timeout_ms=8000,
                                idempotent=True, side_effects=False,
                            ),
                            input_schema  = {
                                "limit": {"type": "integer", "default": 10},
                            },
                            output_schema = {
                                "processes":      {"type": "array"},
                                "total_returned": {"type": "integer"},
                            },
                            risk = UCIRisk(level="low", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["system.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        ),
                    ],
                )
            ],
            transports = [
                UCITransport(
                    transport_id = "http",
                    type         = "http",
                    endpoint     = "http://localhost:8002",
                    options      = {"content_type": "application/json"},
                )
            ],
            governance = UCIGovernanceMeta(
                default_action_policy       = "deny",
                audit_required              = True,
                operator_authority_required = False,
            ),
            health = UCIHealth(
                health_endpoint   = "/uci/health",
                check_interval_ms = 30000,
                expose_uptime     = True,
            ),
            compliance = {"profile": "minimal"},
            audit      = {"audit_enabled": True},
            extensions = {},
        )

    # ── Action handlers ───────────────────────────────────────────────────────

    def _cpu(self, **_) -> dict:
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1.0),
                "core_count":  psutil.cpu_count(logical=True),
            }
        except Exception as exc:
            return {"error": True, "message": str(exc)}

    def _memory(self, **_) -> dict:
        _MB = 1_024 ** 2
        try:
            vm = psutil.virtual_memory()
            return {
                "total_mb":     round(vm.total     / _MB, 2),
                "available_mb": round(vm.available / _MB, 2),
                "used_mb":      round(vm.used      / _MB, 2),
                "percent":      vm.percent,
            }
        except Exception as exc:
            return {"error": True, "message": str(exc)}

    def _disk(self, **_) -> dict:
        _GB = 1_024 ** 3
        try:
            du = psutil.disk_usage("/")
            return {
                "total_gb": round(du.total / _GB, 3),
                "used_gb":  round(du.used  / _GB, 3),
                "free_gb":  round(du.free  / _GB, 3),
                "percent":  du.percent,
            }
        except Exception as exc:
            return {"error": True, "message": str(exc)}

    def _processes(self, limit: int = 10, **_) -> dict:
        limit = max(1, int(limit))
        try:
            snapshot = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent", "status"]
            ):
                try:
                    info = proc.info
                    snapshot.append({
                        "pid":            info["pid"],
                        "name":           info.get("name") or "<unknown>",
                        "cpu_percent":    round(info.get("cpu_percent") or 0.0, 2),
                        "memory_percent": round(info.get("memory_percent") or 0.0, 3),
                        "status":         info.get("status") or "unknown",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            top = sorted(snapshot, key=lambda p: p["cpu_percent"], reverse=True)[:limit]
            return {"processes": top, "total_returned": len(top)}
        except Exception as exc:
            return {"error": True, "message": str(exc)}


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UCI System Monitor")
    parser.add_argument("--port",      type=int, default=8002)
    parser.add_argument("--host",      type=str, default="0.0.0.0")
    parser.add_argument("--log-level", type=str, default="info")
    args = parser.parse_args()

    print(f"""
  ╔══════════════════════════════════════════════════╗
  ║   UCI System Monitor                             ║
  ║   HTTP Transport · v1.0.0                        ║
  ║   Author: Leon Priest                            ║
  ╚══════════════════════════════════════════════════╝

  Endpoints:
    GET  http://{args.host}:{args.port}/uci/manifest
    POST http://{args.host}:{args.port}/uci/invoke
    GET  http://{args.host}:{args.port}/uci/audit/session
    GET  http://{args.host}:{args.port}/uci/health

  All actions are read-only (risk=none or low).
  Press Ctrl+C to stop.
""")

    provider = SystemMonitorProvider()
    server   = UCIHttpServer(
        provider  = provider,
        port      = args.port,
        host      = args.host,
        log_level = args.log_level,
    )
    server.run()


if __name__ == "__main__":
    main()
