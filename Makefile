install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=neurobridge

lint:
	ruff check . && black --check . && mypy neurobridge/

format:
	black . && ruff --fix .

serve:
	neurobridge serve --reload

build:
	python -m build

docs:
	mkdocs serve

benchmark:
	python benchmarks/benchmark_pipeline.py
