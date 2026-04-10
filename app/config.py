"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file and provides type-safe access.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Settings
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    log_level: str = Field(default="INFO", description="Logging level")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # WorkZappy Configuration
    workzappy_target_column: str = Field(..., description="Column/status to filter tickets (e.g., 'Done Tickets')")
    workzappy_webhook_secret: str | None = Field(default=None, description="Optional webhook signature secret")

    # Microsoft Graph API Configuration
    microsoft_tenant_id: str = Field(..., description="Azure AD tenant ID")
    microsoft_client_id: str = Field(..., description="Azure AD application (client) ID")
    microsoft_client_secret: str = Field(..., description="Azure AD client secret")

    # SharePoint Configuration
    sharepoint_site_id: str = Field(..., description="SharePoint site ID")
    sharepoint_file_id: str = Field(..., description="Excel file ID in SharePoint")

    # Excel Configuration
    excel_ticket_id_column: str = Field(default="D", description="Column letter for ticket ID (hidden)")
    excel_ticket_id_hidden: bool = Field(default=True, description="Whether to hide the ticket ID column")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def graph_authority(self) -> str:
        """Get the Microsoft Graph authority URL."""
        return f"https://login.microsoftonline.com/{self.microsoft_tenant_id}"

    @property
    def graph_scopes(self) -> list[str]:
        """Get the required Microsoft Graph API scopes."""
        return ["https://graph.microsoft.com/.default"]


# Global settings instance
settings = Settings()
