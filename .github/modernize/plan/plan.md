# Modernization Plan: Zava Risk Engine — Convert to Python & Deploy to Azure

**Project**: ZavaRiskEngine

---

## Technical Framework

- **Language**: C# / .NET Framework 4.8
- **Framework**: ASP.NET WCF (Windows Communication Foundation) — SOAP service
- **Build Tool**: MSBuild (legacy `.csproj` format)
- **Database**: SQL Server (via `System.Data.SqlClient`, username/password credentials)
- **Key Dependencies**: `System.ServiceModel` (WCF), `System.Data.SqlClient`, `System.Web`

---

## Overview

> This migration converts the ZavaRiskEngine from a legacy .NET Framework 4.8 WCF SOAP service to a modern Python web service, then deploys it to Azure Container Apps.
>
> The application currently exposes three operations — loan application scoring, customer risk factor retrieval, and risk model parameter updates — as a WCF SOAP endpoint backed by SQL Server with username/password authentication.
>
> The new architecture will:
>
> - Replace the WCF SOAP service with a Python-based REST API exposing equivalent endpoints
> - Update the application icon/branding to feature a unicorn
> - Scan and remediate all known CVEs in dependencies
> - Deploy the containerized Python service to Azure Container Apps using Managed Identity for secure Azure resource access
>
> The migration follows a phased approach: code conversion first, then security hardening, and finally containerized deployment to Azure.

---

## Migration Impact Summary

```
| Application     | Original Service          | New Azure Service       | Authentication    | Comments                          |
|-----------------|---------------------------|-------------------------|-------------------|-----------------------------------|
| ZavaRiskEngine  | .NET WCF SOAP service     | Python REST API on ACA  | Managed Identity  | Convert from .NET 4.8 WCF to Python |
| ZavaRiskEngine  | SQL Server (user/password)| Azure SQL Database      | Managed Identity  | Migrate DB to passwordless auth   |
| ZavaRiskEngine  | Static app icon           | Unicorn icon/branding   | N/A               | Change app icon to unicorn        |
```

---

## Open Questions & Questionnaire

- [x] Q: Should environment/infrastructure provisioning be included? → A: No — no existing IaC found; focus on code migration and deployment to new Azure Container Apps resource
- [x] Q: Should integration testing be included? → A: No — not explicitly requested; skipped
- [x] Q: Should security/CVE remediation be included? → A: Yes — always included by default
- [x] Q: What Azure deployment target should be used? → A: Azure Container Apps (default, includes containerization)
