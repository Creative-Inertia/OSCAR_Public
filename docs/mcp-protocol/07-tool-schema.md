# MCP Tool Schema Reference

> Sources:
> - https://modelcontextprotocol.io/specification/2025-11-25/server/tools
> - https://modelcontextprotocol.info/docs/concepts/tools/

This document covers how MCP tools are defined, the JSON schema format for tool parameters, how results are returned, and error handling.

---

## Protocol Version

Protocol Revision: 2025-11-25

---

## Tool Definition Structure

Every MCP tool definition contains these fields:

```json
{
  "name": "string",
  "title": "string (optional)",
  "description": "string",
  "icons": [{"src": "url", "mimeType": "string", "sizes": ["48x48"]}],
  "inputSchema": { ... },
  "outputSchema": { ... },
  "annotations": { ... }
}
```

### Field Details

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier for the tool (1-128 chars) |
| `title` | No | Human-readable display name |
| `description` | No | Human-readable description of functionality |
| `icons` | No | Array of icons for display in UIs |
| `inputSchema` | Yes | JSON Schema defining expected parameters |
| `outputSchema` | No | JSON Schema defining expected output structure |
| `annotations` | No | Properties describing tool behavior |

### Tool Name Rules

- Should be 1-128 characters
- Case-sensitive
- Allowed characters: `A-Z`, `a-z`, `0-9`, `_`, `-`, `.`
- Should NOT contain spaces, commas, or special characters
- Must be unique within a server
- Examples: `getUser`, `DATA_EXPORT_v2`, `admin.tools.list`

---

## inputSchema (JSON Schema)

The `inputSchema` defines what parameters the tool accepts using JSON Schema format.

### Basic Schema

```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or zip code"
      }
    },
    "required": ["location"]
  }
}
```

### Schema with Multiple Parameter Types

```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results",
        "default": 10
      },
      "include_archived": {
        "type": "boolean",
        "description": "Whether to include archived items",
        "default": false
      },
      "tags": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Filter by tags"
      },
      "filters": {
        "type": "object",
        "properties": {
          "date_from": { "type": "string", "format": "date" },
          "date_to": { "type": "string", "format": "date" }
        },
        "description": "Date range filters"
      }
    },
    "required": ["query"]
  }
}
```

### Tool with No Parameters

```json
{
  "name": "get_current_time",
  "description": "Returns the current server time",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false
  }
}
```

Recommended approach: `{ "type": "object", "additionalProperties": false }` -- explicitly accepts only empty objects.

### JSON Schema Version

- Defaults to 2020-12 if no `$schema` field is present
- Can explicitly specify draft-07:

```json
{
  "inputSchema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "a": { "type": "number" },
      "b": { "type": "number" }
    },
    "required": ["a", "b"]
  }
}
```

### Best Practice: Keep Schemas Flat

While JSON Schema supports deep nesting and complex validation (`oneOf`, `allOf`), keep tool schemas as flat as possible. Deeply nested structures increase token count and cognitive load for the LLM, leading to higher latency or parsing errors.

---

## outputSchema

Optional JSON Schema defining expected output structure:

```json
{
  "name": "get_weather_data",
  "description": "Get current weather data for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": { "type": "string", "description": "City name or zip code" }
    },
    "required": ["location"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "temperature": { "type": "number", "description": "Temperature in celsius" },
      "conditions": { "type": "string", "description": "Weather conditions" },
      "humidity": { "type": "number", "description": "Humidity percentage" }
    },
    "required": ["temperature", "conditions", "humidity"]
  }
}
```

Rules:
- Servers MUST provide structured results that conform to this schema
- Clients SHOULD validate structured results against this schema
- Follows the same JSON Schema usage guidelines as inputSchema

---

## Annotations

Annotations describe tool behavior for clients:

```json
{
  "annotations": {
    "title": "Weather Lookup",
    "readOnlyHint": true,
    "destructiveHint": false,
    "idempotentHint": true,
    "openWorldHint": true
  }
}
```

