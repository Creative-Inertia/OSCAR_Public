"""
MCP Server for Fusion 360 control.
Exposes three tools: fusion_api, fusion_python, fusion_inspect.
Communicates with Fusion via HTTP through the fusion_bridge add-in.
"""

from mcp.server.fastmcp import FastMCP
import json
import os
import sys

# Import the HTTP client
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from fusion_client import FusionClient

# -- Initialize --

mcp = FastMCP("fusion-360-secure")

# Load configuration
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

client = FusionClient(
    host=config.get('host', '127.0.0.1'),
    port=config.get('port', 45876),
)


# -- Tools --

@mcp.tool(
    name="fusion_api",
    description="""Execute a Fusion 360 API call via dotted path notation.

HOW IT WORKS:
  You provide a dotted path like 'rootComponent.sketches.add' and the bridge
  resolves it step by step against the live Fusion API, then calls the final
  method with your arguments.

AVAILABLE ROOTS:
  - app: The Fusion Application object
  - ui: The UserInterface object
  - design: The active Design (cast from activeProduct)
  - rootComponent: The root component of the active design
  - xyPlane: XY construction plane shortcut
  - xzPlane: XZ construction plane shortcut
  - yzPlane: YZ construction plane shortcut

REFERENCING STORED OBJECTS:
  Use store_as to save a result, then reference it later with $ prefix.
  In api_path: "$sketch1.sketchCurves.sketchLines"
  In args: ["$xyPlane", "$point1"]

ADSK MODULE ACCESS:
  Use 'adsk.core.Point3D.create' or 'adsk.core.ValueInput.createByReal' etc.

EXAMPLES:
  Create a sketch:
    api_path="rootComponent.sketches.add", args=["$xyPlane"], store_as="sketch1"

  Create a Point3D:
    api_path="adsk.core.Point3D.create", args=[0, 0, 0], store_as="origin"

  Add a line:
    api_path="$sketch1.sketchCurves.sketchLines.addByTwoPoints", args=["$p1", "$p2"]

  Get a profile for extrusion:
    api_path="$sketch1.profiles.item", args=[0], store_as="profile1"

  Create a value input:
    api_path="adsk.core.ValueInput.createByReal", args=[2.0], store_as="dist"
"""
)
async def fusion_api(
    api_path: str,
    args: list = None,
    kwargs: dict = None,
    store_as: str = None
) -> str:
    """Execute a Fusion 360 API call via dotted path."""
    return client.call({
        "operation": "api_call",
        "api_path": api_path,
        "args": args or [],
        "kwargs": kwargs or {},
        "store_as": store_as
    })


@mcp.tool(
    name="fusion_python",
    description="""Execute Python code directly inside Fusion 360's runtime.

Use this for complex operations that are easier as a code block than
a sequence of individual API calls. Particularly useful for:
  - Loops (iterating over edges, faces, bodies)
  - Conditional logic
  - Complex geometry calculations
  - Operations that need intermediate variables

PRE-INJECTED VARIABLES:
  app, ui, design, rootComponent, xyPlane, xzPlane, yzPlane
  adsk (module), json (module)
  All objects previously saved with store_as (by their names, no $ prefix needed)
  store(name, obj) -- function to save objects for later $name references

OUTPUT:
  Use print() to return information. Output is captured and returned.
  If no print() calls are made, returns "Executed successfully".

EXAMPLE:
  code=\"\"\"
  sketch = rootComponent.sketches.add(xyPlane)
  lines = sketch.sketchCurves.sketchLines
  p0 = adsk.core.Point3D.create(0, 0, 0)
  p1 = adsk.core.Point3D.create(10, 0, 0)
  p2 = adsk.core.Point3D.create(10, 5, 0)
  p3 = adsk.core.Point3D.create(0, 5, 0)
  lines.addByTwoPoints(p0, p1)
  lines.addByTwoPoints(p1, p2)
  lines.addByTwoPoints(p2, p3)
  lines.addByTwoPoints(p3, p0)
  store('rect_sketch', sketch)
  print(f'Created rectangle sketch with {sketch.profiles.count} profile(s)')
  \"\"\"
"""
)
async def fusion_python(code: str) -> str:
    """Execute Python code in Fusion 360's runtime."""
    return client.call({
        "operation": "python_exec",
        "code": code
    })


@mcp.tool(
    name="fusion_inspect",
    description="""Inspect a Fusion 360 object to discover its methods and properties.

Use this to explore the API when you are unsure what methods or properties
are available on an object. Returns a list of all public members with their
types and current values.

TARGETS:
  - Root names: 'rootComponent', 'design', 'app', 'ui'
  - Stored objects: '$sketch1', '$body1'
  - Dotted paths: 'rootComponent.sketches', '$sketch1.sketchCurves'

EXAMPLE:
  target="rootComponent" -- shows all members of the root component
  target="$sketch1" -- shows all members of a stored sketch
  target="rootComponent.features" -- shows available feature collections
"""
)
async def fusion_inspect(target: str) -> str:
    """Inspect a Fusion 360 object's methods and properties."""
    return client.call({
        "operation": "inspect",
        "target": target
    })


@mcp.tool(
    name="fusion_pin",
    description="""Pin the currently active Fusion 360 document so all subsequent
operations target it, even if the user switches tabs in the Fusion UI.

Call this BEFORE starting any multi-step modeling session. This prevents
operations from accidentally targeting a different document if the user
clicks on another tab while work is in progress.

Returns the name of the pinned document for confirmation."""
)
async def fusion_pin() -> str:
    """Pin the active document to prevent tab-switching issues."""
    return client.call({"operation": "pin_document"})


@mcp.tool(
    name="fusion_unpin",
    description="""Unpin the document, returning to default behavior where
operations target whichever document is currently active in Fusion.

Call this when you are done with a modeling session, or when the user
wants to switch to working on a different document."""
)
async def fusion_unpin() -> str:
    """Unpin the document and return to targeting the active tab."""
    return client.call({"operation": "unpin_document"})


@mcp.tool(
    name="fusion_pin_status",
    description="Check whether a document is currently pinned, and if so, which one."
)
async def fusion_pin_status() -> str:
    """Check the current document pin state."""
    return client.call({"operation": "pin_status"})


@mcp.tool(
    name="fusion_capture",
    description="""Capture the current Fusion 360 viewport as a PNG image.

Use this to visually verify your work after creating or modifying geometry.
The image is saved to a local file and the path is returned so you can
read it with the Read tool.

WHEN TO USE:
  - After completing a feature or design step, to verify it looks correct
  - When debugging geometry issues (self-intersections, misalignment)
  - Before telling the user "done" on any visual/aesthetic work
  - When the user asks "does that look right?"

Returns the file path to the captured PNG image."""
)
async def fusion_capture(width: int = 1920, height: int = 1080) -> str:
    """Capture the Fusion viewport to a PNG file for visual review."""
    return client.call({
        "operation": "capture_viewport",
        "width": width,
        "height": height
    })


@mcp.tool(
    name="fusion_ping",
    description="Check if the Fusion 360 bridge is running and reachable."
)
async def fusion_ping() -> str:
    """Health check for the Fusion bridge connection."""
    return client.ping()


# -- Entry point --

if __name__ == "__main__":
    mcp.run(transport='stdio')
