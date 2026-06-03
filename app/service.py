from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException

from app.database import get_connection
from app.models import (
    RiskFactorItem,
    RiskFactorsResponse,
    RiskModelUpdateRequest,
    RiskModelUpdateResponse,
    RiskScoreResponse,
)


def _clamp(value: Decimal, min_val: Decimal, max_val: Decimal) -> Decimal:
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def _normalize_credit_score(credit_score: int) -> Decimal:
    return _clamp((Decimal(credit_score) - Decimal(300)) / Decimal(550), Decimal(0), Decimal(1))


def _normalize_balance(balance: Decimal, requested_amount: Decimal) -> Decimal:
    if requested_amount <= Decimal(0):
        return Decimal("0.5")
    return _clamp(balance / requested_amount, Decimal(0), Decimal(1))


def _normalize_term(term_months: int) -> Decimal:
    return _clamp(Decimal(1) - (Decimal(term_months) / Decimal(360)), Decimal(0), Decimal(1))


def _normalize_loan_amount(requested_amount: Decimal) -> Decimal:
    return _clamp(Decimal(1) - (requested_amount / Decimal(500000)), Decimal(0), Decimal(1))


def _get_rating(score: Decimal) -> str:
    if score >= Decimal(85):
        return "A"
    if score >= Decimal(75):
        return "B"
    if score >= Decimal(65):
        return "C"
    if score >= Decimal(55):
        return "D"
    if score >= Decimal(45):
        return "E"
    return "F"


def _get_approval_multiplier(rating: str) -> Decimal:
    multipliers = {
        "A": Decimal("1.25"),
        "B": Decimal("1.10"),
        "C": Decimal("0.90"),
        "D": Decimal("0.70"),
        "E": Decimal("0.50"),
    }
    return multipliers.get(rating, Decimal(0))


def _round2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_model_value(model: dict, key: str, default: Decimal) -> Decimal:
    return model.get(key.lower(), default)


def _ensure_risk_model_table(cursor) -> None:
    cursor.execute("""
        IF OBJECT_ID('dbo.RiskModelParameters', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.RiskModelParameters
            (
                ParameterName NVARCHAR(100) NOT NULL PRIMARY KEY,
                ParameterValue DECIMAL(18,6) NOT NULL,
                ModifiedDate DATETIME NOT NULL DEFAULT GETDATE(),
                ModifiedBy NVARCHAR(100) NULL
            );
        END
    """)
    cursor.commit()


def _load_model_parameters(cursor) -> dict:
    cursor.execute("SELECT ParameterName, ParameterValue FROM RiskModelParameters")
    params = {}
    for row in cursor.fetchall():
        params[row[0].lower()] = Decimal(str(row[1]))
    return params


def _load_factor_metadata(cursor) -> dict:
    cursor.execute("SELECT FactorCode, FactorName, Weight FROM RiskFactors WHERE IsActive = 1")
    metadata = {}
    for row in cursor.fetchall():
        metadata[row[0].upper()] = RiskFactorItem(
            factor_code=row[0],
            factor_name=row[1],
            weight=float(row[2]) if row[2] is not None else 1.0,
        )
    return metadata


def _build_factor(metadata: dict, code: str, value: Decimal) -> RiskFactorItem:
    base = metadata.get(code.upper())
    if base is None:
        base = RiskFactorItem(factor_code=code, factor_name=code, weight=1.0)

    normalized_value = _round2(_clamp(value, Decimal(0), Decimal(100)))
    weight = Decimal(str(base.weight)) if base.weight > 0 else Decimal(1)
    impact_score = _round2(normalized_value * weight)

    return RiskFactorItem(
        factor_code=base.factor_code,
        factor_name=base.factor_name,
        weight=base.weight,
        value=float(normalized_value),
        impact_score=float(impact_score),
    )


