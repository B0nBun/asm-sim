all: format lint typecheck test

format:
	poetry run ruff format .

lint:
	poetry run ruff check --fix .

typecheck:
	poetry run mypy

test:
	poetry run pytest . -v

test-update-golden:
	poetry run pytest . -v --update-goldens