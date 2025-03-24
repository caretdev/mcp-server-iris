import asyncio
import uvicorn
from typing import Any, Callable, Literal
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.server.models import InitializationOptions
from pydantic_settings import BaseSettings, SettingsConfigDict
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.fastmcp.tools import ToolManager
from mcp.server.fastmcp.prompts import PromptManager
from mcp.server.fastmcp.resources import ResourceManager
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context as FastMCPContext
from mcp.server.fastmcp.utilities.logging import configure_logging, get_logger

logger = get_logger(__name__)

Context = FastMCPContext


class Settings(BaseSettings):
    """MCPServer server settings.

    All settings can be configured via environment variables with the prefix MCP_.
    For example, MCP_DEBUG=true will set debug=True.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        extra="ignore",
    )

    # Server settings
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = (
        "DEBUG" if debug else "INFO"
    )

    # HTTP settings
    host: str = "0.0.0.0"
    port: int = 3001

    # resource settings
    warn_on_duplicate_resources: bool = True

    # tool settings
    warn_on_duplicate_tools: bool = True

    # prompt settings
    warn_on_duplicate_prompts: bool = True


class MCPServer(FastMCP):

    def __init__(
        self,
        name: str,
        version: str | None = None,
        instructions: str | None = None,
        lifespan: Callable | None = None,
        **settings,
    ):
        super().__init__(
            name=name, version=version, instructions=instructions, lifespan=lifespan
        )

        self._mcp_server = Server(
            name=name,
            version=version,
            instructions=instructions,
            lifespan=lifespan,
        )

        self.settings = Settings(**settings)

        self._tool_manager = ToolManager(
            warn_on_duplicate_tools=self.settings.warn_on_duplicate_tools
        )
        self._resource_manager = ResourceManager(
            warn_on_duplicate_resources=self.settings.warn_on_duplicate_resources
        )
        self._prompt_manager = PromptManager(
            warn_on_duplicate_prompts=self.settings.warn_on_duplicate_prompts
        )

        self._setup_handlers()

        configure_logging(self.settings.log_level)

    @property
    def name(self) -> str:
        return self._mcp_server.name

    @property
    def version(self) -> str:
        return self._mcp_server.version

    # def _setup_handlers(self) -> None:
    #     """Set up core MCP protocol handlers."""
    #     self._mcp_server.list_tools()(self.list_tools)
    #     self._mcp_server.call_tool()(self.call_tool)
    #     self._mcp_server.list_resources()(self.list_resources)
    #     self._mcp_server.read_resource()(self.read_resource)
    #     self._mcp_server.list_prompts()(self.list_prompts)
    #     self._mcp_server.get_prompt()(self.get_prompt)
    #     self._mcp_server.list_resource_templates()(self.list_resource_templates)

    def run(self, transport: Literal["stdio", "sse"] = "stdio") -> None:
        """Run the FastMCP server. Note this is a synchronous function.

        Args:
            transport: Transport protocol to use ("stdio" or "sse")
        """

        TRANSPORTS = Literal["stdio", "sse"]
        if transport not in TRANSPORTS.__args__:  # type: ignore
            raise ValueError(f"Unknown transport: {transport}")
        if transport == "stdio":
            asyncio.run(self.run_stdio_async())
        else:  # transport == "sse"
            asyncio.run(self.run_sse_async())

    async def run_stdio_async(self) -> None:
        """Run the server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self._mcp_server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=self.name,
                    server_version=self.version,
                    capabilities=self._mcp_server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    async def run_sse_async(self) -> None:
        """Run the server using SSE transport."""
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self._mcp_server.run(
                    streams[0],
                    streams[1],
                    InitializationOptions(
                        server_name=self.name,
                        server_version=self.version,
                        capabilities=self._mcp_server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )

        starlette_app = Starlette(
            debug=self.settings.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()
