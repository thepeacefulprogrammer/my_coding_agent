"""
OAuth 2.0 authentication support for secured MCP servers.

This module provides comprehensive OAuth 2.0 authentication including:
- Authorization Code Flow with PKCE support
- Client Credentials Flow
- Token lifecycle management and automatic refresh
- Security best practices implementation
- Integration with MCP client connections
"""

import asyncio
import base64
import hashlib
import logging
import secrets
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class OAuth2Error(Exception):
    """Base exception for OAuth 2.0 related errors."""

    pass


class OAuth2AuthenticationError(OAuth2Error):
    """Exception raised when OAuth 2.0 authentication fails."""

    pass


class OAuth2TokenExpiredError(OAuth2Error):
    """Exception raised when OAuth 2.0 token has expired."""

    pass


@dataclass
class OAuth2Config:
    """OAuth 2.0 configuration for MCP server authentication."""

    client_id: str
    client_secret: str | None = None
    authorization_url: str | None = None
    token_url: str = ""
    scope: str | None = None
    redirect_uri: str | None = None
    audience: str | None = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate OAuth 2.0 configuration."""
        if not self.client_id:
            raise ValueError("client_id is required")

        if not self.token_url:
            raise ValueError("token_url is required")

        # Validate URLs
        if self.authorization_url and not self._is_valid_url(self.authorization_url):
            raise ValueError("Invalid authorization_url")

        if not self._is_valid_url(self.token_url):
            raise ValueError("Invalid token_url")

        if self.redirect_uri and not self._is_valid_url(self.redirect_uri):
            raise ValueError("Invalid redirect_uri")

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "OAuth2Config":
        """Create OAuth2Config from dictionary."""
        return cls(
            client_id=config_dict.get("client_id", ""),
            client_secret=config_dict.get("client_secret"),
            authorization_url=config_dict.get("authorization_url"),
            token_url=config_dict.get("token_url", ""),
            scope=config_dict.get("scope"),
            redirect_uri=config_dict.get("redirect_uri"),
            audience=config_dict.get("audience"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert OAuth2Config to dictionary."""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "authorization_url": self.authorization_url,
            "token_url": self.token_url,
            "scope": self.scope,
            "redirect_uri": self.redirect_uri,
            "audience": self.audience,
        }


