init:
	pip install pipenv
	pipenv install

dev:
	pipenv run zappa update dev
