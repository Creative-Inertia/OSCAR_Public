# Building MCP Servers with SSE and HTTP Transport

> Sources:
> - https://atalupadhyay.wordpress.com/2025/12/09/building-sse-servers-in-mcp-with-python/
> - https://gofastmcp.com/deployment/running-server
> - https://modelcontextprotocol.info/docs/concepts/transports/

**NOTE**: SSE (Server-Sent Events) transport is being superseded by Streamable HTTP transport. SSE is still supported for backward compatibility, but HTTP transport is recommended for all new projects.

---

## SSE Fundamentals

SSE is about pushing data from server to client over one long-lived HTTP connection. The protocol uses plain HTTP with specific headers:
- `Content-Type: text/event-stream`
- `Cache-Control: no-cache`
- `Connection: keep-alive`

Event format includes optional fields:
- `event: <type>` (defaults to "message")
- `data: <payload>` (can be multi-line)
- `id: <unique-id>` (for reconnection)
- `retry: <ms>` (reconnect timeout)

Double newlines (`\n\n`) separate events.

---

## MCP SSE Handshake Flow

Two-phase protocol:

1. **SSE Connection:** Client performs GET to `/sse` endpoint, receives initial "endpoint" event with message URL and session ID
2. **Messaging:** Client POSTs JSON-RPC payloads to `/messages?session_id=abc123`

---

## Dependencies

```bash
pip install "mcp[cli]" starlette uvicorn
```

- `mcp[cli]`: Python SDK with Inspector tool
- `starlette`: Lightweight ASGI framework
- `uvicorn`: ASGI server

---

## SSE Server with FastMCP (Simplest Approach)

```python
from fastmcp import FastMCP

mcp = FastMCP("Calculator SSE Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    if a < 0 or b < 0:
        raise ValueError("Positive numbers only!")
    return a + b

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)
```

---

## SSE Server with Starlette (More Control)

### Basic Setup

```python
from starlette.applications import Starlette
from starlette.routing import Mount
from fastmcp import FastMCP

mcp = FastMCP("Calculator SSE Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

app = Starlette(
    debug=True,
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

### Full E-Commerce Example

```python
from starlette.applications import Starlette
from starlette.routing import Mount
from fastmcp import FastMCP
from typing import List

mcp = FastMCP("E-Commerce SSE Server")

PRODUCTS = {
    "electronics": [
        {"id": 1, "name": "iPhone 15", "price": 999},
        {"id": 2, "name": "MacBook Pro", "price": 1999}
    ],
    "books": [
        {"id": 3, "name": "Learn MCP with Python", "price": 49},
        {"id": 4, "name": "Async Python Mastery", "price": 59}
    ],
}

CART = []

@mcp.tool()
def list_products(category: str) -> List[dict]:
    """Retrieve products by category (electronics, books)."""
    if category.lower() not in PRODUCTS:
        raise ValueError(f"Invalid category. Options: {list(PRODUCTS.keys())}")
    return PRODUCTS[category.lower()]

@mcp.tool()
def add_to_cart(product_id: int) -> dict:
    """Add product to cart by ID."""
    for cat, prods in PRODUCTS.items():
        for prod in prods:
            if prod["id"] == product_id:
                if product_id not in CART:
                    CART.append(product_id)
                return {"message": f"Added {prod['name']} to cart.", "cart_size": len(CART)}
    raise ValueError(f"Product ID {product_id} not found.")

@mcp.tool()
def list_cart() -> List[dict]:
    """List items in cart."""
    cart_items = []
    for cart_id in CART:
        for cat, prods in PRODUCTS.items():
            for prod in prods:
                if prod["id"] == cart_id:
                    cart_items.append(prod)
    return cart_items if cart_items else [{"message": "Cart empty"}]

@mcp.resource("cart://clear")
def clear_cart():
    """Clear the shopping cart."""
    CART.clear()
    return "Cart cleared."

app = Starlette(debug=True, routes=[Mount('/', app=mcp.sse_app())])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

---

## Low-Level SSE Server (Without FastMCP)

```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from mcp import types

app = Server("my-sse-server")
sse = SseServerTransport("/messages")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="greet",
            description="Generate a greeting",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"}
                },
                "required": ["name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "greet":
        return [types.TextContent(type="text", text=f"Hello, {arguments['name']}!")]
    raise ValueError(f"Unknown tool: {name}")

async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)

# Run: uvicorn server:starlette_app --host 0.0.0.0 --port 3000
```

---

## Running the Server

```bash
# With uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 3000 --reload

# With FastMCP CLI
fastmcp run server.py --transport sse --port 3000

# The --reload flag enables development mode with hot-reloading
# NOTE: SSE transport does NOT support auto-reload with FastMCP CLI
```

