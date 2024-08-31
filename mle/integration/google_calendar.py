import os
import json
import datetime
from mle.utils import load_file
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# FIXME: remove the test app_crediential
app_crediential = json.loads(load_file(
    "https://raw.githubusercontent.com/leeeizhang/leeeizhang/assets/google_app",
    base64_decode=True,
))


def google_calendar_login(app_crediential=app_crediential):
    """
    Authenticate the user using Google OAuth 2.0 and return the credentials.

    :param app_crediential: The client secrets.
    :return: Google OAuth 2.0 credentials or None if authentication fails.
    """
    try:
        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        flow = InstalledAppFlow.from_client_config(
            app_crediential,
            SCOPES,
        )
        creds = flow.run_local_server(host="127.0.0.1", port=0)
    except Exception as e:
        return None
    return creds


class GoogleCalendarIntegration:
    """
    Class to interface with Google Calendar API to fetch events.

    :param token: Google OAuth 2.0 credentials.
    """

    def __init__(self, token=None):
        self.token = token
        if self.token.expired and self.token.refresh_token:
            self.token.refresh(Request())

    def get_events(self, start_date=None, end_date=None, limit=100):
        """
        Fetch upcoming calendar events.
        :param start_date: Start date for calender events (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for calender events (inclusive), in 'YYYY-MM-DD' format
        :param limit: The maximum number of events to return.
        :return: A list of events with details or None if an error occurs.
        """
        try:
            # Build the service object for interacting with the Google Calendar API
            service = build("calendar", "v3", credentials=self.token)

            if start_date is not None:
                start_date = f"{start_date}T00:00:00Z"

            if end_date is not None:
                end_date = f"{end_date}T00:00:00Z"

                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
                end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S%z")
                if start_dt >= end_dt:
                    raise ValueError("start_date must be less than end_date")

            # Retrieve the events from the primary calendar
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_date,
                    timeMax=end_date,
                    maxResults=limit,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events_result = events_result.get("items", [])

            # Format the events into a specified structure
            return [
                {
                    "summary": event.get("summary"),
                    "kind": event.get("kind"),
                    "status": event.get("status"),
                    "description": event.get("description"),
                    "creator": event.get("creator"),
                    "organizer": event.get("organizer"),
                    "htmlLink": event.get("htmlLink"),
                    "start_time": datetime.datetime.fromisoformat(
                        event["start"].get("dateTime")
                    ),
                    "end_time": datetime.datetime.fromisoformat(
                        event["end"].get("dateTime")
                    ),
                }
                for event in events_result
            ]

        except Exception as e:
            return None


if __name__ == "__main__":
    # Example usage of the GoogleCalendarIntegration class
    # Noted: please follow the following docs to set up the credentials in `~/.local/google_oauth/credentials.json`
    # refer to: https://developers.google.com/calendar/api/quickstart/python
    token = google_calendar_login()
    calendar = GoogleCalendarIntegration(token)
    print(calendar.get_events())
