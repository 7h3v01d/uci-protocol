# UCI Release Checklist — v0.1.0-alpha

This checklist must pass before any `v0.1.x` tag is created.
Run it in order. Do not skip steps.

---

## Pre-release checks

### Schemas

- [ ] `uci_manifest_v0_1.json` — byte-for-byte identical across Python and TypeScript repos
- [ ] `uci_response_v0_1.json` — byte-for-byte identical across Python and TypeScript repos
- [ ] `uci_audit_session_v0_1.json` — byte-for-byte identical across Python and TypeScript repos
- [ ] All schemas have `$id` pointing to `uci-spec.org`

**Verify:**
```bash
diff uci-python/uci/schemas/uci_manifest_v0_1.json \
     uci-typescript/schemas/uci_manifest_v0_1.json
# should produce no output
```

---

### Python implementation

- [ ] `python -m pytest test_rig/ -q` → **331 passed, 0 failed**
- [ ] `python uci_validate.py example_manifests/valid_document_service.json --json` → `valid: true`
- [ ] `python run_rig.py` runs without errors
- [ ] All compliance rules pass (`test_compliance.py`)
- [ ] All spec alignment rules pass (`test_patch7_spec_alignment.py`)

---

### TypeScript implementation

- [ ] `npm test` → **63 passed, 0 failed**
- [ ] `npm run typecheck` → no errors
- [ ] `npm run build` → clean compile
- [ ] `demo/index.html` opens in browser and validates all three example manifests correctly

---

### Interoperability

- [ ] `python uci-interop/generate_report.py` → **verdict: pass**
- [ ] `interop_result.json` → `"python_to_typescript": true, "typescript_to_python": true`
- [ ] `INTEROP_REPORT.md` updated and committed
- [ ] Total checks: **87/87**

---

### Documentation

- [ ] `README.md` (Python) — interop headline present near top
- [ ] `SPEC.md` — all 23 spec documents listed
- [ ] `CHANGELOG.md` — current version entry complete
- [ ] `docs/` — all 23 specification documents present
- [ ] `test_vectors/` — valid, invalid, and warnings vectors present

---

### Repository hygiene

- [ ] No `.pyc` or `__pycache__` committed
- [ ] No `node_modules/` committed
- [ ] No `dist/` committed
- [ ] `.gitignore` covers all build artifacts
- [ ] `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md` present in all repos
- [ ] No accidental literal-named folders (e.g. `{core,transport,sdk}/`)

---

## Tagging

Once all checks pass:

```bash
# Python repo
cd uci-python
git tag v0.1.0-alpha
git push origin v0.1.0-alpha

# TypeScript repo
cd uci-typescript
git tag v0.1.0-alpha
git push origin v0.1.0-alpha

# Interop repo
cd uci-interop
git tag v0.1.0-alpha
git push origin v0.1.0-alpha
```

---

## GitHub release (Python repo only)

Create a release from the `v0.1.0-alpha` tag:

- **Title:** `v0.1.0-alpha — First public release`
- **Description:** copy from `CHANGELOG.md`
- **Mark as pre-release:** yes

---

## Known limitations (v0.1.0-alpha)

These are known gaps that do NOT block the alpha tag but MUST be resolved before v0.1.0 stable:

| Limitation | Planned |
|---|---|
| No HTTP transport — all interop is in-process or via JSON file exchange | v0.2 |
| No UCI Registry service — discovery is manual | v0.2 |
| No production integration (Niles/NYALS) | v0.2 |
| No Go or Rust implementation | v0.3 |
| `uci-spec.org` not yet live | before v0.1.0 stable |
| Chain hash algorithm not yet formally specified in docs | next patch |

---

## What comes after v0.1.0-alpha

**Next milestone: HTTP transport proof**

- One Python UCI provider exposing capabilities over HTTP
- One TypeScript UCI client discovering and invoking it
- Manifest, Invocation, Response, and AuditSession exchanged over `localhost`
- Interop harness extended to cover cross-process transport

That becomes the proof:
```
Cross-language objects:    PASS  ← done
Cross-process transport:   next
```

---

*UCI Release Checklist · v0.1.0-alpha · © Leon Priest*
