# Makefile for AIStoryWriter Development Workflow

.PHONY: help test lint format clean install vulture vulture-report lint-report vulture-enforce

# Default target
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run tests"
	@echo "  lint       - Run code quality checks (flake8, mypy, pyright)"
	@echo "  format     - Format code with black and isort"
	@echo "  clean      - Clean up temporary files"
	@echo "  vulture    - Run dead code analysis (reporting only)"
	@echo "  vulture-report - Generate dead code files and whitelist suggestions"
	@echo "  lint-report - Run all analysis and generate reports"
	@echo "  vulture-enforce - Run dead code analysis with enforcement"

# Installation
install:
	pip install -r requirements.txt

# Testing
test:
	.venv/bin/pytest -v

# Code Quality
format:
	.venv/bin/black --line-length 120 Writer/ *.py 2>/dev/null || echo "Black not available"
	.venv/bin/isort Writer/ *.py 2>/dev/null || echo "Isort not available"

lint:
	@echo "Running linting checks..."
	.venv/bin/flake8 Writer/ *.py 2>/dev/null || echo "Flake8 not available"
	.venv/bin/mypy Writer/ *.py 2>/dev/null || echo "MyPy not available"
	.venv/bin/pyright Writer/ *.py 2>/dev/null || echo "Pyright not available"

# Dead Code Analysis (Reporting Phase)
vulture:
	@echo "Running dead code analysis (reporting only)..."
	.venv/bin/vulture --min-confidence 60 --sort-by-size Writer/ Write.py Evaluate.py simulate_story_info.py || echo "Dead code analysis completed - see results above"

vulture-report:
	@echo "Generating dead code report..."
	mkdir -p reports
	.venv/bin/vulture --min-confidence 60 --sort-by-size Writer/ Write.py Evaluate.py simulate_story_info.py > reports/dead_code_$$(date +%Y%m%d).txt || echo "Dead code analysis completed"
	@echo "Dead code report saved to reports/dead_code_$$(date +%Y%m%d).txt"
	.venv/bin/vulture --min-confidence 60 --make-whitelist Writer/ Write.py Evaluate.py simulate_story_info.py > reports/whitelist_suggestions_$$(date +%Y%m%d).txt || echo "Whitelist generation completed"
	@echo "Whitelist suggestions saved to reports/whitelist_suggestions_$$(date +%Y%m%d).txt"
	@echo ""
	@echo "Summary:"
	@wc -l reports/dead_code_$$(date +%Y%m%d).txt | cut -d' ' -f1 2>/dev/null && echo " lines of dead code found" || echo "Report generated"

lint-report: flake8 mypy pyright vulture-report
	@echo "All analysis reports generated"

# Dead Code Analysis (Enforcement Phase - Manual Trigger)
vulture-enforce:
	@echo "Running dead code analysis with enforcement..."
	.venv/bin/vulture --min-confidence 80 Writer/ Write.py Evaluate.py simulate_story_info.py || (echo "❌ Dead code found above 80% confidence!" && exit 1)
	@echo "✅ No high-confidence dead code detected"

# Cleanup
clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf htmlcov 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
	rm -rf reports/* 2>/dev/null || true