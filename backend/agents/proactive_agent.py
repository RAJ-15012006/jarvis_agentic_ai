"""
proactive_agent.py — JARVIS Proactive Suggestions Engine
=========================================================
Makes JARVIS speak FIRST without Raj asking.
Runs background threads that monitor time, activity, and data sources.

Proactive behaviors:
  1. Morning Briefing (8:00 AM IST) — weather + calendar + news
  2. Coding Time Tracker — warns after 2h of activity
  3. GitHub Issue Watcher — alerts when new issues appear
  4. Smart Break Suggestions — every 90 mins of usage
  5. Evening Summary (9:00 PM) — what was accomplished

Uses Python's 'schedule' library for time-based triggers.
"""

import os
import threading
import datetime
import time
import json

# Track session start time for coding time tracking
_session_start: datetime.datetime = None
_last_break_suggestion: datetime.datetime = None
_proactive_callbacks: list = []  # List of (message_text, callback_fn) tuples
_known_github_issues: set = set()

# State file shared with main.py
PROACTIVE_STATE_FILE = os.path.join(
    os.path.dirname(__file__), "face_data", "proactive_state.json"
)
os.makedirs(os.path.dirname(PROACTIVE_STATE_FILE), exist_ok=True)


def _get_ist_now() -> datetime.datetime:
    """Return current IST time."""
    return datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)


def _save_proactive_message(message: str, msg_type: str = "info"):
    """Save a proactive message to the state file for frontend polling."""
    try:
        state = {
            "message": message,
            "type": msg_type,
            "timestamp": _get_ist_now().strftime("%H:%M:%S"),
            "pending": True,
        }
        with open(PROACTIVE_STATE_FILE, "w") as f:
            json.dump(state, f)
        print(f"[PROACTIVE] Queued: {message[:60]}")
    except Exception as e:
        print(f"[PROACTIVE] Save failed: {e}")


def get_pending_proactive_message() -> dict:
    """Retrieve and clear the pending proactive message."""
    try:
        if not os.path.exists(PROACTIVE_STATE_FILE):
            return None
        with open(PROACTIVE_STATE_FILE) as f:
            state = json.load(f)
        if state.get("pending"):
            # Clear it
            state["pending"] = False
            with open(PROACTIVE_STATE_FILE, "w") as f:
                json.dump(state, f)
            return state
    except Exception:
        pass
    return None


def _build_morning_briefing() -> str:
    """Build the morning briefing message."""
    now = _get_ist_now()
    lines = [f"🌅 Good morning, Sir! It's {now.strftime('%A, %d %B %Y')} — {now.strftime('%I:%M %p')} IST.\n"]

    # Weather snippet
    try:
        weather_key = os.getenv("OPENWEATHER_API_KEY", "")
        if weather_key:
            import requests
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": "Vadodara", "appid": weather_key, "units": "metric"},
                timeout=5
            )
            w = resp.json()
            temp = w["main"]["temp"]
            desc = w["weather"][0]["description"]
            lines.append(f"🌤️ Weather: {desc.capitalize()}, {temp:.0f}°C in Vadodara.")
    except Exception:
        pass

    # Calendar events today
    try:
        from agents.calendar_agent import get_today_events
        events = get_today_events()
        if "nothing scheduled" not in events.lower():
            lines.append(f"\n{events}")
    except Exception:
        pass

    # News snippet
    try:
        news_key = os.getenv("NEWS_API_KEY", "")
        if news_key:
            import requests
            resp = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "in", "pageSize": 3, "apiKey": news_key},
                timeout=5
            )
            articles = resp.json().get("articles", [])
            if articles:
                lines.append("\n📰 Top Headlines:")
                for a in articles[:3]:
                    lines.append(f"  • {a['title']}")
    except Exception:
        pass

    lines.append("\nI'm standing by for your commands, Sir.")
    return "\n".join(lines)


