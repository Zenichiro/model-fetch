from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("~/.config/model-fetch/.env").expanduser()


@dataclass(frozen=True)
class AppConfig:
    model_base_dir: Path = Path("/mnt/ai-share/image-models")
    temp_download_dir: Path = Path("/tmp/model-fetch")
    safetch_path: str = "safetch"
    safetch_no_resume: bool = False
    proxy_host: str = "127.0.0.1"
    proxy_port: int = 8888
    civitai_api_key: str | None = None
    civitai_use_mirror: bool = False
    civitai_use_proxy: bool = True
    civitai_gluetun_enabled: bool = False
    huggingface_api_token: str | None = None
    huggingface_use_proxy: bool = False
    huggingface_gluetun_enabled: bool = False


def _parse_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH
    data = _load_env_file(path)

    return AppConfig(
        model_base_dir=Path(data.get("MODEL_BASE_DIR") or "/mnt/ai-share/image-models"),
        temp_download_dir=Path(data.get("TEMP_DOWNLOAD_DIR") or "/tmp/model-fetch"),
        safetch_path=data.get("SAFETCH_PATH") or "safetch",
        safetch_no_resume=_parse_bool(data.get("SAFETCH_NO_RESUME"), False),
        proxy_host=data.get("PROXY_HOST") or "127.0.0.1",
        proxy_port=int(data.get("PROXY_PORT") or 8888),
        civitai_api_key=data.get("CIVITAI_API_KEY") or None,
        civitai_use_mirror=_parse_bool(data.get("CIVITAI_USE_MIRROR"), False),
        civitai_use_proxy=_parse_bool(data.get("CIVITAI_USE_PROXY"), True),
        civitai_gluetun_enabled=_parse_bool(data.get("CIVITAI_GLUETUN_ENABLED"), False),
        huggingface_api_token=data.get("HUGGINGFACE_API_TOKEN") or None,
        huggingface_use_proxy=_parse_bool(data.get("HUGGINGFACE_USE_PROXY"), False),
        huggingface_gluetun_enabled=_parse_bool(data.get("HUGGINGFACE_GLUETUN_ENABLED"), False),
    )
