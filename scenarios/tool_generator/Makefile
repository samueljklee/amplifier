.PHONY: help install check test clean

help:
	@echo "Available targets:"
	@echo "  make install  - Install dependencies"
	@echo "  make check    - Run linting and type checking"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Remove generated files"

install:
	uv sync

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run pyright .

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
