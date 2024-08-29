import os
import os.path
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Path to the application's OAuth 2.0 credentials.
app_crediential = os.path.join(
    os.path.expanduser("~"), ".local/google_oauth/credentials.json"
)


def google_calendar_login(app_crediential_path=app_crediential):
    """
    Authenticate the user using Google OAuth 2.0 and return the credentials.

    :param app_crediential_path: Path to the client secrets file.
    :return: Google OAuth 2.0 credentials or None if authentication fails.
    """
    try:
        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        flow = InstalledAppFlow.from_client_secrets_file(
            app_crediential_path,
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

    def get_events(self, limit=10):
        """
        Fetch upcoming calendar events.

        :param limit: The maximum number of events to return.
        :return: A list of events with details or None if an error occurs.
        """
        try:
            # Build the service object for interacting with the Google Calendar API
            service = build("calendar", "v3", credentials=self.token)
            now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

            # Retrieve the events from the primary calendar
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
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
