"""
Pydantic models for request/response validation and data structures.
These models will be updated once we capture the actual WorkZappy webhook payload.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class TicketData(BaseModel):
    """Structured ticket data extracted from webhook."""

    ticket_id: str = Field(..., description="Unique ticket identifier")
    ticket_title: str = Field(..., description="Ticket title/name")
    sprint_number: str = Field(..., description="Sprint number (converted to string)")
    story_points: float = Field(default=0.0, description="Story points assigned")
    assignee_full_name: str = Field(..., description="Full name of the assignee")
    column_status: str = Field(..., description="Current column/status of the ticket")

    @field_validator("sprint_number", mode="before")
    @classmethod
    def convert_sprint_to_string(cls, v: Any) -> str:
        """Convert sprint number to string if it's a number."""
        return str(v) if v is not None else ""

    @field_validator("story_points", mode="before")
    @classmethod
    def convert_story_points(cls, v: Any) -> float:
        """Convert story points to float, handling various input types."""
        if v is None or v == "":
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0


class WorkZappyWebhook(BaseModel):
    """
    WorkZappy webhook payload model.

    NOTE: This is a flexible model based on common webhook patterns.
    It will be updated once we capture the actual webhook payload from WorkZappy.
    """

    event_type: str | None = Field(default=None, description="Type of event (e.g., 'ticket.moved')")
    timestamp: datetime | None = Field(default=None, description="Event timestamp")
    ticket: dict[str, Any] = Field(..., description="Ticket data (flexible structure)")

    model_config = {
        "extra": "allow"  # Allow additional fields we haven't discovered yet
    }


class ExcelUpdateRequest(BaseModel):
    """Request model for Excel update operations."""

    sheet_name: str = Field(..., description="Name of the sheet to update")
    ticket_id: str = Field(..., description="Unique ticket identifier")
    sprint_number: str = Field(..., description="Sprint number")
    ticket_title: str = Field(..., description="Ticket title")
    story_points: float = Field(..., description="Story points assigned")


class WebhookResponse(BaseModel):
    """Standard response for webhook endpoints."""

    status: str = Field(default="accepted", description="Processing status")
    message: str | None = Field(default=None, description="Optional message")
    correlation_id: str | None = Field(default=None, description="Request correlation ID")


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""

    status: str = Field(default="healthy", description="Service health status")
    environment: str = Field(..., description="Current environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
