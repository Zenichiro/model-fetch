from __future__ import annotations

from urllib.parse import urlparse

from model_fetch.sources.base import ResolvedItem


def resolve_direct_url(raw_input: str) -> ResolvedItem:
    parsed = urlparse(raw_input)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"unsupported URL: {raw_input}")

    host = parsed.netloc.lower()
    if "huggingface.co" in host:
        source = "huggingface"
    elif "civitai.com" in host or "civitai.red" in host:
        source = "civitai"
    else:
        source = "direct"

    return ResolvedItem(raw_input=raw_input, source=source, url=raw_input)
