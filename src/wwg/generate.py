import json
import logging
from collections import Counter
from importlib.resources import files
from pathlib import Path
from string import punctuation

import jieba
import numpy as np
import typer
import wordcloud
from PIL import Image

import wwg
from wwg.config import GenerateConfig

logger = logging.getLogger(__name__)


def get_stopwords() -> set[str]:
    result = set(
        files(wwg).joinpath("stopwords.txt").read_text(encoding="utf-8").split("\n")
    )
    for p in punctuation:
        result.add(p)
    for p in "，。？《》；：”“’‘【】、——（）……￥！·":
        result.add(p)
    result.add(" ")
    result.add("\n")
    return result


def main(config: GenerateConfig) -> None:
    if config.input is None or not config.input.exists() or not config.input.is_file():
        raise typer.BadParameter(f"cannor read input file {config.input}")
    if config.custom_dict is not None:
        jieba.load_userdict(str(config.custom_dict))
    weibo_list = config.input.read_text(encoding="utf-8").split("\n")
    weibo_list = [weibo.strip() for weibo in weibo_list]
    weibo_list = [weibo for weibo in weibo_list if weibo != ""]
    word_list = split_word(weibo_list)
    mask = None
    if config.mask is not None and config.mask.exists():
        img = Image.open(str(config.mask)).convert("RGB")
        mask = np.array(img)
        logger.debug(f"load mask from {config.mask}")
    generate_wordcloud(word_list, config.output, config.font, mask)


def split_word(weibo_list: list[str]) -> list[str]:
    stopwords = get_stopwords()
    result: list[str] = []
    for weibo in weibo_list:
        try:
            content: dict[str, str] = json.loads(weibo)
        except json.JSONDecodeError:
            logger.error(f"cannot parse {weibo}")
            continue

        word_list = jieba.lcut(content["content"], cut_all=True, HMM=True)
        for word in word_list:
            if (
                word not in stopwords
                and word != ""
                and not all(letter in stopwords for letter in word)
            ):
                result.append(word)
    # remove word that only appears once
    counter = Counter(result)
    need_remove = set(x for x, y in counter.items() if y == 1)
    result = [word for word in result if word not in need_remove]

    unique_result = set(result)
    need_remove = set()
    for s in unique_result:
        for t in unique_result:
            if t in s and len(s) > len(t) and (len(t) == 1 or len(s) - len(t) == 1):
                need_remove.add(t)

    result = [word for word in result if word not in need_remove]

    return result


def generate_wordcloud(
    word_list: list[str],
    output: Path,
    font_path: Path | None = None,
    mask: np.ndarray | None = None,
):
    color_func = wordcloud.get_single_color_func("deepskyblue")
    cloud = wordcloud.WordCloud(
        font_path=str(font_path) if font_path is not None else None,
        mask=mask,
        background_color="white",
        prefer_horizontal=1,
        max_words=400,
        scale=2,
        color_func=color_func,
    )
    cloud.generate(" ".join(word_list))
    cloud.to_file(output)
