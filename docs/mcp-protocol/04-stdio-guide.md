# Building MCP Servers with stdio Transport

> Sources:
> - https://dev.to/elsayed85/building-model-context-protocol-mcp-servers-with-stdio-a-complete-guide-513k
> - https://gofastmcp.com/deployment/running-server
> - https://modelcontextprotocol.info/docs/concepts/transports/

stdio (Standard Input/Output) is the default and most commonly used transport for MCP servers. The client spawns the server as a subprocess and communicates through stdin/stdout streams.

---

## How stdio Transport Works

1. **Client spawns server**: The MCP client (e.g., Claude Desktop, Claude Code) starts the server as a child process
2. **Messages via stdin/stdout**: JSON-RPC 2.0 messages are written to the server's stdin and read from its stdout
3. **One message per line**: Each JSON-RPC message is a single line terminated by newline
4. **Lifecycle managed by client**: The client starts and stops the server process
5. **One client per server**: Each stdio server instance serves exactly one client

**CRITICAL**: Anything written to stdout is interpreted as protocol messages. Never use `print()` for debugging. Use `stderr` or Context logging methods instead.

---

## Why Choose stdio?

- **Simplicity**: Easy to implement and debug
- **Local development**: Perfect for testing and development
- **Security**: Runs in the same process space, no network exposure
- **Performance**: Low latency for local operations
- **Claude Desktop/Code integration**: The standard transport for local MCP servers

---

## Project Setup

### Directory Structure

```
my-mcp-server/
  server.py
  pyproject.toml
  requirements.txt  (or use pyproject.toml)
```

### Dependencies (pyproject.toml)

```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "mcp[cli]>=1.9.2",
    "httpx>=0.28.1",  # if making HTTP requests
]
```

### Install Dependencies

```bash
# With uv
uv sync

# With pip
pip install "mcp[cli]"
```

---

## Basic stdio Server (FastMCP)

```python
from fastmcp import FastMCP

mcp = FastMCP(name="My stdio Server")

@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b

if __name__ == "__main__":
    mcp.run()  # Uses stdio transport by default
```

Run with:

```bash
python server.py
```

---

## Explicit stdio with FastMCP

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Or via CLI:

```bash
fastmcp run server.py
# or
fastmcp run server.py --transport stdio
```

---

## Low-Level stdio Server

For full protocol control without FastMCP:

```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("my-server")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="sum_two_numbers",
            description="A tool that sums two numbers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "sum_two_numbers":
        a = arguments["a"]
        b = arguments["b"]
        result = a + b
        return [types.TextContent(type="text", text=f"The sum of {a} and {b} is {result}")]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Complex Example: API Integration Server

```python
from fastmcp import FastMCP
from typing import List, Dict, Any, Optional
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="DevTo_Search_MCP_Server")

@mcp.tool(
    name="search_dev_to_articles",
    description="""
    Search for articles on dev.to by topic/keyword.

    Args:
        query (str): The search query/topic to search for
        per_page (int, optional): Number of articles to return (default: 10)
        page (int, optional): Page number for pagination (default: 1)
        tag (str, optional): Filter by specific tag
        username (str, optional): Filter by specific username

    Returns:
        List of article objects with title, description, URL, tags, etc.
    """,
)
async def search_dev_to_articles(
    query: str,
    per_page: Optional[int] = 10,
    page: Optional[int] = 1,
    tag: Optional[str] = None,
    username: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for articles on dev.to using the public API."""
    try:
        params = {
            "per_page": min(per_page, 1000),
            "page": page,
        }

        if query:
            params["q"] = query.replace(" ", "+")
        if tag:
            params["tag"] = tag
        if username:
            params["username"] = username

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://dev.to/api/articles",
                params=params
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return {"error": f"Failed to fetch articles: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

if __name__ == "__main__":
    mcp.run()
```

---

## Debugging stdio Servers

### Use stderr for Debug Output

```python
import sys

def debug_log(message):
    print(message, file=sys.stderr)
```

### Use Context Logging (FastMCP)

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("debug-server")

@mcp.tool
async def my_tool(input: str, ctx: Context) -> str:
    await ctx.debug("Debug: starting processing")
    await ctx.info(f"Processing: {input}")
    await ctx.warning("Something might be wrong")
    await ctx.error("Something went wrong")
    return "result"
```

### Use Python Logging to stderr

```python
import logging
import sys

# Configure logging to stderr (not stdout!)
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("This goes to stderr, not stdout")
```

### MCP Inspector

The MCP Inspector is a visual tool for testing MCP servers:

```bash
# Install and run
npx @modelcontextprotocol/inspector

# Then in the UI:
# Transport Type: STDIO
# Command: python server.py
```

Or with the CLI:

```bash
npx @modelcontextprotocol/inspector --cli \
  --method tools/call \
  --tool-name add \
  --tool-arg a=5 \
  --tool-arg b=10
```

### Development Mode

```bash
# FastMCP dev mode with auto-reload
fastmcp run server.py --reload

# MCP SDK dev mode
uv run mcp dev server.py
```

---

## Connecting to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

Or use the MCP CLI:

```bash
uv run mcp install server.py
```

---

## Connecting to Claude Code

```bash
# Add via CLI
claude mcp add --transport stdio my-server -- python /absolute/path/to/server.py

# With environment variables
claude mcp add --transport stdio --env API_KEY=your-key my-server -- python server.py

# Verify
claude mcp list
claude mcp get my-server
```

---

## Best Practices for stdio Servers

1. **Never use print()**: Use stderr or Context logging for debug output
2. **Use async/await**: For I/O operations to maintain responsiveness
3. **Validate inputs**: Check all parameters before processing
4. **Handle errors gracefully**: Return meaningful error messages in tool results
5. **Use type hints**: FastMCP generates schemas from them automatically
6. **Write clear docstrings**: They become tool descriptions for the LLM
7. **Use context managers**: For resources like HTTP connections (`async with httpx.AsyncClient()`)
8. **Store secrets in env vars**: Never hardcode API keys
9. **Use absolute paths**: When referencing files, use absolute paths
10. **Test with MCP Inspector**: Visual tool for validating your server

---

## Error Handling Pattern

```python
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("robust-server")

@mcp.tool
async def safe_operation(input: str) -> dict:
    """Perform an operation with proper error handling."""
    # Input validation
    if not input.strip():
        raise ToolError("Input cannot be empty.")

    try:
        result = await perform_operation(input)
        return {"status": "success", "result": result}
    except ConnectionError as e:
        raise ToolError(f"Connection failed: {str(e)}")
    except ValueError as e:
        raise ToolError(f"Invalid input: {str(e)}")
    except Exception as e:
        # Log the full error internally
        import sys
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise ToolError("An unexpected error occurred. Check server logs.")
```

---

## Async Patterns

```python
import asyncio
import httpx

mcp = FastMCP("async-server")

@mcp.tool
async def fetch_multiple(urls: list[str]) -> list[dict]:
    """Fetch data from multiple URLs concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for url, response in zip(urls, responses):
            if isinstance(response, Exception):
                results.append({"url": url, "error": str(response)})
            else:
                results.append({
                    "url": url,
                    "status": response.status_code,
                    "data": response.json() if response.status_code == 200 else None
                })
        return results
```

---

## Process Management for Production

For production deployments, use process managers to keep servers running:

```bash
# systemd service file (/etc/systemd/system/mcp-server.service)
[Unit]
Description=MCP Server
After=network.target

[Service]
Type=simple
User=myuser
ExecStart=/usr/bin/python /path/to/server.py
Restart=always
RestartSec=5
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
```
