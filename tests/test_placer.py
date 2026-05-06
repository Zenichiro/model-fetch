from pathlib import Path

from model_fetch.placer import ensure_destination, move_to_destination


def test_ensure_destination_adds_suffix_for_conflict(tmp_path: Path) -> None:
    base_dir = tmp_path
    target_dir = base_dir / "checkpoints"
    target_dir.mkdir()
    (target_dir / "model.safetensors").write_text("x", encoding="utf-8")

    result = ensure_destination(base_dir, "checkpoints", "model.safetensors")

    assert result.name == "model_1.safetensors"


def test_move_to_destination_moves_file(tmp_path: Path) -> None:
    source = tmp_path / "file.safetensors"
    source.write_text("content", encoding="utf-8")

    destination = move_to_destination(source, tmp_path, "checkpoints")

    assert destination.exists()
    assert not source.exists()
