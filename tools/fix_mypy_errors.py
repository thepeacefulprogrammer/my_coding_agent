#!/usr/bin/env python3
"""Script to fix specific Mypy type annotation errors."""

import re
import subprocess
import sys
from pathlib import Path


def fix_error_handler_issues():
    """Fix issues in error_handler.py."""
    file_path = Path("src/my_coding_agent/core/mcp/error_handler.py")
    content = file_path.read_text()

    # Fix the unreachable statement issue by restructuring the can_execute method
    content = re.sub(
        r"(def can_execute\(self\) -> bool:.*?elif self\.state == CircuitBreakerState\.HALF_OPEN:\s*return self\.half_open_calls < self\.half_open_max_calls)\s*return False",
        r"\1",
        content,
        flags=re.DOTALL,
    )

    # Fix the fallback_results type annotation issue
    content = re.sub(
        r"fallback_results = \{",
        r"fallback_results: dict[str, dict[str, Any] | list[Any] | None] = {",
        content,
    )

    # Add explicit type casts to fix Any return issues
    content = re.sub(
        r"return random\.random\(\)", r"return float(random.random())", content
    )

    # Fix await result type issues
    content = re.sub(
        r"return await operation\(\*\*kwargs\)",
        r"result = await operation(**kwargs)\n        return result",
        content,
    )

    file_path.write_text(content)
    print(f"Fixed {file_path}")


def fix_oauth2_auth_issues():
    """Fix issues in oauth2_auth.py."""
    file_path = Path("src/my_coding_agent/core/mcp/oauth2_auth.py")
    content = file_path.read_text()

    # Fix missing return type annotations
    content = re.sub(
        r"(def __aenter__\(self\))(\s*:)", r'\1 -> "OAuth2Authenticator"\2', content
    )

    content = re.sub(
        r"(def __aexit__\(self, exc_type, exc_val, exc_tb\))(\s*:)",
        r"\1 -> None\2",
        content,
    )

    file_path.write_text(content)
    print(f"Fixed {file_path}")


def fix_mcp_tool_visualization_issues():
    """Fix issues in mcp_tool_visualization.py."""
    file_path = Path("src/my_coding_agent/gui/components/mcp_tool_visualization.py")
    content = file_path.read_text()

    # Fix object return type issues - add explicit type casting
    content = re.sub(
        r"return item\.data\(role\)",
        r"return item.data(role) if item else None",
        content,
    )

    file_path.write_text(content)
    print(f"Fixed {file_path}")


def main():
    """Main function to fix all Mypy errors."""
    print("Fixing Mypy type annotation errors...")

    try:
        fix_error_handler_issues()
        fix_oauth2_auth_issues()
        fix_mcp_tool_visualization_issues()
        print("All fixes applied successfully!")

        # Run mypy to check if issues are resolved
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "src/my_coding_agent/core/mcp/error_handler.py",
                "src/my_coding_agent/core/mcp/oauth2_auth.py",
                "src/my_coding_agent/gui/components/mcp_tool_visualization.py",
                "--show-error-codes",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ All Mypy errors fixed!")
        else:
            print("❌ Some errors remain:")
            print(result.stdout)
            print(result.stderr)

    except Exception as e:
        print(f"Error applying fixes: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
