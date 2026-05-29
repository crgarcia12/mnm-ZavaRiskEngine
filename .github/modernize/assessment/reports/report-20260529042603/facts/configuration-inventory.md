# Configuration & Externalized Settings Inventory

This repository uses a small set of configuration sources centered on `web.config`, environment variables, and container runtime settings. Profile complexity is low, with Debug/Release build configurations and no explicit multi-environment appsettings files.

## Configuration Sources

| Source | Type | Path/Location | Notes |
|---|---|---|---|
| ASP.NET configuration | XML config | `web.config` | Connection string, WCF service hosting, handler mappings |
| Process environment | Externalized vars | Runtime env (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` and fallback `DATABASE_*`) | Used by `DbConfig` to override connection string |
| Project build config | MSBuild project file | `ZavaRiskEngine.csproj` | Target framework and build configuration defaults |
| Container config | Dockerfile | `Dockerfile` | Mono runtime, exposed port 8080, xsp4 startup command |

## Build Profiles

| Profile | Activation | Purpose | Key Dependencies/Plugins |
|---|---|---|---|
| Debug | Default/`Configuration=Debug` | Local debug build output to `bin\Debug\` | Framework references from .NET Framework 4.8 |
| Release | `Configuration=Release` | Release build output to `bin\Release\` | Framework references from .NET Framework 4.8 |

## Runtime Profiles

| Profile | Activation Method | Config Files | Key Overrides |
|---|---|---|---|
| Default | App host default | `web.config` | Uses `connectionStrings/ZavaBankDb` |
| Env-override runtime | Environment variables | Process env + `DbConfig` | DB host/port/name/user/password values override `web.config` |

## Properties Inventory

| Property Key | Default | Profiles | Source |
|---|---|---|---|
| `connectionStrings:ZavaBankDb` | `Server=sqlserver,1433;Database=ZavaBankDB;User Id=sa;******;TrustServerCertificate=true;` | Default | `web.config` |
| `system.web/compilation@debug` | `true` | Default | `web.config` |
| `system.web/compilation@targetFramework` | `4.8` | Default | `web.config` |
| `system.serviceModel/serviceMetadata@httpGetEnabled` | `true` | Default | `web.config` |
| `DB_HOST` / `DATABASE_HOST` | unset | Env-override runtime | Environment |
| `DB_PORT` / `DATABASE_PORT` | unset | Env-override runtime | Environment |
| `DB_NAME` / `DATABASE_NAME` | unset | Env-override runtime | Environment |
| `DB_USER` / `DATABASE_USER` | unset | Env-override runtime | Environment |
| `DB_PASSWORD` / `DATABASE_PASSWORD` | unset | Env-override runtime | Environment |

## Startup Parameters & Resource Requirements

| Service | JVM/Runtime Options | Memory | Instance Count |
|---|---|---|---|
| ZavaRiskEngine (xsp4 on Mono) | `xsp4 --port 8080 --address 0.0.0.0 --nonstop` | Not specified | Not specified |

## Startup Dependency Chain

1. `ZavaRiskEngine` process starts under Mono/xsp4.
2. Service operations become available when the process can resolve DB settings and open SQL connections.
3. Health endpoint `/health` is available through ASP.NET handler mapping.

## Secrets & Sensitive Configuration

| Secret Reference | Type | Storage (masked) |
|---|---|---|
| `connectionStrings:ZavaBankDb` password segment | Database credential | `web.config` (plaintext in repo; should be externalized) |
| `DB_PASSWORD` / `DATABASE_PASSWORD` | Database credential | Environment variable |

### Secrets Provisioning Workflow

Secrets can be provided through runtime environment variables consumed by `DbConfig`; if unset, the application falls back to `web.config` connection string values. No managed secret store integration (Key Vault, Vault, AWS Secrets Manager) is configured in this repository.

## Feature Flags

| Flag Name | Default | Controlled By |
|---|---|---|
| No explicit feature flags detected | n/a | n/a |

## Framework & Runtime Versions

| Component | Version | Source |
|---|---|---|
| .NET Framework target | v4.8 | `ZavaRiskEngine.csproj` |
| Service framework | WCF (`System.ServiceModel`) | Framework assembly reference |
| Web host | ASP.NET (`System.Web`) | Framework assembly reference |
| Runtime container image | `mono:6.12` | `Dockerfile` |
| Build tool format | Legacy MSBuild project (`ToolsVersion=4.0`) | `ZavaRiskEngine.csproj` |
