from model_fetch.sources.direct_url import resolve_direct_url


def test_resolve_direct_url_detects_huggingface_source() -> None:
    result = resolve_direct_url("https://huggingface.co/org/repo/resolve/main/model.safetensors")
    assert result.source == "huggingface"


def test_resolve_direct_url_detects_civitai_source() -> None:
    result = resolve_direct_url("https://civitai.com/api/download/models/2807896")
    assert result.source == "civitai"
