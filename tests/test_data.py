import json
import os
import subprocess
import sys

import pytest

from wwg import __main__ as cli
from wwg import data


@pytest.mark.parametrize(
    "location",
    ["no-config", "default-config", "explicit-relative", "explicit-absolute"],
)
def test_cli_passes_configured_data_directory(cli_runner, tmp_path, mocker, location):
    source = tmp_path / "input.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    args = []
    expected = tmp_path / "data"
    if location != "no-config":
        expected = tmp_path / "model data"
        value = str(expected) if location == "explicit-absolute" else "model data"
        config = tmp_path / "config.toml"
        if location.startswith("explicit"):
            config = tmp_path / "settings" / "custom.toml"
            config.parent.mkdir()
            args += ["--config-file", str(config)]
        config.write_text(f"data_dir = {json.dumps(value)}\n", encoding="utf-8")
    run = mocker.patch.object(cli.wwg.generate, "main")
    result = cli_runner.invoke(cli.app, args + ["generate", "--input", str(source)])
    assert result.exit_code == 0, result.output
    run.assert_called_once_with(cli.CONFIG.generate)
    assert data.DATA_DIR == expected


@pytest.mark.parametrize("external_homes", [False, True])
def test_backends_use_configured_directory_before_import(tmp_path, external_homes):
    startup = tmp_path / "startup directory"
    startup.mkdir()
    later = tmp_path / "later"
    later.mkdir()
    names = (
        "HANLP_HOME",
        "PKUSEG_HOME",
        "HF_HOME",
        "HF_HUB_CACHE",
        "HF_ASSETS_CACHE",
        "HF_XET_CACHE",
        "TORCH_HOME",
    )
    env = {key: value for key, value in os.environ.items() if key not in names}
    if external_homes:
        env.update({name: str(tmp_path / "old" / name) for name in names})

    # A fresh interpreter exercises backend import-time resource paths.
    # The editable installation supplies wwg; no source path injection.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import json
import os
import sys
from pathlib import Path

from wwg import __main__
from wwg.data import configure_data_paths

assert 'hanlp' not in sys.modules
assert 'pkuseg' not in sys.modules

data = Path.cwd() / 'model data'
assert not data.exists(), 'Importing the CLI must not create data directories'
names = ('HF_HOME', 'HF_HUB_CACHE', 'HF_ASSETS_CACHE', 'HF_XET_CACHE', 'TORCH_HOME')
before = {name: os.environ.get(name) for name in names}
configure_data_paths(data)
assert {name: os.environ.get(name) for name in names} == before
from wwg import generate
from hanlp.utils.io_util import get_resource, hanlp_home
from inspect import signature
assert signature(get_resource).parameters['save_dir'].default == str(data / 'hanlp')
os.chdir(sys.argv[1])
(data / 'jieba').mkdir(parents=True)
generate.jieba.dt.tmp_dir = str(data / 'jieba')
tokens = generate.split_use_jieba('自然语言处理')
assert tokens
assert list((data / 'jieba').glob('*.cache'))
print(json.dumps({
    'hanlp': hanlp_home(),
    'pkuseg': generate.pkuseg.config.pkuseg_home,
    'jieba': generate.jieba.dt.tmp_dir,
}))
""",
            str(later),
        ],
        cwd=startup,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    data = startup / "model data"
    assert json.loads(result.stdout) == {
        "hanlp": str(data / "hanlp"),
        "pkuseg": str(data / "pkuseg"),
        "jieba": str(data / "jieba"),
    }
    assert not (startup / "data").exists()
    assert not (later / "data").exists()
    assert not (tmp_path / "old").exists()
