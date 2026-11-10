.PHONY: setup dev dev-api dev-web test test-live build clean

PYTHON = .venv/bin/python
PIP = .venv/bin/pip
UVICORN = .venv/bin/uvicorn
PYTEST = .venv/bin/pytest

setup:
	python3 -m venv .venv
	$(PIP) install -r requirements.txt
	cd apps/web && npm install
	cp -n .env.example .env || true

dev:
	@echo "Starting OpenTrace API and Web frontend..."
	@echo "API: http://localhost:8000"
	@echo "Web: http://localhost:3000"
	@make -j 2 dev-api dev-web

dev-api:
	PYTHONPATH=. $(UVICORN) apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload

dev-web:
	cd apps/web && npm run dev

test:
	PYTHONPATH=. $(PYTEST) -v

test-live:
	PYTHONPATH=. $(PYTHON) scripts/test_live_probe.py

build:
	cd apps/web && npm run build

clean:
	rm -rf .pytest_cache opentrace.db apps/web/.next
	find . -type d -name __pycache__ -exec rm -rf {} +

