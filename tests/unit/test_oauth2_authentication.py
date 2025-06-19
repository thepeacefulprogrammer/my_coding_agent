"""
Comprehensive unit tests for OAuth 2.0 authentication support for MCP servers.

Tests OAuth 2.0 authentication including:
- Authorization Code Flow
- Client Credentials Flow
- Token refresh and lifecycle management
- Error handling and security validation
- Integration with MCP client connections
"""

import asyncio
import urllib.parse
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.my_coding_agent.core.mcp.mcp_client import MCPClient, MCPConnectionError
from src.my_coding_agent.core.mcp.oauth2_auth import (
    OAuth2AuthenticationError,
    OAuth2Authenticator,
    OAuth2Config,
    OAuth2Error,
    OAuth2Token,
)


class TestOAuth2Configuration:
    """Test suite for OAuth 2.0 configuration management."""

    def test_oauth2_config_initialization(self):
        """Test OAuth 2.0 configuration initialization."""
        config = OAuth2Config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_url="https://auth.example.com/oauth/authorize",
            token_url="https://auth.example.com/oauth/token",
            scope="read write",
            redirect_uri="http://localhost:8080/callback",
        )

        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.authorization_url == "https://auth.example.com/oauth/authorize"
        assert config.token_url == "https://auth.example.com/oauth/token"
        assert config.scope == "read write"
        assert config.redirect_uri == "http://localhost:8080/callback"

    def test_oauth2_config_validation(self):
        """Test OAuth 2.0 configuration validation."""
        # Test missing required fields
        with pytest.raises(ValueError, match="client_id is required"):
            OAuth2Config(
                client_id="",
                authorization_url="https://auth.example.com/oauth/authorize",
                token_url="https://auth.example.com/oauth/token",
            )

        # Test invalid URLs
        with pytest.raises(ValueError, match="Invalid authorization_url"):
            OAuth2Config(
                client_id="test-client-id",
                authorization_url="invalid-url",
                token_url="https://auth.example.com/oauth/token",
            )

    def test_oauth2_config_from_dict(self):
        """Test creating OAuth 2.0 config from dictionary."""
        config_dict = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "authorization_url": "https://auth.example.com/oauth/authorize",
            "token_url": "https://auth.example.com/oauth/token",
            "scope": "read write",
            "redirect_uri": "http://localhost:8080/callback",
        }

        config = OAuth2Config.from_dict(config_dict)
        assert config.client_id == "test-client-id"
        assert config.scope == "read write"


class TestOAuth2Token:
    """Test suite for OAuth 2.0 token management."""

    def test_oauth2_token_initialization(self):
        """Test OAuth 2.0 token initialization."""
        token = OAuth2Token(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="test-refresh-token",
            scope="read write",
        )

        assert token.access_token == "test-access-token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.refresh_token == "test-refresh-token"
        assert token.scope == "read write"
        assert isinstance(token.expires_at, datetime)

    def test_oauth2_token_expiry_check(self):
        """Test OAuth 2.0 token expiry checking."""
        # Test non-expired token
        token = OAuth2Token(
            access_token="test-access-token", token_type="Bearer", expires_in=3600
        )
        assert not token.is_expired()

        # Test expired token
        expired_token = OAuth2Token(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=-3600,  # Expired 1 hour ago
        )
        assert expired_token.is_expired()

    def test_oauth2_token_needs_refresh(self):
        """Test OAuth 2.0 token refresh necessity."""
        # Test token that doesn't need refresh yet
        token = OAuth2Token(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="test-refresh-token",
        )
        assert not token.needs_refresh()

        # Test token that needs refresh (expires in 4 minutes, threshold is 5)
        soon_expired_token = OAuth2Token(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=240,  # 4 minutes
            refresh_token="test-refresh-token",
        )
        assert soon_expired_token.needs_refresh()

    def test_oauth2_token_from_response(self):
        """Test creating OAuth 2.0 token from API response."""
        response_data = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "test-refresh-token",
            "scope": "read write",
        }

        token = OAuth2Token.from_response(response_data)
        assert token.access_token == "test-access-token"
        assert token.expires_in == 3600

    def test_oauth2_token_to_header(self):
        """Test creating authorization header from token."""
        token = OAuth2Token(
            access_token="test-access-token", token_type="Bearer", expires_in=3600
        )

        header = token.to_authorization_header()
        assert header == "Bearer test-access-token"


