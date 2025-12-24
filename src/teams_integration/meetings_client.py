"""Microsoft Graph API client for Teams meetings."""

from datetime import datetime
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from src.teams_integration.auth import TeamsAuthManager
from src.utils.logger import logger


class TeamsMeetingsClient:
    """Client for interacting with Microsoft Teams meetings via Graph API."""

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, auth_manager: TeamsAuthManager):
        """
        Initialize Teams meetings client.

        Args:
            auth_manager: Authenticated TeamAuth Manager instance
        """
        if requests is None:
            raise ImportError("requests not installed. Install with: pip install requests")

        self.auth_manager = auth_manager
        logger.info("Teams meetings client initialized")

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authorization token."""
        token = self.auth_manager.get_access_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def list_user_meetings(self, limit: int = 10) -> List[Dict]:
        """
        List user's upcoming meetings.

        Args:
            limit: Maximum number of meetings to return

        Returns:
            List of meeting dictionaries
        """
        logger.info(f"Fetching user meetings (limit={limit})...")

        url = f"{self.GRAPH_API_BASE}/me/onlineMeetings"
        params = {"$top": limit}

        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        meetings = data.get("value", [])

        logger.info(f"Found {len(meetings)} meetings")
        return meetings

    def get_meeting_details(self, meeting_id: str) -> Dict:
        """
        Get details for a specific meeting.

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting details dictionary
        """
        logger.info(f"Fetching meeting details: {meeting_id}")

        url = f"{self.GRAPH_API_BASE}/me/onlineMeetings/{meeting_id}"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        return response.json()

    def list_calendar_events(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        List calendar events with Teams meetings.

        Args:
            start_date: Start date for events (defaults to now)
            end_date: End date for events (defaults to 7 days from now)

        Returns:
            List of calendar events
        """
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            from datetime import timedelta

            end_date = start_date + timedelta(days=7)

        logger.info(f"Fetching calendar events from {start_date} to {end_date}")

        url = f"{self.GRAPH_API_BASE}/me/calendar/events"
        params = {
            "$filter": f"start/dateTime ge '{start_date.isoformat()}' and end/dateTime le '{end_date.isoformat()}'",
            "$select": "subject,start,end,onlineMeeting,organizer,attendees",
        }

        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        events = data.get("value", [])

        # Filter to only events with online meetings
        teams_events = [e for e in events if e.get("onlineMeeting")]

        logger.info(f"Found {len(teams_events)} Teams meetings")
        return teams_events

    def get_meeting_participants(self, meeting_id: str) -> List[Dict]:
        """
        Get participants for a meeting.

        Args:
            meeting_id: Meeting ID

        Returns:
            List of participant dictionaries
        """
        logger.info(f"Fetching participants for meeting: {meeting_id}")

        url = f"{self.GRAPH_API_BASE}/me/onlineMeetings/{meeting_id}/attendanceReports"

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 404:
            logger.warning("Attendance reports not available for this meeting")
            return []

        response.raise_for_status()

        data = response.json()
        reports = data.get("value", [])

        if not reports:
            return []

        # Get latest report
        report_id = reports[0]["id"]
        attendance_url = f"{url}/{report_id}/attendanceRecords"

        response = requests.get(attendance_url, headers=self._get_headers())
        response.raise_for_status()

        data = response.json()
        participants = data.get("value", [])

        logger.info(f"Found {len(participants)} participants")
        return participants
