import time
from typing import Awaitable, Callable, Dict

import boto3
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from .pydantic_models import (
    AiRequest,
    AiResponse,
    ClassifierResponse,
    MLClassifierConfigRequest,
    MLClassifierConfigResponse,
    VaGovClaim,
)
from .util.app_utilities import (
    dc_lookup_table,
    dropdown_lookup_table,
    expanded_lookup_table,
    ml_classifier,
    reinitialize_ml_classifier,
)
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
    if empty_tables or ml_classifier is None:
        errors = []
        if len(empty_tables) == 1:
            errors.append(f"{empty_tables[0]} table is empty")
        elif empty_tables:
            errors.append(f"{', '.join(empty_tables)} tables are empty")
        if ml_classifier is None:
            errors.append("ML Classifier is not initialized")
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


@app.get("/health-aws")
def get_aws_status() -> Dict[str, str]:
    sts_client = boto3.client("sts")
    s3_resource = boto3.resource("s3")

    try:
        caller_identity = sts_client.get_caller_identity().get("Arn")
    except Exception as e:
        log_as_json({"error": "Error retrieving AWS identity", "exception": str(e)})
        caller_identity = "Error retrieving identity"

    try:
        head_bucket = s3_resource.meta.client.head_bucket(Bucket="dsva-vagov-staging-contention-classification-api")
        bucket_info = head_bucket.get("BucketArn")
    except Exception as e:
        log_as_json({"error": "Error accessing S3 bucket", "exception": str(e)})
        bucket_info = "Error accessing bucket"

    return {"identity": caller_identity, "bucket": bucket_info}


@app.post("/ml-classifier-config")
def update_ml_classifier_config(config_request: MLClassifierConfigRequest) -> MLClassifierConfigResponse:
    """
    Update ML classifier configuration and reinitialize with new models.

    This endpoint allows updating the ML classifier with new model files from S3.
    It can update filenames, S3 keys, SHA checksums, and force re-download of files.
    After updating configuration, it reinitializes the classifier with the latest data.

    Args:
        config_request: Configuration update request containing optional fields:
            - model_filename: New model filename
            - vectorizer_filename: New vectorizer filename
            - s3_model_key: New S3 key for model file
            - s3_vectorizer_key: New S3 key for vectorizer file
            - force_download: Force re-download even if files exist
            - expected_model_sha256: Expected SHA256 for model verification
            - expected_vectorizer_sha256: Expected SHA256 for vectorizer verification

    Returns:
        MLClassifierConfigResponse: Response containing:
            - success: Whether the update was successful
            - message: Description of the result
            - previous_version: Previous model/vectorizer versions (if available)
            - new_version: New model/vectorizer versions (if successful)
            - files_updated: List of files that were updated

    Raises:
        HTTPException: If the update fails or required parameters are missing
    """
    try:
        # Validate that at least one parameter is provided
        if not any(
            [
                config_request.model_filename,
                config_request.vectorizer_filename,
                config_request.s3_model_key,
                config_request.s3_vectorizer_key,
                config_request.force_download,
                config_request.expected_model_sha256,
                config_request.expected_vectorizer_sha256,
            ]
        ):
            raise HTTPException(status_code=400, detail="At least one configuration parameter must be provided")

        # Track which files will be updated
        files_updated = []
        if config_request.model_filename or config_request.s3_model_key:
            files_updated.append("model")
        if config_request.vectorizer_filename or config_request.s3_vectorizer_key:
            files_updated.append("vectorizer")
        if config_request.force_download:
            files_updated.extend(["model", "vectorizer"])
            files_updated = list(set(files_updated))  # Remove duplicates

        # Call the reinitialize function
        success, message, previous_version, new_version = reinitialize_ml_classifier(
            new_model_filename=config_request.model_filename,
            new_vectorizer_filename=config_request.vectorizer_filename,
            new_s3_model_key=config_request.s3_model_key,
            new_s3_vectorizer_key=config_request.s3_vectorizer_key,
            force_download=config_request.force_download,
            new_model_sha256=config_request.expected_model_sha256,
            new_vectorizer_sha256=config_request.expected_vectorizer_sha256,
        )

        if not success:
            raise HTTPException(status_code=500, detail=message)

        log_as_json(
            {
                "action": "ml_classifier_config_update",
                "success": success,
                "files_updated": files_updated,
                "previous_version": previous_version,
                "new_version": new_version,
            }
        )

        return MLClassifierConfigResponse(
            success=success,
            message=message,
            previous_version=previous_version,
            new_version=new_version,
            files_updated=files_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Unexpected error updating ML classifier configuration: {str(e)}"
        log_as_json({"error": error_message, "exception": str(e)})
        raise HTTPException(status_code=500, detail=error_message) from e
