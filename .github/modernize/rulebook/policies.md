# Policies

Enforceable standards and hard boundaries for modernization. Every policy here is validatable against generated artifacts.

## Guardrails (Hard Boundaries)

### Prohibited Technologies

| Technology | Reason | Approved Alternative |
|-----------|--------|---------------------|
| Any database service not in the approved list | Only Azure SQL, Azure Database for PostgreSQL, and Azure Cosmos DB are supported | Azure SQL, Azure Database for PostgreSQL, Azure Cosmos DB |

### Required Elements

Every modernized application must include:

#### Data Services

- Database tier must use one of the approved services: **Azure SQL**, **Azure Database for PostgreSQL**, or **Azure Cosmos DB**.
