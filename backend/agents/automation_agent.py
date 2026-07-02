import pywhatkit
import webbrowser
import time
import pyautogui
import os
import re
import requests
import json
from groq import Groq

# Whitelist of allowed URL schemes — blocks file://, javascript:, data: etc.
ALLOWED_SCHEMES = ("https://", "http://")

# Destructive system actions that need to be explicitly whitelisted
DESTRUCTIVE_ACTIONS = ["shutdown", "restart", "format", "delete", "remove"]

SCHEDULE_FILE = os.path.join(os.path.dirname(__file__), "..", "schedule.txt")

def _open_vscode() -> str:
    """Open VS Code by clicking on the window and typing 'vs code'."""
    import subprocess
    import sys
    
    if sys.platform == "darwin":
        try:
            subprocess.Popen(["open", "-a", "Visual Studio Code"])
            time.sleep(2)
            return "Raj, launching VS Code."
        except Exception:
            try:
                subprocess.Popen(['code'])
                time.sleep(2)
                return "Raj, launching VS Code."
            except Exception as e2:
                return f"Raj, couldn't open VS Code: {str(e2)}"
                
    try:
        import pygetwindow as gw
    except ImportError:
        gw = None
        
    try:
        # Try to find the Windows Start menu or taskbar
        time.sleep(0.5)
        
        # Click on the Windows Start button (usually bottom-left at ~20, 700)
        # Or use Windows key to open search
        pyautogui.press('win')
        time.sleep(0.8)  # Wait for Start menu/search to open
        
        # Type "vs code"
        pyautogui.typewrite('vs code', interval=0.1)
        time.sleep(1.5)  # Wait for search results to appear
        
        # Press Enter to open the first result
        pyautogui.press('enter')
        time.sleep(3)  # Wait for VS Code to launch
        
        return "Raj, opening VS Code for you."
    except Exception as e:
        try:
            # Fallback: Use subprocess to launch directly
            subprocess.Popen(['code'])
            time.sleep(3)
            return "Raj, launching VS Code."
        except Exception as e2:
            return f"Raj, couldn't open VS Code: {str(e2)}"

def _safe_url(url: str) -> str:
    """Ensure URL starts with http/https. Blocks file://, javascript:, data: etc."""
    if not url.startswith(ALLOWED_SCHEMES):
        return "https://www.google.com"  # safe fallback
    return url

def _safe_typewrite(text: str) -> str:
    """Strip non-printable and control characters before typing."""
    return re.sub(r'[^\x20-\x7E]', '', text)[:200]  # printable ASCII, max 200 chars

CONTACTS = {
    "raj": "+918591296816",
    "mom": "+91XXXXXXXXXX",
    "dad": "+91XXXXXXXXXX",
}

PROFILES = {
    "linkedin":  "https://www.linkedin.com/in/raj-samrendra-kumar-85770b2ba/",
    "github":    "https://github.com/RAJ-15012006",
    "portfolio": "https://raj-personal-portfolio.netlify.app/",
}

# Map site keywords to their URLs for closing (find & close tab)
SITE_KEYWORDS = {
    "youtube":   "youtube.com",
    "instagram": "instagram.com",
    "insta":     "instagram.com",
    "whatsapp":  "web.whatsapp.com",
    "linkedin":  "linkedin.com",
    "github":    "github.com",
    "portfolio": "raj-personal-portfolio",
    "amazon":    "amazon",
    "flipkart":  "flipkart",
    "chatgpt":   "chat.openai.com",
    "gpt":       "chat.openai.com",
    "gemini":    "gemini.google.com",
    "claude":    "claude.ai",
    "google":    "google.com",
    "netflix":   "netflix.com",
    "spotify":   "spotify.com",
}

# AI assistant URLs and their prompt input wait times
AI_ASSISTANTS = {
    "chatgpt": {"url": "https://chat.openai.com", "wait": 5},
    "gpt":     {"url": "https://chat.openai.com", "wait": 5},
    "gemini":  {"url": "https://gemini.google.com", "wait": 6},
    "claude":  {"url": "https://claude.ai", "wait": 6},
}

