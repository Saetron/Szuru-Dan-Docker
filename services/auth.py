import base64
import binascii
from flask import request
from utils import encode_auth_headers


def get_auth_headers():
    """Extract authentication from request and return headers dict along with credentials"""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    login, api_key = extract_auth_from_request()

    if login and api_key:
        # Szurubooru authenticates username and password via HTTP Basic Auth
        headers["Authorization"] = f"Basic {encode_auth_headers(login, api_key)}"

    return headers, login, api_key


def extract_auth_from_request():
    """
    Extract login and api_key/password from multiple possible sources:
    1. HTTP Basic Authorization header
    2. Query string parameters (?login=...&api_key=... or ?user=...&password=...)
    3. Form data (POST body)
    4. JSON body
    """
    login = None
    api_key = None

    # 1. Authorization header (Basic Auth)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        if auth_header.startswith("Basic "):
            try:
                encoded_credentials = auth_header.split(" ", 1)[1].strip()
                decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                if ":" in decoded:
                    login, api_key = decoded.split(":", 1)
            except (binascii.Error, UnicodeDecodeError, ValueError):
                pass
        elif auth_header.startswith("Token "):
            # If client forwarded a token header directly
            try:
                encoded_credentials = auth_header.split(" ", 1)[1].strip()
                decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                if ":" in decoded:
                    login, api_key = decoded.split(":", 1)
            except (binascii.Error, UnicodeDecodeError, ValueError):
                pass

    # 2. Query parameters
    if not login or not api_key:
        login = (
            request.args.get("login")
            or request.args.get("user")
            or request.args.get("username")
            or login
        )
        api_key = (
            request.args.get("api_key")
            or request.args.get("password")
            or request.args.get("pass")
            or api_key
        )

    # 3. Form data
    if not login or not api_key:
        if request.form:
            login = (
                request.form.get("login")
                or request.form.get("user")
                or request.form.get("username")
                or login
            )
            api_key = (
                request.form.get("api_key")
                or request.form.get("password")
                or request.form.get("pass")
                or api_key
            )

    # 4. JSON payload
    if not login or not api_key:
        json_data = request.get_json(silent=True)
        if isinstance(json_data, dict):
            login = (
                json_data.get("login")
                or json_data.get("user")
                or json_data.get("username")
                or login
            )
            api_key = (
                json_data.get("api_key")
                or json_data.get("password")
                or json_data.get("pass")
                or api_key
            )

    return login, api_key
