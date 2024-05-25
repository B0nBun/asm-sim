all: format lint typecheck test

format:
	poetry run ruff format ./src

lint:
	poetry run ruff check --fix ./src

typecheck:
	poetry run mypy

test:
	poetry run pytest ./src -v

test-update-golden:
	poetry run pytest ./src -v --update-goldens