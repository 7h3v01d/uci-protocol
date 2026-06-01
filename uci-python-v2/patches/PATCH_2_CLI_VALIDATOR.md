# UCI Patch 2 — CLI Manifest Validator

## Purpose

Add a standalone command-line validator (`uci_validate.py`) that checks
UCI manifest files against the v0.1 specification and reports structured
errors, warnings, and metadata.

## New Files

- `uci_validate.py` — CLI validator (run from project root)
- `example_manifests/valid_document_service.json` — clean passing manifest
- `example_manifests/warnings_minimal_agent.json` — valid but warns on missing fields
- `example_manifests/invalid_bad_actor.json` — multiple spec violations
- `test_rig/scenarios/test_validator.py` — 35 validator tests

## Usage

```
python uci_validate.py manifest.json
python uci_validate.py example_manifests/
python uci_validate.py manifest.json --strict
python uci_validate.py manifest.json --json
python uci_validate.py manifests/ --strict --quiet
```

## Flags

| Flag         | Effect                                              |
|--------------|-----------------------------------------------------|
| `--strict`   | Promotes all warnings to errors                     |
| `--json`     | Machine-readable JSON output (CI/pipeline friendly) |
| `--quiet`    | One line per manifest — pass/fail only              |
| `--no-colour`| Disable ANSI colour                                 |

## Exit Codes

| Code | Meaning                          |
|------|----------------------------------|
| 0    | All manifests valid              |
| 1    | One or more manifests invalid    |
| 2    | Usage error / file not found     |

## Validation Pipeline

1. File exists and is readable
2. JSON parses without error
3. Top-level required blocks present (`uci_manifest_version`, `node`, `capabilities`, `transports`, `governance`)
4. Recommended blocks checked for warnings (`compliance`, `audit`, `extensions`)
5. `UCIManifest.from_dict()` deserialisation
6. Full `manifest.validate()` spec check
7. Deep semantic warnings (missing descriptions, schemas, high-risk without confirmation, permissive policy)
8. Strict mode: all warnings → errors

## Test Result

```
91 passed (56 existing + 35 new)
0 failed
```
