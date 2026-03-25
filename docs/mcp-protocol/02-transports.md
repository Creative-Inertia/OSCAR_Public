# MCP Transports

> Source: https://modelcontextprotocol.info/docs/concepts/transports/

Transports in the Model Context Protocol (MCP) provide the foundation for communication between clients and servers. The transport layer converts MCP protocol messages into JSON-RPC 2.0 format for transmission and converts received JSON-RPC messages back into MCP protocol messages.

---

## Message Format (JSON-RPC 2.0)

MCP uses JSON-RPC 2.0 as its wire format with three message types:

### Requests

```json
{
  "jsonrpc": "2.0",
  "id": "number | string",
  "method": "string",
  "params": "object (optional)"
}
```

### Responses

```json
{
  "jsonrpc": "2.0",
  "id": "number | string",
  "result": "object (optional)",
  "error": {
    "code": "number",
    "message": "string",
    "data": "unknown (optional)"
  }
}
```

### Notifications (one-way, no response expected)

```json
{
  "jsonrpc": "2.0",
  "method": "string",
  "params": "object (optional)"
}
```

---

## Transport Types

### 1. Standard Input/Output (stdio)

The stdio transport enables communication through standard input and output streams.

**Use Cases:**
- Building command-line tools
- Implementing local integrations
- Simple process communication
- Working with shell scripts
- Claude Desktop and Claude Code local integrations

**How it works:** The client spawns the server as a subprocess. Messages are written to the server's stdin and read from its stdout. Each message is a JSON-RPC payload terminated by a newline.

**Python Server Implementation:**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("example-server")

async with stdio_server() as streams:
    await app.run(
        streams[0],
        streams[1],
        app.create_initialization_options()
    )
```

**Python Client Implementation:**

```python
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

params = StdioServerParameters(
    command="./server",
    args=["--option", "value"]
)

async with stdio_client(params) as streams:
    async with ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
