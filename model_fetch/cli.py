from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_fetch import __version__
from model_fetch.config import AppConfig, load_config
from model_fetch.detector.classifier import classify_file
from model_fetch.placer import move_to_destination
from model_fetch.result import FetchItemResult
from model_fetch.safetch_client import SafetchError, run_safetch
from model_fetch.sources import resolve_civitai_item, resolve_direct_url


def _parse_batch_file(path: Path) -> list[str]:
    items: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        items.append(line)
    return items


def _resolve_item(source: str | None, identifier: str, config: AppConfig) -> tuple[str, object]:
    civitai_proxy_url = None
    if config.civitai_use_proxy:
        civitai_proxy_url = f"http://{config.proxy_host}:{config.proxy_port}"

    if source:
        if source.lower() == "civitai":
            return (
                "civitai",
                resolve_civitai_item(
                    source,
                    identifier,
                    api_key=config.civitai_api_key,
                    proxy_url=civitai_proxy_url,
                ),
            )
        raise ValueError(f"unsupported source: {source}")
    resolved = resolve_direct_url(identifier)
    if resolved.source == "civitai":
        return (
            "civitai",
            resolve_civitai_item(
                "civitai",
                identifier,
                api_key=config.civitai_api_key,
                proxy_url=civitai_proxy_url,
            ),
        )
    return ("direct", resolved)


def _split_entry(entry: str) -> tuple[str | None, str]:
    parts = entry.split(maxsplit=1)
    if len(parts) == 2 and parts[0].lower() == "civitai":
        return (parts[0], parts[1])
    return (None, entry)


def _build_entries(args: list[str], input_file: Path | None) -> list[str]:
    if input_file:
        if args:
            raise ValueError("cannot mix --input with positional arguments")
        return _parse_batch_file(input_file)

    if not args:
        raise ValueError("provide an item or use --input")

    if len(args) == 1:
        return [args[0]]

    if len(args) == 2 and args[0].lower() == "civitai":
        return [f"{args[0]} {args[1]}"]

    raise ValueError("unsupported positional arguments")


