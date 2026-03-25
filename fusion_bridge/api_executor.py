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

# Document pinning: when set, all operations target this specific document
# regardless of which tab the user switches to in the Fusion UI.
_pinned_document = None   # adsk.core.Document or None
_pinned_design = None     # adsk.fusion.Design or None


def pin_document():
    """
    Pin the currently active document so all subsequent operations target it,
    even if the user switches tabs. Returns the pinned document name.
    """
    global _pinned_document, _pinned_design
    app = adsk.core.Application.get()
    _pinned_document = app.activeDocument
    _pinned_design = adsk.fusion.Design.cast(app.activeProduct)
    name = _pinned_document.name if _pinned_document else '(none)'
    return {'success': True, 'result': f'Pinned to document: {name}'}


def unpin_document():
    """
    Unpin the document, returning to default behavior of targeting
    whichever document is currently active.
    """
    global _pinned_document, _pinned_design
    _pinned_document = None
    _pinned_design = None
    return {'success': True, 'result': 'Unpinned. Operations will target the active document.'}


def get_pin_status():
    """Return the current pin state."""
    if _pinned_document and _pinned_document.isValid:
        return {'success': True, 'pinned': True, 'document': _pinned_document.name}
    elif _pinned_document and not _pinned_document.isValid:
        # Document was closed — auto-unpin
        unpin_document()
        return {'success': True, 'pinned': False, 'document': None,
                'warning': 'Previously pinned document was closed. Auto-unpinned.'}
    return {'success': True, 'pinned': False, 'document': None}


def capture_viewport(filepath=None, width=1920, height=1080):
    """
    Capture the current Fusion 360 viewport to an image file.
    Returns the file path so Claude can read the image.
    """
    import os
    import time

    app = adsk.core.Application.get()

    # Default filepath if none provided
    if not filepath:
        capture_dir = os.path.join(os.path.expanduser('~'), '.fusion_captures')
        os.makedirs(capture_dir, exist_ok=True)
        timestamp = int(time.time())
        filepath = os.path.join(capture_dir, f'viewport_{timestamp}.png')

    try:
        # saveAsImageFile is on the Viewport object
        viewport = app.activeViewport
        success = viewport.saveAsImageFile(filepath, width, height)
        if success:
            return {
                'success': True,
                'filepath': filepath,
                'width': width,
                'height': height,
                'result': f'Viewport captured to {filepath}'
            }
        else:
            return {'success': False, 'error': 'saveAsImageFile returned False'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _get_roots():
    """
    Get the Fusion application roots for the target document.

    If a document is pinned, activates it first (bringing it back to the
    foreground) so the Fusion API operates on the correct document. If no
    document is pinned, uses whatever is currently active.
    """
    global _pinned_document, _pinned_design
    app = adsk.core.Application.get()

    # If we have a pinned document, make sure we're operating on it
    if _pinned_document is not None:
        if not _pinned_document.isValid:
            # Pinned document was closed — fall back to active
            _pinned_document = None
            _pinned_design = None
        elif app.activeDocument != _pinned_document:
            # User switched tabs — activate the pinned document
            _pinned_document.activate()

    if _pinned_design and _pinned_design.isValid:
        design = _pinned_design
    else:
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
                elif operation == 'pin_document':
                    result = pin_document()
                elif operation == 'unpin_document':
                    result = unpin_document()
                elif operation == 'pin_status':
                    result = get_pin_status()
                elif operation == 'capture_viewport':
                    result = capture_viewport(
                        payload.get('filepath'),
                        payload.get('width', 1920),
                        payload.get('height', 1080)
                    )
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
