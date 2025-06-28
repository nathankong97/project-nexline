from datetime import time
from typing import List, TypedDict

from src.transformer import transform, CleanRecord


class DummyRawRecord(TypedDict):
    station: str
    sched_tm: str
    est_tm: str
    act_tm: str


def test_transform_valid_records() -> None:
    """
    transform should parse valid time strings into time objects and include all records.
    """
    raw: List[DummyRawRecord] = [
        {"station": "A", "sched_tm": "08:00 am", "est_tm": "08:05 am", "act_tm": "08:07 am"},  # type: ignore
        {"station": "B", "sched_tm": "15:30", "est_tm": "15:35", "act_tm": "na"},  # type: ignore
    ]

    results: List[CleanRecord] = transform(raw)  # type: ignore

    assert len(results) == 2
    rec1 = results[0]
    assert isinstance(rec1["sched_time"], time)
    assert rec1["sched_time"] == time(hour=8, minute=0)
    assert rec1["est_time"] == time(hour=8, minute=5)
    assert rec1["act_time"] == time(hour=8, minute=7)

    rec2 = results[1]
    assert rec2["act_time"] is None


def test_transform_invalid_times_skipped() -> None:
    """
    transform should skip records with invalid scheduled or estimated times.
    """
    raw: List[DummyRawRecord] = [
        {"station": "C", "sched_tm": "invalid", "est_tm": "09:00", "act_tm": "09:05"},  # type: ignore
        {"station": "D", "sched_tm": "10:00", "est_tm": "notatime", "act_tm": "na"},  # type: ignore
    ]

    results: List[CleanRecord] = transform(raw)  # type: ignore
    assert results == []


def test_transform_duplicate_records_removed() -> None:
    """
    transform should remove duplicate records based on station and times.
    """
    raw: List[DummyRawRecord] = [
        {"station": "E", "sched_tm": "11:00", "est_tm": "11:05", "act_tm": "11:06"},  # type: ignore
        {"station": "E", "sched_tm": "11:00", "est_tm": "11:05", "act_tm": "11:06"},  # duplicate
    ]

    results: List[CleanRecord] = transform(raw)  # type: ignore
    assert len(results) == 1


def test_transform_whitespace_and_case_insensitive_na() -> None:
    """
    transform should strip whitespace and treat different cases of 'na' as None.
    """
    raw: List[DummyRawRecord] = [
        {"station": " F ", "sched_tm": " 12:00 PM ", "est_tm": "12:05 pm", "act_tm": " NA "},  # type: ignore
    ]

    results: List[CleanRecord] = transform(raw)  # type: ignore
    assert len(results) == 1
    rec = results[0]
    assert rec["station"] == "F"
    assert rec["act_time"] is None
