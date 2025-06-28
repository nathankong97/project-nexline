from typing import Any, Dict, List, Set
import pytest
import requests
import src.extractors as extractors


class DummyResponse:
    """Simulate requests.Response for testing purposes."""

    def __init__(self, json_data: Any, status_code: int = 200) -> None:
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        """Raise HTTPError on bad status codes."""
        if self.status_code >= 400:
            raise requests.HTTPError(f"Status code: {self.status_code}")

    def json(self) -> Any:
        """Return the prepared JSON payload."""
        return self._json


def test_get_train_numbers_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    get_train_numbers() should return a deduplicated set of train numbers
    when the API returns a valid list.
    """
    sample: List[Dict[str, Any]] = [
        {"trainno": "100"},
        {"trainno": "200"},
        {"trainno": "100"},  # duplicate
    ]
    monkeypatch.setattr(
        requests, "get", lambda url: DummyResponse(sample, status_code=200)
    )

    result: Set[str] = extractors.get_train_numbers()
    assert result == {"100", "200"}


def test_get_train_numbers_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    get_train_numbers() should propagate HTTPError when the API returns a 5xx status.
    """
    monkeypatch.setattr(
        requests, "get", lambda url: DummyResponse(None, status_code=500)
    )

    with pytest.raises(requests.HTTPError):
        extractors.get_train_numbers()


def test_get_train_numbers_invalid_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    get_train_numbers() should raise ValueError when the JSON is not a list.
    """
    # Return a dict instead of a list
    monkeypatch.setattr(
        requests, "get", lambda url: DummyResponse({"foo": "bar"}, status_code=200)
    )

    with pytest.raises(ValueError):
        extractors.get_train_numbers()
