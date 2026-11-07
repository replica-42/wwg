import json
import logging
from datetime import datetime

import pytest
import requests

from wwg import crawl
from wwg.config import CrawlConfig


def response(status):
    result = requests.Response()
    result.status_code = status
    result.url = "https://example.invalid"
    return result


@pytest.mark.parametrize(
    "failure",
    [requests.Timeout("timeout"), requests.ConnectionError("offline"), response(503)],
    ids=["timeout", "connection", "http-503"],
)
def test_transient_failures_are_retried_with_timeouts(mocker, caplog, failure):
    success = response(200)
    get = mocker.patch.object(crawl.requests, "get", side_effect=[failure, success])
    sleep = mocker.patch.object(crawl.time, "sleep")
    result = crawl.retry_get(
        "https://example.invalid", {"Cookie": "test"}, lambda r: r.status_code == 200
    )
    assert result is success
    assert get.call_count == 2
    assert get.call_args.kwargs["timeout"] == (5, 30)
    assert get.call_args.kwargs["headers"] == {"Cookie": "test"}
    sleep.assert_called_once_with(1)
    assert "retry after 1s" in caplog.text


def test_exhausted_retries_raise_the_original_error(mocker):
    error = requests.Timeout("timeout")
    get = mocker.patch.object(crawl.requests, "get", side_effect=error)
    sleep = mocker.patch.object(crawl.time, "sleep")
    with pytest.raises(requests.Timeout) as result:
        crawl.retry_get("https://example.invalid", {}, lambda r: True, max_retries=2)
    assert result.value is error
    assert get.call_count == 3
    assert sleep.call_args_list == [mocker.call(1), mocker.call(2)]


@pytest.mark.parametrize("full_text", [False, True], ids=["page", "full-text"])
def test_http_error_is_not_reported_as_end_of_pages(mocker, full_text):
    mocker.patch.object(crawl, "retry_get", side_effect=requests.HTTPError("503"))
    if full_text:
        records = crawl.crawl_full_text("123", "https://example.invalid", {})
    else:
        records = crawl.crawl_page("https://example.invalid", {}, False)
    with pytest.raises(requests.HTTPError):
        list(records)


def test_rejected_response_is_an_error(mocker):
    mocker.patch.object(crawl.requests, "get", return_value=response(201))
    with pytest.raises(requests.RequestException, match="HTTP 201"):
        crawl.retry_get(
            "https://example.invalid", {}, lambda r: r.status_code == 200, max_retries=0
        )


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO])
def test_crawl_progress_reports_writes_and_empty_last_page(
    tmp_path, mocker, caplog, level
):
    caplog.set_level(level, logger=crawl.__name__)
    post = crawl.Weibo("123", "private content", datetime(2026, 1, 2))

    def page(url, headers, original_only):
        if "page=2" not in url:
            yield post
            return "/user/profile?page=2"
        return None

    mocker.patch.object(crawl, "crawl_page", side_effect=page)
    sleep = mocker.patch.object(crawl.time, "sleep")
    output = tmp_path / "posts.jsonl"
    crawl.main(
        CrawlConfig(
            uid="user",
            cookies="secret-cookie",
            output=output,
            after=datetime(2026, 1, 1),
        )
    )
    assert [json.loads(line)["id"] for line in output.read_text().splitlines()] == [
        "123"
    ]
    sleep.assert_called_once()
    assert "secret-cookie" not in caplog.text
    assert "private content" not in caplog.text
    if level == logging.DEBUG:
        assert "fetch page 1:" in caplog.text
        assert "before fetching page 2" in caplog.text
        assert "page 1 complete: 1 posts written; total written: 1" in caplog.text
        assert "page 2 complete: 0 posts written; total written: 1" in caplog.text
        assert "stop: no next page" in caplog.text
        assert "crawl complete: 2 pages fetched, 1 posts written" in caplog.text
    else:
        assert not caplog.records


@pytest.mark.parametrize("stop_reason", ["date", "page-limit"])
def test_crawl_logs_stop_reason_without_fetching_another_page(
    tmp_path, mocker, caplog, stop_reason
):
    caplog.set_level(logging.DEBUG, logger=crawl.__name__)

    def page(url, headers, original_only):
        yield crawl.Weibo("new", "content", datetime(2026, 1, 2))
        if stop_reason == "date":
            yield crawl.Weibo("old", "content", datetime(2025, 12, 31))
            pytest.fail("crawl continued after the date cutoff")
        return "/user/profile?page=2"

    fetch = mocker.patch.object(crawl, "crawl_page", side_effect=page)
    sleep = mocker.patch.object(crawl.time, "sleep")
    output = tmp_path / "posts.jsonl"
    crawl.main(
        CrawlConfig(uid="user", output=output, after=datetime(2026, 1, 1), max_page=1)
    )
    fetch.assert_called_once()
    sleep.assert_not_called()
    assert len(output.read_text().splitlines()) == 1
    assert "crawl complete: 1 pages fetched, 1 posts written" in caplog.text
    if stop_reason == "date":
        assert "stop: post old" in caplog.text
        assert "is older than after=2026-01-01" in caplog.text
    else:
        assert "stop: reached max_page=1" in caplog.text


def test_page_progress_logs_repost_skip_and_full_text_fetch(mocker, caplog):
    caplog.set_level(logging.DEBUG, logger=crawl.__name__)
    page = response(200)
    page.encoding = "utf-8"
    page._content = (
        '<div class="c" id="M_repost"><span class="cmt">转发理由</span></div>'
        '<div class="c" id="M_original"><a href="/comment/original">全文</a></div>'
    ).encode()
    full = response(200)
    full.encoding = "utf-8"
    full._content = (
        '<div class="c" id="M_original"><span class="ctt">完整内容</span>'
        '<span class="ct">2026-01-02 12:00:00</span></div>'
    ).encode()
    mocker.patch.object(crawl, "retry_get", side_effect=[page, full])
    mocker.patch.object(crawl.time, "sleep")
    assert list(crawl.crawl_page("https://example.invalid", {}, True)) == [
        crawl.Weibo("original", "完整内容", datetime(2026, 1, 2, 12))
    ]
    assert "page contains 2 post entries" in caplog.text
    assert "skip repost repost" in caplog.text
    assert "fetch full text for post original" in caplog.text
