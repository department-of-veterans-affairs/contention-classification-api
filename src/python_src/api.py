import os
import time

from fastapi import FastAPI, HTTPException, Request

from .pydantic_models import (
    ClaimLinkInfo,
    ClassifierResponse,
    VaGovClaim,
)
from .util.app_utilities import load_config
from .util.classifier_utilities import classify_contention, classify_contention_expanded_table
from .util.expanded_lookup_table import ExpandedLookupTable
from .util.logging_dropdown_selections import build_logging_table
from .util.logging_utilities import log_as_json, log_claim_stats_decorator
from .util.lookup_table import ContentionTextLookupTable, DiagnosticCodeLookupTable
from .util.sanitizer import sanitize_log

app_config = load_config(os.path.join(os.path.dirname(__file__), "util", "app_config.yaml"))

expanded_lookup_table = ExpandedLookupTable(
    key_text=app_config["expanded_classifier"]["contention_text"],
    classification_code=app_config["expanded_classifier"]["classification_code"],
    classification_name=app_config["expanded_classifier"]["classification_name"],
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


@app.middleware("http")
async def save_process_time_as_metric(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    log_as_json({"process_time": process_time, "url": request.url.path})

    return response


@app.get("/health")
def get_health_status():
    if not len(dc_lookup_table):
        raise HTTPException(status_code=500, detail="Lookup table is empty")

    return {"status": "ok"}


@app.post("/claim-linker")
def link_vbms_claim_id(claim_link_info: ClaimLinkInfo):
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
