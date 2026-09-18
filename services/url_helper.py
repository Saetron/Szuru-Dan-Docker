from urllib.parse import urljoin
from flask import request
from config import config


def get_current_domain() -> str:
    """Dynamically get the base URL of the current request or configured domain"""
    if config.REVERSE_PROXY_MODE:
        scheme = request.scheme
        host = request.host
        return f"{scheme}://{host}/"
    return config.DOMAIN_URL


def build_resource_url(resource_path: str) -> str:
    """Build full resource URL cleanly without double slashes"""
    if not resource_path:
        return ""

    if resource_path.startswith("http://") or resource_path.startswith("https://"):
        return resource_path

    base_domain = get_current_domain()
    # Strip leading slash on resource path if base_domain ends with slash to avoid replacing path
    clean_path = resource_path.lstrip("/")
    return urljoin(base_domain, clean_path)
