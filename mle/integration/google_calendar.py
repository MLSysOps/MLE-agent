import json
import datetime
from mle.utils import load_file
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def google_calendar_login(credential=None):
    """
    Authenticate the user using Google OAuth 2.0 and return the credentials.

    :param credential: The client secrets.
    :return: Google OAuth 2.0 credentials or None if authentication fails.
    """

    if credential is None:
        # FIXME: remove the test app_credential
        credential = json.loads(load_file(
            "https://raw.githubusercontent.com/leeeizhang/leeeizhang/assets/google_app",
            base64_decode=True,
        ))

    try:
        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        flow = InstalledAppFlow.from_client_config(
            credential,
            SCOPES,
        )
        creds = flow.run_local_server(host="127.0.0.1", port=0)
    except Exception:
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

    def get_events(self, start_date=None, end_date=None, limit=100, detailed=True):
        """
        Fetch upcoming calendar events.
        :param start_date: Start date for calendar events (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for calendar events (inclusive), in 'YYYY-MM-DD' format
        :param limit: The maximum number of events to return.
        :param detailed: Whether to return detailed event information.
        :return: A list of events with details or None if an error occurs.
        """
        try:
            # Set default dates if not provided
            today = datetime.date.today()
            if start_date is None:
                start_date = (today - datetime.timedelta(days=7)).isoformat()
            if end_date is None:
                end_date = (today + datetime.timedelta(days=7)).isoformat()

            # Convert dates to datetime objects with time
            start_dt = datetime.datetime.strptime(f"{start_date}T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
            end_dt = datetime.datetime.strptime(f"{end_date}T23:59:59Z", "%Y-%m-%dT%H:%M:%S%z")

            if start_dt >= end_dt:
                raise ValueError("start_date must be less than end_date")

            # Convert back to string format for API call
            start_date = start_dt.isoformat()
            end_date = end_dt.isoformat()

            # Build the service object for interacting with the Google Calendar API
            service = build("calendar", "v3", credentials=self.token)

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
            events = []
            for event in events_result:
                e = {
                    "title": event.get("summary"),
                    "status": event.get("status"),
                    "description": event.get("description"),
                    "creator": event.get("creator"),
                    "organizer": event.get("organizer"),
                    "start_time": event["start"].get("dateTime", event["start"].get("date")),
                    "end_time": event["end"].get("dateTime", event["end"].get("date"))
                }

                if detailed:
                    e.update(
                        {
                            "htmlLink": event.get("htmlLink"),
                            "kind": event.get("kind"),
                        }
                    )

                events.append(e)
            return events

        except Exception as e:
            print(f"An error occurred: {e}")
            return None
