# FastMCP Tutorial: Creating an MCP Server

> Source: https://gofastmcp.com/tutorials/create-mcp-server
> Additional sources: https://gofastmcp.com/servers/tools, https://gofastmcp.com/servers/context, https://gofastmcp.com/servers/resources, https://gofastmcp.com/servers/prompts

FastMCP is a high-level Python framework that handles all MCP protocol complexities, letting you focus on writing Python functions that power your server. The philosophy: "write Python, not protocol boilerplate."

---

## Installation

```bash
pip install fastmcp
# or with CLI tools
pip install "mcp[cli]"
# or with uv
uv add "mcp[cli]"
```

---

## Step 1: Create a Server Instance

```python
from fastmcp import FastMCP

mcp = FastMCP(name="My First MCP Server")
```

The `FastMCP` class requires a `name` parameter to identify the server.

### Server Configuration Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Server name identifier |
| `strict_input_validation` | `bool` | If `True`, reject type mismatches instead of coercing (default: `False`) |
| `mask_error_details` | `bool` | If `True`, hide internal error details from clients (default: `False`) |
| `on_duplicate_tools` | `str` | How to handle duplicate tool names: `"warn"`, `"error"`, `"replace"`, `"ignore"` |
| `on_duplicate_resources` | `str` | Same options as above, for resources |
| `on_duplicate_prompts` | `str` | Same options as above, for prompts |
| `dereference_schemas` | `bool` | Dereference JSON Schema `$ref` entries for client compatibility (default: `True`) |
| `session_state_store` | `AsyncKeyValue` | Custom session state storage backend (v3.0.0+) |

---

## Step 2: Register Tools with `@mcp.tool`

Tools are the primary way to expose functionality to LLMs.

### Basic Tool

```python
@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b
```

FastMCP automatically:
- Derives tool name from function name
- Extracts description from docstring
- Generates JSON schema from type hints (`a: int, b: int`)

### Decorator Parameters

| Parameter | Type | Purpose |
|-----------|------|---------|
| `name` | `str \| None` | Custom tool name; defaults to function name |
| `description` | `str \| None` | Overrides docstring as tool description |
| `tags` | `set[str] \| None` | Categorization strings for filtering |
| `meta` | `dict[str, Any] \| None` | Custom metadata passed to clients |
| `icons` | `list[Icon] \| None` | Icon representations (v2.13.0+) |
| `annotations` | `ToolAnnotations \| dict \| None` | MCP annotation metadata |
| `timeout` | `float \| None` | Execution timeout in seconds (v3.0.0+) |
| `version` | `str \| int \| None` | Version identifier (v3.0.0+) |
| `output_schema` | `dict[str, Any] \| None` | JSON schema for outputs (v2.10.0+) |

### Tool with Full Configuration

```python
@mcp.tool(
    name="find_products",
    description="Search the product catalog with optional category filtering.",
    tags={"catalog", "search"},
    meta={"version": "1.2", "author": "product-team"}
)
def search_products_implementation(query: str, category: str | None = None) -> list[dict]:
    print(f"Searching for '{query}' in category '{category}'")
    return [{"id": 2, "name": "Another Product"}]
```

### ToolAnnotations

Annotations communicate tool behavior to clients without consuming LLM tokens:

```python
@mcp.tool(
    annotations={
        "title": "Calculate Sum",
        "readOnlyHint": True,        # Tool only reads; doesn't modify state
        "destructiveHint": False,     # Changes are NOT permanent/irreversible
        "idempotentHint": True,       # Repeated calls produce identical results
        "openWorldHint": False        # Tool does NOT interact with external systems
    }
)
def calculate_sum(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b
```

### Supported Type Annotations

| Type Category | Examples | Notes |
|--------------|----------|-------|
| Basic scalars | `int`, `float`, `str`, `bool` | Simple values |
| Binary | `bytes` | Raw strings, not auto-decoded base64 |
| Date/Time | `datetime`, `date`, `timedelta` | ISO format strings |
| Collections | `list[str]`, `dict[str, int]`, `set[int]` | Typed containers |
| Optional | `float \| None`, `Optional[float]` | May be null/omitted |
| Union | `str \| int`, `Union[str, int]` | Multiple allowed types |
| Constrained | `Literal["A", "B"]`, `Enum` | Specific values only |
| Paths | `Path` | Auto-converted from strings |
| UUIDs | `UUID` | Auto-converted from strings |
| Pydantic | `UserData` (BaseModel subclass) | Complex structured validation |

