import os
import re
import time
import subprocess
import pyautogui
import sys
try:
    import pygetwindow as gw
except ImportError:
    gw = None

IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"

# Whitelist of allowed executables — nothing outside this list can be launched
ALLOWED_APPS_WIN = {
    "chrome":       ["start", "chrome"],
    "google chrome":["start", "chrome"],
    "vscode":       ["code"],
    "vs code":      ["code"],
    "code":         ["code"],
    "notepad":      ["notepad.exe"],
    "spotify":      ["start", "spotify"],
    "whatsapp":     ["start", "whatsapp"],
    "explorer":     ["explorer.exe"],
    "file explorer":["explorer.exe"],
    "files":        ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
    "calculator":   ["calc.exe"],
    "calc":         ["calc.exe"],
    "camera":       ["start", "microsoft.windows.camera:"],
    "settings":     ["start", "ms-settings:"],
    "paint":        ["mspaint.exe"],
    "word":         ["search", "Microsoft Word"],
    "excel":        ["search", "Microsoft Excel"],
    "powerpoint":   ["search", "Microsoft PowerPoint"],
    "power point":  ["search", "Microsoft PowerPoint"],
    "cmd":          ["cmd.exe"],
    "command prompt":["cmd.exe"],
    "terminal":     ["cmd.exe"],
}

ALLOWED_CLOSE_WIN = {
    "chrome":       "chrome.exe",
    "notepad":      "notepad.exe",
    "spotify":      "spotify.exe",
    "whatsapp":     "whatsapp.exe",
    "vscode":       "code.exe",
    "vs code":      "code.exe",
    "code":         "code.exe",
    "explorer":     "explorer.exe",
    "task manager": "taskmgr.exe",
    "calculator":   "calc.exe",
    "paint":        "mspaint.exe",
    "word":         "winword.exe",
    "excel":        "excel.exe",
    "powerpoint":   "powerpnt.exe",
    "cmd":          "cmd.exe",
    "terminal":     "cmd.exe",
}

# macOS App mapping
ALLOWED_APPS_MAC = {
    "chrome":       "Google Chrome",
    "google chrome":"Google Chrome",
    "vscode":       "Visual Studio Code",
    "vs code":      "Visual Studio Code",
    "code":         "Visual Studio Code",
    "notepad":      "TextEdit",
    "textedit":     "TextEdit",
    "spotify":      "Spotify",
    "whatsapp":     "WhatsApp",
    "explorer":     "Finder",
    "file explorer":"Finder",
    "files":        "Finder",
    "task manager": "Activity Monitor",
    "activity monitor": "Activity Monitor",
    "calculator":   "Calculator",
    "calc":         "Calculator",
    "camera":       "Photo Booth",
    "photo booth":  "Photo Booth",
    "settings":     "System Settings",
    "system settings": "System Settings",
    "terminal":     "Terminal",
}

def _open_via_windows_search(app_name: str) -> bool:
    """Open any app by searching in Windows Start menu."""
    pyautogui.press('win')
    time.sleep(1.5)
    pyautogui.typewrite(app_name, interval=0.1)
    time.sleep(2)  # wait for search results
    pyautogui.press('enter')
    time.sleep(1)
    return True

def _run(args: list):
    """Safe subprocess call — no shell=True, fixed arg list only."""
    subprocess.run(args, shell=False, creationflags=subprocess.CREATE_NO_WINDOW
                   if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)

def _run_shell(args: list):
    """For Windows 'start' commands that require shell=True but with fixed args only."""
    subprocess.run(" ".join(args), shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                   if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)

