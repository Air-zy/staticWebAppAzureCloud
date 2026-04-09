import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import uuid
from datetime import datetime, timezone
import azure.functions as func
from shared import db, auth

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def main(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=CORS_HEADERS)

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
            headers=CORS_HEADERS,
        )

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    name = (body.get("name") or "").strip()

    if not email or not password or not name:
        return func.HttpResponse(
            json.dumps({"error": "email, password, and name are required"}),
            status_code=400,
            mimetype="application/json",
            headers=CORS_HEADERS,
        )

    if db.get_user_by_email(email):
        return func.HttpResponse(
            json.dumps({"error": "An account with this email already exists"}),
            status_code=409,
            mimetype="application/json",
            headers=CORS_HEADERS,
        )

    user_id = str(uuid.uuid4())
    doc = {
        "id": user_id,
        "email": email,
        "name": name,
        "password_hash": auth.hash_password(password),
        "provider": "email",
        "google_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.upsert_user(doc)

    token = auth.create_token(user_id, email, name)
    return func.HttpResponse(
        json.dumps({"token": token, "name": name, "email": email}),
        status_code=201,
        mimetype="application/json",
        headers=CORS_HEADERS,
    )
