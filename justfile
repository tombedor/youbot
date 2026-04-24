default: run

run:
    uv run youbot

install:
    uv sync

test:
    uv run pytest tests/ -v

lint:
    uv run ruff check src/
    uv run mypy src/

format:
    uv run ruff format src/
    uv run ruff check --fix src/