def _finish(results: list[FetchItemResult], *, json_output: bool) -> None:
    if json_output:
        payload = {
            "status": "success" if all(item.ok for item in results) else "partial_failure",
            "items": [item.to_dict() for item in results],
            "summary": {
                "total": len(results),
                "success": sum(1 for item in results if item.ok),
                "failed": sum(1 for item in results if not item.ok),
                "skipped": 0,
            },
        }
        print(json.dumps(payload, indent=2))
        return

    for item in results:
        status = "success" if item.ok else "failed"
        line = f"[{status}] {item.input}"
        if item.destination:
            line = f"{line} -> {item.destination}"
        if item.message:
            line = f"{line} :: {item.message}"
        print(line)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="model-fetch",
        description="Download model files through safetch and place them for ComfyUI.",
    )
    parser.add_argument("args", nargs="*", help="Direct URL or `civitai <id>`.")
    parser.add_argument("--input", "-i", dest="input_file", type=Path, help="Read inputs from file.")
    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        help="Override output filename for a single download.",
    )
    parser.add_argument(
        "--output-dir",
        "-d",
        dest="output_dir",
        type=Path,
        help="Temporary download directory.",
    )
    parser.add_argument("--confirm", action="store_true", help="Prompt before placing files.")
    parser.add_argument("--auto", action="store_true", default=True, help="Auto-place without prompting.")
    parser.add_argument("--dry-run", "--test", dest="dry_run", action="store_true", help="Resolve and classify without downloading.")
    parser.add_argument("--config", dest="config_path", type=Path, help="Path to .env config file.")
    parser.add_argument("--model-base-dir", dest="model_base_dir", type=Path, help="Override model base dir.")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Emit machine-readable output.")
    parser.add_argument("--log", action="store_true", help="Reserved simple logging flag.")
    parser.add_argument("--no-log", action="store_true", help="Reserved simple logging disable flag.")
    parser.add_argument("--verbose", action="store_true", help="Reserved verbose flag.")
    parser.add_argument("--no-resume", action="store_true", help="Disable safetch resume support.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)
    del ns.log, ns.no_log, ns.verbose

    try:
        entries = _build_entries(ns.args, ns.input_file)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    config = load_config(ns.config_path)
    if ns.model_base_dir is not None:
        config = AppConfig(
            model_base_dir=ns.model_base_dir,
            temp_download_dir=config.temp_download_dir,
            safetch_path=config.safetch_path,
            safetch_no_resume=config.safetch_no_resume,
            proxy_host=config.proxy_host,
            proxy_port=config.proxy_port,
            civitai_api_key=config.civitai_api_key,
            civitai_use_mirror=config.civitai_use_mirror,
            civitai_use_proxy=config.civitai_use_proxy,
            civitai_gluetun_enabled=config.civitai_gluetun_enabled,
            huggingface_api_token=config.huggingface_api_token,
            huggingface_use_proxy=config.huggingface_use_proxy,
            huggingface_gluetun_enabled=config.huggingface_gluetun_enabled,
        )

    auto = False if ns.confirm else ns.auto
    results: list[FetchItemResult] = []

    for entry in entries:
        entry_source, entry_identifier = _split_entry(entry)
        try:
            resolved_source, resolved = _resolve_item(entry_source, entry_identifier, config)
            if ns.dry_run:
                inferred_name = str(resolved.metadata.get("filename") or Path(resolved.url.split("?")[0]).name or "downloaded-file")
                target_name = ns.output or inferred_name
                classification = classify_file(Path(target_name), metadata=resolved.metadata)
                final_type = classification.model_type if classification.confidence >= 0.70 or not auto else "unknown"
                destination = str(config.model_base_dir / final_type / target_name)
                results.append(
                    FetchItemResult(
                        input=entry,
                        source=resolved_source,
                        resolved_url=resolved.url,
                        filename=target_name,
                        detected_type=final_type,
                        detection_confidence=classification.confidence,
                        detection_method=classification.method,
                        destination=destination,
                        ok=True,
                        message="dry run",
                    )
                )
                continue

            safetch_result, downloaded_file = run_safetch(
                config,
                resolved,
                output_dir=ns.output_dir or config.temp_download_dir,
                dry_run=False,
                no_resume=ns.no_resume,
            )
            if not safetch_result.get("ok"):
                raise SafetchError(str(safetch_result.get("message") or "download failed"))
            if downloaded_file is None:
                raise SafetchError("could not determine downloaded file")

            if ns.output:
                renamed = downloaded_file.with_name(ns.output)
                downloaded_file.rename(renamed)
                downloaded_file = renamed

            classification = classify_file(downloaded_file, metadata=resolved.metadata)
            final_type = classification.model_type
            if classification.confidence < 0.70 and auto:
                final_type = "unknown"

            if ns.confirm:
                prompt = f"Place {downloaded_file.name} into {final_type}? ({classification.confidence:.2f}) [Y/n]: "
                answer = input(prompt).strip().lower()
                if answer not in {"", "y", "yes"}:
                    results.append(
                        FetchItemResult(
                            input=entry,
                            source=resolved_source,
                            resolved_url=resolved.url,
                            filename=downloaded_file.name,
                            detected_type=final_type,
                            detection_confidence=classification.confidence,
                            detection_method=classification.method,
                            destination=None,
                            ok=False,
                            message="user skipped placement",
                        )
                    )
                    continue

            destination = move_to_destination(downloaded_file, config.model_base_dir, final_type)
            results.append(
                FetchItemResult(
                    input=entry,
                    source=resolved_source,
                    resolved_url=resolved.url,
                    filename=destination.name,
                    detected_type=final_type,
                    detection_confidence=classification.confidence,
                    detection_method=classification.method,
                    destination=str(destination),
                    ok=True,
                )
            )
        except Exception as exc:
            results.append(
                FetchItemResult(
                    input=entry,
                    source=entry_source or "direct",
                    resolved_url=None,
                    filename=None,
                    detected_type=None,
                    detection_confidence=None,
                    detection_method=None,
                    destination=None,
                    ok=False,
                    message=str(exc),
                )
            )

    _finish(results, json_output=ns.json_output)
    return 0 if all(item.ok for item in results) else 1


def entrypoint() -> None:
    raise SystemExit(run())
