"""Fetcher for project-nexline: RRSchedules endpoint.

This module provides functionality to retrieve the schedule for a given train number
from SEPTA's RRSchedules API, handling rate-limiting and retry logic.
"""
import time
from typing import List, TypedDict

import requests
from requests.exceptions import HTTPError

import config


class ScheduleRecord(TypedDict):
    """Type definition for a single schedule entry."""
    station: str
    sched_tm: str
    est_tm: str
    act_tm: str


def fetch_schedule(
        train_no: str,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
) -> List[ScheduleRecord]:
    """
    Fetch the schedule for a specific train number, with retries and rate-limiting.

    Args:
        train_no (str): The train number to fetch the schedule for.
        max_retries (int, optional): Maximum number of retry attempts on HTTP errors.
            Defaults to 3.
        retry_backoff (float, optional): Base backoff time in seconds for retries.
            Defaults to 0.5.

    Returns:
        List[ScheduleRecord]: A list of schedule records, each containing:
            - station: Name of the station.
            - sched_tm: Scheduled time (e.g. "15:08").
            - est_tm: Estimated time (e.g. "15:11").
            - act_tm: Actual time or "na".

    Raises:
        HTTPError: If the HTTP request ultimately fails after retries.
        ValueError: If the JSON response is not a list.
        RuntimeError: If no response is received.
    """
    url = config.RRSCHEDULES_URL
    params = {"req1": train_no}

    response = None  # type: ignore
    attempts = 0
    total_attempts = max_retries + 1

    while attempts < total_attempts:
        response = requests.get(url, params=params)
        try:
            response.raise_for_status()
            break
        except HTTPError:
            attempts += 1
            if attempts >= total_attempts:
                raise
            backoff_time = retry_backoff * (2 ** (attempts - 1))
            time.sleep(backoff_time)

    if response is None:
        raise RuntimeError("fetch_schedule did not receive a response.")

    data = response.json()
    if not isinstance(data, list):
        raise ValueError(
            "Unexpected JSON format: expected a list of schedule records"
        )

    records: List[ScheduleRecord] = []
    for item in data:
        records.append(
            ScheduleRecord(
                station=str(item.get("station", "")),
                sched_tm=str(item.get("sched_tm", "")),
                est_tm=str(item.get("est_tm", "")),
                act_tm=str(item.get("act_tm", "")),
            )
        )

    time.sleep(1 / config.RATE_LIMIT_RPS)

    return records
