from pathlib import Path

from model_fetch.detector.classifier import classify_file


def test_classifier_detects_lora_from_filename(tmp_path: Path) -> None:
    path = tmp_path / "cool_lora_model.safetensors"
    path.write_bytes(b"test")

    result = classify_file(path)

    assert result.model_type == "loras"
    assert result.method == "filename_pattern"


def test_classifier_falls_back_to_unknown_for_small_file(tmp_path: Path) -> None:
    path = tmp_path / "mystery.bin"
    path.write_bytes(b"x" * 16)

    result = classify_file(path)

    assert result.model_type == "unknown"
