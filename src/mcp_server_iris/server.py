import os
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import mcp.types as types
import iris as irisnative
from mcp_server_iris.mcpserver import MCPServer, Context
from mcp_server_iris.interoperability import init as interoperability

logger = logging.getLogger("mcp_server_iris")
logger.info("Starting InterSystems IRIS MCP Server")


def get_db_config():
    """Get database configuration from environment variables."""
    config = {
        "hostname": os.getenv("IRIS_HOSTNAME", "localhost"),
        "port": int(os.getenv("IRIS_PORT", 1972)),
        "namespace": os.getenv("IRIS_NAMESPACE", "USER"),
        "username": os.getenv("IRIS_USERNAME", "_SYSTEM"),
        "password": os.getenv("IRIS_PASSWORD", "SYS"),
    }

    if not all([config["username"], config["password"], config["namespace"]]):
        raise ValueError("Missing required database configuration")

    return config


@asynccontextmanager
async def server_lifespan(server: MCPServer) -> AsyncIterator[dict]:
    """Manage server startup and shutdown lifecycle."""
    config = get_db_config()
    try:
        db = irisnative.connect(**config)
        iris = irisnative.createIRIS(db)
        yield {"db": db, "iris": iris}
    except Exception:
        db = None
        iris = None
        yield {"db": db, "iris": iris}
    finally:
        if db:
            db.close()


server_name = "InterSystems IRIS MCP Server"
server_version = "0.1.0"
server = MCPServer(name=server_name, version=server_version, lifespan=server_lifespan)
interoperability(server, logger)

# @server.list_resources()
# async def list_resources() -> list[types.Resource]:
#     """List SQL Server tables as resources."""
#     try:
#         ctx = server.request_context
#         conn = ctx.lifespan_context["db"]
#         with conn.cursor() as cursor:
#             # Query to get user tables from the current database
#             cursor.execute(
#                 """
#                 SELECT TABLE_SCHEMA || '.' || TABLE_NAME TABLE_NAME
#                 FROM INFORMATION_SCHEMA.TABLES
#                 WHERE TABLE_TYPE = 'BASE TABLE'
#                 AND   TABLE_SCHEMA NOT LIKE 'Ens%'
#                 AND   TABLE_SCHEMA NOT LIKE 'HS%'
#             """
#             )
#             tables = cursor.fetchall()
#             logger.info(f"Found tables: {tables}")

#             resources = []
#             for table in tables:
#                 resources.append(
#                     types.Resource(
#                         uri=f"iris://{table[0]}/schema",
#                         name=f"Table: {table[0]} columns",
#                         mimeType="application/json",
#                         description=f"Columns in table: {table[0]}",
#                     )
#                 )
#                 resources.append(
#                     types.Resource(
#                         uri=f"iris://{table[0]}/data",
#                         name=f"Table: {table[0]} data",
#                         mimeType="application/json",
#                         description=f"Data in table: {table[0]}",
#                     )
#                 )
#             return resources
#     except Exception as e:
#         logger.error(f"Failed to list resources: {str(e)}")
#         return []


# def read_table_schema(conn, table) -> list[ReadResourceContents]:
#     try:
#         with conn.cursor() as cursor:
#             (schema, table_name) = table.split(".")
#             cursor.execute(
#                 """
#                     SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
#                 """,
#                 (schema, table_name),
#             )
#             rows = cursor.fetchall()
#             return [ReadResourceContents(json.dumps(rows), "application/json")]
#             # [{"content": rows, "mime_type": "application/json"}]
#     except Exception as e:
#         logger.error(
#             f"Database error reading resource data for table {table}: {str(e)}"
#         )
#         raise RuntimeError(f"Database error: {str(e)}")


# def read_table_data(conn, table) -> list[ReadResourceContents]:
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute(f"SELECT TOP 100 * FROM {table}")
#             rows = cursor.fetchall()
#             return [ReadResourceContents(json.dumps(rows), "application/json")]
#     except Exception as e:
#         logger.error(f"Database error reading table {table} columns: {str(e)}")
#         raise RuntimeError(f"Database error: {str(e)}")


# @server.read_resource()
# async def read_resource(uri: types.AnyUrl) -> str:
#     """Read table contents."""
#     uri_str = str(uri)
#     logger.info(f"Reading resource: {uri_str}")

#     if not uri_str.startswith("iris://"):
#         raise ValueError(f"Invalid URI scheme: {uri_str}")

#     (table, resource_type) = uri_str[7:].split("/")
#     logger.debug(f"Table: {table}, resource_type: {resource_type}; from url: {uri_str}")

#     ctx = server.request_context
#     conn = ctx.lifespan_context["db"]
#     if resource_type == "data":
#         return read_table_data(conn, table)
#     elif resource_type == "schema":
#         return read_table_schema(conn, table)
#     else:
#         raise RuntimeError(f"Unknown resource_type: {resource_type}")


@server.tool(description="Execute an SQL query on the Server")
async def execute_sql(
    query: str, ctx: Context, params: list[str] = []
) -> list[types.TextContent]:
    # params = arguments.get("params", [])
    logger.info(f"Executing SQL query: {query}")
    conn = ctx.db
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        # limit by 100 rows
        rows = cursor.fetchall()[:100]
        return [types.TextContent(type="text", text=str(rows))]


def main():
    import argparse

    parser = argparse.ArgumentParser(description=server_name)
    parser.add_argument(
        "transport",
        nargs="?",
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport type (stdio or sse)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3001,
        help="Port for SSE transport (default: 3001)",
    )
    parser.add_argument(
        "--debug",
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Debug",
    )

    args = parser.parse_args()
    server.settings.port = args.port
    server.settings.debug = args.debug
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
