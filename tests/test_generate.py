import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime

import pytest
from PIL import Image

from wwg import generate
from wwg.config import GenerateConfig, SplitUse


@pytest.fixture
def filter_words(mocker):
    def run(words, protected_words=None, backend=SplitUse.HANLP):
        mocker.patch.object(generate, "split_use_jieba", return_value=words)
        thu, pku, hantok = mocker.Mock(), mocker.Mock(), mocker.Mock()
        thu.cut.return_value = [(word, "") for word in words]
        pku.cut.return_value = words
        hantok.return_value = words
        return generate.split_word(
            [("sample", datetime(2026, 1, 1))],
            datetime(2027, 1, 1),
            datetime(2025, 1, 1),
            backend,
            thu,
            pku,
            hantok,
            protected_words=protected_words,
        )

    return run


@pytest.mark.parametrize("backend", list(SplitUse))
def test_dictionary_words_survive_single_character_stopword_and_frequency_filters(
    filter_words, backend
):
    words = ["侑", "瑛", "soyo", "たきな", "33号远征队", "的"]
    assert filter_words(words, set(words), backend) == words


def test_whole_words_are_not_removed_based_on_their_characters(filter_words):
    words = ["soyo", "mio", "不好"] * 2
    assert filter_words(words) == words


@pytest.mark.parametrize(
    "word",
    [
        "只能",
        "都是",
        "一点",
        "一遍",
        "有种",
        "有没有",
        "能不能",
        "那种",
        "又是",
        "尤其是",
        "没什么",
        "是因为",
    ],
)
def test_low_information_words_are_removed_unless_protected(filter_words, word):
    assert filter_words([word, word, "喜欢", "喜欢"]) == ["喜欢", "喜欢"]
    assert filter_words([word], {word}) == [word]


def test_added_stopwords_only_match_whole_tokens(filter_words):
    assert filter_words(["一点", "那种", "一点点", "那种感觉"] * 2) == [
        "一点点",
        "那种感觉",
        "一点点",
        "那种感觉",
    ]


@pytest.mark.parametrize("word", ["战斗", "总结", "相信", "认真", "novel", "useful"])
def test_restored_content_words_still_require_two_occurrences(filter_words, word):
    assert filter_words([word, word]) == [word, word]
    assert filter_words([word]) == []


def test_longer_words_do_not_remove_shorter_words(filter_words):
    words = ["咖啡", "咖啡机", "可爱", "小可爱", "艾莉", "艾莉卡"] * 2
    assert filter_words(words) == words


@pytest.mark.parametrize("backend", list(SplitUse))
def test_generic_words_removed_without_losing_personal_expression(
    filter_words, backend
):
    generic = ["感觉", "真的", "剧情", "作品", "博主", "体验", "东西", "回来"]
    personal = [
        "喜欢",
        "讨厌",
        "可爱",
        "希望",
        "不赖",
        "有意思",
        "力竭",
        "遗憾",
        "焦虑",
        "难过",
        "心情",
        "生活",
        "关系",
        "意义",
        "时间",
        "感受",
        "咖啡",
        "下班",
        "终末地",
    ]
    assert filter_words((generic + personal) * 2, backend=backend) == personal * 2
    assert filter_words(["剧情"], {"剧情"}, backend=backend) == ["剧情"]


def test_generic_stopwords_do_not_remove_compound_names(filter_words):
    words = ["故事", "游戏", "世界观", "剧情片", "游戏机", "故事模式"] * 2
    assert filter_words(words) == ["世界观", "剧情片", "游戏机", "故事模式"] * 2


def test_boundary_cleanup_merges_variants_before_frequency_filter(filter_words):
    assert Counter(
        filter_words(["たきな", "。たきな", "たきな）", " \t「 たきな 」\u3000"])
    ) == {"たきな": 4}


def test_boundary_cleanup_precedes_dictionary_lookup(filter_words):
    assert filter_words(["（侑）", "「soyo」"], {"侑", "soyo"}) == ["侑", "soyo"]


def test_internal_punctuation_and_name_symbols_are_preserved(filter_words):
    words = ["C++", "C#", "Sea-Bed", "v1.2", "O'Connor"] * 2
    assert filter_words(words) == words


