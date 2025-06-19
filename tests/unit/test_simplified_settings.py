"""
Tests for simplified settings configuration focused on MCP server settings.

These tests define the expected behavior for the new simplified Settings class
that focuses only on MCP server configuration and essential UI settings.
"""

import os
from pathlib import Path
from unittest.mock import patch

from src.my_coding_agent.config.settings import (
    Settings,
    get_settings,
    load_settings_from_file,
    reset_settings,
    save_settings_to_file,
)


class TestSimplifiedSettings:
    """Test suite for simplified MCP-focused settings."""

    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()

    def test_settings_initialization(self):
        """Test that settings initialize with correct MCP-focused defaults."""
        settings = Settings()

        # Essential UI settings should be preserved
        assert settings.window_width == 1200
        assert settings.window_height == 800
        assert settings.theme == "dark"

        # MCP server settings should have defaults
        assert settings.mcp_server_url == "http://localhost:8080"
        assert settings.mcp_timeout == 30.0
        assert settings.mcp_enable_streaming is True
        assert settings.mcp_max_retries == 3
        assert settings.mcp_auth_token == ""

        # Directories should still exist
        assert isinstance(settings.config_dir, Path)
        assert isinstance(settings.cache_dir, Path)

    def test_mcp_server_configuration_validation(self):
        """Test MCP server configuration validation."""
        settings = Settings()

        # Test valid URL validation
        settings.mcp_server_url = "https://api.example.com"
        assert settings.is_mcp_url_valid()

        # Test invalid URL validation
        settings.mcp_server_url = "not-a-url"
        assert not settings.is_mcp_url_valid()

        # Test timeout validation
        settings.mcp_timeout = 10.0
        assert settings.is_mcp_timeout_valid()

        settings.mcp_timeout = -1.0
        assert not settings.is_mcp_timeout_valid()

    def test_settings_to_dict_conversion(self):
        """Test settings can be converted to dictionary format."""
        settings = Settings()
        settings_dict = settings.to_dict()

        # Verify essential keys are present
        assert "mcp_server_url" in settings_dict
        assert "mcp_timeout" in settings_dict
        assert "mcp_enable_streaming" in settings_dict
        assert "theme" in settings_dict
        assert "window_width" in settings_dict

        # Verify Path objects are converted to strings
        assert isinstance(settings_dict["config_dir"], str)
        assert isinstance(settings_dict["cache_dir"], str)

    def test_global_settings_singleton(self):
        """Test that get_settings() returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

        # Modify one and verify the other reflects the change
        settings1.mcp_server_url = "https://test.com"
        assert settings2.mcp_server_url == "https://test.com"

    def test_removed_settings_not_present(self):
        """Test that old AI/memory/workspace settings are no longer present."""
        settings = Settings()

        # These should not exist in simplified settings
        assert not hasattr(settings, "ai_model")
        assert not hasattr(settings, "memory_enabled")
        assert not hasattr(settings, "workspace_path")
        assert not hasattr(settings, "max_memory_items")
        assert not hasattr(settings, "ai_temperature")
        assert not hasattr(settings, "ai_max_tokens")

    def test_mcp_environment_variable_overrides(self):
        """Test that MCP settings can be overridden via environment variables."""
        with patch.dict(
            os.environ,
            {
                "MCP_SERVER_URL": "https://custom-server.com",
                "MCP_TIMEOUT": "60",
                "MCP_ENABLE_STREAMING": "false",
                "MCP_MAX_RETRIES": "5",
                "MCP_AUTH_TOKEN": "secret-token",
            },
        ):
            settings = Settings()

            assert settings.mcp_server_url == "https://custom-server.com"
            assert settings.mcp_timeout == 60.0
            assert settings.mcp_enable_streaming is False
            assert settings.mcp_max_retries == 5
            assert settings.mcp_auth_token == "secret-token"

    def test_settings_update_functionality(self):
        """Test that settings can be updated dynamically."""
        settings = Settings()

        # Update MCP settings
        settings.update(
            mcp_server_url="https://new-server.com", mcp_timeout=45.0, theme="light"
        )

        assert settings.mcp_server_url == "https://new-server.com"
        assert settings.mcp_timeout == 45.0
        assert settings.theme == "light"

    def test_mcp_connection_settings_structure(self):
        """Test that MCP connection settings are properly structured."""
        settings = Settings()

        # Test get_mcp_config method returns proper configuration
        mcp_config = settings.get_mcp_config()

        assert "server_url" in mcp_config
        assert "timeout" in mcp_config
        assert "enable_streaming" in mcp_config
        assert "max_retries" in mcp_config
        assert "auth_token" in mcp_config

        # Verify values match settings
        assert mcp_config["server_url"] == settings.mcp_server_url
        assert mcp_config["timeout"] == settings.mcp_timeout
        assert mcp_config["enable_streaming"] == settings.mcp_enable_streaming

    def test_settings_file_operations(self):
        """Test settings can be saved and loaded from files."""
        settings = Settings()
        settings.mcp_server_url = "https://test-server.com"
        settings.theme = "light"

        # Create a temporary config file path
        config_file = settings.config_dir / "test_config.json"

        # Save settings
        save_settings_to_file(settings, config_file)

        # Load settings
        loaded_settings = load_settings_from_file(config_file)

        # Verify loaded settings match saved settings
        assert loaded_settings.mcp_server_url == "https://test-server.com"
        assert loaded_settings.theme == "light"

        # Clean up
        if config_file.exists():
            config_file.unlink()

    def test_mcp_authentication_settings(self):
        """Test MCP authentication configuration."""
        settings = Settings()

        # Test default auth settings
        assert settings.mcp_auth_token == ""
        assert settings.mcp_auth_type == "none"

        # Test OAuth2 configuration
        settings.mcp_auth_type = "oauth2"
        settings.mcp_auth_token = "bearer-token-123"

        auth_config = settings.get_mcp_auth_config()
        assert auth_config["type"] == "oauth2"
        assert auth_config["token"] == "bearer-token-123"

    def test_settings_validation_comprehensive(self):
        """Test comprehensive validation of all MCP settings."""
        settings = Settings()

        # Test valid configuration
        settings.mcp_server_url = "https://api.example.com"
        settings.mcp_timeout = 30.0
        settings.mcp_max_retries = 3
        settings.mcp_auth_token = "valid-token"

        validation_result = settings.validate_mcp_config()
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0

        # Test invalid configuration
        settings.mcp_server_url = "invalid-url"
        settings.mcp_timeout = -5.0
        settings.mcp_max_retries = -1

        validation_result = settings.validate_mcp_config()
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) > 0
