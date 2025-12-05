import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

import wwg.crawl
import wwg.generate
from wwg.config import Config, init_config, init_logger, update_config, SplitUse

logger = logging.getLogger("wwg")

app = typer.Typer()

CONFIG: Config = Config()


@app.callback()
def main(
    verbose: bool = False,
    config_file: Annotated[
        Optional[Path],
        typer.Option(exists=True, dir_okay=False, readable=True, resolve_path=True),
    ] = None,
) -> None:
    global CONFIG

    init_logger(verbose)
    if config_file is not None:
        logger.debug(f"load configuration from {config_file}")
        CONFIG = init_config(config_file)
    elif (config_file := Path("config.toml").resolve()).exists():
        logger.debug(f"load configuration from default {config_file}")
        CONFIG = init_config(config_file)
    else:
        logger.debug("using default configuration")


@app.command(
    help="Crawl Weibo content. "
    "If options are not specified explicitly, "
    "values in the configuration file are used."
)
def crawl(
    uid: Annotated[
        Optional[str],
        typer.Option(
            help="Weibo user id",
        ),
    ] = None,
    cookies: Annotated[Optional[str], typer.Option(help="weibo.cn cookies")] = None,
    original_only: Annotated[
        Optional[bool], typer.Option(help="only crawl original Weibo")
    ] = None,
    start_page: Annotated[Optional[int], typer.Option(help="crawl start page")] = None,
    max_page: Annotated[
        Optional[int], typer.Option(help="maximum number of crawled pages")
    ] = None,
    after: Annotated[
        Optional[datetime],
        typer.Option(help="crawl Weibo posts published later than this time"),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            help="crawling result storage path (format: JSONL)", resolve_path=True
        ),
    ] = None,
) -> None:
    config = CONFIG.crawl
    update_config(config, "uid", uid)
    update_config(config, "cookies", cookies)
    update_config(config, "original_only", original_only)
    update_config(config, "start_page", start_page)
    update_config(config, "max_page", max_page)
    update_config(config, "after", after)
    update_config(config, "output", output)
    if config.uid is None or config.uid == "":
        raise typer.BadParameter(
            "uid is missing, "
            "please provide it via command line argument or configuration file",
        )
    if config.cookies is None or config.cookies == "":
        raise typer.BadParameter(
            "cookie is missing, "
            "please provide it via command line argument or configuration file"
        )
    if config.start_page < 1:
        raise typer.BadParameter("start page must greater than 1")
    logger.debug(f"uid: {config.uid}")
    logger.debug(f"original_only: {config.original_only}")
    logger.debug(f"start_page: {config.start_page}")
    logger.debug(f"max_page: {config.max_page}")
    logger.debug(f"after: {config.after}")
    logger.debug(f"output: {config.output}")
    wwg.crawl.main(config)


@app.command(
    help="Generate Weibo wordcloud. "
    "If options are not specified explicitly, "
    "values in the configuration file are used."
)
def generate(
    input: Annotated[
        Optional[Path],
        typer.Option(
            help="crawled weibo path (format: JSONL). "
            "If this option is not provided, "
            "the value of crawl.output is used",
            exists=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    font: Annotated[
        Optional[Path],
        typer.Option(
            help="wordcloud font path",
            exists=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    mask: Annotated[
        Optional[Path],
        typer.Option(
            help="wordcloud mask image path",
            exists=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    custom_dict: Annotated[
        Optional[Path],
        typer.Option(
            help="jieba custom dict path",
            exists=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    before: Annotated[
        Optional[datetime],
        typer.Option(help="using Weibo posts published earlier than this time"),
    ] = None,
    after: Annotated[
        Optional[datetime],
        typer.Option(help="using Weibo posts published later than this time"),
    ] = None,
    max_word: Annotated[
        Optional[int],
        typer.Option(
            help="wordcloud max word num",
            callback=lambda x: max(1, x) if x is not None else None,
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            help="generated wordcloud path",
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    split_use: Annotated[
        Optional[SplitUse],
        typer.Option(
            help="word segmentation tool, choose from 'jieba', 'thulac', 'pkuseg'",
        )
    ] = None,
) -> None:
    config = CONFIG.generate
    update_config(config, "input", input)
    update_config(config, "font", font)
    update_config(config, "mask", mask)
    update_config(config, "custom_dict", custom_dict)
    update_config(config, "before", before)
    update_config(config, "after", after)
    update_config(config, "max_word", max_word)
    update_config(config, "output", output)
    update_config(config, "split_use", split_use)

    if config.input is None:
        config.input = CONFIG.crawl.output

    if config.input is None:
        raise typer.BadParameter(
            "input is None, "
            "please specify via command line parameters "
            "or configuration file entries"
        )

    logger.debug(f"input: {config.input}")
    logger.debug(f"font: {config.font}")
    logger.debug(f"mask: {config.mask}")
    logger.debug(f"custom_dict: {config.custom_dict}")
    logger.debug(f"before: {config.before}")
    logger.debug(f"after: {config.after}")
    logger.debug(f"max_word: {config.max_word}")
    logger.debug(f"output: {config.output}")
    logger.debug(f"split_use: {config.split_use}")

    wwg.generate.main(CONFIG.generate)


def entry() -> None:
    app()


if __name__ == "__main__":
    entry()
