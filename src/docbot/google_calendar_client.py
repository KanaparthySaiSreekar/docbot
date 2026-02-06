"""Google Calendar API client with OAuth2 and Meet link generation."""

import os
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from docbot.config import get_settings
from docbot.alerts import log_alert
import logging

logger = logging.getLogger(__name__)

# OAuth2 scopes for calendar access
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _get_credentials() -> Credentials | None:
    """
    Get or refresh Google OAuth2 credentials.

    Looks for token.json in project root.
    If not found or expired, initiates OAuth flow using credentials file.

    Returns:
        Credentials object or None if authentication fails
    """
    settings = get_settings()
    creds_path = Path(settings.google_calendar.credentials_path)
    token_path = Path("token.json")

    creds = None

    # Load existing token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token.json: {e}")

    # Refresh or initiate new flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                creds = None

        if not creds:
            if not creds_path.exists():
                logger.error(f"Google Calendar credentials file not found: {creds_path}")
                return None

            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                return None

        # Save token for next run
        try:
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
        except Exception as e:
            logger.warning(f"Failed to save token.json: {e}")

    return creds


def _get_calendar_service():
    """Get authenticated Google Calendar service."""
    creds = _get_credentials()
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds)


async def create_event(
    summary: str,
    description: str,
    start_time: datetime,
    duration_minutes: int = 15,
    location: str | None = None,
    add_meet_link: bool = False,
    attendee_email: str | None = None
) -> dict | None:
    """
    Create a Google Calendar event.

    Args:
        summary: Event title
        description: Event description
        start_time: Event start time (with timezone)
        duration_minutes: Duration in minutes
        location: Physical location (for offline)
        add_meet_link: Whether to generate Google Meet link
        attendee_email: Optional attendee email

    Returns:
        dict with event_id, meet_link (if requested) on success
        None on failure
    """
    service = _get_calendar_service()
    if not service:
        log_alert("ERROR", "google_calendar_auth_failed",
                  "Google Calendar authentication failed",
                  {"summary": summary})
        return None

    settings = get_settings()
    calendar_id = settings.google_calendar.calendar_id or "primary"

    end_time = start_time + timedelta(minutes=duration_minutes)

    event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Asia/Kolkata"
        }
    }

    if location:
        event["location"] = location

    if add_meet_link:
        event["conferenceData"] = {
            "createRequest": {
                "requestId": f"docbot-{start_time.timestamp()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"}
            }
        }

    if attendee_email:
        event["attendees"] = [{"email": attendee_email}]

    try:
        created = service.events().insert(
            calendarId=calendar_id,
            body=event,
            conferenceDataVersion=1 if add_meet_link else 0,
            sendUpdates="none"  # Don't send email notifications
        ).execute()

        result = {"event_id": created["id"]}

        if add_meet_link and "conferenceData" in created:
            entry_points = created["conferenceData"].get("entryPoints", [])
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    result["meet_link"] = ep["uri"]
                    break

        logger.info(f"Calendar event created: {created['id']} - {summary}")
        return result

    except HttpError as e:
        log_alert("ERROR", "google_calendar_create_failed",
                  "Failed to create Google Calendar event",
                  {
                      "summary": summary,
                      "error": str(e)
                  })
        logger.error(f"Failed to create calendar event: {e}")
        return None


async def delete_event(event_id: str) -> bool:
    """
    Delete a Google Calendar event.

    Args:
        event_id: Google Calendar event ID

    Returns:
        bool: True if deleted successfully
    """
    service = _get_calendar_service()
    if not service:
        return False

    settings = get_settings()
    calendar_id = settings.google_calendar.calendar_id or "primary"

    try:
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates="none"
        ).execute()
        logger.info(f"Calendar event deleted: {event_id}")
        return True
    except HttpError as e:
        if e.resp.status == 404:
            logger.warning(f"Calendar event not found for deletion: {event_id}")
            return True  # Already deleted
        log_alert("ERROR", "google_calendar_delete_failed",
                  "Failed to delete Google Calendar event",
                  {
                      "event_id": event_id,
                      "error": str(e)
                  })
        return False


async def get_event(event_id: str) -> dict | None:
    """
    Get a Google Calendar event by ID.

    Args:
        event_id: Google Calendar event ID

    Returns:
        Event data dict or None if not found
    """
    service = _get_calendar_service()
    if not service:
        return None

    settings = get_settings()
    calendar_id = settings.google_calendar.calendar_id or "primary"

    try:
        return service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            return None
        logger.error(f"Failed to get calendar event {event_id}: {e}")
        return None
