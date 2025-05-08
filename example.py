import sys
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self):
        """Connect to an MCP server"""
        server_params = StdioServerParameters(
            command=sys.executable, args=["-m", "mcp_server_iris"], env=None
        )
        # server_params = StdioServerParameters(
        #     command="uvx", args=["mcp-server-iris"], env=None
        # )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print(
            "\nConnected to server with tools:",
            "\n\t".join([""] + [tool.name for tool in tools]),
        )

    async def process_query(self, query: str) -> str:
        response = await self.session.call_tool(
            "execute_sql",
            {
                "query": query,
                "params": [],
            },
        )
        print("Response from execute_sql:", response.content)
        return

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    client = MCPClient()
    try:
        await client.connect_to_server()
        await client.session.set_logging_level("debug")
        await client.process_query("select $namespace, $zversion")
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
