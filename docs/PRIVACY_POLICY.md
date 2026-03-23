# NeuroBridge Privacy Policy

Last updated: 2026-03-23

## What We Store

NeuroBridge minimizes stored user content by default:
- User profile preferences linked to user IDs.
- Interaction counts per user.
- Feedback metadata and one-way SHA-256 hashes of feedback text fields.
- Delta metrics derived from feedback (for profile tuning).

NeuroBridge does not persist raw feedback text in the default memory stores.

## Data Subject Rights

NeuroBridge provides code-level methods and API endpoints to support user rights:
- Export user data: profile, feedback metadata, and interaction counts.
- Delete user data: removes profile, feedback history, and interaction counters.

## Security Controls

The server includes the following baseline protections:
- Bearer token API key authentication (optional, environment-controlled).
- Per-IP and per-API-key rate limiting.
- Request size limit and request timeout protection.
- Security headers to reduce browser attack surface.

## Data Retention

Data retention is controlled by the deployed memory backend.
- SQLite: data persists until explicit deletion.
- Redis: persistence and TTL behavior depend on Redis configuration.
- None backend: no persistence.

## Contact

Security and privacy issues can be reported following the process documented in SECURITY.md.