def _open_all_github_repos() -> str:
    """Fetch all public repos from GitHub API and open each in a new tab."""
    try:
        res = requests.get("https://api.github.com/users/RAJ-15012006/repos?per_page=100", timeout=5)
        repos = res.json()
        if not isinstance(repos, list) or len(repos) == 0:
            return "Raj, no public repositories found on your GitHub."
        for repo in repos:
            webbrowser.open_new_tab(repo["html_url"])
            time.sleep(0.5)
        return f"Raj, opened all {len(repos)} of your GitHub repositories."
    except Exception as e:
        return f"Raj, couldn't fetch GitHub repos: {str(e)}"

def _open_and_wait(url, wait=2):
    url = _safe_url(url)  # validate URL scheme before opening
    webbrowser.open(url)
    time.sleep(wait)

def _close_tab_by_name(site_name: str) -> str:
    """Use Chrome tab search to find and close a tab by site name."""
    import sys
    try:
        import pygetwindow as gw
    except ImportError:
        gw = None

    TITLE_KEYWORDS = {
        "youtube":   "youtube",
        "instagram": "instagram",
        "insta":     "instagram",
        "whatsapp":  "whatsapp",
        "linkedin":  "linkedin",
        "github":    "github",
        "amazon":    "amazon",
        "flipkart":  "flipkart",
        "netflix":   "netflix",
        "spotify":   "spotify",
        "chatgpt":   "chatgpt",
        "gpt":       "chatgpt",
        "gemini":    "gemini",
        "claude":    "claude",
        "google":    "google",
    }
    keyword = TITLE_KEYWORDS.get(site_name.lower(), site_name.lower())

    try:
        if sys.platform == "darwin":
            # Focus Google Chrome via AppleScript on Mac
            os.system("osascript -e 'tell application \"Google Chrome\" to activate'")
            time.sleep(1)
            # Open Chrome tab search with Command+Shift+A
            pyautogui.hotkey('command', 'shift', 'a')
            time.sleep(1.2)
            # Clear any existing text and type keyword
            pyautogui.hotkey('command', 'a')
            time.sleep(0.2)
            pyautogui.typewrite(keyword, interval=0.1)
            time.sleep(1.5)  # wait for results to appear
            # Press Enter to switch to first matching tab
            pyautogui.press('enter')
            time.sleep(1)
            # Close that tab with Command+W
            pyautogui.hotkey('command', 'w')
            time.sleep(0.5)
            return f"Closed {site_name} tab, Raj."
        else:
            if gw is None:
                return "Raj, pygetwindow is not installed/supported."
            # Find any Chrome window
            chrome_wins = [w for w in gw.getAllWindows()
                           if "chrome" in w.title.lower() and w.visible]
            if not chrome_wins:
                return f"Raj, Chrome is not open."

            # Focus Chrome window
            win = chrome_wins[0]
            win.restore()
            win.activate()
            time.sleep(1)

            # Open Chrome tab search with Ctrl+Shift+A
            pyautogui.hotkey('ctrl', 'shift', 'a')
            time.sleep(1.2)

            # Clear any existing text and type keyword
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.typewrite(keyword, interval=0.1)
            time.sleep(1.5)  # wait for results to appear

            # Press Enter to switch to first matching tab
            pyautogui.press('enter')
            time.sleep(1)

            # Close that tab
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(0.5)
            return f"Closed {site_name} tab, Raj."

    except Exception as e:
        return f"Raj, couldn't close {site_name}: {str(e)}"

def _parse_action(cmd: str):
    """Returns 'video_call', 'voice_call', or 'message'."""
    if any(p in cmd for p in ["video call", "video chat"]):
        return "video_call"
    if any(p in cmd for p in ["voice call", "audio call", "call ", "ring "]):
        return "voice_call"
    return "message"