| Annotation | Type | Description |
|------------|------|-------------|
| `title` | string | Display name for UIs |
| `readOnlyHint` | boolean | Tool only reads, doesn't modify state |
| `destructiveHint` | boolean | Changes are permanent/irreversible |
| `idempotentHint` | boolean | Repeated calls produce identical results |
| `openWorldHint` | boolean | Tool interacts with external systems |

**Security note**: Clients MUST consider annotations untrusted unless from trusted servers.

---

## Protocol Messages

### Server Capability Declaration

Servers that support tools MUST declare the `tools` capability:

```json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    }
  }
}
```

`listChanged` indicates whether the server will emit notifications when the tool list changes.

### tools/list -- Listing Available Tools

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "title": "Weather Information Provider",
        "description": "Get current weather information for a location",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name or zip code"
            }
          },
          "required": ["location"]
        }
      }
    ],
    "nextCursor": "next-page-cursor"
  }
}
```

Supports pagination via `cursor`/`nextCursor`.

### tools/call -- Invoking a Tool

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "location": "New York"
    }
  }
}
```

**Response (success):**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Current weather in New York:\nTemperature: 72F\nConditions: Partly cloudy"
      }
    ],
    "isError": false
  }
}
```

**Response with structured content:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"temperature\": 22.5, \"conditions\": \"Partly cloudy\", \"humidity\": 65}"
      }
    ],
    "structuredContent": {
      "temperature": 22.5,
      "conditions": "Partly cloudy",
      "humidity": 65
    }
  }
}
```

### notifications/tools/list_changed -- Tool List Changed

Servers that declared `listChanged` capability SHOULD send this notification when tools change:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

---

## Tool Result Content Types

Tool results can contain multiple content items of different types in the `content` array.

### TextContent

```json
{
  "type": "text",
  "text": "Tool result text"
}
```

### ImageContent

```json
{
  "type": "image",
  "data": "base64-encoded-data",
  "mimeType": "image/png",
  "annotations": {
    "audience": ["user"],
    "priority": 0.9
  }
}
```

### AudioContent

```json
{
  "type": "audio",
  "data": "base64-encoded-audio-data",
  "mimeType": "audio/wav"
}
```

### ResourceLink

Links to resources that can be fetched separately:

```json
{
  "type": "resource_link",
  "uri": "file:///project/src/main.rs",
  "name": "main.rs",
  "description": "Primary application entry point",
  "mimeType": "text/x-rust"
}
```

### EmbeddedResource

Resources embedded directly in the response:

```json
{
  "type": "resource",
  "resource": {
    "uri": "file:///project/src/main.rs",
    "mimeType": "text/x-rust",
    "text": "fn main() {\n    println!(\"Hello world!\");\n}",
    "annotations": {
      "audience": ["user", "assistant"],
      "priority": 0.7,
      "lastModified": "2025-05-03T14:30:00Z"
    }
  }
}
```

### Content Annotations

All content types support optional annotations:

| Annotation | Type | Description |
|------------|------|-------------|
| `audience` | `string[]` | Who should see this: `"user"`, `"assistant"`, or both |
| `priority` | `number` | Relative importance (0.0 to 1.0) |
| `lastModified` | `string` | ISO 8601 timestamp |

---

## Error Handling

MCP uses two error reporting mechanisms:

### 1. Protocol Errors (JSON-RPC errors)

For issues with the request itself:
- Unknown tools
- Malformed requests
- Server errors

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32602,
    "message": "Unknown tool: invalid_tool_name"
  }
}
```

Standard JSON-RPC error codes:
- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

### 2. Tool Execution Errors (in result with isError: true)

For errors during tool execution that the LLM can potentially handle:
- API failures
- Input validation errors
- Business logic errors

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Invalid departure date: must be in the future. Current date is 08/08/2025."
      }
    ],
    "isError": true
  }
}
```

**Key principle**: Tool execution errors contain actionable feedback that LLMs can use to self-correct and retry. Protocol errors indicate structural issues that models are less likely to fix.

