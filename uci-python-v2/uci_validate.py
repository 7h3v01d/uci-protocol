#!/usr/bin/env python3
"""
UCI Manifest Validator  —  uci_validate.py
==========================================
Validates one or more UCI manifest files (JSON) against the v0.1 spec.

Usage
-----
  python uci_validate.py manifest.json
  python uci_validate.py manifests/          # validates all .json in directory
  python uci_validate.py manifest.json --strict
  python uci_validate.py manifest.json --json
  python uci_validate.py manifest.json --strict --json

Exit codes
----------
  0  All manifests valid
  1  One or more manifests invalid or not parseable
  2  Usage error (bad arguments, file not found)

Flags
-----
  --strict    Promote warnings to errors
  --json      Emit machine-readable JSON report to stdout (suppresses colour output)
  --quiet     Only print the summary line (useful in CI)
  --no-colour Disable ANSI colour even on supporting terminals
"""

from __future__ import annotations

import sys
import os
import json
import argparse
import glob
from dataclasses import dataclass, field
from typing import Any

# ── Windows ANSI colour support ───────────────────────────────────────────────
if sys.platform == "win32":
    import ctypes
    _k32 = ctypes.windll.kernel32
    _h = _k32.GetStdHandle(-11)
    _m = ctypes.c_ulong()
    if _k32.GetConsoleMode(_h, ctypes.byref(_m)):
        _k32.SetConsoleMode(_h, _m.value | 0x0004)

# ── Path setup (works when run from any cwd) ──────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from uci.core.manifest import UCIManifest
from uci.core.errors import UCIManifestError, UCIValidationError, UCICompatibilityError
from uci.core.schema_validator import validate_manifest_schema, SchemaIssue


# ─────────────────────────────────────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    severity: str          # "error" | "warning"
    code: str              # machine-readable code e.g. "MISSING_FIELD"
    message: str
    location: str = ""     # e.g. "capabilities[0].actions[1].risk.level"

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "code":     self.code,
            "message":  self.message,
            "location": self.location,
        }


