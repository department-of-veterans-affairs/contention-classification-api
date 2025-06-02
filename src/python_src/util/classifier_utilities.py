import traceback
from typing import Any, Dict, Optional, Protocol, Tuple, Union, runtime_checkable

import httpx
from fastapi import Request

from ..pydantic_models import (
    AiRequest,
    AiResponse,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from .ai_client import AiClient
from .app_utilities import app_config, dc_lookup_table, expanded_lookup_table
from .expanded_lookup_table import ExpandedLookupTable
from .logging_utilities import log_as_json, log_contention_stats_decorator
from .lookup_table import ContentionTextLookupTable

from .ml_classifier import ml_classify_text


@runtime_checkable
class LookupTable(Protocol):
    def get(self, input_str: str, default_value: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...


def get_classification_code_name(
    contention: Contention, lookup_table: LookupTable
) -> Tuple[Optional[int], Optional[str], str]:
    """
    check contention type and match contention to appropriate table's
    classification code (if available)

    Parameters
    ----------
    contention : Contention
        A single contention from the claim
    lookup_table : dict
        The lookup table to use for classification of contention text. This is determine based on the request url
        in the classify_contention function

    Returns
    -------
    tuple:
        classification_code : int
        classification_name: str
        classified_by: str
    """
    classified_by = "not classified"
    classification_code = None
    classification_name = None

    if contention.contention_type == "INCREASE" and contention.diagnostic_code is not None:
        classification = dc_lookup_table.get(str(contention.diagnostic_code))
        if classification:
            classification_code = classification["classification_code"]
            classification_name = classification["classification_name"]
            if classification_code is not None:
                classified_by = "diagnostic_code"

    if contention.contention_text and not classification_code:
        classification = lookup_table.get(contention.contention_text)
        classification_code = classification["classification_code"]
        classification_name = classification["classification_name"]
        if classification_code is not None:
            classified_by = "contention_text"

    if not classification_code and contention.contention_text:
        ml_code = ml_classify_text(contention.contention_text)
        if ml_code is not None:
            classification = dc_lookup_table.get(str(ml_code))
            classification_code = ml_code
            classification_name = classification.get("classification_name") if classification else None
            classified_by = "ml_fallback"


@log_contention_stats_decorator
def classify_contention(contention: Contention, claim: VaGovClaim, request: Request) -> Tuple[ClassifiedContention, str]:
    lookup_table: Union[ExpandedLookupTable, ContentionTextLookupTable] = expanded_lookup_table

    classification_code, classification_name, classified_by = get_classification_code_name(contention, lookup_table)

    response = ClassifiedContention(
        classification_code=classification_code,
        classification_name=classification_name,
        diagnostic_code=contention.diagnostic_code,
        contention_type=contention.contention_type,
    )
    return response, classified_by


def classify_claim(claim: VaGovClaim, request: Request) -> ClassifierResponse:
    classified_contentions: list[ClassifiedContention] = []
    for contention in claim.contentions:
        classification = classify_contention(contention, claim, request)
        classified_contentions.append(classification)

    num_classified = len([c for c in classified_contentions if c.classification_code])

    response = ClassifierResponse(
        contentions=classified_contentions,
        claim_id=claim.claim_id,
        form526_submission_id=claim.form526_submission_id,
        is_fully_classified=num_classified == len(classified_contentions),
        num_processed_contentions=len(classified_contentions),
        num_classified_contentions=num_classified,
    )

    return response


def build_ai_request(response: ClassifierResponse, claim: VaGovClaim) -> tuple[list[int], AiRequest]:
    """
    Builds the request body for the Ai Classifier by extracting unclassified contentions
    """
    non_classified_indices = [i for i, c in enumerate(response.contentions) if not c.classification_code]

    non_classified_contentions = [claim.contentions[i] for i in non_classified_indices]
    ai_request = AiRequest(contentions=non_classified_contentions)
    return non_classified_indices, ai_request


def update_classifications(response: ClassifierResponse, indices: list[int], ai_classified: AiResponse) -> ClassifierResponse:
    """
    Updates the originally classified claim with classifications from the ml classifier
    """
    for idx, c in zip(indices, ai_classified.classified_contentions, strict=True):
        response.contentions[idx].classification_code = c.classification_code
        response.contentions[idx].classification_name = c.classification_name
    return response


def ml_classification(response: ClassifierResponse, claim: VaGovClaim) -> ClassifierResponse:
    """
    Establishes and calls the AI client to classify unclassified contentions
    """
    non_classified_indices, ai_request = build_ai_request(response, claim)
    client = AiClient(base_url=app_config["ai_classification_endpoint"]["url"])
    try:
        ai_response = client.classify_contention(
            endpoint=app_config["ai_classification_endpoint"]["endpoint"], data=ai_request
        )

        response = update_classifications(response, non_classified_indices, ai_response)

        return response
    except httpx.HTTPStatusError as e:
        log_as_json({"message": "Failure to reach AI Endpoint", "error": str(e)})
    except httpx.RequestError as e:
        log_as_json({"message": "Failure to reach AI Endpoint", "error": str(e)})
    except Exception as e:
        log_as_json({"message": "Unexpected error in ML classification", "error": str(e), "traceback": traceback.format_exc()})
    return response
