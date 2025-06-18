"""Unit tests for ConfigurationService."""

import os
from unittest.mock import patch

import pytest
from src.my_coding_agent.core.ai_services.configuration_service import (
    AIAgentConfig,
    ConfigurationService,
)


class TestAIAgentConfig:
    """Test the AIAgentConfig model."""

    def test_config_creation_with_required_fields(self):
        """Test creating config with all required fields."""
        config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )

        assert config.azure_endpoint == "https://test.openai.azure.com"
        assert config.azure_api_key == "test-key"
        assert config.deployment_name == "test-deployment"
        assert config.api_version == "2024-02-15-preview"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.request_timeout == 30
        assert config.max_retries == 3

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values."""
        config = AIAgentConfig(
            azure_endpoint="https://custom.openai.azure.com",
            azure_api_key="custom-key",
            deployment_name="custom-deployment",
            api_version="2024-01-01",
            max_tokens=4000,
            temperature=0.5,
            request_timeout=60,
            max_retries=5,
        )

        assert config.azure_endpoint == "https://custom.openai.azure.com"
        assert config.azure_api_key == "custom-key"
        assert config.deployment_name == "custom-deployment"
        assert config.api_version == "2024-01-01"
        assert config.max_tokens == 4000
        assert config.temperature == 0.5
        assert config.request_timeout == 60
        assert config.max_retries == 5

    @patch.dict(
        os.environ,
        {
            "ENDPOINT": "https://env.openai.azure.com",
            "API_KEY": "env-api-key",
            "MODEL": "env-model",
            "API_VERSION": "2024-03-01",
            "AI_MAX_TOKENS": "3000",
            "AI_TEMPERATURE": "0.8",
            "AI_REQUEST_TIMEOUT": "45",
            "AI_MAX_RETRIES": "4",
        },
    )
    def test_from_env_with_all_variables(self):
        """Test creating config from environment variables."""
        config = AIAgentConfig.from_env()

        assert config.azure_endpoint == "https://env.openai.azure.com"
        assert config.azure_api_key == "env-api-key"
        assert config.deployment_name == "env-model"
        assert config.api_version == "2024-03-01"
        assert config.max_tokens == 3000
        assert config.temperature == 0.8
        assert config.request_timeout == 45
        assert config.max_retries == 4

    @patch.dict(
        os.environ,
        {
            "ENDPOINT": "https://minimal.openai.azure.com",
            "API_KEY": "minimal-key",
            "MODEL": "minimal-model",
        },
        clear=True,
    )
    def test_from_env_with_minimal_variables(self):
        """Test creating config from environment with only required variables."""
        config = AIAgentConfig.from_env()

        assert config.azure_endpoint == "https://minimal.openai.azure.com"
        assert config.azure_api_key == "minimal-key"
        assert config.deployment_name == "minimal-model"
        # Should use defaults
        assert config.api_version == "2024-02-15-preview"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.request_timeout == 30
        assert config.max_retries == 3

    @patch.dict(
        os.environ,
        {
            "API_KEY": "key-only",
            "MODEL": "model-only",
        },
        clear=True,
    )
    def test_from_env_missing_required_variables(self):
        """Test error when required environment variables are missing."""
        with pytest.raises(
            ValueError, match="Missing required environment variables: ENDPOINT"
        ):
            AIAgentConfig.from_env()

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_no_variables(self):
        """Test error when no environment variables are set."""
        with pytest.raises(ValueError, match="Missing required environment variables"):
            AIAgentConfig.from_env()


class TestConfigurationService:
    """Test the ConfigurationService."""

    def test_initialization(self):
        """Test ConfigurationService initialization."""
        service = ConfigurationService()
        assert service is not None
        assert hasattr(service, "config")
        assert service.config is None

    def test_create_config_from_dict(self):
        """Test creating config from dictionary."""
        service = ConfigurationService()
        config_dict = {
            "azure_endpoint": "https://test.openai.azure.com",
            "azure_api_key": "test-key",
            "deployment_name": "test-deployment",
            "max_tokens": 1500,
        }

        config = service.create_config_from_dict(config_dict)

        assert isinstance(config, AIAgentConfig)
        assert config.azure_endpoint == "https://test.openai.azure.com"
        assert config.azure_api_key == "test-key"
        assert config.deployment_name == "test-deployment"
        assert config.max_tokens == 1500

    @patch.dict(
        os.environ,
        {
            "ENDPOINT": "https://service.openai.azure.com",
            "API_KEY": "service-key",
            "MODEL": "service-model",
        },
    )
    def test_create_config_from_env(self):
        """Test creating config from environment variables."""
        service = ConfigurationService()
        config = service.create_config_from_env()

        assert isinstance(config, AIAgentConfig)
        assert config.azure_endpoint == "https://service.openai.azure.com"
        assert config.azure_api_key == "service-key"
        assert config.deployment_name == "service-model"

    def test_set_config(self):
        """Test setting configuration."""
        service = ConfigurationService()
        config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )

        service.set_config(config)
        assert service.config == config

    def test_get_config_when_set(self):
        """Test getting configuration when it's set."""
        service = ConfigurationService()
        config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )
        service.set_config(config)

        retrieved_config = service.get_config()
        assert retrieved_config == config

    def test_get_config_when_not_set(self):
        """Test getting configuration when it's not set."""
        service = ConfigurationService()
        with pytest.raises(ValueError, match="Configuration not set"):
            service.get_config()

    def test_is_configured_true(self):
        """Test is_configured returns True when config is set."""
        service = ConfigurationService()
        config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )
        service.set_config(config)

        assert service.is_configured() is True

    def test_is_configured_false(self):
        """Test is_configured returns False when config is not set."""
        service = ConfigurationService()
        assert service.is_configured() is False

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        service = ConfigurationService()
        config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )

        # Should not raise any exception
        service.validate_config(config)

    def test_validate_config_invalid_endpoint(self):
        """Test config validation with invalid endpoint."""
        service = ConfigurationService()
        config = AIAgentConfig(
            azure_endpoint="not-a-url",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )

        with pytest.raises(ValueError, match="Invalid Azure endpoint URL"):
            service.validate_config(config)

    def test_validate_config_empty_fields(self):
        """Test config validation with empty required fields."""
        service = ConfigurationService()
        config = AIAgentConfig(
            azure_endpoint="",
            azure_api_key="",
            deployment_name="",
        )

        with pytest.raises(ValueError, match="Azure endpoint cannot be empty"):
            service.validate_config(config)

    def test_update_config(self):
        """Test updating configuration."""
        service = ConfigurationService()
        original_config = AIAgentConfig(
            azure_endpoint="https://original.openai.azure.com",
            azure_api_key="original-key",
            deployment_name="original-deployment",
            max_tokens=1000,
        )
        service.set_config(original_config)

        updates = {
            "max_tokens": 2500,
            "temperature": 0.9,
        }

        updated_config = service.update_config(updates)

        assert updated_config.azure_endpoint == "https://original.openai.azure.com"
        assert updated_config.max_tokens == 2500
        assert updated_config.temperature == 0.9
        assert service.config == updated_config

    def test_get_health_status(self):
        """Test getting health status."""
        service = ConfigurationService()

        # Test without config
        health = service.get_health_status()
        assert health["service_name"] == "ConfigurationService"
        assert health["is_configured"] is False
        assert health["config_valid"] is False

        # Test with config
        config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )
        service.set_config(config)

        health = service.get_health_status()
        assert health["service_name"] == "ConfigurationService"
        assert health["is_configured"] is True
        assert health["config_valid"] is True
        assert health["endpoint"] == "https://test.openai.azure.com"
        assert health["deployment"] == "test-deployment"
