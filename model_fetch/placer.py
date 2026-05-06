from __future__ import annotations

import shutil
from pathlib import Path


def ensure_destination(base_dir: Path, model_type: str, filename: str) -> Path:
    destination_dir = base_dir / model_type
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / filename

    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 1
    while True:
        candidate = destination_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_to_destination(source: Path, base_dir: Path, model_type: str) -> Path:
    destination = ensure_destination(base_dir, model_type, source.name)
    shutil.move(str(source), str(destination))
    return destination
