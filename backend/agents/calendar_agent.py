"""
calendar_agent.py — JARVIS Google Calendar Voice Control
==========================================================
Allows Raj to read, create, and delete calendar events by voice.
Also provides proactive reminders for upcoming events.

SETUP REQUIRED (same OAuth as Gmail):
  - Place 'calendar_credentials.json' in backend/agents/face_data/
  - (Can reuse the same credentials.json from Gmail setup)

Voice commands:
  - "what do I have today / tomorrow"
  - "what's on my calendar"
  - "schedule a meeting with [person] at [time]"
  - "add event [title] on [date] at [time]"
  - "delete event [title]"
  - "upcoming events"
  - "remind me about [event] at [time]"
"""

import os
import json
import re
import datetime

CREDS_DIR = os.path.join(os.path.dirname(__file__), "face_data")
CREDENTIALS_FILE = os.path.join(CREDS_DIR, "gmail_credentials.json")  # Reuse same OAuth app
TOKEN_FILE = os.path.join(CREDS_DIR, "calendar_token.json")

CALENDAR_TRIGGERS = [
    "what do i have today", "what do i have tomorrow", "what's on my calendar",
    "whats on my calendar", "my schedule", "upcoming events", "calendar",
    "schedule a meeting", "add event", "create event", "book a meeting",
    "what's my schedule", "what meetings", "remind me", "event today",
    "events tomorrow", "my meetings", "schedule for today", "schedule for tomorrow",
]

def is_calendar_command(command: str) -> bool:
    cmd = command.lower()
    return any(t in cmd for t in CALENDAR_TRIGGERS)