- Clients SHOULD provide tool execution errors to LLMs for self-correction
- Clients MAY provide protocol errors to LLMs (less likely to enable recovery)

---

## Python Implementation Examples

### Low-Level (mcp.server)

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

### Error Handling in Low-Level Server

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        result = perform_operation(arguments)
        return [types.TextContent(type="text", text=f"Success: {result}")]
    except ValueError as e:
        # Return as tool execution error (LLM can see and handle)
        return types.CallToolResult(
            isError=True,
            content=[types.TextContent(type="text", text=f"Error: {str(e)}")]
        )
```

### FastMCP (High-Level)

```python
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("example-server")

@mcp.tool
def calculate_sum(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ToolError("Division by zero is not allowed.")
    return a / b
```

FastMCP automatically:
- Generates the `inputSchema` from type annotations
- Generates `outputSchema` from return type annotations
- Converts `ToolError` exceptions to `isError: true` responses
- Converts return values to appropriate content types

---

## TypeScript Implementation Example

```typescript
const server = new Server({
  name: "example-server",
  version: "1.0.0"
}, {
  capabilities: { tools: {} }
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [{
      name: "calculate_sum",
      description: "Add two numbers together",
      inputSchema: {
        type: "object",
        properties: {
          a: { type: "number" },
          b: { type: "number" }
        },
        required: ["a", "b"]
      }
    }]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "calculate_sum") {
    const { a, b } = request.params.arguments;
    return { toolResult: a + b };
  }
  throw new Error("Tool not found");
});
```

---

## Common Schema Patterns

### String with Enum

```json
{
  "type": "string",
  "enum": ["ascending", "descending"],
  "description": "Sort order"
}
```

### Array of Objects

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "key": { "type": "string" },
      "value": { "type": "string" }
    },
    "required": ["key", "value"]
  }
}
```

### Optional with Default

```json
{
  "type": "integer",
  "description": "Page number",
  "default": 1,
  "minimum": 1
}
```

### String with Format

```json
{
  "type": "string",
  "format": "date-time",
  "description": "ISO 8601 datetime"
}
```

### Nested Object

```json
{
  "type": "object",
  "properties": {
    "location": {
      "type": "object",
      "properties": {
        "lat": { "type": "number" },
        "lon": { "type": "number" }
      },
      "required": ["lat", "lon"]
    }
  }
}
```

---

## Security Requirements

### Servers MUST:
- Validate all tool inputs against the schema
- Implement proper access controls
- Rate limit tool invocations
- Sanitize tool outputs

### Clients SHOULD:
- Prompt for user confirmation on sensitive operations
- Show tool inputs to user before calling (prevent data exfiltration)
- Validate tool results before passing to LLM
- Implement timeouts for tool calls
- Log tool usage for audit purposes

---

## Message Flow Diagram

```
Discovery:
  Client -> Server: tools/list
  Server -> Client: List of tools

Tool Selection:
  LLM -> Client: Select tool to use

Invocation:
  Client -> Server: tools/call
  Server -> Client: Tool result
  Client -> LLM: Process result

Updates:
  Server -> Client: notifications/tools/list_changed
  Client -> Server: tools/list
  Server -> Client: Updated tools
```

---

## Best Practices Summary

1. **Clear names and descriptions**: Help the LLM understand when to use each tool
2. **Flat schemas**: Avoid deep nesting to reduce LLM confusion
3. **Required vs optional**: Mark critical params as required; provide defaults for optional ones
4. **Descriptions on every property**: Help the LLM provide correct values
5. **Return tool errors in result**: Use `isError: true`, not protocol errors, for recoverable issues
6. **Keep operations atomic**: Each tool should do one thing well
7. **Include examples in descriptions**: Show the LLM what valid input looks like
8. **Validate all inputs**: Never trust LLM-provided arguments
9. **Implement timeouts**: Prevent hanging tool calls
10. **Log tool usage**: For debugging and monitoring
