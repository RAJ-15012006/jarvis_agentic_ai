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
        "close all tabs", "close every tab", "close all browser tabs"
    ]
    
    web_keywords = [
        "weather", "temperature", "forecast", "stock", "price", "nifty", "sensex", "bitcoin", "crypto",
        "score", "match", "gold", "silver", "rate", "dollar", "euro", "rupee", "forex", "news", 
        "headlines", "flight", "train", "hotel", "map", "direction", "navigate", "route", "buy", "shop"
    ]
    
    system_keywords = [
        "shutdown", "shut down", "restart", "reboot", "sleep", "hibernate", "lock", "screenshot", "volume",
        "brightness", "mute", "unmute", "notepad", "type", "turn", "folder", "script",
        "command", "battery", "disk", "python", "code", "run", "power off", "turn off"
    ]

    # Check for multi-word phrase matches first
    for kw in automation_keywords:
        if len(kw.split()) > 1 and kw in cmd:
            return {"agent": "automation", "command": command}
    for kw in system_keywords:
        if len(kw.split()) > 1 and kw in cmd:
            return {"agent": "system", "command": command}
    for kw in web_keywords:
        if len(kw.split()) > 1 and kw in cmd:
            return {"agent": "web", "command": command}

    # Fall back to word-by-word matches
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
    
    # Explicitly catch crew requests before LLM to save latency if possible, or let LLM decide
    # We support the Crew Agent for newsletters and tech digests
    if any(w in cmd for w in ["crew", "newsletter", "tech digest", "weekly digest", "collaboration"]):
        return {"agent": "crew", "command": command}

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return fallback_route(command)

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Analyze the following user command: "{command}"
        You must route it to one of these agents:
        1. "automation": For browser/website automation, opening social media profiles (e.g., "open instagram profile of avneetkaur_13", "play rain sounds on youtube", "open whatsapp"), or specific online search portals like Amazon, Netflix, ChatGPT.
        2. "system": For operating system commands (volume, brightness, restart, screenshot, notepad, lock screen, shutdown), folder creation, file writing, script execution, and shell operations.
        3. "web": For real-time web searches or live queries that need dynamic fetching (weather, stocks, currency rates, news, map directions, train/flight search).
        4. "crew": For complex research requests, newsletter creation, weekly digest generation, or drafting comprehensive reports (e.g. "create a weekly tech newsletter digest", "give me a dynamic digest of latest AI trends").
        5. "chat": For general conversations, direct answers, questions that don't need real-time data, or when none of the above apply.

        Respond strictly in JSON format with two keys:
        - "agent": one of ["automation", "system", "web", "crew", "chat"]
        - "command": the refined/cleaned command (or original if clean enough)
        
        Example JSON:
        {{
          "agent": "automation",
          "command": "open instagram profile avneetkaur_13"
        }}
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        res_data = json.loads(response.choices[0].message.content)
        # Validate keys
        if "agent" in res_data and "command" in res_data:
            return res_data
        return fallback_route(command)
    except Exception:
        return fallback_route(command)
