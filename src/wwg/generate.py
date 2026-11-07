import json
import logging
from collections import Counter
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from string import punctuation

import hanlp
import hanlp.pretrained
import jieba
import numpy as np
import pkuseg
import thulac
import typer
import wordcloud
from hanlp.common.component import Component
from numpy.typing import NDArray
from PIL import Image

import wwg
from wwg.config import GenerateConfig, SplitUse

logger = logging.getLogger(__name__)

jieba.setLogLevel(logging.ERROR)

# Sentence punctuation and enclosing marks, excluding symbols used in names
# such as C++, C# and hyphenated words.
BOUNDARY_PUNCTUATION = "，。！？；：、,.!?;:（）()[]{}<>《》〈〉【】「」『』“”‘’\"'"


def strip_word_boundaries(word: str) -> str:
    start, end = 0, len(word)
    while start < end and (
        word[start].isspace() or word[start] in BOUNDARY_PUNCTUATION
    ):
        start += 1
    while end > start and (
        word[end - 1].isspace() or word[end - 1] in BOUNDARY_PUNCTUATION
    ):
        end -= 1
    return word[start:end]


def get_stopwords() -> set[str]:
    result = set(
        files(wwg).joinpath("stopwords.txt").read_text(encoding="utf-8").split("\n")
    )
    for p in punctuation:
        result.add(p)
    for p in "，。？《》；：”“’‘【】、——（）……￥！·「」":
        result.add(p)
    result.add(" ")
    result.add("\n")
    return result


def read_weibo(input_file: Path) -> list[tuple[str, datetime]]:
    records = []
    with input_file.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("expected a JSON object")
                if not isinstance(record.get("content"), str):
                    raise ValueError("content must be a string")
                if not isinstance(record.get("create_at"), str):
                    raise ValueError("create_at must be a string")
                create_at = datetime.strptime(record["create_at"], "%Y-%m-%dT%H:%M:%S")
            except ValueError as error:
                raise ValueError(f"{input_file}:{line_number}: {error}") from error
            records.append((record["content"], create_at))
    return records


def main(config: GenerateConfig) -> None:
    if config.input is None or not config.input.exists() or not config.input.is_file():
        raise typer.BadParameter(f"cannot read input file {config.input}")

    weibo_list = read_weibo(config.input)

    hantok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
    hantok.dict_force = None  # type: ignore
    hantok.dict_combine = None  # type: ignore
    dict_content: set[str] = set()
    if config.custom_dict is not None:
        logger.debug(f"load custom_dict from {config.custom_dict}")
        dict_content = {
            word.strip()
            for word in config.custom_dict.read_text(encoding="utf-8").splitlines()
            if word.strip()
        }
        jieba.load_userdict(str(config.custom_dict))
        thu = thulac.thulac(
            user_dict=str(config.custom_dict),
            seg_only=True,
            filt=True,
            rm_space=True,
            T2S=True,
        )
        pku = pkuseg.pkuseg(model_name="web", user_dict=str(config.custom_dict))
        hantok.dict_force = dict_content  # type: ignore
    else:
        thu = thulac.thulac(seg_only=True, filt=True, rm_space=True, T2S=True)
        pku = pkuseg.pkuseg(model_name="web")

    word_list = split_word(
        weibo_list,
        config.before,
        config.after,
        config.split_use,
        thu,
        pku,
        hantok,
        protected_words=dict_content,
    )

    mask = None
    if config.mask is not None and config.mask.exists():
        img = Image.open(str(config.mask)).convert("RGB")
        mask = np.array(img)
        logger.debug(f"load mask from {config.mask}")

    generate_wordcloud(word_list, config.output, config.max_word, config.font, mask)


def split_use_jieba(content: str) -> list[str]:
    return jieba.lcut(content, cut_all=True, HMM=True)


def split_use_thulac(thu: thulac.thulac, content: str) -> list[str]:
    return [word[0] for word in thu.cut(content)]


def split_use_pkuseg(pku: pkuseg.pkuseg, content: str) -> list[str]:
    return pku.cut(content)  # type: ignore


def split_use_hanlp(hantok: Component, content: str) -> list[str]:
    return hantok(content)


def split_word(
    weibo_list: list[tuple[str, datetime]],
    before: datetime,
    after: datetime,
    split_use: SplitUse,
    thu: thulac.thulac,
    pku: pkuseg.pkuseg,
    hantok: Component,
    protected_words: set[str] | None = None,
) -> list[str]:
    count, length = 0, 0
    stopwords = get_stopwords()
    protected_words = protected_words or set()
    exclude = {"网页链接", "网页", "链接", "jpg", ".jpg"}
    result: list[str] = []

    for content, create_at in weibo_list:
        if create_at < after or create_at > before:
            continue
        count += 1
        length += len(content)
        if split_use == SplitUse.PKUSEG:
            word_list = split_use_pkuseg(pku, content)
        elif split_use == SplitUse.THULAC:
            word_list = split_use_thulac(thu, content)
        elif split_use == SplitUse.HANLP:
            word_list = split_use_hanlp(hantok, content)
        else:  # SplitUse.JIEBA
            word_list = split_use_jieba(content)

        for word in word_list:
            word = strip_word_boundaries(word)
            if not word:
                continue
            if word in protected_words or (
                len(word) > 1
                and word not in stopwords
                and word not in exclude
                and any(letter.isalnum() for letter in word)
            ):
                result.append(word)

    # Keep rare dictionary entries; ordinary words still need two occurrences.
    counter = Counter(result)
    result = [word for word in result if word in protected_words or counter[word] > 1]

    logger.debug(
        f"using {count} Weibo posts with {length} characters, {len(result)} words"
    )
    counter = Counter(result)
    logger.debug(f"most common: {counter.most_common(30)}")
    return result


def generate_wordcloud(
    word_list: list[str],
    output: Path,
    max_word: int,
    font_path: Path | None = None,
    mask: NDArray[np.uint8] | None = None,
) -> None:
    # color_func = wordcloud.get_single_color_func("#D90E2C")
    cloud = wordcloud.WordCloud(
        font_path=str(font_path) if font_path is not None else None,
        mask=mask,
        background_color="white",
        prefer_horizontal=1,
        max_words=max_word,
        scale=2,
        # color_func=color_func,
        colormap="ocean",
    )
    cloud.generate_from_frequencies(Counter(word_list))
    cloud.to_file(output)
