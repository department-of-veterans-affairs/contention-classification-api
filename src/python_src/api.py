import json
import logging
import sys
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Protocol, Tuple, TypeVar, cast

from fastapi import FastAPI, HTTPException, Request, Response

from .pydantic_models import (
    ClaimLinkInfo,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from .util.expanded_lookup_config import FILE_READ_HELPER
from .util.expanded_lookup_table import ExpandedLookupTable
from .util.logging_dropdown_selections import build_logging_table
from .util.lookup_table import LUT_DEFAULT_VALUE, ContentionTextLookupTable, DiagnosticCodeLookupTable
from .util.sanitizer import sanitize_log

expanded_lookup_table = ExpandedLookupTable(
    key_text=FILE_READ_HELPER["contention_text"],
    classification_code=FILE_READ_HELPER["classification_code"],
    classification_name=FILE_READ_HELPER["classification_name"],
)

dc_lookup_table = DiagnosticCodeLookupTable()
dropdown_lookup_table = ContentionTextLookupTable()
dropdown_values = build_logging_table()

app = FastAPI(
    title="Contention Classification",
    description=(
        "Mapping VA.gov disability form contentions to actual classifications defined in the "
        "[Benefits Reference Data API](https://developer.va.gov/explore/benefits/docs/benefits_reference_data) "
        "for use in downstream VA systems."
    ),
    contact={"name": "Premal Shah", "email": "premal.shah@va.gov"},
    version="v0.2",
    license={
        "name": "CCO 1.0",
        "url": "https://github.com/department-of-veterans-affairs/abd-vro/blob/master/LICENSE.md",
    },
    servers=[
        {
            "url": "/contention-classification",
            "description": "Contention Classification Default",
        },
    ],
)

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


class NextCallable(Protocol):
    async def __call__(self, request: Request) -> Response: ...


@app.middleware("http")
async def save_process_time_as_metric(request: Request, call_next: NextCallable) -> Response:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    log_as_json({"process_time": process_time, "url": request.url.path})

    return response


@app.get("/health")
def get_health_status() -> Dict[str, str]:
    if not len(dc_lookup_table):
        raise HTTPException(status_code=500, detail="Lookup table is empty")

    return {"status": "ok"}


def log_as_json(log: Dict[str, Any]) -> None:
    if "date" not in log.keys():
        log.update({"date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())})
    if "level" not in log.keys():
        log.update({"level": "info"})
    logging.info(json.dumps(log))


def log_expanded_contention_text(
    logging_dict: Dict[str, Any], contention_text: str, log_contention_text: str
) -> Dict[str, Any]:
    """
    Updates the logging dictionary with the contention text updates from the expanded classification method
    """
    processed_text = expanded_lookup_table.prep_incoming_text(contention_text)
    # only log these items if the expanded lookup returns a classification code
    if expanded_lookup_table.get(contention_text)["classification_code"]:
        if log_contention_text == "unmapped contention text":
            log_contention_text = f"unmapped contention text ['{processed_text}']"
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
    classification_code = classified_contention.classification_code or None
    classification_name = classified_contention.classification_name or None

    contention_text = contention.contention_text or ""
    is_in_dropdown = contention_text.strip().lower() in dropdown_values
    is_mapped_text = dropdown_lookup_table.get(contention_text) is not None
    log_contention_text = "unmapped contention text" if not is_mapped_text else contention_text
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
        "diagnostic_code": str(contention.diagnostic_code) if contention.diagnostic_code is not None else "None",
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
    percent_classified = 0.0
    if response.num_processed_contentions > 0:
        percent_classified = float(response.num_classified_contentions) / float(response.num_processed_contentions) * 100.0

    log_as_json(
        {
            "claim_id": sanitize_log(claim.claim_id),
            "form526_submission_id": sanitize_log(claim.form526_submission_id),
            "is_fully_classified": response.is_fully_classified,
            "percent_clasified": percent_classified,
            "num_processed_contentions": response.num_processed_contentions,
            "num_classified_contentions": response.num_classified_contentions,
            "endpoint": request.url.path,
        }
    )


T = TypeVar("T", bound=ClassifierResponse)


def log_claim_stats_decorator(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        result = func(*args, **kwargs)

        if kwargs.get("claim"):
            claim = kwargs["claim"]
            request = kwargs["request"]
            log_claim_stats_v2(claim, result, request)

        return result

    return wrapper


def log_contention_stats_decorator(func: Callable[..., ClassifiedContention]) -> Callable[..., ClassifiedContention]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ClassifiedContention:
        result = func(*args, **kwargs)
        if isinstance(args[0], Contention) and isinstance(args[1], VaGovClaim):
            contention = args[0]
            claim = args[1]
            request = args[2]
            log_contention_stats(contention, result, claim, request, "contention_text")

        return result

    return wrapper


@app.post("/claim-linker")
def link_vbms_claim_id(claim_link_info: ClaimLinkInfo) -> Dict[str, bool]:
    log_as_json(
        {
            "message": "linking claims",
            "va_gov_claim_id": sanitize_log(claim_link_info.va_gov_claim_id),
            "vbms_claim_id": sanitize_log(claim_link_info.vbms_claim_id),
        }
    )
    return {
        "success": True,
    }


def get_classification_code_name(contention: Contention) -> Tuple[Optional[int], Optional[str], str]:
    """
    check contention type and match contention to appropriate table's
    classification code (if available)
    """
    classified_by = "not classified"
    classification_code: Optional[int] = None
    classification_name: Optional[str] = None

    if contention.contention_type == "INCREASE" and contention.diagnostic_code is not None:
        classification = dc_lookup_table.get(contention.diagnostic_code)
        classification_code = cast(Optional[int], classification["classification_code"])
        classification_name = cast(Optional[str], classification["classification_name"])
        if classification_code is not None:
            classified_by = "diagnostic_code"

    if contention.contention_text and not classification_code:
        classification = dropdown_lookup_table.get(contention.contention_text, LUT_DEFAULT_VALUE)
        classification_code = cast(Optional[int], classification["classification_code"])
        classification_name = cast(Optional[str], classification["classification_name"])
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
    return response


@app.post("/va-gov-claim-classifier")
@log_claim_stats_decorator
def va_gov_claim_classifier(claim: VaGovClaim, request: Request) -> ClassifierResponse:
    classified_contentions = []
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


def get_expanded_classification(contention: Contention) -> Tuple[Optional[int], Optional[str], str]:
    """
    Performs the dictionary lookup for the expanded lookup table
    """
    classification_code: Optional[int] = None
    classification_name: Optional[str] = None
    classified_by = "not classified"

    if contention.contention_type == "INCREASE" and contention.diagnostic_code is not None:
        classification = dc_lookup_table.get(contention.diagnostic_code)
        classification_code = cast(Optional[int], classification["classification_code"])
        classification_name = cast(Optional[str], classification["classification_name"])
        if classification_code is not None:
            classified_by = "diagnostic_code"

    if contention.contention_text and not classification_code:
        classification = expanded_lookup_table.get(contention.contention_text)
        classification_code = cast(Optional[int], classification["classification_code"])
        classification_name = cast(Optional[str], classification["classification_name"])
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
    return response


@app.post("/expanded-contention-classification")
@log_claim_stats_decorator
def expanded_classifications(claim: VaGovClaim, request: Request) -> ClassifierResponse:
    classified_contentions = []
    for contention in claim.contentions:
        classification = classify_contention_expanded_table(contention, claim, request)
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
