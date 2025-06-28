"""Transformation module for project-nexline.

This module normalizes and validates raw schedule records fetched from the RRSchedules
endpoint. It converts time strings to datetime.time objects, filters out duplicates,
 and discards malformed entries.
"""
from datetime import time
from typing import List, Optional, TypedDict, Tuple, Set

from dateutil import parser

from src.fetchers.rrschedules import ScheduleRecord


class CleanRecord(TypedDict):
    """Type definition for a cleaned schedule record."""
    station: str
    sched_time: time
    est_time: time
    act_time: Optional[time]


def transform(raw_records: List[ScheduleRecord]) -> List[CleanRecord]:
    """
    Transform raw schedule records into cleaned records.

    Args:
        raw_records (List[ScheduleRecord]): List of raw JSON-like schedule records.

    Returns:
        List[CleanRecord]: A list of cleaned records with time fields parsed and
            duplicates removed.
    """
    cleaned: List[CleanRecord] = []
    seen: Set[Tuple[str, time, time, Optional[time]]] = set()

    for record in raw_records:
        station = record.get("station", "").strip()
        raw_sched = record.get("sched_tm", "").strip()
        raw_est = record.get("est_tm", "").strip()
        raw_act = record.get("act_tm", "").strip()

        try:
            sched_time = parser.parse(raw_sched).time()
            est_time = parser.parse(raw_est).time()
        except (ValueError, TypeError):
            continue

        if raw_act.lower() == "na" or not raw_act:
            act_time: Optional[time] = None
        else:
            try:
                act_time = parser.parse(raw_act).time()
            except (ValueError, TypeError):
                act_time = None

        key = (station, sched_time, est_time, act_time)
        if key in seen:
            continue

        seen.add(key)
        cleaned.append(
            CleanRecord(
                station=station,
                sched_time=sched_time,
                est_time=est_time,
                act_time=act_time,
            )
        )

    return cleaned
