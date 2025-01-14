import json
import os
from typing import Dict, Optional

# sourced from Lighthouse Benefits Reference Data /disabilities endpoint:
# https://developer.va.gov/explore/benefits/docs/benefits_reference_data?version=current
BRD_CLASSIFICATIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "lh_brd_classification_ids.json")


def get_classification_names_by_code() -> Dict[str, str]:
    name_by_code = {}
    with open(BRD_CLASSIFICATIONS_PATH, "r") as fh:
        disability_items = json.load(fh)["items"]
        for item in disability_items:
            name_by_code[str(item["id"])] = item["name"]
    return name_by_code


CLASSIFICATION_NAMES_BY_CODE = get_classification_names_by_code()


def get_classification_name(classification_code: str) -> Optional[str]:
    return CLASSIFICATION_NAMES_BY_CODE.get(classification_code)
