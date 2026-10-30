"""Gmail OAuth refresh and MIME message delivery."""
import base64
from email.message import EmailMessage

import requests

from .http import request_json
from .settings import GmailSettings


def refresh_access_token(config: GmailSettings):
    """Exchange an OAuth refresh token without exposing credentials in errors."""
    for key, value in (
        ("GMAIL_CLIENT_ID", config.client_id),
        ("GMAIL_CLIENT_SECRET", config.client_secret),
        ("GMAIL_REFRESH_TOKEN", config.refresh_token),
        ("EMAIL_FROM", config.email_from),
        ("EMAIL_TO", config.email_to),
    ):
        if not value:
            raise RuntimeError(f"Missing Gmail environment variable: {key}")
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": config.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if not token_response.ok:
        raise RuntimeError(
            f"Gmail OAuth refresh failed (HTTP {token_response.status_code}); check OAuth credentials"
        )
    access_token = token_response.json().get("access_token")
    if not access_token:
        raise RuntimeError("Gmail OAuth refresh response has no access_token")
    return access_token


def build_message(subject, plain, rich, config: GmailSettings):
    """Create a MIME message without network or environment access."""
    message = EmailMessage()
    message["From"] = config.email_from
    message["To"] = config.email_to
    message["Subject"] = subject
    message.set_content(plain)
    message.add_alternative(rich, subtype="html")
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def send_gmail(subject, plain, rich, config: GmailSettings):
    """Send MIME mail via Gmail API; require Gmail message ID confirmation."""
    access_token = refresh_access_token(config)
    raw = build_message(subject, plain, rich, config)
    result = request_json(
        "POST",
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        data={"raw": raw},
    )
    if not result.get("id"):
        raise RuntimeError("Gmail did not return a message ID; delivery is unconfirmed")
    print(f'Gmail send confirmed; message ID: {result["id"]}')
    return result["id"]
