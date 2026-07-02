import os
import webbrowser
import tempfile
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "built_sites")
os.makedirs(BUILD_DIR, exist_ok=True)

BUILDER_PROMPT = """You are an expert web developer. Generate a complete, beautiful, single-file HTML website based on the user's description.

Rules:
- Output ONLY raw HTML code — no explanation, no markdown, no ```html blocks, just pure HTML
- Everything must be in one single HTML file — inline CSS in <style> and inline JS in <script>
- Make it visually stunning — use modern design, gradients, animations, good typography
- Use Google Fonts via CDN link
- Make it fully responsive (mobile + desktop)
- Add smooth animations and hover effects
- Use a professional color scheme matching the website purpose
- Include all sections the user asks for
- Make it production-ready quality
- DO NOT use any external JS frameworks — pure HTML/CSS/JS only
"""

def build_website(prompt: str) -> str:
    """Generate a complete website from prompt using Groq, save and open in browser."""
    try:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return "Raj, GROQ_API_KEY is not set. Cannot build website."

        client = Groq(api_key=api_key)

        # Generate website code
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": BUILDER_PROMPT},
                {"role": "user", "content": f"Build me a website: {prompt}"}
            ],
            max_tokens=4000,
            temperature=0.7
        )

        html_code = response.choices[0].message.content.strip()

        # Strip any accidental markdown code fences
        if html_code.startswith("```"):
            lines = html_code.split("\n")
            html_code = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            )

        # Ensure it starts with <!DOCTYPE or <html
        if not html_code.lower().startswith(("<!doctype", "<html")):
            html_code = "<!DOCTYPE html>\n" + html_code

        # Save to built_sites folder with a clean filename
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in prompt[:40])
        safe_name = safe_name.strip().replace(" ", "_") or "jarvis_site"
        filepath = os.path.join(BUILD_DIR, f"{safe_name}.html")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_code)

        # Open in browser
        from pathlib import Path
        webbrowser.open(Path(filepath).as_uri())

        return f"Raj, your website has been built and opened in the browser. Saved as {safe_name}.html."

    except Exception as e:
        return f"Raj, I encountered an error while building the website: {str(e)}"


def is_build_request(command: str) -> bool:
    """Detect if user wants to build a website."""
    cmd = command.lower()
    build_triggers = [
        "build me a website", "build a website", "create a website",
        "make a website", "build me a webpage", "create a webpage",
        "make a webpage", "build website", "create website",
        "make website", "design a website", "design website",
        "build me a landing page", "create a landing page",
        "make a portfolio website", "build a portfolio",
        "build me an app", "create a web app", "make a web page",
    ]
    return any(t in cmd for t in build_triggers)


def extract_build_prompt(command: str) -> str:
    """Extract the website description from the command."""
    cmd = command.lower()
    for trigger in [
        "build me a website", "build a website", "create a website",
        "make a website", "build me a webpage", "create a webpage",
        "make a webpage", "build website", "create website",
        "make website", "design a website", "design website",
        "build me a landing page", "create a landing page",
        "build me an app", "create a web app", "make a web page",
    ]:
        if trigger in cmd:
            after = command[cmd.index(trigger) + len(trigger):].strip()
            # Clean connectors
            for noise in ["that", "which", "with", "for", "about", "on", "of"]:
                if after.lower().startswith(noise + " "):
                    after = after[len(noise):].strip()
            return after if after else command
    return command