def _parse_person_and_message(cmd: str):
    """Extract person name and message from command."""
    person = None
    message = None
    # Extract message after 'saying', 'say', or 'message' keyword
    for kw in ["saying", "say"]:
        if kw in cmd:
            parts = cmd.split(kw)
            message = parts[-1].strip()
            cmd = parts[0]
            break
    # Extract person name
    for kw in ["message to", "send to", "chat with", "open chat with", "dm to", "dm",
               "call to", "video call to", "voice call to", "to"]:
        if kw in cmd:
            person = cmd.split(kw)[-1].strip()
            for noise in ["on whatsapp", "on instagram", "on insta", "whatsapp",
                          "instagram", "insta", "and", "send", "please",
                          "voice", "video", "audio", "call"]:
                person = person.replace(noise, "").strip()
            break
    return person, message

def extract_automation_params(command: str, action_type: str) -> dict:
    """Uses Groq Llama-3 to extract exact arguments for automation tasks."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return {}

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Extract the target parameters from the user's desktop automation command.
        User Command: "{command}"
        Action Type: "{action_type}"

        Rules for extraction:
        - If action_type is "instagram": Extract "username" (the clean username like 'avneetkaur_13' without spaces, 'of', 'profile', or noise) and "message" (if any).
        - If action_type is "whatsapp": Extract "person" (the contact name like 'Raj' or '+91...') and "message" (if any).
        - If action_type is "youtube": Extract "query" (what they want to search or play) and "is_search" (true if they said 'search', false if they said 'play' or 'watch').

        Respond strictly in JSON format matching the action type keys.
        Example for instagram:
        {{
          "username": "avneetkaur_13",
          "message": ""
        }}
        """
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {}


def reflect_and_fix_automation(error_msg: str, current_strategy: str) -> str:
    """Uses Groq Llama-3 to reflect on the automation failure and suggest a fallback strategy."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return "fallback"
    
    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Our desktop automation agent encountered an error during controlling Chrome or apps.
        Current attempted action: {current_strategy}
        Error message: {error_msg}

        Reflect on why this failed and choose the best recovery strategy from:
        - "retry_with_longer_wait": If it's a timing issue where elements didn't load.
        - "focus_and_alt_tab": If the browser lost active focus and we need to activate the window again.
        - "use_direct_url": If GUI navigation/search failed but we can just jump to the direct URL.
        - "fail": If it's an unrecoverable crash.

        Respond with a clean JSON block:
        {{
          "reflection": "Brief explanation of why it failed.",
          "strategy": "one of the strategies"
        }}
        """
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        data = json.loads(response.choices[0].message.content)
        print(f"[Reflection] {data.get('reflection')}")
        return data.get("strategy", "fallback")
    except Exception:
        return "fallback"