class TestOAuth2Authenticator:
    """Test suite for OAuth 2.0 authenticator."""

    @pytest.fixture
    def oauth2_config(self):
        """Create OAuth 2.0 configuration for testing."""
        return OAuth2Config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_url="https://auth.example.com/oauth/authorize",
            token_url="https://auth.example.com/oauth/token",
            scope="read write",
            redirect_uri="http://localhost:8080/callback",
        )

    @pytest.fixture
    def oauth2_authenticator(self, oauth2_config):
        """Create OAuth 2.0 authenticator for testing."""
        return OAuth2Authenticator(oauth2_config)

    def test_oauth2_authenticator_initialization(
        self, oauth2_authenticator, oauth2_config
    ):
        """Test OAuth 2.0 authenticator initialization."""
        assert oauth2_authenticator.config == oauth2_config
        assert oauth2_authenticator.current_token is None

    def test_generate_authorization_url(self, oauth2_authenticator):
        """Test generating OAuth 2.0 authorization URL."""
        auth_url = oauth2_authenticator.generate_authorization_url()

        assert "https://auth.example.com/oauth/authorize" in auth_url
        assert "client_id=test-client-id" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=read+write" in auth_url
        assert "state=" in auth_url  # State parameter should be included

    @pytest.mark.asyncio
    async def test_authorization_code_flow(self, oauth2_authenticator):
        """Test OAuth 2.0 authorization code flow."""
        # First generate a valid state through the authorization URL
        auth_url = oauth2_authenticator.generate_authorization_url()

        # Extract state from the URL
        parsed_url = urllib.parse.urlparse(auth_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        state = query_params.get("state", [None])[0]

        # Mock HTTP client
        mock_response = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "test-refresh-token",
            "scope": "read write",
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            token = await oauth2_authenticator.exchange_code_for_token(
                "auth-code-123", state
            )

            assert token.access_token == "test-access-token"
            assert token.token_type == "Bearer"
            assert oauth2_authenticator.current_token == token

    @pytest.mark.asyncio
    async def test_client_credentials_flow(self, oauth2_authenticator):
        """Test OAuth 2.0 client credentials flow."""
        mock_response = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write",
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            token = await oauth2_authenticator.client_credentials_flow()

            assert token.access_token == "test-access-token"
            assert oauth2_authenticator.current_token == token

    @pytest.mark.asyncio
    async def test_token_refresh(self, oauth2_authenticator):
        """Test OAuth 2.0 token refresh."""
        # Set up initial token that needs refresh
        initial_token = OAuth2Token(
            access_token="old-access-token",
            token_type="Bearer",
            expires_in=60,  # Expires soon
            refresh_token="test-refresh-token",
        )
        oauth2_authenticator.current_token = initial_token

        mock_response = {
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "new-refresh-token",
            "scope": "read write",
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            new_token = await oauth2_authenticator.refresh_token()

            assert new_token.access_token == "new-access-token"
            assert oauth2_authenticator.current_token == new_token

    @pytest.mark.asyncio
    async def test_automatic_token_refresh(self, oauth2_authenticator):
        """Test automatic token refresh when needed."""
        # Set up token that needs refresh
        soon_expired_token = OAuth2Token(
            access_token="soon-expired-token",
            token_type="Bearer",
            expires_in=240,  # 4 minutes, needs refresh
            refresh_token="test-refresh-token",
        )
        oauth2_authenticator.current_token = soon_expired_token

        mock_response = {
            "access_token": "refreshed-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "new-refresh-token",
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            header = await oauth2_authenticator.get_authorization_header()

            assert header == "Bearer refreshed-access-token"

    def test_token_storage_and_retrieval(self, oauth2_authenticator):
        """Test token storage and retrieval functionality."""
        token = OAuth2Token(
            access_token="test-access-token", token_type="Bearer", expires_in=3600
        )

        # Store token
        oauth2_authenticator.store_token(token)
        assert oauth2_authenticator.current_token == token

        # Retrieve token
        retrieved_token = oauth2_authenticator.get_current_token()
        assert retrieved_token == token

    @pytest.mark.asyncio
    async def test_error_handling_invalid_credentials(self, oauth2_authenticator):
        """Test error handling for invalid credentials."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 401
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={
                    "error": "invalid_client",
                    "error_description": "Invalid client credentials",
                }
            )

            with pytest.raises(
                OAuth2AuthenticationError, match="Invalid client credentials"
            ):
                await oauth2_authenticator.client_credentials_flow()

    @pytest.mark.asyncio
    async def test_error_handling_network_failure(self, oauth2_authenticator):
        """Test error handling for network failures."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Network timeout")

            with pytest.raises(OAuth2Error, match="Network timeout"):
                await oauth2_authenticator.client_credentials_flow()

    def test_pkce_support(self, oauth2_authenticator):
        """Test PKCE (Proof Key for Code Exchange) support."""
        # Generate PKCE challenge
        code_verifier, code_challenge = oauth2_authenticator.generate_pkce_challenge()

        assert len(code_verifier) >= 43  # Minimum length for PKCE
        assert len(code_challenge) > 0
        assert code_verifier != code_challenge  # Should be different

    def test_state_parameter_validation(self, oauth2_authenticator):
        """Test state parameter validation for security."""
        # Generate authorization URL with state
        auth_url = oauth2_authenticator.generate_authorization_url()

        # Extract state from URL
        parsed_url = urllib.parse.urlparse(auth_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        state = query_params.get("state", [None])[0]

        assert state is not None
        assert len(state) >= 16  # Minimum secure length

        # Validate state
        assert oauth2_authenticator.validate_state(state) is True
        assert oauth2_authenticator.validate_state("invalid-state") is False


class TestMCPClientOAuth2Integration:
    """Test suite for OAuth 2.0 integration with MCP client."""

    @pytest.fixture
    def oauth2_config(self):
        """Create OAuth 2.0 configuration for testing."""
        return OAuth2Config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_url="https://auth.example.com/oauth/authorize",
            token_url="https://auth.example.com/oauth/token",
            scope="mcp:read mcp:write",
        )

    @pytest.fixture
    def mcp_config_with_oauth2(self, oauth2_config):
        """Create MCP client configuration with OAuth 2.0."""
        return {
            "server_name": "oauth-protected-server",
            "url": "https://api.example.com/mcp",
            "transport": "http",
            "oauth2": oauth2_config.to_dict(),
        }

    def test_mcp_client_with_oauth2_config(self, mcp_config_with_oauth2):
        """Test MCP client initialization with OAuth 2.0 configuration."""
        client = MCPClient(mcp_config_with_oauth2)

        assert client.oauth2_authenticator is not None
        assert client.oauth2_authenticator.config.client_id == "test-client-id"

    @pytest.mark.asyncio
    async def test_mcp_client_oauth2_authentication_flow(self, mcp_config_with_oauth2):
        """Test MCP client OAuth 2.0 authentication flow."""
        client = MCPClient(mcp_config_with_oauth2)

        # Mock token response
        mock_token_response = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "mcp:read mcp:write",
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_token_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            # Authenticate using client credentials flow
            await client.authenticate_oauth2()

            assert client.oauth2_authenticator.current_token is not None
            assert (
                client.oauth2_authenticator.current_token.access_token
                == "test-access-token"
            )

    @pytest.mark.asyncio
    async def test_mcp_client_authenticated_requests(self, mcp_config_with_oauth2):
        """Test MCP client making authenticated requests with OAuth 2.0."""
        client = MCPClient(mcp_config_with_oauth2)

        # Set up authenticated token
        token = OAuth2Token(
            access_token="test-access-token", token_type="Bearer", expires_in=3600
        )
        client.oauth2_authenticator.current_token = token

        # Test that the client is authenticated
        assert client.is_oauth2_authenticated() is True

        # Test token info retrieval
        token_info = client.get_oauth2_token_info()
        assert token_info is not None
        assert token_info["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_mcp_client_token_refresh_on_401(self, mcp_config_with_oauth2):
        """Test automatic token refresh when receiving 401 Unauthorized."""
        client = MCPClient(mcp_config_with_oauth2)

        # Set up soon-to-expire token
        old_token = OAuth2Token(
            access_token="old-access-token",
            token_type="Bearer",
            expires_in=60,
            refresh_token="test-refresh-token",
        )
        client.oauth2_authenticator.current_token = old_token

        # Mock refresh token response
        mock_refresh_response = {
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "new-refresh-token",
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_refresh_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            # This should trigger token refresh
            header = await client.oauth2_authenticator.get_authorization_header()

            assert "new-access-token" in header

    def test_oauth2_configuration_validation_in_mcp_client(self):
        """Test OAuth 2.0 configuration validation in MCP client."""
        # Test invalid OAuth 2.0 configuration
        invalid_config = {
            "server_name": "test-server",
            "url": "https://api.example.com/mcp",
            "transport": "http",
            "oauth2": {
                "client_id": "",  # Invalid empty client_id
                "token_url": "https://auth.example.com/oauth/token",
            },
        }

        with pytest.raises(ValueError, match="client_id is required"):
            MCPClient(invalid_config)

    @pytest.mark.asyncio
    async def test_oauth2_connection_failure_handling(self, mcp_config_with_oauth2):
        """Test handling of OAuth 2.0 connection failures."""
        client = MCPClient(mcp_config_with_oauth2)

        # Mock network failure during authentication
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = ConnectionError("Network unreachable")

            with pytest.raises(
                MCPConnectionError, match="OAuth 2.0 authentication failed"
            ):
                await client.authenticate_oauth2()

    def test_oauth2_security_best_practices(self, oauth2_config):
        """Test OAuth 2.0 security best practices implementation."""
        authenticator = OAuth2Authenticator(oauth2_config)

        # Test secure state generation
        auth_url = authenticator.generate_authorization_url()
        assert "state=" in auth_url

        # Test PKCE support for public clients
        code_verifier, code_challenge = authenticator.generate_pkce_challenge()
        assert len(code_verifier) >= 43
        assert code_challenge != code_verifier
