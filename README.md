# OpenTrace (v1.0 MVP)
### Open-Source Digital Footprint Intelligence Platform

> *"Your digital footprint, transparently discovered."*

OpenTrace is a free, open-source digital footprint intelligence platform designed to help individuals and security researchers audit their publicly accessible online presence. OpenTrace provides evidence-backed identity correlation without subscription paywalls, rate-limit exploitation, or fabricated profile statistics.

---

## 🌟 Key Features

- **Multi-Signal Detection Engine:** An HTTP 200 response alone is never treated as proof of existence. OpenTrace detects soft-404s, generic landing pages, login redirections, rate limits, and CAPTCHA challenges.
- **Three Independent Confidence Dimensions:**
  1. *Profile Existence Confidence:* Statistical certainty that the account exists.
  2. *Data Reliability Confidence:* Quality of extracted public metadata.
  3. *Identity Confidence:* Strength of evidence linking separate accounts (e.g., matching personal domains, explicit cross-references).
- **Interactive Relationship Graph:** Visualize discovered accounts and evidenced connections using an interactive node canvas powered by `@xyflow/react`.
- **Zero-Bypass & SSRF Protection:** Strict destination address validation blocks internal subnets (RFC 1918), loopback interfaces, and cloud metadata APIs (`169.254.169.254`).
- **Data Erasure & Privacy:** Users can permanently delete investigations and all associated evidence records at any time.

---

## 📁 Repository Structure

```text
opentrace/
├── apps/
│   ├── web/                     # Next.js 14 App Router, TypeScript, Tailwind CSS
│   └── api/                     # FastAPI backend, SQLAlchemy 2.0 (async), Pydantic
├── services/
│   └── worker/                  # Celery background tasks & Redis worker configuration
├── packages/
│   ├── osint-engine/            # Curated adapter, SSRF guard, classifier, extractor, resolver
│   ├── schemas/                 # Shared Pydantic data schemas
│   └── site-registry/           # Curated definitions for supported public services
├── infra/
│   ├── postgres/                # PostgreSQL init schema
│   ├── redis/                   # Redis configuration
│   └── deployment/              # Docker Compose deployment configuration
├── docs/                        # Architecture, API reference, Privacy, and Contributing
├── scripts/                     # Live probe verification scripts
├── Makefile                     # Build & developer automation commands
└── requirements.txt             # Python 3.12 dependencies
```

---

## 🚀 Quick Start (Native macOS Development)

No Docker is required for local development. OpenTrace runs natively with Python 3.12 and Node.js.

### 1. Prerequisites
- **Python:** 3.12+
- **Node.js:** 20+

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/opentrace/opentrace.git
cd opentrace

# Copy environment template
cp .env.example .env

# Create Python virtual environment and install backend dependencies
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd apps/web && npm install && cd ../..
```

### 3. Run the Backend API
```bash
source .venv/bin/activate
uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI backend will start at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/api/docs`.

### 4. Run the Web Application
In a new terminal window:
```bash
cd apps/web
npm run dev
```
Open your browser at `http://localhost:3000`.

---

## 🧪 Testing

OpenTrace includes automated tests for SSRF validation, multi-signal classification, identity correlation, and REST endpoints:

```bash
# Run automated test suite
source .venv/bin/activate
PYTHONPATH=. pytest -v

# Run live probe test against real public accounts
source .venv/bin/activate
python scripts/test_live_probe.py
```

---

## 🗺️ Implementation Status

| Feature | Phase | Status |
|---|---|---|
| Username Search Engine | Phase 1 (MVP) | ✅ Completed |
| SSRF Isolation & Security | Phase 1 (MVP) | ✅ Completed |
| Multi-Signal Response Classifier | Phase 1 (MVP) | ✅ Completed |
| 3-Dimensional Confidence Model | Phase 1 (MVP) | ✅ Completed |
| Interactive Relationship Graph | Phase 1 (MVP) | ✅ Completed |
| Report Exports (JSON & HTML) | Phase 1 (MVP) | ✅ Completed |
| User Authentication & History | Phase 1 (MVP) | ✅ Completed |
| Recursive Deep Discovery (Depth > 2) | Phase 2 | 📋 Planned |
| Verified Email Self-Audit (OTP Workflow) | Phase 3 | 📋 Preview in UI |
| Verified Phone Self-Audit (OTP Workflow) | Phase 4 | 📋 Preview in UI |

---

## 📄 License
This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

