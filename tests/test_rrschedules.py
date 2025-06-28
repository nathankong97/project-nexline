import time
from typing import Any, Dict, List

import pytest
import requests

from src.fetchers.rrschedules import fetch_schedule, ScheduleRecord


class DummyResponse:
    """Simulated requests.Response for testing fetch_schedule."""

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


def test_fetch_schedule_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    fetch_schedule should return a list of ScheduleRecord on success
    and respect the order of items.
    """
    sample: List[Dict[str, Any]] = [
        {"station": "A", "sched_tm": "08:00", "est_tm": "08:05", "act_tm": "na"},
        {"station": "B", "sched_tm": "08:10", "est_tm": "08:12", "act_tm": "08:13"},
    ]
    # Patch requests.get to always return a successful DummyResponse
    monkeypatch.setattr(
        "requests.get",
        lambda url, params=None: DummyResponse(sample, status_code=200)
    )
    # Patch time.sleep to avoid delays
    monkeypatch.setattr(time, "sleep", lambda x: None)

    records: List[ScheduleRecord] = fetch_schedule("123")
    assert len(records) == 2
    assert records[0]["station"] == "A"
    assert records[1]["act_tm"] == "08:13"


def test_fetch_schedule_retry_and_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    fetch_schedule should retry on HTTP errors with exponential backoff
    and eventually succeed.
    """
    calls: List[int] = []

    def fake_get(url: str, params=None):
        # Fail the first two times, then succeed
        if len(calls) < 2:
            calls.append(1)
            return DummyResponse(None, status_code=500)
        return DummyResponse([{"station": "X", "sched_tm": "09:00", "est_tm": "09:05", "act_tm": "na"}],
                             status_code=200)

    monkeypatch.setattr("requests.get", fake_get)
    # Track sleep invocations without real delay
    sleep_calls: List[float] = []
    monkeypatch.setattr(time, "sleep", lambda secs: sleep_calls.append(secs))

    records = fetch_schedule("456", max_retries=3, retry_backoff=0.1)
    # Ensure it retried twice before succeeding
    assert len(calls) == 2
    # Exponential backoff times: 0.1, 0.2
    assert pytest.approx(sleep_calls[:2], rel=1e-3) == [0.1, 0.2]
    assert records[0]["station"] == "X"


def test_fetch_schedule_max_retries_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    fetch_schedule should raise HTTPError after exceeding max_retries.
    """
    # Always return a 503 error
    monkeypatch.setattr(
        "requests.get",
        lambda url, params=None: DummyResponse(None, status_code=503)
    )
    # Patch sleep to no-op
    monkeypatch.setattr(time, "sleep", lambda x: None)

    with pytest.raises(requests.HTTPError):
        fetch_schedule("789", max_retries=2, retry_backoff=0.01)


def test_fetch_schedule_invalid_json_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    fetch_schedule should raise ValueError when JSON is not a list.
    """
    # Return a dict instead of list
    monkeypatch.setattr(
        "requests.get",
        lambda url, params=None: DummyResponse({"foo": "bar"}, status_code=200)
    )
    monkeypatch.setattr(time, "sleep", lambda x: None)

    with pytest.raises(ValueError):
        fetch_schedule("321")
