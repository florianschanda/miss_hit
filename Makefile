pre-commit-checks: doc test lint

doc:
	@cd util; ./update_docs.py
	@cd util; ./update_versions.py

test:
	@cd tests; ./run.py

lint: style
	@python3 -m pylint --rcfile=pylint3.cfg --reports=no *.py

style:
	@python3 -m pycodestyle *.py

ast_picture.pdf: m_ast.py util/mk_ast_hierarchy.py
	./util/mk_ast_hierarchy.py | dot -Tpdf > ast_picture.pdf

.PHONY: doc test lint style
