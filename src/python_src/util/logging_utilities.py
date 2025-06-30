import json
import logging
import sys
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Tuple, TypeVar, cast

from fastapi import Request

from ..pydantic_models import (
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from .app_utilities import dropdown_lookup_table, dropdown_values, expanded_lookup_table
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
    if "date" not in log.keys():
        log.update({"date": datetime.now(tz=timezone.utc).isoformat()})
    if "level" not in log.keys():
        log.update({"level": "info"})
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
        logging_dict.update({"processed_contention_text": None, "ml_sample": processed_text})

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
    compatibility with the existing datadog widgets.
    """
    classification_code = classified_contention.classification_code or None
    classification_name = classified_contention.classification_name or None

    contention_text = contention.contention_text or ""
    is_in_dropdown = contention_text.strip().lower() in dropdown_values
    is_mapped_text = dropdown_lookup_table.get(contention_text, None)["classification_code"] is not None
    log_contention_text = contention_text if is_mapped_text else "unmapped contention text"
    if contention.contention_type == "INCREASE":
        log_contention_type = "claim_for_increase"
    else:
        log_contention_type = contention.contention_type.lower()

    is_multi_contention = len(claim.contentions) > 1

    logging_dict = {
        "vagov_claim_id": sanitize_log(claim.claim_id),
        "claim_type": sanitize_log(log_contention_type),
        "classification_code": classification_code,
        "classification_name": classification_name,
        "contention_text": log_contention_text,
        "diagnostic_code": sanitize_log(contention.diagnostic_code),
        "is_in_dropdown": is_in_dropdown,
        "is_lookup_table_match": classification_code is not None,
        "is_multi_contention": is_multi_contention,
        "endpoint": request.url.path,
        "classification_method": classified_by,
    }

    if request.url.path == "/expanded-contention-classification":
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
R = TypeVar("R")


def log_claim_stats_decorator(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)

        if kwargs.get("claim"):
            claim = kwargs["claim"]
            request = kwargs["request"]
            log_claim_stats_v2(claim, result, request)

        return result

    return cast(F, wrapper)


def log_contention_stats_decorator(
    func: Callable[..., Tuple[ClassifiedContention, str]],
) -> Callable[..., ClassifiedContention]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ClassifiedContention:
        result, classified_by = func(*args, **kwargs)
        if isinstance(args[0], Contention) and isinstance(args[1], VaGovClaim):
            contention = args[0]
            claim = args[1]
            request = args[2]
            log_contention_stats(contention, result, claim, request, classified_by)

        return result

    return wrapper
