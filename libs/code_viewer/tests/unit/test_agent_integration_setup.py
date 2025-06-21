"""
Tests for Agent Integration Setup (Task 1.0)

This module tests the basic setup requirements for agent architecture integration:
- PydanticAI dependency removal
- Agent integration package structure
- Package initialization
- Documentation updates
"""

from pathlib import Path

import pytest


class TestAgentIntegrationSetup:
    """Test agent integration setup requirements."""

    def test_pydantic_ai_removed_from_requirements(self):
        """Test that pydantic-ai dependency is removed from pyproject.toml."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml should exist"

        with open(pyproject_path) as f:
            content = f.read().lower()

        # Should not contain pydantic-ai references in dependencies
        assert "pydantic-ai" not in content, "pydantic-ai should be removed from pyproject.toml dependencies"

    def test_agent_integration_package_exists(self):
        """Test that agent integration package directory exists."""
        package_path = Path("src/code_viewer/core/agent_integration")
        assert package_path.exists(), "Agent integration package directory should exist"
        assert package_path.is_dir(), "Agent integration should be a directory"

    def test_agent_integration_init_exists(self):
        """Test that agent integration package __init__.py exists."""
        init_path = Path("src/code_viewer/core/agent_integration/__init__.py")
        assert init_path.exists(), "Agent integration __init__.py should exist"

    def test_agent_integration_init_has_public_api(self):
        """Test that agent integration __init__.py exports public API."""
        init_path = Path("src/code_viewer/core/agent_integration/__init__.py")

        if init_path.exists():
            with open(init_path) as f:
                content = f.read()

            # Should have some basic structure for public API
            assert "__all__" in content or "import" in content, "Should have public API exports"

    def test_readme_mentions_agent_integration(self):
        """Test that README.md mentions agent integration."""
        readme_path = Path("README.md")
        assert readme_path.exists(), "README.md should exist"

        with open(readme_path) as f:
            content = f.read().lower()

        # Should mention agent integration or architecture
        agent_terms = ["agent", "integration", "architecture"]
        has_agent_reference = any(term in content for term in agent_terms)
        assert has_agent_reference, "README should mention agent integration or architecture"


class TestProjectStructure:
    """Test overall project structure expectations."""

    def test_core_package_structure(self):
        """Test that core package has expected structure."""
        core_path = Path("src/code_viewer/core")
        assert core_path.exists(), "Core package should exist"

        # Check for agent_integration package
        agent_integration_path = core_path / "agent_integration"
        assert agent_integration_path.exists(), "Agent integration package should exist in core"


if __name__ == "__main__":
    # Run tests to verify current state
    pytest.main([__file__, "-v"])
