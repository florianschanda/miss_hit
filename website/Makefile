build: style.css assets metric_examples

assets:
	mkdir -p assets
	cp ../docs/assets/*.svg assets/

style.css:
	cp ../docs/style.css .

metric_examples:
	make -C examples/metrics

MH_ROOT:=$(MH_ORG_USER)@$(MH_ORG_HOST):~/miss_hit_org

upload:
	scp *.html $(MH_ROOT)
	scp style.css $(MH_ROOT)
	scp -r assets $(MH_ROOT)
	scp metric_example.* $(MH_ROOT)
