"""
Integration routes — connect/manage external services (Gmail, Slack, etc.)
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.integrations import gmail

router = APIRouter()


# ── Status ──────────────────────────────────────────────

@router.get("/status")
async def integration_status():
    """Check which integrations are available and connected."""
    return {
        "gmail": {
            "configured": gmail.is_configured(),
            "connected": gmail.is_connected(),
        },
        # Future: slack, calendar, etc.
    }


# ── Gmail OAuth Flow ────────────────────────────────────

@router.get("/gmail/connect")
async def gmail_connect():
    """Start the Gmail OAuth flow. Returns the URL to redirect the user to."""
    if not gmail.is_configured():
        return {
            "error": "Gmail not configured. Place your Google credentials at ~/.aria/google_credentials.json",
            "help": (
                "1. Go to console.cloud.google.com\n"
                "2. Create a project and enable Gmail API\n"
                "3. Create OAuth credentials (Desktop app)\n"
                "4. Download the JSON and save as ~/.aria/google_credentials.json"
            ),
        }

    auth_url = gmail.get_auth_url()
    if not auth_url:
        return {"error": "Failed to generate auth URL"}

    return {"auth_url": auth_url}


@router.get("/gmail/callback")
async def gmail_callback(code: str = ""):
    """OAuth callback — exchanges the auth code for tokens."""
    if not code:
        return HTMLResponse(
            "<h2>Authorization failed</h2><p>No authorization code received.</p>",
            status_code=400,
        )

    success = gmail.handle_callback(code)
    if success:
        # Show a success page that auto-closes
        return HTMLResponse("""
        <html>
        <body style="display:flex;align-items:center;justify-content:center;height:100vh;background:#0a0a0a;color:white;font-family:system-ui">
          <div style="text-align:center">
            <h1 style="color:#7c3aed">✓ Gmail Connected!</h1>
            <p style="color:#888">You can close this tab and return to Aria.</p>
            <script>setTimeout(()=>window.close(),2000)</script>
          </div>
        </body>
        </html>
        """)
    return HTMLResponse("<h2>Authorization failed</h2>", status_code=400)


@router.get("/gmail/disconnect")
async def gmail_disconnect():
    """Disconnect Gmail by removing the token."""
    import os
    token_path = gmail.TOKEN_PATH
    if token_path.exists():
        os.remove(token_path)
    gmail._gmail_service = None
    gmail._credentials = None
    return {"disconnected": True}


# ── Gmail API ───────────────────────────────────────────

@router.get("/gmail/emails")
async def list_emails(q: str = "", max_results: int = 15, label: str = "INBOX"):
    """List emails. Optional query for search."""
    return await gmail.list_emails(query=q, max_results=max_results, label=label)


@router.get("/gmail/emails/{email_id}")
async def read_email(email_id: str):
    """Read a single email by ID."""
    return await gmail.read_email(email_id)


@router.post("/gmail/send")
async def send_email(req: dict):
    """Send an email. Body: {to, subject, body}"""
    return await gmail.send_email(
        to=req.get("to", ""),
        subject=req.get("subject", ""),
        body=req.get("body", ""),
    )


@router.get("/gmail/profile")
async def gmail_profile():
    """Get Gmail profile info."""
    return await gmail.get_profile_info()
