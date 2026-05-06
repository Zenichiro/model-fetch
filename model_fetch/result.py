from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class FetchItemResult:
    input: str
    source: str
    resolved_url: str | None
    filename: str | None
    detected_type: str | None
    detection_confidence: float | None
    detection_method: str | None
    destination: str | None
    ok: bool
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
