# mcp-server-iris: An InterSystems IRIS MCP server

## Overview

A [Model Context Protocol](https://modelcontextprotocol.io/introduction) server for InterSystems IRIS database interaction and automation.

## Configure Claude

- [Claude Desktop](https://claude.ai/download)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

```json
{
  "mcpServers": {
    "iris": {
      "command": "uvx",
      "args": [
        "mcp-server-iris"
      ],
      "env": {
        "IRIS_HOSTNAME": "localhost",
        "IRIS_PORT": "1972",
        "IRIS_NAMESPACE": "USER",
        "IRIS_USERNAME": "_SYSTEM",
        "IRIS_PASSWORD": "SYS"
      }
    }
  }
}
```
