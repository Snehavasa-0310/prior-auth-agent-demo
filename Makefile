.PHONY: setup data ingest run-api run-ui run test lint eval demo clean docker-up docker-down help

PYTHON ?= python3
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate && export PYTHONPATH=.

help:
	@echo "Prior Authorization Copilot Agent - Commands:"
	@echo "  make setup       Create virtualenv and install dependencies"
	@echo "  make data        Generate policies and synthetic clinical cases"
	@echo "  make ingest      Warm policy index and criteria cache"
	@echo "  make run-api     Launch FastAPI REST backend (port 8000)"
	@echo "  make run-ui      Launch Streamlit Reviewer Workspace (port 8501)"
	@echo "  make run         Run both API and UI locally"
	@echo "  make test        Execute pytest test suite"
	@echo "  make lint        Run ruff and mypy static analysis"
	@echo "  make eval        Execute full evaluation suite & ablations across 104 cases"
	@echo "  make docker-up   Start services via docker-compose"
	@echo "  make docker-down Stop docker-compose services"

setup:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -r requirements.txt

data:
	$(ACTIVATE) && python scripts/prepare_policies.py
	$(ACTIVATE) && python scripts/generate_synthetic_cases.py

ingest: data
	$(ACTIVATE) && python -c 'from src.policy.loader import load_and_index_policies; from pathlib import Path; load_and_index_policies(Path("data/policies")); print("Policy indexing complete.")'

run-api:
	$(ACTIVATE) && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

run-ui:
	$(ACTIVATE) && streamlit run src/ui/app.py --server.port 8501

run:
	@echo "Starting FastAPI and Streamlit in parallel..."
	$(ACTIVATE) && (uvicorn src.api.main:app --host 0.0.0.0 --port 8000 & streamlit run src/ui/app.py --server.port 8501)

test:
	$(ACTIVATE) && pytest tests/ -v

lint:
	$(ACTIVATE) && ruff check .
	$(ACTIVATE) && mypy src/ tests/ eval/

eval:
	$(ACTIVATE) && python -m eval.runner

demo:
	$(ACTIVATE) && python scripts/demo_cli.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache prior_auth.db
	find . -type d -name "__pycache__" -exec rm -rf {} +