@dataclass
class OAuth2Token:
    """OAuth 2.0 token with expiration and refresh capabilities."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    expires_at: datetime = field(init=False)

    def __post_init__(self):
        """Calculate expiration time after initialization."""
        if self.expires_in:
            self.expires_at = datetime.now() + timedelta(seconds=self.expires_in)
        else:
            # Default to 1 hour if no expiration provided
            self.expires_at = datetime.now() + timedelta(hours=1)

    def is_expired(self, buffer_seconds: int = 0) -> bool:
        """
        Check if token is expired.

        Args:
            buffer_seconds: Add buffer time to consider token expired earlier

        Returns:
            True if token is expired or will expire within buffer_seconds
        """
        return datetime.now() + timedelta(seconds=buffer_seconds) >= self.expires_at

    def needs_refresh(self, threshold_minutes: int = 5) -> bool:
        """
        Check if token needs refresh.

        Args:
            threshold_minutes: Minutes before expiration to trigger refresh

        Returns:
            True if token should be refreshed
        """
        return self.refresh_token is not None and self.is_expired(
            buffer_seconds=threshold_minutes * 60
        )

    def to_authorization_header(self) -> str:
        """Create authorization header value."""
        return f"{self.token_type} {self.access_token}"

    @classmethod
    def from_response(cls, response_data: dict[str, Any]) -> "OAuth2Token":
        """Create OAuth2Token from token response."""
        return cls(
            access_token=response_data["access_token"],
            token_type=response_data.get("token_type", "Bearer"),
            expires_in=response_data.get("expires_in"),
            refresh_token=response_data.get("refresh_token"),
            scope=response_data.get("scope"),
        )


class OAuth2Authenticator:
    """
    OAuth 2.0 authenticator for MCP server authentication.

    Supports multiple OAuth 2.0 flows and handles token lifecycle management.
    """

    def __init__(self, config: OAuth2Config):
        """
        Initialize OAuth 2.0 authenticator.

        Args:
            config: OAuth 2.0 configuration
        """
        self.config = config
        self.current_token: OAuth2Token | None = None
        self._session: aiohttp.ClientSession | None = None
        self._states: dict[str, datetime] = {}  # For state validation
        self._code_verifiers: dict[str, str] = {}  # For PKCE

        logger.info(
            f"OAuth 2.0 authenticator initialized for client: {config.client_id}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    def generate_authorization_url(
        self, state: str | None = None, use_pkce: bool = True
    ) -> str:
        """
        Generate OAuth 2.0 authorization URL.

        Args:
            state: State parameter for security (generated if not provided)
            use_pkce: Whether to use PKCE for additional security

        Returns:
            Authorization URL
        """
        if not self.config.authorization_url:
            raise ValueError(
                "authorization_url is required for authorization code flow"
            )

        # Generate state if not provided
        if state is None:
            state = self._generate_state()

        # Store state for validation
        self._states[state] = datetime.now()

        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "state": state,
        }

        if self.config.scope:
            params["scope"] = self.config.scope

        if self.config.redirect_uri:
            params["redirect_uri"] = self.config.redirect_uri

        if self.config.audience:
            params["audience"] = self.config.audience

        # Add PKCE parameters if enabled
        if use_pkce:
            code_verifier, code_challenge = self.generate_pkce_challenge()
            self._code_verifiers[state] = code_verifier
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        # Build URL
        query_string = urllib.parse.urlencode(params)
        return f"{self.config.authorization_url}?{query_string}"

    def _generate_state(self) -> str:
        """Generate secure state parameter."""
        return secrets.token_urlsafe(32)

    def validate_state(self, state: str, max_age_minutes: int = 10) -> bool:
        """
        Validate state parameter.

        Args:
            state: State parameter to validate
            max_age_minutes: Maximum age of state in minutes

        Returns:
            True if state is valid
        """
        if state not in self._states:
            return False

        # Check age
        state_time = self._states[state]
        if datetime.now() - state_time > timedelta(minutes=max_age_minutes):
            del self._states[state]
            return False

        return True

    def generate_pkce_challenge(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = (
            base64.urlsafe_b64encode(secrets.token_bytes(32))
            .decode("utf-8")
            .rstrip("=")
        )

        # Generate code challenge
        challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = (
            base64.urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")
        )

        return code_verifier, code_challenge

    async def exchange_code_for_token(
        self, authorization_code: str, state: str
    ) -> OAuth2Token:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from OAuth provider
            state: State parameter for validation

        Returns:
            OAuth 2.0 token

        Raises:
            OAuth2AuthenticationError: If authentication fails
        """
        # Validate state
        if not self.validate_state(state):
            raise OAuth2AuthenticationError("Invalid or expired state parameter")

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": self.config.client_id,
        }

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        if self.config.redirect_uri:
            data["redirect_uri"] = self.config.redirect_uri

        # Add PKCE code verifier if used
        if state in self._code_verifiers:
            data["code_verifier"] = self._code_verifiers[state]
            del self._code_verifiers[state]

        # Clean up state
        del self._states[state]

        token = await self._request_token(data)
        self.current_token = token
        return token

    async def client_credentials_flow(self) -> OAuth2Token:
        """
        Perform OAuth 2.0 client credentials flow.

        Returns:
            OAuth 2.0 token

        Raises:
            OAuth2AuthenticationError: If authentication fails
        """
        if not self.config.client_secret:
            raise ValueError("client_secret is required for client credentials flow")

        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if self.config.scope:
            data["scope"] = self.config.scope

        if self.config.audience:
            data["audience"] = self.config.audience

        token = await self._request_token(data)
        self.current_token = token
        return token

    async def refresh_token(self) -> OAuth2Token:
        """
        Refresh current access token.

        Returns:
            New OAuth 2.0 token

        Raises:
            OAuth2AuthenticationError: If refresh fails
        """
        if not self.current_token or not self.current_token.refresh_token:
            raise OAuth2AuthenticationError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.current_token.refresh_token,
            "client_id": self.config.client_id,
        }

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        if self.config.scope:
            data["scope"] = self.config.scope

        token = await self._request_token(data)
        self.current_token = token
        return token

    async def _request_token(self, data: dict[str, str]) -> OAuth2Token:
        """
        Make token request to OAuth provider.

        Args:
            data: Request data

        Returns:
            OAuth 2.0 token

        Raises:
            OAuth2AuthenticationError: If request fails
        """
        if not self._session:
            self._session = aiohttp.ClientSession()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        try:
            async with self._session.post(
                self.config.token_url,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response_data = await response.json()

                if response.status != 200:
                    error_msg = response_data.get(
                        "error_description",
                        response_data.get("error", f"HTTP {response.status}"),
                    )
                    raise OAuth2AuthenticationError(
                        f"Token request failed: {error_msg}"
                    )

                return OAuth2Token.from_response(response_data)

        except OAuth2AuthenticationError:
            # Re-raise OAuth2AuthenticationError as-is
            raise
        except asyncio.TimeoutError as e:
            raise OAuth2Error(f"Token request timeout: {e}")
        except aiohttp.ClientError as e:
            raise OAuth2Error(f"Network error during token request: {e}")
        except Exception as e:
            raise OAuth2Error(f"Unexpected error during token request: {e}")

    async def get_authorization_header(self) -> str:
        """
        Get authorization header, refreshing token if needed.

        Returns:
            Authorization header value

        Raises:
            OAuth2TokenExpiredError: If token is expired and cannot be refreshed
        """
        if not self.current_token:
            raise OAuth2TokenExpiredError("No access token available")

        # Check if token needs refresh
        if self.current_token.needs_refresh():
            logger.info("Token needs refresh, attempting to refresh")
            try:
                await self.refresh_token()
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                raise OAuth2TokenExpiredError("Token expired and refresh failed")

        # Check if token is expired
        if self.current_token.is_expired():
            raise OAuth2TokenExpiredError("Access token has expired")

        return self.current_token.to_authorization_header()

    def store_token(self, token: OAuth2Token) -> None:
        """
        Store OAuth 2.0 token.

        Args:
            token: Token to store
        """
        self.current_token = token
        logger.info("OAuth 2.0 token stored successfully")

    def get_current_token(self) -> OAuth2Token | None:
        """
        Get current OAuth 2.0 token.

        Returns:
            Current token or None if not authenticated
        """
        return self.current_token

    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated with valid token.

        Returns:
            True if authenticated with non-expired token
        """
        return self.current_token is not None and not self.current_token.is_expired()

    async def revoke_token(self, token: str | None = None) -> bool:
        """
        Revoke OAuth 2.0 token.

        Args:
            token: Token to revoke (uses current access token if not provided)

        Returns:
            True if revocation successful
        """
        if not token and self.current_token:
            token = self.current_token.access_token

        if not token:
            return False

        # Note: Not all OAuth providers support token revocation
        # This is a best-effort implementation
        revoke_url = self.config.token_url.replace("/token", "/revoke")

        if not self._session:
            self._session = aiohttp.ClientSession()

        data = {"token": token, "client_id": self.config.client_id}

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        try:
            async with self._session.post(revoke_url, data=data) as response:
                success = response.status in [200, 204]
                if success:
                    self.current_token = None
                    logger.info("Token revoked successfully")
                return success
        except Exception as e:
            logger.warning(f"Token revocation failed: {e}")
            return False

    def clear_authentication(self) -> None:
        """Clear current authentication state."""
        self.current_token = None
        self._states.clear()
        self._code_verifiers.clear()
        logger.info("Authentication state cleared")

    def get_token_info(self) -> dict[str, Any] | None:
        """
        Get information about current token.

        Returns:
            Token information dictionary or None if not authenticated
        """
        if not self.current_token:
            return None

        return {
            "token_type": self.current_token.token_type,
            "scope": self.current_token.scope,
            "expires_at": self.current_token.expires_at.isoformat(),
            "is_expired": self.current_token.is_expired(),
            "needs_refresh": self.current_token.needs_refresh(),
            "has_refresh_token": self.current_token.refresh_token is not None,
        }
