from typing import Optional, List

from fastapi import HTTPException
from pydantic import BaseModel, model_validator


class ClaimLinkInfo(BaseModel):
    """used for connecting VA.gov and VBMS claims to each other in order to track contention changes downstream"""

    va_gov_claim_id: int
    vbms_claim_id: int


class Contention(BaseModel):
    contention_text: str
    contention_type: str  # "disabilityActionType" in the VA.gov API
    diagnostic_code: Optional[int] = None  # only required for contention_type: "claim_for_increase"

    @model_validator(mode="before")
    @classmethod
    def check_dc_for_cfi(cls, values):
        contention_type = values.get("contention_type")
        diagnostic_code = values.get("diagnostic_code")

        if contention_type == "INCREASE" and not diagnostic_code:
            raise HTTPException(
                422,
                "diagnostic_code is required for contention_type claim_for_increase",
            )
        return values


class VaGovClaim(BaseModel):
    claim_id: int
    form526_submission_id: int
    contentions: List[Contention]

    @model_validator(mode='after')
    def validate_contentions_length(self):
        if len(self.contentions) < 1:
            raise ValueError("contentions must have at least 1 item")
        return self


class ClassifiedContention(BaseModel):
    classification_code: Optional[int]
    classification_name: Optional[str]
    diagnostic_code: Optional[int] = None  # only required for contention_type: "claim_for_increase"
    contention_type: str  # "disabilityActionType" in the VA.gov API


class ClassifierResponse(BaseModel):
    contentions: List[ClassifiedContention]
    claim_id: int
    form526_submission_id: int
    is_fully_classified: bool
    num_processed_contentions: int
    num_classified_contentions: int

    @model_validator(mode='after')
    def validate_contentions_length(self):
        if len(self.contentions) < 1:
            raise ValueError("contentions must have at least 1 item")
        return self
