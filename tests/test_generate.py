import json
import os
import subprocess
import sys
from datetime import datetime

import pytest
from PIL import Image

from wwg import generate
from wwg.config import GenerateConfig


def test_reads_valid_records_with_trailing_newline(source_file):
    source_file.write_text(
        json.dumps(
            {"id": "123", "content": "测试微博", "create_at": "2026-01-01T12:34:56"}
        )
        + "\n",
        encoding="utf-8",
    )
    assert generate.read_weibo(source_file) == [
        ("测试微博", datetime(2026, 1, 1, 12, 34, 56))
    ]


@pytest.mark.parametrize(
    "record",
    [
        "not json",
        "null",
        "[]",
        "{}",
        json.dumps({"content": 1, "create_at": "2026-01-01T00:00:00"}),
        json.dumps({"content": "text", "create_at": 1}),
        json.dumps({"content": "text", "create_at": "invalid"}),
        "",
    ],
    ids=[
        "syntax",
        "null",
        "array",
        "missing-fields",
        "content-type",
        "date-type",
        "date-format",
        "blank",
    ],
)
def test_invalid_record_stops_with_file_and_line_number(source_file, record):
    valid = json.dumps({"content": "valid", "create_at": "2026-01-01T00:00:00"})
    source_file.write_text(f"{valid}\n{record}\n{valid}\n", encoding="utf-8")
    with pytest.raises(ValueError) as result:
        generate.read_weibo(source_file)
    assert f"{source_file}:2:" in str(result.value)


def test_validation_happens_before_loading_models(source_file, mocker):
    source_file.write_text("{}\n", encoding="utf-8")
    load = mocker.patch.object(generate.hanlp, "load")
    with pytest.raises(ValueError):
        generate.main(GenerateConfig(input=source_file))
    load.assert_not_called()


def test_valid_file_generates_image_and_initializes_all_backends(
    source_file, tmp_path, mocker
):
    source_file.write_text(
        json.dumps(
            {
                "content": "apple banana apple banana",
                "create_at": "2026-01-01T00:00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "cloud.png"
    hanlp = mocker.patch.object(generate.hanlp, "load")
    thulac = mocker.patch.object(generate.thulac, "thulac")
    pkuseg = mocker.patch.object(generate.pkuseg, "pkuseg")
    generate.main(
        GenerateConfig(input=source_file, output=output, before=datetime(2027, 1, 1))
    )
    hanlp.assert_called_once()
    thulac.assert_called_once()
    pkuseg.assert_called_once()
    with Image.open(output) as image:
        assert image.format == "PNG"


def test_invalid_input_exits_cleanly_from_real_cli(source_file, tmp_path):
    source_file.write_text("{}\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "wwg", "generate", "--input", str(source_file)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert f"{source_file}:1:" in result.stderr
    assert "Traceback" not in result.stderr


def test_wordcloud_preserves_supplied_words_and_frequencies(tmp_path, monkeypatch):
    output = tmp_path / "cloud.png"
    saved = []
    to_file = generate.wordcloud.WordCloud.to_file

    def save(cloud, path):
        saved.append(dict(cloud.words_))
        return to_file(cloud, path)

    monkeypatch.setattr(generate.wordcloud.WordCloud, "to_file", save)
    generate.generate_wordcloud(
        ["自然"] * 100 + ["语言"] * 50 + ["the"] * 25, output, 20
    )
    assert saved == [{"自然": 1.0, "语言": 0.5, "the": 0.25}]
    with Image.open(output) as image:
        assert image.format == "PNG"
