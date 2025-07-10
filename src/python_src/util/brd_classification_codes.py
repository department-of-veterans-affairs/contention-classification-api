import json
import os
from typing import Dict, Optional

from .app_utilities import dc_lookup_table

import datetime

# sourced from Lighthouse Benefits Reference Data /disabilities endpoint:
# https://developer.va.gov/explore/benefits/docs/benefits_reference_data?version=current
BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")


def get_classification_names_by_code() -> Dict[int, str]:
    name_by_code = {}
    with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
        disability_items = json.load(fh)["items"]
        for item in disability_items:
            name_by_code[item["id"]] = item["name"]
    return name_by_code


CLASSIFICATION_NAMES_BY_CODE = get_classification_names_by_code()
CLASSIFICATION_CODES_BY_NAME = {v: k for k, v in CLASSIFICATION_NAMES_BY_CODE.items()}


def get_classification_name(classification_code: int) -> Optional[str]:
    return CLASSIFICATION_NAMES_BY_CODE.get(classification_code)


def get_classification_code(classification_name: str) -> Optional[int]:
    return CLASSIFICATION_CODES_BY_NAME.get(classification_name)


def get_classification_by_code() -> Dict[int, str]:
    return_dict = {}
    with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
        disability_items = json.load(fh)["items"]
        for item in disability_items:
            return_dict[item["id"]] = item
    return return_dict


CLASSIFICATION_CODES_BY_ID = get_classification_by_code()


def get_classification(classification_code: int = None, classification_name: str = None) -> Optional[dict]:
    print("\n *** \n")
    print(f"\nclassification_code: {classification_code}")
    # print(f"classification_name: {classification_name}")
    # print(CLASSIFICATION_CODES_BY_ID)
    # print(get_classification_by_code())
    # print(classification.get('endDateTime'))
    if classification_code:
        # classification = dc_lookup_table.get(str(classification_code))
        # classification.update(CLASSIFICATION_CODES_BY_ID.get(classification_code))
        # classification = CLASSIFICATION_CODES_BY_ID.get(classification_code)
        classification = get_classification_by_code().get(str(classification_code))
    elif classification_name: 
        # classification = dc_lookup_table.get(classification_name)
        # classification.update(CLASSIFICATION_CODES_BY_ID.get(classification_name))
        classification = get_classification_by_code().get(str(classification_name))
    print(f"classification: {classification}")
    if  "endDateTime" in classification.keys() and \
            classification.get("endDateTime") is not None and \
            datetime.datetime.strptime(classification.get("endDateTime"), "%Y-%m-%dT%H:%M:%SZ") < datetime.datetime.now():
        classification['id'] = None
        classification['name'] = None 
    return classification