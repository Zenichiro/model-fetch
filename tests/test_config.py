from pathlib import Path

from model_fetch.config import AppConfig, DEFAULT_CONFIG_PATH, load_config


def test_load_config_defaults_when_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.env")
    assert config == AppConfig()


def test_load_config_from_env_file(tmp_path: Path) -> None:
    config_path = tmp_path / ".env"
    config_path.write_text(
        "\n".join(
            [
                "MODEL_BASE_DIR=/models",
                "TEMP_DOWNLOAD_DIR=/tmp/model-fetch-test",
                "SAFETCH_PATH=/usr/local/bin/safetch",
                "PROXY_HOST=10.0.0.5",
                "PROXY_PORT=9999",
                "CIVITAI_USE_PROXY=false",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert str(config.model_base_dir) == "/models"
    assert str(config.temp_download_dir) == "/tmp/model-fetch-test"
    assert config.safetch_path == "/usr/local/bin/safetch"
    assert config.proxy_host == "10.0.0.5"
    assert config.proxy_port == 9999
    assert config.civitai_use_proxy is False


def test_default_config_path_constant() -> None:
    assert str(DEFAULT_CONFIG_PATH).endswith(".config/model-fetch/.env")
