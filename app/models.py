from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RiskScoreResponse(BaseModel):
    application_id: int = Field(alias="applicationId")
    customer_id: int = Field(alias="customerId")
    requested_amount: float = Field(alias="requestedAmount")
    max_approved_amount: float = Field(alias="maxApprovedAmount")
    calculated_score: float = Field(alias="calculatedScore")
    risk_rating: str = Field(alias="riskRating")
    evaluated_at_utc: datetime = Field(alias="evaluatedAtUtc")

    model_config = {"populate_by_name": True}


class RiskFactorItem(BaseModel):
    factor_code: str = Field(alias="factorCode")
    factor_name: str = Field(alias="factorName")
    weight: float
    value: float = 0.0
    impact_score: float = Field(default=0.0, alias="impactScore")

    model_config = {"populate_by_name": True}


class RiskFactorsResponse(BaseModel):
    customer_id: int = Field(alias="customerId")
    overall_score: float = Field(alias="overallScore")
    factors: list[RiskFactorItem]

    model_config = {"populate_by_name": True}


class RiskModelParameter(BaseModel):
    name: str
    value: float


class RiskModelUpdateRequest(BaseModel):
    updated_by: Optional[str] = Field(default=None, alias="updatedBy")
    parameters: list[RiskModelParameter]

    model_config = {"populate_by_name": True}


class RiskModelUpdateResponse(BaseModel):
    success: bool
    updated_count: int = Field(alias="updatedCount")
    message: str
    updated_at_utc: datetime = Field(alias="updatedAtUtc")

    model_config = {"populate_by_name": True}
