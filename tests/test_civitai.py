from model_fetch.sources.civitai import resolve_civitai_item


def test_resolve_civitai_numeric_id_to_download_url() -> None:
    result = resolve_civitai_item("civitai", "2807896")
    assert result.source == "civitai"
    assert result.url == "https://civitai.com/api/download/models/2807896"
