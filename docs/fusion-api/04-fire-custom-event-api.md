# Fusion 360 API - Application.fireCustomEvent Method

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Application_fireCustomEvent.htm

## Overview

The `fireCustomEvent` method belongs to the `Application` object and is used to fire a previously registered custom event. This enables communication between worker threads (or other add-ins) and the primary Fusion thread.

**Critical behavior:** Firing a custom event does NOT immediately result in the event handler being called. Instead, the event is queued and processed when Fusion becomes idle.

## Namespace

`adsk::core`

## Method Signature

### Python

```python
returnValue = app.fireCustomEvent(eventId)
returnValue = app.fireCustomEvent(eventId, additionalInfo)
```

### C++

```cpp
returnValue = app->fireCustomEvent(eventId);
returnValue = app->fireCustomEvent(eventId, additionalInfo);
```

## Parameters

| Name | Type | Description |
|------|------|-------------|
| `eventId` | `string` | The unique ID string of the custom event to fire. Must match the ID used in `registerCustomEvent()`. |
| `additionalInfo` | `string` | Optional. Additional information passed to the event handler via `args.additionalInfo`. Default: `""`. Use JSON encoding for structured data. |

## Return Value

| Type | Description |
|------|-------------|
| `boolean` | Returns `True` if the event was successfully added to the event queue. A `True` return indicates successful queueing, NOT that the event has been executed. |

## Related Methods

### registerCustomEvent

```python
customEvent = app.registerCustomEvent('MyCustomEventId')
```

Registers a new custom event with the given ID. Returns a `CustomEvent` object that you can attach handlers to.

### unregisterCustomEvent

```python
app.unregisterCustomEvent('MyCustomEventId')
```

Unregisters a previously registered custom event. Call this during cleanup (in `stop()` function).

## CustomEventHandler Class

```python
class MyHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # args is a CustomEventArgs object
        # args.additionalInfo - the string passed to fireCustomEvent
        # args.firingEvent - the CustomEvent object
        data = json.loads(args.additionalInfo)
```

## Usage Pattern

```python
import adsk.core, json

app = adsk.core.Application.get()

# 1. Register
event = app.registerCustomEvent('com.mycompany.myevent')

# 2. Connect handler
handler = MyHandler()
event.add(handler)

# 3. Fire (safe from any thread)
app.fireCustomEvent('com.mycompany.myevent', json.dumps({'key': 'value'}))

# 4. Cleanup
event.remove(handler)
app.unregisterCustomEvent('com.mycompany.myevent')
```

## Thread Safety

- `fireCustomEvent()` is the ONLY Fusion API method safe to call from a background thread
- The handler's `notify()` method always executes on the main Fusion thread
- Events are queued, so there may be a small delay between firing and handling

## Version

Introduced in January 2017