### Required vs. Optional Parameters

Parameters without defaults are required; those with defaults are optional:

```python
@mcp.tool
def search_products(
    query: str,                   # Required
    max_results: int = 10,        # Optional
    sort_by: str = "relevance",   # Optional
    category: str | None = None   # Optional, nullable
) -> list[dict]:
    """Search the product catalog."""
    ...
```

### Parameter Metadata with Annotated

Simple descriptions:

```python
from typing import Annotated

@mcp.tool
def process_image(
    image_url: Annotated[str, "URL of the image to process"],
    resize: Annotated[bool, "Whether to resize the image"] = False,
    width: Annotated[int, "Target width in pixels"] = 800
) -> dict:
    """Process an image with optional resizing."""
    ...
```

Advanced metadata with Pydantic `Field`:

```python
from typing import Annotated
from pydantic import Field

@mcp.tool
def process_image(
    image_url: Annotated[str, Field(description="URL to process")],
    width: Annotated[int, Field(description="Width in pixels", ge=1, le=2000)] = 800,
    format: Annotated[Literal["jpeg", "png", "webp"], Field(description="Output format")] = "jpeg"
) -> dict:
    """Process an image with optional resizing."""
    ...
```

### Async and Sync Tools

FastMCP supports both. Sync functions run in thread pools automatically to avoid blocking the event loop:

```python
import time

@mcp.tool
def slow_tool(x: int) -> int:
    """This sync function won't block other concurrent requests."""
    time.sleep(2)  # Runs in threadpool
    return x * 2

@mcp.tool
async def async_tool(x: int) -> int:
    """Async tools are more efficient for I/O operations."""
    # Use async I/O here
    return x * 2
```

### Error Handling

Raise standard Python exceptions or FastMCP's `ToolError`:

```python
from fastmcp.exceptions import ToolError

@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ToolError("Division by zero is not allowed.")
    return a / b
```

Enable error masking to hide internal details:

```python
mcp = FastMCP(name="SecureServer", mask_error_details=True)
# Only ToolError messages are sent to clients; other exceptions become generic messages.
```

### Tool Timeouts (v3.0.0+)

```python
@mcp.tool(timeout=30.0)
async def fetch_data(url: str) -> dict:
    """Fetch data with a 30-second timeout."""
    ...
```

### Return Values and Content Types

FastMCP automatically converts return values to MCP content:

| Return Type | MCP Content Type |
|-------------|-----------------|
| `str` | `TextContent` |
| `bytes` | Base64-encoded `BlobResourceContents` |
| `Image(path=...)` | `ImageContent` |
| `Audio(path=...)` | `AudioContent` |
| `File(path=...)` | Base64-encoded `EmbeddedResource` |
| MCP SDK blocks | Sent as-is |
| `list` of above | Each item converted |
| `None` | Empty response |
| `dict` / dataclass / Pydantic model | `TextContent` + `structuredContent` |

Media helper classes:

```python
from fastmcp.utilities.types import Image, Audio, File

@mcp.tool
def get_chart() -> Image:
    """Generate a chart image."""
    return Image(path="chart.png")

@mcp.tool
def get_audio_clip() -> Audio:
    return Audio(data=audio_bytes, format="wav")
```

### Structured Output (v2.10.0+)

Object-like returns automatically get structured content:

```python
@mcp.tool
def get_user_data(user_id: str) -> dict:
    """Get user data."""
    return {"name": "Alice", "age": 30, "active": True}

# MCP Response includes both:
# "content": [{"type": "text", "text": "{...}"}],
# "structuredContent": {"name": "Alice", "age": 30, "active": true}
```

With Pydantic models:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    email: str

@mcp.tool
def get_user_profile(user_id: str) -> Person:
    return Person(name="Alice", age=30, email="alice@example.com")
```

### ToolResult for Complete Control

```python
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

@mcp.tool
def advanced_tool() -> ToolResult:
    """Tool with full control over output."""
    return ToolResult(
        content=[TextContent(type="text", text="Human-readable summary")],
        structured_content={"data": "value", "count": 42},
        meta={"execution_time_ms": 145}
    )
```

### Dependency Injection (Hiding Parameters from LLM)

```python
from fastmcp.dependencies import Depends

def get_user_id() -> str:
    return "user_123"  # Injected at runtime