def _get_calendar_service():
    """Authenticate and return Google Calendar API service."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    return None, (
                        "Sir, Google Calendar credentials not found. "
                        "Please place your google_credentials.json file in "
                        "backend/agents/face_data/ and restart JARVIS."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        service = build("calendar", "v3", credentials=creds)
        return service, None

    except ImportError:
        return None, (
            "Sir, Google API libraries not installed. "
            "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
        )
    except Exception as e:
        return None, f"Calendar auth failed: {str(e)}"


def _fmt_event(event: dict) -> str:
    """Format a calendar event as a human-readable string."""
    summary = event.get("summary", "Untitled Event")
    start = event.get("start", {})
    start_dt = start.get("dateTime", start.get("date", ""))

    try:
        if "T" in start_dt:
            dt = datetime.datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
            # Convert to IST
            ist = dt + datetime.timedelta(hours=5, minutes=30)
            time_str = ist.strftime("%I:%M %p")
            date_str = ist.strftime("%A, %d %b")
        else:
            dt = datetime.datetime.strptime(start_dt, "%Y-%m-%d")
            time_str = "All day"
            date_str = dt.strftime("%A, %d %b")
    except Exception:
        time_str = start_dt
        date_str = ""

    location = event.get("location", "")
    desc = event.get("description", "")
    loc_str = f" @ {location}" if location else ""
    return f"• {summary}{loc_str} — {date_str} at {time_str}"


def get_upcoming_events(days: int = 7, max_results: int = 10) -> str:
    """Fetch upcoming events for the next N days."""
    service, error = _get_calendar_service()
    if error:
        return error

    try:
        now = datetime.datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + datetime.timedelta(days=days)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return f"Your calendar is clear for the next {days} days, Sir."

        lines = [f"📅 Upcoming {len(events)} event(s) in the next {days} days:\n"]
        for ev in events:
            lines.append(_fmt_event(ev))

        return "\n".join(lines)
    except Exception as e:
        return f"Raj, couldn't fetch calendar: {str(e)}"


def get_today_events() -> str:
    """Get all events for today."""
    service, error = _get_calendar_service()
    if error:
        return error

    try:
        now_ist = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
        today_start = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + datetime.timedelta(days=1)

        # Convert back to UTC for API
        utc_start = (today_start - datetime.timedelta(hours=5, minutes=30)).isoformat() + "Z"
        utc_end = (today_end - datetime.timedelta(hours=5, minutes=30)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=utc_start,
            timeMax=utc_end,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return "You have nothing scheduled today, Sir. The calendar is clear."

        lines = [f"📅 Today's schedule — {now_ist.strftime('%A, %d %B')}:\n"]
        for ev in events:
            lines.append(_fmt_event(ev))
        return "\n".join(lines)
    except Exception as e:
        return f"Couldn't get today's events: {str(e)}"


def get_tomorrow_events() -> str:
    """Get all events for tomorrow."""
    service, error = _get_calendar_service()
    if error:
        return error

    try:
        now_utc = datetime.datetime.utcnow()
        tomorrow_utc = now_utc + datetime.timedelta(days=1)
        start = tomorrow_utc.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = tomorrow_utc.replace(hour=23, minute=59, second=59).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary", timeMin=start, timeMax=end,
            singleEvents=True, orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        tomorrow_ist = now_utc + datetime.timedelta(days=1, hours=5, minutes=30)
        if not events:
            return f"Nothing scheduled for tomorrow ({tomorrow_ist.strftime('%A, %d %B')}), Sir."

        lines = [f"📅 Tomorrow — {tomorrow_ist.strftime('%A, %d %B')}:\n"]
        for ev in events:
            lines.append(_fmt_event(ev))
        return "\n".join(lines)
    except Exception as e:
        return f"Couldn't get tomorrow's events: {str(e)}"


def create_event(title: str, start_time: str, duration_minutes: int = 60,
                  description: str = "", location: str = "") -> str:
    """Create a new calendar event."""
    service, error = _get_calendar_service()
    if error:
        return error

    try:
        # Parse the time string (expect ISO format or natural language via LLM)
        try:
            start_dt = datetime.datetime.fromisoformat(start_time)
        except ValueError:
            # Fallback: try common formats
            for fmt in ["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%d %B %Y %I:%M %p"]:
                try:
                    start_dt = datetime.datetime.strptime(start_time, fmt)
                    break
                except ValueError:
                    continue
            else:
                return f"Raj, I couldn't parse the time '{start_time}'. Please use format: 'YYYY-MM-DD HH:MM'"

        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

        # Convert IST to UTC for storage
        start_utc = (start_dt - datetime.timedelta(hours=5, minutes=30)).isoformat() + "Z"
        end_utc = (end_dt - datetime.timedelta(hours=5, minutes=30)).isoformat() + "Z"

        event_body = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start_utc, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_utc, "timeZone": "Asia/Kolkata"},
        }

        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return (
            f"✅ Event '{title}' created for "
            f"{start_dt.strftime('%A, %d %B at %I:%M %p')}, Sir."
        )
    except Exception as e:
        return f"Raj, event creation failed: {str(e)}"


def _parse_create_command(command: str) -> dict:
    """Use LLaMA to extract event details from voice command."""
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return {}

        now = datetime.datetime.now()
        client = Groq(api_key=api_key)
        prompt = f"""Extract calendar event details from this voice command: "{command}"
Current date and time: {now.strftime("%Y-%m-%d %H:%M")} (IST)

Return ONLY valid JSON with these keys:
- "title": event title/name
- "start_time": ISO format datetime string (YYYY-MM-DD HH:MM)
- "duration_minutes": integer duration (default 60)
- "location": location string (optional, empty string if none)
- "description": description (optional, empty string if none)

Example: {{"title": "Team Meeting", "start_time": "2026-07-12 15:00", "duration_minutes": 60, "location": "", "description": ""}}"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {}


def handle_calendar_command(command: str) -> str:
    """Main dispatcher for Calendar voice commands."""
    cmd = command.lower().strip()

    if any(w in cmd for w in ["today", "schedule for today", "today's events"]):
        return get_today_events()

    if any(w in cmd for w in ["tomorrow", "schedule for tomorrow"]):
        return get_tomorrow_events()

    if any(w in cmd for w in ["this week", "next 7 days", "upcoming", "next week"]):
        return get_upcoming_events(days=7)

    if any(w in cmd for w in ["schedule", "create", "add event", "book", "set up meeting", "meeting with"]):
        details = _parse_create_command(command)
        if details and details.get("title") and details.get("start_time"):
            return create_event(
                title=details["title"],
                start_time=details["start_time"],
                duration_minutes=details.get("duration_minutes", 60),
                description=details.get("description", ""),
                location=details.get("location", ""),
            )
        return "Raj, please say: 'Schedule a meeting titled [name] at [time]'"

    # Default: show today
    return get_today_events()
