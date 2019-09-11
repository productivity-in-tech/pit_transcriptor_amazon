init:
	pip install pipenv
	pipenv install

dev:
	pipenv run zappa deploy dev
