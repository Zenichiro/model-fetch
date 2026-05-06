from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from model_fetch.detector.confidence import choose_best
from model_fetch.detector.patterns import PATTERN_RULES
from model_fetch.detector.safetensors_inspect import classify_safetensors_header


@dataclass(frozen=True)
class Classification:
    model_type: str
    confidence: float
    method: str


def _classify_from_metadata(metadata: dict[str, object]) -> tuple[str, float, str] | None:
    raw_type = metadata.get("model_type")
    if not isinstance(raw_type, str):
        return None

    normalized = raw_type.strip().lower()
    mapping = {
        "checkpoint": "checkpoints",
        "lora": "loras",
        "vae": "vae",
        "controlnet": "controlnet",
        "upscaler": "upscalers",
        "embedding": "embeddings",
        "textualinversion": "embeddings",
        "hypernetwork": "hypernetworks",
    }
    if normalized in mapping:
        return (mapping[normalized], 0.97, "source_metadata")
    return None


def _classify_from_filename(path: Path) -> tuple[str, float, str] | None:
    name = path.name.lower()
    for needles, target, confidence, method in PATTERN_RULES:
        if any(needle in name for needle in needles):
            return (target, confidence, method)
    return None


def _classify_from_size(path: Path) -> tuple[str, float, str] | None:
    if not path.exists():
        return None

    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb < 100:
        return ("unknown", 0.5, "size_heuristic")
    if 500 <= size_mb <= 30_000:
        return ("checkpoints", 0.55, "size_heuristic")
    return None


def classify_file(path: Path, metadata: dict[str, object] | None = None) -> Classification:
    candidates: list[tuple[str, float, str]] = []

    if metadata:
        metadata_choice = _classify_from_metadata(metadata)
        if metadata_choice:
            candidates.append(metadata_choice)

    filename_choice = _classify_from_filename(path)
    if filename_choice:
        candidates.append(filename_choice)

    if path.exists():
        header_choice = classify_safetensors_header(path)
        if header_choice:
            candidates.append(header_choice)

        size_choice = _classify_from_size(path)
        if size_choice:
            candidates.append(size_choice)

    model_type, confidence, method = choose_best(candidates)
    return Classification(model_type=model_type, confidence=confidence, method=method)
