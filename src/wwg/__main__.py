import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

import wwg.crawl
from wwg.config import Config, init_config

logger = logging.getLogger("wwg")

app = typer.Typer()

CONFIG: Config | None = None


@app.callback()
def main(
    verbose: bool = False,
    config_file: Annotated[
        Path,
        typer.Option(exists=True, dir_okay=False, readable=True, resolve_path=True),
    ] = Path("config.toml"),
) -> None:
    global CONFIG
    CONFIG = init_config(config_file, verbose)


@app.command(
    help="Crawl Weibo content. If options are not specified explicitly, values in the configuration file are used."  # noqa
)
def crawl(
    ctx: typer.Context,
    uid: Annotated[
        Optional[str],
        typer.Option(
            help="weibo user id",
        ),
    ] = None,
    cookies: Annotated[Optional[str], typer.Option(help="weibo.cn cookies")] = None,
    max_page: Annotated[
        Optional[int], typer.Option(help="maximum number of crawled pages")
    ] = None,
    after: Annotated[
        Optional[datetime],
        typer.Option(help="crawl Weibo posts published later than this time"),
    ] = None,
    dest: Annotated[
        Optional[Path],
        typer.Option(help="crawling result storage path (format: JSONL)"),
    ] = None,
) -> None:
    if CONFIG is None:
        logger.error("Configuration initialization failed")
        raise typer.Exit(code=-1)
    for name, value in ctx.params.items():
        if value is not None:
            CONFIG.crawl.__setattr__(name, value)
    wwg.crawl.main(CONFIG)


def entry() -> None:
    app()


if __name__ == "__main__":
    entry()
