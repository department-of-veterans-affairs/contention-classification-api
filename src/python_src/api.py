import time
from typing import Awaitable, Callable, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from .pydantic_models import (
    ClaimLinkInfo,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from .util.api_client import AiClient
from .util.app_utilities import app_config, dc_lookup_table, dropdown_lookup_table, expanded_lookup_table
from .util.classifier_utilities import classify_contention
from .util.logging_utilities import log_as_json, log_claim_stats_decorator
from .util.sanitizer import sanitize_log

app = FastAPI(
    title="Contention Classification",
    description=(
        "Mapping VA.gov disability form contentions to actual classifications defined in the "
        "[Benefits Reference Data API](https://developer.va.gov/explore/benefits/docs/benefits_reference_data) "
        "for use in downstream VA systems."
    ),
    contact={"name": "Jennifer Bertsch", "email": "jennifer.bertsch@va.gov"},
    version="v1.1",
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
async def save_process_time_as_metric(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    log_as_json({"process_time": process_time, "url": request.url.path})
    return response


@app.get("/health")
def get_health_status() -> Dict[str, str]:
    empty_tables = []
    if not len(dc_lookup_table):
        empty_tables.append("DC Lookup")
    if not len(expanded_lookup_table):
        empty_tables.append("Expanded Lookup")
    if not len(dropdown_lookup_table):
        empty_tables.append("Contention Text Lookup")
    if empty_tables:
        if len(empty_tables) == 1:
            raise HTTPException(status_code=500, detail=f"{' and '.join(empty_tables)} table is empty")
        else:
            raise HTTPException(status_code=500, detail=f"{', '.join(empty_tables)} tables are empty")
    return {"status": "ok"}


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


@app.post("/ml-contention-classification")
def fake_endpoint(contentions: list[Contention]) -> dict[str, list[ClassifiedContention]]:
    response: list[ClassifiedContention] = []
    for contention in contentions:
        temp_classy = ClassifiedContention(
            classification_code=9999,
            classification_name="ml classification",
            diagnostic_code=contention.diagnostic_code,
            contention_type=contention.contention_type,
        )
        response.append(temp_classy)
    return {"classified_contentions": response}


@app.post("/hybrid-contention-classification")
def hybrid_classification(claim: VaGovClaim, request: Request) -> ClassifierResponse:
    # classify using expanded classifier
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

    if response.is_fully_classified:
        return response
    else:
        non_classified_indices = [i for i, c in enumerate(classified_contentions) if not c.classification_code]
        non_classified_contentions = [claim.contentions[i] for i in non_classified_indices]
        contention_to_classify = [contention.dict() for contention in non_classified_contentions]
        ai_client: AiClient = AiClient(app_config["ai_classification_endpoint"]["url"])
        ml_response = ai_client.classify_contention(
            endpoint=app_config["ai_classification_endpoint"]["endpoint"], data=contention_to_classify
        )
        ml_model_vals = [i for i in range(len(ml_response["classified_contentions"]))]
        # need to find a way to map the index stuff to the ml response...
        for idx, val in list(zip(non_classified_indices, ml_model_vals, strict=False)):
            response.contentions[idx].classification_code = ml_response["classified_contentions"][val]["classification_code"]
            response.contentions[idx].classification_name = ml_response["classified_contentions"][val]["classification_name"]

        return response