---

## Streamable HTTP Transport (Recommended Alternative)

For new projects, use HTTP transport instead of SSE:

```python
from fastmcp import FastMCP

mcp = FastMCP(name="MyServer")

@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
```

Server becomes accessible at `http://localhost:8000/mcp`.

### HTTP Transport Advantages Over SSE

- Bidirectional communication (SSE is unidirectional)
- Multiple concurrent clients
- Better for production deployments
- No browser connection limits
- Supports binary data natively
- Auto-reload supported with FastMCP CLI

### Custom Routes with HTTP Transport

```python
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

mcp = FastMCP("MyServer")

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.tool
def process(data: str) -> str:
    return f"Processed: {data}"

if __name__ == "__main__":
    mcp.run(transport="http")
```

Custom routes are available at the root domain while the MCP endpoint is at `/mcp/`.

---

## Testing SSE/HTTP Servers

### 1. MCP Inspector (Visual)

```bash
npx @modelcontextprotocol/inspector
```

Configuration:
- Transport Type: SSE (or HTTP)
- URL: `http://localhost:3000/sse` (or `http://localhost:8000/mcp`)

### 2. Inspector CLI

```bash
npx @modelcontextprotocol/inspector --cli http://localhost:3000/sse \
  --method tools/call \
  --tool-name add \
  --tool-arg a=5 \
  --tool-arg b=10
```

### 3. cURL Testing (SSE - Three Steps)

**Step 1 - Connect and obtain session:**

```bash
export MCP_SERVER="http://localhost:3000"
curl -N -H "Accept: text/event-stream" "${MCP_SERVER}/sse"
# Outputs: event: endpoint
# data: /messages?session_id=abc123
```

**Step 2 - Initialize (new terminal):**

```bash
export MCP_ENDPOINT="http://localhost:3000/messages?session_id=abc123"
curl -X POST "${MCP_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}'
```

**Step 3 - List tools:**

```bash
curl -X POST "${MCP_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

**Step 4 - Call a tool:**

```bash
curl -X POST "${MCP_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"add","arguments":{"a":5,"b":10}}}'
```

Responses stream back to the SSE connection terminal:

```
event: message
data: {"jsonrpc": "2.0", "id": 1, "result": {...}}
```

---

## Connecting to Claude Code

### SSE Transport

```bash
claude mcp add --transport sse my-server http://localhost:3000/sse

# With authentication header
claude mcp add --transport sse my-server http://localhost:3000/sse \
  --header "X-API-Key: your-key-here"
```

### HTTP Transport

```bash
claude mcp add --transport http my-server http://localhost:8000/mcp

# With Bearer token
claude mcp add --transport http my-server http://localhost:8000/mcp \
  --header "Authorization: Bearer your-token"
```

---

## ASGI Application Pattern

For integrating with existing ASGI applications:

```python
from fastmcp import FastMCP

def create_app():
    mcp = FastMCP("MyServer")

    @mcp.tool
    def process(data: str) -> str:
        return f"Processed: {data}"

    return mcp.http_app()

app = create_app()
# Run: uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## Async Run Pattern

For use within async contexts:

```python
from fastmcp import FastMCP
import asyncio

mcp = FastMCP(name="MyServer")

@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

async def main():
    await mcp.run_async(transport="http", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
```

**IMPORTANT**: `run()` cannot be called from inside an async function because it creates its own event loop. Use `run_async()` instead.

---

## Security Considerations

- **CORS**: Set `Access-Control-Allow-Origin` headers for cross-origin requests
- **Authentication**: Use JWT tokens in headers for both `/sse` and `/messages` endpoints
- **Rate Limiting**: Implement rate limiting on long-lived connections
- **Heartbeats**: Send empty events every ~30 seconds to prevent timeout disconnections
- **TLS**: Use HTTPS in production

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Verify `pip install mcp[cli]` completed |
| No stream data | Check firewall/port accessibility |
| 404 responses | Validate endpoint paths |
| JSON errors | Validate request payload syntax |
| Connection drops | Implement heartbeats |
| Debug logging | Run with `uvicorn --log-level debug` |

---

## Transport Comparison

| Feature | SSE | HTTP (Streamable) |
|---------|-----|-------------------|
| Direction | Server->Client streaming only | Bidirectional |
| Client->Server | Separate POST endpoint | Same connection |
| Binary data | Base64 required | Native support |
| Auto-reload | Not supported | Supported |
| Browser limits | ~6 per domain (HTTP/1.1) | None |
| Recommended | Legacy/backward compat | New projects |
