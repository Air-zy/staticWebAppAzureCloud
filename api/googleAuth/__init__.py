import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from urllib.parse import urlencode
import azure.functions as func

REDIRECT_URI = "https://lemon-beach-08663e51e.azurestaticapps.net/api/googleCallback"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def main(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=CORS_HEADERS)

    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    return func.HttpResponse(
        status_code=302,
        headers={"Location": google_auth_url, **CORS_HEADERS},
    )
