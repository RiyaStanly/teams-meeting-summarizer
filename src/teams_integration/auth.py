"""Microsoft Teams OAuth2 authentication manager."""

from typing import Optional

try:
    from msal import ConfidentialClientApplication, PublicClientApplication
except ImportError:
    ConfidentialClientApplication = None
    PublicClientApplication = None

from src.config import settings
from src.utils.logger import logger


class TeamsAuthManager:
    """OAuth2 authentication for Microsoft Graph API."""

    # Microsoft Graph API scopes
    SCOPES = [
        "https://graph.microsoft.com/OnlineMeetings.ReadWrite",
        "https://graph.microsoft.com/Calendars.Read",
        "https://graph.microsoft.com/User.Read",
    ]

    def __init__(self, use_device_code: bool = True):
        """
        Initialize Teams authentication manager.

        Args:
            use_device_code: Use device code flow (True) or client credentials (False)
        """
        if ConfidentialClientApplication is None or PublicClientApplication is None:
            raise ImportError(
                "MSAL not installed. Install with: pip install msal"
            )

        if not settings.teams_client_id:
            raise ValueError(
                "Teams client ID not configured. "
                "Set TEAMS_CLIENT_ID in environment or .env file"
            )

        self.use_device_code = use_device_code

        if use_device_code:
            # Public client for device code flow (user authentication)
            self.app = PublicClientApplication(
                client_id=settings.teams_client_id,
                authority=f"https://login.microsoftonline.com/{settings.teams_tenant_id}",
            )
        else:
            # Confidential client for client credentials flow (app-only)
            if not settings.teams_client_secret:
                raise ValueError("Teams client secret required for client credentials flow")

            self.app = ConfidentialClientApplication(
                client_id=settings.teams_client_id,
                client_credential=settings.teams_client_secret,
                authority=f"https://login.microsoftonline.com/{settings.teams_tenant_id}",
            )

        self.access_token: Optional[str] = None
        logger.info(f"Teams auth manager initialized (device_code={use_device_code})")

    def authenticate(self) -> str:
        """
        Authenticate and get access token.

        Returns:
            Access token string

        Raises:
            RuntimeError: If authentication fails
        """
        if self.use_device_code:
            return self._authenticate_device_code()
        else:
            return self._authenticate_client_credentials()

    def _authenticate_device_code(self) -> str:
        """Authenticate using device code flow (interactive)."""
        logger.info("Starting device code authentication...")

        # Initiate device code flow
        flow = self.app.initiate_device_flow(scopes=self.SCOPES)

        if "user_code" not in flow:
            raise RuntimeError(
                f"Failed to create device flow: {flow.get('error_description')}"
            )

        # Display authentication instructions
        print("\n" + "=" * 60)
        print("MICROSOFT TEAMS AUTHENTICATION")
        print("=" * 60)
        print(f"\n{flow['message']}\n")
        print("=" * 60 + "\n")

        # Wait for user to authenticate
        result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            self.access_token = result["access_token"]
            logger.info("✓ Authentication successful!")
            return self.access_token
        else:
            error = result.get("error_description", "Unknown error")
            raise RuntimeError(f"Authentication failed: {error}")

    def _authenticate_client_credentials(self) -> str:
        """Authenticate using client credentials flow (app-only)."""
        logger.info("Authenticating with client credentials...")

        result = self.app.acquire_token_for_client(scopes=self.SCOPES)

        if "access_token" in result:
            self.access_token = result["access_token"]
            logger.info("✓ Authentication successful!")
            return self.access_token
        else:
            error = result.get("error_description", "Unknown error")
            raise RuntimeError(f"Authentication failed: {error}")

    def get_access_token(self) -> str:
        """
        Get current access token, refreshing if needed.

        Returns:
            Valid access token
        """
        if not self.access_token:
            return self.authenticate()

        # TODO: Implement token refresh logic
        # For now, just return existing token
        return self.access_token

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self.access_token is not None