```

**TypeScript Server Implementation:**

```typescript
const server = new Server({
  name: "example-server",
  version: "1.0.0"
}, {
  capabilities: {}
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

**TypeScript Client Implementation:**

```typescript
const client = new Client({
  name: "example-client",
  version: "1.0.0"
}, {
  capabilities: {}
});

const transport = new StdioClientTransport({
  command: "./server",
  args: ["--option", "value"]
});
await client.connect(transport);
```

**Key characteristics:**
- Client spawns a new server process for each session
- Messages sent via stdin/stdout
- stderr is available for logging (do NOT use print() for debugging)
- Process lifecycle managed by the client
- Most commonly used transport for local development

---

### 2. Server-Sent Events (SSE)

SSE transport enables server-to-client streaming with HTTP POST requests for client-to-server communication.

**NOTE: SSE is being superseded by Streamable HTTP transport. Use HTTP transport instead of SSE for all new projects.**

**Use Cases:**
- Server-to-client streaming scenarios
- Restricted network environments
- Simple update implementations
- Legacy compatibility

**How it works (Two-Phase Protocol):**
1. **SSE Connection:** Client performs GET to `/sse` endpoint, receives initial "endpoint" event with message URL and session ID
2. **Messaging:** Client POSTs JSON-RPC payloads to `/messages?session_id=abc123`

**Python Server Implementation:**

```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

app = Server("example-server")
sse = SseServerTransport("/messages")

async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as streams:
        await app.run(streams[0], streams[1],
                      app.create_initialization_options())

async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages,
              methods=["POST"]),
    ]
)
```

**Python Client Implementation:**

```python
from mcp.client.sse import sse_client
from mcp import ClientSession

async with sse_client("http://localhost:8000/sse") as streams:
    async with ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
```

**TypeScript Server Implementation:**

```typescript
import express from "express";

const app = express();
const server = new Server({
  name: "example-server",
  version: "1.0.0"
}, {
  capabilities: {}
});

let transport: SSEServerTransport | null = null;

app.get("/sse", (req, res) => {
  transport = new SSEServerTransport("/messages", res);
  server.connect(transport);
});

app.post("/messages", (req, res) => {
  if (transport) {
    transport.handlePostMessage(req, res);
  }
});

app.listen(3000);
```

**TypeScript Client Implementation:**

```typescript
const client = new Client({
  name: "example-client",
  version: "1.0.0"
}, {
  capabilities: {}
});

const transport = new SSEClientTransport(
  new URL("http://localhost:3000/sse")
);
await client.connect(transport);
```

**Key characteristics:**
- Unidirectional streaming (server -> client via SSE, client -> server via POST)
- Two endpoints: `/sse` (GET) and `/messages` (POST)
- Session management via session IDs
- HTTP-based, firewall-friendly
- Text-only (binary data requires base64 encoding)
- Browser connection limit: ~6 concurrent per domain under HTTP/1.1

---

### 3. Streamable HTTP (Recommended for Remote)

The newer transport that supersedes SSE. Uses standard HTTP for both directions.

**Python Implementation with FastMCP:**

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

---

## Custom Transport Interface

### Python

```python
@contextmanager
async def create_transport(
    read_stream: MemoryObjectReceiveStream[JSONRPCMessage | Exception],
    write_stream: MemoryObjectSendStream[JSONRPCMessage]
):
    async with anyio.create_task_group() as tg:
        try:
            tg.start_soon(lambda: process_messages(read_stream))
            async with write_stream:
                yield write_stream
        except Exception as exc:
            raise exc
        finally:
            tg.cancel_scope.cancel()
            await write_stream.aclose()
            await read_stream.aclose()
```

Note: "While MCP Servers are often implemented with asyncio, implement low-level interfaces like transports with `anyio` for wider compatibility."

### TypeScript

```typescript
interface Transport {
  start(): Promise<void>;
  send(message: JSONRPCMessage): Promise<void>;
  close(): Promise<void>;
  onclose?: () => void;
  onerror?: (error: Error) => void;
  onmessage?: (message: JSONRPCMessage) => void;
}
```

---

## Error Handling

Transport implementations should handle:

1. Connection errors
2. Message parsing errors
3. Protocol errors
4. Network timeouts
5. Resource cleanup

**Python Error Handling Example:**

```python
@contextmanager
async def example_transport(scope, receive, send):
    try:
        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        async def message_handler():
            try:
                async with read_stream_writer:
                    pass  # Message handling logic
            except Exception as exc:
                logger.error(f"Failed to handle message: {exc}")
                raise exc

        async with anyio.create_task_group() as tg:
            tg.start_soon(message_handler)
            try:
                yield read_stream, write_stream
            except Exception as exc:
                logger.error(f"Transport error: {exc}")
                raise exc
            finally:
                tg.cancel_scope.cancel()
                await write_stream.aclose()
                await read_stream.aclose()
    except Exception as exc:
        logger.error(f"Failed to initialize transport: {exc}")
        raise exc
```

---

## Best Practices

1. Handle connection lifecycle properly
2. Implement proper error handling
3. Clean up resources on connection close
4. Use appropriate timeouts
5. Validate messages before sending
6. Log transport events for debugging
7. Implement reconnection logic when appropriate
8. Handle backpressure in message queues
9. Monitor connection health
10. Implement proper security measures

---

## Security Considerations

### Authentication and Authorization
- Implement proper authentication mechanisms
- Validate client credentials
- Use secure token handling
- Implement authorization checks

### Data Security
- Use TLS for network transport
- Encrypt sensitive data
- Validate message integrity
- Implement message size limits
- Sanitize input data

### Network Security
- Implement rate limiting
- Use appropriate timeouts
- Handle denial of service scenarios
- Monitor for unusual patterns
- Implement proper firewall rules

---

## Transport Comparison

| Feature | stdio | SSE | Streamable HTTP |
|---------|-------|-----|-----------------|
| Communication | stdin/stdout | HTTP GET + POST | HTTP |
| Direction | Bidirectional | Server->Client streaming, Client->Server POST | Bidirectional |
| Deployment | Local process | Network service | Network service |
| Multiple clients | No (1:1) | Yes | Yes |
| Recommended for | Local dev, CLI tools | Legacy/backward compat | Production remote |
| Firewall-friendly | N/A (local) | Yes | Yes |
| Binary support | Yes | Text only (base64) | Yes |
