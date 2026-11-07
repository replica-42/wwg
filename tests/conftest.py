import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wwg import __main__ as cli
from wwg.config import Config


@pytest.fixture
def cli_runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "CONFIG", Config())
    monkeypatch.setattr(cli, "init_logger", lambda verbose: None)
    return CliRunner()


@pytest.fixture
def source_file(tmp_path):
    return tmp_path / "weibo.jsonl"


@pytest.fixture
def analyze_script():
    # This standalone script is outside the installed wwg package.
    path = Path(__file__).resolve().parents[1] / "scripts" / "analyze.py"
    spec = importlib.util.spec_from_file_location("wwg_analyze_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
