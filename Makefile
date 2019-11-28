pre-commit-checks: test lint

test:
	@cd tests; ./run.py

lint: style
	@pylint3 --rcfile=pylint3.cfg --reports=no *.py

style:
	@python3 -m pycodestyle *.py
