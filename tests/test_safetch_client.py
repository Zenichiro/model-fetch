from pathlib import Path

from model_fetch.config import AppConfig
from model_fetch.safetch_client import build_safetch_command, find_new_file
from model_fetch.sources.base import ResolvedItem


def test_build_safetch_command_adds_auth_header_for_civitai() -> None:
    config = AppConfig(civitai_api_key="secret")
    item = ResolvedItem(raw_input="civitai 1", source="civitai", url="https://civitai.com/api/download/models/1")

    command = build_safetch_command(
        config,
        item,
        output_dir=Path("/tmp/model-fetch"),
        dry_run=False,
        no_resume=False,
    )

    assert "--header" in command
    assert "Authorization: Bearer secret" in command


def test_find_new_file_returns_created_path(tmp_path: Path) -> None:
    before = set()
    file_path = tmp_path / "model.safetensors"
    file_path.write_text("x", encoding="utf-8")
    after = {file_path}

    assert find_new_file(before, after) == file_path
