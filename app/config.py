import os


def get_connection_string() -> str:
    """Build a SQL Server connection string from environment variables."""
    host = os.environ.get("DB_HOST") or os.environ.get("DATABASE_HOST", "")
    port = os.environ.get("DB_PORT") or os.environ.get("DATABASE_PORT", "1433")
    name = os.environ.get("DB_NAME") or os.environ.get("DATABASE_NAME", "")
    user = os.environ.get("DB_USER") or os.environ.get("DATABASE_USER", "")
    password = os.environ.get("DB_PASSWORD") or os.environ.get("DATABASE_PASSWORD", "")

    if host and name:
        parts = [
            "DRIVER={ODBC Driver 18 for SQL Server}",
            f"SERVER={host},{port}",
            f"DATABASE={name}",
            f"UID={user}",
            f"PWD={password}",
            "TrustServerCertificate=yes",
        ]
        return ";".join(parts) + ";"
    return ""


def get_use_managed_identity() -> bool:
    """Check if Managed Identity should be used for Azure SQL authentication."""
    return os.environ.get("USE_MANAGED_IDENTITY", "false").lower() == "true"
