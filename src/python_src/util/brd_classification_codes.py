import datetime
import json
import logging
import os
from typing import Dict, Optional

# sourced from Lighthouse Benefits Reference Data /disabilities endpoint:
# https://developer.va.gov/explore/benefits/docs/benefits_reference_data?version=current
BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")


def get_classification_names_by_code() -> Dict[int, str]:
    with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
        brd_classification_list = json.load(fh)["items"]
    brd_classification_dict = {}
    for item in brd_classification_list:
        if item.get("endDateTime"):
            try:
                item_datetime = datetime.datetime.strptime(item.get("endDateTime"), "%Y-%m-%dT%H:%M:%SZ")
                if item_datetime is None or item_datetime < datetime.datetime.now():
                    continue
            except Exception as e:
                logging.error(f"endDateTime format error: {e}")
                continue
        brd_classification_dict[item["id"]] = item["name"]
    return brd_classification_dict


CLASSIFICATION_NAMES_BY_CODE = get_classification_names_by_code()
CLASSIFICATION_CODES_BY_NAME = {v: k for k, v in CLASSIFICATION_NAMES_BY_CODE.items()}


def get_classification_name(classification_code: int) -> Optional[str]:
    return CLASSIFICATION_NAMES_BY_CODE.get(classification_code)


def get_classification_code(classification_name: str) -> Optional[int]:
    return CLASSIFICATION_CODES_BY_NAME.get(classification_name)
