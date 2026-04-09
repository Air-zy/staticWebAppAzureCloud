import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import base64
import uuid
import requests as http_requests
from datetime import datetime, timezone
import azure.functions as func
from shared import db, auth

REDIRECT_URI = "https://lemon-beach-08663e51e.azurestaticapps.net/api/googleCallback"


def _decode_id_token_payload(id_token: str) -> dict:
    # Decode without signature verification — token was received directly from Google over HTTPS
    payload_part = id_token.split(".")[1]
    # Add padding if needed
    padding = 4 - len(payload_part) % 4
    if padding != 4:
        payload_part += "=" * padding
    return json.loads(base64.urlsafe_b64decode(payload_part))


def main(req: func.HttpRequest) -> func.HttpResponse:
    code = req.params.get("code")
    if not code:
        return func.HttpResponse(
            status_code=302,
            headers={"Location": "/?error=oauth_failed"},
        )

    # Exchange code for tokens
    token_resp = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    if not token_resp.ok:
        return func.HttpResponse(
            status_code=302,
            headers={"Location": "/?error=oauth_failed"},
        )

    token_data = token_resp.json()
    id_token = token_data.get("id_token")
    if not id_token:
        return func.HttpResponse(
            status_code=302,
            headers={"Location": "/?error=oauth_failed"},
        )

    try:
        payload = _decode_id_token_payload(id_token)
    except Exception:
        return func.HttpResponse(
            status_code=302,
            headers={"Location": "/?error=oauth_failed"},
        )

    google_id = payload.get("sub")
    email = (payload.get("email") or "").lower()
    name = payload.get("name") or email

    if not email or not google_id:
        return func.HttpResponse(
            status_code=302,
            headers={"Location": "/?error=oauth_failed"},
        )

    existing = db.get_user_by_email(email)
    if existing:
        user_id = existing["id"]
        existing["google_id"] = google_id
        existing["provider"] = "google"
        db.upsert_user(existing)
    else:
        user_id = str(uuid.uuid4())
        db.upsert_user({
            "id": user_id,
            "email": email,
            "name": name,
            "password_hash": None,
            "provider": "google",
            "google_id": google_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    jwt_token = auth.create_token(user_id, email, name)
    return func.HttpResponse(
        status_code=302,
        headers={"Location": f"/?token={jwt_token}"},
    )
