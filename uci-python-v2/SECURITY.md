# Security Policy

## Supported versions

| Version       | Status            |
|---------------|-------------------|
| v0.1.0-alpha  | Active development |

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Contact: Leon Priest

Provide:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

Expect acknowledgement within 72 hours.

## Scope

Security issues in:
- Governance bypass (any path that allows action execution without policy evaluation)
- Trust escalation (any path that elevates trust state without proper validation)
- Audit tampering (any path that allows chain hash bypass)
- Schema injection (any path that allows malformed manifests to pass validation)

are considered critical and will be prioritised immediately.
