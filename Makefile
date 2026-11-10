.PHONY: verify verify-full test report-rts clean help

help:
	@echo "Available commands:"
	@echo "  make verify        - Run portable tests across all three projects"
	@echo "  make verify-full   - Run full tests including derived data assertions"
	@echo "  make report-rts    - Rebuild Road to Safety public deliverables"
	@echo "  make clean         - Remove pycache and temporary files"

verify:
	@./scripts/verify.sh

verify-full:
	@./scripts/verify.sh --full

test: verify

report-rts:
	@echo "Rebuilding Road to Safety portfolio deliverables..."
	@MPLCONFIGDIR=/tmp/mpl projects/road_to_safety/experiments/tree_comparison_v1/.venv/bin/python projects/road_to_safety/experiments/tree_comparison_v1/portfolio.py
	@MPLCONFIGDIR=/tmp/mpl projects/road_to_safety/experiments/tree_comparison_v1/.venv/bin/python projects/road_to_safety/experiments/tree_comparison_v1/build_brief.py
	@MPLCONFIGDIR=/tmp/mpl projects/road_to_safety/experiments/tree_comparison_v1/.venv/bin/python projects/road_to_safety/experiments/tree_comparison_v1/build_story.py

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf /tmp/mpl 2>/dev/null || true
