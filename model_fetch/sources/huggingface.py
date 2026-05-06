from __future__ import annotations

from urllib.parse import urlparse

from model_fetch.sources.base import ResolvedItem


def resolve_huggingface_url(raw_input: str) -> ResolvedItem:
    parsed = urlparse(raw_input)
    if parsed.scheme not in {"http", "https"} or "huggingface.co" not in parsed.netloc.lower():
        raise ValueError("not a Hugging Face URL")
    return ResolvedItem(raw_input=raw_input, source="huggingface", url=raw_input)
