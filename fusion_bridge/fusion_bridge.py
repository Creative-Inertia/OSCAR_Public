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

__version__ = '0.3.0'

# Keep references alive for the lifetime of the add-in.
# If these get garbage-collected, Fusion will crash or silently stop firing events.
_handlers = []
_stop_event = threading.Event()
_server_thread = None
_custom_event_id = 'SecureFusionMCPBridge'


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

        # -- Generate auth token and write to shared file --
        token = secrets.token_urlsafe(32)

        token_dir = os.path.join(os.path.expanduser('~'), '.fusion_mcp')
        os.makedirs(token_dir, exist_ok=True)
        token_path = os.path.join(token_dir, 'auth_token')
        with open(token_path, 'w') as f:
            f.write(token)

        text_palette = ui.palettes.itemById('TextCommands')
        if text_palette:
            text_palette.writeText('=' * 60)
            text_palette.writeText(f'FUSION MCP BRIDGE v{__version__} - STARTED')
            text_palette.writeText(f'Auth token written to: {token_path}')
            text_palette.writeText('The MCP server reads this automatically.')
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
