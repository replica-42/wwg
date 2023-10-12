import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import dacite
import tomli

logger = logging.getLogger(__name__)


@dataclass
class CrawlConfig:
    uid: str | None = None
    cookies: str | None = None
    original_only: bool = False
    max_page: int = -1
    after: datetime = datetime(datetime.now().year, 1, 1)
    output: Path = Path("weibo.jsonl").resolve()


@dataclass
class GenerateConfig:
    input: Path | None = None
    font: Path | None = None
    mask: Path | None = None
    custom_dict: Path | None = None
    max_word: int = 400
    output: Path = Path("weibo.png").resolve()


@dataclass
class Config:
    crawl: CrawlConfig = field(default_factory=CrawlConfig)
    generate: GenerateConfig = field(default_factory=GenerateConfig)


def init_logger(verbose: bool) -> None:
    logger = logging.getLogger("wwg")
    formatter = logging.Formatter(
        "%(name)-16s %(lineno)-4d %(levelname)-8s %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(handler)


def init_config(config_file: Path) -> Config:
    config_str = config_file.read_text(encoding="utf-8")
    config_dict = tomli.loads(config_str)
    return dacite.from_dict(
        Config,
        config_dict,
        config=dacite.Config(type_hooks={Path: lambda s: Path(s).resolve()}),
    )


def update_config(config: object, name: str, value: object | None) -> None:
    if value is not None:
        setattr(config, name, value)
