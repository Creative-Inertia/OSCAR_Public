# Fusion 360 API - Custom Event Threading Pattern

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomEventSample_Sample.htm
> Also: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Threading_UM.htm

## Overview

This is THE critical pattern for building an MCP server that communicates with Fusion 360. It demonstrates how a background thread can safely communicate with Fusion's main thread using custom events.

**Key Principle:** Fusion 360 is single-threaded. All API calls MUST happen on the main thread. Background threads communicate with the main thread by firing custom events that get queued and processed when Fusion is idle.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Fusion 360 Main Thread                         │
│  ┌───────────────────────────────────────────┐  │
│  │  Event Queue                              │  │
│  │  [Custom Event] → ThreadEventHandler      │  │
│  │    → Modify model / read data / respond   │  │
│  └───────────────────────────────────────────┘  │
│           ▲                                     │
│           │ fireCustomEvent(id, json_data)      │
│  ┌────────┴──────────────────────────────────┐  │
│  │  Background Worker Thread                 │  │
│  │  (Python threading.Thread)                │  │
│  │  - NO Fusion API calls allowed here       │  │
│  │  - Only fireCustomEvent() is safe         │  │
│  │  - Can do: network I/O, file I/O, compute │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Complete Working Code

This is a complete add-in that modifies a model parameter every 2 seconds from a background thread:

```python
import adsk.core, adsk.fusion, adsk.cam, traceback
import threading, random, json

app = None
ui = adsk.core.UserInterface.cast(None)
handlers = []
stopFlag = None
myCustomEvent = 'MyCustomEventId'
customEvent = None


class ThreadEventHandler(adsk.core.CustomEventHandler):
    """Event handler that runs on the MAIN THREAD when custom event fires.
    This is where ALL Fusion API calls must happen."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            # Make sure a command isn't running before changes are made.
            # This is important - if a command dialog is open, modifying
            # the model will fail or cause issues.
            if ui.activeCommand != 'SelectCommand':
                ui.commandDefinitions.itemById('SelectCommand').execute()

            # Get the value from the JSON data passed through the event.
            eventArgs = json.loads(args.additionalInfo)
            newValue = float(eventArgs['Value'])

            # Set the parameter value.
            # ALL Fusion API work happens here, on the main thread.
            design = adsk.fusion.Design.cast(app.activeProduct)
            param = design.rootComponent.modelParameters.itemByName('Length')
            param.value = newValue
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            adsk.autoTerminate(False)


class MyThread(threading.Thread):
    """Background worker thread.
    NEVER call Fusion API here except fireCustomEvent()."""
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        # Every two seconds fire a custom event, passing a random number.
        while not self.stopped.wait(2):
            args = {'Value': random.randint(1000, 10000) / 1000}
            app.fireCustomEvent(myCustomEvent, json.dumps(args))


def run(context):
    """Called when the add-in is loaded."""
    global ui, app
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Step 1: Register the custom event and connect the handler.
        global customEvent
        customEvent = app.registerCustomEvent(myCustomEvent)
        onThreadEvent = ThreadEventHandler()
        customEvent.add(onThreadEvent)
        handlers.append(onThreadEvent)  # Prevent garbage collection

        # Step 2: Create and start the background thread.
        global stopFlag
        stopFlag = threading.Event()
        myThread = MyThread(stopFlag)
        myThread.start()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    """Called when the add-in is unloaded."""
    try:
        if handlers.count:
            customEvent.remove(handlers[0])
        stopFlag.set()  # Signal the thread to stop
        app.unregisterCustomEvent(myCustomEvent)
        ui.messageBox('Stop addin')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

## Key Implementation Details

### 1. Event Registration

```python
# Register with a unique string ID
customEvent = app.registerCustomEvent('MyUniqueEventId')

# Connect handler
handler = ThreadEventHandler()
customEvent.add(handler)
handlers.append(handler)  # MUST keep reference to prevent GC
```

### 2. Firing Events from Background Thread

```python
# Only safe Fusion API call from background thread
app.fireCustomEvent('MyUniqueEventId', json.dumps(data))
```

- `fireCustomEvent()` does NOT immediately execute the handler
- The event is **queued** and processed when Fusion becomes idle
- Returns `True` if successfully queued
- The `additionalInfo` parameter is a string (use JSON for structured data)

### 3. Handling Events on Main Thread

```python
class ThreadEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # args.additionalInfo contains the string passed to fireCustomEvent
        data = json.loads(args.additionalInfo)
        # Now safe to call ANY Fusion API
```

### 4. Pre-Modification Safety Check

Before modifying the model, ensure no command dialog is active:

```python
if ui.activeCommand != 'SelectCommand':
    ui.commandDefinitions.itemById('SelectCommand').execute()
```

### 5. Cleanup

```python
def stop(context):
    stopFlag.set()                              # Stop the thread
    customEvent.remove(handlers[0])             # Remove handler
    app.unregisterCustomEvent('MyUniqueEventId')  # Unregister event
```

## Threading Rules Summary

| Thread | Can Do | Cannot Do |
|--------|--------|-----------|
| **Main Thread** | All Fusion API calls, UI operations, model modifications | Long-running blocking operations (freezes UI) |
| **Background Thread** | Network I/O, file I/O, computation, `fireCustomEvent()` | ANY other Fusion API call (will crash) |

## MCP Server Application Pattern

For an MCP server controlling Fusion 360, the pattern would be:

```
MCP Server (background thread)
  ↓ receives command from client
  ↓ fireCustomEvent('mcp_command', json.dumps({action: 'create_sketch', params: {...}}))

Fusion Main Thread (event handler)
  ↓ receives custom event
  ↓ parses command JSON
  ↓ executes Fusion API calls
  ↓ puts result in shared data structure
  ↓ fires response event or sets threading.Event

MCP Server (background thread)
  ↓ reads result from shared data structure
  ↓ returns response to client
```

### Bidirectional Communication Pattern

```python
import threading, json, queue

# Shared response queue
response_queue = queue.Queue()

class FusionCommandHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = json.loads(args.additionalInfo)
            result = execute_fusion_command(command)
            response_queue.put(json.dumps(result))
        except Exception as e:
            response_queue.put(json.dumps({'error': str(e)}))

class MCPServerThread(threading.Thread):
    def __init__(self, stop_event):
        threading.Thread.__init__(self)
        self.stopped = stop_event

    def run(self):
        # Start MCP server, listen for commands
        while not self.stopped.is_set():
            command = wait_for_mcp_command()  # Your MCP protocol handling
            app.fireCustomEvent('mcp_command', json.dumps(command))

            # Wait for response from main thread
            try:
                response = response_queue.get(timeout=30)
                send_mcp_response(response)
            except queue.Empty:
                send_mcp_response(json.dumps({'error': 'timeout'}))
```

## Critical Warnings

1. **Never call `messageBox()` from a background thread** - it can crash Fusion
2. **Never modify the model from a background thread** - undefined behavior / crash
3. **`doEvents()` in long-running loops will eventually crash Fusion** - use custom events instead
4. **Keep handler references in a global list** - Python garbage collection will destroy them otherwise
5. **Custom events are queued, not immediate** - there is a small delay between firing and handling
6. **Multiple add-ins can fire each other's custom events** if they know the event ID
