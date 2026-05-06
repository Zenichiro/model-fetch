from __future__ import annotations

import json
import subprocess
from pathlib import Path

from model_fetch.config import AppConfig
from model_fetch.sources.base import ResolvedItem


class SafetchError(RuntimeError):
    pass


def build_safetch_command(
    config: AppConfig,
    item: ResolvedItem,
    *,
    output_dir: Path,
    dry_run: bool,
    no_resume: bool,
) -> list[str]:
    command = [config.safetch_path, "--output-dir", str(output_dir), "--json"]

    if dry_run:
        command.append("--dry-run")
    if no_resume or config.safetch_no_resume:
        command.append("--no-resume")

    headers: list[str] = []
    if item.source == "civitai" and config.civitai_api_key:
        headers.append(f"Authorization: Bearer {config.civitai_api_key}")
        if config.civitai_use_proxy:
            if config.civitai_gluetun_enabled:
                command.append("--gluetun")
            else:
                command.append("--no-gluetun")
    elif item.source == "huggingface" and config.huggingface_api_token:
        headers.append(f"Authorization: Bearer {config.huggingface_api_token}")
        if not config.huggingface_use_proxy:
            command.append("--no-gluetun")
    else:
        command.append("--no-gluetun")

    for header in headers:
        command.extend(["--header", header])

    command.append(item.url)
    return command


def find_new_file(before: set[Path], after: set[Path]) -> Path | None:
    created = sorted(after - before)
    if not created:
        return None
    return created[-1]


def run_safetch(
    config: AppConfig,
    item: ResolvedItem,
    *,
    output_dir: Path,
    dry_run: bool,
    no_resume: bool,
) -> tuple[dict[str, object], Path | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    before = {path for path in output_dir.iterdir() if path.is_file()}
    command = build_safetch_command(
        config,
        item,
        output_dir=output_dir,
        dry_run=dry_run,
        no_resume=no_resume,
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    stdout = completed.stdout.strip()

    if not stdout:
        raise SafetchError("safetch produced no JSON output")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SafetchError(f"failed to parse safetch JSON: {exc}") from exc

    if not isinstance(payload, list) or not payload:
        raise SafetchError("unexpected safetch JSON payload")

    after = {path for path in output_dir.iterdir() if path.is_file()}
    new_file = None if dry_run else find_new_file(before, after)
    return payload[0], new_file