def _whatsapp_action(person: str, message: str, action: str) -> str:
    """Open WhatsApp Web, wait for load, search contact in search bar, then message/call with self-correction."""
    import pygetwindow as gw

    attempt = 0
    max_attempts = 2
    wait_time = 12

    while attempt < max_attempts:
        try:
            # Check if WhatsApp Web is already open in Chrome
            wa_open = any("whatsapp" in w.title.lower() for w in gw.getAllWindows() if w.visible)

            if wa_open:
                # Focus existing WhatsApp tab via Chrome tab search
                chrome_wins = [w for w in gw.getAllWindows()
                               if "chrome" in w.title.lower() and w.visible]
                if chrome_wins:
                    chrome_wins[0].restore()
                    chrome_wins[0].activate()
                    time.sleep(0.8)
                    pyautogui.hotkey('ctrl', 'shift', 'a')
                    time.sleep(1)
                    pyautogui.typewrite('whatsapp', interval=0.1)
                    time.sleep(1)
                    pyautogui.press('enter')
                    time.sleep(1.5)
            else:
                # Open WhatsApp Web fresh
                webbrowser.open("https://web.whatsapp.com/")
                time.sleep(wait_time)

            # Use Alt+/ to focus the WhatsApp contact search bar
            pyautogui.hotkey('alt', '/')
            time.sleep(1.5)

            # Clear and type contact name
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.typewrite(_safe_typewrite(person), interval=0.1)
            time.sleep(3)  # Wait for search results

            # Press Down arrow to select first result, then Enter to open chat
            pyautogui.press('down')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)

            if action == "video_call":
                pyautogui.hotkey('alt', 'shift', 'v')
                time.sleep(1)
                return f"Raj, starting video call with {person} on WhatsApp."

            elif action == "voice_call":
                pyautogui.hotkey('alt', 'shift', 'p')
                time.sleep(1)
                return f"Raj, starting voice call with {person} on WhatsApp."

            else:  # message
                # Click message input — use Tab to focus it
                pyautogui.press('tab')
                time.sleep(0.5)
                if message:
                    pyautogui.typewrite(_safe_typewrite(message), interval=0.07)
                    time.sleep(0.3)
                    pyautogui.press('enter')
                    return f"Raj, message sent to {person} on WhatsApp."
                return f"Raj, opened WhatsApp chat with {person}."
        except Exception as e:
            attempt += 1
            if attempt >= max_attempts:
                raise e
            
            # Reflect on the failure using Llama-3
            strategy = reflect_and_fix_automation(str(e), "whatsapp message typing")
            print(f"[Self-Correction] Strategy recommended: {strategy}")
            if strategy == "retry_with_longer_wait":
                wait_time += 8  # wait longer for WhatsApp Web to load
                time.sleep(2)
            elif strategy == "focus_and_alt_tab":
                # Try to re-focus Chrome window explicitly
                chrome_wins = [w for w in gw.getAllWindows() if "chrome" in w.title.lower() and w.visible]
                if chrome_wins:
                    chrome_wins[0].restore()
                    chrome_wins[0].activate()
                time.sleep(2)
            else:
                # Direct fallback (webbrowser reload)
                webbrowser.open("https://web.whatsapp.com/")
                time.sleep(15)

def _instagram_action(person: str, message: str) -> str:
    """Open Instagram DMs, search person, select first result, open chat, type and send."""
    webbrowser.open("https://www.instagram.com/direct/new/")
    time.sleep(10)  # Wait for Instagram DM new chat page to fully load

    # Search box is auto-focused on /direct/new/
    pyautogui.typewrite(_safe_typewrite(person), interval=0.1)
    time.sleep(3)  # Wait for search results

    # Select first result with arrow down then Enter
    pyautogui.press('down')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(1)

    # Click the "Next" / "Chat" button to open conversation
    pyautogui.hotkey('tab')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(3)  # Wait for chat to open

    if message:
        pyautogui.typewrite(_safe_typewrite(message), interval=0.07)
        time.sleep(0.5)
        pyautogui.press('enter')
        return f"Raj, message '{message}' sent to {person} on Instagram."
    return f"Raj, opened Instagram DM with {person}."

