"""
UCI JSON Schema Validator  —  uci/core/schema_validator.py
==========================================================
Language-agnostic schema validation layer.

The three canonical schemas live in uci/schemas/:
  uci_manifest_v0_1.json
  uci_response_v0_1.json
  uci_audit_session_v0_1.json

This module loads them once and exposes a clean validation API
that returns structured SchemaIssue lists rather than raising.
The uci_validate.py CLI calls this as Stage 2a — before the
Python semantic checks — so schema errors are reported first
with precise JSON Path locations.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator, ValidationError


# ─────────────────────────────────────────────
# Schema registry
# ─────────────────────────────────────────────

_SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")

_SCHEMA_FILES = {
    "manifest":      "uci_manifest_v0_1.json",
    "response":      "uci_response_v0_1.json",
    "audit_session": "uci_audit_session_v0_1.json",
}

_schema_cache: dict[str, dict] = {}


def _load_schema(name: str) -> dict:
    if name not in _schema_cache:
        path = os.path.join(_SCHEMAS_DIR, _SCHEMA_FILES[name])
        with open(path, "r", encoding="utf-8") as f:
            _schema_cache[name] = json.load(f)
    return _schema_cache[name]


def get_schema(name: str) -> dict:
    """Return the raw schema dict for 'manifest', 'response', or 'audit_session'."""
    return _load_schema(name)


# ─────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────

@dataclass
class SchemaIssue:
    path:    str    # JSON path e.g. "capabilities[0].actions[1].execution.mode"
    message: str    # human-readable error
    value:   Any    # the offending value
    schema_path: str = ""  # path within the schema that triggered the error

    def to_dict(self) -> dict:
        return {
            "path":        self.path,
            "message":     self.message,
            "value":       repr(self.value) if not isinstance(self.value, (str, int, float, bool, type(None))) else self.value,
            "schema_path": self.schema_path,
        }


@dataclass
class SchemaValidationResult:
    valid:       bool
    schema_name: str
    issues:      list[SchemaIssue] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        return {
            "valid":       self.valid,
            "schema_name": self.schema_name,
            "issue_count": len(self.issues),
            "issues":      [i.to_dict() for i in self.issues],
        }


# ─────────────────────────────────────────────
# Validator
# ─────────────────────────────────────────────

def _json_path(error: ValidationError) -> str:
    """Convert a jsonschema ValidationError path to a readable string."""
    if not error.absolute_path:
        return "$"
    parts = []
    for segment in error.absolute_path:
        if isinstance(segment, int):
            parts.append(f"[{segment}]")
        else:
            if parts:
                parts.append(f".{segment}")
            else:
                parts.append(str(segment))
    return "".join(parts)


def _schema_path(error: ValidationError) -> str:
    """Convert a jsonschema schema path to a readable string."""
    return " > ".join(str(s) for s in error.absolute_schema_path)


def validate_against_schema(
    data: dict[str, Any],
    schema_name: str,
) -> SchemaValidationResult:
    """
    Validate data against the named schema.
    Returns SchemaValidationResult — never raises.
    Schema names: 'manifest', 'response', 'audit_session'.
    """
    try:
        schema = _load_schema(schema_name)
    except (FileNotFoundError, KeyError) as exc:
        return SchemaValidationResult(
            valid       = False,
            schema_name = schema_name,
            issues      = [SchemaIssue(
                path    = "$",
                message = f"Schema '{schema_name}' could not be loaded: {exc}",
                value   = None,
            )],
        )

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))

    if not errors:
        return SchemaValidationResult(valid=True, schema_name=schema_name)

    issues = [
        SchemaIssue(
            path        = _json_path(err),
            message     = err.message,
            value       = err.instance,
            schema_path = _schema_path(err),
        )
        for err in errors
    ]

    return SchemaValidationResult(valid=False, schema_name=schema_name, issues=issues)


def validate_manifest_schema(data: dict[str, Any]) -> SchemaValidationResult:
    """Validate a manifest dict against the UCI manifest v0.1 schema."""
    return validate_against_schema(data, "manifest")


def validate_response_schema(data: dict[str, Any]) -> SchemaValidationResult:
    """Validate a response envelope dict against the UCI response v0.1 schema."""
    return validate_against_schema(data, "response")


def validate_audit_session_schema(data: dict[str, Any]) -> SchemaValidationResult:
    """Validate an audit session dict against the UCI audit session v0.1 schema."""
    return validate_against_schema(data, "audit_session")
