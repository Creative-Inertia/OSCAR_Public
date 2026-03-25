# Fusion 360 API - Python-Specific Issues

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonSpecific_UM.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Fusion provides a unified API accessible from Python or C++. While syntax differs between languages, certain functionality requires substantially different approaches in Python due to language constraints.

## Python Version

As of January 2026, Fusion 360 uses **Python 3.14**. Previous versions used Python 3.12. Pre-compiled `.pyc` files are tied to the minor version and must be recompiled when the Python version changes. Source-based add-ins (`.py` files) are unaffected.

## Creating Add-Ins with Python

Use the "Create" button in the Scripts and Add-Ins dialog, select Python as the programming language. The system generates a complete add-in framework ready for immediate execution.

## Editing and Debugging

- **IDE**: VS Code serves as the integrated development environment
- **Debug Extension**: `ms-python.python` extension required (auto-installs on first use)
- **Breakpoints**: Click left edge of code window
- **Debug Controls**: Run menu or F5
  - Continue execution until next breakpoint
  - Step over function calls line-by-line
  - Step into functions
  - Step out of current functions
  - Disconnect debugging sessions
- **Variable Inspection**: VARIABLES pane displays current values; WATCH pane tracks specific variables
- **Add-In Debugging**: Uncheck "Run on Startup" before debugging; use "Stop" button to halt running instances

## Reference Arguments (Out Parameters)

**Python does not support output or 'by reference' arguments.** When methods have out parameters, Python returns them as tuples.

```python
# Method with out parameters returns a tuple
(retVal, x, y, z) = point.getData()
```

The tuple's first value is always the documented return value, with subsequent values representing out arguments in their original order.

### Common Example Patterns

```python
# Getting point coordinates
(retVal, x, y, z) = point.getData()

# Getting surface normal at a parameter
(retVal, normal) = surfEval.getNormalAtParameter(paramPoint)

# Getting point at parameter
(retVal, positionPoint) = surfEval.getPointAtParameter(paramPoint)

# Getting curve end points
(retVal, startPt, endPt) = curveEval.getEndPoints()
```

## Working with Collections and Arrays

Collections support standard Python iteration syntax:

```python
# Standard iteration
for item in col:
    process(item)

# Length function
count = len(col)

# Index access
first = col[0]        # First item
last = col[-1]        # Last item
first_two = col[:2]   # First two items
last_two = col[-2:]   # Last two items
middle = col[1:4]     # Second through fourth items
```

### Arrays and Vectors

When methods return arrays, they return special "vector" objects rather than standard Python lists. Convert to standard lists:

```python
curves = skText.explode()
curvesList = list(curves)
```

## Object Types

### Type Checking (Exact Type)

```python
if type(selObj) is adsk.fusion.SketchLine:
    print("SketchLine is selected.")
```

### Inheritance Checking

```python
if isinstance(selObj, adsk.fusion.SketchEntity):
    print("Is some kind of sketch entity.")
```

**Note:** `type()` fails for inheritance hierarchies. Use `isinstance()` for derived class detection.

## Object Equality

```python
# CORRECT: Use == for comparing Fusion objects
if face1 == face2:
    print("Faces are the same")

# WRONG: Do NOT use 'is' for Fusion objects
# if face1 is face2:  # This will NOT work correctly
```

The Python `is` identity operator cannot compare Fusion objects; always use `==`.

## Type Hints and Cast

### Type Hints (Python 3.5+)

```python
# Variable type hint
des: adsk.fusion.Design = app.activeProduct

# Function type hints
def CheckIfHollow(body: adsk.fusion.BRepBody) -> bool:
    if body.shells.count > 1:
        return True
    else:
        return False
```

Type hints inform the IDE without runtime validation. Invalid types won't raise errors but will fail during execution.

### Cast Function

Returns `None` if the type doesn't match - useful for safe type conversion:

```python
edge = adsk.fusion.BRepEdge.cast(sels[0].entity)
if not edge:
    ui.messageBox('An edge was not selected.')
    return

# Common cast patterns
design = adsk.fusion.Design.cast(app.activeProduct)
cam = adsk.cam.CAM.cast(app.activeProduct)
```

## Additional Python Modules

**Instead of installing via pip or adding to sys.path, bundle modules locally with your script/add-in.**

Recommended directory structure:

```
MyScript/
├── MyScript.py
└── Modules/
    └── xlrd/
        └── ...
```

Reference using relative import:

```python
from .Modules import xlrd
```

## Threading Constraints (CRITICAL)

**Python runs within the Fusion process and also runs in the main Fusion thread.** During script execution, most Fusion interface elements appear frozen because the main thread cannot process system messages.

### Key Rules

1. All Fusion API calls MUST happen on the main thread
2. Background threads should NEVER call Fusion API functions
3. Use Custom Events to communicate from background threads to main thread
4. Do NOT use `doEvents()` in long-running loops - it will crash Fusion

### doEvents Function

`adsk.doEvents()` temporarily pauses execution and allows Fusion to handle queued messages. Use for:

- Real-time display updates during modeling
- Camera manipulation and visualization
- Progress indication to users

```python
def copyOccurrence():
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        occ = adsk.fusion.Occurrence.cast(
            ui.selectEntity('Select an occurrence', 'Occurrences').entity
        )
        if occ:
            root = app.activeProduct.rootComponent
            comp = occ.component
            trans = occ.transform
            offset = trans.getCell(0, 3)
            for i in range(0, 100):
                offset += 5
                trans.setCell(0, 3, offset)
                root.occurrences.addExistingComponent(comp, trans)
                adsk.doEvents()  # Allow UI to update
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

Without `doEvents()` calls, graphics remain static until program completion, despite successful model modifications occurring in the background.

## Event Handlers in Python

Python event handlers MUST be kept in a global list to prevent garbage collection:

```python
handlers = []  # Global list to prevent garbage collection

class MyEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Handle event
        pass

# Connect handler
handler = MyEventHandler()
event.add(handler)
handlers.append(handler)  # CRITICAL: prevent garbage collection
```

## autoTerminate

For scripts that create commands with dialogs:

```python
def run(context):
    # ... create command and dialog ...
    buttonSample.execute()
    adsk.autoTerminate(False)  # Keep script running until command completes

# In execute handler:
def notify(self, args):
    # ... do work ...
    adsk.terminate()  # Signal script is done
```
