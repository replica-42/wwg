from pathlib import Path

import pytest
import requests

from wwg import __main__ as cli


@pytest.mark.parametrize("command", ["crawl", "generate"])
@pytest.mark.parametrize("answer", ["n\n", "\n", "y\n"], ids=["no", "default", "yes"])
def test_overwrite_confirmation_for_both_commands(cli_runner, mocker, command, answer):
    source = Path("input.jsonl")
    source.write_text("{}\n", encoding="utf-8")
    output = Path("output.txt").resolve()
    output.write_text("previous data", encoding="utf-8")
    args = [command, "--output", str(output)]
    if command == "crawl":
        args += ["--uid", "123", "--cookies", "test"]
    else:
        args += ["--input", str(source.resolve())]
    module = cli.wwg.crawl if command == "crawl" else cli.wwg.generate
    run = mocker.patch.object(
        module,
        "main",
        side_effect=lambda config: config.output.write_text("new data"),
    )
    result = cli_runner.invoke(cli.app, args, input=answer)
    assert "[y/N]" in result.output
    if answer == "y\n":
        assert result.exit_code == 0, result.output
        run.assert_called_once()
        assert output.read_text() == "new data"
    else:
        assert result.exit_code != 0
        run.assert_not_called()
        assert output.read_text() == "previous data"


def test_new_output_does_not_prompt(cli_runner, mocker):
    run = mocker.patch.object(cli.wwg.crawl, "main")
    result = cli_runner.invoke(
        cli.app,
        ["crawl", "--uid", "123", "--cookies", "test", "--output", "new.jsonl"],
    )
    assert result.exit_code == 0, result.output
    assert "Overwrite?" not in result.output
    run.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        requests.ConnectionError("connection failed"),
        PermissionError("permission denied"),
        ValueError("input.jsonl:2: invalid record"),
    ],
    ids=["network", "permission", "invalid-input"],
)
def test_expected_errors_have_nonzero_exit_and_readable_message(mocker, capsys, error):
    mocker.patch.object(cli, "app", side_effect=error)
    with pytest.raises(SystemExit) as result:
        cli.entry()
    assert result.value.code == 1
    assert capsys.readouterr().err == f"Error: {error}\n"
