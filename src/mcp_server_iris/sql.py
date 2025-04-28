import logging
import mcp.types as types
from mcp_server_iris.mcpserver import MCPServer, Context


def init(server: MCPServer, logger: logging.Logger) -> None:
    """Initialize the SQL server with a tool to execute SQL queries."""
    logger.info("Initializing SQL tool for InterSystems IRIS MCP Server")

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