def test_ordinary_stopwords_short_words_and_noise_are_still_removed(filter_words):
    words = [
        "可以",
        "爱",
        "网页链接",
        ".jpg",
        "",
        " \t\n",
        "（。！？）",
        "——",
        "✨✨",
    ] * 2
    assert filter_words(words + ["稀有候选", "正常候选", "正常候选"]) == [
        "正常候选",
        "正常候选",
    ]


def test_date_filter_runs_before_protected_word_frequency_handling(mocker):
    hantok = mocker.Mock(return_value=["侑"])
    assert generate.split_word(
        [
            ("excluded", datetime(2025, 12, 31)),
            ("start", datetime(2026, 1, 1)),
            ("end", datetime(2026, 1, 2)),
            ("excluded", datetime(2026, 1, 3)),
        ],
        datetime(2026, 1, 2),
        datetime(2026, 1, 1),
        SplitUse.HANLP,
        None,
        None,
        hantok,
        protected_words={"侑"},
    ) == ["侑", "侑"]
    assert hantok.call_args_list == [mocker.call("start"), mocker.call("end")]


def test_main_passes_custom_dictionary_to_filtering(source_file, tmp_path, mocker):
    source_file.write_text(
        json.dumps({"content": "侑 soyo", "create_at": "2026-01-01T00:00:00"}),
        encoding="utf-8",
    )
    dictionary = tmp_path / "dict.txt"
    dictionary.write_text("\n侑\r\nsoyo\r\n\n", encoding="utf-8")
    mocker.patch.object(generate.jieba, "load_userdict")
    hanlp = mocker.patch.object(generate.hanlp, "load")
    hanlp.return_value.return_value = ["侑", "soyo"]
    mocker.patch.object(generate.thulac, "thulac")
    mocker.patch.object(generate.pkuseg, "pkuseg")
    cloud = mocker.patch.object(generate, "generate_wordcloud")

    generate.main(
        GenerateConfig(
            input=source_file,
            custom_dict=dictionary,
            split_use=SplitUse.HANLP,
            before=datetime(2027, 1, 1),
        )
    )

    assert Counter(cloud.call_args.args[0]) == {"侑": 1, "soyo": 1}
    assert hanlp.return_value.dict_force == {"侑", "soyo"}
    hanlp.return_value.assert_called_once_with("侑 soyo")


def test_real_hanlp_segmentation_and_filtering(source_file, tmp_path, mocker):
    model_path = os.environ.get("WWG_TEST_HANLP_MODEL")
    if not model_path:
        pytest.skip("Set WWG_TEST_HANLP_MODEL to run real HanLP inference")
    load_model = generate.hanlp.load
    source_file.write_text(
        json.dumps(
            {
                "content": "soyo喜欢侑。たきな也很可爱。游戏剧情很好。游戏剧情很可爱。",
                "create_at": "2026-01-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )
    dictionary = tmp_path / "dict.txt"
    dictionary.write_text("侑\nsoyo\nたきな\n", encoding="utf-8")
    mocker.patch.object(
        generate.hanlp, "load", side_effect=lambda _: load_model(model_path, devices=-1)
    )
    mocker.patch.object(generate.jieba, "load_userdict")
    mocker.patch.object(generate.thulac, "thulac")
    mocker.patch.object(generate.pkuseg, "pkuseg")
    cloud = mocker.patch.object(generate, "generate_wordcloud")

    generate.main(
        GenerateConfig(
            input=source_file,
            custom_dict=dictionary,
            split_use=SplitUse.HANLP,
            before=datetime(2027, 1, 1),
        )
    )

    assert Counter(cloud.call_args.args[0]) == {
        "soyo": 1,
        "侑": 1,
        "たきな": 1,
        "可爱": 2,
    }


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
    hanlp.return_value.return_value = ["apple", "banana", "apple", "banana"]
    thulac = mocker.patch.object(generate.thulac, "thulac")
    pkuseg = mocker.patch.object(generate.pkuseg, "pkuseg")
    generate.main(
        GenerateConfig(
            input=source_file,
            output=output,
            before=datetime(2027, 1, 1),
            split_use=SplitUse.HANLP,
        )
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
