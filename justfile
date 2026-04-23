default:
    @just --list

install:
    uv sync

format:
    uv run ruff format .

check-sizes:
    uv run python scripts/check_sizes.py

lint:
    uv run ruff check .
    just check-sizes

test:
    uv run pytest

review-usage:
    uv run youbot review-usage
