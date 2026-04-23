default:
    @just --list

install:
    uv sync

format:
    uv run ruff format .

lint:
    uv run ruff check .

test:
    uv run pytest

review-usage:
    uv run youbot review-usage
