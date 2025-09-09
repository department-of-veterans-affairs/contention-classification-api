import time
from typing import Awaitable, Callable, Dict

import boto3
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from .pydantic_models import (
    AiRequest,
    AiResponse,
    ClassifierResponse,
    VaGovClaim,
)
from .util.app_utilities import dc_lookup_table, dropdown_lookup_table, expanded_lookup_table, ml_classifier
from .util.classifier_utilities import classify_claim, ml_classify_claim, supplement_with_ml_classification
from .util.logging_utilities import log_as_json, log_claim_stats_decorator

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
        errors = []
        if len(empty_tables) == 1:
            errors.append(f"{empty_tables[0]} table is empty")
        else:
            errors.append(f"{', '.join(empty_tables)} tables are empty")
        raise HTTPException(status_code=500, detail=", ".join(errors))
    return {"status": "ok"}


@app.post("/expanded-contention-classification")
@log_claim_stats_decorator
def expanded_classifications(claim: VaGovClaim, request: Request) -> ClassifierResponse:
    response = classify_claim(claim, request)
    return response


@app.post("/ml-contention-classification")
def ml_classifications_endpoint(contentions: AiRequest) -> AiResponse:
    response = ml_classify_claim(contentions)
    return response


@app.post("/hybrid-contention-classification")
@log_claim_stats_decorator
def hybrid_classification(claim: VaGovClaim, request: Request) -> ClassifierResponse:
    # classifies using expanded classification
    response: ClassifierResponse = classify_claim(claim, request)

    if response.is_fully_classified:
        return response

    response = supplement_with_ml_classification(response, claim)

    num_classified = len([c for c in response.contentions if c.classification_code])
    response.num_classified_contentions = num_classified
    response.is_fully_classified = num_classified == len(response.contentions)

    return response


@app.get("/health-ml-classifier")
def get_aws_status() -> Dict[str, str]:
    
    errors = []
    if ml_classifier is None:
        errors.append("ML Classifier is not initialized")
    try:
        sts_client = boto3.client("sts")
        sts_client.get_caller_identity()["Arn"]
    except Exception:
        errors.append("Undefined AWS STS caller identity")

    if errors:
        raise HTTPException(status_code=500, detail=", ".join(errors))

    return {"status": "ok"}
