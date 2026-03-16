setup: # setup the environment with poetry
	pip install pipx
	pipx install poetry>=2
	poetry install
	poetry run pre-commit install
	poetry env activate

format: # format docstrings and markdown to 80 chars per line
	poetry run docformatter --in-place --recursive vigil/
	poetry run mdformat --wrap 80 .

check: # run quality checks
	poetry check --lock
	poetry run pre-commit run -a
	poetry run mypy --check vigil/ tests/

test: # test the code with pytest
	poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html tests/
