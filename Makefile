pre-commit-checks: copyright doc test lint

copyright:
	@hook_scripts/copyright_year.py

doc:
	@cd util; ./update_docs.py
	@cd util; ./update_versions.py

test:
	@cd tests; ./run.py

lint: style
	@python3 -m pylint --rcfile=pylint3.cfg --reports=no mh_* miss_hit_core miss_hit

style:
	@python3 -m pycodestyle mh_* miss_hit_core miss_hit

package:
	@git clean -xdf
	@cp setup_gpl.py setup.py
	@mkdir -p miss_hit_core/resources/assets
	@cp docs/style.css miss_hit_core/resources
	@cp docs/assets/* miss_hit_core/resources/assets
	@python3 setup.py sdist bdist_wheel
	@rm -r miss_hit_core/resources
	@cp setup_agpl.py setup.py
	@python3 setup.py sdist bdist_wheel
	@rm setup.py

upload_test: package
	python3 -m twine upload --repository testpypi dist/*

upload_main: package
	python3 -m twine upload --repository pypi dist/*

release:
	python3 -m util.release

github_release:
	git push
	python3 -m util.github_release

bump:
	python3 -m util.bump_version_post_release

m_ast_picture.pdf: miss_hit_core/m_ast.py util/mk_ast_hierarchy.py
	python3 -m util.mk_ast_hierarchy m | dot -Tpdf > m_ast_picture.pdf

s_ast_picture.pdf: miss_hit_core/s_ast.py util/mk_ast_hierarchy.py
	python3 -m util.mk_ast_hierarchy s | dot -Tpdf > s_ast_picture.pdf

m_types_picture.pdf: miss_hit_core/m_types.py util/mk_ast_hierarchy.py
	python3 -m util.mk_ast_hierarchy t | dot -Tpdf > m_types_picture.pdf

cfg_ast_picture.pdf: miss_hit_core/cfg_ast.py util/mk_ast_hierarchy.py
	python3 -m util.mk_ast_hierarchy cfg | dot -Tpdf > cfg_ast_picture.pdf

.PHONY: doc test lint style
.PHONY: release package upload_test upload_main
