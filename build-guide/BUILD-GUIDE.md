# Fusion 360 Secure MCP Server -- Complete Build Guide

> **Purpose:** This document is a complete, self-contained specification for building a secure MCP server that gives Claude Code (or any MCP-capable AI agent) full control over Autodesk Fusion 360. An AI coding agent should be able to read this document and produce a working implementation without any additional context.

> **Author context:** This build guide was created after analyzing an existing open-source MCP server (AuraFriday's) that had security problems -- hardcoded tokens, binding to 0.0.0.0, bundled auto-updaters. This guide specifies a clean, minimal, secure replacement.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Why Two Processes](#2-why-two-processes)
3. [Component 1: Fusion Add-in (fusion_bridge)](#3-component-1-fusion-add-in-fusion_bridge)
4. [Component 2: MCP Server (fusion_mcp_server)](#4-component-2-mcp-server-fusion_mcp_server)
5. [Security Requirements (Non-Negotiable)](#5-security-requirements-non-negotiable)
6. [Installation Steps](#6-installation-steps)
7. [Claude Code Configuration](#7-claude-code-configuration)
8. [Common Fusion 360 API Patterns](#8-common-fusion-360-api-patterns)
9. [Testing and Verification](#9-testing-and-verification)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Architecture Overview

The system uses a **two-process architecture** with an HTTP bridge between them:

```
Claude Code ──stdio──> MCP Server (FastMCP, system Python)
                              |
                         HTTP POST (127.0.0.1:45876)
                         Bearer token auth
                              |
                              v
                     Fusion Add-in (runs inside Fusion's bundled Python)
                         HTTP server on background daemon thread
                              |
                         CustomEvent + work queue
                              |
                              v
                     Fusion Main Thread (safe API calls here)
```

**Data flow for a single tool call:**

1. Claude Code sends an MCP tool call (e.g., `fusion_api`) over stdio.
2. The MCP server (FastMCP) receives it, constructs an HTTP POST payload, and sends it to `http://127.0.0.1:45876`.
3. The Fusion add-in's HTTP server (running on a background daemon thread) receives the request.
4. It validates the Bearer token, parses the JSON body, and puts a work item into a thread-safe queue.
5. It fires a Fusion CustomEvent to wake up the main thread.
6. The CustomEvent handler (running on Fusion's main thread) pulls the work item, executes the Fusion API call, and puts the result into a result queue.
7. The HTTP handler (still waiting on the background thread) reads the result from the result queue and sends it back as an HTTP response.
8. The MCP server receives the HTTP response and returns it to Claude Code via stdio.

This round-trip happens for every tool call. The CustomEvent pattern is mandatory because Fusion's API is not thread-safe -- all API calls must happen on the main thread.

---

## 2. Why Two Processes

Four reasons this cannot be a single process:

1. **Fusion bundles its own Python runtime.** You cannot `pip install` packages into it. The Fusion add-in can only use Fusion's Python's standard library plus the `adsk` module that Fusion provides.

2. **The MCP SDK (FastMCP) requires pip install.** It depends on `pydantic`, `anyio`, `httpx`, and other packages that are not in stdlib.

3. **Separation of concerns.** The MCP server handles protocol framing (stdio, JSON-RPC). The Fusion add-in handles API bridging. Neither needs to know about the other's internals.

4. **Version independence.** The MCP server can run on Python 3.10, 3.11, 3.12, or whatever the system has. The Fusion add-in runs on whatever Python Fusion ships (currently CPython 3.11.x on Fusion 2024+).

---

## 3. Component 1: Fusion Add-in (fusion_bridge)

### 3.1 File Structure

Fusion requires add-ins to follow a specific directory layout. The directory name MUST match the main Python file name (without the `.py` extension):

```
fusion_bridge/
    fusion_bridge.py          # Main entry point (run/stop functions)
    fusion_bridge.manifest    # Add-in manifest (JSON, required by Fusion)
    bridge_server.py          # HTTP server on background daemon thread
    api_executor.py           # Fusion API path resolution + Python exec
```

All four files go into this single directory. No subdirectories, no `__init__.py`, no virtual environments.

### 3.2 Add-in Manifest

File: `fusion_bridge/fusion_bridge.manifest`

```json
{
    "autodeskProduct": "Fusion",
    "type": "addin",
    "id": "f1e2d3c4-a5b6-7890-abcd-ef1234567890",
    "author": "Creative_Inertia",
    "description": {
        "": "Secure MCP Bridge for Fusion 360 - allows AI agents to control Fusion via localhost HTTP"
    },
    "version": "1.0.0",
    "runOnStartup": true,
    "supportedOS": "windows|mac"
}
```

Notes:
- The `id` field must be a valid UUID. Generate a fresh one for production (use `python -c "import uuid; print(uuid.uuid4())"`).
- `runOnStartup` means Fusion will auto-start this add-in when Fusion launches. The user can toggle this off in the Add-Ins dialog.
- `supportedOS` uses `|` as the separator, not a comma.
- The empty string key `""` in `description` is the default locale.

### 3.3 Main Entry Point

File: `fusion_bridge/fusion_bridge.py`

This file MUST define two module-level functions: `run(context)` and `stop(context)`. Fusion calls these when the add-in starts and stops.

```python
"""
Fusion 360 Add-in: Secure MCP Bridge
Main entry point. Starts an HTTP server on a background thread
and uses CustomEvents to safely execute Fusion API calls on the main thread.
"""

import adsk.core
import adsk.fusion
import threading
import secrets
import traceback

# Keep references alive for the lifetime of the add-in.
# If these get garbage-collected, Fusion will crash or silently stop firing events.
_handlers = []
_stop_event = threading.Event()
_server_thread = None
_custom_event_id = 'SecureFusionMCPBridge'

# These are imported here so bridge_server and api_executor can access them.
# Fusion add-ins cannot do normal Python imports between files in the same directory
# without path manipulation, so we handle that in run().


def run(context):
    """Called by Fusion when the add-in starts."""
    global _server_thread

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # -- Import sibling modules --
        # Fusion's add-in loader does not put the add-in directory on sys.path,
        # so we must add it manually.
        import os, sys
        addin_dir = os.path.dirname(os.path.realpath(__file__))
        if addin_dir not in sys.path:
            sys.path.insert(0, addin_dir)

        # Force-reload in case Fusion cached a previous version
        import importlib
        import api_executor
        import bridge_server
        importlib.reload(api_executor)
        importlib.reload(bridge_server)

        # -- Register CustomEvent --
        custom_event = app.registerCustomEvent(_custom_event_id)
        handler = api_executor.WorkQueueHandler()
        custom_event.add(handler)
        _handlers.append(handler)
        _handlers.append(custom_event)

        # -- Generate auth token --
        token = secrets.token_urlsafe(32)

        # Display token in Fusion's TEXT COMMANDS panel so the user can copy it.
        text_palette = ui.palettes.itemById('TextCommands')
        if text_palette:
            text_palette.writeText('=' * 60)
            text_palette.writeText('FUSION MCP BRIDGE - AUTH TOKEN')
            text_palette.writeText(f'Token: {token}')
            text_palette.writeText('Copy this token into fusion_mcp_server/config.json')
            text_palette.writeText('=' * 60)

        # -- Start HTTP server on background daemon thread --
        _stop_event.clear()
        host = '127.0.0.1'
        port = 45876

        _server_thread = threading.Thread(
            target=bridge_server.start_server,
            args=(host, port, token, _stop_event, _custom_event_id),
            daemon=True
        )
        _server_thread.start()

        if text_palette:
            text_palette.writeText(f'MCP Bridge server started on {host}:{port}')
            text_palette.writeText('Ready for connections from Claude Code.')

    except Exception:
        app = adsk.core.Application.get()
        if app and app.userInterface:
            app.userInterface.messageBox(
                f'fusion_bridge failed to start:\n{traceback.format_exc()}'
            )


def stop(context):
    """Called by Fusion when the add-in stops."""
    global _server_thread

    try:
        # Signal the HTTP server to shut down
        _stop_event.set()

        if _server_thread and _server_thread.is_alive():
            _server_thread.join(timeout=5)

        # Unregister CustomEvent
        app = adsk.core.Application.get()
        if app:
            app.unregisterCustomEvent(_custom_event_id)

        # Clear handler references
        _handlers.clear()
        _server_thread = None

    except Exception:
        pass  # Shutting down, best-effort cleanup
```

**Critical implementation notes:**

- `_handlers` is a module-level list. You MUST keep references to the CustomEventHandler and the CustomEvent object. If Python garbage-collects them, the event stops firing and the bridge silently breaks.
- The `daemon=True` flag on the server thread ensures it dies when Fusion exits, even if `stop()` is not called cleanly.
- `sys.path.insert(0, addin_dir)` is required because Fusion does not add the add-in's directory to `sys.path` by default.
- `importlib.reload()` is required because Fusion caches modules between add-in stop/start cycles. Without it, code changes require a full Fusion restart.

### 3.4 HTTP Server

File: `fusion_bridge/bridge_server.py`

Uses ONLY Python stdlib (`http.server`, `json`, `threading`). No third-party packages.

```python
"""
HTTP server that runs on a background daemon thread inside Fusion.
Receives commands from the MCP server, queues them for the main thread,
and returns results.
"""

import http.server
import json
import threading
import traceback

# These will be set by start_server()
_auth_token = None
_custom_event_id = None


class BridgeRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handle incoming HTTP POST requests from the MCP server."""

    # Suppress default stderr logging (it clutters Fusion's console)
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        # -- Authenticate --
        auth_header = self.headers.get('Authorization', '')
        if auth_header != f'Bearer {_auth_token}':
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': 'Unauthorized: invalid or missing Bearer token'
            }).encode())
            return

        # -- Read and parse body --
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body)
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'Bad request: {str(e)}'
            }).encode())
            return

        # -- Dispatch to the appropriate handler --
        try:
            operation = payload.get('operation', '')

            if operation == 'ping':
                # Health check -- does not need the main thread
                result = {'success': True, 'result': 'pong'}

            elif operation in ('api_call', 'python_exec', 'inspect'):
                # These MUST run on Fusion's main thread via CustomEvent
                import api_executor
                result = api_executor.execute_on_main_thread(
                    operation, payload, timeout=30
                )

            else:
                result = {
                    'success': False,
                    'error': f'Unknown operation: {operation}'
                }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }).encode())

    def do_GET(self):
        """Reject GET requests with a helpful message."""
        self.send_response(405)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'success': False,
            'error': 'Only POST requests are accepted'
        }).encode())


def start_server(host, port, token, stop_event, custom_event_id):
    """
    Start the HTTP server. Called from a background daemon thread.
    Blocks until stop_event is set.

    Args:
        host: Bind address (must be '127.0.0.1')
        port: Port number (default 45876)
        token: Bearer auth token (generated by fusion_bridge.py)
        stop_event: threading.Event that signals shutdown
        custom_event_id: Fusion CustomEvent ID string
    """
    global _auth_token, _custom_event_id
    _auth_token = token
    _custom_event_id = custom_event_id

    server = http.server.HTTPServer((host, port), BridgeRequestHandler)
    server.timeout = 1.0  # Check stop_event every second

    while not stop_event.is_set():
        server.handle_request()

    server.server_close()
```

**Critical implementation notes:**

- `server.timeout = 1.0` combined with the `while not stop_event.is_set()` loop means the server checks for shutdown every second. Without the timeout, `handle_request()` blocks forever and `stop()` cannot cleanly shut down the add-in.
- `log_message` is overridden to suppress per-request logging to stderr, which would clutter Fusion's output. For debugging, you can re-enable it.
- The `do_GET` handler exists only to return a helpful error if someone hits the endpoint in a browser.

### 3.5 API Executor

File: `fusion_bridge/api_executor.py`

This is the core of the bridge. It resolves dotted API paths, executes Python code, and inspects objects -- all on Fusion's main thread via the CustomEvent/work-queue pattern.

```python
"""
Fusion API executor. All public functions in this module are designed to run
on Fusion's main thread via the CustomEvent work queue.
"""

import adsk.core
import adsk.fusion
import adsk.cam
import threading
import queue
import json
import traceback

# Thread-safe work queue: background HTTP thread puts items here,
# main thread CustomEvent handler pulls them out.
work_queue = queue.Queue()

# Persistent object store: keeps references to Fusion objects across calls.
# e.g., after creating a sketch with store_as="sketch1", later calls can
# reference it as "$sketch1" in api_path or args.
object_store = {}

CUSTOM_EVENT_ID = 'SecureFusionMCPBridge'


def _get_roots():
    """
    Get the current Fusion application roots.
    Called fresh each time because the active document/design can change.
    """
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root_comp = design.rootComponent if design else None

    roots = {
        'app': app,
        'ui': app.userInterface,
        'design': design,
        'rootComponent': root_comp,
    }

    # Add construction plane shortcuts
    if root_comp:
        roots['xyPlane'] = root_comp.xYConstructionPlane
        roots['xzPlane'] = root_comp.xZConstructionPlane
        roots['yzPlane'] = root_comp.yZConstructionPlane

    return roots


def _resolve_arg(arg):
    """
    Resolve a single argument value.
    - Strings starting with '$' are looked up in the object store.
    - Everything else is passed through as-is.
    """
    if isinstance(arg, str) and arg.startswith('$'):
        key = arg[1:]
        if key in object_store:
            return object_store[key]
        # Also check roots (e.g., $xyPlane)
        roots = _get_roots()
        if key in roots:
            return roots[key]
        raise ValueError(f'Object "${key}" not found in store or roots')
    return arg


def _resolve_args(args):
    """Resolve a list of arguments, expanding $references."""
    if not args:
        return []
    return [_resolve_arg(a) for a in args]


def _resolve_kwargs(kwargs):
    """Resolve keyword arguments, expanding $references in values."""
    if not kwargs:
        return {}
    return {k: _resolve_arg(v) for k, v in kwargs.items()}


def _make_serializable(obj):
    """
    Convert a Fusion API object to a serializable string representation.
    Fusion objects are not JSON-serializable, so we convert them to descriptive strings.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}

    # For Fusion API objects, return their type and any useful identifying info
    type_name = type(obj).__name__
    result = f'<{type_name}'

    # Try to get common identifying attributes
    for attr in ('name', 'objectType', 'entityToken'):
        try:
            val = getattr(obj, attr, None)
            if val is not None:
                result += f' {attr}="{val}"'
                break
        except Exception:
            pass

    result += '>'
    return result


def resolve_api_path(path_str, args=None, kwargs=None, store_as=None):
    """
    Resolve a dotted API path like 'rootComponent.sketches.add' and optionally call it.

    Path resolution rules:
    - Paths starting with '$' reference the object store (e.g., '$sketch1.profiles')
    - Known roots: app, ui, design, rootComponent, xyPlane, xzPlane, yzPlane
    - Paths starting with 'adsk.' resolve against the adsk module hierarchy
    - Arguments containing '$varName' strings are resolved from the object store

    Args:
        path_str: Dotted path like 'rootComponent.sketches.add'
        args: Positional arguments (list). $-prefixed strings resolved from store.
        kwargs: Keyword arguments (dict). $-prefixed string values resolved from store.
        store_as: If set, save the result in object_store under this name.

    Returns:
        dict with 'success', 'result', and optionally 'stored_as' keys.
    """
    roots = _get_roots()
    roots.update(object_store)

    parts = path_str.split('.')

    # Determine the starting object
    if parts[0].startswith('$'):
        key = parts[0][1:]
        if key not in object_store:
            raise ValueError(f'Object "${key}" not found in object store. '
                           f'Available: {list(object_store.keys())}')
        obj = object_store[key]
        parts = parts[1:]
    elif parts[0] == 'adsk':
        # Handle full module paths like adsk.core.Point3D.create
        # Walk the module path
        obj = adsk
        parts = parts[1:]  # skip 'adsk'
    elif parts[0] in roots:
        obj = roots[parts[0]]
        parts = parts[1:]
    else:
        available = list(roots.keys())
        raise ValueError(f'Unknown root: "{parts[0]}". '
                       f'Available roots: {available}')

    if obj is None:
        raise ValueError(f'Root object is None. Is a design document open in Fusion?')

    # Walk the remaining path
    for i, part in enumerate(parts):
        try:
            obj = getattr(obj, part)
        except AttributeError:
            traversed = '.'.join([path_str.split('.')[0]] + parts[:i])
            raise AttributeError(
                f'Object at "{traversed}" has no attribute "{part}". '
                f'Available: {[a for a in dir(obj) if not a.startswith("_")]}'
            )

    # If the final object is callable and we have arguments, call it
    resolved_args = _resolve_args(args)
    resolved_kwargs = _resolve_kwargs(kwargs)

    if callable(obj) and (resolved_args or resolved_kwargs):
        result = obj(*resolved_args, **resolved_kwargs)
    elif callable(obj) and not args and not kwargs:
        # Callable with no args -- return it without calling (it might be a property)
        result = obj
    else:
        result = obj

    # Store the result if requested
    if store_as:
        object_store[store_as] = result

    return {
        'success': True,
        'result': _make_serializable(result),
        'stored_as': store_as if store_as else None,
        'object_store_keys': list(object_store.keys())
    }


def execute_python(code):
    """
    Execute arbitrary Python code in Fusion's runtime with pre-injected variables.

    Pre-injected into the execution namespace:
    - app, ui, design, rootComponent (current Fusion state)
    - xyPlane, xzPlane, yzPlane (construction plane shortcuts)
    - adsk module (adsk.core, adsk.fusion, adsk.cam)
    - json module
    - All objects in the persistent object_store
    - store(name, obj) function to save objects for later use

    The code's print() output is captured and returned.
    """
    roots = _get_roots()

    # Build the execution namespace
    exec_globals = {
        '__builtins__': __builtins__,
        'adsk': adsk,
        'json': json,
    }
    exec_globals.update(roots)
    exec_globals.update(object_store)

    # Provide a store() function so code can save objects
    def store_object(name, obj):
        object_store[name] = obj
        return f'Stored as ${name}'

    exec_globals['store'] = store_object

    # Capture print output
    import io
    import sys
    output_buffer = io.StringIO()
    exec_globals['print'] = lambda *a, **kw: print(*a, file=output_buffer, **kw)

    # Compile and execute
    compiled = compile(code, '<mcp-python-exec>', 'exec')
    exec(compiled, exec_globals)

    output = output_buffer.getvalue()
    return {
        'success': True,
        'result': output if output else 'Executed successfully (no output)',
        'object_store_keys': list(object_store.keys())
    }


def inspect_object(target):
    """
    Inspect a Fusion object and return its available methods and properties.

    Args:
        target: Name of the object to inspect. Can be a root name ('rootComponent'),
                a store reference ('$sketch1'), or a dotted path ('rootComponent.sketches').
    """
    roots = _get_roots()
    roots.update(object_store)

    # Resolve the target object
    if target.startswith('$'):
        key = target[1:]
        if key not in object_store:
            raise ValueError(f'Object "${key}" not found. '
                           f'Available: {list(object_store.keys())}')
        obj = object_store[key]
    elif '.' in target:
        # Dotted path -- resolve it
        parts = target.split('.')
        if parts[0].startswith('$'):
            obj = object_store[parts[0][1:]]
            parts = parts[1:]
        elif parts[0] in roots:
            obj = roots[parts[0]]
            parts = parts[1:]
        else:
            raise ValueError(f'Unknown root: {parts[0]}')

        for part in parts:
            obj = getattr(obj, part)
    elif target in roots:
        obj = roots[target]
    else:
        raise ValueError(f'Unknown target: {target}. '
                       f'Available roots: {list(roots.keys())}')

    if obj is None:
        return {
            'success': True,
            'result': f'{target} is None (no active design?)',
            'type': 'NoneType'
        }

    # Gather information about the object
    type_name = type(obj).__name__
    members = []

    for name in sorted(dir(obj)):
        if name.startswith('_'):
            continue
        try:
            attr = getattr(obj, name)
            if callable(attr):
                members.append(f'  {name}() -- method')
            else:
                attr_type = type(attr).__name__
                members.append(f'  {name}: {attr_type} = {_make_serializable(attr)}')
        except Exception as e:
            members.append(f'  {name}: <error reading: {e}>')

    return {
        'success': True,
        'type': type_name,
        'target': target,
        'members': members,
        'result': f'{type_name} with {len(members)} accessible members'
    }


class WorkQueueHandler(adsk.core.CustomEventHandler):
    """
    CustomEvent handler that runs on Fusion's MAIN THREAD.
    Pulls work items from the queue, executes them, and puts results
    into the per-item result queue.
    """

    def __init__(self):
        super().__init__()

    def notify(self, args):
        """Called by Fusion on the main thread when a CustomEvent fires."""
        while not work_queue.empty():
            try:
                work_item = work_queue.get_nowait()
            except queue.Empty:
                break

            operation = work_item['operation']
            payload = work_item['payload']
            result_q = work_item['result_queue']

            try:
                if operation == 'api_call':
                    result = resolve_api_path(
                        payload['api_path'],
                        args=payload.get('args'),
                        kwargs=payload.get('kwargs'),
                        store_as=payload.get('store_as')
                    )
                elif operation == 'python_exec':
                    result = execute_python(payload['code'])
                elif operation == 'inspect':
                    result = inspect_object(payload['target'])
                else:
                    result = {'success': False, 'error': f'Unknown operation: {operation}'}

                result_q.put(result)

            except Exception as e:
                result_q.put({
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })


def execute_on_main_thread(operation, payload, timeout=30):
    """
    Queue a function for execution on Fusion's main thread and wait for the result.

    This is called from the HTTP server's background thread. It puts a work item
    in the queue, fires the CustomEvent to wake up the main thread, and blocks
    until the result is available (or timeout).

    Args:
        operation: 'api_call', 'python_exec', or 'inspect'
        payload: The full request payload dict
        timeout: Seconds to wait for a result (default 30)

    Returns:
        dict with the operation result

    Raises:
        TimeoutError: If the main thread does not respond within timeout seconds
    """
    result_q = queue.Queue()

    work_queue.put({
        'operation': operation,
        'payload': payload,
        'result_queue': result_q
    })

    # Fire the CustomEvent to wake up the main thread handler
    app = adsk.core.Application.get()
    app.fireCustomEvent(CUSTOM_EVENT_ID, '')

    try:
        return result_q.get(timeout=timeout)
    except queue.Empty:
        return {
            'success': False,
            'error': f'Timeout: main thread did not respond within {timeout} seconds. '
                     f'Fusion may be busy with a modal dialog or long operation.'
        }
```

**Critical implementation notes for `api_executor.py`:**

- `_handlers` (in `fusion_bridge.py`) MUST hold a reference to the `WorkQueueHandler` instance. If it gets garbage-collected, the `notify` method will never be called.
- `_get_roots()` is called fresh on each request because the active document can change between calls (user opens a different file).
- `object_store` persists for the lifetime of the add-in session. It is intentionally NOT cleared between requests because multi-step operations depend on referencing previously created objects (e.g., create a sketch, then add lines to it).
- `_make_serializable()` converts Fusion objects to descriptive strings. Fusion API objects are C++ wrappers and are not JSON-serializable. The string representation includes the object type and name/entityToken when available.
- The `$` prefix convention (e.g., `$sketch1`) is used in both `api_path` and `args` to reference stored objects. This is the primary mechanism for multi-step operations.
- `execute_python` gives the AI full Python execution inside Fusion. This is powerful but intentionally unrestricted -- the security boundary is the auth token + localhost binding, not code sandboxing.

---

## 4. Component 2: MCP Server (fusion_mcp_server)

### 4.1 File Structure

```
fusion_mcp_server/
    server.py           # FastMCP server with stdio transport
    fusion_client.py    # HTTP client that talks to the Fusion add-in
    requirements.txt    # Python package dependencies
    config.json         # Auth token + port (user fills in after Fusion starts)
```

This directory lives anywhere on the filesystem (e.g., the user's home directory or a project folder). It does NOT go in Fusion's add-in directory.

### 4.2 Requirements

File: `fusion_mcp_server/requirements.txt`

```
mcp[cli]>=1.0.0
```

This pulls in FastMCP, which provides the `mcp.server.fastmcp.FastMCP` class and the stdio transport. Install with:

```bash
pip install -r requirements.txt
```

### 4.3 Configuration

File: `fusion_mcp_server/config.json`

```json
{
    "host": "127.0.0.1",
    "port": 45876,
    "auth_token": "PASTE_TOKEN_FROM_FUSION_TEXT_COMMANDS_HERE"
}
```

The user updates `auth_token` each time Fusion restarts (the token is regenerated on each startup for security). The host and port should not be changed unless there is a conflict.

### 4.4 Fusion HTTP Client

File: `fusion_mcp_server/fusion_client.py`

```python
"""
HTTP client that communicates with the Fusion 360 add-in's bridge server.
Uses only urllib (stdlib) so it has no external dependencies of its own,
though the MCP server that imports this does use third-party packages.
"""

import urllib.request
import urllib.error
import json


class FusionClient:
    """Sends commands to the Fusion bridge HTTP server."""

    def __init__(self, host, port, token):
        self.url = f'http://{host}:{port}'
        self.token = token

    def call(self, payload):
        """
        Send a command to the Fusion bridge and return the response.

        Args:
            payload: dict with 'operation' and operation-specific fields

        Returns:
            str: JSON response from the bridge (success or error)

        Raises:
            ConnectionError: If the Fusion bridge is not running
        """
        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            self.url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                response_body = resp.read().decode('utf-8')
                return response_body
        except urllib.error.URLError as e:
            if 'Connection refused' in str(e):
                return json.dumps({
                    'success': False,
                    'error': 'Cannot connect to Fusion 360. Is Fusion running with the '
                             'fusion_bridge add-in active? Check the Add-Ins dialog.'
                })
            return json.dumps({
                'success': False,
                'error': f'HTTP error: {str(e)}'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            })

    def ping(self):
        """Check if the Fusion bridge is reachable."""
        return self.call({'operation': 'ping'})
```

### 4.5 MCP Server

File: `fusion_mcp_server/server.py`

```python
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
    print(f"ERROR: config.json not found at {config_path}", file=sys.stderr)
    print("Create config.json with: {\"host\": \"127.0.0.1\", \"port\": 45876, \"auth_token\": \"YOUR_TOKEN\"}", file=sys.stderr)
    sys.exit(1)

client = FusionClient(
    host=config.get('host', '127.0.0.1'),
    port=config.get('port', 45876),
    token=config['auth_token']
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
    name="fusion_ping",
    description="Check if the Fusion 360 bridge is running and reachable."
)
async def fusion_ping() -> str:
    """Health check for the Fusion bridge connection."""
    return client.ping()


# -- Entry point --

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

---

## 5. Security Requirements (Non-Negotiable)

These are hard requirements. Do not relax any of them.

| # | Requirement | Implementation |
|---|-------------|----------------|
| 1 | HTTP server binds to 127.0.0.1 ONLY | `HTTPServer(('127.0.0.1', 45876), ...)` -- never `0.0.0.0`, never a DNS name |
| 2 | Random auth token on each Fusion startup | `secrets.token_urlsafe(32)` in `fusion_bridge.py run()` |
| 3 | Token displayed in Fusion TEXT COMMANDS | `ui.palettes.itemById('TextCommands').writeText(...)` |
| 4 | Every HTTP request validates Bearer token | Check `Authorization` header in `do_POST` before any processing |
| 5 | No auto-updater | No phone-home, no update checks, no telemetry |
| 6 | No bundled high-level tools | Only raw API access + Python exec. The AI builds its own tool chains. |
| 7 | No external network calls | Everything stays on localhost. No DNS resolution needed. |
| 8 | No DNS tricks | Bind to IP `127.0.0.1` directly, not `localhost` (which could be remapped) |
| 9 | Fusion add-in uses ONLY stdlib | No pip installs into Fusion's Python. Only `http.server`, `json`, `threading`, `queue`, `secrets`, `traceback`, `io`, `sys`, `os`, `importlib` |
| 10 | MCP server is a separate process | Runs on system Python with its own pip environment |

**Why these matter:** The previous MCP server (AuraFriday's) bound to `0.0.0.0` (accessible from the network), had a hardcoded auth token, and included an auto-updater that could execute arbitrary code. Any one of those is a critical vulnerability. Our implementation avoids all of them.

---

## 6. Installation Steps

### Step 1: Install system Python (if not already present)

The MCP server needs Python 3.10 or later on the system PATH. This is separate from Fusion's bundled Python.

- **Windows:** Download from python.org or use `winget install Python.Python.3.12`
- **Mac:** `brew install python@3.12` or download from python.org

Verify: `python --version` (or `python3 --version`)

### Step 2: Install MCP SDK

```bash
pip install "mcp[cli]"
```

Or if using `pip3`:
```bash
pip3 install "mcp[cli]"
```

### Step 3: Place the Fusion add-in

Copy the entire `fusion_bridge/` directory to Fusion's add-in folder:

- **Windows:** `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`
- **Mac:** `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`

The final path should be:
- Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\fusion_bridge\fusion_bridge.py`
- Mac: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/fusion_bridge/fusion_bridge.py`

### Step 4: Place the MCP server

Put the `fusion_mcp_server/` directory anywhere convenient. For example:

```
~/fusion-mcp/fusion_mcp_server/server.py
```

### Step 5: Start the Fusion add-in

1. Open Fusion 360
2. Go to **Utilities** tab (or **Tools** depending on version) > **Add-Ins** (or press Shift+S)
3. In the **Add-Ins** tab, find `fusion_bridge`
4. Click **Run**
5. Open the **TEXT COMMANDS** panel (View > Text Commands, or the small `>>` icon at the bottom of the Fusion window)
6. Copy the auth token displayed there

If `fusion_bridge` does not appear in the list, the directory is in the wrong location or the directory name does not match the `.py` file name.

### Step 6: Configure the MCP server

Edit `fusion_mcp_server/config.json` and paste the token:

```json
{
    "host": "127.0.0.1",
    "port": 45876,
    "auth_token": "your-actual-token-here"
}
```

### Step 7: Configure Claude Code

Add to Claude Code's MCP settings. The location depends on the platform:

**For Claude Code CLI** (`~/.claude/settings.json` or project-level `.claude/settings.json`):

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "python3",
      "args": ["/absolute/path/to/fusion_mcp_server/server.py"],
      "env": {}
    }
  }
}
```

**For Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "python3",
      "args": ["/absolute/path/to/fusion_mcp_server/server.py"]
    }
  }
}
```

Replace `/absolute/path/to/` with the actual path. On Windows, use `python` instead of `python3` and use forward slashes or escaped backslashes in the path.

### Step 8: Test

Start a Claude Code session and ask it to create a simple box:

> "Create a 5cm x 3cm x 2cm box in Fusion 360."

Claude should use the `fusion_api` or `fusion_python` tools to create a sketch, draw a rectangle, and extrude it.

---

## 7. Claude Code Configuration

### MCP Server Entry

The minimal configuration needed:

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "python3",
      "args": ["/path/to/fusion_mcp_server/server.py"],
      "env": {}
    }
  }
}
```

Notes:
- Use the absolute path to `server.py`. Relative paths may not resolve correctly.
- On Windows, you may need to use `python` instead of `python3`.
- If Python is not on PATH, use the full path to the Python executable (e.g., `/usr/local/bin/python3`).
- The `env` dict can include `PYTHONPATH` if needed, but should be empty for most setups.

### Token Rotation Workflow

Because the auth token changes each time Fusion restarts:

1. Restart Fusion (or stop/start the add-in)
2. Copy the new token from TEXT COMMANDS
3. Update `config.json`
4. Restart Claude Code (or the MCP server process)

This is intentional security behavior. A persistent token would be a credential that could be stolen and reused.

### Recommended Companion: Context7 MCP Server

Context7 is a free MCP server that gives your AI agent live, up-to-date documentation for any library -- including the Fusion 360 API. It fills gaps in the static docs included in this package by pulling current API references on demand.

**Setup:** Add this to your Claude Code MCP configuration alongside the fusion360 entry:

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

Requires Node.js/npm installed. Once configured, your Claude Code can query Fusion API docs in real time when it needs a method signature, parameter type, or usage example that isn't covered in the static docs bundled with this package.

---

## 8. Common Fusion 360 API Patterns

These patterns are provided as reference for the AI agent. They demonstrate the most common operations and the correct API calling conventions. All measurements in Fusion's API are in **centimeters** by default.

### Create a Sketch on the XY Plane

```python
# Using fusion_python tool:
sketch = rootComponent.sketches.add(xyPlane)
store('sketch1', sketch)
print(f'Created sketch: {sketch.name}')
```

Or via sequential `fusion_api` calls:
```
fusion_api(api_path="rootComponent.sketches.add", args=["$xyPlane"], store_as="sketch1")
```

### Draw a Rectangle

```python
# Using fusion_python tool:
lines = sketch1.sketchCurves.sketchLines
p0 = adsk.core.Point3D.create(0, 0, 0)
p1 = adsk.core.Point3D.create(10, 0, 0)   # 10 cm
p2 = adsk.core.Point3D.create(10, 5, 0)   # 5 cm
p3 = adsk.core.Point3D.create(0, 5, 0)
lines.addByTwoPoints(p0, p1)
lines.addByTwoPoints(p1, p2)
lines.addByTwoPoints(p2, p3)
lines.addByTwoPoints(p3, p0)
print(f'Profiles: {sketch1.profiles.count}')
```

### Extrude a Profile

```python
profile = sketch1.profiles.item(0)
extrudes = rootComponent.features.extrudeFeatures
extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
distance = adsk.core.ValueInput.createByReal(2.0)  # 2 cm
extInput.setDistanceExtent(False, distance)
ext = extrudes.add(extInput)
store('extrude1', ext)
print(f'Extruded body: {ext.bodies.item(0).name}')
```

### Export to STL

```python
exportMgr = design.exportManager
body = rootComponent.bRepBodies.item(0)
stlOptions = exportMgr.createSTLExportOptions(body, '/path/to/output.stl')
stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
exportMgr.execute(stlOptions)
print('STL exported successfully')
```

### Add a Fillet

```python
fillets = rootComponent.features.filletFeatures
edges = adsk.core.ObjectCollection.create()
# Add edges from the extruded body
body = extrude1.bodies.item(0)
for edge in body.edges:
    edges.add(edge)
filletInput = fillets.createInput()
filletInput.addConstantRadiusEdgeSet(
    edges,
    adsk.core.ValueInput.createByReal(0.2),  # 0.2 cm = 2mm radius
    True
)
fillet = fillets.add(filletInput)
store('fillet1', fillet)
print(f'Filleted {edges.count} edges')
```

### Create a New Component

```python
occ = rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
newComp = occ.component
newComp.name = "MyComponent"
store('myComponent', newComp)
store('myOccurrence', occ)
print(f'Created component: {newComp.name}')
```

### Set a User Parameter

```python
params = design.userParameters
params.add('width', adsk.core.ValueInput.createByString('10 cm'), 'cm', 'Width of the part')
params.add('height', adsk.core.ValueInput.createByString('5 cm'), 'cm', 'Height of the part')
print(f'User parameters: {params.count}')
```

### Create a Circle and Extrude It

```python
sketch = rootComponent.sketches.add(xyPlane)
circles = sketch.sketchCurves.sketchCircles
center = adsk.core.Point3D.create(0, 0, 0)
circle = circles.addByCenterRadius(center, 3.0)  # 3 cm radius
store('circleSketch', sketch)

profile = sketch.profiles.item(0)
extrudes = rootComponent.features.extrudeFeatures
extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5.0))
ext = extrudes.add(extInput)
store('cylinder', ext)
print('Created cylinder')
```

### Boolean Operations (Cut / Join / Intersect)

```python
# Assuming body1 and body2 exist
combineFeatures = rootComponent.features.combineFeatures
toolBodies = adsk.core.ObjectCollection.create()
toolBodies.add(body2)

combineInput = combineFeatures.createInput(body1, toolBodies)
combineInput.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
# Other options: JoinFeatureOperation, IntersectFeatureOperation
combine = combineFeatures.add(combineInput)
print('Boolean cut completed')
```

### Mirror a Body

```python
mirrorFeatures = rootComponent.features.mirrorFeatures
inputEntities = adsk.core.ObjectCollection.create()
inputEntities.add(rootComponent.bRepBodies.item(0))

mirrorInput = mirrorFeatures.createInput(inputEntities, rootComponent.xZConstructionPlane)
mirrorInput.isCombine = False  # Create new body, don't merge
mirror = mirrorFeatures.add(mirrorInput)
print('Mirror completed')
```

### Pattern (Rectangular)

```python
rectangularPatterns = rootComponent.features.rectangularPatternFeatures
inputEntities = adsk.core.ObjectCollection.create()
inputEntities.add(rootComponent.bRepBodies.item(0))

patternInput = rectangularPatterns.createInput(
    inputEntities,
    rootComponent.xConstructionAxis,  # direction 1
    adsk.core.ValueInput.createByReal(3),  # count
    adsk.core.ValueInput.createByReal(5.0),  # spacing (5 cm)
    adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
)
pattern = rectangularPatterns.add(patternInput)
print('Rectangular pattern created')
```

### Save / Export the Design

```python
# Save (to Fusion cloud)
doc = app.activeDocument
doc.save('Auto-saved by MCP bridge')

# Export to F3D (archive)
exportMgr = design.exportManager
f3dOptions = exportMgr.createFusionArchiveExportOptions('/path/to/output.f3d')
exportMgr.execute(f3dOptions)

# Export to STEP
stepOptions = exportMgr.createSTEPExportOptions('/path/to/output.step')
exportMgr.execute(stepOptions)
print('Exported')
```

---

## 9. Testing and Verification

### Test 1: Bridge Health Check

After starting the add-in and configuring the MCP server, the simplest test is the ping tool:

> "Use fusion_ping to check if the Fusion bridge is reachable."

Expected: `{"success": true, "result": "pong"}`

### Test 2: Inspect the Root Component

> "Use fusion_inspect to see what's available on rootComponent."

Expected: A JSON response listing dozens of methods and properties (sketches, features, bRepBodies, occurrences, etc.).

### Test 3: Create a Simple Box

> "Create a 5cm x 3cm x 2cm box in Fusion 360."

The AI should:
1. Create a sketch on the XY plane
2. Draw a rectangle (5cm x 3cm)
3. Extrude it 2cm

### Test 4: Multi-Step Operation

> "Create a cylinder (2cm radius, 4cm tall), then fillet all top edges with 0.3cm radius."

This tests the object store (`store_as` / `$ref`) across multiple calls.

### Test 5: Python Execution

> "Run this code in Fusion: list all bodies in the root component and print their names and volumes."

Expected: The AI uses `fusion_python` with code that iterates `rootComponent.bRepBodies`.

---

## 10. Troubleshooting

### "Cannot connect to Fusion 360"

- Is Fusion running?
- Is the `fusion_bridge` add-in active? Check Add-Ins dialog (Shift+S).
- Is the port correct? Default is 45876. Check for port conflicts.
- Try: `curl -X POST http://127.0.0.1:45876 -H "Authorization: Bearer YOUR_TOKEN" -H "Content-Type: application/json" -d '{"operation":"ping"}'`

### "Unauthorized: invalid or missing Bearer token"

- The token in `config.json` does not match the token displayed in Fusion's TEXT COMMANDS.
- Did Fusion restart? A new token was generated. Copy the new one.

### "Root object is None. Is a design document open?"

- Fusion is running but no design is open, or the active document is not a Design (could be a Drawing or Animation workspace).
- Open or create a new design: File > New Design.

### "Timeout: main thread did not respond"

- Fusion's main thread is blocked. Common causes:
  - A modal dialog is open (e.g., save dialog, error dialog). Close it.
  - A long-running operation is in progress. Wait for it to finish.
  - The CustomEvent handler was garbage-collected (bug). Restart the add-in.

### Add-in does not appear in the Add-Ins list

- Verify the directory structure: `fusion_bridge/fusion_bridge.py` (directory name = file name without `.py`)
- Verify the manifest file: `fusion_bridge/fusion_bridge.manifest` (must be valid JSON)
- Restart Fusion after placing the files

### Python errors in the add-in

- Open TEXT COMMANDS panel in Fusion (View > Text Commands)
- Errors and tracebacks will appear there
- The add-in uses Fusion's bundled Python, which may differ from your system Python version

### Port already in use

- Another instance of the add-in (or another program) is using port 45876
- Change the port in both `bridge_server.py` (the `port` parameter in `start_server`) and `config.json`
- Or find and stop the conflicting process

---

## Appendix A: File Listing for the Builder

When building this project, create the following files:

```
fusion_bridge/
    fusion_bridge.py          # Section 3.3
    fusion_bridge.manifest    # Section 3.2
    bridge_server.py          # Section 3.4
    api_executor.py           # Section 3.5

fusion_mcp_server/
    server.py                 # Section 4.5
    fusion_client.py          # Section 4.4
    requirements.txt          # Section 4.2
    config.json               # Section 4.3
```

Total: 8 files across 2 directories.

## Appendix B: Key Design Decisions

1. **Why CustomEvent instead of adsk.doEvents() polling?** CustomEvent is the officially supported way to execute code on Fusion's main thread from a background thread. Polling with doEvents() is unreliable and can cause Fusion to hang.

2. **Why HTTP instead of a Unix socket or named pipe?** HTTP is the simplest protocol that works cross-platform (Windows + Mac) using only Python's stdlib. Unix sockets are not available on Windows. Named pipes have different APIs on each platform.

3. **Why random token instead of a config file shared secret?** A random token generated at runtime means there is no persistent credential on disk that could be stolen. The user must explicitly copy it after each Fusion start, which is a mild inconvenience but a significant security improvement.

4. **Why port 45876?** Arbitrary high port in the ephemeral range. Unlikely to conflict with common services. The exact number does not matter as long as both sides agree.

5. **Why `_make_serializable()` instead of returning raw objects?** Fusion API objects are C++ wrappers managed by Fusion's runtime. They cannot be pickled, JSON-serialized, or passed across process boundaries. Converting them to descriptive strings is the only reliable approach. The `object_store` keeps the actual objects in-process for subsequent API calls.

6. **Why `store_as` / `$ref` pattern?** Multi-step CAD operations are the norm. You create a sketch, then add curves to it, then extrude a profile from it. Each step needs a reference to the previous result. The `$ref` convention lets the AI chain operations naturally without the MCP server needing to understand Fusion's object model.

7. **Why no sandboxing on `python_exec`?** The security boundary is the auth token and localhost binding, not code sandboxing. If an attacker can send authenticated HTTP requests to localhost, they already have local code execution. Restricting `exec()` would add complexity without meaningful security improvement, while making legitimate operations harder.

---

*End of build guide. An AI coding agent reading this document has everything needed to create both the Fusion add-in and the MCP server from scratch.*