@mcp.tool
def get_user_details(user_id: str = Depends(get_user_id)) -> str:
    # user_id is injected; LLM cannot provide it
    return f"Details for {user_id}"
```

---

## Step 3: Register Resources with `@mcp.resource`

Resources provide read-only data to LLMs.

### Static Resource

```python
@mcp.resource("resource://config")
def get_config() -> dict:
    """Provides the application's configuration."""
    return {"version": "1.0", "author": "MyTeam"}
```

### Dynamic Resource Templates

```python
@mcp.resource("greetings://{name}")
def personalized_greeting(name: str) -> str:
    """Generates a personalized greeting for the given name."""
    return f"Hello, {name}! Welcome to the MCP server."
```

URI placeholders like `{name}` map to function parameters. Clients can request `greetings://Ford` or `greetings://Marvin`.

### Resource Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| URI (first arg) | `str` | Required. Unique identifier for the resource |
| `name` | `str` | Custom human-readable name |
| `description` | `str` | Explanation text |
| `mime_type` | `str` | Content type (e.g., `"application/json"`) |
| `tags` | `set[str]` | Categorization strings |
| `annotations` | `dict` | `readOnlyHint` and `idempotentHint` booleans |
| `meta` | `dict` | Custom metadata (v2.11.0+) |
| `version` | `str \| int` | Version identifier (v3.0.0+) |

### Resource Return Types

- `str`: Sent as `TextResourceContents` with `"text/plain"` MIME type
- `bytes`: Base64-encoded as `BlobResourceContents`
- `ResourceResult`: Explicit control with multiple content items

### Wildcard Parameters (v2.2.4+)

```python
@mcp.resource("path://{filepath*}")
def get_path_content(filepath: str) -> str:
    return f"Content at path: {filepath}"
    # Matches: path://docs/server/resources.mdx
```

### Query Parameters (v2.13.0+)

```python
@mcp.resource("data://{id}{?format}")
def get_data(id: str, format: str = "json") -> str:
    if format == "xml":
        return f"<data id='{id}' />"
    return f'{{"id": "{id}"}}'
```

### Resource Classes (Pre-defined Resources)

```python
from fastmcp.resources import FileResource, TextResource
from pathlib import Path

readme = FileResource(
    uri=f"file:///{Path('./README.md').as_posix()}",
    path=Path("./README.md"),
    name="README File",
    description="The project's README.",
    mime_type="text/markdown"
)
mcp.add_resource(readme)
```

Available classes: `TextResource`, `BinaryResource`, `FileResource`, `HttpResource`, `DirectoryResource`.

---

## Step 4: Register Prompts with `@mcp.prompt`

Prompts are reusable message templates that help LLMs generate structured responses.

### Basic Prompt

```python
@mcp.prompt
def ask_about_topic(topic: str) -> str:
    """Generates a user message asking for an explanation of a topic."""
    return f"Can you please explain the concept of '{topic}'?"
```

### Multi-Message Prompt

```python
from fastmcp.prompts import Message

@mcp.prompt
def generate_code_request(language: str, task_description: str) -> list[Message]:
    """Generates a conversation for code generation."""
    return [
        Message(f"Write a {language} function that performs the following task: {task_description}"),
        Message("I'll help you write that function.", role="assistant"),
    ]
```

### Prompt with Custom Configuration

```python
@mcp.prompt(
    name="analyze_data_request",
    description="Creates a request to analyze data with specific parameters",
    tags={"analysis", "data"},
    meta={"version": "1.1", "author": "data-team"}
)
def data_analysis_prompt(
    data_uri: str,
    analysis_type: str = "summary"
) -> str:
    return f"Please perform a '{analysis_type}' analysis on the data found at {data_uri}."
```

### PromptResult (v3.0.0+)

```python
from fastmcp.prompts import PromptResult, Message

@mcp.prompt
def code_review(code: str) -> PromptResult:
    return PromptResult(
        messages=[
            Message(f"Please review this code:\n\n```\n{code}\n```"),
            Message("I'll analyze this code for issues.", role="assistant"),
        ],
        description="Code review prompt",
        meta={"review_type": "security", "priority": "high"}
    )
```

---

## Step 5: Using the Context Object

The `Context` object provides access to MCP features within tools, resources, and prompts.

### Injecting Context

