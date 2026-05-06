from urllib.error import URLError

from model_fetch.sources.civitai import resolve_civitai_item


def test_resolve_civitai_numeric_id_to_download_url(monkeypatch) -> None:
    def fake_fetch_json(
        url: str,
        api_key: str | None = None,
        *,
        proxy_url: str | None = None,
    ) -> dict[str, object]:
        assert url.endswith("/api/v1/model-versions/2807896")
        assert api_key == "secret"
        return {
            "downloadUrl": "https://civitai.com/api/download/models/2807896",
            "model": {"type": "Checkpoint"},
            "files": [
                {
                    "name": "ilustmixv111.safetensors",
                    "downloadUrl": "https://civitai.com/api/download/models/2807896",
                    "primary": True,
                }
            ],
        }

    monkeypatch.setattr("model_fetch.sources.civitai._fetch_json", fake_fetch_json)
    result = resolve_civitai_item("civitai", "2807896", api_key="secret")
    assert result.source == "civitai"
    assert result.url == "https://civitai.com/api/download/models/2807896"
    assert result.metadata["filename"] == "ilustmixv111.safetensors"
    assert result.metadata["model_type"] == "Checkpoint"


def test_resolve_civitai_download_url_preserves_query(monkeypatch) -> None:
    def fake_fetch_json(
        url: str,
        api_key: str | None = None,
        *,
        proxy_url: str | None = None,
    ) -> dict[str, object]:
        return {
            "downloadUrl": "https://civitai.com/api/download/models/2807896",
            "model": {"type": "Checkpoint"},
            "files": [{"name": "ilustmixv111.safetensors", "primary": True}],
        }

    monkeypatch.setattr("model_fetch.sources.civitai._fetch_json", fake_fetch_json)
    raw_url = "https://civitai.com/api/download/models/2807896?type=Model&format=SafeTensor"
    result = resolve_civitai_item("civitai", raw_url)
    assert result.url == raw_url
    assert result.metadata["filename"] == "ilustmixv111.safetensors"


def test_resolve_civitai_numeric_id_falls_back_on_soft_error(monkeypatch) -> None:
    def fake_fetch_json(
        url: str,
        api_key: str | None = None,
        *,
        proxy_url: str | None = None,
    ) -> dict[str, object]:
        raise URLError("curl: (22) The requested URL returned error: 503")

    monkeypatch.setattr("model_fetch.sources.civitai._fetch_json", fake_fetch_json)
    result = resolve_civitai_item("civitai", "2807896", api_key="secret", proxy_url="http://127.0.0.1:8888")
    assert result.url == "https://civitai.com/api/download/models/2807896"
    assert result.metadata["identifier_type"] == "numeric_fallback"
