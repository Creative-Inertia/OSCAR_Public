# MCP Protocol Documentation Index

Documentation package for building a custom MCP (Model Context Protocol) server in Python.

---

## Documents

### 01 - FastMCP Tutorial
**File:** `01-fastmcp-tutorial.md`
Complete guide to creating MCP servers with FastMCP, the high-level Python framework. Covers:
- Installation and server setup
- Tool registration with `@mcp.tool` decorator (all parameters, type annotations, async/sync, error handling, timeouts, return types, structured output, dependency injection)
- Resource registration with `@mcp.resource` (static, templates, wildcards, query params, resource classes)
- Prompt registration with `@mcp.prompt` (messages, PromptResult, async)
- Context object (`Context`) for logging, progress, sampling, session state
- Component visibility and dynamic updates
- Complete server template with all features

### 02 - MCP Transports
**File:** `02-transports.md`
How MCP clients and servers communicate. Covers:
- JSON-RPC 2.0 message format (requests, responses, notifications)
- stdio transport (stdin/stdout, local process)
- SSE transport (Server-Sent Events, HTTP-based)
- Streamable HTTP transport (recommended for remote)
- Custom transport interface (Python and TypeScript)
- Error handling, security, and best practices
- Transport comparison table

### 03 - Python SDK Reference
**File:** `03-python-sdk.md`
The official `mcp` Python SDK. Covers:
- Installation (`pip install "mcp[cli]"`)
- FastMCP (high-level) vs Low-Level Server approaches
- Running with different transports (stdio, SSE, HTTP, ASGI)
- Core types (`mcp.types`): Tool, TextContent, ImageContent, Resource, Prompt
- Low-level server handlers (`@app.list_tools()`, `@app.call_tool()`, etc.)
- Client usage (`ClientSession`, `stdio_client`, `sse_client`)
- Context object, lifespan management, structured output
- FastMCP CLI commands

### 04 - stdio Transport Guide
**File:** `04-stdio-guide.md`
Building MCP servers with stdio transport (the default). Covers:
- How stdio works (process spawning, stdin/stdout messaging)
- Project setup (dependencies, directory structure)
- Basic and complex server examples
- Debugging (stderr, Context logging, MCP Inspector)
- Connecting to Claude Desktop and Claude Code
- Error handling patterns, async patterns
- Process management for production (systemd)

### 05 - SSE and HTTP Transport Guide
**File:** `05-sse-guide.md`
Building network-accessible MCP servers. Covers:
- SSE fundamentals and MCP SSE handshake flow
- FastMCP SSE server (simple and Starlette-based)
- Low-level SSE server without FastMCP
- Streamable HTTP transport (recommended alternative)
- Custom routes with HTTP transport
- Testing with MCP Inspector and cURL
- Connecting to Claude Code (SSE and HTTP)
- ASGI application pattern
- Security (CORS, auth, rate limiting, heartbeats)

### 06 - Claude Code MCP Configuration
**File:** `06-claude-code-mcp-config.md`
How to configure MCP servers in Claude Code and Claude Desktop. Covers:
- CLI commands (`claude mcp add`, `add-json`, `list`, `get`, `remove`)
- All transport types (HTTP, SSE, stdio) with examples
- Configuration file locations and formats
- `.mcp.json` project-scoped config (with env var expansion)
- `claude_desktop_config.json` format
- Scopes (local, project, user) and precedence
- OAuth authentication
- Plugin-provided MCP servers
- Using Claude Code as an MCP server
- Environment variables (MCP_TIMEOUT, MAX_MCP_OUTPUT_TOKENS, etc.)
- Managed MCP for enterprise (allowlists, denylists)
- Troubleshooting guide

### 07 - Tool Schema Reference
**File:** `07-tool-schema.md`
Complete specification for MCP tool definitions. Covers:
- Tool definition structure (name, title, description, inputSchema, outputSchema, annotations)
- Tool naming rules
- inputSchema (JSON Schema format, parameter types, required/optional, no-param tools)
- outputSchema for structured results
- Annotations (readOnlyHint, destructiveHint, idempotentHint, openWorldHint)
- Protocol messages (tools/list, tools/call, list_changed notification)
- Tool result content types (text, image, audio, resource_link, embedded resource)
- Content annotations (audience, priority, lastModified)
- Error handling (protocol errors vs tool execution errors, isError flag)
- Python and TypeScript implementation examples
- Common schema patterns (enum, array, nested, defaults)
- Security requirements and best practices

---

## Quick Start: Build a Minimal MCP Server

```python
from fastmcp import FastMCP

mcp = FastMCP(name="my-server")

@mcp.tool
def hello(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
```

Install: `pip install fastmcp`

Connect to Claude Code: `claude mcp add --transport stdio my-server -- python /path/to/server.py`

---

## Key References

| Resource | URL |
|----------|-----|
| FastMCP Docs | https://gofastmcp.com/ |
| MCP Specification | https://modelcontextprotocol.io/specification/2025-11-25 |
| Python SDK GitHub | https://github.com/modelcontextprotocol/python-sdk |
| Python SDK Docs | https://modelcontextprotocol.github.io/python-sdk/ |
| Claude Code MCP Docs | https://code.claude.com/docs/en/mcp |
| MCP Inspector | `npx @modelcontextprotocol/inspector` |
