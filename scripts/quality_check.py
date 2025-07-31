#!/usr/bin/env python3
"""
Quality check script for AIStoryWriter project.
Runs type checking, linting, and tests to ensure code quality.
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except FileNotFoundError:
        print(f"❌ {description} - TOOL NOT FOUND")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run quality checks on AIStoryWriter")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-lint", action="store_true", help="Skip linting")
    parser.add_argument("--skip-types", action="store_true", help="Skip type checking")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues automatically")
    args = parser.parse_args()
    
    print("🚀 Starting AIStoryWriter Quality Checks")
    
    results = []
    
    # Type checking with pyright
    if not args.skip_types:
        success = run_command(
            ["pyright", "Writer/", "tests/"],
            "Type Checking (pyright)"
        )
        results.append(("Type Checking", success))
    
    # Linting with flake8
    if not args.skip_lint:
        flake8_cmd = ["flake8", "Writer/", "tests/", "--ignore=E501,W504,W503,E203,W291"]
        if args.fix:
            print("Note: flake8 cannot auto-fix. Consider using autopep8 or black for auto-fixing.")
        
        success = run_command(flake8_cmd, "Linting (flake8)")
        results.append(("Linting", success))
    
    # Integration tests (signature validation)
    if not args.skip_tests:
        success = run_command(
            ["python3", "-m", "pytest", "tests/integration/", "-v"],
            "Integration Tests (signature validation)"
        )
        results.append(("Integration Tests", success))
        
        # Contract tests  
        success = run_command(
            ["python3", "-m", "pytest", "tests/integration/test_mock_contracts.py", "-v"],
            "Contract Tests (mock validation)"
        )
        results.append(("Contract Tests", success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 QUALITY CHECK SUMMARY")
    print(f"{'='*60}")
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All quality checks PASSED!")
        return 0
    else:
        print("💥 Some quality checks FAILED!")
        print("\nRecommendations:")
        print("1. Fix type errors: Review pyright output and add type hints")
        print("2. Fix lint errors: Follow PEP 8 style guidelines")
        print("3. Fix test failures: Ensure function signatures match real implementations")
        print("4. Run with --fix flag to attempt automatic fixes where possible")
        return 1

if __name__ == "__main__":
    sys.exit(main())