#!/usr/bin/env python3
"""
Comprehensive linting check script to prevent CI failures.

This script checks the entire codebase for linting errors before pushing to GitHub.
Run this before committing to catch issues locally.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: "list[str]", description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔍 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run comprehensive linting checks."""
    print("🚀 Running comprehensive linting checks...")

    # Change to project root
    project_root = Path(__file__).parent.parent
    print(f"📁 Project root: {project_root}")

    checks = [
        # Check source code
        (["python", "-m", "ruff", "check", "src/"], "Ruff check on src/"),
        # Check tests
        (["python", "-m", "ruff", "check", "tests/"], "Ruff check on tests/"),
        # Check entire project
        (["python", "-m", "ruff", "check", "."], "Ruff check on entire project"),
        # Format check
        (["python", "-m", "ruff", "format", "--check", "."], "Ruff format check"),
        # Run pre-commit hooks on all files
        (["pre-commit", "run", "--all-files"], "Pre-commit hooks"),
    ]

    all_passed = True

    for cmd, description in checks:
        if not run_command(cmd, description):
            all_passed = False

    if all_passed:
        print("\n🎉 All linting checks passed! Safe to push to GitHub.")
        return 0
    else:
        print("\n💥 Some linting checks failed. Fix these issues before pushing.")
        print("\n🔧 To auto-fix many issues, run:")
        print("   python -m ruff check . --fix --unsafe-fixes")
        print("   python -m ruff format .")
        return 1


if __name__ == "__main__":
    sys.exit(main())
