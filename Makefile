.PHONY: install
install:
	uv sync --locked --all-extras --dev


.PHONY: lint
lint:
	uv run ruff check src tests


.PHONY: format
format:
	uv run ruff check src tests --fix
	uv run ruff format src tests


.PHONY: format-check
format-check:
	uv run ruff format --check src tests


.PHONY: test
test:
	uv run pytest -m "not integration" -q


.PHONY: test-integration
test-integration:
	uv run pytest -m integration -q


.PHONY: test-all
test-all:
	uv run pytest -q


.PHONY: eval-routing
eval-routing:
	uv run python -m ecom_agent_os.commerce_pilot.evaluation.runner --routing-only


.PHONY: eval-analytics
eval-analytics:
	uv run python -m ecom_agent_os.commerce_pilot.evaluation.runner --analytics-only


.PHONY: docker-build
docker-build:
	docker build -t commercepilot:local .


.PHONY: up
up:
	docker compose up --build -d


.PHONY: down
down:
	docker compose down


.PHONY: logs
logs:
	docker compose logs -f api


.PHONY: clean
clean:
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +