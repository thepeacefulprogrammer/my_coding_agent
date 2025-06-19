#!/usr/bin/env python3
"""Script to add pytest.mark.qt markers to all Qt-related test files.

This script identifies test files that import PyQt6 components and adds
the @pytest.mark.qt decorator to prevent them from running in parallel.
"""

import re
from pathlib import Path


def has_pyqt_imports(file_path: Path) -> bool:
    """Check if a file has PyQt6 imports."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            return "from PyQt6" in content or "import PyQt6" in content
    except Exception:
        return False


def has_pytest_import(content: str) -> bool:
    """Check if file already imports pytest."""
    return "import pytest" in content


def add_pytest_import(content: str) -> str:
    """Add pytest import after other imports."""
    lines = content.split("\n")

    # Find the last import line
    last_import_idx = -1
    for i, line in enumerate(lines):
        if (
            line.strip().startswith("import ")
            or line.strip().startswith("from ")
            or line.strip().startswith("    ")
        ):  # continuation line
            last_import_idx = i

    if last_import_idx >= 0:
        # Insert pytest import after the last import
        lines.insert(last_import_idx + 1, "import pytest")
    else:
        # No imports found, add at the beginning after docstring
        docstring_end = 0
        if lines and lines[0].strip().startswith('"""'):
            # Find end of docstring
            for i in range(1, len(lines)):
                if '"""' in lines[i]:
                    docstring_end = i + 1
                    break
        lines.insert(docstring_end, "import pytest")

    return "\n".join(lines)


def add_qt_markers(content: str) -> str:
    """Add @pytest.mark.qt markers to test classes."""
    lines = content.split("\n")
    result_lines = []

    for i, line in enumerate(lines):
        # Check if this line defines a test class
        if re.match(r"^class Test.*:", line.strip()):
            # Check if the previous line already has a pytest marker
            has_marker = i > 0 and result_lines and "@pytest.mark." in result_lines[-1]

            if not has_marker:
                # Add the qt marker before the class definition
                result_lines.append("@pytest.mark.qt")

        result_lines.append(line)

    return "\n".join(result_lines)


def process_test_file(file_path: Path) -> bool:
    """Process a single test file to add Qt markers."""
    if not has_pyqt_imports(file_path):
        return False

    print(f"Processing {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Add pytest import if needed
        if not has_pytest_import(content):
            content = add_pytest_import(content)

        # Add Qt markers to test classes
        content = add_qt_markers(content)

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all test files."""
    test_dir = Path("tests/unit")
    processed_count = 0

    for test_file in test_dir.glob("test_*.py"):
        if process_test_file(test_file):
            processed_count += 1

    print(f"Processed {processed_count} Qt test files")


if __name__ == "__main__":
    main()
