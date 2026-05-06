from __future__ import annotations

import re
from urllib.parse import urlparse

from model_fetch.sources.base import ResolvedItem

_CIVITAI_ID_PATTERN = re.compile(r"^\d+$")


def resolve_civitai_item(source: str, identifier: str) -> ResolvedItem:
    normalized_source = source.strip().lower()
    if normalized_source != "civitai":
        raise ValueError("unsupported source")

    if _CIVITAI_ID_PATTERN.fullmatch(identifier):
        url = f"https://civitai.com/api/download/models/{identifier}"
        return ResolvedItem(
            raw_input=f"{source} {identifier}",
            source="civitai",
            url=url,
            metadata={"identifier_type": "numeric"},
        )

    parsed = urlparse(identifier)
    if parsed.scheme in {"http", "https"} and (
        "civitai.com" in parsed.netloc.lower() or "civitai.red" in parsed.netloc.lower()
    ):
        return ResolvedItem(raw_input=identifier, source="civitai", url=identifier)

    raise ValueError(f"unsupported CivitAI input: {identifier}")
