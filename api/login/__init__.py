import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
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

    if not email or not password:
        return func.HttpResponse(
            json.dumps({"error": "Invalid credentials"}),
            status_code=401,
            mimetype="application/json",
            headers=CORS_HEADERS,
        )

    user = db.get_user_by_email(email)
    if not user or not user.get("password_hash") or not auth.verify_password(password, user["password_hash"]):
        return func.HttpResponse(
            json.dumps({"error": "Invalid credentials"}),
            status_code=401,
            mimetype="application/json",
            headers=CORS_HEADERS,
        )

    token = auth.create_token(user["id"], user["email"], user["name"])
    return func.HttpResponse(
        json.dumps({"token": token, "name": user["name"], "email": user["email"]}),
        status_code=200,
        mimetype="application/json",
        headers=CORS_HEADERS,
    )
