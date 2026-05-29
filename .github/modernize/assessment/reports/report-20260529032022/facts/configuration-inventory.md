# Configuration & Externalized Settings Inventory

The project uses a small configuration surface primarily from `web.config`, environment variables, and container runtime settings.

## Configuration Sources

| Source | Type | Path/Location | Notes |
|---|---|---|---|
| web.config | XML app config | `web.config` | Connection strings, WCF/service behavior, handlers |
| Environment variables | Runtime overrides | Process/container env | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` and fallback names |
| Dockerfile | Container build/runtime | `Dockerfile` | Mono runtime image, exposed port 8080, startup command |

## Build Profiles

| Profile | Activation | Purpose | Key Dependencies/Plugins |
|---|---|---|---|
| Debug | `Configuration=Debug` | Local debug build output | `OutputPath=bin\Debug\` |
| Release | `Configuration=Release` | Release build output | `OutputPath=bin\Release\` |

## Runtime Profiles

| Profile | Activation Method | Config Files | Key Overrides |
|---|---|---|---|
| Default | ASP.NET/WCF host startup | `web.config` | Uses `ZavaBankDb` connection string |
| Env-overridden | Set DB_* or DATABASE_* env vars | env + `web.config` fallback | Replaces DB host/port/name/user/password |

## Properties Inventory

| Property Key | Default | Profiles | Source |
|---|---|---|---|
| `connectionStrings:ZavaBankDb` | SQL connection string in file | Default | `web.config` |
| `system.web/compilation@debug` | `true` | Default | `web.config` |
| `system.web/customErrors@mode` | `Off` | Default | `web.config` |
| `DB_HOST` / `DATABASE_HOST` | none | Env-overridden | Environment variable |
| `DB_PORT` / `DATABASE_PORT` | none | Env-overridden | Environment variable |
| `DB_NAME` / `DATABASE_NAME` | none | Env-overridden | Environment variable |
| `DB_USER` / `DATABASE_USER` | none | Env-overridden | Environment variable |
| `DB_PASSWORD` / `DATABASE_PASSWORD` | none | Env-overridden | Environment variable |

## Startup Parameters & Resource Requirements

| Service | JVM/Runtime Options | Memory | Instance Count |
|---|---|---|---|
| ZavaRiskEngine (Mono xsp4) | `xsp4 --port 8080 --address 0.0.0.0 --nonstop` | Not specified | Not specified |

## Startup Dependency Chain

1. `ZavaRiskEngine` starts and loads `web.config`.
2. On first DB operation, `DbConfig` resolves env overrides or default connection string.
3. Service operations depend on SQL Server availability before business requests can complete.

## Secrets & Sensitive Configuration

| Secret Reference | Type | Storage (masked) |
|---|---|---|
| `connectionStrings:ZavaBankDb` password segment | DB credential | `web.config` (`[MASKED]`) |
| `DB_PASSWORD` / `DATABASE_PASSWORD` | DB credential | Environment variable (`[MASKED]`) |

### Secrets Provisioning Workflow

Secrets can be injected as environment variables at deployment runtime, otherwise the service falls back to file-based credentials in `web.config`. No external secret manager integration or managed identity workflow is defined in the repository.

## Feature Flags

No feature flag framework or conditional feature toggles were found.

## Framework & Runtime Versions

| Component | Version | Source |
|---|---|---|
| .NET Framework target | 4.8 | `ZavaRiskEngine.csproj` |
| WCF / ASP.NET assemblies | .NET Framework 4.8 | `ZavaRiskEngine.csproj` references |
| Container base image | `mono:6.12` | `Dockerfile` |
| Build format | Legacy MSBuild (`ToolsVersion=4.0`) | `ZavaRiskEngine.csproj` |
