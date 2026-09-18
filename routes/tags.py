import logging
from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import category_map

logger = logging.getLogger(__name__)
tags_bp = Blueprint("tags", __name__)


def _get_tag_category_num(cat_raw) -> int:
    if isinstance(cat_raw, int):
        return cat_raw
    cat_str = str(cat_raw).lower()
    return category_map.get(cat_str, 0)


@tags_bp.route("/tags/autocomplete.json", methods=["GET"])
@tags_bp.route("/tags/autocomplete", methods=["GET"])
@tags_bp.route("/autocomplete.json", methods=["GET"])
@tags_bp.route("/autocomplete", methods=["GET"])
def autocomplete_tags():
    headers, _, _ = get_auth_headers()

    query = (
        request.args.get("search[query]")
        or request.args.get("search[name_matches]")
        or request.args.get("term")
        or request.args.get("q")
        or ""
    ).strip()

    if query:
        if len(query) < 3:
            search_pattern = f"{query}*"
        else:
            search_pattern = f"*{query}*"
    else:
        search_pattern = "*"

    try:
        limit = min(int(request.args.get("limit", 10)), 50)
    except (ValueError, TypeError):
        limit = 10

    try:
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/tags",
            params={"query": f"{search_pattern} sort:usages", "limit": limit},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            auto_complete_tags = []
            for tag in results:
                names = tag.get("names", [])
                if not names:
                    continue
                tag_name = names[0]
                category_num = _get_tag_category_num(tag.get("category", "default"))
                auto_complete_tags.append(
                    {
                        "type": "tag-word",
                        "label": tag_name,
                        "value": tag_name,
                        "category": category_num,
                        "post_count": tag.get("usages", 0),
                    }
                )
            return jsonify(auto_complete_tags), 200
        else:
            return jsonify({"message": "Failed to fetch tags"}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error autocompleting tags: {e}")
        return jsonify([]), 200


@tags_bp.route("/tags.json", methods=["GET"])
@tags_bp.route("/tags", methods=["GET"])
def search_tags():
    headers, _, _ = get_auth_headers()

    name_query = (
        request.args.get("search[name_matches]")
        or request.args.get("search[name]")
        or request.args.get("name")
        or ""
    ).strip()

    try:
        limit = min(int(request.args.get("limit", 20)), 100)
    except (ValueError, TypeError):
        limit = 20

    query_str = f"{name_query} sort:usages" if name_query else "sort:usages"

    try:
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/tags",
            params={"query": query_str, "limit": limit},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            tags_list = []
            for i, tag in enumerate(results):
                names = tag.get("names", [])
                tag_name = names[0] if names else ""
                category_num = _get_tag_category_num(tag.get("category", "default"))
                tags_list.append(
                    {
                        "id": i + 1,
                        "name": tag_name,
                        "post_count": tag.get("usages", 0),
                        "category": category_num,
                        "is_locked": False,
                        "created_at": "2020-01-01T00:00:00Z",
                        "updated_at": "2020-01-01T00:00:00Z",
                    }
                )
            return jsonify(tags_list), 200
        else:
            return jsonify([]), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching tags: {e}")
        return jsonify([]), 200
