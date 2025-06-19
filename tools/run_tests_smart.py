#!/usr/bin/env python3
"""Smart test runner that handles Qt tests separately from parallel execution.

This script runs Qt GUI tests sequentially (to avoid segmentation faults)
while running all other tests in parallel for maximum performance.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> tuple[int, str]:
    """Run a command and return exit code and output."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        # Print output regardless of success/failure
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        return result.returncode, result.stdout

    except Exception as e:
        print(f"❌ Error running command: {e}")
        return 1, str(e)


def main():
    """Main test runner function."""
    print("🧪 Smart Test Runner - Handling Qt tests separately")

    # First, run non-Qt tests in parallel for speed
    print("\n" + "=" * 60)
    print("PHASE 1: Running non-Qt tests in parallel")
    print("=" * 60)

    non_qt_cmd = [
        "python",
        "-m",
        "pytest",
        "tests/unit/",
        "-n",
        "auto",  # Use all available CPU cores
        "-v",
        "--tb=short",
        "-m",
        "not qt",  # Exclude Qt tests
        "--maxfail=5",  # Stop after 5 failures to save time
    ]

    exit_code_1, output_1 = run_command(non_qt_cmd, "Non-Qt tests (parallel)")

    # Then, run Qt tests sequentially to avoid segmentation faults
    print("\n" + "=" * 60)
    print("PHASE 2: Running Qt tests sequentially")
    print("=" * 60)

    qt_cmd = [
        "python",
        "-m",
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-m",
        "qt",  # Only Qt tests
        "--maxfail=5",  # Stop after 5 failures
    ]

    exit_code_2, output_2 = run_command(qt_cmd, "Qt tests (sequential)")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if exit_code_1 == 0:
        print("✅ Non-Qt tests: PASSED")
    else:
        print("❌ Non-Qt tests: FAILED")

    if exit_code_2 == 0:
        print("✅ Qt tests: PASSED")
    else:
        print("❌ Qt tests: FAILED")

    # Overall result
    overall_exit_code = max(exit_code_1, exit_code_2)

    if overall_exit_code == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n💥 TESTS FAILED (exit code: {overall_exit_code})")

    return overall_exit_code


if __name__ == "__main__":
    sys.exit(main())
