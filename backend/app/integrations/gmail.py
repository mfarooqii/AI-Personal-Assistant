"""
Gmail Integration — OAuth2 flow + read/search/send emails.

Setup:
1. User creates a Google Cloud project and enables Gmail API
2. Downloads client_secret.json to ~/.aria/google_credentials.json
3. Aria runs the OAuth flow via browser redirect
4. Refresh token is stored in the database (encrypted in future)

This is the simplest possible path for a non-technical user:
- Go to console.cloud.google.com → create project → enable Gmail API
- Download credentials → drop in ~/.aria/
- Click "Connect Gmail" in Aria → browser opens → authorize → done
"""

import os
import json
import base64
import email as email_lib
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings

# Lazy imports — only loaded when Gmail is actually used
_gmail_service = None
_credentials = None

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

CREDENTIALS_PATH = settings.DATA_DIR / "google_credentials.json"
TOKEN_PATH = settings.DATA_DIR / "google_token.json"


def is_configured() -> bool:
    """Check if Google credentials file exists."""
    return CREDENTIALS_PATH.exists()


def is_connected() -> bool:
    """Check if we have a valid token (user has authorized)."""
    return TOKEN_PATH.exists()


def _get_service():
    """Get or create the Gmail API service."""
    global _gmail_service, _credentials

    if _gmail_service:
        # Check if credentials need refresh
        if _credentials and _credentials.expired and _credentials.refresh_token:
            from google.auth.transport.requests import Request
            _credentials.refresh(Request())
            _save_token(_credentials)
        return _gmail_service

    if not TOKEN_PATH.exists():
        return None

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    _credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if _credentials.expired and _credentials.refresh_token:
        from google.auth.transport.requests import Request
        _credentials.refresh(Request())
        _save_token(_credentials)

    _gmail_service = build("gmail", "v1", credentials=_credentials)
    return _gmail_service


def _save_token(creds):
    """Save token to disk."""
    TOKEN_PATH.write_text(creds.to_json())


def get_auth_url() -> Optional[str]:
    """Generate the OAuth2 authorization URL for the user to visit."""
    if not CREDENTIALS_PATH.exists():
        return None

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_PATH),
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/api/integrations/gmail/callback",
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def handle_callback(authorization_code: str) -> bool:
    """Exchange the auth code for tokens and save them."""
    if not CREDENTIALS_PATH.exists():
        return False

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_PATH),
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/api/integrations/gmail/callback",
    )
    flow.fetch_token(code=authorization_code)
    creds = flow.credentials
    _save_token(creds)

    global _gmail_service, _credentials
    _credentials = creds
    _gmail_service = None  # Force rebuild on next use

    return True


def _parse_message(msg: dict) -> dict:
    """Parse a Gmail API message into a clean dict."""
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

    # Get body text
    body = ""
    payload = msg.get("payload", {})

    def extract_text(part: dict) -> str:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        for sub in part.get("parts", []):
            result = extract_text(sub)
            if result:
                return result
        return ""

    body = extract_text(payload)
    if not body and payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Get labels
    label_ids = msg.get("labelIds", [])
    is_unread = "UNREAD" in label_ids

    return {
        "id": msg.get("id", ""),
        "thread_id": msg.get("threadId", ""),
        "subject": headers.get("subject", "(no subject)"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "body": body[:5000],  # Limit body size
        "is_unread": is_unread,
        "labels": label_ids,
    }


# ── Public API ──────────────────────────────────────────

async def list_emails(
    query: str = "",
    max_results: int = 15,
    label: str = "INBOX",
) -> dict:
    """List emails from Gmail."""
    service = _get_service()
    if not service:
        return {"error": "Gmail not connected. Please connect Gmail first.", "emails": []}

    try:
        q = query if query else f"label:{label}"
        results = service.users().messages().list(
            userId="me", q=q, maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg_ref in messages[:max_results]:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()
            emails.append(_parse_message(msg))

        return {
            "emails": emails,
            "total": results.get("resultSizeEstimate", len(emails)),
            "query": q,
        }
    except Exception as e:
        return {"error": str(e), "emails": []}


async def read_email(email_id: str) -> dict:
    """Read a single email by ID."""
    service = _get_service()
    if not service:
        return {"error": "Gmail not connected."}

    try:
        msg = service.users().messages().get(
            userId="me", id=email_id, format="full"
        ).execute()

        # Mark as read
        service.users().messages().modify(
            userId="me", id=email_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

        return _parse_message(msg)
    except Exception as e:
        return {"error": str(e)}


async def search_emails(query: str, max_results: int = 10) -> dict:
    """Search emails with Gmail search syntax."""
    return await list_emails(query=query, max_results=max_results)


async def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email."""
    service = _get_service()
    if not service:
        return {"error": "Gmail not connected."}

    try:
        message = email_lib.message.EmailMessage()
        message.set_content(body)
        message["To"] = to
        message["Subject"] = subject

        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me", body={"raw": encoded}
        ).execute()

        return {"sent": True, "message_id": result.get("id", "")}
    except Exception as e:
        return {"error": str(e), "sent": False}


async def get_profile_info() -> dict:
    """Get the user's Gmail profile."""
    service = _get_service()
    if not service:
        return {"error": "Gmail not connected."}

    try:
        profile = service.users().getProfile(userId="me").execute()
        return {
            "email": profile.get("emailAddress", ""),
            "total_messages": profile.get("messagesTotal", 0),
            "threads_total": profile.get("threadsTotal", 0),
        }
    except Exception as e:
        return {"error": str(e)}