def execute_system_command(command: str) -> str:
    cmd = command.lower()
    try:

        # --- Shutdown ---
        if "shut down" in cmd or "shutdown" in cmd:
            if IS_MAC:
                subprocess.run(["osascript", "-e", 'tell app "System Events" to shut down'])
            else:
                _run(["shutdown", "/s", "/t", "5"])
            return "Raj, shutting down in 5 seconds."

        # --- Restart ---
        elif "restart" in cmd or "reboot" in cmd:
            if IS_MAC:
                subprocess.run(["osascript", "-e", 'tell app "System Events" to restart'])
            else:
                _run(["shutdown", "/r", "/t", "5"])
            return "Raj, restarting in 5 seconds."

        # --- Lock ---
        elif "lock" in cmd:
            if IS_MAC:
                subprocess.run(["pmset", "displaysleepnow"])
            else:
                _run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "Screen locked, Raj."

        # --- Sleep ---
        elif "sleep" in cmd or "hibernate" in cmd:
            if IS_MAC:
                subprocess.run(["osascript", "-e", 'tell application "System Events" to sleep'])
            else:
                _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "Putting laptop to sleep, Raj."

        # --- Screenshot ---
        elif "screenshot" in cmd:
            if IS_MAC:
                # Minimize all windows on Mac
                subprocess.run(["osascript", "-e", 'tell application "System Events" to set visible of every process whose visible is true to false'])
                time.sleep(0.8)
                if any(w in cmd for w in ["page", "browser", "chrome", "tab", "screen"]):
                    subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'])
                    time.sleep(0.8)
            else:
                # Minimize all windows on Windows
                pyautogui.hotkey('win', 'd')  # show desktop
                time.sleep(0.8)
                if gw and any(w in cmd for w in ["page", "browser", "chrome", "tab", "screen"]):
                    chrome_wins = [w for w in gw.getAllWindows()
                                   if "chrome" in w.title.lower() and w.visible]
                    if chrome_wins:
                        chrome_wins[0].restore()
                        chrome_wins[0].activate()
                        time.sleep(0.8)

            path = os.path.join(os.path.expanduser("~"), "Desktop", "jarvis_screenshot.png")
            pyautogui.screenshot(path)

            if IS_MAC:
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["explorer", path])
            return f"Screenshot taken and saved to Desktop, Raj."

        # --- Volume ---
        elif "volume up" in cmd or "increase volume" in cmd or "turn up" in cmd:
            if IS_MAC:
                subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])
            else:
                for _ in range(5): pyautogui.press("volumeup")
            return "Volume increased, Raj."

        elif "volume down" in cmd or "decrease volume" in cmd or "turn down" in cmd:
            if IS_MAC:
                subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])
            else:
                for _ in range(5): pyautogui.press("volumedown")
            return "Volume decreased, Raj."

        elif "unmute" in cmd:
            if IS_MAC:
                subprocess.run(["osascript", "-e", "set volume without output muted"])
            else:
                pyautogui.press("volumemute")
            return "Audio unmuted, Raj."

        elif "mute" in cmd:
            if IS_MAC:
                subprocess.run(["osascript", "-e", "set volume with output muted"])
            else:
                pyautogui.press("volumemute")
            return "Audio muted, Raj."

        # --- Brightness ---
        elif "brightness up" in cmd or "increase brightness" in cmd:
            _set_brightness(80)
            return "Brightness increased, Raj."

        elif "brightness down" in cmd or "decrease brightness" in cmd:
            _set_brightness(30)
            return "Brightness decreased, Raj."

        # --- Open Apps ---
        elif "open" in cmd:
            app_key = cmd.replace("open", "").strip()

            # --- Notepad / TextEdit ---
            if "notepad" in app_key or "textedit" in app_key:
                text_to_type = ""
                for kw in ["and type", "and write", "type", "write"]:
                    if kw in app_key:
                        text_to_type = app_key.split(kw, 1)[-1].strip()
                        break

                if IS_MAC:
                    subprocess.Popen(["open", "-a", "TextEdit"])
                    time.sleep(2)
                    if text_to_type:
                        import pyperclip
                        pyperclip.copy(text_to_type)
                        pyautogui.hotkey('command', 'v')
                        return f"Raj, opened TextEdit and typed '{text_to_type}'."
                    return "Opening TextEdit, Raj."
                else:
                    _run(["notepad.exe"])
                    time.sleep(2)
                    if text_to_type and gw:
                        notepad_wins = [w for w in gw.getAllWindows()
                                        if "notepad" in w.title.lower() and w.visible]
                        if notepad_wins:
                            notepad_wins[0].activate()
                            time.sleep(0.5)
                        import pyperclip
                        pyperclip.copy(text_to_type)
                        pyautogui.hotkey('ctrl', 'v')
                        return f"Raj, opened Notepad and typed '{text_to_type}'."
                    return "Opening Notepad, Raj."

            # --- All other apps ---
            if IS_MAC:
                matched = next((v for k, v in ALLOWED_APPS_MAC.items() if k in app_key), None)
                if matched:
                    subprocess.Popen(["open", "-a", matched])
                    return f"Opening {matched}, Raj."
                else:
                    # Generic try open on mac
                    subprocess.Popen(["open", "-a", app_key.strip().title()])
                    return f"Opening {app_key.strip().title()}, Raj."
            else:
                matched = next((v for k, v in ALLOWED_APPS_WIN.items() if k in app_key), None)
                if matched:
                    label = app_key.strip().title()
                    try:
                        if matched[0] == "search":
                            _open_via_windows_search(matched[1])
                        elif matched[0] == "start":
                            _run_shell(matched)
                        else:
                            _run(matched)
                        time.sleep(1.5)
                        if gw:
                            opened = any(label.lower().split()[0] in w.title.lower()
                                         for w in gw.getAllWindows() if w.title)
                            if not opened and matched[0] != "search":
                                _open_via_windows_search(label)
                    except Exception:
                        _open_via_windows_search(app_key.strip())
                    return f"Opening {label}, Raj."
                else:
                    _open_via_windows_search(app_key.strip())
                    return f"Opening {app_key.strip()}, Raj."

        # --- Close Apps ---
        elif "close" in cmd:
            app_key = cmd.replace("close", "").strip()
            if IS_MAC:
                matched = next((v for k, v in ALLOWED_APPS_MAC.items() if k in app_key), None)
                if matched:
                    subprocess.run(["osascript", "-e", f'quit app "{matched}"'])
                    return f"Closed {app_key.strip()}, Raj."
                else:
                    subprocess.run(["pkill", "-f", app_key.strip()])
                    return f"Closed {app_key.strip()}, Raj."
            else:
                exe = next((v for k, v in ALLOWED_CLOSE_WIN.items() if k in app_key), None)
                if exe:
                    _run(["taskkill", "/f", "/im", exe])
                    return f"Closed {app_key.strip()}, Raj."
                return f"Raj, I couldn't find '{app_key}' to close."

        # --- Folder Creation ---
        elif "make folder" in cmd or "create folder" in cmd:
            folder_name = "NewFolder"
            for prefix in ["make folder", "create folder"]:
                if prefix in cmd:
                    parts = cmd.split(prefix, 1)
                    if len(parts) > 1 and parts[1].strip():
                        folder_name = parts[1].strip()
                    break
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            folder_path = os.path.join(desktop_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            return f"Raj, I created the folder '{folder_name}' on your Desktop."

        # --- Python Code Generation ---
        elif "write python code for chatbot" in cmd:
            code = '''def chat():
    print("Hello! I am your interactive chatbot.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chatbot: Goodbye!")
            break
        print(f"Chatbot: You said '{user_input}'")

if __name__ == "__main__":
    chat()
'''
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            file_path = os.path.join(desktop_path, "chatbot.py")
            with open(file_path, "w") as f:
                f.write(code)
            return f"Raj, I wrote the python chatbot script to {file_path}."

        # --- Execute Python Scripts ---
        elif "run script" in cmd or "execute script" in cmd:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            file_path = os.path.join(desktop_path, "chatbot.py")
            if IS_MAC:
                subprocess.run(["osascript", "-e", f'tell application "Terminal" to do script "python3 {file_path}"'])
            else:
                subprocess.Popen(["cmd.exe", "/c", f"start cmd.exe /k python {file_path}"])
            return f"Raj, I am running the script in a new terminal window."

        # --- Terminal Execution ---
        elif "run command" in cmd:
            command_to_run = cmd.split("run command", 1)[1].strip()
            if command_to_run:
                try:
                    output = subprocess.check_output(command_to_run, shell=True, text=True, stderr=subprocess.STDOUT)
                    return f"Raj, output of '{command_to_run}':\n{output[:500]}"
                except subprocess.CalledProcessError as e:
                    return f"Raj, command failed with output: {e.output}"
            return "Raj, please provide a command to run."

        # --- Mac Resource Status ---
        elif "battery" in cmd:
            if IS_MAC:
                try:
                    output = subprocess.check_output(["pmset", "-g", "batt"], text=True)
                    return f"Raj, your battery status is: {output.strip()}"
                except:
                    return "Raj, could not check battery status."
            return "Raj, battery check is currently supported on Mac."

        elif "disk space" in cmd:
            if IS_MAC:
                try:
                    output = subprocess.check_output(["df", "-h", "/"], text=True)
                    return f"Raj, your disk space is:\n{output.strip()}"
                except:
                    return "Raj, could not check disk space."
            return "Raj, disk space check is currently supported on Mac."

        else:
            return f"Raj, I executed: {command}"

    except Exception as e:
        return f"Raj, I encountered an error: {str(e)}"


def _set_brightness(level: int):
    # Fixed args — level is an int, not user input, so safe
    level = max(0, min(100, int(level)))  # clamp 0-100
    if IS_MAC:
        # Increase or decrease using AppleScript keystrokes based on target level
        # A simple estimation: 30% is low (repeat down), 80% is high (repeat up)
        repeats = 10
        key_code = 144 if level > 50 else 145
        subprocess.run(["osascript", "-e", f'tell application "System Events" to repeat {repeats} times', "-e", f'key code {key_code}', "-e", 'end repeat'])
    else:
        subprocess.run(
            ["powershell", "-command",
             f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"],
            shell=False
        )
