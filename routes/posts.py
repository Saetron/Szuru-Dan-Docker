import logging
from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import convert_post_format
from utils import parse_query
from services.timing import Timer, RequestTimer

logger = logging.getLogger(__name__)
posts_bp = Blueprint("posts", __name__)


@posts_bp.route("/posts", methods=["GET"])
@posts_bp.route("/posts.json", methods=["GET"])
def search_posts():
    timer = RequestTimer("search_posts")
    timer.checkpoint("Request started")

    # Parse query parameters safely
    with Timer("Parse query parameters"):
        raw_query = request.args.get("tags", "")
        query = parse_query(raw_query)

        # Parse limit
        try:
            raw_limit = request.args.get("limit", 40)
            limit = max(1, min(int(raw_limit), 100))
        except (ValueError, TypeError):
            limit = 40

        # Parse page
        raw_page = request.args.get("page", 1)
        try:
            page = int(raw_page)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            # In case cursor-based pagination (e.g. "b1234") is passed
            page = 1

    timer.checkpoint("Query parameters parsed")

    with Timer("Get authentication headers"):
        headers, login, _ = get_auth_headers()

    timer.checkpoint("Authentication processed")

    offset = (page - 1) * limit
    api_url = f"{config.SZURUBOORU_API_URL}/posts"
    params = {
        "offset": offset,
        "limit": limit,
        "query": query,
    }

    timer.checkpoint("API request prepared")

    with Timer("Szurubooru API request"):
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            logger.error(f"API request timeout for query: {raw_query}")
            return jsonify({"message": "API request timeout"}), 504
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return jsonify({"message": "API request failed"}), 500

    timer.checkpoint("Szurubooru API response received")

    if response.status_code == 200:
        with Timer("Parse JSON response"):
            try:
                szuru_posts = response.json()
            except ValueError:
                return jsonify([]), 200

        timer.checkpoint("JSON parsed")

        with Timer("Convert post formats"):
            results = szuru_posts.get("results", [])
            danbooru_posts = []

            for post in results:
                converted_post = convert_post_format(post, login)
                danbooru_posts.append(converted_post)

        timer.checkpoint("All posts converted")
        timer.summary()

        return jsonify(danbooru_posts), 200
    else:
        timer.checkpoint(f"API error: {response.status_code}")
        timer.summary()
        return jsonify({"message": "Failed to fetch posts"}), response.status_code


@posts_bp.route("/posts/<int:post_id>.json", methods=["GET"])
@posts_bp.route("/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    timer = RequestTimer(f"post-{post_id}")
    timer.checkpoint("Single post request started")

    with Timer("Get authentication headers"):
        headers, login, _ = get_auth_headers()

    timer.checkpoint("Authentication processed")

    with Timer("Szurubooru API request"):
        try:
            response = requests.get(
                f"{config.SZURUBOORU_API_URL}/post/{post_id}",
                headers=headers,
                timeout=20,
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch post {post_id}: {e}")
            return jsonify({"message": "API request failed"}), 500

    timer.checkpoint("API response received")

    if response.status_code == 200:
        with Timer("Parse JSON and convert format"):
            szuru_post = response.json()
            danbooru_post = convert_post_format(szuru_post, login)

        timer.checkpoint("Post converted")
        timer.summary()

        return jsonify(danbooru_post), 200
    else:
        timer.checkpoint(f"API error: {response.status_code}")
        timer.summary()
        return jsonify({"message": "Post not found"}), response.status_code


@posts_bp.route("/counts/posts.json", methods=["GET"])
@posts_bp.route("/counts/posts", methods=["GET"])
def get_post_count():
    raw_query = request.args.get("tags", "")
    query = parse_query(raw_query)
    headers, _, _ = get_auth_headers()

    try:
        response = requests.get(
            f"{config.SZURUBOORU_API_URL}/posts",
            params={"offset": 0, "limit": 1, "query": query},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            return jsonify({"counts": {"posts": total}}), 200
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch post count: {e}")

    return jsonify({"counts": {"posts": 0}}), 200