@dataclass
class ManifestReport:
    path: str
    valid: bool
    node_id: str = ""
    display_name: str = ""
    manifest_version: str = ""
    issues: list[ValidationIssue] = field(default_factory=list)
    capabilities_found: list[str] = field(default_factory=list)
    transports_found: list[str] = field(default_factory=list)
    parse_error: str = ""

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def to_dict(self) -> dict:
        return {
            "path":             self.path,
            "valid":            self.valid,
            "node_id":          self.node_id,
            "display_name":     self.display_name,
            "manifest_version": self.manifest_version,
            "capabilities":     self.capabilities_found,
            "transports":       self.transports_found,
            "parse_error":      self.parse_error,
            "issues":           [i.to_dict() for i in self.issues],
            "summary": {
                "errors":   len(self.errors),
                "warnings": len(self.warnings),
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# Validator
# ─────────────────────────────────────────────────────────────────────────────

class UCIValidator:
    """
    Runs a complete validation pipeline on a manifest dict.
    Produces a ManifestReport with structured issues rather than raising.
    """

    def __init__(self, strict: bool = False):
        self.strict = strict

    def validate_file(self, path: str) -> ManifestReport:
        report = ManifestReport(path=path, valid=False)

        # ── Stage 1: File exists and is readable ──────────────────────────
        if not os.path.isfile(path):
            report.parse_error = f"File not found: {path}"
            report.issues.append(ValidationIssue(
                severity="error", code="FILE_NOT_FOUND",
                message=f"File not found: {path}",
            ))
            return report

        # ── Stage 2: JSON parse ───────────────────────────────────────────
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as exc:
            report.parse_error = str(exc)
            report.issues.append(ValidationIssue(
                severity="error", code="JSON_PARSE_ERROR",
                message=f"JSON parse error: {exc}",
            ))
            return report
        except Exception as exc:
            report.parse_error = str(exc)
            report.issues.append(ValidationIssue(
                severity="error", code="FILE_READ_ERROR",
                message=f"Could not read file: {exc}",
            ))
            return report

        return self.validate_dict(raw, path=path)

    def validate_dict(self, data: dict[str, Any], path: str = "<inline>") -> ManifestReport:
        report = ManifestReport(path=path, valid=False)

        if not isinstance(data, dict):
            report.issues.append(ValidationIssue(
                severity="error", code="NOT_A_DICT",
                message="Manifest must be a JSON object (dict), not a list or scalar.",
            ))
            return report

        # ── Stage 3: Top-level structure checks ───────────────────────────
        self._check_top_level(data, report)

        # ── Stage 3a: JSON Schema validation ──────────────────────────────
        schema_result = validate_manifest_schema(data)
        if not schema_result.valid:
            existing_paths = {i.location for i in report.issues}
            for issue in schema_result.issues:
                if issue.path not in existing_paths:
                    report.issues.append(ValidationIssue(
                        severity = "error",
                        code     = "SCHEMA_VIOLATION",
                        message  = issue.message,
                        location = issue.path,
                    ))

        # ── Stage 4: from_dict() deserialisation ──────────────────────────
        try:
            manifest = UCIManifest.from_dict(data)
        except UCIManifestError as exc:
            report.issues.append(ValidationIssue(
                severity="error", code="MANIFEST_STRUCTURE_ERROR",
                message=str(exc),
            ))
            return report
        except Exception as exc:
            report.issues.append(ValidationIssue(
                severity="error", code="DESERIALISATION_ERROR",
                message=f"Unexpected deserialisation error: {exc}",
            ))
            return report

        # Populate report metadata from parsed manifest
        report.node_id          = manifest.node.node_id
        report.display_name     = manifest.node.display_name
        report.manifest_version = manifest.uci_manifest_version
        report.capabilities_found = manifest.capability_ids()
        report.transports_found   = [t.transport_id for t in manifest.transports]

        # ── Stage 5: Full spec validation ─────────────────────────────────
        try:
            manifest.validate()
        except UCIManifestError as exc:
            report.issues.append(ValidationIssue(
                severity="error", code="MANIFEST_VALIDATION_ERROR",
                message=str(exc),
                location=self._infer_location(str(exc)),
            ))
            return report
        except UCIValidationError as exc:
            report.issues.append(ValidationIssue(
                severity="error", code="SPEC_VALIDATION_ERROR",
                message=str(exc),
                location=self._infer_location(str(exc)),
            ))
            return report
        except Exception as exc:
            report.issues.append(ValidationIssue(
                severity="error", code="VALIDATION_RUNTIME_ERROR",
                message=f"Unexpected validation error: {exc}",
            ))
            return report

        # ── Stage 6: Deep warnings ─────────────────────────────────────────
        self._deep_warnings(manifest, report)

        # ── Stage 7: Strict mode — warnings → errors ──────────────────────
        if self.strict:
            for issue in report.issues:
                if issue.severity == "warning":
                    issue.severity = "error"

        # Valid if no errors remain
        report.valid = len(report.errors) == 0
        return report

    # ── Top-level structural pre-checks ──────────────────────────────────────

    def _check_top_level(self, data: dict, report: ManifestReport) -> None:
        required_blocks = ["uci_manifest_version", "node", "capabilities", "transports", "governance"]
        for block in required_blocks:
            if block not in data:
                report.issues.append(ValidationIssue(
                    severity="error", code="MISSING_BLOCK",
                    message=f"Required top-level block '{block}' is missing.",
                    location=block,
                ))

        recommended_blocks = ["compliance", "audit", "extensions"]
        for block in recommended_blocks:
            if block not in data:
                report.issues.append(ValidationIssue(
                    severity="warning", code="MISSING_RECOMMENDED_BLOCK",
                    message=f"Recommended top-level block '{block}' is absent. "
                            f"Include it even if empty to ensure forward compatibility.",
                    location=block,
                ))

        # Version check
        version = data.get("uci_manifest_version", "")
        if version and version not in {"0.1"}:
            report.issues.append(ValidationIssue(
                severity="error", code="UNSUPPORTED_VERSION",
                message=f"Manifest version '{version}' is not supported. Supported: ['0.1']",
                location="uci_manifest_version",
            ))

    # ── Deep semantic warnings ────────────────────────────────────────────────

    def _deep_warnings(self, manifest: UCIManifest, report: ManifestReport) -> None:
        # Node warnings
        if not manifest.node.vendor:
            report.issues.append(ValidationIssue(
                severity="warning", code="MISSING_VENDOR",
                message="node.vendor is empty. Recommended for identification.",
                location="node.vendor",
            ))
        if not manifest.node.description:
            report.issues.append(ValidationIssue(
                severity="warning", code="MISSING_NODE_DESCRIPTION",
                message="node.description is empty. Recommended for discovery.",
                location="node.description",
            ))

        # Capability / action warnings
        for ci, cap in enumerate(manifest.capabilities):
            loc_cap = f"capabilities[{ci}]"
            if not cap.description:
                report.issues.append(ValidationIssue(
                    severity="warning", code="MISSING_CAPABILITY_DESCRIPTION",
                    message=f"Capability '{cap.capability_id}' has no description.",
                    location=f"{loc_cap}.description",
                ))
            for ai, action in enumerate(cap.actions):
                loc_act = f"{loc_cap}.actions[{ai}]"
                if not action.description:
                    report.issues.append(ValidationIssue(
                        severity="warning", code="MISSING_ACTION_DESCRIPTION",
                        message=f"Action '{cap.capability_id}/{action.action_id}' has no description.",
                        location=f"{loc_act}.description",
                    ))
                if not action.input_schema:
                    report.issues.append(ValidationIssue(
                        severity="warning", code="MISSING_INPUT_SCHEMA",
                        message=f"Action '{cap.capability_id}/{action.action_id}' has no input_schema.",
                        location=f"{loc_act}.input_schema",
                    ))
                if not action.output_schema:
                    report.issues.append(ValidationIssue(
                        severity="warning", code="MISSING_OUTPUT_SCHEMA",
                        message=f"Action '{cap.capability_id}/{action.action_id}' has no output_schema.",
                        location=f"{loc_act}.output_schema",
                    ))
                # High-risk without confirmation
                if action.risk.level in {"high", "critical"}:
                    if action.permissions.operator_confirmation == "none":
                        report.issues.append(ValidationIssue(
                            severity="warning", code="HIGH_RISK_NO_CONFIRMATION",
                            message=(
                                f"Action '{cap.capability_id}/{action.action_id}' has risk "
                                f"'{action.risk.level}' but operator_confirmation is 'none'."
                            ),
                            location=f"{loc_act}.permissions.operator_confirmation",
                        ))

        # Governance warnings
        if manifest.governance.default_action_policy == "allow":
            report.issues.append(ValidationIssue(
                severity="warning", code="PERMISSIVE_DEFAULT_POLICY",
                message="governance.default_action_policy is 'allow'. "
                        "Recommended value is 'deny' for fail-closed behaviour.",
                location="governance.default_action_policy",
            ))
        if not manifest.governance.audit_required:
            report.issues.append(ValidationIssue(
                severity="warning", code="AUDIT_DISABLED",
                message="governance.audit_required is false. "
                        "Disabling audit reduces traceability.",
                location="governance.audit_required",
            ))

    def _infer_location(self, message: str) -> str:
        """Best-effort location hint from error message text."""
        hints = {
            "node_id":       "node.node_id",
            "instance_id":   "node.instance_id",
            "node_type":     "node.node_type",
            "capability_id": "capabilities[?].capability_id",
            "action_id":     "capabilities[?].actions[?].action_id",
            "risk level":    "capabilities[?].actions[?].risk.level",
            "transport_id":  "transports[?].transport_id",
            "transport type":"transports[?].type",
            "endpoint":      "transports[?].endpoint",
            "execution mode":"capabilities[?].actions[?].execution.mode",
            "timeout_ms":    "capabilities[?].actions[?].execution.timeout_ms",
            "default_action_policy": "governance.default_action_policy",
        }
        msg_lower = message.lower()
        for keyword, location in hints.items():
            if keyword.lower() in msg_lower:
                return location
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Renderer
# ─────────────────────────────────────────────────────────────────────────────

class Reporter:
    def __init__(self, use_colour: bool = True, quiet: bool = False):
        self.use_colour = use_colour
        self.quiet = quiet

    def c(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.use_colour else text

    def green(self, t):   return self.c("32", t)
    def red(self, t):     return self.c("31", t)
    def yellow(self, t):  return self.c("33", t)
    def cyan(self, t):    return self.c("36", t)
    def bold(self, t):    return self.c("1",  t)
    def dim(self, t):     return self.c("2",  t)
    def magenta(self, t): return self.c("35", t)

    def print_header(self) -> None:
        if self.quiet:
            return
        print()
        print(self.bold(self.cyan("─" * 64)))
        print(self.bold(self.cyan("  UCI Manifest Validator  v0.1")))
        print(self.bold(self.cyan("  KeystoneAI / Leon Priest")))
        print(self.bold(self.cyan("─" * 64)))

    def print_report(self, report: ManifestReport) -> None:
        if self.quiet:
            status = self.green("PASS") if report.valid else self.red("FAIL")
            print(f"  [{status}]  {report.path}")
            return

        print()
        status_tag = self.bold(self.green(" VALID ")) if report.valid else self.bold(self.red(" INVALID "))
        print(f"  {status_tag}  {self.bold(report.path)}")

        if report.parse_error:
            print(f"    {self.red('✗')} Parse failed: {report.parse_error}")
            return

        # Identity
        if report.node_id:
            print(f"    {self.dim('node_id')}        {self.cyan(report.node_id)}")
        if report.display_name:
            print(f"    {self.dim('display_name')}   {report.display_name}")
        if report.manifest_version:
            print(f"    {self.dim('version')}        {report.manifest_version}")
        if report.capabilities_found:
            caps = ", ".join(report.capabilities_found)
            print(f"    {self.dim('capabilities')}   {self.cyan(caps)}")
        if report.transports_found:
            trans = ", ".join(report.transports_found)
            print(f"    {self.dim('transports')}     {trans}")

        # Issues
        if not report.issues:
            print(f"    {self.green('✓')} No issues found.")
            return

        print()
        for issue in report.issues:
            if issue.severity == "error":
                icon  = self.red("✗ ERROR  ")
                msg   = self.red(issue.message)
            else:
                icon  = self.yellow("⚠ WARNING")
                msg   = issue.message

            loc = f"  {self.dim(issue.location)}" if issue.location else ""
            code_tag = self.dim(f"[{issue.code}]")
            print(f"    {icon}  {msg}{loc}  {code_tag}")

    def print_summary(self, reports: list[ManifestReport], strict: bool) -> None:
        total   = len(reports)
        passed  = sum(1 for r in reports if r.valid)
        failed  = total - passed
        errors  = sum(len(r.errors)   for r in reports)
        warnings= sum(len(r.warnings) for r in reports)

        print()
        print(self.bold(self.cyan("─" * 64)))

        if failed == 0:
            status = self.bold(self.green(f"  ✓ All {total} manifest(s) valid"))
        else:
            status = self.bold(self.red(f"  ✗ {failed}/{total} manifest(s) invalid"))

        print(status)
        print(f"    errors: {self.red(str(errors))}   "
              f"warnings: {self.yellow(str(warnings))}   "
              f"{'strict mode ON' if strict else ''}")
        print(self.bold(self.cyan("─" * 64)))
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def collect_paths(targets: list[str]) -> list[str]:
    """Expand files and directories into a flat list of .json paths."""
    paths = []
    for target in targets:
        if os.path.isdir(target):
            found = sorted(glob.glob(os.path.join(target, "*.json")))
            if not found:
                print(f"  Warning: no .json files found in directory '{target}'", file=sys.stderr)
            paths.extend(found)
        elif os.path.isfile(target):
            paths.append(target)
        else:
            # Could be a glob pattern
            expanded = sorted(glob.glob(target))
            if expanded:
                paths.extend(expanded)
            else:
                print(f"  Error: path not found: '{target}'", file=sys.stderr)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="uci_validate",
        description="Validate UCI manifest files against the v0.1 specification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python uci_validate.py my_manifest.json
  python uci_validate.py manifests/
  python uci_validate.py my_manifest.json --strict
  python uci_validate.py my_manifest.json --json
  python uci_validate.py manifests/ --strict --quiet
        """,
    )
    parser.add_argument(
        "targets", nargs="+",
        help="Manifest file(s) or directory/directories containing .json manifests.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Promote all warnings to errors.",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output machine-readable JSON report to stdout.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Only print one line per manifest (pass/fail). Useful in CI.",
    )
    parser.add_argument(
        "--no-colour", action="store_true",
        help="Disable ANSI colour output.",
    )

    args = parser.parse_args()

    use_colour = not args.no_colour and not args.json_output
    reporter   = Reporter(use_colour=use_colour, quiet=args.quiet)
    validator  = UCIValidator(strict=args.strict)

    # Collect paths
    paths = collect_paths(args.targets)
    if not paths:
        print("  Error: no manifest files to validate.", file=sys.stderr)
        return 2

    if not args.json_output:
        reporter.print_header()

    reports: list[ManifestReport] = []
    for path in paths:
        report = validator.validate_file(path)
        reports.append(report)
        if not args.json_output:
            reporter.print_report(report)

    if args.json_output:
        output = {
            "uci_validator_version": "0.1",
            "strict":  args.strict,
            "total":   len(reports),
            "passed":  sum(1 for r in reports if r.valid),
            "failed":  sum(1 for r in reports if not r.valid),
            "manifests": [r.to_dict() for r in reports],
        }
        print(json.dumps(output, indent=2))
    else:
        reporter.print_summary(reports, strict=args.strict)

    # Exit 0 = all valid, 1 = any invalid
    return 0 if all(r.valid for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
