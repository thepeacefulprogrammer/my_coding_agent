#!/usr/bin/env python3
"""
Basic AI Service Configuration Example

This example shows how to configure AI services for different scenarios:
- Environment variable configuration
- Configuration file setup
- Runtime parameter adjustments

This is a reference implementation for developers getting started with AI services.
"""

import os
from dataclasses import dataclass


@dataclass
class AIServiceConfig:
    """Example configuration structure for AI services."""

    # Azure OpenAI Configuration
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str = "2024-07-01-preview"
    deployment_name: str = "gpt-4o"

    # Model Parameters
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = True

    # Connection Settings
    timeout_seconds: int = 30
    max_retries: int = 3


def load_config_from_environment() -> AIServiceConfig | None:
    """Load AI service configuration from environment variables."""

    # Check for required environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint or not api_key:
        print("❌ Missing required environment variables:")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_API_KEY")
        return None

    return AIServiceConfig(
        azure_openai_endpoint=endpoint,
        azure_openai_api_key=api_key,
        azure_openai_api_version=os.getenv(
            "AZURE_OPENAI_API_VERSION", "2024-07-01-preview"
        ),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("AI_MAX_TOKENS", "1000")),
        stream=os.getenv("AI_STREAM", "true").lower() == "true",
        timeout_seconds=int(os.getenv("AI_TIMEOUT", "30")),
        max_retries=int(os.getenv("AI_MAX_RETRIES", "3")),
    )


def example_environment_setup():
    """Show example environment variable setup."""
    print("🔧 Environment Variable Configuration Example")
    print("=" * 50)
    print("Add these to your .bashrc, .zshrc, or .env file:")
    print()
    print("# Required Azure OpenAI Configuration")
    print("export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
    print("export AZURE_OPENAI_API_KEY='your-api-key-here'")
    print()
    print("# Optional Configuration")
    print("export AZURE_OPENAI_API_VERSION='2024-07-01-preview'")
    print("export AZURE_OPENAI_DEPLOYMENT='gpt-4o'")
    print("export AI_TEMPERATURE='0.7'")
    print("export AI_MAX_TOKENS='1000'")
    print("export AI_STREAM='true'")
    print("export AI_TIMEOUT='30'")
    print("export AI_MAX_RETRIES='3'")


def example_yaml_config():
    """Show example YAML configuration structure."""
    print("\n📄 YAML Configuration Example")
    print("=" * 50)
    print("Create a file called 'ai_config.yaml':")
    print()
    yaml_content = """
ai_service:
  provider: "azure_openai"
  azure_openai:
    endpoint: "https://your-resource.openai.azure.com/"
    api_key: "${AZURE_OPENAI_API_KEY}"  # Reference environment variable
    api_version: "2024-07-01-preview"
    deployment_name: "gpt-4o"
    model_params:
      temperature: 0.7
      max_tokens: 1000
      stream: true
    connection:
      timeout_seconds: 30
      max_retries: 3
"""
    print(yaml_content.strip())


def main():
    """Run configuration examples."""
    print("🎯 AI Service Configuration Examples")
    print("Learn how to configure AI services for your application")

    # Show environment setup
    example_environment_setup()

    # Show YAML config
    example_yaml_config()

    # Try to load current environment config
    print("\n🔍 Current Environment Check")
    print("=" * 50)

    config = load_config_from_environment()
    if config:
        print("✅ Configuration loaded successfully from environment!")
        print(f"Endpoint: {config.azure_openai_endpoint}")
        print(f"Deployment: {config.deployment_name}")
        print(f"Temperature: {config.temperature}")
        print(f"Max Tokens: {config.max_tokens}")
        print(f"Streaming: {config.stream}")
    else:
        print("ℹ️  Set environment variables to test configuration loading")

    print("\n🎉 Configuration examples completed!")


if __name__ == "__main__":
    main()
