# Security Policy

## Supported Versions

This project currently supports the latest main branch for security fixes.

## Reporting a Vulnerability

Please report vulnerabilities privately and do not open a public issue for active security problems.

Include:
- Affected component(s)
- Reproduction steps
- Potential impact
- Suggested mitigation (if available)

Disclosure target:
- Initial acknowledgement: within 3 business days
- Triage update: within 7 business days
- Mitigation plan or fix timeline: within 14 business days

## Security Scope

In scope:
- Authentication and authorization
- Data leakage and privacy violations
- Injection, traversal, and deserialization issues
- Dependency vulnerabilities affecting shipped code

Out of scope:
- Social engineering and phishing
- Denial of service without a reproducible code-level issue
- Vulnerabilities in unsupported forks

## Current Hardening Baseline

- Bearer API key support (optional)
- Request-size and request-timeout middleware
- Security headers on server and website
- Input validation for API payloads and identifiers
- Privacy-minimized feedback persistence

## Dependency Audit Process

Use these checks before release:

```bash
python -m pip install pip-audit
pip-audit
npm audit --prefix website --production
```

Track findings with severity, package, fixed version, and mitigation status in release notes.

## Latest Audit Snapshot

Last run: 2026-03-23 (local development environment)

Python (`pip-audit`) findings:
- `nltk==3.9.3` flagged by `GHSA-rf74-v2fm-23pw`, `CVE-2026-33230`, `CVE-2026-33231`
- `pip-audit` did not report fixed versions at scan time

Current mitigations:
- Do not process untrusted NLTK corpora or model downloads at runtime.
- Restrict runtime egress in production where possible.
- Track upstream `nltk` advisories and patch immediately when fixed versions are available.
