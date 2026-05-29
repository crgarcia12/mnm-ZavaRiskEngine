# Data Architecture & Persistence Layer

The data layer is implemented with direct ADO.NET access to a single SQL Server database and runtime-created support tables for risk model parameters.

## Database Configuration

| Service/Module | DB Type | Profile | Driver | Connection | Migration Tool |
|---|---|---|---|---|---|
| ZavaRiskEngine | SQL Server | Default / env override | `System.Data.SqlClient` | `Server=...;Database=...;User Id=...;****** from env vars or `web.config` | None detected |

## Data Ownership per Service

| Service | Tables Owned | ORM Framework | Caching | Notes |
|---|---|---|---|---|
| ZavaRiskEngine | `RiskAssessments`, `RiskModelParameters` (plus reads from `LoanApplications`, `Accounts`, `CreditScores`, `RiskFactors`) | ADO.NET (no ORM) | None | `RiskModelParameters` is created on demand if missing |

## Entity Model

```mermaid
erDiagram
    CUSTOMERS ||--o{ LOAN_APPLICATIONS : "submits"
    CUSTOMERS ||--o{ ACCOUNTS : "owns"
    CUSTOMERS ||--o{ CREDIT_SCORES : "has"
    CUSTOMERS ||--o{ RISK_ASSESSMENTS : "evaluated by"
    LOAN_APPLICATIONS ||--o{ RISK_ASSESSMENTS : "generates"
    CUSTOMERS {
        int CustomerID PK
    }
    LOAN_APPLICATIONS {
        int ApplicationID PK
        int CustomerID FK
        int LoanAccountID FK
        decimal RequestedAmount
        int TermMonths
        string Status
    }
    ACCOUNTS {
        int AccountID PK
        int CustomerID FK
        decimal Balance
        string Status
    }
    CREDIT_SCORES {
        int CustomerID FK
        int Score
        datetime ReportDate
    }
    RISK_FACTORS {
        string FactorCode PK
        string FactorName
        decimal Weight
        bool IsActive
    }
    RISK_MODEL_PARAMETERS {
        string ParameterName PK
        decimal ParameterValue
        datetime ModifiedDate
        string ModifiedBy
    }
    RISK_ASSESSMENTS {
        int ApplicationID FK
        int CustomerID FK
        decimal OverallRiskScore
        string RiskLevel
        string Recommendation
        string FactorBreakdown
    }
```

## Key Repository Methods

| Service | Repository | Notable Methods | Purpose |
|---|---|---|---|
| ZavaRiskEngine | Inline SQL in `ZavaRiskEngineService.cs` | `ScoreLoanApplication` SELECT+INSERT flow | Computes and stores risk assessment for an application |
| ZavaRiskEngine | Inline SQL in `ZavaRiskEngineService.cs` | `GetRiskFactors` aggregate SELECTs | Builds factor list and overall score for a customer |
| ZavaRiskEngine | Inline SQL in `ZavaRiskEngineService.cs` | `UpdateRiskModel` upsert within transaction | Updates or inserts model parameters safely |
| ZavaRiskEngine | Inline SQL in `ZavaRiskEngineService.cs` | `EnsureRiskModelTableExists` | Initializes required table at runtime |

## Caching Strategy

No caching provider, cache regions, or cache annotations were found. All reads are served directly from SQL Server.

## Data Ownership Boundaries

The application is a single-service topology with one shared SQL Server database. Data composition occurs inside SQL statements and in-memory calculations within the same service process; no cross-service data ownership boundaries were found.

### Data Classification & Sensitivity

| Entity | Sensitive Fields | Classification (PII/PHI/PCI/None) | Controls in Place |
|---|---|---|---|
| CUSTOMERS | Name/contact/customer identifiers (inferred) | PII | No masking or encryption controls visible in repo |
| LOAN_APPLICATIONS | Requested loan amounts and status | Confidential financial | No explicit data-protection controls in repo |
| ACCOUNTS | Balance data | Confidential financial | No explicit data-protection controls in repo |
| RISK_ASSESSMENTS | Risk scores and recommendations | Confidential financial | No explicit data-protection controls in repo |
