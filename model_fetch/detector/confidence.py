from __future__ import annotations


def choose_best(candidates: list[tuple[str, float, str]]) -> tuple[str, float, str]:
    if not candidates:
        return ("unknown", 0.0, "fallback")
    return max(candidates, key=lambda item: item[1])