def score_loan_application(application_id: int) -> RiskScoreResponse:
    if application_id <= 0:
        raise HTTPException(status_code=400, detail="applicationId must be greater than 0.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        _ensure_risk_model_table(cursor)

        cursor.execute("""
            SELECT TOP 1
                la.CustomerID,
                la.RequestedAmount,
                la.TermMonths,
                ISNULL(a.Balance, 0) AS Balance,
                ISNULL((
                    SELECT TOP 1 cs.Score
                    FROM CreditScores cs
                    WHERE cs.CustomerID = la.CustomerID
                    ORDER BY cs.ReportDate DESC
                ), 650) AS CreditScore
            FROM LoanApplications la
            LEFT JOIN Accounts a ON a.AccountID = la.LoanAccountID
            WHERE la.ApplicationID = ?
        """, application_id)

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Loan application was not found.")

        customer_id = int(row[0])
        requested_amount = Decimal(str(row[1]))
        term_months = int(row[2])
        account_balance = Decimal(str(row[3]))
        credit_score = int(row[4])

        model = _load_model_parameters(cursor)
        weighted_score = (
            _normalize_credit_score(credit_score) * _get_model_value(model, "CreditScoreWeight", Decimal("0.45"))
            + _normalize_balance(account_balance, requested_amount) * _get_model_value(model, "BalanceWeight", Decimal("0.20"))
            + _normalize_term(term_months) * _get_model_value(model, "TermWeight", Decimal("0.10"))
            + _normalize_loan_amount(requested_amount) * _get_model_value(model, "RequestedAmountWeight", Decimal("0.25"))
        )

        base_score = _get_model_value(model, "BaseScore", Decimal(5))
        final_score = _round2(base_score + weighted_score * Decimal(100))
        rating = _get_rating(final_score)
        max_approved_amount = _round2(requested_amount * _get_approval_multiplier(rating))

        cursor.execute("""
            INSERT INTO RiskAssessments (ApplicationID, CustomerID, OverallRiskScore, RiskLevel, Recommendation, FactorBreakdown)
            VALUES (?, ?, ?, ?, ?, ?)
        """, application_id, customer_id, float(final_score), rating,
            "Deny" if rating == "F" else "Review",
            f"CreditScore={credit_score};RequestedAmount={requested_amount};TermMonths={term_months};Balance={account_balance}")
        cursor.commit()

        return RiskScoreResponse(
            applicationId=application_id,
            customerId=customer_id,
            requestedAmount=float(requested_amount),
            maxApprovedAmount=float(max_approved_amount),
            calculatedScore=float(final_score),
            riskRating=rating,
            evaluatedAtUtc=datetime.now(timezone.utc),
        )
    finally:
        conn.close()


def get_risk_factors(customer_id: int) -> RiskFactorsResponse:
    if customer_id <= 0:
        raise HTTPException(status_code=400, detail="customerId must be greater than 0.")

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ISNULL((SELECT TOP 1 Score FROM CreditScores WHERE CustomerID = ? ORDER BY ReportDate DESC), 650) AS CreditScore,
                ISNULL((SELECT SUM(RequestedAmount) FROM LoanApplications WHERE CustomerID = ? AND Status IN ('Submitted','UnderReview','Approved')), 0) AS OpenLoanExposure,
                ISNULL((SELECT AVG(Balance) FROM Accounts WHERE CustomerID = ?), 0) AS AverageBalance,
                ISNULL((SELECT COUNT(*) FROM Accounts WHERE CustomerID = ? AND Status = 'Active'), 0) AS ActiveAccountCount
        """, customer_id, customer_id, customer_id, customer_id)

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer risk profile was not found.")

        credit_score = int(row[0])
        open_loan_exposure = Decimal(str(row[1]))
        avg_balance = Decimal(str(row[2]))
        active_account_count = int(row[3])

        factor_metadata = _load_factor_metadata(cursor)
        factors = [
            _build_factor(factor_metadata, "CREDIT_SCORE", _normalize_credit_score(credit_score) * Decimal(100)),
            _build_factor(factor_metadata, "EXIST_DEBT", _round2(Decimal(100) - _clamp(open_loan_exposure / Decimal(5000), Decimal(0), Decimal(100)))),
            _build_factor(factor_metadata, "ASSET_RES", _clamp(avg_balance / Decimal(200), Decimal(0), Decimal(100))),
            _build_factor(factor_metadata, "ACCT_AGE", _clamp(Decimal(active_account_count) * Decimal(12), Decimal(0), Decimal(100))),
        ]

        weighted_total = Decimal(0)
        weight_sum = Decimal(0)
        for factor in factors:
            weighted_total += Decimal(str(factor.impact_score))
            w = Decimal(str(factor.weight))
            weight_sum += Decimal(1) if w <= Decimal(0) else w

        overall = Decimal(0) if weight_sum == Decimal(0) else _round2(weighted_total / weight_sum)

        return RiskFactorsResponse(
            customerId=customer_id,
            overallScore=float(overall),
            factors=factors,
        )
    finally:
        conn.close()


def update_risk_model(model_params: RiskModelUpdateRequest) -> RiskModelUpdateResponse:
    if not model_params.parameters:
        raise HTTPException(status_code=400, detail="modelParams with at least one parameter is required.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        _ensure_risk_model_table(cursor)

        updated_count = 0
        for param in model_params.parameters:
            if not param.name or not param.name.strip():
                continue

            cursor.execute("""
                IF EXISTS (SELECT 1 FROM RiskModelParameters WHERE ParameterName = ?)
                BEGIN
                    UPDATE RiskModelParameters
                    SET ParameterValue = ?,
                        ModifiedDate = GETDATE(),
                        ModifiedBy = ?
                    WHERE ParameterName = ?;
                END
                ELSE
                BEGIN
                    INSERT INTO RiskModelParameters (ParameterName, ParameterValue, ModifiedBy)
                    VALUES (?, ?, ?);
                END
            """, param.name.strip(), param.value,
                model_params.updated_by.strip() if model_params.updated_by else "SYSTEM",
                param.name.strip(), param.name.strip(), param.value,
                model_params.updated_by.strip() if model_params.updated_by else "SYSTEM")

            if cursor.rowcount > 0:
                updated_count += 1

        cursor.commit()

        return RiskModelUpdateResponse(
            success=True,
            updatedCount=updated_count,
            message="Risk model parameters updated.",
            updatedAtUtc=datetime.now(timezone.utc),
        )
    finally:
        conn.close()
