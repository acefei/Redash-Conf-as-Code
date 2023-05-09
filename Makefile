.PHONY: help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([^:]+):[^#]+##([^#]+)', line)
	if match:
		target, help = match.groups()
		print("%-10s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

ifdef FUNC_APP
	EXTRA_ENV = -e FUNC_APP=$(FUNC_APP)
endif


help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

backup: ## backup configuration of dashboards and queries as code
	python3 data_visualization/migration.py $(UI_URL) $(API_KEY) backup

recovery: ## recovery dashboards and queries from configuration file
	@python3 data_visualization/migration.py $(UI_URL) $(API_KEY) recovery

clean: ## clean all of dashboards and queries from UI
	@python3 data_visualization/migration.py $(UI_URL) $(API_KEY) clean

init:  ## install pre-commit
	@command -v pre-commit >/dev/null 2>&1 || (pip install pre-commit --no-cache-dir && pre-commit install)

pre-commit: init ## run pre-commit manually
	@pre-commit autoupdate && pre-commit run --all-files
