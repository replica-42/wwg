import json
import logging
import random
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Generator

import requests
from bs4 import BeautifulSoup, Tag

from wwg.config import CrawlConfig

logger = logging.getLogger(__name__)
time_pattern = r"(?:(?:今天)|(?:(?P<month>\d\d)月(?P<day>\d\d)日)|(?:(?P<yyyy>\d\d\d\d)-(?P<MM>\d\d)-(?P<dd>\d\d)))\s(?P<HH>\d\d):(?P<mm>\d\d)(?::(?P<ss>\d\d))?.*"  # noqa
base_url = "https://weibo.cn"


@dataclass
class Weibo:
    id: str
    content: str
    create_at: datetime

    def __str__(self) -> str:
        d = asdict(self)
        d["create_at"] = self.create_at.strftime("%Y-%m-%dT%H:%M:%S")
        return json.dumps(d, ensure_ascii=False)


def retry_get(
    url: str,
    headers: dict[str, str],
    predictor: Callable[[requests.Response], bool],
    max_retries: int = 3,
) -> requests.Response | None:
    response = requests.get(url, headers=headers)
    i = 0
    wait_time = 1
    while i < max_retries and not predictor(response):
        logger.debug(f"get {url} failed, retry after {wait_time}s")
        time.sleep(wait_time)
        wait_time *= 2
        response = requests.get(url, headers=headers)
        i += 1
    return response if predictor(response) else None


def weibo_predictor(tag: Tag) -> bool:
    return (
        tag.name == "div"
        and tag.has_attr("class")
        and "c" in tag.attrs["class"]
        and tag.has_attr("id")
        and tag.attrs["id"].startswith("M_")
    )


def content_predictor(tag: Tag) -> bool:
    return tag.name == "span" and tag.has_attr("class") and "ctt" in tag.attrs["class"]


def create_time_predictor(tag: Tag) -> bool:
    return tag.name == "span" and tag.has_attr("class") and "ct" in tag.attrs["class"]


def full_text_predictor(tag: Tag) -> bool:
    return tag.name == "a" and tag.has_attr("href") and tag.text.strip() == "全文"


def next_page_predictor(tag: Tag) -> bool:
    return tag.name == "a" and tag.has_attr("href") and tag.text.strip() == "下页"


def main(config: CrawlConfig) -> None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.33",  # noqa
        "Cookie": config.cookies,
        "Accept": "text/html",
    }
    url = f"{base_url}/{config.uid}/profile"
    with open(config.output, "w", encoding="utf-8") as f:
        current_page = 1
        flag = True
        while flag and (config.max_page < 0 or current_page <= config.max_page):
            weibo_iter = crawl_page(url, headers)
            try:
                while True:
                    weibo = next(weibo_iter)
                    if weibo.create_at < config.after:
                        flag = False
                        break
                    f.write(f"{weibo}\n")
            except StopIteration as e:
                if isinstance((next_url := e.value), str):
                    url = f"{base_url}{next_url}"
                else:
                    break
            current_page += 1
            # sleep 1~2 s
            time.sleep(1 + random.random())


def crawl_page(url: str, headers: dict[str, str]) -> Generator[Weibo, None, str | None]:
    if (
        response := retry_get(url, headers, lambda r: r.status_code == 200)
    ) is not None:
        soup = BeautifulSoup(
            response.text.removeprefix('<?xml version="1.0" encoding="UTF-8"?>'),
            "html5lib",
        )
        weibo_list: list[Tag] = soup.find_all(weibo_predictor)
        for weibo in weibo_list:
            weibo_id = weibo.attrs["id"].removeprefix("M_")
            if (
                full_text := weibo.find(full_text_predictor)
            ) is not None and isinstance(full_text, Tag):
                yield from crawl_full_text(
                    weibo_id, f"{base_url}{full_text.attrs['href']}", headers
                )
                time.sleep(1 + random.random())
            elif (result := parse_weibo(weibo_id, weibo)) is not None:
                yield result
        if (next_page := soup.find(next_page_predictor)) is not None and isinstance(
            next_page, Tag
        ):
            return next_page.attrs["href"]
        else:
            logger.info("cannot find next page href")
            return None
    else:
        logger.error(f"crawl page {url} failed")
        return None


def crawl_full_text(
    weibo_id: str, url: str, headers: dict[str, str]
) -> Generator[Weibo, None, None]:
    if (
        response := retry_get(url, headers, lambda r: r.status_code == 200)
    ) is not None:
        soup = BeautifulSoup(
            response.text.removeprefix('<?xml version="1.0" encoding="UTF-8"?>'),
            "html5lib",
        )
        if (
            (weibo := soup.find(weibo_predictor)) is not None
            and isinstance(weibo, Tag)
            and (result := parse_weibo(weibo_id, weibo)) is not None
        ):
            yield result
    else:
        logger.error(f"crawl weibo {weibo_id} full text failed")
    return None


def parse_weibo(weibo_id: str, weibo: Tag) -> Weibo | None:
    if (content := weibo.find(content_predictor)) is not None and (
        create_time := weibo.find(create_time_predictor)
    ) is not None:
        return Weibo(
            weibo_id,
            content.get_text(separator="\n", strip=True).removeprefix(":"),
            parse_time(create_time.text.strip()),
        )
    else:
        logger.error(f"parse weibo {weibo_id} failed: {weibo}")
        return None


def parse_time(s: str) -> datetime:
    now = datetime.now()
    if (match := re.match(time_pattern, s)) is not None:
        return datetime(
            int(y) if (y := match.group("yyyy")) is not None else now.year,
            (
                int(m)
                if (m := match.group("MM")) is not None
                or (m := match.group("month")) is not None
                else now.month
            ),
            (
                int(d)
                if (d := match.group("dd")) is not None
                or (d := match.group("day")) is not None
                else now.day
            ),
            int(match.group("HH")),
            int(match.group("mm")),
            int(s) if (s := match.group("ss")) is not None else 0,
        )

    logger.error(f"cannot parse create time: {s}, return datetime.now() instead.")
    return now
