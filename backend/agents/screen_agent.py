"""
screen_agent.py — JARVIS Screen Reading & Visual AI
====================================================
Captures a screenshot and sends it to Groq's vision model (llama-4-scout)
for AI-powered screen analysis, debugging, and description.

Voice commands handled:
  - "what's on my screen"
  - "read my screen"
  - "debug this error"
  - "what error am I seeing"
  - "describe my screen"
  - "analyze my screen"
  - "what's open"
"""

import os
import io
import base64
import subprocess
import sys
import re
import datetime

# ── Trigger detection ────────────────────────────────────────────────────────
SCREEN_TRIGGERS = [
    "what's on my screen", "whats on my screen", "read my screen",
    "what is on my screen", "describe my screen", "analyze my screen",
    "what do you see", "look at my screen", "screen reading",
    "what error am i seeing", "debug this error", "debug this",
    "debug my screen", "help me with this error", "what's open",
    "whats open", "tell me what's on screen", "screen analysis",
    "screenshot and analyze", "read the screen", "read what's on screen",
]

def is_screen_command(command: str) -> bool:
    """Returns True if the command is a screen reading request."""
    cmd = command.lower().strip()
    return any(trigger in cmd for trigger in SCREEN_TRIGGERS)


def _take_screenshot() -> bytes:
    """
    Capture the full screen as PNG bytes.
    Uses native macOS screencapture or PIL on other platforms.
    """
    if sys.platform == "darwin":
        # macOS: use screencapture utility (most reliable)
        tmpfile = "/tmp/jarvis_screen_cap.png"
        try:
            subprocess.run(
                ["screencapture", "-x", "-t", "png", tmpfile],
                check=True, timeout=5
            )
            with open(tmpfile, "rb") as f:
                data = f.read()
            os.remove(tmpfile)
            return data
        except Exception as e:
            print(f"[SCREEN] screencapture failed: {e}, trying PIL fallback")

    # Universal fallback: PIL
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        raise RuntimeError("Pillow not installed. Run: pip install pillow")


def analyze_screen(command: str = "What is on my screen?") -> str:
    """
    Takes a screenshot and sends it to Groq llama-4-scout vision model.
    Returns JARVIS's AI analysis as a string.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return "Raj, I need a Groq API key to analyze your screen."

    try:
        # Capture screen
        screenshot_bytes = _take_screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        # Build a focused prompt based on the command
        cmd_lower = command.lower()
        if any(w in cmd_lower for w in ["error", "bug", "debug", "problem", "issue", "fix"]):
            task_prompt = (
                "Look at this screenshot carefully. Identify any errors, bugs, exceptions, "
                "or problems visible on the screen. Give a clear diagnosis and suggest "
                "specific fixes. Be direct and actionable. Address Raj as 'Sir'."
            )
        elif any(w in cmd_lower for w in ["open", "what's open", "apps", "running"]):
            task_prompt = (
                "List all the applications, windows, and tabs currently visible on this screen. "
                "Describe what's open and what the user seems to be doing. Address Raj as 'Sir'."
            )
        else:
            task_prompt = (
                "Describe everything visible on this screenshot in detail: apps, windows, "
                "text content, UI elements, any errors or important information. "
                "Be concise but comprehensive. Address Raj as 'Sir'."
            )

        from groq import Groq
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are J.A.R.V.I.S., Raj's elite AI assistant. You have just been given "
                        "a screenshot of Raj's screen. Analyze it with precision and intelligence. "
                        "Be like Tony Stark's AI — sharp, direct, and helpful. Always address Raj as 'Sir'."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": task_prompt
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=600
        )

        analysis = response.choices[0].message.content.strip()
        return f"📸 Screen Analysis: {analysis}"

    except Exception as e:
        return f"Raj, I couldn't analyze your screen: {str(e)}"


def save_screenshot_with_analysis(command: str) -> tuple:
    """
    Saves the screenshot to disk and returns (analysis_text, file_path).
    Used when user wants to keep a copy of what JARVIS saw.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, f"screen_cap_{ts}.png")

    try:
        screenshot_bytes = _take_screenshot()
        with open(filepath, "wb") as f:
            f.write(screenshot_bytes)
        analysis = analyze_screen(command)
        return analysis, filepath
    except Exception as e:
        return f"Screenshot failed: {e}", None
