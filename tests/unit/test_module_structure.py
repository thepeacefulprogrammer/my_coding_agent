"""Test module to verify the core module structure is properly set up.

This test ensures that the core and gui modules are properly structured
with __init__.py files and can be imported.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_core_module_exists() -> None:
    """Test that the core module directory exists with __init__.py.

    This test verifies that the core module is properly structured
    and can be imported.
    """
    # Check that the core directory exists
    core_dir = Path("src/my_coding_agent/core")
    assert core_dir.exists(), f"Core directory does not exist: {core_dir}"
    assert core_dir.is_dir(), f"Core path is not a directory: {core_dir}"

    # Check that __init__.py exists in core directory
    core_init = core_dir / "__init__.py"
    assert core_init.exists(), f"Core __init__.py does not exist: {core_init}"
    assert core_init.is_file(), f"Core __init__.py is not a file: {core_init}"


def test_gui_module_exists() -> None:
    """Test that the gui module directory exists with __init__.py.

    This test verifies that the gui module is properly structured
    and can be imported.
    """
    # Check that the gui directory exists
    gui_dir = Path("src/my_coding_agent/gui")
    assert gui_dir.exists(), f"GUI directory does not exist: {gui_dir}"
    assert gui_dir.is_dir(), f"GUI path is not a directory: {gui_dir}"

    # Check that __init__.py exists in gui directory
    gui_init = gui_dir / "__init__.py"
    assert gui_init.exists(), f"GUI __init__.py does not exist: {gui_init}"
    assert gui_init.is_file(), f"GUI __init__.py is not a file: {gui_init}"


def test_core_module_importable() -> None:
    """Test that the core module can be imported.

    This test verifies that the core module is properly set up
    for Python imports.
    """
    try:
        import my_coding_agent.core

        # If we get here, the module is importable
        assert hasattr(my_coding_agent.core, "__file__")
    except ImportError as e:
        pytest.fail(f"Core module not importable: {e}")


def test_gui_module_importable() -> None:
    """Test that the gui module can be imported.

    This test verifies that the gui module is properly set up
    for Python imports.
    """
    try:
        import my_coding_agent.gui

        # If we get here, the module is importable
        assert hasattr(my_coding_agent.gui, "__file__")
    except ImportError as e:
        pytest.fail(f"GUI module not importable: {e}")


def test_module_structure_integrity() -> None:
    """Test that the overall module structure is correct.

    This test verifies that both core and gui modules are properly
    integrated into the my_coding_agent package.
    """
    try:
        # Test that we can import both modules from the main package
        # Verify both modules are actually modules
        import types

        from my_coding_agent import core, gui

        assert isinstance(core, types.ModuleType), "Core is not a module"
        assert isinstance(gui, types.ModuleType), "GUI is not a module"

    except ImportError as e:
        pytest.fail(f"Module structure integrity test failed: {e}")
