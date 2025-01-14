import csv
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

# from .logging_utilities import log_as_json


@dataclass
class InitValues:
    csv_filepath: str
    input_key: str
    classification_code: str
    classification_name: str
    lut_default_value: Dict[str, Any]


def read_csv_to_list(filepath: str) -> List[Dict[str, str]]:
    """
    Reads a CSV file and returns a list of dictionaries (one dict per row).

    Parameters
    ----------
    filepath : str
        The fully qualified path to the CSV file

    Returns
    -------
    list[dict[str, str]]
        List of rows as dictionaries, keyed by column headers

    Raises
    ------
    FileNotFoundError
        If the CSV file cannot be found
    csv.Error
        If there's a parsing issue
    """
    rows = []
    try:
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except csv.Error as e:
        logging.error(f"Error reading CSV file {filepath}: {e}")
        raise
    return rows
