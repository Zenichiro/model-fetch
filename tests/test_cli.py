import pytest

from model_fetch.cli import _build_entries, run


def test_build_entries_accepts_single_url() -> None:
    entries = _build_entries(["https://example.com/model.safetensors"], None)
    assert entries == ["https://example.com/model.safetensors"]


def test_build_entries_accepts_civitai_pair() -> None:
    entries = _build_entries(["civitai", "2807896"], None)
    assert entries == ["civitai 2807896"]


def test_build_entries_rejects_extra_args() -> None:
    with pytest.raises(Exception):
        _build_entries(["one", "two", "three"], None)


def test_run_help_exits_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        run(["--help"])
    assert exc.value.code == 0
    assert "model-fetch" in capsys.readouterr().out
