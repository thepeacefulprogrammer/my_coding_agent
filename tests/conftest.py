"""Main pytest configuration for My Coding Agent tests.

This is the top-level conftest file that configures pytest plugins
and provides shared configuration for all tests (unit and integration).
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QApplication

# Import GUI fixtures directly to avoid module import issues in CI
# GUI fixtures are defined in tests/unit/fixtures/gui_fixtures.py
# but we import them here to make them available across all tests
# Import the fixtures to make them available
from tests.unit.fixtures.gui_fixtures import qapp_instance, qwidget  # noqa: F401


# Global environment variable mocking for AI agent tests
@pytest.fixture(autouse=True)
def mock_ai_agent_env_vars():
    """Mock AI agent environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "ENDPOINT": "https://test.openai.azure.com/",
            "API_KEY": "test_key",
            "MODEL": "test_deployment",
            "API_VERSION": "2024-02-15-preview",
        },
        clear=False,  # Don't clear existing environment variables
    ):
        yield


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
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    yield app  # type: ignore[misc]

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


@pytest.fixture(autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """Set up test environment variables and cleanup.

    This fixture automatically runs for every test to ensure
    a clean testing environment.
    """
    # Store original environment
    original_env = os.environ.copy()

    # Set test-specific environment variables
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["TESTING"] = "1"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle Qt tests specially.

    This hook ensures that Qt tests are marked appropriately and can be
    handled differently during parallel execution.
    """
    for item in items:
        # Check if the test is marked as a Qt test
        if item.get_closest_marker("qt") is not None:
            # Add a custom marker to indicate this test should run sequentially
            item.add_marker(pytest.mark.no_parallel)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "no_parallel: mark test to run sequentially, not in parallel"
    )
