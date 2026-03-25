# MCP Python SDK Reference

> Source: https://github.com/modelcontextprotocol/python-sdk
> Documentation: https://modelcontextprotocol.github.io/python-sdk/

The official Python SDK for the Model Context Protocol, providing both a high-level FastMCP interface and a low-level server/client API.

---

## Installation

```bash
# With uv (recommended)
uv add "mcp[cli]"

# With pip
pip install "mcp[cli]"
```

The `[cli]` extra includes the MCP CLI tools for development and debugging.

---

## Development Tools

```bash
# Start the MCP Inspector for visual testing
uv run mcp dev server.py

# Install server into Claude Desktop
uv run mcp install server.py
```

---

## Two Approaches: FastMCP vs Low-Level Server

### Approach 1: FastMCP (High-Level, Recommended)

FastMCP provides a decorator-based interface. This is the recommended approach for most use cases.

```python
from fastmcp import FastMCP

mcp = FastMCP(name="Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting."""
    return f"Hello, {name}!"

@mcp.prompt()
def review_code(code: str) -> str:
    """Create a code review prompt."""
    return f"Please review this code:\n\n{code}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Approach 2: Low-Level Server (Full Protocol Control)

For cases where you need direct control over the MCP protocol:

```python
from mcp.server import Server
from mcp import types

app = Server("example-server")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="calculate_sum",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@app.call_tool()
async def call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "calculate_sum":
        a = arguments["a"]
        b = arguments["b"]
        result = a + b
        return [types.TextContent(type="text", text=str(result))]
    raise ValueError(f"Tool not found: {name}")
```

---

## Running with Different Transports

### stdio Transport (Default)

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("my-server")

# Register handlers...

async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

Or with FastMCP:

```python
mcp.run()  # stdio is default
# or explicitly:
mcp.run(transport="stdio")
```

### SSE Transport

```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

app = Server("my-server")
sse = SseServerTransport("/messages")

# Register handlers on `app`...

async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as streams:
        await app.run(streams[0], streams[1],
                      app.create_initialization_options())

async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)

# Run with uvicorn:
# uvicorn server:starlette_app --host 0.0.0.0 --port 8000
```

Or with FastMCP:

```python
mcp.run(transport="sse", host="127.0.0.1", port=8000)
```

### Streamable HTTP Transport (Recommended for Remote)

```python
mcp.run(transport="http", host="127.0.0.1", port=8000)
```

Server accessible at `http://localhost:8000/mcp`.

### ASGI Mounting

```python
from fastmcp import FastMCP

def create_app():
    mcp = FastMCP("MyServer")

    @mcp.tool
    def process(data: str) -> str:
        return f"Processed: {data}"

    return mcp.http_app()

app = create_app()
# Run with: uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## Core Types (mcp.types)

### Tool Definition

```python
from mcp import types

types.Tool(
    name="tool_name",
    description="What the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "integer", "description": "Second parameter"}
        },
        "required": ["param1"]
    }
)
```

### Content Types

```python
# Text content
types.TextContent(type="text", text="Result text")

# Image content
types.ImageContent(type="image", data="base64-encoded", mimeType="image/png")

# Embedded resource
types.EmbeddedResource(
    type="resource",
    resource=types.TextResourceContents(
        uri="file:///path",
        mimeType="text/plain",
        text="File contents"
    )
)
```

### Resource Types

```python
types.Resource(
    uri="resource://example",
    name="Example Resource",
    description="A sample resource",
    mimeType="application/json"
)

types.ResourceTemplate(
    uriTemplate="users://{user_id}/profile",
    name="User Profile",
    description="Get a user's profile"
)
```

### Prompt Types

```python
types.Prompt(
    name="code_review",
    description="Review code for issues",
    arguments=[
        types.PromptArgument(
            name="code",
            description="The code to review",
            required=True
        )
    ]
)

types.PromptMessage(
    role="user",
    content=types.TextContent(type="text", text="Review this code...")
)
```

---

## Low-Level Server Handlers

### List Tools Handler

```python
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="my_tool",
            description="Does something useful",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        )
    ]
```

### Call Tool Handler

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "my_tool":
        result = process(arguments["input"])
        return [types.TextContent(type="text", text=result)]
    raise ValueError(f"Unknown tool: {name}")
```

### List Resources Handler

```python
@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="config://app",
            name="Application Config",
            mimeType="application/json"
        )
    ]
```

### Read Resource Handler

