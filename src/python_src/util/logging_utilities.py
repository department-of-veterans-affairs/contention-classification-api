import json
import logging
import sys
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Tuple, TypeVar, cast

from fastapi import Request

from ..pydantic_models import (
    AiResponse,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from .app_utilities import dropdown_lookup_table, dropdown_values, expanded_lookup_table, ml_classifier
from .sanitizer import sanitize_log

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    stream=sys.stdout,
)


def log_as_json(log: Dict[str, Any]) -> None:
    """
    Logs the dictionary as a JSON to enable easier parsing in DataDog
    """
    log.setdefault("date", datetime.now(tz=timezone.utc).isoformat())
    log.setdefault("level", "info")
    logging.info(json.dumps(log))


def log_expanded_contention_text(
    logging_dict: Dict[str, Any], contention_text: str, log_contention_text: str
) -> Dict[str, Any]:
    """
    Updates the  logging dictionary with the contention text updates from the expanded classification method
    """
    processed_text = expanded_lookup_table.prep_incoming_text(contention_text)
    # only log these items if the expanded lookup returns a classification code
    if expanded_lookup_table.get(contention_text)["classification_code"]:
        if log_contention_text == "unmapped contention text":
            log_contention_text = f"unmapped contention text {[processed_text]}"
        logging_dict.update(
            {
                "processed_contention_text": processed_text,
                "contention_text": log_contention_text,
            }
        )
    # log none as the processed text if it is not in the LUT and leave unmapped contention text as is
    else:
        logging_dict.update({"processed_contention_text": None})

    return logging_dict


def log_contention_stats(
    contention: Contention,
    classified_contention: ClassifiedContention,
    claim: VaGovClaim,
    request: Request,
    classified_by: str,
) -> None:
    """
    Logs stats about each contention process by the classifier. This will maintain
    compatability with the existing datadog widgets.
    """
    contention_text = contention.contention_text or ""
    is_in_dropdown = contention_text.strip().lower() in dropdown_values
    is_mapped_text = dropdown_lookup_table.get(contention_text, {}).get("classification_code") is not None
    log_contention_text = contention_text if is_mapped_text else "unmapped contention text"
    log_contention_type = (
        "claim_for_increase" if contention.contention_type == "INCREASE" else contention.contention_type.lower()
    )

    is_multi_contention = len(claim.contentions) > 1

    logging_dict = {
        "vagov_claim_id": sanitize_log(claim.claim_id),
        "claim_type": sanitize_log(log_contention_type),
        "classification_code": classified_contention.classification_code,
        "classification_name": classified_contention.classification_name,
        "contention_text": log_contention_text,
        "diagnostic_code": sanitize_log(contention.diagnostic_code),
        "is_in_dropdown": is_in_dropdown,
        "is_lookup_table_match": classified_contention.classification_code is not None,
        "is_multi_contention": is_multi_contention,
        "endpoint": request.url.path,
        "classification_method": classified_by,
    }

    if request.url.path in ["/expanded-contention-classification", "/hybrid-contention-classification"]:
        logging_dict = log_expanded_contention_text(logging_dict, contention.contention_text, log_contention_text)

    log_as_json(logging_dict)


def log_claim_stats_v2(claim: VaGovClaim, response: ClassifierResponse, request: Request) -> None:
    """
    Logs stats about each claim processed by the classifier.  This will provide
    the capability to build widgets to track metrics about claims.
    """
    log_as_json(
        {
            "claim_id": sanitize_log(claim.claim_id),
            "form526_submission_id": sanitize_log(claim.form526_submission_id),
            "is_fully_classified": response.is_fully_classified,
            "percent_clasified": (response.num_classified_contentions / response.num_processed_contentions) * 100,
            "num_processed_contentions": response.num_processed_contentions,
            "num_classified_contentions": response.num_classified_contentions,
            "endpoint": request.url.path,
        }
    )


F = TypeVar("F", bound=Callable[..., Any])


def log_claim_stats_decorator(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)

        if (claim := kwargs.get("claim")) and (request := kwargs.get("request")):
            log_claim_stats_v2(claim, result, request)

        return result

    return cast(F, wrapper)


def log_contention_stats_decorator(
    func: Callable[..., Tuple[ClassifiedContention, str]],
) -> Callable[..., ClassifiedContention]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ClassifiedContention:
        result, classified_by = func(*args, **kwargs)
        if len(args) >= 3 and isinstance(args[0], Contention) and isinstance(args[1], VaGovClaim):
            log_contention_stats(args[0], result, args[1], args[2], classified_by)

        return result

    return wrapper


def log_ml_contention_stats(response: ClassifierResponse, ai_response: AiResponse, request: Request) -> None:
    """
    Logs stats about each contention processed by the ML classifier.
    """
    # Get ML classifier version if available
    if ml_classifier is not None:
        version_tuple = ml_classifier.get_version()
        # Convert tuple to a formatted string for logging
        if isinstance(version_tuple, tuple) and len(version_tuple) == 2:
            ml_version = f"model:{version_tuple[0]},vectorizer:{version_tuple[1]}"
        else:
            ml_version = str(version_tuple)
    else:
        ml_version = "unknown"

    for classified_contention in ai_response.classified_contentions:
        log_contention_type = (
            "claim_for_increase"
            if classified_contention.contention_type == "INCREASE"
            else classified_contention.contention_type.lower()
        )
        is_multi_contention = len(response.contentions) > 1
        logging_dict = {
            "vagov_claim_id": sanitize_log(response.claim_id),
            "claim_type": sanitize_log(log_contention_type),
            "classification_code": classified_contention.classification_code,
            "classification_name": classified_contention.classification_name,
            "contention_text": "unmapped contention text",
            "diagnostic_code": classified_contention.diagnostic_code,
            "is_in_dropdown": False,
            "is_lookup_table_match": False,
            "is_multi_contention": is_multi_contention,
            "endpoint": request.url.path,
            "classification_method": "ml_classifier",
            "ml_classifier_version": ml_version,
        }

        log_as_json(logging_dict)


def log_ml_contention_stats_decorator(func: Callable[..., ClassifierResponse]) -> Callable[..., ClassifierResponse]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ClassifierResponse:
        result = func(*args, **kwargs)
        if (
            (classifier_response := kwargs.get("response"))
            and (ai_response := kwargs.get("ai_classified"))
            and (request := kwargs.get("request"))
        ):
            log_ml_contention_stats(classifier_response, ai_response, request)
        return result

    return wrapper
