# Modernization Plan: modernization-plan

**Project**: mnm-ZavaRiskEngine

---

## Technical Framework

- **Language**: C# (.NET Framework 4.8)
- **Framework**: ASP.NET / WCF service (.svc)
- **Build Tool**: MSBuild (`.csproj`)
- **Database**: SQL Server (connection string `ZavaBankDb`)
- **Key Dependencies**: System.ServiceModel, System.Web, System.Configuration

---

## Overview

> This migration modernizes the existing risk engine service for Azure deployment.
> The application currently runs as a .NET Framework 4.8 WCF/ASP.NET service
> with SQL Server connectivity configured through environment variables and
> `web.config`. The modernization scope will:
>
> - Improve security posture by scanning and remediating dependency CVEs.
> - Prepare and deploy the application to Azure Container Apps.
> - Keep current business behavior while enabling cloud-ready operations.
>
> The migration follows a phased approach: security readiness first, then
> deployment enablement.

---

## Migration Impact Summary

| Application | Original Service | New Azure Service | Authentication | Comments |
|-------------|------------------|-------------------|----------------|----------|
| mnm-ZavaRiskEngine | Current hosted WCF/ASP.NET service | Azure Container Apps | Managed Identity | `givemeaplan` default Azure modernization scope |

---

## Open Questions & Questionnaire

- [x] Q: Should the plan include environment/infrastructure provisioning? → A: No — use existing infrastructure/configuration and focus on modernization tasks only (inferred default).
- [x] Q: Should the plan include integration testing to verify migrated services? → A: No — not explicitly requested in the prompt; integration testing task omitted.
- [x] Q: Should the plan include a security scan and CVE remediation task? → A: Yes — included by default.
- [x] Q: Which Azure deployment target should the plan use? → A: Azure Container Apps (default).
- [x] Q: Should the plan include a separate containerization task? → A: No — containerization is included in the deployment task for Azure Container Apps.
