import logging
from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import is_post_favorited_by

logger = logging.getLogger(__name__)
favorites_bp = Blueprint("favorites", __name__)


def _extract_post_id():
    """Safely extract post_id from query params, form values, or JSON body"""
    post_id = request.values.get("post_id")
    if not post_id and request.is_json:
        json_data = request.get_json(silent=True) or {}
        post_id = json_data.get("post_id")
    if not post_id:
        raw_data = request.get_data(as_text=True)
        if raw_data:
            if "post_id=" in raw_data:
                for part in raw_data.split("&"):
                    if part.startswith("post_id="):
                        post_id = part.split("=", 1)[1]
                        break
    if post_id is not None:
        try:
            return int(post_id)
        except (ValueError, TypeError):
            return None
    return None


@favorites_bp.route("/favorites.json", methods=["POST"])
@favorites_bp.route("/favorites", methods=["POST"])
def create_favorite():
    post_id = _extract_post_id()
    if not post_id:
        return jsonify({"message": "post_id is required"}), 400

    headers, _, _ = get_auth_headers()

    try:
        response = requests.post(
            f"{config.SZURUBOORU_API_URL}/post/{post_id}/favorite",
            headers=headers,
            timeout=15,
        )
        if response.status_code in (200, 201):
            return (
                jsonify(
                    {
                        "id": post_id,
                        "user_id": 1,
                        "post_id": post_id,
                        "message": "Favorite created",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"message": "Failed to create favorite"}),
                response.status_code,
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating favorite for post {post_id}: {e}")
        return jsonify({"message": "API request failed"}), 500


@favorites_bp.route("/favorites/<int:post_id>.json", methods=["DELETE"])
@favorites_bp.route("/favorites/<int:post_id>", methods=["DELETE"])
def delete_favorite(post_id):
    headers, _, _ = get_auth_headers()

    try:
        response = requests.delete(
            f"{config.SZURUBOORU_API_URL}/post/{post_id}/favorite",
            headers=headers,
            timeout=15,
        )
        if response.status_code in (200, 204):
            return jsonify({"message": "Favorite deleted"}), 200
        else:
            return (
                jsonify({"message": "Failed to delete favorite"}),
                response.status_code,
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting favorite for post {post_id}: {e}")
        return jsonify({"message": "API request failed"}), 500


@favorites_bp.route("/post_votes.json", methods=["GET"])
@favorites_bp.route("/favorites.json", methods=["GET"])
def get_favorites():
    headers, login, _ = get_auth_headers()

    raw_post_ids = (
        request.args.get("search[post_id]")
        or request.args.get("post_id")
        or ""
    )

    clean_ids = []
    if raw_post_ids:
        # Split by comma, plus, or space
        normalized = (
            raw_post_ids.replace(",", " ").replace("+", " ")
        )
        for item in normalized.split():
            item_str = item.strip()
            if item_str.isdigit():
                clean_ids.append(int(item_str))

    favorites = []

    # If specific post IDs were requested, check them
    if clean_ids:
        for pid in clean_ids:
            try:
                res = requests.get(
                    f"{config.SZURUBOORU_API_URL}/post/{pid}",
                    headers=headers,
                    timeout=5,
                )
                if res.status_code == 200:
                    szuru_post = res.json()
                    if is_post_favorited_by(szuru_post, login):
                        favorites.append(
                            {
                                "id": pid,
                                "user_id": 1,
                                "post_id": pid,
                                "created_at": szuru_post.get("creationTime", ""),
                                "updated_at": szuru_post.get("creationTime", ""),
                                "score": 1,
                                "is_deleted": False,
                            }
                        )
            except requests.exceptions.RequestException:
                continue
    elif login:
        # If no specific post_ids requested, fetch user's favorites from Szurubooru
        try:
            res = requests.get(
                f"{config.SZURUBOORU_API_URL}/posts",
                params={"query": f"fav:{login}", "limit": 100},
                headers=headers,
                timeout=15,
            )
            if res.status_code == 200:
                data = res.json()
                for post in data.get("results", []):
                    pid = post.get("id")
                    if pid:
                        favorites.append(
                            {
                                "id": pid,
                                "user_id": 1,
                                "post_id": pid,
                                "created_at": post.get("creationTime", ""),
                                "updated_at": post.get("creationTime", ""),
                                "score": 1,
                                "is_deleted": False,
                            }
                        )
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch favorites for user {login}: {e}")

    return jsonify(favorites), 200
