# Security Policy

## Supported Versions
Only the latest release of OpenTrace receives active security updates.

## Reporting a Vulnerability
If you discover a security vulnerability or bypass in OpenTrace, please do not open a public issue.
Instead, submit a security advisory on GitHub or email security@opentrace.org.

## Anti-SSRF Guarantees
All network calls dispatched by OpenTrace background workers pass through `validate_target_url` in `packages/osint_engine/core/ssrf.py`. Any attempt to probe internal resources (e.g. 127.0.0.1, 169.254.169.254) will result in immediate termination of the request.

