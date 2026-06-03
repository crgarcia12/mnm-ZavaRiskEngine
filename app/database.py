import pyodbc

from app.config import get_connection_string, get_use_managed_identity


def get_connection() -> pyodbc.Connection:
    """Get a database connection, using Managed Identity if configured."""
    conn_str = get_connection_string()

    if get_use_managed_identity():
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        conn = pyodbc.connect(conn_str, attrs_before={1256: token.token.encode()})
    else:
        conn = pyodbc.connect(conn_str)

    return conn