```python
@app.read_resource()
async def read_resource(uri: str) -> list[types.TextResourceContents]:
    if uri == "config://app":
        return [types.TextResourceContents(
            uri=uri,
            mimeType="application/json",
            text='{"version": "1.0"}'
        )]
    raise ValueError(f"Unknown resource: {uri}")
```

### List Prompts Handler

```python
@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="summarize",
            description="Summarize text",
            arguments=[
                types.PromptArgument(name="text", required=True)
            ]
        )
    ]
```

### Get Prompt Handler

```python
@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    if name == "summarize":
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Summarize: {arguments['text']}"
                    )
                )
            ]
        )
    raise ValueError(f"Unknown prompt: {name}")
```

---

## Client Usage

### Creating a Client Session

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

params = StdioServerParameters(
    command="python",
    args=["server.py"]
)

async with stdio_client(params) as streams:
    async with ClientSession(streams[0], streams[1]) as session:
        await session.initialize()

        # List tools
        tools = await session.list_tools()

        # Call a tool
        result = await session.call_tool("my_tool", {"input": "hello"})

        # List resources
        resources = await session.list_resources()

        # Read a resource
        content = await session.read_resource("config://app")

        # List prompts
        prompts = await session.list_prompts()

        # Get a prompt
        prompt_result = await session.get_prompt("summarize", {"text": "..."})
```

### SSE Client

```python
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8000/sse") as streams:
    async with ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
        # Use session as above...
```

---

## Context Object (FastMCP)

When using FastMCP, inject `Context` to access MCP features:

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("demo")

@mcp.tool()
async def my_tool(input: str, ctx: Context) -> str:
    # Logging
    await ctx.info(f"Processing: {input}")
    await ctx.debug("Debug details...")
    await ctx.warning("Something concerning")
    await ctx.error("Something failed")

    # Progress reporting
    await ctx.report_progress(progress=50, total=100)

    # Read another resource
    data = await ctx.read_resource("config://app")

    # Request LLM sampling
    response = await ctx.sample("Analyze this data...")

    # Request info
    print(ctx.request_id)
    print(ctx.client_id)

    return f"Processed: {input}"
```

---

## Lifespan Management

For setup/teardown logic (database connections, etc.):

```python
from contextlib import asynccontextmanager
from fastmcp import FastMCP

@asynccontextmanager
async def lifespan(server: FastMCP):
    # Startup
    db = await connect_to_database()
    try:
        yield {"db": db}  # Available via server state
    finally:
        # Shutdown
        await db.close()

mcp = FastMCP("demo", lifespan=lifespan)

@mcp.tool()
async def query_db(sql: str, ctx: Context) -> str:
    db = ctx.fastmcp.state["db"]
    result = await db.execute(sql)
    return str(result)
```

---

## Structured Output

### With Return Type Annotations

```python
from dataclasses import dataclass

@dataclass
class WeatherData:
    temperature: float
    conditions: str
    humidity: int

@mcp.tool()
def get_weather(city: str) -> WeatherData:
    return WeatherData(temperature=72.5, conditions="Sunny", humidity=45)

# Response includes both content and structuredContent
```

### With Output Schema

```python
@mcp.tool(output_schema={
    "type": "object",
    "properties": {
        "temperature": {"type": "number"},
        "conditions": {"type": "string"}
    },
    "required": ["temperature", "conditions"]
})
def get_weather(city: str) -> dict:
    return {"temperature": 72.5, "conditions": "Sunny"}
```

---

## FastMCP CLI

```bash
# Run with default stdio transport
fastmcp run server.py

# Run with HTTP transport
fastmcp run server.py --transport http --port 8000

# With dependencies
fastmcp run server.py --with pandas --with numpy

# With auto-reload for development
fastmcp run server.py --reload

# Watch specific directories
fastmcp run server.py --reload --reload-dir ./src

# Pass arguments to server
fastmcp run server.py -- --config config.json --debug
```

The CLI automatically finds a FastMCP instance named `mcp`, `server`, or `app` in your file.

---

## Key Design Notes

- **IMPORTANT**: MCP uses stdio for communication. Anything on stdout is interpreted as protocol messages. Do NOT use `print()` for debugging. Use `stderr` or Context logging methods instead.
- Sync functions in FastMCP automatically run in thread pools to avoid blocking the event loop.
- Use `anyio` (not `asyncio`) for low-level transport implementations for wider compatibility.
- The `[cli]` install extra is required for `mcp dev` and `mcp install` commands.
