UV ?= uv
UV_CACHE_DIR ?= $(CURDIR)/.uv-cache
export UV_CACHE_DIR

.PHONY: bootstrap lock list-checks check check-full check-nightly

bootstrap:
	$(UV) sync --frozen --all-groups

lock:
	$(UV) lock

list-checks:
	$(UV) run --frozen python tools/validate_repo.py --list

check:
	$(UV) run --frozen python tools/validate_repo.py --profile fast

check-full:
	$(UV) run --frozen python tools/validate_repo.py --profile full

check-nightly:
	$(UV) run --frozen python tools/validate_repo.py --profile nightly
