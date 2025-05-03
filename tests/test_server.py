import sys
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp_server_iris.server import server


@pytest.fixture
def iris_config(request):
    return {
        "IRIS_HOSTNAME": request.config.option.iris_host,
        "IRIS_PORT": str(request.config.option.iris_port),
        "IRIS_NAMESPACE": request.config.option.iris_namespace,
        "IRIS_USERNAME": request.config.option.iris_username,
        "IRIS_PASSWORD": request.config.option.iris_password,
    }


def test_server_initialization():
    """Test that the server initializes correctly."""
    assert server.name == "InterSystems IRIS MCP Server"


@pytest.mark.asyncio
async def test_list_tools():
    """Test that list_tools returns expected tools."""
    tools = await server.list_tools()
    assert len(tools) > 0


@pytest.mark.asyncio
async def test_params_in_tool():
    tools = await server.list_tools()
    execute_sql_tool = next(t for t in tools if t.name == "execute_sql")
    props = list(execute_sql_tool.inputSchema["properties"].keys())
    assert len(props) == 2
    assert props[0] == "query"
    assert props[1] == "params"


@pytest.mark.asyncio
async def test_call_tool_execute_sql(iris_config):
    """Test calling execute_sql with a query."""
    print("IRIS_CONFIG", iris_config)
    async with stdio_client(StdioServerParameters(command=sys.executable, args=["-m", "mcp_server_iris"], env=iris_config)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            _ = await session.call_tool(
                "execute_sql",
                {
                    "query": "select $namespace, $zversion",
                    "params": [],
                },
            )
