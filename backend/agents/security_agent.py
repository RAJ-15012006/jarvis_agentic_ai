"""
security_agent.py — JARVIS Security Module
===========================================
Runs at the HIGHEST priority — checked before any other routing.
Handles:
  1. Intrusion-phrase detection → instant macOS screen lock + intruder photo capture
  2. "Close all tabs" → close every Chrome tab via AppleScript
  3. "Shut down" → instant macOS shutdown (no routing delay)
  4. Intruder Photo Capture → OpenCV snapshot saved with timestamp for audit trail
"""

import subprocess
import sys
import re
import os
import datetime

IS_MAC = sys.platform == "darwin"

# Directory to store intruder photos
INTRUDER_LOG_DIR = os.path.join(os.path.dirname(__file__), "face_data", "intruder_log")
os.makedirs(INTRUDER_LOG_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Intrusion phrases — if anyone (Raj or otherwise) utters these,
# the screen locks IMMEDIATELY. Priority: safety first.
# ---------------------------------------------------------------------------
INTRUSION_PHRASES = [
    "access raj",
    "access raj's laptop",
    "access raj laptop",
    "access the laptop",
    "access rajsamrendra",
    "access raj's computer",
    "access raj computer",
    "hack raj",
    "hack the laptop",
    "get into the laptop",
    "get into raj",
    "open raj's computer",
    "open raj laptop",
    "unlock raj laptop",
    "unlock raj's laptop",
    "break into raj",
    "steal raj",
    "raj's password",
    "raj password",
    "raj's pin",
    "someone is watching",
]

# Shutdown trigger phrases (fast-path, bypasses all routing)
SHUTDOWN_PHRASES = [
    "shut down",
    "shutdown",
    "power off",
    "turn off the laptop",
    "turn off computer",
    "power down",
]

# Close all tabs phrases
CLOSE_ALL_TABS_PHRASES = [
    "close all tabs",
    "close every tab",
    "close all chrome tabs",
    "close all browser tabs",
    "shut all tabs",
    "close all the tabs",
]


def _normalize(text: str) -> str:
    """Lowercase + remove punctuation for fuzzy matching."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def is_intrusion_attempt(command: str) -> bool:
    """Returns True if the command matches any intrusion phrase."""
    normalized = _normalize(command)
    for phrase in INTRUSION_PHRASES:
        if phrase in normalized:
            return True
    return False


def is_shutdown_command(command: str) -> bool:
    """Returns True if command is a shutdown order."""
    normalized = _normalize(command)
    for phrase in SHUTDOWN_PHRASES:
        if phrase in normalized:
            return True
    return False


def is_close_all_tabs_command(command: str) -> bool:
    """Returns True if command asks to close all browser tabs."""
    normalized = _normalize(command)
    for phrase in CLOSE_ALL_TABS_PHRASES:
        if phrase in normalized:
            return True
    return False


# ---------------------------------------------------------------------------
# Intruder Photo Capture
# ---------------------------------------------------------------------------

def capture_intruder_photo() -> str:
    """
    Silently captures a photo from the webcam using OpenCV and saves it
    to the intruder log directory with a timestamp filename.
    Returns the file path if successful, None otherwise.
    """
    try:
        import cv2

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            print("[SECURITY] Warning: Could not open webcam for intruder capture.")
            return None

        # Warm up the camera (first few frames are often dark)
        for _ in range(5):
            cam.read()

        ret, frame = cam.read()
        cam.release()

        if not ret or frame is None:
            print("[SECURITY] Warning: Failed to capture frame from webcam.")
            return None

        # Timestamp the filename
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intruder_{ts}.jpg"
        filepath = os.path.join(INTRUDER_LOG_DIR, filename)

        cv2.imwrite(filepath, frame)
        print(f"[SECURITY] 📸 Intruder photo saved: {filepath}")
        return filepath

    except ImportError:
        print("[SECURITY] OpenCV not available — skipping photo capture.")
        return None
    except Exception as e:
        print(f"[SECURITY] Intruder capture error: {e}")
        return None


def get_intruder_log() -> list:
    """
    Returns a list of all intruder photos (filename + full path + timestamp).
    Used by the BiometricsDashboard to display security events.
    """
    entries = []
    try:
        for fname in sorted(os.listdir(INTRUDER_LOG_DIR), reverse=True):
            if fname.startswith("intruder_") and fname.endswith(".jpg"):
                fpath = os.path.join(INTRUDER_LOG_DIR, fname)
                # Parse timestamp from filename: intruder_YYYYMMDD_HHMMSS.jpg
                ts_str = fname.replace("intruder_", "").replace(".jpg", "")
                try:
                    ts = datetime.datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    ts_display = ts.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts_display = ts_str
                entries.append({
                    "filename": fname,
                    "path": fpath,
                    "timestamp": ts_display,
                })
    except Exception as e:
        print(f"[SECURITY] Error reading intruder log: {e}")
    return entries


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def lock_screen() -> str:
    """Immediately lock the macOS screen."""
    try:
        if IS_MAC:
            subprocess.Popen(["pmset", "displaysleepnow"])
        else:
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return "🔒 Security alert — screen locked immediately, Sir."
    except Exception as e:
        return f"Security lock failed: {e}"


def lock_screen_with_photo() -> tuple:
    """
    Lock the screen AND silently take an intruder photo simultaneously.
    Returns (lock_message, photo_path).
    """
    photo_path = capture_intruder_photo()
    lock_msg = lock_screen()
    return lock_msg, photo_path


def shutdown_system() -> str:
    """Immediately shut down the system (Disabled for safety)."""
    return "Raj, shutdown capability is disabled for safety."


def close_all_chrome_tabs() -> str:
    """Close every tab in every Chrome window via AppleScript (macOS)."""
    try:
        if IS_MAC:
            script = """
            tell application "Google Chrome"
                set windowList to every window
                repeat with w in windowList
                    set tabList to every tab of w
                    repeat with t in tabList
                        close t
                    end repeat
                end repeat
            end tell
            """
            subprocess.run(["osascript", "-e", script], timeout=10)
            return "Done, Sir. All Chrome tabs have been closed."
        else:
            # Windows — use pyautogui to Ctrl+W each tab
            import pyautogui, time
            import pygetwindow as gw
            chrome_wins = [w for w in gw.getAllWindows()
                           if "chrome" in w.title.lower() and w.visible]
            for win in chrome_wins:
                win.activate()
                time.sleep(0.3)
                # Close tabs repeatedly until window is gone
                for _ in range(30):
                    pyautogui.hotkey("ctrl", "w")
                    time.sleep(0.1)
            return "Done, Sir. All Chrome tabs have been closed."
    except Exception as e:
        return f"Raj, I couldn't close all tabs: {e}"
