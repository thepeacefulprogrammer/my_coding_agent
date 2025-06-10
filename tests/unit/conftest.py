"""Pytest configuration and shared fixtures for My Coding Agent tests.

This module provides comprehensive testing infrastructure including:
- GUI testing fixtures with QApplication management
- Performance benchmarking setup
- Test data generation and cleanup
- Mock configurations for CI/CD environments
- Integration test helpers
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from PyQt6.QtWidgets import QApplication

# Additional fixtures for unit tests


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Create a QApplication instance for GUI testing.

    This fixture ensures proper QApplication lifecycle management
    during test execution, preventing conflicts between tests.

    Yields:
        QApplication instance for use in GUI tests.
    """
    # Set up headless environment
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Check if QApplication already exists
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

    yield app

    # Cleanup is handled automatically by QApplication


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files.

    This fixture provides a clean temporary directory for each test
    that requires file system operations. The directory is automatically
    cleaned up after the test completes.

    Yields:
        Path to a temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_code_files(temp_dir: Path) -> dict[str, Path]:
    """Create sample code files for testing.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        Dictionary mapping file types to their paths.
    """
    files = {}

    # Python file
    python_file = temp_dir / "sample.py"
    python_file.write_text('''#!/usr/bin/env python3
"""Sample Python file for testing."""

def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.

    Args:
        n: The position in the Fibonacci sequence.

    Returns:
        The nth Fibonacci number.
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


class Calculator:
    """A simple calculator class."""

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b


if __name__ == "__main__":
    print(f"fib(10) = {fibonacci(10)}")
''')
    files["python"] = python_file

    # JavaScript file
    js_file = temp_dir / "sample.js"
    js_file.write_text("""/**
 * Sample JavaScript file for testing.
 */

function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

class MathUtils {
    static square(x) {
        return x * x;
    }

    static cube(x) {
        return x * x * x;
    }
}

console.log(`factorial(5) = ${factorial(5)}`);
""")
    files["javascript"] = js_file

    # JSON configuration file
    json_file = temp_dir / "config.json"
    json_file.write_text("""{
    "theme": "dark",
    "font_size": 12,
    "syntax_highlighting": true,
    "line_numbers": true,
    "plugins": [
        "autocomplete",
        "linting",
        "git_integration"
    ]
}""")
    files["json"] = json_file

    return files


@pytest.fixture
def mock_ai_agent() -> Mock:
    """Create a mock AI agent for testing.

    Returns:
        Mock object configured to simulate AI agent behavior.
    """
    agent = Mock()
    agent.analyze_code.return_value = {
        "complexity": "medium",
        "suggestions": ["Add type hints", "Improve docstrings"],
        "security_issues": [],
        "performance_notes": ["Consider caching results"],
    }
    agent.is_available = True
    agent.api_key = "mock-api-key"
    return agent


@pytest.fixture
def performance_config() -> dict[str, Any]:
    """Configuration for performance benchmarks.

    Returns:
        Dictionary with benchmark configuration parameters.
    """
    return {
        "min_rounds": 3,
        "max_time": 5.0,  # seconds
        "warmup_rounds": 1,
        "timer": "time.perf_counter",
    }


@pytest.fixture(autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """Set up test environment variables and cleanup.

    This fixture automatically runs for every test to ensure
    a clean testing environment.
    """
    # Store original environment
    original_env = os.environ.copy()

    # Clear any existing QSettings to avoid test interference
    try:
        from PyQt6.QtCore import QSettings

        # Clear settings for the main application
        settings = QSettings("MyCodeViewerApp", "SimpleCodeViewer")
        settings.clear()
        settings.sync()
    except ImportError:
        # PyQt6 not available, skip settings cleanup
        pass

    # Set test-specific environment variables
    os.environ["MY_CODING_AGENT_ENV"] = "testing"
    os.environ["MY_CODING_AGENT_DEBUG"] = "false"
    os.environ["MY_CODING_AGENT_LOG_LEVEL"] = "WARNING"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def large_file_content() -> str:
    """Generate large file content for performance testing.

    Returns:
        String containing a large amount of code for stress testing.
    """
    lines = []
    for i in range(1000):
        lines.append(f"def function_{i}(param_{i}: int) -> int:")
        lines.append(f'    """Function number {i}."""')
        lines.append(f"    return param_{i} * {i}")
        lines.append("")

    return "\n".join(lines)


# Benchmark fixtures for performance testing
@pytest.fixture
def benchmark_small_file(sample_code_files: dict[str, Path]) -> Path:
    """Small file for benchmarking."""
    return sample_code_files["python"]


@pytest.fixture
def benchmark_large_file(temp_dir: Path, large_file_content: str) -> Path:
    """Large file for benchmarking."""
    large_file = temp_dir / "large_file.py"
    large_file.write_text(large_file_content)
    return large_file


# Integration test fixtures
@pytest.fixture
def integration_test_config() -> dict[str, Any]:
    """Configuration for integration tests.

    Returns:
        Dictionary with integration test parameters.
    """
    return {
        "timeout": 30.0,  # seconds
        "retry_attempts": 3,
        "mock_external_services": True,
    }
