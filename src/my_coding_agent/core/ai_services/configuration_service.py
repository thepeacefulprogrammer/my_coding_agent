"""Configuration Service for AI Agent.

This service handles all configuration-related functionality including:
- AIAgentConfig management and validation
- Environment variable loading and parsing
- Configuration updates and health checks
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AIAgentConfig(BaseModel):
    """Configuration for the AI Agent."""

    azure_endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    azure_api_key: str = Field(..., description="Azure OpenAI API key")
    deployment_name: str = Field(..., description="Azure OpenAI deployment name")
    api_version: str = Field(
        default="2024-02-15-preview", description="Azure OpenAI API version"
    )
    max_tokens: int = Field(default=2000, description="Maximum tokens per response")
    temperature: float = Field(
        default=0.7, description="Temperature for response generation"
    )
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(
        default=3, description="Maximum number of retries for failed requests"
    )

    @classmethod
    def from_env(cls) -> AIAgentConfig:
        """Create configuration from environment variables.

        Returns:
            AIAgentConfig: The configuration instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        required_vars = [
            "ENDPOINT",
            "API_KEY",
            "MODEL",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        return cls(
            azure_endpoint=os.getenv("ENDPOINT") or "",
            azure_api_key=os.getenv("API_KEY") or "",
            deployment_name=os.getenv("MODEL") or "",
            api_version=os.getenv("API_VERSION", "2024-02-15-preview"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
            request_timeout=int(os.getenv("AI_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("AI_MAX_RETRIES", "3")),
        )


class ConfigurationService:
    """Service for managing AI Agent configuration."""

    def __init__(self) -> None:
        """Initialize the configuration service."""
        self.config: AIAgentConfig | None = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def create_config_from_dict(self, config_dict: dict[str, Any]) -> AIAgentConfig:
        """Create configuration from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            AIAgentConfig: The configuration instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            config = AIAgentConfig(**config_dict)
            self.validate_config(config)
            return config
        except Exception as e:
            self.logger.error(f"Failed to create config from dict: {e}")
            raise ValueError(f"Invalid configuration: {e}") from e

    def create_config_from_env(self) -> AIAgentConfig:
        """Create configuration from environment variables.

        Returns:
            AIAgentConfig: The configuration instance

        Raises:
            ValueError: If required environment variables are missing
        """
        try:
            config = AIAgentConfig.from_env()
            self.validate_config(config)
            return config
        except Exception as e:
            self.logger.error(f"Failed to create config from environment: {e}")
            raise

    def set_config(self, config: AIAgentConfig) -> None:
        """Set the current configuration.

        Args:
            config: The configuration to set

        Raises:
            ValueError: If configuration is invalid
        """
        self.validate_config(config)
        self.config = config
        self.logger.info("Configuration set successfully")

    def get_config(self) -> AIAgentConfig:
        """Get the current configuration.

        Returns:
            AIAgentConfig: The current configuration

        Raises:
            ValueError: If configuration is not set
        """
        if self.config is None:
            raise ValueError("Configuration not set")
        return self.config

    def is_configured(self) -> bool:
        """Check if configuration is set and valid.

        Returns:
            bool: True if configuration is set and valid
        """
        if self.config is None:
            return False

        try:
            self.validate_config(self.config)
            return True
        except ValueError:
            return False

    def validate_config(self, config: AIAgentConfig) -> None:
        """Validate configuration for correctness and security.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate required fields are not empty
        if not config.azure_endpoint or not config.azure_endpoint.strip():
            raise ValueError("Azure endpoint cannot be empty")

        if not config.azure_api_key or not config.azure_api_key.strip():
            raise ValueError("Azure API key cannot be empty")

        if not config.deployment_name or not config.deployment_name.strip():
            raise ValueError("Deployment name cannot be empty")

        # Validate endpoint URL format
        endpoint = config.azure_endpoint.strip()
        if not self._is_valid_url(endpoint):
            raise ValueError("Invalid Azure endpoint URL")

        # Validate numeric ranges
        if config.max_tokens <= 0:
            raise ValueError("Max tokens must be greater than 0")

        if not 0.0 <= config.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")

        if config.request_timeout <= 0:
            raise ValueError("Request timeout must be greater than 0")

        if config.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid.

        Args:
            url: URL to check

        Returns:
            bool: True if URL is valid
        """
        # Basic URL validation for Azure OpenAI endpoints
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"[a-zA-Z0-9.-]+\."  # domain name
            r"[a-zA-Z]{2,}"  # domain extension
            r"(?:/.*)?$"  # optional path
        )
        return bool(url_pattern.match(url))

    def update_config(self, updates: dict[str, Any]) -> AIAgentConfig:
        """Update the current configuration with new values.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            AIAgentConfig: The updated configuration

        Raises:
            ValueError: If configuration is not set or updates are invalid
        """
        if self.config is None:
            raise ValueError("Configuration not set")

        # Create a dict from current config and apply updates
        current_dict = self.config.model_dump()
        current_dict.update(updates)

        # Create new config with updated values
        updated_config = self.create_config_from_dict(current_dict)
        self.config = updated_config

        self.logger.info(f"Configuration updated with keys: {list(updates.keys())}")
        return updated_config

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the configuration service.

        Returns:
            dict: Health status information
        """
        health = {
            "service_name": "ConfigurationService",
            "is_configured": self.is_configured(),
            "config_valid": False,
        }

        if self.config is not None:
            try:
                self.validate_config(self.config)
                health["config_valid"] = True
                health["endpoint"] = self.config.azure_endpoint
                health["deployment"] = self.config.deployment_name
                health["api_version"] = self.config.api_version
                health["max_tokens"] = self.config.max_tokens
                health["temperature"] = self.config.temperature
            except ValueError as e:
                health["config_valid"] = False
                health["validation_error"] = str(e)

        return health
