"""
Microsoft Graph API authentication service.
Handles OAuth2 token acquisition and management using MSAL.
"""

from datetime import datetime, timedelta
from typing import Optional

from msal import ConfidentialClientApplication

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class GraphAuthenticationError(Exception):
    """Raised when Graph API authentication fails."""
    pass


class GraphAuthService:
    """
    Service for managing Microsoft Graph API authentication.

    Uses OAuth2 Client Credentials flow for app-only authentication.
    Implements token caching to minimize authentication requests.
    """

    def __init__(self):
        """Initialize the Graph authentication service."""
        self._app: Optional[ConfidentialClientApplication] = None
        self._token_cache: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._initialize_app()

    def _initialize_app(self) -> None:
        """Initialize the MSAL confidential client application."""
        try:
            self._app = ConfidentialClientApplication(
                client_id=settings.microsoft_client_id,
                client_credential=settings.microsoft_client_secret,
                authority=settings.graph_authority
            )
            logger.info("Graph authentication client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Graph auth client: {e}", exc_info=True)
            raise GraphAuthenticationError(f"Failed to initialize authentication: {e}")

    async def get_access_token(self) -> str:
        """
        Get a valid access token for Microsoft Graph API.

        Returns cached token if still valid, otherwise acquires a new token.

        Returns:
            Valid access token

        Raises:
            GraphAuthenticationError: If token acquisition fails
        """
        # Check if we have a cached token that's still valid
        if self._is_token_valid():
            logger.debug("Using cached access token")
            return self._token_cache

        # Acquire new token
        logger.info("Acquiring new access token")
        return await self._acquire_token()

    def _is_token_valid(self) -> bool:
        """
        Check if the cached token is still valid.

        Returns:
            True if token exists and hasn't expired, False otherwise
        """
        if not self._token_cache or not self._token_expiry:
            return False

        # Consider token expired 5 minutes before actual expiry (safety margin)
        return datetime.utcnow() < self._token_expiry - timedelta(minutes=5)

    async def _acquire_token(self) -> str:
        """
        Acquire a new access token from Azure AD.

        Returns:
            New access token

        Raises:
            GraphAuthenticationError: If token acquisition fails
        """
        try:
            # Acquire token using client credentials flow
            result = self._app.acquire_token_for_client(scopes=settings.graph_scopes)

            if "access_token" in result:
                # Cache the token
                self._token_cache = result["access_token"]

                # Calculate expiry time (default: 3600 seconds / 60 minutes)
                expires_in = result.get("expires_in", 3600)
                self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

                logger.info(
                    "Access token acquired successfully",
                    extra={
                        "expires_in_seconds": expires_in,
                        "expiry_time": self._token_expiry.isoformat()
                    }
                )

                return self._token_cache
            else:
                # Token acquisition failed
                error = result.get("error", "unknown_error")
                error_description = result.get("error_description", "No description provided")

                logger.error(
                    "Failed to acquire access token",
                    extra={
                        "error": error,
                        "error_description": error_description
                    }
                )

                raise GraphAuthenticationError(
                    f"Token acquisition failed: {error} - {error_description}"
                )

        except GraphAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token acquisition: {e}", exc_info=True)
            raise GraphAuthenticationError(f"Unexpected authentication error: {e}")

    def clear_cache(self) -> None:
        """Clear the cached token (useful for testing or forcing re-authentication)."""
        self._token_cache = None
        self._token_expiry = None
        logger.info("Token cache cleared")


# Global instance
_graph_auth_instance: Optional[GraphAuthService] = None


def get_graph_auth_service() -> GraphAuthService:
    """
    Get or create the global GraphAuthService instance.

    Returns:
        GraphAuthService instance
    """
    global _graph_auth_instance

    if _graph_auth_instance is None:
        _graph_auth_instance = GraphAuthService()

    return _graph_auth_instance
