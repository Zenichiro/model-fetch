from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResolvedItem:
    raw_input: str
    source: str
    url: str
    metadata: dict[str, object] = field(default_factory=dict)
