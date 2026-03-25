# Build a Secure MCP Server for Autodesk Fusion 360

## Context for Claude Code

You are building a secure Model Context Protocol (MCP) server that allows AI agents (like you, Claude) to control Autodesk Fusion 360 -- creating 3D models, modifying designs, running CAM operations, and exporting files.

This replaces an insecure third-party MCP (AuraFriday's "MCP Server for Autodesk Fusion") that has security issues including no authentication, DNS tricks, opaque binaries, disabled TLS verification, and unnecessary bundled tools. See `WHY-DISCONNECT.md` in this package for full details.

**Your job:** Build every file described below, end to end, so the system is ready to install and test.

---

## What You're Building

A two-process system that bridges Claude Code to Fusion 360's API:

### Process 1: Fusion Add-in (`fusion_bridge`)

- A Python add-in that runs INSIDE Autodesk Fusion's process
- Starts an HTTP server on a background daemon thread (bound to `127.0.0.1` only)
- Uses Fusion's CustomEvent system to safely execute API calls on the main thread
- Generates a random Bearer auth token on startup, displays it in Fusion's TEXT COMMANDS panel
- **CONSTRAINT:** Can only use Python stdlib (no pip -- Fusion bundles its own Python interpreter and you cannot install packages into it)

### Process 2: MCP Server (`fusion_mcp_server`)

- A separate Python script using FastMCP with stdio transport
- Claude Code launches this as a subprocess (configured in Claude's MCP settings)
- Receives tool calls from Claude, forwards them as HTTP requests to the Fusion add-in
- CAN use pip packages (runs in system Python, not Fusion's)

---

## Architecture Diagram

```
Claude Code ──stdio──> fusion_mcp_server/server.py (FastMCP)
                              │
                         HTTP POST to 127.0.0.1:45876
                         Authorization: Bearer <token>
                              │
                              ▼
                     Fusion Add-in (fusion_bridge)
                         BaseHTTPRequestHandler (daemon thread)
                              │
                         queue.Queue + app.fireCustomEvent()
                              │
                              ▼
                     Fusion Main Thread
                         CustomEventHandler.notify()
                         → executes Fusion API calls safely
                         → returns results via queue
```

**Data flow in plain English:**

1. Claude Code calls a tool (e.g., `fusion_api`) via stdio.
2. `server.py` receives the tool call, packages it as JSON, sends an HTTP POST to `127.0.0.1:45876` with a Bearer token.
3. The Fusion add-in's HTTP handler (running on a daemon thread) validates the token, parses the request, and puts a work item on a `queue.Queue`.
4. The handler calls `app.fireCustomEvent()` to wake the main thread.
5. Fusion's main thread fires the CustomEventHandler, which pulls the work item from the queue, executes the Fusion API call, and puts the result back on a response queue.
6. The daemon thread picks up the response and returns it as HTTP JSON.
7. `server.py` returns the result to Claude Code via stdio.

---

## Critical Technical Constraints

Read these carefully. Violating any of them will cause crashes, security holes, or broken functionality.

### 1. Fusion's Threading Model

Fusion 360's Python API is **NOT thread-safe**. All Fusion API calls must execute on the main UI thread. Your add-in's HTTP server runs on a daemon thread. If you call ANY Fusion API from the daemon thread, **Fusion will crash** -- sometimes silently, sometimes with a segfault.

**Required pattern:** Use `app.registerCustomEvent()` + a `queue.Queue` to marshal work from the daemon thread to the main thread. The daemon thread puts work on the queue and calls `app.fireCustomEvent()`. The main thread's `CustomEventHandler.notify()` pulls work off the queue and executes it.

### 2. Fusion's Bundled Python

Fusion ships its own Python interpreter (currently Python 3.11.x on most platforms). You **cannot** run `pip install` into it. The add-in must use **ONLY** Python standard library modules:

- `http.server`, `http.client`
- `threading`, `queue`
- `json`, `uuid`, `secrets`, `traceback`, `inspect`
- `socketserver`, `urllib.parse`
- `os`, `sys`, `time`, `math`

Do NOT import `requests`, `flask`, `fastapi`, `mcp`, or any third-party package in the add-in code.

### 3. Separate Process for MCP

The MCP server (`fusion_mcp_server/server.py`) runs as a completely separate Python process -- system Python, not Fusion's Python. This process CAN use pip packages. It needs `mcp[cli]` (the FastMCP library).

Claude Code launches this process via stdio transport (configured in `.claude/settings.json` or equivalent). The MCP server then makes HTTP calls to the Fusion add-in running inside Fusion.

### 4. Security Requirements (Non-Negotiable)

- HTTP server binds to `127.0.0.1` only -- never `0.0.0.0`, never any external interface
- Auth token generated via `secrets.token_urlsafe(32)` on each Fusion startup -- a new token every time
- Bearer token validation on **every single HTTP request** -- reject with 401 if missing or wrong
- No auto-updater mechanism
- No DNS tricks or external hostname resolution
- No disabled TLS verification
- No external network calls from the add-in
- No bundled opaque binaries

---

## File Structure to Create

Build exactly this structure:

```
fusion-mcp/
├── fusion_bridge/                    # Fusion add-in (copy to Fusion's AddIns folder)
│   ├── fusion_bridge.py              # Main entry point (run/stop lifecycle)
│   ├── fusion_bridge.manifest        # Fusion add-in manifest (JSON)
│   ├── bridge_server.py              # HTTP server (BaseHTTPRequestHandler)
│   └── api_executor.py              # API path resolution + Python exec + work queue
│
├── fusion_mcp_server/               # MCP server (runs in system Python)
│   ├── server.py                    # FastMCP server with stdio transport
│   ├── fusion_client.py             # HTTP client for talking to Fusion add-in
│   ├── config.json                  # Auth token + port config
│   └── requirements.txt             # mcp dependency
│
├── install.sh                       # Installation helper script
└── README.md                        # Setup instructions
```

---

## Detailed Specifications

### fusion_bridge/fusion_bridge.manifest

Fusion requires a `.manifest` file to recognize the add-in. Generate a proper UUID for the `id` field.

```json
{
    "autodeskProduct": "Fusion",
    "type": "addin",
    "id": "<generate-a-real-uuid-here>",
    "author": "OSCAR",
    "description": {
        "": "Secure MCP Bridge for AI agent control of Fusion 360"
    },
    "version": "1.0.0",
    "runOnStartup": true,
    "supportedOS": "windows|mac"
}
```

---

### fusion_bridge/fusion_bridge.py

The main add-in entry point. Fusion calls `run(context)` when the add-in starts and `stop(context)` when it shuts down.

**Must implement:**

- `run(context)`:
  1. Get the Fusion `Application` and `UserInterface` objects.
  2. Register a CustomEvent with a unique event ID string (e.g., `"FusionMCPBridgeEvent"`).
  3. Create and attach a `WorkQueueHandler` (from `api_executor`) to the custom event.
  4. Store the handler reference in a module-level `handlers` list to prevent garbage collection.
  5. Generate an auth token via `secrets.token_urlsafe(32)`.
  6. Display the token in Fusion's TEXT COMMANDS palette so the user can copy it.
  7. Start the HTTP server on a daemon thread, passing `127.0.0.1`, port `45876`, the token, and a `threading.Event()` stop signal.
  8. Log a startup confirmation to the TEXT COMMANDS palette.

- `stop(context)`:
  1. Signal the stop event to shut down the HTTP server.
  2. Unregister the custom event.
  3. Clear the handlers list.
  4. Log a shutdown message to the TEXT COMMANDS palette.

**Key implementation pattern:**

```python
import adsk.core
import adsk.fusion
import threading
import secrets
import traceback

# These must be module-level to survive garbage collection
_handlers = []
_custom_event = None
_stop_event = threading.Event()
_server_thread = None

CUSTOM_EVENT_ID = 'FusionMCPBridgeEvent'
PORT = 45876

def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Import sibling modules (Fusion add-in style)
        from . import bridge_server, api_executor

        # Register custom event for main-thread execution
        global _custom_event
        _custom_event = app.registerCustomEvent(CUSTOM_EVENT_ID)
        on_custom_event = api_executor.WorkQueueHandler(app)
        _custom_event.add(on_custom_event)
        _handlers.append(on_custom_event)

        # Generate auth token
        token = secrets.token_urlsafe(32)

        # Show token in TEXT COMMANDS palette
        text_palette = ui.palettes.itemById('TextCommands')
        if text_palette:
            text_palette.writeText('========================================')
            text_palette.writeText('  FUSION MCP BRIDGE - STARTED')
            text_palette.writeText('========================================')
            text_palette.writeText(f'Auth Token: {token}')
            text_palette.writeText('')
            text_palette.writeText('Copy this token into fusion_mcp_server/config.json')
            text_palette.writeText('========================================')

        # Start HTTP server on daemon thread
        global _server_thread, _stop_event
        _stop_event.clear()
        _server_thread = threading.Thread(
            target=bridge_server.start_server,
            args=('127.0.0.1', PORT, token, _stop_event, app),
            daemon=True
        )
        _server_thread.start()

    except:
        app = adsk.core.Application.get()
        if app:
            app.userInterface.messageBox(f'Fusion MCP Bridge failed to start:\n{traceback.format_exc()}')


def stop(context):
    try:
        global _custom_event, _stop_event, _server_thread

        # Signal server to stop
        _stop_event.set()

        # Unregister custom event
        if _custom_event:
            app = adsk.core.Application.get()
            app.unregisterCustomEvent(CUSTOM_EVENT_ID)
            _custom_event = None

        # Clear handler references
        _handlers.clear()

        # Log shutdown
        app = adsk.core.Application.get()
        if app:
            text_palette = app.userInterface.palettes.itemById('TextCommands')
            if text_palette:
                text_palette.writeText('Fusion MCP Bridge - STOPPED')

    except:
        pass
```

**Important notes:**
- Fusion add-ins use relative imports (`from . import bridge_server`) because Fusion loads the add-in folder as a package.
- Handler objects MUST be kept in a module-level list. If they are garbage collected, the custom event will silently stop working.
- The `__init__.py` file is NOT needed -- Fusion treats the add-in folder as a package based on the manifest.

---

### fusion_bridge/bridge_server.py

The HTTP server that listens for requests from the MCP server process.

**Must implement:**

- A `BridgeRequestHandler` class extending `http.server.BaseHTTPRequestHandler`.
- Token validation on every request.
- JSON parsing of POST body.
- Routing to `api_executor` functions based on the `"action"` field.
- JSON responses with proper error handling.
- Suppression of default stderr logging (override `log_message`).

**Request format (JSON POST body):**

```json
{
    "action": "api_call" | "python_exec" | "inspect",
    "api_path": "rootComponent.sketches.add",
    "args": ["$xyPlane"],
    "kwargs": {},
    "store_as": "sketch1",
    "code": "# Python code for python_exec action",
    "target": "$sketch1"
}
```

**Response format:**

```json
{
    "success": true,
    "result": "<string representation of result>",
    "type": "adsk.fusion.Sketch",
    "stored_as": "sketch1"
}
```

Or on error:

```json
{
    "success": false,
    "error": "Error message here",
    "traceback": "Full traceback string"
}
```

**Key implementation details:**

```python
import http.server
import json
import threading
import socketserver

# Reference to api_executor -- set by start_server()
_executor = None
_auth_token = None


class BridgeRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handles HTTP requests from the MCP server process."""

    def do_POST(self):
        # Validate auth token
        auth_header = self.headers.get('Authorization', '')
        if auth_header != f'Bearer {_auth_token}':
            self.send_error_response(401, 'Unauthorized: invalid or missing auth token')
            return

        # Parse JSON body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            request = json.loads(body)
        except json.JSONDecodeError as e:
            self.send_error_response(400, f'Invalid JSON: {e}')
            return

        # Route to appropriate executor function
        action = request.get('action')
        try:
            if action == 'api_call':
                result = _executor.execute_api_call(
                    api_path=request.get('api_path', ''),
                    args=request.get('args', []),
                    kwargs=request.get('kwargs', {}),
                    store_as=request.get('store_as')
                )
            elif action == 'python_exec':
                result = _executor.execute_python(
                    code=request.get('code', '')
                )
            elif action == 'inspect':
                result = _executor.inspect_object(
                    target=request.get('target', 'app')
                )
            elif action == 'health':
                result = {'success': True, 'result': 'Fusion MCP Bridge is running'}
            else:
                self.send_error_response(400, f'Unknown action: {action}')
                return

            self.send_json_response(200, result)

        except Exception as e:
            import traceback
            self.send_error_response(500, str(e), traceback.format_exc())

    def do_GET(self):
        """Health check endpoint."""
        auth_header = self.headers.get('Authorization', '')
        if auth_header != f'Bearer {_auth_token}':
            self.send_error_response(401, 'Unauthorized')
            return
        self.send_json_response(200, {'success': True, 'result': 'healthy'})

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, status_code, message, tb=None):
        response = {'success': False, 'error': message}
        if tb:
            response['traceback'] = tb
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress default stderr logging."""
        pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def start_server(host, port, token, stop_event, app):
    """Start the HTTP server. Called from daemon thread."""
    global _auth_token, _executor

    from . import api_executor
    _auth_token = token
    _executor = api_executor.ApiExecutor(app)

    server = ReusableTCPServer((host, port), BridgeRequestHandler)
    server.timeout = 1.0  # Check stop_event every second

    while not stop_event.is_set():
        server.handle_request()

    server.server_close()
```

---

### fusion_bridge/api_executor.py

The core execution engine. This is the most critical file. It handles:

1. **Work queue + CustomEvent pattern** for thread-safe Fusion API execution.
2. **API path resolution** for walking dotted paths on Fusion objects.
3. **Python code execution** with pre-injected Fusion globals.
4. **Object inspection** for API discovery.
5. **Object store** for persisting references across calls.

**Detailed specification:**

```python
import adsk.core
import adsk.fusion
import adsk.cam
import queue
import threading
import json
import traceback
import inspect
import uuid
import math

CUSTOM_EVENT_ID = 'FusionMCPBridgeEvent'


class WorkQueueHandler(adsk.core.CustomEventHandler):
    """
    Processes queued work items on Fusion's main thread.

    This handler is attached to a CustomEvent. When the daemon thread
    fires the event, Fusion calls notify() on the main thread, where
    it is safe to call Fusion API methods.
    """

    def __init__(self, app):
        super().__init__()
        self._app = app

    def notify(self, args):
        """Called on main thread when custom event fires."""
        try:
            # Process all pending work items
            while not ApiExecutor._work_queue.empty():
                try:
                    work_item = ApiExecutor._work_queue.get_nowait()
                    func = work_item['func']
                    result_queue = work_item['result_queue']
                    try:
                        result = func()
                        result_queue.put({'success': True, 'data': result})
                    except Exception as e:
                        result_queue.put({
                            'success': False,
                            'error': str(e),
                            'traceback': traceback.format_exc()
                        })
                except queue.Empty:
                    break
        except:
            pass


class ApiExecutor:
    """Executes Fusion API operations via the work queue pattern."""

    _work_queue = queue.Queue()

    def __init__(self, app):
        self._app = app
        self._object_store = {}  # Named object references

    def _execute_on_main_thread(self, func, timeout=30):
        """
        Queue a function for execution on Fusion's main thread.
        Blocks until the result is available or timeout is reached.

        Args:
            func: A callable that will be invoked on the main thread.
            timeout: Maximum seconds to wait for a result.

        Returns:
            The result dict from the main thread execution.
        """
        result_queue = queue.Queue()
        work_item = {
            'func': func,
            'result_queue': result_queue
        }
        ApiExecutor._work_queue.put(work_item)

        # Fire custom event to wake the main thread
        self._app.fireCustomEvent(CUSTOM_EVENT_ID)

        # Wait for result
        try:
            result = result_queue.get(timeout=timeout)
            return result
        except queue.Empty:
            return {
                'success': False,
                'error': f'Timeout after {timeout}s waiting for main thread execution'
            }

    def execute_api_call(self, api_path, args=None, kwargs=None, store_as=None):
        """
        Execute a Fusion API call by resolving a dotted path.

        The path is walked starting from known roots (app, ui, design,
        rootComponent) or stored object references ($varName).

        Special handling:
        - Args starting with $ are resolved from the object store
        - Args that are dicts with a "type" key are constructed as
          Fusion value types (Point3D, Vector3D, ValueInput, etc.)
        """
        args = args or []
        kwargs = kwargs or {}

        def _do_call():
            # Resolve args that reference stored objects or Fusion types
            resolved_args = [self._resolve_arg(a) for a in args]
            resolved_kwargs = {k: self._resolve_arg(v) for k, v in kwargs.items()}

            # Walk the dotted path
            obj = self._resolve_path(api_path)

            # If the final object is callable, call it
            if callable(obj):
                result = obj(*resolved_args, **resolved_kwargs)
            else:
                result = obj

            # Store if requested
            if store_as:
                self._object_store[store_as] = result

            return self._serialize_result(result, store_as)

        return self._execute_on_main_thread(_do_call)

    def execute_python(self, code):
        """
        Execute arbitrary Python code with Fusion objects pre-injected.

        Available in the execution namespace:
        - app, ui, design, rootComponent (Fusion objects)
        - adsk (the adsk module and submodules)
        - math (the math module)
        - store: dict -- the object store (read/write access)
        - All previously stored objects as local variables

        The code can assign to `result` to return a value.
        """
        def _do_exec():
            app = self._app
            design = adsk.fusion.Design.cast(app.activeProduct)
            root_comp = design.rootComp if design else None

            # Build execution namespace
            namespace = {
                'app': app,
                'ui': app.userInterface,
                'design': design,
                'rootComponent': root_comp,
                'rootComp': root_comp,
                'adsk': adsk,
                'math': math,
                'store': self._object_store,
                'result': None
            }

            # Inject all stored objects
            for name, obj in self._object_store.items():
                namespace[name] = obj

            exec(code, namespace)

            result = namespace.get('result')
            return self._serialize_result(result)

        return self._execute_on_main_thread(_do_exec)

    def inspect_object(self, target):
        """
        Inspect a Fusion object to discover its methods and properties.

        Returns categorized listings of:
        - Properties (non-callable attributes)
        - Methods (callable attributes)
        - Filtered to exclude private/dunder attributes
        """
        def _do_inspect():
            obj = self._resolve_path(target)

            members = dir(obj)
            properties = []
            methods = []

            for name in members:
                if name.startswith('_'):
                    continue
                try:
                    attr = getattr(obj, name)
                    if callable(attr):
                        # Try to get signature
                        try:
                            sig = str(inspect.signature(attr))
                        except (ValueError, TypeError):
                            sig = '(...)'
                        methods.append(f'{name}{sig}')
                    else:
                        type_name = type(attr).__name__
                        properties.append(f'{name}: {type_name} = {repr(attr)[:100]}')
                except Exception as e:
                    properties.append(f'{name}: <error accessing: {e}>')

            return {
                'success': True,
                'result': {
                    'type': type(obj).__name__,
                    'module': type(obj).__module__,
                    'properties': properties,
                    'methods': methods
                }
            }

        result = self._execute_on_main_thread(_do_inspect)
        # The inner function already returns the full dict, so unwrap if needed
        if result.get('success') and isinstance(result.get('data'), dict):
            return result['data']
        return result

    def _resolve_path(self, path):
        """
        Resolve a dotted path to a Fusion object.

        Starting roots:
        - "app" -> Application object
        - "ui" -> UserInterface object
        - "design" -> active Design
        - "rootComponent" / "rootComp" -> root Component
        - "$varName" -> object from the store
        - "adsk.core.X" / "adsk.fusion.X" -> class/static access
        """
        parts = path.split('.')

        # Determine the starting object
        first = parts[0]

        if first.startswith('$'):
            var_name = first[1:]
            if var_name not in self._object_store:
                raise KeyError(f'No stored object named "{var_name}". '
                             f'Available: {list(self._object_store.keys())}')
            obj = self._object_store[var_name]
            parts = parts[1:]
        elif first == 'app':
            obj = self._app
            parts = parts[1:]
        elif first == 'ui':
            obj = self._app.userInterface
            parts = parts[1:]
        elif first == 'design':
            obj = adsk.fusion.Design.cast(self._app.activeProduct)
            if obj is None:
                raise RuntimeError('No active Fusion design. Open or create a design first.')
            parts = parts[1:]
        elif first == 'rootComponent' or first == 'rootComp':
            design = adsk.fusion.Design.cast(self._app.activeProduct)
            if design is None:
                raise RuntimeError('No active Fusion design.')
            obj = design.rootComp
            parts = parts[1:]
        elif first == 'adsk':
            # Walking into adsk module hierarchy
            obj = adsk
            parts = parts[1:]
        else:
            raise ValueError(
                f'Unknown root "{first}". Use: app, ui, design, '
                f'rootComponent, $storedVar, or adsk.core/fusion/cam.*'
            )

        # Walk remaining path segments
        for part in parts:
            try:
                obj = getattr(obj, part)
            except AttributeError:
                raise AttributeError(
                    f'"{part}" not found on {type(obj).__name__}. '
                    f'Available: {[a for a in dir(obj) if not a.startswith("_")][:20]}'
                )

        return obj

    def _resolve_arg(self, arg):
        """
        Resolve a single argument value.

        - Strings starting with "$" are looked up in the object store
        - Dicts with a "type" key are constructed as Fusion value types
        - Everything else is passed through as-is
        """
        if isinstance(arg, str) and arg.startswith('$'):
            var_name = arg[1:]
            if var_name not in self._object_store:
                raise KeyError(f'No stored object "{var_name}"')
            return self._object_store[var_name]

        if isinstance(arg, dict) and 'type' in arg:
            return self._construct_value_type(arg)

        if isinstance(arg, list):
            return [self._resolve_arg(a) for a in arg]

        return arg

    def _construct_value_type(self, spec):
        """
        Construct Fusion API value types from dict specifications.

        Supported types:
        - Point3D: {"type": "Point3D", "x": 0, "y": 0, "z": 0}
        - Vector3D: {"type": "Vector3D", "x": 0, "y": 0, "z": 1}
        - ValueInput (real): {"type": "ValueInput", "real": 2.0}
        - ValueInput (string): {"type": "ValueInput", "value": "5 mm"}
        """
        t = spec['type']

        if t == 'Point3D':
            return adsk.core.Point3D.create(
                spec.get('x', 0),
                spec.get('y', 0),
                spec.get('z', 0)
            )
        elif t == 'Vector3D':
            return adsk.core.Vector3D.create(
                spec.get('x', 0),
                spec.get('y', 0),
                spec.get('z', 0)
            )
        elif t == 'ValueInput':
            if 'real' in spec:
                return adsk.core.ValueInput.createByReal(spec['real'])
            elif 'value' in spec:
                return adsk.core.ValueInput.createByString(spec['value'])
            else:
                raise ValueError('ValueInput needs "real" or "value" key')
        elif t == 'ObjectCollection':
            coll = adsk.core.ObjectCollection.create()
            for item in spec.get('items', []):
                coll.add(self._resolve_arg(item))
            return coll
        else:
            raise ValueError(f'Unknown value type: {t}. Supported: Point3D, Vector3D, ValueInput, ObjectCollection')

    def _serialize_result(self, result, store_as=None):
        """Convert a Fusion API result to a JSON-serializable dict."""
        response = {'success': True}

        if result is None:
            response['result'] = None
            response['type'] = 'None'
        elif isinstance(result, (str, int, float, bool)):
            response['result'] = result
            response['type'] = type(result).__name__
        elif isinstance(result, dict):
            response['result'] = result
            response['type'] = 'dict'
        elif isinstance(result, (list, tuple)):
            response['result'] = str(result)
            response['type'] = type(result).__name__
        else:
            response['result'] = str(result)
            response['type'] = f'{type(result).__module__}.{type(result).__name__}'

        if store_as:
            response['stored_as'] = store_as

        return response
```

**Important design notes for api_executor.py:**

- The `_work_queue` is a **class variable** on `ApiExecutor`, not an instance variable. The `WorkQueueHandler` accesses it via `ApiExecutor._work_queue`. This ensures there is a single shared queue.
- The `_execute_on_main_thread` method blocks the daemon thread (which is fine -- the HTTP request is waiting for a response anyway).
- The `_resolve_path` method must handle the `adsk.core.*` and `adsk.fusion.*` namespaces so the agent can access static/class methods like `adsk.core.ValueInput.createByReal()`.
- The `_serialize_result` method must never try to JSON-serialize Fusion API objects directly. Always convert to string with `str()`.
- The `inspect_object` method wraps its return differently because it returns a structured dict. Make sure the result unwrapping logic handles this correctly.

---

### fusion_mcp_server/server.py

The FastMCP server that Claude Code launches as a subprocess.

**Must implement three tools:**

```python
import json
import os
from mcp.server.fastmcp import FastMCP
from fusion_client import FusionClient

# Load config
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path) as f:
    config = json.load(f)

client = FusionClient(
    host=config['host'],
    port=config['port'],
    token=config['auth_token']
)

mcp = FastMCP("Fusion 360 MCP Server")


@mcp.tool()
def fusion_api(
    api_path: str,
    args: list = None,
    kwargs: dict = None,
    store_as: str = None
) -> str:
    """Execute a Fusion 360 API call using dotted path notation.

    Navigate the Fusion 360 object model and call methods or access properties
    using a dotted path starting from one of the available roots.

    Available roots:
    - app: The Application object (access documents, preferences, etc.)
    - ui: The UserInterface object (palettes, dialogs, selections)
    - design: The active Design (timeline, components, etc.)
    - rootComponent: The root Component of the active design
    - $storedVariable: Any previously stored object reference
    - adsk.core.ClassName: Static/class method access (e.g., adsk.core.ValueInput.createByReal)

    Parameters:
    - api_path: Dotted path to the property or method (e.g., "rootComponent.sketches.add")
    - args: List of positional arguments. Use "$varName" to reference stored objects.
            Use {"type": "Point3D", "x": 0, "y": 0, "z": 0} for Fusion value types.
    - kwargs: Dict of keyword arguments (same resolution rules as args).
    - store_as: Name to store the result under for subsequent calls (access as "$name").

    Supported value type constructors (pass as args):
    - {"type": "Point3D", "x": 0, "y": 0, "z": 0}
    - {"type": "Vector3D", "x": 0, "y": 0, "z": 1}
    - {"type": "ValueInput", "real": 2.0} (for real number values, in cm)
    - {"type": "ValueInput", "value": "5 mm"} (for string expressions)
    - {"type": "ObjectCollection", "items": [...]} (collection of objects)

    All dimensions in Fusion 360 are in centimeters by default.

    Common workflow examples:

    1. Create a box:
       Step 1: Get XY plane
         api_path: "rootComponent.xYConstructionPlane"
         store_as: "xyPlane"

       Step 2: Create sketch on XY plane
         api_path: "rootComponent.sketches.add"
         args: ["$xyPlane"]
         store_as: "sketch1"

       Step 3: Draw a rectangle
         api_path: "$sketch1.sketchCurves.sketchLines.addTwoPointRectangle"
         args: [
           {"type": "Point3D", "x": 0, "y": 0, "z": 0},
           {"type": "Point3D", "x": 5, "y": 3, "z": 0}
         ]

       Step 4: Get the profile
         api_path: "$sketch1.profiles.item"
         args: [0]
         store_as: "profile1"

       Step 5: Create extrude input
         api_path: "rootComponent.features.extrudeFeatures.createInput"
         args: ["$profile1", 0]
         store_as: "extInput"

       Step 6: Set distance
         api_path: "$extInput.setDistanceExtent"
         args: [false, {"type": "ValueInput", "real": 2.0}]

       Step 7: Execute extrude
         api_path: "rootComponent.features.extrudeFeatures.add"
         args: ["$extInput"]
         store_as: "extrude1"

    2. Export as STL:
       Step 1: Get export manager
         api_path: "design.exportManager"
         store_as: "exportMgr"

       Step 2: Create STL options
         api_path: "$exportMgr.createSTLExportOptions"
         args: ["$rootComp", "/path/to/output.stl"]
         store_as: "stlOptions"

       Step 3: Execute export
         api_path: "$exportMgr.execute"
         args: ["$stlOptions"]
    """
    result = client.send_request({
        'action': 'api_call',
        'api_path': api_path,
        'args': args or [],
        'kwargs': kwargs or {},
        'store_as': store_as
    })
    return json.dumps(result, indent=2)


@mcp.tool()
def fusion_python(code: str) -> str:
    """Execute Python code directly in Fusion 360's runtime environment.

    The code runs on Fusion's main thread with full access to the Fusion API.
    Use this for complex operations that are easier to express as Python code
    rather than individual API calls.

    Pre-injected variables available in your code:
    - app: adsk.core.Application
    - ui: adsk.core.UserInterface
    - design: adsk.fusion.Design (the active design)
    - rootComponent / rootComp: adsk.fusion.Component (root component)
    - adsk: The adsk module (adsk.core, adsk.fusion, adsk.cam)
    - math: The math module
    - store: dict - the object store (read/write, persists across calls)
    - All previously stored objects are available as local variables

    To return a value, assign to the `result` variable:
        result = some_value

    Example - Create a cylinder:
        code: '''
        # Create sketch
        xyPlane = rootComponent.xYConstructionPlane
        sketch = rootComponent.sketches.add(xyPlane)

        # Draw circle
        circles = sketch.sketchCurves.sketchCircles
        center = adsk.core.Point3D.create(0, 0, 0)
        circles.addByCenterRadius(center, 3.0)  # 3cm radius

        # Extrude
        profile = sketch.profiles.item(0)
        extrudes = rootComponent.features.extrudeFeatures
        ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(5.0)  # 5cm
        ext_input.setDistanceExtent(False, distance)
        extrude = extrudes.add(ext_input)

        # Store for later use
        store['cylinder'] = extrude
        result = f'Created cylinder: {extrude.name}'
        '''

    Example - List all bodies:
        code: '''
        bodies = rootComponent.bRepBodies
        result = [bodies.item(i).name for i in range(bodies.count)]
        '''

    Example - Modify existing object:
        code: '''
        body = store['myBody']
        result = f'Body has {body.faces.count} faces and {body.edges.count} edges'
        '''
    """
    result = client.send_request({
        'action': 'python_exec',
        'code': code
    })
    return json.dumps(result, indent=2)


@mcp.tool()
def fusion_inspect(target: str = "app") -> str:
    """Inspect a Fusion 360 object to discover its available methods and properties.

    Use this to explore the Fusion API when you're unsure what methods or
    properties are available on an object.

    Parameters:
    - target: Dotted path to the object to inspect. Same path syntax as fusion_api.
              Defaults to "app" (the Application object).

    Examples:
    - "app" -- inspect the Application object
    - "design" -- inspect the active Design
    - "rootComponent" -- inspect the root Component
    - "rootComponent.sketches" -- inspect the Sketches collection
    - "rootComponent.features" -- inspect the Features collection
    - "rootComponent.features.extrudeFeatures" -- inspect ExtrudeFeatures
    - "$sketch1" -- inspect a stored sketch object
    - "adsk.fusion.FeatureOperations" -- inspect an enum

    Returns a categorized listing of properties (with types and current values)
    and methods (with signatures where available).
    """
    result = client.send_request({
        'action': 'inspect',
        'target': target
    })
    return json.dumps(result, indent=2)


if __name__ == '__main__':
    mcp.run(transport='stdio')
```

---

### fusion_mcp_server/fusion_client.py

Simple HTTP client using only stdlib. Sends JSON POST requests to the Fusion add-in.

```python
import json
import urllib.request
import urllib.error


class FusionClient:
    """HTTP client for communicating with the Fusion MCP Bridge add-in."""

    def __init__(self, host='127.0.0.1', port=45876, token=''):
        self.base_url = f'http://{host}:{port}'
        self.token = token

    def send_request(self, payload: dict) -> dict:
        """
        Send a JSON request to the Fusion Bridge and return the response.

        Args:
            payload: Dict with 'action' and action-specific fields.

        Returns:
            Response dict from the bridge.

        Raises:
            ConnectionError: If the bridge is not running.
            RuntimeError: If the bridge returns an error status.
        """
        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                body = response.read().decode('utf-8')
                return json.loads(body)
        except urllib.error.URLError as e:
            if 'Connection refused' in str(e):
                return {
                    'success': False,
                    'error': (
                        'Cannot connect to Fusion MCP Bridge. '
                        'Make sure the fusion_bridge add-in is running in Fusion 360 '
                        'and the port/token in config.json are correct.'
                    )
                }
            return {
                'success': False,
                'error': f'HTTP error: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {e}'
            }

    def health_check(self) -> bool:
        """Check if the Fusion Bridge is running and reachable."""
        result = self.send_request({'action': 'health'})
        return result.get('success', False)
```

---

### fusion_mcp_server/config.json

```json
{
    "host": "127.0.0.1",
    "port": 45876,
    "auth_token": "PASTE_TOKEN_FROM_FUSION_TEXT_COMMANDS_HERE"
}
```

After starting the Fusion add-in, copy the token from Fusion's TEXT COMMANDS palette and paste it here.

---

### fusion_mcp_server/requirements.txt

```
mcp[cli]>=1.0.0
```

---

### install.sh

A helper script for installation. Should:

1. Detect the OS (macOS vs Windows).
2. Locate or prompt for the Fusion 360 add-ins directory.
3. Copy/symlink the `fusion_bridge` folder into Fusion's AddIns directory.
4. Set up a Python virtualenv for the MCP server and install dependencies.
5. Print instructions for configuring Claude Code's MCP settings.

Typical Fusion add-in paths:
- **macOS:** `~/Library/Application Support/Autodesk/Autodesk Fusion/API/AddIns/`
- **Windows:** `%APPDATA%/Autodesk/Autodesk Fusion/API/AddIns/`

The script should create a symlink rather than copying, so edits to the source are reflected immediately.

After installation, print the Claude Code MCP configuration snippet:

```json
{
    "mcpServers": {
        "fusion360": {
            "type": "stdio",
            "command": "python",
            "args": ["/absolute/path/to/fusion_mcp_server/server.py"],
            "env": {}
        }
    }
}
```

(Using the actual resolved path from the install location.)

---

### README.md

Write a clear README covering:

1. **What this is** -- one paragraph
2. **Prerequisites** -- Fusion 360, Python 3.10+, Claude Code
3. **Installation** -- run install.sh or manual steps
4. **Usage**:
   - Start Fusion 360, enable the fusion_bridge add-in
   - Copy auth token from TEXT COMMANDS palette
   - Paste token into config.json
   - Configure Claude Code MCP settings
   - Start using: "Create a 5cm cube in Fusion"
5. **Security model** -- localhost only, per-session auth tokens, no external network
6. **Troubleshooting** -- common issues and fixes
7. **Architecture** -- brief description of the two-process model

---

## Testing Instructions

After building all files, test the build by verifying:

1. All Python files parse without syntax errors (`python -c "import ast; ast.parse(open('file.py').read())"`)
2. The manifest JSON is valid
3. The config JSON is valid
4. The requirements.txt is present and correct
5. The install.sh is executable and has correct shebang

Then provide these manual testing instructions:

1. Open Fusion 360
2. Go to **Utilities tab > Scripts and Add-Ins > Add-Ins tab**
3. Click the green "+" next to "My Add-Ins" to add the fusion_bridge folder
4. Select `fusion_bridge` and click **Run**
5. Open the **TEXT COMMANDS** palette (View > Text Commands, or Ctrl+Alt+C / Cmd+Alt+C)
6. Copy the auth token displayed there
7. Paste the token into `fusion_mcp_server/config.json`
8. Start a Claude Code session with the MCP configured
9. Ask Claude: "Create a 5cm x 3cm x 2cm box in Fusion"
10. Verify the box appears in Fusion's viewport

---

## Reference Documentation

The `docs/` folder in this build package contains additional reference material:
- `fusion-api/` -- Fusion 360 API documentation (object model, threading, sketches, features, etc.)
- `mcp-protocol/` -- MCP protocol documentation (FastMCP, transports, tool schemas)
- `aurafriday-analysis/` -- Security analysis of the MCP server being replaced

Read the build guide at `build-guide/BUILD-GUIDE.md` for the complete technical specification that informed this prompt. Consult the docs when you need API details or aren't sure about a Fusion method signature.

### Recommended Companion: Context7 MCP Server

If you have Context7 configured as an MCP server, use it to look up Fusion 360 API details in real time. It provides live, up-to-date documentation for any library and is especially useful when you need a method signature, parameter type, or usage example not covered in the static docs above.

Context7 MCP config (add alongside the fusion360 entry):

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

Requires Node.js/npm. This is optional but strongly recommended -- it fills any gaps in the bundled documentation.

---

## Important Reminders

- **Do NOT call any Fusion API from the daemon thread.** This is the #1 cause of crashes. Always go through the work queue.
- **Do NOT import third-party packages in the add-in.** Fusion's Python has no pip. stdlib only.
- **Do NOT bind to 0.0.0.0.** Localhost only.
- **Generate a NEW auth token on every add-in startup.** Never hardcode tokens.
- **Keep handler references alive.** Store them in a module-level list to prevent garbage collection.
- **Test each file for syntax errors** before considering the build complete.
- **The `__init__.py` file is NOT needed** for the Fusion add-in -- Fusion handles package loading via the manifest file.
