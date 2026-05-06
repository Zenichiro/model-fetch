from __future__ import annotations

import json
import struct
from pathlib import Path


def read_safetensors_header(path: Path) -> dict[str, object] | None:
    with path.open("rb") as handle:
        raw_length = handle.read(8)
        if len(raw_length) != 8:
            return None
        header_length = struct.unpack("<Q", raw_length)[0]
        if header_length <= 0 or header_length > 16 * 1024 * 1024:
            return None
        header_bytes = handle.read(header_length)
        if len(header_bytes) != header_length:
            return None
    return json.loads(header_bytes.decode("utf-8"))


def classify_safetensors_header(path: Path) -> tuple[str, float, str] | None:
    if path.suffix.lower() != ".safetensors":
        return None

    try:
        header = read_safetensors_header(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(header, dict):
        return None

    keys = " ".join(str(item).lower() for item in header.keys())
    if "lora" in keys:
        return ("loras", 0.9, "safetensors_header")
    if "vae" in keys:
        return ("vae", 0.85, "safetensors_header")
    if "text" in keys or "clip" in keys:
        return ("text_encoders", 0.8, "safetensors_header")
    if "unet" in keys:
        return ("unet", 0.8, "safetensors_header")
    if "diffusion_model" in keys:
        return ("checkpoints", 0.75, "safetensors_header")
    return None
