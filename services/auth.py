import base64
import binascii
from flask import request
from utils import encode_auth_headers


def get_auth_headers():
    """Extract authentication from request and return headers dict along with credentials"""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    login, api_key = extract_auth_from_request()

    if login and api_key:
        headers["Authorization"] = f"Token {encode_auth_headers(login, api_key)}"

    return headers, login, api_key


def extract_auth_from_request():
    """
    Extract login and api_key from multiple possible sources:
    1. HTTP Basic Authorization header
    2. Query string parameters (?login=...&api_key=...)
    3. Form data (POST body)
    4. JSON body
    """
    login = None
    api_key = None

    # 1. Authorization header (Basic Auth)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        try:
            encoded_credentials = auth_header.split(" ", 1)[1].strip()
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
            if ":" in decoded:
                login, api_key = decoded.split(":", 1)
        except (binascii.Error, UnicodeDecodeError, ValueError):
            pass

    # 2. Query parameters
    if not login or not api_key:
        if "login" in request.args and "api_key" in request.args:
            login = request.args.get("login")
            api_key = request.args.get("api_key")

    # 3. Form data
    if not login or not api_key:
        if request.form:
            login = request.form.get("login", login)
            api_key = request.form.get("api_key", api_key)

    # 4. JSON payload
    if not login or not api_key:
        json_data = request.get_json(silent=True)
        if isinstance(json_data, dict):
            login = json_data.get("login", login)
            api_key = json_data.get("api_key", api_key)

    return login, api_key