def _check_github_new_issues():
    """Check for new GitHub issues silently in background."""
    global _known_github_issues
    try:
        import requests
        username = "RAJ-15012006"
        token = os.getenv("GITHUB_TOKEN", "")
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        resp = requests.get(
            f"https://api.github.com/users/{username}/repos?per_page=50",
            headers=headers, timeout=8
        )
        repos = resp.json()
        if not isinstance(repos, list):
            return

        current_issues = set()
        for repo in repos:
            if repo.get("open_issues_count", 0) > 0:
                r2 = requests.get(
                    f"https://api.github.com/repos/{username}/{repo['name']}/issues?state=open&per_page=3",
                    headers=headers, timeout=5
                )
                issues = r2.json()
                if isinstance(issues, list):
                    for issue in issues:
                        issue_id = f"{repo['name']}#{issue['number']}"
                        current_issues.add(issue_id)

        new_issues = current_issues - _known_github_issues
        if new_issues and _known_github_issues:  # Only alert after first scan
            msg = f"⚠️ New GitHub issue(s) detected, Sir:\n" + "\n".join(f"• {i}" for i in new_issues)
            _save_proactive_message(msg, "github_alert")

        _known_github_issues = current_issues
    except Exception:
        pass


def _check_break_time():
    """Suggest a break if Raj has been active for 90+ minutes."""
    global _last_break_suggestion, _session_start
    if not _session_start:
        return

    now = datetime.datetime.utcnow()
    active_minutes = (now - _session_start).total_seconds() / 60

    if active_minutes >= 90:
        if not _last_break_suggestion or (now - _last_break_suggestion).total_seconds() > 5400:
            hours = int(active_minutes // 60)
            mins = int(active_minutes % 60)
            msg = (
                f"💡 Sir, you've been active for {hours}h {mins}m. "
                f"Consider a 5-10 minute break — your productivity will thank you!"
            )
            _save_proactive_message(msg, "break_suggestion")
            _last_break_suggestion = now


def _evening_summary():
    """Evening summary at 9 PM IST."""
    now = _get_ist_now()
    msg = (
        f"🌙 Good evening, Sir. It's {now.strftime('%I:%M %p')}. "
        f"JARVIS has been running for {_get_session_uptime()}. "
        f"How can I assist you as you wind down?"
    )
    _save_proactive_message(msg, "evening_summary")


def _get_session_uptime() -> str:
    """Return formatted uptime string."""
    if not _session_start:
        return "some time"
    elapsed = datetime.datetime.utcnow() - _session_start
    h = int(elapsed.total_seconds() // 3600)
    m = int((elapsed.total_seconds() % 3600) // 60)
    return f"{h}h {m}m"


def start_session():
    """Call this when JARVIS connects to start session tracking."""
    global _session_start
    _session_start = datetime.datetime.utcnow()
    print(f"[PROACTIVE] Session started at {_session_start}")


def run_proactive_scheduler():
    """
    Background thread — runs proactive checks on a schedule.
    Call start_proactive_engine() to launch this in background.
    """
    try:
        import schedule
    except ImportError:
        print("[PROACTIVE] 'schedule' library not installed. Run: pip install schedule")
        return

    # Morning briefing at 8:00 AM IST
    schedule.every().day.at("02:30").do(
        lambda: _save_proactive_message(_build_morning_briefing(), "morning_briefing")
    )  # 08:00 IST = 02:30 UTC

    # Evening summary at 9:00 PM IST
    schedule.every().day.at("15:30").do(_evening_summary)  # 21:00 IST = 15:30 UTC

    # GitHub issue check every 30 minutes
    schedule.every(30).minutes.do(_check_github_new_issues)

    # Break time check every 15 minutes
    schedule.every(15).minutes.do(_check_break_time)

    print("[PROACTIVE] Scheduler running...")
    while True:
        schedule.run_pending()
        time.sleep(60)


_scheduler_thread: threading.Thread = None

def start_proactive_engine():
    """Launch the proactive scheduler in a daemon background thread."""
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return  # Already running

    start_session()
    _scheduler_thread = threading.Thread(
        target=run_proactive_scheduler,
        daemon=True,
        name="JARVIS-Proactive-Engine"
    )
    _scheduler_thread.start()
    print("[PROACTIVE] Engine started in background thread.")


def trigger_morning_briefing() -> str:
    """Manually trigger morning briefing (for testing or voice command)."""
    return _build_morning_briefing()


def is_briefing_command(command: str) -> bool:
    triggers = [
        "morning briefing", "daily briefing", "what's happening today",
        "brief me", "daily update", "good morning jarvis", "morning report",
        "today's summary", "what's new today",
    ]
    cmd = command.lower()
    return any(t in cmd for t in triggers)
