import logging
from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import convert_user_format

logger = logging.getLogger(__name__)
users_bp = Blueprint("users", __name__)


@users_bp.route("/users/<user_identifier>.json", methods=["GET"])
@users_bp.route("/users/<user_identifier>", methods=["GET"])
def get_user(user_identifier):
    headers, login, _ = get_auth_headers()
    target_user = user_identifier
    if target_user.isdigit() and login:
        target_user = login

    try:
        # First try direct /user/<name>
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/user/{target_user}",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            user_obj = response.json()
            profile = convert_user_format(user_obj)
            if user_identifier.isdigit():
                profile["id"] = int(user_identifier)
            return jsonify(profile), 200

        # Fallback to /users?query=<name>
        fallback_resp = requests.get(
            f"{config.SZURUBOORU_API_URL}/users",
            params={"query": target_user},
            headers=headers,
            timeout=10,
        )
        if fallback_resp.status_code == 200:
            data = fallback_resp.json()
            results = data.get("results", [])
            if results:
                profile = convert_user_format(results[0])
                if user_identifier.isdigit():
                    profile["id"] = int(user_identifier)
                return jsonify(profile), 200

        if response.status_code in (401, 403):
            return jsonify({"message": "Access denied"}), response.status_code

        return jsonify({"message": "Profile not found"}), 404
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching user {user_identifier}: {e}")
        return jsonify(convert_user_format({})), 200


@users_bp.route("/users.json", methods=["GET"])
@users_bp.route("/users", methods=["GET"])
def search_users():
    headers, login, _ = get_auth_headers()
    name_query = (
        request.args.get("search[name_matches]")
        or request.args.get("search[name]")
        or request.args.get("name")
        or login
        or ""
    ).strip()

    try:
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/users",
            params={"query": name_query} if name_query else {},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            users_list = []
            for item in data.get("results", []):
                users_list.append(convert_user_format(item))
            return jsonify(users_list), 200
        else:
            return jsonify([]), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching users: {e}")
        return jsonify([]), 200


@users_bp.route("/profile", methods=["GET"])
@users_bp.route("/profile.json", methods=["GET"])
def get_profile():
    headers, login, _ = get_auth_headers()
    if not login:
        return jsonify(convert_user_format({})), 200

    try:
        # Try direct user endpoint first
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/user/{login}",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            user_obj = response.json()
            return jsonify(convert_user_format(user_obj)), 200

        # Fallback to searching users
        fallback_resp = requests.get(
            f"{config.SZURUBOORU_API_URL}/users",
            params={"query": login},
            headers=headers,
            timeout=10,
        )
        if fallback_resp.status_code == 200:
            user_profile = fallback_resp.json()
            results = user_profile.get("results", [])
            if results:
                return jsonify(convert_user_format(results[0])), 200

        if response.status_code in (401, 403):
            return (
                jsonify({"message": "Invalid username or password", "success": False}),
                response.status_code,
            )

        return jsonify(convert_user_format({})), 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching profile: {e}")
        return jsonify(convert_user_format({})), 200