```python
from fastmcp import FastMCP, Context

@mcp.tool
async def process_data(data_uri: str, ctx: Context) -> dict:
    """Process data with progress reporting."""
    await ctx.info(f"Processing data from {data_uri}")

    # Read a resource
    resource = await ctx.read_resource(data_uri)
    data = resource[0].content if resource else ""

    # Report progress
    await ctx.report_progress(progress=50, total=100)

    # Request LLM sampling
    summary = await ctx.sample(f"Summarize this in 10 words: {data[:200]}")

    await ctx.report_progress(progress=100, total=100)
    return {"length": len(data), "summary": summary.text}
```

### All Context Methods

| Category | Methods |
|----------|---------|
| **Logging** | `ctx.debug()`, `ctx.info()`, `ctx.warning()`, `ctx.error()` |
| **Progress** | `ctx.report_progress(progress, total)` |
| **Resources** | `ctx.list_resources()`, `ctx.read_resource(uri)` |
| **Prompts** | `ctx.list_prompts()`, `ctx.get_prompt(name, args)` |
| **LLM Sampling** | `ctx.sample(message, temperature=...)` |
| **Elicitation** | `ctx.elicit(message, response_type=...)` (v2.10.0+) |
| **Session State** | `ctx.get_state(key)`, `ctx.set_state(key, value)`, `ctx.delete_state(key)` (v3.0.0+) |
| **Request Info** | `ctx.request_id`, `ctx.client_id`, `ctx.session_id`, `ctx.transport` |
| **Notifications** | `ctx.send_notification(notification)` |
| **Server Access** | `ctx.fastmcp` (the server instance) |

### Alternative Context Access (v2.2.11+)

```python
from fastmcp.server.dependencies import get_context

async def helper_function(data: list[float]) -> dict:
    ctx = get_context()  # Works in any nested call during request
    await ctx.info(f"Processing {len(data)} data points")
    return {"count": len(data)}
```

---

## Step 6: Run the Server

```python
if __name__ == "__main__":
    mcp.run()
```

This starts the server using the default stdio transport. See `04-stdio-guide.md` and `05-sse-guide.md` for transport options.

---

## Complete Server Template

```python
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from typing import Annotated
from pydantic import Field

mcp = FastMCP(name="My MCP Server")

# --- Tools ---
@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b

@mcp.tool
async def divide(
    a: Annotated[float, Field(description="Numerator")],
    b: Annotated[float, Field(description="Denominator")]
) -> float:
    """Divide a by b. Raises error on division by zero."""
    if b == 0:
        raise ToolError("Division by zero is not allowed.")
    return a / b

@mcp.tool
async def process_with_progress(items: list[str], ctx: Context) -> dict:
    """Process items with progress reporting."""
    results = []
    for i, item in enumerate(items):
        await ctx.report_progress(progress=i, total=len(items))
        await ctx.info(f"Processing item: {item}")
        results.append(item.upper())
    await ctx.report_progress(progress=len(items), total=len(items))
    return {"processed": results, "count": len(results)}

# --- Resources ---
@mcp.resource("resource://config")
def get_config() -> dict:
    """Provides the application's configuration."""
    return {"version": "1.0", "author": "MyTeam"}

@mcp.resource("greetings://{name}")
def personalized_greeting(name: str) -> str:
    """Generates a personalized greeting."""
    return f"Hello, {name}! Welcome to the MCP server."

# --- Prompts ---
@mcp.prompt
def ask_about_topic(topic: str) -> str:
    """Ask about a specific topic."""
    return f"Can you please explain the concept of '{topic}'?"

if __name__ == "__main__":
    mcp.run()
```

---

## Class-Based Tools

```python
from fastmcp import FastMCP
from fastmcp.tools import tool

class Calculator:
    def __init__(self, multiplier: int):
        self.multiplier = multiplier

    @tool()
    def multiply(self, x: int) -> int:
        """Multiply x by the instance multiplier."""
        return x * self.multiplier

calc = Calculator(multiplier=3)
mcp = FastMCP()
mcp.add_tool(calc.multiply)  # Registers with only 'x' as parameter
```

---

## Component Visibility (v3.0.0+)

Control which tools/resources/prompts are available to clients:

```python
mcp = FastMCP("MyServer")

@mcp.tool(tags={"admin"})
def admin_action() -> str:
    return "Done"

@mcp.tool(tags={"public"})
def public_action() -> str:
    return "Done"

# Disable by key or tag
mcp.disable(keys={"tool:admin_action"})
mcp.disable(tags={"admin"})

# Allowlist mode - only enable specific tags
mcp.enable(tags={"public"}, only=True)
```
