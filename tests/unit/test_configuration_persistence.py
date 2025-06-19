"""
Tests for configuration persistence and loading functionality.

These tests verify that settings are properly saved and loaded across
application restarts, ensuring configuration persistence works correctly.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.my_coding_agent.config.settings import (
    Settings,
    get_settings,
    load_settings_from_file,
    reset_settings,
    save_settings_to_file,
)


class TestConfigurationPersistence:
    """Test suite for configuration persistence and loading."""

    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()

    def test_settings_save_and_load_cycle(self):
        """Test complete save and load cycle of settings."""
        # Create custom settings
        settings = Settings()
        settings.mcp_server_url = "https://custom-server.example.com"
        settings.mcp_timeout = 45.0
        settings.mcp_enable_streaming = False
        settings.mcp_auth_token = "test-token-123"
        settings.theme = "light"
        settings.window_width = 1600
        settings.window_height = 900

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)

        try:
            # Save settings
            save_settings_to_file(settings, config_path)

            # Verify file exists and has content
            assert config_path.exists()
            assert config_path.stat().st_size > 0

            # Load settings from file
            loaded_settings = load_settings_from_file(config_path)

            # Verify all MCP settings were preserved
            assert loaded_settings.mcp_server_url == "https://custom-server.example.com"
            assert loaded_settings.mcp_timeout == 45.0
            assert loaded_settings.mcp_enable_streaming is False
            assert loaded_settings.mcp_auth_token == "test-token-123"

            # Verify UI settings were preserved
            assert loaded_settings.theme == "light"
            assert loaded_settings.window_width == 1600
            assert loaded_settings.window_height == 900

        finally:
            # Clean up
            if config_path.exists():
                config_path.unlink()

    def test_settings_persistence_with_defaults(self):
        """Test that default settings are properly handled during persistence."""
        # Create settings with all defaults
        settings = Settings()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)

        try:
            # Save and reload default settings
            save_settings_to_file(settings, config_path)
            loaded_settings = load_settings_from_file(config_path)

            # Verify defaults are preserved
            assert loaded_settings.mcp_server_url == "http://localhost:8080"
            assert loaded_settings.mcp_timeout == 30.0
            assert loaded_settings.mcp_enable_streaming is True
            assert loaded_settings.mcp_max_retries == 3
            assert loaded_settings.mcp_auth_token == ""
            assert loaded_settings.theme == "dark"

        finally:
            if config_path.exists():
                config_path.unlink()

    def test_settings_loading_with_missing_file(self):
        """Test loading settings when configuration file doesn't exist."""
        non_existent_path = Path("/tmp/non_existent_config.json")

        # Ensure file doesn't exist
        if non_existent_path.exists():
            non_existent_path.unlink()

        # Loading should return default settings
        loaded_settings = load_settings_from_file(non_existent_path)

        # Verify we get default settings
        assert loaded_settings.mcp_server_url == "http://localhost:8080"
        assert loaded_settings.theme == "dark"

    def test_settings_loading_with_corrupted_file(self):
        """Test loading settings when configuration file is corrupted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)
            # Write invalid JSON
            f.write("{ invalid json content")

        try:
            # Loading should return default settings on error
            loaded_settings = load_settings_from_file(config_path)

            # Verify we get default settings despite corruption
            assert loaded_settings.mcp_server_url == "http://localhost:8080"
            assert loaded_settings.theme == "dark"

        finally:
            if config_path.exists():
                config_path.unlink()

    def test_settings_directory_creation(self):
        """Test that configuration directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "nested" / "config" / "path"
            config_file = config_dir / "settings.json"

            # Ensure directory doesn't exist
            assert not config_dir.exists()

            # Save settings should create directory
            settings = Settings()
            save_settings_to_file(settings, config_file)

            # Verify directory was created
            assert config_dir.exists()
            assert config_file.exists()

    def test_environment_variables_override_loaded_settings(self):
        """Test that environment variables override settings when creating new Settings instances."""
        # Create settings file
        settings = Settings()
        settings.mcp_server_url = "https://file-server.com"
        settings.mcp_timeout = 20.0

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)

        try:
            save_settings_to_file(settings, config_path)

            # Load settings from file (this doesn't apply env vars)
            loaded_settings = load_settings_from_file(config_path)
            assert loaded_settings.mcp_server_url == "https://file-server.com"

            # But creating new Settings instance should apply env vars
            with patch.dict(
                os.environ,
                {"MCP_SERVER_URL": "https://env-server.com", "MCP_TIMEOUT": "60"},
            ):
                env_settings = Settings()

                # Environment variables should override defaults
                assert env_settings.mcp_server_url == "https://env-server.com"
                assert env_settings.mcp_timeout == 60.0

        finally:
            if config_path.exists():
                config_path.unlink()

    def test_partial_configuration_loading(self):
        """Test loading configuration with only some settings present."""
        # Manually create a partial JSON config
        partial_config = {
            "mcp_server_url": "https://partial-server.com",
            "theme": "light",
            # Missing other settings
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)
            import json

            json.dump(partial_config, f)

        try:
            loaded_settings = load_settings_from_file(config_path)

            # Specified settings should be loaded
            assert loaded_settings.mcp_server_url == "https://partial-server.com"
            assert loaded_settings.theme == "light"

            # Missing settings should have defaults
            assert loaded_settings.mcp_timeout == 30.0  # default
            assert loaded_settings.mcp_enable_streaming is True  # default

        finally:
            if config_path.exists():
                config_path.unlink()

    def test_settings_validation_after_loading(self):
        """Test that loaded settings can be validated."""
        # Create settings with invalid values
        invalid_config = {
            "mcp_server_url": "not-a-valid-url",
            "mcp_timeout": -5.0,
            "mcp_max_retries": -1,
            "theme": "dark",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)
            import json

            json.dump(invalid_config, f)

        try:
            loaded_settings = load_settings_from_file(config_path)

            # Validation should detect issues
            validation = loaded_settings.validate_mcp_config()
            assert validation["valid"] is False
            assert len(validation["errors"]) > 0

        finally:
            if config_path.exists():
                config_path.unlink()

    def test_global_settings_persistence(self):
        """Test that global settings instance works with persistence."""
        # Modify global settings
        settings = get_settings()
        settings.mcp_server_url = "https://global-test.com"
        settings.theme = "light"

        # Create config file path
        config_file = settings.config_dir / "test_global.json"

        try:
            # Save current global settings
            save_settings_to_file(settings, config_file)

            # Reset global settings
            reset_settings()

            # Verify reset worked
            new_settings = get_settings()
            assert new_settings.mcp_server_url == "http://localhost:8080"  # default

            # Load from file and verify
            loaded_settings = load_settings_from_file(config_file)
            assert loaded_settings.mcp_server_url == "https://global-test.com"
            assert loaded_settings.theme == "light"

        finally:
            if config_file.exists():
                config_file.unlink()
            reset_settings()
