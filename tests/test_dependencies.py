"""Test module to verify required dependencies are available.

This test ensures that PyQt6 and Pygments are properly installed
and can be imported for the code viewer application.
"""

from pathlib import Path

import pytest
import toml


def test_pyqt6_available() -> None:
    """Test that PyQt6 is available and can be imported.

    This test verifies that the PyQt6 GUI framework is properly
    installed and its core modules can be imported.
    """
    try:
        import PyQt6.QtCore  # noqa: F401
        import PyQt6.QtGui  # noqa: F401
        import PyQt6.QtWidgets  # noqa: F401

        # If we get here, PyQt6 is available
        assert True
    except ImportError as e:
        pytest.fail(f"PyQt6 not available: {e}")


def test_pygments_available() -> None:
    """Test that Pygments is available and can be imported.

    This test verifies that the Pygments syntax highlighting
    library is properly installed and functional.
    """
    try:
        import pygments  # noqa: F401
        from pygments.formatters import get_formatter_by_name
        from pygments.lexers import get_lexer_by_name  # noqa: F401

        # Test that we can get lexers for our target languages
        python_lexer = get_lexer_by_name("python")
        javascript_lexer = get_lexer_by_name("javascript")

        # Test that we can get a formatter
        html_formatter = get_formatter_by_name("html")

        assert python_lexer is not None
        assert javascript_lexer is not None
        assert html_formatter is not None

    except ImportError as e:
        pytest.fail(f"Pygments not available: {e}")
    except Exception as e:
        pytest.fail(f"Pygments functionality test failed: {e}")


def test_pygments_syntax_highlighting() -> None:
    """Test that Pygments can perform basic syntax highlighting.

    This test verifies that Pygments can actually highlight code,
    not just that it's importable.
    """
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import PythonLexer

        code = "def hello():\n    print('Hello, World!')"
        lexer = PythonLexer()
        formatter = HtmlFormatter()

        result = highlight(code, lexer, formatter)

        # Should contain HTML tags indicating syntax highlighting
        assert "<span" in result
        assert "hello" in result
        assert "print" in result

    except Exception as e:
        pytest.fail(f"Pygments syntax highlighting test failed: {e}")


def test_ai_dependencies_added():
    """Test that Pydantic AI and MCP dependencies are added to pyproject.toml."""
    # Read the pyproject.toml file
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path) as f:
        config = toml.load(f)

    # Check that the main dependencies include AI libraries
    dependencies = config["project"]["dependencies"]

    # Expected AI dependencies
    expected_ai_deps = [
        "pydantic-ai",
        "openai",  # Azure OpenAI client
        "mcp",  # Model Context Protocol
    ]

    # Check each dependency is present (allowing for version specifications)
    for expected_dep in expected_ai_deps:
        found = any(dep.startswith(expected_dep) for dep in dependencies)
        assert found, f"Missing dependency: {expected_dep} in {dependencies}"


def test_environment_configuration_exists():
    """Test that .env_example file exists for Azure AI configuration."""
    project_root = Path(__file__).parent.parent
    env_example_path = project_root / ".env_example"

    assert env_example_path.exists(), (
        ".env_example file should exist for Azure AI configuration"
    )

    # Check that it contains Azure AI configuration keys
    with open(env_example_path) as f:
        content = f.read()

    expected_keys = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
    ]

    for key in expected_keys:
        assert key in content, f"Missing environment variable: {key} in .env_example"
