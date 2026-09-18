import base64
from typing import List, Optional, Union


def encode_auth_headers(u: str, p: str) -> str:
    """Encode username and password/token as base64 for Szurubooru Token header"""
    return base64.b64encode(f"{u}:{p}".encode("utf-8")).decode("ascii")


def tags_str(tags: list) -> str:
    """Extract first name from list of Szurubooru tag dicts and return space-delimited string"""
    names = []
    for tag in tags:
        if isinstance(tag, dict) and tag.get("names"):
            names.append(tag["names"][0])
        elif isinstance(tag, str):
            names.append(tag)
    return " ".join(names)


def convert_rating(rating: Optional[str]) -> Optional[str]:
    """Convert Danbooru rating to Szurubooru safety level"""
    if not rating:
        return None
    rating = rating.lower().strip()
    mapping = {
        "safe": "safe",
        "s": "safe",
        "g": "safe",
        "general": "safe",
        "questionable": "sketchy",
        "sketchy": "sketchy",
        "q": "sketchy",
        "sensitive": "sketchy",
        "explicit": "unsafe",
        "e": "unsafe",
        "unsafe": "unsafe",
    }
    return mapping.get(rating)


def convert_back_rating(rating: Optional[str]) -> str:
    """Convert Szurubooru safety level to Danbooru rating character"""
    if not rating:
        return "g"
    rating = rating.lower().strip()
    mapping = {
        "safe": "s",
        "sketchy": "q",
        "unsafe": "e",
    }
    return mapping.get(rating, "g")


def parse_query(query: Optional[str]) -> str:
    """
    Translate Danbooru search query tokens into Szurubooru search syntax.
    Handles ratings, ordering/sorting, favorites, and user filters.
    """
    if not query:
        return ""

    tokens = query.strip().split()
    translated_tokens = []

    for token in tokens:
        # 1. Rating mapping (e.g. rating:s, -rating:e, rating:safe)
        is_negated = token.startswith("-")
        clean_token = token[1:] if is_negated else token
        prefix = "-" if is_negated else ""

        if clean_token.startswith("rating:"):
            raw_rating = clean_token.split(":", 1)[1]
            mapped_rating = convert_rating(raw_rating)
            if mapped_rating:
                translated_tokens.append(f"{prefix}safety:{mapped_rating}")
                continue

        # 2. Ordering / Sorting mapping (order:score -> sort:score)
        if clean_token.startswith("order:"):
            order_val = clean_token.split(":", 1)[1].lower()
            sort_map = {
                "score": "sort:score",
                "score_desc": "sort:score",
                "score_asc": "sort:score-asc",
                "favcount": "sort:favs",
                "fav": "sort:favs",
                "id": "sort:id",
                "id_desc": "sort:id",
                "id_asc": "sort:id-asc",
                "rank": "sort:random",
                "random": "sort:random",
                "tagcount": "sort:tag-count",
                "tag_count": "sort:tag-count",
                "date": "sort:creation-date",
            }
            translated = sort_map.get(order_val, f"sort:{order_val}")
            translated_tokens.append(f"{prefix}{translated}")
            continue

        # 3. Favorite mapping (ordfav:user -> fav:user)
        if clean_token.startswith("ordfav:"):
            username = clean_token.split(":", 1)[1]
            translated_tokens.append(f"{prefix}fav:{username}")
            continue

        # 4. Uploader / User mapping
        if clean_token.startswith("uploader:"):
            username = clean_token.split(":", 1)[1]
            translated_tokens.append(f"{prefix}user:{username}")
            continue

        # Keep original token (handles tag names, wildcards, etc.)
        translated_tokens.append(token)

    return " ".join(translated_tokens)


def parse_tags(tags: Union[str, list]) -> List[str]:
    """Parse comma/space/bracket separated tags into a clean list of tag strings"""
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]

    if not tags:
        return []

    cleaned = (
        tags.replace(",", " ")
        .replace("[", "")
        .replace("]", "")
        .replace('"', "")
        .replace("'", "")
    )
    return [t.strip() for t in cleaned.split() if t.strip()]


def parse_tags_str(tags: Union[str, list]) -> str:
    """Parse tags and return a single space-separated string"""
    return " ".join(parse_tags(tags))
