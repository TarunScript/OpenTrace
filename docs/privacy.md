# OpenTrace Privacy and Ethical OSINT Policy

## 1. Ethical Boundaries
OpenTrace strictly adheres to ethical research guidelines:
- **Public Surface Only:** Probes are limited to publicly accessible endpoints that require no credentials.
- **No CAPTCHA/Anti-Bot Bypassing:** When a service presents a challenge or rate limit, OpenTrace marks the check as `INCONCLUSIVE` rather than attempting evasion.
- **No Password Reset Exploitation:** OpenTrace never accesses account-recovery or registration forms to determine whether a private account exists.

## 2. Server-Side Request Forgery (SSRF) Protection
To protect internal networks, OpenTrace implements strict destination verification:
- Checks target IP against RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
- Rejects loopback addresses (`127.0.0.0/8`, `::1`).
- Rejects cloud metadata addresses (`169.254.169.254`, `metadata.google.internal`).
- Restricts protocols to HTTP/HTTPS only.

## 3. Data Protection & India DPDP Act Alignment
- **Right to Erasure:** Users can permanently delete investigations at any time via the UI or `DELETE /api/v1/investigations/{id}`.
- **Purpose Limitation:** Search inputs are processed strictly to fulfill the immediate query.
- **Storage Minimization:** No third-party passwords or authentication tokens are ever persisted.

