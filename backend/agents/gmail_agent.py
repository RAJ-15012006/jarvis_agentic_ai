"""
gmail_agent.py — JARVIS Gmail Voice Control
============================================
Allows Raj to read, summarize, compose, and delete emails by voice.

SETUP REQUIRED (one-time):
  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable Gmail API
  3. Create OAuth 2.0 Desktop credentials → Download as 'credentials.json'
  4. Place 'credentials.json' in backend/agents/face_data/gmail_credentials.json
  5. First run will open a browser for OAuth consent → saves token.json

Voice commands:
  - "read my emails" / "check my inbox"
  - "read unread emails"
  - "summarize my emails"
  - "send email to [person] saying [message]"
  - "delete latest email"
  - "how many unread emails"
"""

import os
import json
import base64
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CREDS_DIR = os.path.join(os.path.dirname(__file__), "face_data")
CREDENTIALS_FILE = os.path.join(CREDS_DIR, "gmail_credentials.json")
TOKEN_FILE = os.path.join(CREDS_DIR, "gmail_token.json")

GMAIL_TRIGGERS = [
    "read my email", "check my email", "check my inbox", "read my inbox",
    "unread email", "unread emails", "email count", "how many emails",
    "summarize my email", "latest email", "send email", "compose email",
    "email to", "write email", "delete email", "delete latest email",
    "new email", "any email", "my emails",
]

def is_gmail_command(command: str) -> bool:
    cmd = command.lower()
    return any(t in cmd for t in GMAIL_TRIGGERS)


def _get_gmail_service():
    """Authenticate and return Gmail API service object."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    return None, (
                        "Sir, Gmail credentials not found. Please place your "
                        "gmail_credentials.json file in backend/agents/face_data/ "
                        "and restart JARVIS."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)
        return service, None

    except ImportError:
        return None, (
            "Sir, Google API libraries not installed. "
            "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
        )
    except Exception as e:
        return None, f"Gmail auth failed: {str(e)}"


def _decode_email_body(payload) -> str:
    """Recursively extract text body from email payload."""
    body = ""
    if payload.get("mimeType", "").startswith("text/plain"):
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
    elif "parts" in payload:
        for part in payload["parts"]:
            body += _decode_email_body(part)
    return body


def _summarize_email_with_llm(email_text: str, subject: str) -> str:
    """Use LLaMA to summarize a long email."""
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return email_text[:300] + "..."

        client = Groq(api_key=api_key)
        prompt = f"""Summarize this email for Raj (address him as 'Sir') in 2-3 sentences.
Subject: {subject}
Body: {email_text[:3000]}

Give a direct, concise summary."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return email_text[:300] + "..."


def read_unread_emails(max_emails: int = 5) -> str:
    """Read and summarize unread emails."""
    service, error = _get_gmail_service()
    if error:
        return error

    try:
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=max_emails
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            return "No unread emails in your inbox, Sir."

        summaries = []
        for i, msg_ref in enumerate(messages[:max_emails], 1):
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            subject = headers.get("Subject", "(No Subject)")
            sender = headers.get("From", "Unknown")
            # Strip email address from display
            sender_name = re.sub(r"<.*?>", "", sender).strip() or sender

            body = _decode_email_body(msg["payload"])
            summary = _summarize_email_with_llm(body, subject)

            summaries.append(
                f"{i}. From: {sender_name}\n"
                f"   Subject: {subject}\n"
                f"   Summary: {summary}"
            )

        count = len(messages)
        header = f"📧 You have {count} unread email(s), Sir:\n\n"
        return header + "\n\n".join(summaries)

    except Exception as e:
        return f"Raj, I couldn't read your emails: {str(e)}"


def get_unread_count() -> str:
    """Return only the count of unread emails."""
    service, error = _get_gmail_service()
    if error:
        return error
    try:
        results = service.users().messages().list(
            userId="me", labelIds=["INBOX", "UNREAD"]
        ).execute()
        count = results.get("resultSizeEstimate", 0)
        if count == 0:
            return "Your inbox is clear, Sir. No unread emails."
        return f"You have approximately {count} unread email(s), Sir."
    except Exception as e:
        return f"Couldn't count emails: {str(e)}"


def send_email(to_address: str, subject: str, body: str) -> str:
    """Compose and send an email."""
    service, error = _get_gmail_service()
    if error:
        return error
    try:
        message = MIMEMultipart()
        message["to"] = to_address
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

        return f"✅ Email sent to {to_address} with subject '{subject}', Sir."
    except Exception as e:
        return f"Raj, email failed to send: {str(e)}"


def _parse_send_command(command: str) -> tuple:
    """Extract (to, subject, body) from a voice command."""
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return None, None, None

        client = Groq(api_key=api_key)
        prompt = f"""Extract email details from this voice command: "{command}"

Return ONLY valid JSON with keys: "to", "subject", "body"
Example: {{"to": "mom@email.com", "subject": "Hello", "body": "Hey Mom, just checking in."}}
If 'to' is a name like 'Mom', use it as-is."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("to"), data.get("subject", "Message from Raj"), data.get("body", "")
    except Exception:
        return None, None, None


def handle_gmail_command(command: str) -> str:
    """Main dispatcher for Gmail voice commands."""
    cmd = command.lower().strip()

    if any(w in cmd for w in ["count", "how many", "number of"]):
        return get_unread_count()

    if any(w in cmd for w in ["send", "compose", "write", "email to"]):
        to, subject, body = _parse_send_command(command)
        if to and body:
            return send_email(to, subject or "Message from JARVIS", body)
        return "Raj, please say: 'Send email to [person] saying [message]'"

    # Default: read unread emails
    return read_unread_emails(max_emails=5)
