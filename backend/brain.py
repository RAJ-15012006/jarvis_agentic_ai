import difflib
import re
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def fallback_route(command: str) -> dict:
    cmd = command.lower()
    cmd = re.sub(r'[^\w\s]', '', cmd)
    words = cmd.split()

    automation_keywords = [
        "youtube", "instagram", "insta", "play", "whatsapp", "message", "remind", "note", "schedule",
        "linkedin", "github", "portfolio", "repo", "chatgpt", "gpt", "gemini", "claude", "close", "tab",
        "website", "site", "amazon", "netflix", "flipkart", "irctc", "zomato", "swiggy", "google",
        "vscode", "vs code", "code", "search for", "look up", "find online", "search the web",
        "close all tabs", "close every tab", "close all browser tabs",
        # Browser navigation
        "scroll", "zoom", "refresh", "reload", "new tab", "fullscreen",
    ]

    web_keywords = [
        "weather", "temperature", "forecast", "stock", "price", "nifty", "sensex", "bitcoin", "crypto",
        "score", "match", "gold", "silver", "rate", "dollar", "euro", "rupee", "forex", "news",
        "headlines", "flight", "train", "hotel", "map", "direction", "navigate", "route", "buy", "shop"
    ]

    system_keywords = [
        # Power
        "shutdown", "shut down", "restart", "reboot", "sleep", "hibernate",
        "power off", "turn off laptop",
        # Screen
        "lock", "lock screen", "screenshot", "capture screen", "take a photo",
        "dark mode", "light mode", "night mode", "toggle mode",
        "brightness", "brighter", "dimmer", "dim screen",
        # Audio
        "volume", "mute", "unmute", "louder", "quieter",
        # Battery & Storage
        "battery", "disk space", "storage", "how much space", "uptime", "system info",
        # Notifications
        "do not disturb", "dnd", "focus mode", "don't disturb",
        # Clipboard
        "clipboard", "what did i copy", "copy that",
        # Window
        "minimize", "maximise", "maximize", "close window", "close this window",
        "hide all", "show desktop", "switch app",
        # Network
        "wifi", "wi-fi", "wireless", "bluetooth",
        # Files
        "empty trash", "clear trash", "make folder", "create folder", "new folder",
        # Dev
        "notepad", "type", "folder", "script", "command", "run command",
        "python", "run", "battery", "disk",
    ]

    # New agent keywords
    screen_keywords = [
        "screen", "what's on my screen", "read my screen", "describe my screen", "debug this error",
        "analyze my screen", "what error", "look at my screen",
    ]
    emotion_keywords = [
        "how do i look", "my mood", "emotion", "how am i feeling", "am i stressed", "mood check",
    ]
    gmail_keywords = [
        "email", "inbox", "gmail", "unread", "send email", "compose email", "read my email",
    ]
    calendar_keywords = [
        "calendar", "schedule", "meeting", "event", "appointment", "what do i have",
        "today's events", "tomorrow's events",
    ]
    spotify_keywords = [
        "spotify", "play music", "pause music", "skip song", "next song", "previous song",
        "what song", "now playing", "volume up", "volume down", "shuffle", "playlist",
    ]
    translation_keywords = [
        "translate", "in hindi", "in spanish", "in french", "in japanese", "in german",
        "how do you say", "say it in", "language translation", "convert to",
    ]
    github_keywords = [
        "github stats", "my github", "github activity", "commits today", "open issues",
        "git push", "git pull", "git status", "push my changes", "git commit",
    ]
    proactive_keywords = [
        "morning briefing", "daily briefing", "brief me", "daily update", "morning report",
    ]

    # Check new agents first (multi-word phrases take priority)
    for kw in screen_keywords:
        if kw in cmd:
            return {"agent": "screen", "command": command}
    for kw in emotion_keywords:
        if kw in cmd:
            return {"agent": "emotion", "command": command}
    for kw in gmail_keywords:
        if kw in cmd:
            return {"agent": "gmail", "command": command}
    for kw in calendar_keywords:
        if kw in cmd:
            return {"agent": "calendar", "command": command}
    for kw in spotify_keywords:
        if kw in cmd:
            return {"agent": "spotify", "command": command}
    for kw in translation_keywords:
        if kw in cmd:
            return {"agent": "translation", "command": command}
    for kw in github_keywords:
        if kw in cmd:
            return {"agent": "github", "command": command}
    for kw in proactive_keywords:
        if kw in cmd:
            return {"agent": "proactive", "command": command}

    # Existing agents (multi-word phrases)
    for kw in automation_keywords:
        if len(kw.split()) > 1 and kw in cmd:
            return {"agent": "automation", "command": command}
    for kw in system_keywords:
        if len(kw.split()) > 1 and kw in cmd:
            return {"agent": "system", "command": command}
    for kw in web_keywords:
        if len(kw.split()) > 1 and kw in cmd:
            return {"agent": "web", "command": command}

    # Word-by-word fallback
    def _has_intent(target_keywords, threshold=0.8):
        for word in words:
            if word in target_keywords:
                return True
            matches = difflib.get_close_matches(word, target_keywords, n=1, cutoff=threshold)
            if matches:
                return True
        return False

    if _has_intent(automation_keywords):
        return {"agent": "automation", "command": command}
    elif _has_intent(system_keywords):
        return {"agent": "system", "command": command}
    elif _has_intent(web_keywords):
        return {"agent": "web", "command": command}
    else:
        return {"agent": "chat", "command": command}


