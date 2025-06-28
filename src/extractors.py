"""Extraction module for project-nexline.

This module provides functionality to fetch SEPTA's TrainView API endpoint and
extract a set of train numbers operating on the current service day.
"""
from typing import Set

import requests

import config


def get_train_numbers() -> Set[str]:
    """
    Fetch the TrainView API and return a set of unique train numbers.

    Performs an HTTP GET request to the configured TRAINVIEW_URL, parses the JSON
    response to extract train numbers, and returns them without duplicates.

    Returns:
        Set[str]: A set of train numbers as strings.

    Raises:
        requests.HTTPError: If the HTTP request to the TrainView API fails.
        ValueError: If the JSON structure is unexpected.
    """
    response = requests.get(config.TRAINVIEW_URL)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Unexpected JSON format: expected a list of train records")

    train_numbers: Set[str] = set()
    for record in data:
        train_no = record.get("trainno")
        if train_no:
            train_numbers.add(str(train_no))

    return train_numbers
