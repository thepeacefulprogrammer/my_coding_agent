#!/usr/bin/env python3
"""
Fix type annotation issues across the codebase.

This script systematically fixes common type annotation problems:
1. Adds proper imports for typing constructs
2. Updates dict[...] to "dict[...]" for compatibility
3. Updates list[...] to "list[...]" for compatibility
4. Fixes QApplication type issues
5. Adds __future__ imports where needed
"""

import re
from pathlib import Path


def has_future_annotations(content: str) -> bool:
    """Check if file already has __future__ annotations import."""
    return "from __future__ import annotations" in content


def has_typing_imports(content: str) -> bool:
    """Check if file already has typing imports."""
    return bool(
        re.search(r"from typing import.*\b(Dict|List|Any|Optional|Union)\b", content)
    )


def add_future_annotations(content: str) -> str:
    """Add __future__ annotations import if not present."""
    if has_future_annotations(content):
        return content

    lines = content.split("\n")

    # Find the best place to insert the import
    insert_idx = 0

    # Skip over module docstring and encoding declarations
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # Find end of docstring
            quote = '"""' if stripped.startswith('"""') else "'''"
            if line.count(quote) == 2:  # Single line docstring
                insert_idx = i + 1
            else:
                # Multi-line docstring
                for j in range(i + 1, len(lines)):
                    if quote in lines[j]:
                        insert_idx = j + 1
                        break
            break
        elif stripped.startswith("#") or stripped == "" or stripped.startswith("# -*-"):
            insert_idx = i + 1
        else:
            break

    # Insert the import
    lines.insert(insert_idx, "from __future__ import annotations")
    if insert_idx < len(lines) - 1 and lines[insert_idx + 1].strip():
        lines.insert(insert_idx + 1, "")

    return "\n".join(lines)


def fix_qapplication_types(content: str) -> str:
    """Fix QApplication type annotation issues."""
    # Fix generator return types for QApplication
    pattern = r"-> Generator\[QApplication,.*?\]"
    replacement = "-> Generator[QApplication, None, None]"
    content = re.sub(pattern, replacement, content)

    # Fix QApplication.instance() type issues - replace naive implementation with type-safe version
    if "QApplication.instance()" in content and "yield app" in content:
        # Replace the naive pattern with type-safe logic
        old_pattern = r"""    # Check if QApplication already exists
    app = QApplication\.instance\(\)
    if app is None:
        app = QApplication\(sys\.argv\)

    yield app(?:  # type: ignore\[misc\])?"""

        new_pattern = """    # Check if QApplication already exists
    existing_app = QApplication.instance()
    if existing_app is None:
        app = QApplication(sys.argv)
    else:
        # Ensure we have a QApplication, not just QCoreApplication
        if isinstance(existing_app, QApplication):
            app = existing_app
        else:
            # This should not happen in practice, but just in case
            app = QApplication(sys.argv)

    yield app"""

        content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

    return content


def fix_dict_list_annotations(content: str) -> str:
    """Fix dict[...] and list[...] type annotations to be quoted."""

    # Don't modify if we have __future__ annotations
    if has_future_annotations(content):
        return content

    # Fix dict[...] patterns that aren't already quoted
    dict_pattern = r"\bdict\[[^\]]+\]"
    matches = re.finditer(dict_pattern, content)
    for match in reversed(list(matches)):
        start, end = match.span()
        # Check if already quoted
        if start > 0 and content[start - 1] == '"':
            continue
        if end < len(content) and content[end] == '"':
            continue

        # Quote the type annotation
        type_hint = content[start:end]
        content = content[:start] + f'"{type_hint}"' + content[end:]

    # Fix list[...] patterns that aren't already quoted
    list_pattern = r"\blist\[[^\]]+\]"
    matches = re.finditer(list_pattern, content)
    for match in reversed(list(matches)):
        start, end = match.span()
        # Check if already quoted
        if start > 0 and content[start - 1] == '"':
            continue
        if end < len(content) and content[end] == '"':
            continue

        # Quote the type annotation
        type_hint = content[start:end]
        content = content[:start] + f'"{type_hint}"' + content[end:]

    return content


