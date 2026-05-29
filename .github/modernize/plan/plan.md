# Modernization Plan: ZavaRiskEngine – Modernize to .NET 10 and Azure

**Project**: ZavaRiskEngine

---

## Technical Framework

- **Language**: C# / .NET Framework 4.8
- **Framework**: WCF (Windows Communication Foundation) – legacy `System.ServiceModel` SOAP service hosted via Mono/XSP4
- **Build Tool**: MSBuild (legacy non-SDK-style `.csproj`)
- **Database**: SQL Server (Docker container) using `System.Data.SqlClient` with username/password credentials
- **Key Dependencies**: System.ServiceModel (WCF), System.Data.SqlClient, System.Configuration

---

## Overview

> This migration modernizes the ZavaRiskEngine from a legacy .NET Framework 4.8 WCF application to a cloud-native .NET 10 service deployed on Azure. The application currently runs as a SOAP/WCF service hosted on Mono, using a SQL Server database with username/password authentication. The new architecture will:
>
> - Upgrade to .NET 10, converting the project format to SDK-style and replacing legacy WCF/ASP.NET hosting with modern .NET equivalents
> - Migrate the SQL Server dependency to Azure SQL Database with passwordless Managed Identity authentication, eliminating hard-coded credentials
> - Configure cloud-native console logging so logs are correctly captured by Azure's log aggregation infrastructure
> - Scan and remediate all known CVEs in project dependencies
> - Deploy the modernized application to Azure Container Apps for scalable, cloud-native hosting
>
> The migration follows a phased approach: framework upgrade first, then cloud service migrations, security hardening, and finally deployment.

---

## Migration Impact Summary

| Application      | Original Service             | New Azure Service        | Authentication   | Comments                                      |
|------------------|------------------------------|--------------------------|------------------|-----------------------------------------------|
| ZavaRiskEngine   | SQL Server (Docker/on-prem)  | Azure SQL Database       | Managed Identity | Eliminate username/password connection string |
| ZavaRiskEngine   | Console/ASP.NET logging      | Azure Monitor (via logs) | N/A              | Configure stdout/stderr for cloud log capture |
| ZavaRiskEngine   | Mono/XSP4 host (Docker)      | Azure Container Apps     | Managed Identity | Deploy containerized .NET 10 app to ACA       |

---

## Open Questions & Questionnaire

- [x] Q: Should the plan include environment/infrastructure provisioning? → A: No — no infrastructure provisioning; focus on code migration and deployment only
- [x] Q: Should the plan include integration testing to verify migrated services? → A: No — skip integration testing (not explicitly requested)
- [x] Q: Should the plan include a security scan and CVE remediation task? → A: Yes — include security/CVE remediation (default)
- [x] Q: Which Azure deployment target should the plan use? → A: Azure Container Apps (default)
