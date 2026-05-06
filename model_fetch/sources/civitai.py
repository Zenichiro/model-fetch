from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from model_fetch.sources.base import ResolvedItem

_CIVITAI_ID_PATTERN = re.compile(r"^\d+$")
_DOWNLOAD_PATH_PATTERN = re.compile(r"^/api/download/models/(?P<id>\d+)$")
_MODEL_PAGE_PATTERN = re.compile(r"^/models/(?P<id>\d+)(?:/.*)?$")


def _api_base_for_host(host: str) -> str:
    normalized = host.lower()
    if "civitai.red" in normalized:
        return "https://civitai.red/api/v1"
    return "https://civitai.com/api/v1"


def _fetch_json(url: str, api_key: str | None = None) -> dict[str, object]:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(url=url, headers=headers, method="GET")
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _select_primary_file(files: list[object]) -> dict[str, object] | None:
    dict_files = [item for item in files if isinstance(item, dict)]
    if not dict_files:
        return None
    for item in dict_files:
        if item.get("primary") is True:
            return item
    return dict_files[0]


def _build_resolved_item(
    raw_input: str,
    download_url: str,
    metadata_payload: dict[str, object],
    file_payload: dict[str, object] | None,
    *,
    identifier_type: str,
) -> ResolvedItem:
    model_payload = metadata_payload.get("model", {})
    model_type = None
    if isinstance(model_payload, dict):
        raw_type = model_payload.get("type")
        if isinstance(raw_type, str):
            model_type = raw_type

    filename = None
    if isinstance(file_payload, dict):
        raw_name = file_payload.get("name")
        if isinstance(raw_name, str):
            filename = raw_name

    metadata = {
        "identifier_type": identifier_type,
    }
    if model_type:
        metadata["model_type"] = model_type
    if filename:
        metadata["filename"] = filename

    return ResolvedItem(
        raw_input=raw_input,
        source="civitai",
        url=download_url,
        metadata=metadata,
    )


def _resolve_version_id(version_id: str, raw_input: str, host: str, api_key: str | None) -> ResolvedItem:
    api_base = _api_base_for_host(host)
    payload = _fetch_json(f"{api_base}/model-versions/{version_id}", api_key=api_key)
    file_payload = _select_primary_file(payload.get("files", [])) if isinstance(payload, dict) else None
    download_url = None
    if isinstance(file_payload, dict):
        candidate_url = file_payload.get("downloadUrl")
        if isinstance(candidate_url, str):
            download_url = candidate_url
    if not download_url and isinstance(payload, dict):
        candidate_url = payload.get("downloadUrl")
        if isinstance(candidate_url, str):
            download_url = candidate_url
    if not download_url:
        download_url = f"https://civitai.com/api/download/models/{version_id}"
    return _build_resolved_item(
        raw_input,
        download_url,
        payload if isinstance(payload, dict) else {},
        file_payload,
        identifier_type="model_version",
    )


def _resolve_model_id(model_id: str, raw_input: str, host: str, api_key: str | None) -> ResolvedItem:
    api_base = _api_base_for_host(host)
    payload = _fetch_json(f"{api_base}/models/{model_id}", api_key=api_key)
    versions = payload.get("modelVersions", []) if isinstance(payload, dict) else []
    if not isinstance(versions, list) or not versions:
        raise ValueError(f"CivitAI model {model_id} has no downloadable versions")

    version_payload = next(
        (item for item in versions if isinstance(item, dict) and item.get("downloadUrl")),
        versions[0],
    )
    if not isinstance(version_payload, dict):
        raise ValueError(f"CivitAI model {model_id} returned unexpected version data")

    file_payload = _select_primary_file(version_payload.get("files", []))
    download_url = version_payload.get("downloadUrl")
    if not isinstance(download_url, str):
        raise ValueError(f"CivitAI model {model_id} did not provide a download URL")

    model_type = payload.get("type") if isinstance(payload, dict) else None
    metadata_payload: dict[str, object] = dict(version_payload)
    if isinstance(model_type, str):
        metadata_payload["model"] = {"type": model_type}

    return _build_resolved_item(
        raw_input,
        download_url,
        metadata_payload,
        file_payload,
        identifier_type="model",
    )


def resolve_civitai_item(source: str, identifier: str, api_key: str | None = None) -> ResolvedItem:
    normalized_source = source.strip().lower()
    if normalized_source != "civitai":
        raise ValueError("unsupported source")

    if _CIVITAI_ID_PATTERN.fullmatch(identifier):
        try:
            return _resolve_version_id(identifier, f"{source} {identifier}", "civitai.com", api_key)
        except (HTTPError, URLError):
            return _resolve_model_id(identifier, f"{source} {identifier}", "civitai.com", api_key)

    parsed = urlparse(identifier)
    if parsed.scheme in {"http", "https"} and (
        "civitai.com" in parsed.netloc.lower() or "civitai.red" in parsed.netloc.lower()
    ):
        download_match = _DOWNLOAD_PATH_PATTERN.fullmatch(parsed.path)
        if download_match:
            resolved = _resolve_version_id(
                download_match.group("id"),
                identifier,
                parsed.netloc,
                api_key,
            )
            if parsed.query:
                resolved = ResolvedItem(
                    raw_input=resolved.raw_input,
                    source=resolved.source,
                    url=identifier,
                    metadata=resolved.metadata,
                )
            return resolved

        page_match = _MODEL_PAGE_PATTERN.fullmatch(parsed.path)
        if page_match:
            query = parse_qs(parsed.query)
            version_id = query.get("modelVersionId", [None])[0]
            if isinstance(version_id, str) and _CIVITAI_ID_PATTERN.fullmatch(version_id):
                return _resolve_version_id(version_id, identifier, parsed.netloc, api_key)
            return _resolve_model_id(page_match.group("id"), identifier, parsed.netloc, api_key)

        return ResolvedItem(raw_input=identifier, source="civitai", url=identifier)

    raise ValueError(f"unsupported CivitAI input: {identifier}")
