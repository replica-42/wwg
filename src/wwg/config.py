import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import dacite
import tomli


@dataclass
class CrawlConfig:
    uid: str
    cookies: str
    max_page: int = -1
    after: datetime = datetime(datetime.now().year, 1, 1)
    output: Path = Path("weibo.jsonl").resolve()


@dataclass
class GenerateConfig:
    input: Path | None = None
    font: Path | None = None
    mask: Path | None = None
    custom_dict: Path | None = None
    output: Path = Path("weibo.png").resolve()


@dataclass
class Config:
    crawl: CrawlConfig
    generate: GenerateConfig


def config_logger(verbose: bool) -> None:
    logger = logging.getLogger("wwg")
    formatter = logging.Formatter(
        "%(name)-16s %(lineno)-4d %(levelname)-8s %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(handler)


def init_config(config_file: Path, verbose: bool) -> Config:
    config_logger(verbose)
    config_str = config_file.read_text(encoding="utf-8")
    config_dict = tomli.loads(config_str)
    return dacite.from_dict(Config, config_dict, config=dacite.Config(cast=[Path]))