def execute_automation(command: str) -> str:
    cmd = command.lower().strip()
    try:

        # --- Open VS Code ---
        if "open vs code" in cmd or "open vscode" in cmd or "launch vs code" in cmd:
            return _open_vscode()

        # --- Close any website tab ---
        elif "close" in cmd:
            for site, domain in SITE_KEYWORDS.items():
                if site in cmd:
                    return _close_tab_by_name(site)
            if "tab" in cmd:
                return _close_tab_by_name("current")
            return "Raj, I couldn't find a matching tab to close."

        # --- Open any website ---
        elif "open" in cmd and ("website" in cmd or "site" in cmd or "page" in cmd):
            # Extract site name
            site = cmd
            for noise in ["open", "website", "site", "page", "the", "please"]:
                site = site.replace(noise, "").strip()
            # Known sites
            known = {
                "amazon": "https://www.amazon.in",
                "flipkart": "https://www.flipkart.com",
                "air india": "https://www.airindia.com",
                "indigo": "https://www.goindigo.in",
                "spicejet": "https://www.spicejet.com",
                "netflix": "https://www.netflix.com",
                "google": "https://www.google.com",
                "gmail": "https://mail.google.com",
                "twitter": "https://www.twitter.com",
                "facebook": "https://www.facebook.com",
                "reddit": "https://www.reddit.com",
                "wikipedia": "https://www.wikipedia.org",
                "irctc": "https://www.irctc.co.in",
                "makemytrip": "https://www.makemytrip.com",
                "zomato": "https://www.zomato.com",
                "swiggy": "https://www.swiggy.com",
            }
            matched_url = next((v for k, v in known.items() if k in site), None)
            if matched_url:
                _open_and_wait(matched_url)
                return f"Opening {site.strip()}, Raj."
            else:
                # Try as a direct URL
                url = f"https://www.{site.replace(' ', '')}.com"
                _open_and_wait(url)
                return f"Opening {site.strip()}, Raj."

        # --- Google ---
        elif "google" in cmd:
            # Extract search query
            query = ""
            for kw in ["search", "search for", "find", "look up"]:
                if kw in cmd:
                    query = cmd.split(kw)[-1].strip()
                    for noise in ["on google", "google", "please", "in google"]:
                        query = query.replace(noise, "").strip()
                    break
            if query:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                _open_and_wait(url, wait=2)
                return f"Raj, searching Google for '{query}'."
            _open_and_wait("https://www.google.com", wait=2)
            return "Opening Google, Raj."

        # --- LinkedIn ---
        elif "linkedin" in cmd:
            person = ""
            for kw in ["linkedin of", "linkedin profile of", "open linkedin of", "search linkedin for", "find on linkedin"]:
                if kw in cmd:
                    person = cmd.split(kw)[-1].strip()
                    break
            if person and person not in ["my", "mine", "raj"]:
                url = f"https://www.linkedin.com/search/results/people/?keywords={person.replace(' ', '%20')}"
                _open_and_wait(url)
                return f"Searching LinkedIn for {person}, Raj."
            _open_and_wait(PROFILES["linkedin"])
            return "Opening your LinkedIn profile, Raj."

        # --- GitHub ---
        elif "github" in cmd or "git hub" in cmd:
            # Open all repos
            if any(kw in cmd for kw in ["all repo", "all repos", "all repositories", "my repos", "my repositories"]):
                return _open_all_github_repos()

            repo_name = ""
            for kw in ["open repo", "open repository", "open github repo", "repo", "repository"]:
                if kw in cmd:
                    repo_name = cmd.split(kw)[-1].strip()
                    for noise in ["on github", "github", "git hub", "please", "open"]:
                        repo_name = repo_name.replace(noise, "").strip()
                    break
            if repo_name:
                _open_and_wait(f"https://github.com/RAJ-15012006/{repo_name.replace(' ', '-')}")
                return f"Opening {repo_name} repo on GitHub, Raj."
            _open_and_wait(PROFILES["github"])
            return "Opening your GitHub profile, Raj."

        # --- Portfolio ---
        elif "portfolio" in cmd:
            _open_and_wait(PROFILES["portfolio"])
            return "Opening your portfolio, Raj."

        # --- AI Assistants: ChatGPT, Gemini, Claude ---
        elif any(ai in cmd for ai in ["chatgpt", "chat gpt", "gpt", "gemini", "claude"]):
            # Detect which AI
            ai_key = next((k for k in AI_ASSISTANTS if k in cmd), "chatgpt")
            ai_info = AI_ASSISTANTS[ai_key]
            ai_label = ai_key.capitalize()

            # Extract query after keywords like 'ask', 'search', 'find', 'in', 'on'
            query = ""
            for kw in ["ask", "search", "find", "tell", "type", "write", "in", "on"]:
                if kw in cmd:
                    candidate = cmd.split(kw)[-1].strip()
                    # Strip AI name noise from extracted query
                    for noise in list(AI_ASSISTANTS.keys()) + ["chat gpt", "please", "about"]:
                        candidate = candidate.replace(noise, "").strip()
                    if candidate:
                        query = candidate
                        break

            # Open the AI site
            webbrowser.open(ai_info["url"])
            time.sleep(ai_info["wait"])  # Wait for page to fully load

            if query:
                # Type the query into the input box
                pyautogui.typewrite(query, interval=0.07)
                time.sleep(0.5)
                pyautogui.press('enter')
                return f"Raj, asked {ai_label}: '{query}'."
            return f"Opening {ai_label}, Raj."

        # --- YouTube ---
        elif "youtube" in cmd:
            params = extract_automation_params(command, "youtube")
            query = params.get("query", "")
            is_search = params.get("is_search", False)

            if not query:
                is_search = "search" in cmd  # search = show results; play/watch = autoplay
                for kw in ["search", "play", "watch"]:
                    if kw in cmd:
                        query = cmd.split(kw)[-1].replace("on youtube", "").replace("youtube", "").strip()
                        break
            if query:
                if is_search:
                    # Open YouTube search results page
                    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                    _open_and_wait(url, wait=2)
                    return f"Raj, showing YouTube search results for '{query}'."
                else:
                    # Autoplay first result
                    pywhatkit.playonyt(query)
                    return f"Playing {query} on YouTube, Raj."
            _open_and_wait("https://www.youtube.com")
            return "Opening YouTube, Raj."

        # --- Play song ---
        elif "play" in cmd:
            song = cmd.split("play")[-1].strip()
            if song:
                pywhatkit.playonyt(song)
                return f"Playing {song} on YouTube, Raj."
            return "Raj, what should I play?"

        # --- WhatsApp ---
        elif "whatsapp" in cmd or ("send message" in cmd and "insta" not in cmd):
            params = extract_automation_params(command, "whatsapp")
            person = params.get("person", "")
            message = params.get("message", "")
            action = _parse_action(cmd)

            if not person:
                person, message = _parse_person_and_message(cmd)

            if person:
                return _whatsapp_action(person, message or "", action)
            _open_and_wait("https://web.whatsapp.com/", wait=12)
            return "Opening WhatsApp Web, Raj."

        # --- Instagram ---
        elif "instagram" in cmd or "insta" in cmd:
            params = extract_automation_params(command, "instagram")
            username = params.get("username", "")
            message = params.get("message", "")

            # Heuristic fallbacks if extraction fails
            if not username:
                is_search = any(kw in cmd for kw in ["search", "find", "look up", "show me", "go to", "open"])
                for kw in ["search", "find", "look up", "show me", "go to", "open"]:
                    if kw in cmd:
                        candidate = cmd.split(kw)[-1].strip()
                        for noise in ["on instagram", "on insta", "instagram", "insta",
                                      "profile", "account", "please", "page", "of"]:
                            candidate = candidate.replace(noise, "").strip()
                        if candidate:
                            username = candidate
                            break

            is_dm = any(kw in cmd for kw in ["send", "message", "dm", "chat", "say", "saying"]) or bool(message)

            if username and not is_dm:
                # Open Instagram profile directly by exact username
                slug = username.replace(" ", "").replace("of", "").strip()
                url = f"https://www.instagram.com/{slug}/"
                _open_and_wait(url, wait=3)
                return f"Raj, opening Instagram profile of {username}."

            # DM flow
            if username and is_dm:
                return _instagram_action(username, message or "")

            # Plain open — just open your profile
            _open_and_wait("https://www.instagram.com/raj.k.18/")
            return "Opening your Instagram, Raj."

        # --- Google Search ---
        elif "search" in cmd and "google" in cmd:
            query = cmd.split("search")[1].replace("on google", "").strip()
            pywhatkit.search(query)
            return f"Searching Google for {query}, Raj."

        # --- Reminders ---
        elif any(word in cmd for word in ["remind", "note", "schedule"]):
            task = cmd
            for prefix in ["remind me to", "remind me", "note that", "note down", "schedule a", "schedule"]:
                if prefix in cmd:
                    task = cmd.split(prefix)[-1].strip()
                    break
            with open(SCHEDULE_FILE, "a") as f:
                f.write(task + "\n")
            return f"Raj, I have added '{task}' to your schedule."

        else:
            return "Raj, I have attempted to automate that task, but no specific module was engaged."

    except Exception as e:
        return f"Raj, I encountered an issue: {str(e)}"
