import os
import re
import time
import subprocess
import pyautogui
import sys
import datetime

try:
    import pygetwindow as gw
except ImportError:
    gw = None

IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"

# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _osascript(script: str) -> str:
    """Run an AppleScript one-liner and return stdout."""
    try:
        result = subprocess.run(["osascript", "-e", script],
                                capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

def _extract_number(text: str):
    """Extract first integer from a string."""
    m = re.search(r'\d+', text)
    return int(m.group()) if m else None

def _clamp(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, val))

def _save_screenshot() -> str:
    """Take a screenshot and save to Desktop AND Downloads. Returns filepath."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"jarvis_screenshot_{ts}.png"
    desktop = os.path.expanduser(f"~/Desktop/{fname}")
    downloads = os.path.expanduser(f"~/Downloads/{fname}")
    img = pyautogui.screenshot()
    img.save(desktop)
    img.save(downloads)
    return desktop, downloads, fname

# ─────────────────────────────────────────────────────────────────────────────
# Volume
# ─────────────────────────────────────────────────────────────────────────────

def _get_volume() -> int:
    if IS_MAC:
        out = _osascript("output volume of (get volume settings)")
        try:
            return int(out)
        except:
            return 50
    return 50

def _set_volume(level: int):
    level = _clamp(level, 0, 100)
    if IS_MAC:
        _osascript(f"set volume output volume {level}")
    else:
        for _ in range(10):
            pyautogui.press("volumedown")
        steps = level // 6
        for _ in range(steps):
            pyautogui.press("volumeup")

def handle_volume(cmd: str) -> str:
    # Set volume to exact number
    m = re.search(r'(?:set|volume)\s+(?:to\s+)?(\d+)', cmd)
    if m:
        val = _clamp(int(m.group(1)), 0, 100)
        _set_volume(val)
        return f"Volume set to {val}%, Raj."

    current = _get_volume()

    if any(p in cmd for p in ["volume up", "increase volume", "louder", "turn up", "raise volume"]):
        step = _extract_number(cmd) or 10
        _set_volume(current + step)
        return f"Volume increased to {min(100, current + step)}%, Raj."

    if any(p in cmd for p in ["volume down", "decrease volume", "quieter", "turn down", "lower volume"]):
        step = _extract_number(cmd) or 10
        _set_volume(current - step)
        return f"Volume decreased to {max(0, current - step)}%, Raj."

    if "unmute" in cmd:
        if IS_MAC:
            _osascript("set volume without output muted")
        else:
            pyautogui.press("volumemute")
        return "Audio unmuted, Raj."

    if "mute" in cmd:
        if IS_MAC:
            _osascript("set volume with output muted")
        else:
            pyautogui.press("volumemute")
        return "Audio muted, Raj."

    if any(p in cmd for p in ["what is the volume", "current volume", "volume level"]):
        return f"Current volume is {current}%, Raj."

    return f"Current volume is {current}%, Raj."

# ─────────────────────────────────────────────────────────────────────────────
# Brightness
# ─────────────────────────────────────────────────────────────────────────────

def _set_brightness_mac(level: int):
    """Set brightness using AppleScript key presses (relative, not absolute)."""
    level = _clamp(level, 0, 100)
    # First press brightness down 16 times to go to minimum
    script = """
    tell application "System Events"
        repeat 16 times
            key code 145
        end repeat
    end tell
    """
    subprocess.run(["osascript", "-e", script])
    time.sleep(0.3)
    # Then press up to reach target level (each press ~6%)
    steps = round(level / 6)
    up_script = f"""
    tell application "System Events"
        repeat {steps} times
            key code 144
        end repeat
    end tell
    """
    subprocess.run(["osascript", "-e", up_script])

def handle_brightness(cmd: str) -> str:
    m = re.search(r'(?:set|brightness)\s+(?:to\s+)?(\d+)', cmd)
    if m:
        val = _clamp(int(m.group(1)), 0, 100)
        if IS_MAC:
            _set_brightness_mac(val)
        return f"Brightness set to {val}%, Raj."

    if any(p in cmd for p in ["brightness up", "increase brightness", "brighter", "more bright"]):
        if IS_MAC:
            _osascript('tell application "System Events" to repeat 3 times\nkey code 144\nend repeat')
        return "Brightness increased, Raj."

    if any(p in cmd for p in ["brightness down", "decrease brightness", "dimmer", "dim", "less bright"]):
        if IS_MAC:
            _osascript('tell application "System Events" to repeat 3 times\nkey code 145\nend repeat')
        return "Brightness decreased, Raj."

    if "max brightness" in cmd or "full brightness" in cmd:
        if IS_MAC:
            _set_brightness_mac(100)
        return "Brightness set to maximum, Raj."

    if "min brightness" in cmd or "minimum brightness" in cmd:
        if IS_MAC:
            _set_brightness_mac(0)
        return "Brightness set to minimum, Raj."

    return "Raj, say 'brightness up', 'brightness down', or 'set brightness to 70'."

# ─────────────────────────────────────────────────────────────────────────────
# Battery
# ─────────────────────────────────────────────────────────────────────────────

def handle_battery(cmd: str) -> str:
    if IS_MAC:
        try:
            raw = subprocess.check_output(["pmset", "-g", "batt"], text=True)
            # Parse percentage
            pct_match = re.search(r'(\d+)%', raw)
            pct = pct_match.group(1) if pct_match else "unknown"
            # Parse charging status
            if "AC Power" in raw:
                status = "charging"
            elif "discharging" in raw:
                status = "discharging (on battery)"
            else:
                status = "on battery"
            # Parse time remaining
            time_match = re.search(r'(\d+:\d+) remaining', raw)
            time_left = f", {time_match.group(1)} remaining" if time_match else ""
            return f"Raj, your battery is at {pct}% and is {status}{time_left}."
        except Exception as e:
            return f"Raj, could not read battery: {e}"
    return "Raj, battery check is only supported on Mac right now."

# ─────────────────────────────────────────────────────────────────────────────
# Screenshot
# ─────────────────────────────────────────────────────────────────────────────

def handle_screenshot(cmd: str) -> str:
    try:
        time.sleep(0.5)  # Small delay so JARVIS window doesn't appear in screenshot
        desktop_path, downloads_path, fname = _save_screenshot()
        # Open the screenshot in Preview
        if IS_MAC:
            subprocess.Popen(["open", desktop_path])
        return f"Screenshot saved! '{fname}' is in both your Desktop and Downloads, Raj."
    except Exception as e:
        return f"Raj, screenshot failed: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# Do Not Disturb
# ─────────────────────────────────────────────────────────────────────────────

def handle_do_not_disturb(cmd: str) -> str:
    if not IS_MAC:
        return "Do Not Disturb is only supported on Mac, Raj."
    enable = any(p in cmd for p in ["enable", "on", "turn on", "activate", "start"])
    disable = any(p in cmd for p in ["disable", "off", "turn off", "deactivate", "stop"])
    if enable:
        # macOS Sonoma/Ventura: toggle Focus via shortcuts
        _osascript("""
        tell application "System Events"
            tell process "Control Center"
                set frontmost to true
            end tell
        end tell
        """)
        subprocess.run(["osascript", "-e",
            'tell application "System Events" to keystroke "d" using {command down, option down}'])
        return "Do Not Disturb enabled, Raj. You won't be disturbed."
    elif disable:
        subprocess.run(["osascript", "-e",
            'tell application "System Events" to keystroke "d" using {command down, option down}'])
        return "Do Not Disturb disabled, Raj. Notifications are back on."
    else:
        # Toggle
        subprocess.run(["osascript", "-e",
            'tell application "System Events" to keystroke "d" using {command down, option down}'])
        return "Do Not Disturb toggled, Raj."

# ─────────────────────────────────────────────────────────────────────────────
# Dark Mode
# ─────────────────────────────────────────────────────────────────────────────

def handle_dark_mode(cmd: str) -> str:
    if not IS_MAC:
        return "Dark mode toggle is only supported on Mac, Raj."
    enable = any(p in cmd for p in ["enable", "on", "turn on", "activate", "dark"])
    disable = any(p in cmd for p in ["disable", "off", "turn off", "light mode", "light"])

    if "toggle" in cmd or (enable and disable) or (not enable and not disable):
        _osascript('tell app "System Events" to tell appearance preferences to set dark mode to not dark mode')
        return "Dark mode toggled, Raj."
    elif enable and "light" not in cmd:
        _osascript('tell app "System Events" to tell appearance preferences to set dark mode to true')
        return "Dark mode enabled, Raj."
    else:
        _osascript('tell app "System Events" to tell appearance preferences to set dark mode to false')
        return "Light mode enabled, Raj."

# ─────────────────────────────────────────────────────────────────────────────
# Clipboard
# ─────────────────────────────────────────────────────────────────────────────

def handle_clipboard(cmd: str) -> str:
    if "what" in cmd or "read" in cmd or "show" in cmd:
        try:
            result = subprocess.run(["pbpaste"], capture_output=True, text=True)
            content = result.stdout.strip()
            if content:
                return f"Raj, your clipboard contains: '{content[:200]}'"
            return "Raj, your clipboard is empty."
        except Exception as e:
            return f"Raj, could not read clipboard: {e}"
    if "clear" in cmd:
        subprocess.run(["pbcopy"], input="", text=True)
        return "Clipboard cleared, Raj."
    if "copy" in cmd:
        pyautogui.hotkey("command" if IS_MAC else "ctrl", "c")
        return "Copied, Raj."
    if "paste" in cmd:
        pyautogui.hotkey("command" if IS_MAC else "ctrl", "v")
        return "Pasted, Raj."
    return "Raj, say 'read clipboard', 'copy', 'paste', or 'clear clipboard'."

# ─────────────────────────────────────────────────────────────────────────────
# Window Management
# ─────────────────────────────────────────────────────────────────────────────

def handle_window(cmd: str) -> str:
    if IS_MAC:
        if any(p in cmd for p in ["minimize", "minimise", "hide window"]):
            _osascript('tell application "System Events" to keystroke "m" using command down')
            return "Window minimized, Raj."
        if any(p in cmd for p in ["maximize", "maximise", "full screen", "fullscreen window"]):
            pyautogui.hotkey("ctrl", "command", "f")
            return "Window maximized, Raj."
        if any(p in cmd for p in ["close window", "close this window", "close app"]):
            _osascript('tell application "System Events" to keystroke "w" using command down')
            return "Window closed, Raj."
        if any(p in cmd for p in ["hide all", "show desktop", "minimize all"]):
            _osascript('tell application "System Events" to keystroke "h" using {command down, option down}')
            return "All windows hidden, Raj."
        if "switch app" in cmd or "next app" in cmd:
            pyautogui.hotkey("command", "tab")
            return "Switched to next app, Raj."
    else:
        if "minimize" in cmd:
            pyautogui.hotkey("win", "down")
            return "Window minimized, Raj."
        if "maximize" in cmd:
            pyautogui.hotkey("win", "up")
            return "Window maximized, Raj."
        if "close window" in cmd:
            pyautogui.hotkey("alt", "f4")
            return "Window closed, Raj."
        if "show desktop" in cmd:
            pyautogui.hotkey("win", "d")
            return "Showing desktop, Raj."
    return "Raj, say 'minimize', 'maximize', 'close window', or 'show desktop'."

# ─────────────────────────────────────────────────────────────────────────────
# Wi-Fi & Bluetooth
# ─────────────────────────────────────────────────────────────────────────────

def handle_wifi(cmd: str) -> str:
    if not IS_MAC:
        return "Raj, Wi-Fi toggle is Mac-only right now."
    if any(p in cmd for p in ["turn on", "enable", "on"]):
        subprocess.run(["networksetup", "-setairportpower", "en0", "on"])
        return "Wi-Fi turned on, Raj."
    if any(p in cmd for p in ["turn off", "disable", "off"]):
        subprocess.run(["networksetup", "-setairportpower", "en0", "off"])
        return "Wi-Fi turned off, Raj."
    # Get current status
    result = subprocess.run(["networksetup", "-getairportpower", "en0"],
                            capture_output=True, text=True)
    return f"Raj, Wi-Fi status: {result.stdout.strip()}"

def handle_bluetooth(cmd: str) -> str:
    if not IS_MAC:
        return "Raj, Bluetooth toggle is Mac-only right now."
    if any(p in cmd for p in ["turn on", "enable", "on"]):
        subprocess.run(["blueutil", "--power", "1"])
        return "Bluetooth turned on, Raj."
    if any(p in cmd for p in ["turn off", "disable", "off"]):
        subprocess.run(["blueutil", "--power", "0"])
        return "Bluetooth turned off, Raj."
    return "Raj, say 'turn on Bluetooth' or 'turn off Bluetooth'."

# ─────────────────────────────────────────────────────────────────────────────
# Disk & System Info
# ─────────────────────────────────────────────────────────────────────────────

def handle_disk(cmd: str) -> str:
    if IS_MAC:
        try:
            out = subprocess.check_output(["df", "-h", "/"], text=True)
            lines = out.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                total, used, avail = parts[1], parts[2], parts[3]
                return f"Raj, your disk: Total {total}, Used {used}, Available {avail}."
        except:
            pass
    return "Raj, could not check disk space."

def handle_system_info(cmd: str) -> str:
    if IS_MAC:
        try:
            uptime = subprocess.check_output(["uptime"], text=True).strip()
            return f"Raj, system uptime: {uptime}"
        except:
            pass
    return "Raj, system info is only available on Mac."

# ─────────────────────────────────────────────────────────────────────────────
# Empty Trash
# ─────────────────────────────────────────────────────────────────────────────

def handle_empty_trash(cmd: str) -> str:
    if IS_MAC:
        _osascript('tell application "Finder" to empty trash')
        return "Trash emptied, Raj."
    return "Raj, empty trash is only supported on Mac."

# ─────────────────────────────────────────────────────────────────────────────
# Folder Creation
# ─────────────────────────────────────────────────────────────────────────────

def handle_create_and_write_code(cmd: str) -> str:
    """Create a folder and write a generated Python script inside it."""
    import json
    from groq import Groq
    
    # 1. Determine base path using heuristic fallback
    base_dir = os.path.expanduser("~/Desktop")
    target_name = "Desktop"
    cmd_lower = cmd.lower()
    
    if "download" in cmd_lower:
        base_dir = os.path.expanduser("~/Downloads")
        target_name = "Downloads"
    elif "document" in cmd_lower:
        base_dir = os.path.expanduser("~/Documents")
        target_name = "Documents"
    elif "desktop" in cmd_lower or "home screen" in cmd_lower or "homescreen" in cmd_lower:
        base_dir = os.path.expanduser("~/Desktop")
        target_name = "Desktop"
    elif "home" in cmd_lower:
        base_dir = os.path.expanduser("~")
        target_name = "Home"

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        # Heuristic fallback if Groq is unavailable
        folder_path = os.path.join(base_dir, "JarvisProject")
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "main.py")
        fallback_code = 'print("Hello from JARVIS!")\n'
        with open(file_path, "w") as f:
            f.write(fallback_code)
        if IS_MAC:
            subprocess.Popen(["open", folder_path])
        return f"Raj, I created a folder named 'JarvisProject' in your {target_name} and wrote a default main.py inside it."

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Extract or generate the folder name, file name, Python code, and target location from the user request: "{cmd}"
        
        Guidelines:
        - "folder_name": Extracted folder name (capitalized/camelCase, e.g., "ChatbotProject"). If not specified, use "JarvisApp".
        - "file_name": The target Python filename (e.g. "chatbot.py", "main.py").
        - "code": Generate complete, fully-functional, clean, commented Python code fulfilling the request.
          CRITICAL: Use only single quotes for strings and only '#' for comments in the Python code. Do NOT use triple double-quotes (\\\"\\\"\\\") or triple single-quotes (''') anywhere, as it breaks JSON. All newlines in the code must be escaped as \\n.
        - "target_location": The target directory. Must be one of: "desktop" (use this also for "home screen" or "homescreen"), "downloads", "documents", "home". Defaults to "desktop".

        Respond strictly in valid JSON format:
        {{
          "folder_name": "folder_name",
          "file_name": "file_name",
          "code": "Python code here",
          "target_location": "target_location"
        }}
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        res_data = json.loads(response.choices[0].message.content)
        folder_name = res_data.get("folder_name", "JarvisApp").strip()
        file_name = res_data.get("file_name", "main.py").strip()
        code_content = res_data.get("code", "")
        extracted_loc = res_data.get("target_location", "").strip().lower()
        
        if extracted_loc == "downloads":
            base_dir = os.path.expanduser("~/Downloads")
            target_name = "Downloads"
        elif extracted_loc == "documents":
            base_dir = os.path.expanduser("~/Documents")
            target_name = "Documents"
        elif extracted_loc == "home":
            base_dir = os.path.expanduser("~")
            target_name = "Home"
        else:
            base_dir = os.path.expanduser("~/Desktop")
            target_name = "Desktop"
            
        # Sanitize folder/file names
        folder_name = re.sub(r'[^\w\-_]', '_', folder_name)
        if not file_name.endswith(".py"):
            file_name += ".py"
        file_name = re.sub(r'[^\w\-_.]', '_', file_name)
        
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "w") as f:
            f.write(code_content)
            
        if IS_MAC:
            subprocess.Popen(["open", folder_path])
            
        return f"Raj, I created the folder '{folder_name}' in your {target_name} folder and wrote '{file_name}' inside it."
    except Exception as e:
        return f"Raj, failed to create project: {e}"


def handle_create_folder(cmd: str) -> str:
    import json
    from groq import Groq
    
    # 1. Determine base path using heuristic fallback
    base_dir = os.path.expanduser("~/Desktop")
    target_name = "Desktop"
    cmd_lower = cmd.lower()
    
    if "download" in cmd_lower:
        base_dir = os.path.expanduser("~/Downloads")
        target_name = "Downloads"
    elif "document" in cmd_lower:
        base_dir = os.path.expanduser("~/Documents")
        target_name = "Documents"
    elif "desktop" in cmd_lower or "home screen" in cmd_lower or "homescreen" in cmd_lower:
        base_dir = os.path.expanduser("~/Desktop")
        target_name = "Desktop"
    elif "home" in cmd_lower:
        base_dir = os.path.expanduser("~")
        target_name = "Home"

    folder_name = "NewFolder"
    for prefix in ["make folder", "create folder", "new folder", "make a folder", "create a folder"]:
        if prefix in cmd_lower:
            parts = cmd.split(prefix, 1)
            if len(parts) > 1 and parts[1].strip():
                # Extract potential folder name (remove location words)
                raw_name = parts[1].strip()
                # Clean up common trailing target descriptions like "in downloads", "on desktop"
                raw_name = re.split(r'\s+(?:in|on|at|inside)\s+', raw_name, maxsplit=1)[0].strip()
                if raw_name:
                    folder_name = raw_name.title()
            break

    api_key = os.getenv("GROQ_API_KEY", "")
    if api_key and api_key != "your_groq_api_key_here":
        try:
            client = Groq(api_key=api_key)
            prompt = f"""
            Extract the folder name and target location from the user request: "{cmd}"
            
            Guidelines:
            - "folder_name": The folder name to create (capitalized/camelCase, e.g., "MyFolder"). If not specified or vague, use "NewFolder".
            - "target_location": The target directory. Must be one of: "desktop" (use this also for "home screen" or "homescreen"), "downloads", "documents", "home". Defaults to "desktop".

            Respond strictly in JSON:
            {{
              "folder_name": "folder_name",
              "target_location": "target_location"
            }}
            """
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            res_data = json.loads(response.choices[0].message.content)
            extracted_folder = res_data.get("folder_name", "").strip()
            extracted_loc = res_data.get("target_location", "").strip().lower()
            
            if extracted_folder:
                folder_name = extracted_folder
            if extracted_loc == "downloads":
                base_dir = os.path.expanduser("~/Downloads")
                target_name = "Downloads"
            elif extracted_loc == "documents":
                base_dir = os.path.expanduser("~/Documents")
                target_name = "Documents"
            elif extracted_loc == "home":
                base_dir = os.path.expanduser("~")
                target_name = "Home"
            else:
                base_dir = os.path.expanduser("~/Desktop")
                target_name = "Desktop"
        except Exception:
            pass  # Fall back to heuristic values

    # Sanitize folder name
    folder_name = re.sub(r'[^\w\-_]', '_', folder_name)
    folder_path = os.path.join(base_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    if IS_MAC:
        subprocess.Popen(["open", folder_path])
        
    return f"Raj, created folder '{folder_name}' in your {target_name} folder."

# ─────────────────────────────────────────────────────────────────────────────
# Main dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def execute_system_command(command: str) -> str:
    cmd = command.lower().strip()
    try:

        # ── Volume ────────────────────────────────────────────────────────────
        if any(p in cmd for p in ["volume", "mute", "unmute", "louder", "quieter"]):
            return handle_volume(cmd)

        # ── Brightness ───────────────────────────────────────────────────────
        if any(p in cmd for p in ["brightness", "brighter", "dimmer", "dim screen"]):
            return handle_brightness(cmd)

        # ── Battery ──────────────────────────────────────────────────────────
        if "battery" in cmd:
            return handle_battery(cmd)

        # ── Screenshot ───────────────────────────────────────────────────────
        if "screenshot" in cmd or "take a photo" in cmd or "capture screen" in cmd:
            return handle_screenshot(cmd)

        # ── Do Not Disturb ───────────────────────────────────────────────────
        if any(p in cmd for p in ["do not disturb", "dnd", "focus mode", "don't disturb"]):
            return handle_do_not_disturb(cmd)

        # ── Dark Mode ────────────────────────────────────────────────────────
        if any(p in cmd for p in ["dark mode", "light mode", "toggle mode", "night mode"]):
            return handle_dark_mode(cmd)

        # ── Clipboard ────────────────────────────────────────────────────────
        if any(p in cmd for p in ["clipboard", "what did i copy", "paste", "copy that"]):
            return handle_clipboard(cmd)

        # ── Window Management ────────────────────────────────────────────────
        if any(p in cmd for p in ["minimize", "maximise", "maximize", "close window",
                                    "close this window", "hide all", "show desktop",
                                    "switch app", "next app"]):
            return handle_window(cmd)

        # ── Wi-Fi ────────────────────────────────────────────────────────────
        if "wifi" in cmd or "wi-fi" in cmd or "wireless" in cmd:
            return handle_wifi(cmd)

        # ── Bluetooth ────────────────────────────────────────────────────────
        if "bluetooth" in cmd:
            return handle_bluetooth(cmd)

        # ── Empty Trash ──────────────────────────────────────────────────────
        if any(p in cmd for p in ["empty trash", "clear trash", "delete trash"]):
            return handle_empty_trash(cmd)

        # ── Disk Space ───────────────────────────────────────────────────────
        if any(p in cmd for p in ["disk space", "storage", "how much space"]):
            return handle_disk(cmd)

        # ── Uptime / System Info ─────────────────────────────────────────────
        if any(p in cmd for p in ["uptime", "system info", "how long"]):
            return handle_system_info(cmd)

        # ── Folder & Code Creation ───────────────────────────────────────────
        is_folder_cmd = "folder" in cmd or "directory" in cmd
        is_create_cmd = any(p in cmd for p in ["make", "create", "new", "generate", "write", "setup"])
        
        if is_folder_cmd and is_create_cmd:
            has_code = any(k in cmd for k in ["write", "python", "code", "file", "script", "program"])
            if has_code:
                return handle_create_and_write_code(cmd)
            else:
                return handle_create_folder(cmd)

        # ── Lock ─────────────────────────────────────────────────────────────
        if any(p in cmd for p in ["lock", "lock screen", "lock laptop"]):
            if IS_MAC:
                subprocess.run(["pmset", "displaysleepnow"])
            else:
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "Screen locked, Raj."

        # ── Sleep ────────────────────────────────────────────────────────────
        if any(p in cmd for p in ["sleep", "hibernate", "sleep mode"]):
            if IS_MAC:
                _osascript('tell application "System Events" to sleep')
            else:
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "Putting laptop to sleep, Raj."

        # ── Shutdown ─────────────────────────────────────────────────────────
        if any(p in cmd for p in ["shut down", "shutdown", "power off", "turn off laptop"]):
            return "Raj, shutdown capability is disabled for safety."

        # ── Restart ──────────────────────────────────────────────────────────
        if any(p in cmd for p in ["restart", "reboot"]):
            return "Raj, restart capability is disabled for safety."

        # ── Run Terminal Command ──────────────────────────────────────────────
        if "run command" in cmd:
            command_to_run = cmd.split("run command", 1)[1].strip()
            if command_to_run:
                try:
                    output = subprocess.check_output(
                        command_to_run, shell=True, text=True,
                        stderr=subprocess.STDOUT, timeout=10
                    )
                    return f"Raj, output: {output.strip()[:400]}"
                except subprocess.CalledProcessError as e:
                    return f"Raj, command failed: {e.output}"
            return "Raj, please provide a command to run."

        return f"Raj, I've executed: {command}"

    except Exception as e:
        return f"Raj, I encountered an error: {str(e)}"