def fix_union_syntax(content: str) -> str:
    """Fix | union syntax to use Union for older Python versions."""
    if has_future_annotations(content):
        return content

    # Find | unions that aren't in strings
    pattern = r"\b(\w+(?:\[[^\]]+\])?)\s*\|\s*(\w+(?:\[[^\]]+\])?)"

    def replace_union(match):
        left = match.group(1)
        right = match.group(2)
        return f"Union[{left}, {right}]"

    content = re.sub(pattern, replace_union, content)

    return content


def fix_duplicate_imports(content: str) -> str:
    """Fix duplicate imports, especially from typing and collections.abc."""
    lines = content.split("\n")

    for i, line in enumerate(lines):
        # Check for typing imports with Generator that conflicts with collections.abc
        if line.strip().startswith("from typing import") and "Generator" in line:
            # Check if we already have Generator from collections.abc
            has_collections_generator = any(
                "from collections.abc import" in line_content
                and "Generator" in line_content
                for line_content in lines[:i]
            )
            if has_collections_generator:
                # Remove Generator from typing import
                parts = line.split("Generator")
                if len(parts) == 2:
                    before, after = parts
                    # Clean up comma handling
                    before = before.rstrip(", ")
                    after = after.lstrip(", ")
                    if before.endswith("import"):
                        # Generator was the first import
                        if after:
                            lines[i] = before + " " + after
                        else:
                            lines[i] = ""  # Remove empty import line
                    elif after:
                        # Generator was in the middle
                        lines[i] = before + after
                    else:
                        # Generator was the last import
                        lines[i] = before

    return "\n".join(line for line in lines if line.strip())


def needs_typing_imports(content: str) -> "set[str]":
    """Determine which typing imports are needed."""
    needed = set()

    if "Dict[" in content or '"dict[' in content:
        needed.add("Dict")
    if "List[" in content or '"list[' in content:
        needed.add("List")
    if "Any" in content:
        needed.add("Any")
    if "Optional[" in content:
        needed.add("Optional")
    if "Union[" in content:
        needed.add("Union")
    if "Generator[" in content:
        needed.add("Generator")
    if "Callable[" in content:
        needed.add("Callable")

    return needed


def add_typing_imports(content: str) -> str:
    """Add necessary typing imports."""
    needed = needs_typing_imports(content)
    if not needed:
        return content

    lines = content.split("\n")

    # Check for existing typing imports
    existing_typing_line = None
    for i, line in enumerate(lines):
        if line.strip().startswith("from typing import"):
            existing_typing_line = i
            break

    if existing_typing_line is not None:
        # Merge with existing import
        existing_import = lines[existing_typing_line]
        # Extract existing imports
        match = re.search(r"from typing import (.+)", existing_import)
        if match:
            existing_imports = {imp.strip() for imp in match.group(1).split(",")}
            all_imports = sorted(existing_imports | needed)
            lines[existing_typing_line] = f"from typing import {', '.join(all_imports)}"
    else:
        # Add new typing import
        # Find where to insert (after __future__ imports)
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("from __future__"):
                insert_idx = i + 1
            elif line.startswith("import ") or line.startswith("from "):
                insert_idx = max(insert_idx, i)
                break

        import_line = f"from typing import {', '.join(sorted(needed))}"
        lines.insert(insert_idx, import_line)

    return "\n".join(lines)


def fix_file(file_path: Path) -> bool:
    """Fix type annotations in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Apply fixes
        content = add_future_annotations(content)
        content = fix_qapplication_types(content)
        content = fix_dict_list_annotations(content)
        content = fix_union_syntax(content)
        content = fix_duplicate_imports(content)
        content = add_typing_imports(content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            print(f"Fixed: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to fix all Python files."""
    project_root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    for pattern in ["src/**/*.py", "tests/**/*.py"]:
        python_files.extend(project_root.glob(pattern))

    # Exclude certain files
    exclude_patterns = {"__pycache__", ".git", "venv", "build", "dist"}
    python_files = [
        f for f in python_files if not any(part in exclude_patterns for part in f.parts)
    ]

    print(f"Found {len(python_files)} Python files to check")

    fixed_count = 0
    for file_path in python_files:
        if fix_file(file_path):
            fixed_count += 1

    print(f"Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
