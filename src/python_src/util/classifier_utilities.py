from typing import Tuple

from fastapi import Request

from ..pydantic_models import (
    ClassifiedContention,
    Contention,
    VaGovClaim,
)
from .app_utilities import dc_lookup_table, dropdown_lookup_table, expanded_lookup_table
from .logging_utilities import log_contention_stats_decorator


def get_classification_code_name(contention: Contention) -> Tuple:
    """
    check contention type and match contention to appropriate table's
    classification code (if available)
    """
    classified_by = "not classified"
    classification_code = None
    classification_name = None

    if contention.contention_type == "INCREASE":
        classification = dc_lookup_table.get(contention.diagnostic_code)
        classification_code = classification["classification_code"]
        classification_name = classification["classification_name"]
        if classification_code is not None:
            classified_by = "diagnostic_code"

    if contention.contention_text and not classification_code:
        classification = dropdown_lookup_table.get(contention.contention_text)
        classification_code = classification["classification_code"]
        classification_name = classification["classification_name"]
        if classification_code is not None:
            classified_by = "contention_text"

    return classification_code, classification_name, classified_by


@log_contention_stats_decorator
def classify_contention(contention: Contention, claim: VaGovClaim, request: Request) -> ClassifiedContention:
    classification_code, classification_name, classified_by = get_classification_code_name(contention)

    response = ClassifiedContention(
        classification_code=classification_code,
        classification_name=classification_name,
        diagnostic_code=contention.diagnostic_code,
        contention_type=contention.contention_type,
    )
    return response, classified_by


def get_expanded_classification(contention: Contention) -> Tuple[int, str]:
    """
    Performs the dictionary lookup for the expanded lookup table
    """
    classification_code = None
    classification_name = None
    classified_by = "not classified"

    if contention.contention_type == "INCREASE":
        classification = dc_lookup_table.get(contention.diagnostic_code)
        classification_code = classification["classification_code"]
        classification_name = classification["classification_name"]
        if classification_code is not None:
            classified_by = "diagnostic_code"

    if contention.contention_text and not classification_code:
        classification = expanded_lookup_table.get(contention.contention_text)
        classification_code = classification["classification_code"]
        classification_name = classification["classification_name"]
        if classification_code is not None:
            classified_by = "contention_text"

    return classification_code, classification_name, classified_by


@log_contention_stats_decorator
def classify_contention_expanded_table(contention: Contention, claim: VaGovClaim, request: Request) -> ClassifiedContention:
    classification_code, classification_name, classified_by = get_expanded_classification(contention)

    response = ClassifiedContention(
        classification_code=classification_code,
        classification_name=classification_name,
        diagnostic_code=contention.diagnostic_code,
        contention_type=contention.contention_type,
    )

    return response, classified_by
