pre-commit-checks: doc test lint

doc:
	@cd util; ./update_docs.py

test:
	@cd tests; ./run.py

lint: style
	@pylint3 --rcfile=pylint3.cfg --reports=no *.py

style:
	@python3 -m pycodestyle *.py

.PHONY: doc test lint style
