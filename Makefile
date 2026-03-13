setup: # setup the environment with poetry
	pip install pipx
	pipx install poetry>=2
	poetry install
	poetry run pre-commit install
	poetry env activate
