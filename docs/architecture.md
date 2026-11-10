# OpenTrace System Architecture

## 1. Overview
OpenTrace is designed as a modular monolith adhering to strict separation of concerns across presentation, business logic, background orchestration, and data extraction.

```
┌────────────────────────────────────────────────────────┐
│               OpenTrace Web (Next.js)                  │
│   Landing • Search Console • Graph View • Audit Logs   │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON
┌───────────────────────────▼────────────────────────────┐
│               OpenTrace API (FastAPI)                  │
│    Validation • Auth • Orchestration • Graph Builder   │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
┌─────────────▼──────────────┐   ┌─────────▼─────────────┐
│    Database (PostgreSQL)   │   │  Worker (Celery/Async)│
│ Profiles • Evidence • Rel. │   │  Concurrent Probes    │
└────────────────────────────┘   └─────────┬─────────────┘
                                           │
                                 ┌─────────▼─────────────┐
                                 │      OSINT Engine     │
                                 │ SSRF Guard • Adapter  │
                                 │ Detector • Extractor  │
                                 └───────────────────────┘
```

## 2. Core Components

### 2.1 Web Application (`apps/web`)
- **Framework:** Next.js (App Router), TypeScript, Tailwind CSS.
- **Visualizations:** `@xyflow/react` for interactive relationship network graphs.
- **Design:** Dark-first cybersecurity intelligence theme.

### 2.2 API Backend (`apps/api`)
- **Framework:** FastAPI with Python 3.12.
- **Database:** SQLAlchemy 2.0 (async), supporting SQLite (zero-config local dev) and PostgreSQL (production).
- **Authentication:** JWT Bearer tokens with Bcrypt password hashing.

### 2.3 OSINT Engine (`packages/osint-engine`)
- **Anti-SSRF Validator:** Pre-flight DNS resolution checking against RFC 1918 private subnets, loopbacks, link-local addresses, and cloud provider metadata IPs (`169.254.169.254`).
- **Response Classifier:** Multi-signal evaluation rejecting bare HTTP 200 checks. Evaluates soft-404 strings, generic landing pages, login redirections, CAPTCHAs, and rate limits.
- **Profile Extractor:** Extracts display names, public bios, declared personal websites, avatar URLs, and locations without fragile brittle hacks.
- **Identity Resolver:** Correlates discovered accounts based on public evidence (matching domains, explicit cross-links, exact handles).

## 3. Confidence Dimensions
OpenTrace computes three distinct, non-conflated confidence metrics:
1. **Profile Existence Confidence (0.0 - 1.0):** Certainty that the public profile exists on the target service.
2. **Profile Data Confidence (0.0 - 1.0):** Quality and richness of extracted public metadata.
3. **Identity Confidence (0.0 - 1.0):** Strength of evidence tying two distinct platform accounts to the same person.