def route_command(command: str) -> dict:
    cmd = command.lower().strip()

    # Fast-path: crew requests
    if any(w in cmd for w in ["crew", "newsletter", "tech digest", "weekly digest", "collaboration"]):
        return {"agent": "crew", "command": command}

    # Fast-path: screen reading (high priority — check before LLM)
    if any(p in cmd for p in [
        "what's on my screen", "whats on my screen", "read my screen",
        "debug this error", "analyze my screen", "describe my screen",
        "what error am i", "look at my screen"
    ]):
        return {"agent": "screen", "command": command}

    # Fast-path: emotion detection
    if any(p in cmd for p in ["how do i look", "my mood", "emotion scan", "am i stressed", "mood check"]):
        return {"agent": "emotion", "command": command}

    # Fast-path: Gmail
    if any(p in cmd for p in ["read my email", "check my email", "my inbox", "unread email",
                                "send email", "compose email", "how many emails"]):
        return {"agent": "gmail", "command": command}

    # Fast-path: Calendar
    if any(p in cmd for p in ["what do i have today", "what do i have tomorrow", "my calendar",
                                "schedule a meeting", "add event", "upcoming events", "my schedule"]):
        return {"agent": "calendar", "command": command}

    # Fast-path: Spotify
    if any(p in cmd for p in ["spotify", "play music", "pause music", "skip song", "next song",
                                "what song is playing", "now playing", "my playlist"]):
        return {"agent": "spotify", "command": command}

    # Fast-path: Translation
    if any(p in cmd for p in ["translate", "in hindi", "in spanish", "in french", "in japanese",
                                "in german", "how do you say", "say it in"]):
        return {"agent": "translation", "command": command}

    # Fast-path: GitHub
    if any(p in cmd for p in ["github stats", "my github", "git push", "git status",
                                "push my changes", "open issues", "github activity"]):
        return {"agent": "github", "command": command}

    # Fast-path: System commands (instant, no LLM needed)
    if any(p in cmd for p in [
        "volume", "mute", "unmute", "louder", "quieter",
        "brightness", "brighter", "dimmer",
        "battery", "disk space", "how much space", "uptime",
        "screenshot", "capture screen",
        "dark mode", "light mode", "night mode",
        "do not disturb", "dnd", "focus mode",
        "clipboard", "what did i copy",
        "minimize", "maximize", "maximise", "close window", "hide all",
        "wifi", "wi-fi", "bluetooth",
        "empty trash", "lock screen", "lock laptop",
        "shutdown", "shut down", "restart", "reboot",
        "sleep mode", "hibernate",
    ]):
        return {"agent": "system", "command": command}

    # Fast-path: Automation (opening profiles, PDFs, and key websites/apps)
    if "open" in cmd and any(app in cmd for app in ["linkedin", "github", "git hub", "instagram", "insta", "portfolio", "youtube", "whatsapp", "vs code", "vscode", "jarvis", "pdf", "download"]):
        return {"agent": "automation", "command": command}

    # Fast-path: Morning briefing
    if any(p in cmd for p in ["morning briefing", "daily briefing", "brief me", "morning report"]):
        return {"agent": "proactive", "command": command}

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return fallback_route(command)

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Analyze the following user command: "{command}"
        Route it to ONE of these agents:
        1. "screen": Requests to read, analyze, or describe what's on the screen, debug errors visible on screen.
        2. "emotion": Requests to detect facial emotion, mood analysis, how Raj looks.
        3. "gmail": Email-related commands — read emails, send email, check inbox, email count.
        4. "calendar": Calendar events — today's schedule, tomorrow's schedule, create events, meetings.
        5. "spotify": Music playback — play song, pause, skip, volume, playlists, what's playing.
        6. "translation": Translate text to any language.
        7. "github": GitHub stats, git push/pull/status, open issues, commit activity.
        8. "proactive": Morning briefing, daily update, brief me.
        9. "automation": Browser/website automation, WhatsApp, Instagram, YouTube, open apps, Chrome navigation (scroll, zoom, new tab, etc.).
        10. "system": OS commands — volume, brightness, restart, screenshot, notepad, file operations.
        11. "web": Real-time web data — weather, stocks, news, currency rates, cricket.
        12. "crew": Complex research, newsletter creation, tech digest.
        13. "chat": General conversation, Q&A, anything not covered above.

        Respond ONLY in JSON:
        {{"agent": "agent_name", "command": "cleaned command"}}
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        res_data = json.loads(response.choices[0].message.content)
        if "agent" in res_data and "command" in res_data:
            return res_data
        return fallback_route(command)
    except Exception:
        return fallback_route(command)
