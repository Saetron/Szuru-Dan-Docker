import logging
from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import convert_user_format

logger = logging.getLogger(__name__)
users_bp = Blueprint("users", __name__)


@users_bp.route("/users/<int:user_id>.json", methods=["GET"])
@users_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    headers, login, _ = get_auth_headers()
    target_user = login or str(user_id)

    try:
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/users",
            params={"query": target_user},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            user_profile = response.json()
            profile = convert_user_format(user_profile)
            profile["id"] = user_id
            return jsonify(profile), 200
        else:
            return jsonify({"message": "Profile not found"}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching user {user_id}: {e}")
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
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/users",
            params={"query": login},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            user_profile = response.json()
            profile = convert_user_format(user_profile)
            return jsonify(profile), 200
        else:
            return jsonify(convert_user_format({})), 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching profile: {e}")
        return jsonify(convert_user_format({})), 200
