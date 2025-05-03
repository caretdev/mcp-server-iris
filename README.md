[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/caretdev-mcp-server-iris-badge.png)](https://mseep.ai/app/caretdev-mcp-server-iris)

# mcp-server-iris: An InterSystems IRIS MCP server

<a href="https://glama.ai/mcp/servers/@caretdev/mcp-server-iris">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@caretdev/mcp-server-iris/badge" />
</a>

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

![ClaudeIRISInteroperability](https://github.com/user-attachments/assets/ec5b90e6-1cd3-467a-8875-72a13606a747)
