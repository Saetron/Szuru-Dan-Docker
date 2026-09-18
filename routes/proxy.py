import logging
import mimetypes
from urllib.parse import unquote
from flask import Blueprint, request, Response
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import config

logger = logging.getLogger(__name__)
proxy_bp = Blueprint("proxy", __name__)

# Reusable HTTP session with connection pooling
session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=25,
    pool_maxsize=25,
    max_retries=Retry(total=2, backoff_factor=0.2),
)
session.mount("http://", adapter)
session.mount("https://", adapter)


def _proxy_resource(resource_folder: str, raw_filename: str) -> Response:
    filename = unquote(raw_filename)

    # Path traversal protection
    if ".." in filename or filename.startswith("/"):
        return Response("Forbidden path", status=403)

    internal_url = f"{config.SZURUBOORU_URL}{resource_folder}/{filename}"

    range_header = request.headers.get("Range")
    headers = {}
    if range_header:
        headers["Range"] = range_header

    try:
        backend_resp = session.get(
            internal_url,
            headers=headers,
            stream=True,
            timeout=30,
        )

        if backend_resp.status_code in (200, 206):
            content_type = backend_resp.headers.get("Content-Type")
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    ext = filename.lower().split("?")[0].split(".")[-1]
                    mime_map = {
                        "mp4": "video/mp4",
                        "webm": "video/webm",
                        "avi": "video/avi",
                        "mov": "video/quicktime",
                        "png": "image/png",
                        "jpg": "image/jpeg",
                        "jpeg": "image/jpeg",
                        "gif": "image/gif",
                        "webp": "image/webp",
                    }
                    content_type = mime_map.get(ext, "application/octet-stream")

            def stream_generator():
                try:
                    for chunk in backend_resp.iter_content(chunk_size=16384):
                        if chunk:
                            yield chunk
                finally:
                    backend_resp.close()

            response_headers = {
                "Content-Type": content_type,
                "Cache-Control": "public, max-age=31536000",
            }

            for h in ("Content-Length", "Content-Range", "Accept-Ranges", "ETag", "Last-Modified"):
                val = backend_resp.headers.get(h)
                if val:
                    response_headers[h] = val

            ext = filename.lower().split("?")[0].split(".")[-1]
            if ext in ("mp4", "webm", "avi", "mov", "mkv"):
                response_headers["Accept-Ranges"] = "bytes"

            return Response(
                stream_generator(),
                status=backend_resp.status_code,
                headers=response_headers,
            )
        else:
            backend_resp.close()
            return Response("File not found", status=404)

    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy error for {resource_folder}/{filename}: {e}")
        return Response("Internal server error", status=500)


@proxy_bp.route("/data/<path:filename>")
def proxy_content(filename):
    """Proxy image and video content with HTTP range support"""
    return _proxy_resource("data", filename)


@proxy_bp.route("/thumbnails/<path:filename>")
def proxy_thumbnail(filename):
    """Proxy image thumbnails"""
    return _proxy_resource("thumbnails", filename)


@proxy_bp.route("/avatars/<path:filename>")
def proxy_avatar(filename):
    """Proxy user avatars"""
    return _proxy_resource("avatars", filename)
