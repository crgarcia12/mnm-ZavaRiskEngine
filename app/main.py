from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.models import (
    RiskFactorsResponse,
    RiskModelUpdateRequest,
    RiskModelUpdateResponse,
    RiskScoreResponse,
)
from app.service import get_risk_factors, score_loan_application, update_risk_model

app = FastAPI(title="ZavaRiskEngine", version="2.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health", response_class=HTMLResponse, status_code=200)
def health():
    """Health check endpoint for container monitoring."""
    return "OK"


@app.get("/", response_class=HTMLResponse)
def landing_page():
    """Landing page with unicorn branding."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>ZavaRiskEngine - Zava Bank</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .unicorn { font-size: 80px; }
        h1 { color: #6B46C1; }
        .status { color: #38A169; font-weight: bold; }
    </style>
</head>
<body>
    <div class="unicorn">\U0001F984</div>
    <h1>ZavaRiskEngine REST API - Online</h1>
    <p class="status">Service Running</p>
    <p><a href="/docs">API Documentation (Swagger)</a></p>
    <p><a href="/redoc">API Documentation (ReDoc)</a></p>
</body>
</html>"""


@app.post("/api/score-loan-application/{application_id}", response_model=RiskScoreResponse)
def api_score_loan_application(application_id: int):
    """Score a loan application and return risk assessment."""
    return score_loan_application(application_id)


@app.get("/api/risk-factors/{customer_id}", response_model=RiskFactorsResponse)
def api_get_risk_factors(customer_id: int):
    """Get risk factors for a customer."""
    return get_risk_factors(customer_id)


@app.post("/api/update-risk-model", response_model=RiskModelUpdateResponse)
def api_update_risk_model(model_params: RiskModelUpdateRequest):
    """Update risk model parameters."""
    return update_risk_model(model_params)
