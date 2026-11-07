import pytest
import requests

from wwg import crawl


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
