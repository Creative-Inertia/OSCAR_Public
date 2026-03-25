# Fusion 360 API - Events and Commands System

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Events_UM.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Commands_UM.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Events Overview

Events allow receiving notifications when specific actions occur within Fusion. They are crucial for custom commands and add-in interactivity.

### Event Pattern (3 Steps)

1. **Access the event** through a property on the supporting object
2. **Create a handler** (class inheriting from appropriate EventHandler)
3. **Connect the handler** using the event's `add()` method

### Handler Pattern (Python)

```python
handlers = []  # GLOBAL list to prevent garbage collection

class MyHandler(adsk.core.SomeEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # args is derived from EventArgs
        # args.firingEvent - the event object
        # Additional event-specific properties
        pass

# Connect
handler = MyHandler()
event.add(handler)
handlers.append(handler)  # CRITICAL: prevent GC

# Disconnect
event.remove(handler)
```

## Command System

A command represents a complete user action: button click -> dialog -> preview -> execute -> undo-able result.

### Command Lifecycle

```
User clicks button
    → CommandCreated event
        → Create dialog inputs
        → Connect command events
    → User interacts with dialog
        → InputChanged events
        → ValidateInputs events
        → ExecutePreview events (previews)
    → User clicks OK
        → Execute event (all changes = single undo)
    → Command terminates
        → Destroy event
```

### Creating a Command (Add-In)

```python
import adsk.core, adsk.fusion, traceback

handlers = []

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    cmdDefs = ui.commandDefinitions

    # Create command definition
    buttonSample = cmdDefs.addButtonDefinition(
        'MyButtonDefIdPython',
        'Python Sample Button',
        'Sample button tooltip',
        './Resources/Sample'  # Icon folder
    )

    # Connect commandCreated event
    sampleCreated = SampleCommandCreatedHandler()
    buttonSample.commandCreated.add(sampleCreated)
    handlers.append(sampleCreated)

    # Add to UI panel
    addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
    buttonControl = addInsPanel.controls.addCommand(buttonSample)
    buttonControl.isPromotedByDefault = True
    buttonControl.isPromoted = True


class SampleCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        cmd = adsk.core.CommandCreatedEventArgs.cast(args).command
        inputs = cmd.commandInputs

        # Create dialog inputs
        inputs.addBoolValueInput('equilateral', 'Equilateral', True, '', False)

        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)
        defaultUnits = des.unitsManager.defaultLengthUnits
        minVal = des.unitsManager.convert(1, defaultUnits, 'cm')
        maxVal = des.unitsManager.convert(10, defaultUnits, 'cm')
        inputs.addFloatSliderCommandInput(
            'baseLength', 'Base Length', defaultUnits, minVal, maxVal, False
        )

        inputs.addValueInput(
            'heightScale', 'Height Scale', '',
            adsk.core.ValueInput.createByReal(0.75)
        )

        # Connect command events
        onExecute = SampleExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

        onInputChanged = SampleInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)

        onValidate = SampleValidateHandler()
        cmd.validateInputs.add(onValidate)
        handlers.append(onValidate)

        onPreview = SamplePreviewHandler()
        cmd.executePreview.add(onPreview)
        handlers.append(onPreview)

        onDestroy = SampleDestroyHandler()
        cmd.destroy.add(onDestroy)
        handlers.append(onDestroy)


class SampleExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # All model changes here are grouped into ONE undo operation
        inputs = args.command.commandInputs
        # Read inputs and perform operations
        pass


class SampleInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        changedInput = adsk.core.InputChangedEventArgs.cast(args).input
        inputs = args.firingEvent.sender.commandInputs
        # Modify UI (toggle visibility, etc.) - do NOT modify model here
        if changedInput.id == 'equilateral':
            scaleInput = inputs.itemById('heightScale')
            scaleInput.isVisible = not changedInput.value


class SampleValidateHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
        inputs = eventArgs.firingEvent.sender.commandInputs
        # Set areInputsValid to control OK button
        eventArgs.areInputsValid = True


class SamplePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # Show preview of result
        # Set isValidResult = True to use preview as final result
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        eventArgs.isValidResult = True  # Skip execute, use preview


class SampleDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # Cleanup
        pass


def stop(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    # Delete command definition
    cmdDef = ui.commandDefinitions.itemById('MyButtonDefIdPython')
    if cmdDef:
        cmdDef.deleteMe()

    # Delete button control
    addinsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
    cntrl = addinsPanel.controls.itemById('MyButtonDefIdPython')
    if cntrl:
        cntrl.deleteMe()
```

## Command Events Reference

| Event | Handler Type | When Fired |
|-------|-------------|-----------|
| `commandCreated` | CommandCreatedEventHandler | Button clicked; create inputs & connect events |
| `execute` | CommandEventHandler | User clicks OK; perform main work |
| `executePreview` | CommandEventHandler | Input changes; show preview |
| `inputChanged` | InputChangedEventHandler | Any input value changes |
| `validateInputs` | ValidateInputsEventHandler | Check if inputs are valid (controls OK button) |
| `activate` | CommandEventHandler | Command becomes active |
| `deactivate` | CommandEventHandler | Command temporarily deactivated |
| `destroy` | CommandEventHandler | Command terminates (OK, Cancel, or forced) |
| `select` | SelectionEventHandler | Entity selection filtering |
| `mouseClick` | MouseEventHandler | Mouse click in viewport |

## Command Input Types

| Method | Creates | Description |
|--------|---------|-------------|
| `addBoolValueInput(id, name, isCheckbox, resourceFolder, initialValue)` | Checkbox | Boolean input |
| `addValueInput(id, name, units, initialValue)` | Value field | Numeric with units |
| `addStringValueInput(id, name, initialValue)` | Text field | String input |
| `addIntegerSpinnerCommandInput(id, name, min, max, step, initialValue)` | Spinner | Integer value |
| `addFloatSpinnerCommandInput(id, name, units, min, max, step, initialValue)` | Spinner | Float value with units |
| `addFloatSliderCommandInput(id, name, units, min, max, hasText)` | Slider | Float range |
| `addSelectionInput(id, name, tooltip)` | Selection | Entity picking from viewport |
| `addDropDownCommandInput(id, name, style)` | Dropdown | List selection |
| `addRadioButtonGroupCommandInput(id, name)` | Radio buttons | Single selection |
| `addButtonRowCommandInput(id, name, isCheckBox)` | Button row | Multiple buttons |
| `addTextBoxCommandInput(id, name, text, rows, isReadOnly)` | Text box | Multi-line text |
| `addImageCommandInput(id, name, resourceFolder)` | Image | Display image |
| `addGroupCommandInput(id, name)` | Group | Container for other inputs |
| `addTabCommandInput(id, name)` | Tab | Tabbed interface |
| `addTableCommandInput(id, name, columns, rows)` | Table | Grid layout |
| `addDirectionCommandInput(id, name)` | Direction | Direction picker |
| `addDistanceValueCommandInput(id, name, initialValue)` | Distance | On-canvas manipulator |
| `addAngleValueCommandInput(id, name, initialValue)` | Angle | On-canvas angle manipulator |

### Selection Input Filters

```python
selInput = inputs.addSelectionInput('selection', 'Select', 'Select entity')
selInput.addSelectionFilter('PlanarFaces')
selInput.addSelectionFilter('Edges')
selInput.setSelectionLimits(1, 1)  # min=1, max=1

# Common filters
# 'Bodies', 'SolidBodies', 'SurfaceBodies', 'MeshBodies'
# 'Faces', 'PlanarFaces', 'CylindricalFaces', 'SphericalFaces'
# 'Edges', 'LinearEdges', 'CircularEdges'
# 'Vertices'
# 'SketchCurves', 'SketchLines', 'SketchCircles'
# 'Profiles'
# 'ConstructionPlanes', 'ConstructionAxes', 'ConstructionPoints'
# 'Occurrences', 'RootComponents'
# 'JointOrigins', 'Joints'
```

## UI Customization

### Toolbar Structure

```
Application
  └── Workspaces (Design, Manufacturing, etc.)
       └── Toolbar Tabs (SOLID, SURFACE, MESH, etc.)
            └── Toolbar Panels (Create, Modify, etc.)
                 └── Controls (buttons, dropdowns)
```

### Common Workspace/Panel IDs

| Workspace | ID |
|-----------|-----|
| Design | `FusionSolidEnvironment` |
| Manufacturing | `CAMEnvironment` |

| Panel | ID |
|-------|-----|
| Scripts/Add-Ins | `SolidScriptsAddinsPanel` |
| Create | `SolidCreatePanel` |
| Modify | `SolidModifyPanel` |
| Construct | `ConstructPanel` |

### Creating Drop-Down Controls

```python
# Get panel
panel = workspace.toolbarPanels.itemById('SolidCreatePanel')

# Add dropdown
dropdown = panel.controls.addDropDown('My Tools', '', 'myDropdownId')
dropdown.controls.addCommand(cmdDef1)
dropdown.controls.addCommand(cmdDef2)
dropdown.controls.addSeparator()
dropdown.controls.addCommand(cmdDef3)
```

### Icon Requirements

Icons go in a `resources/` folder. Required files:

| File | Size | Purpose |
|------|------|---------|
| `16x16.png` or `.svg` | 16x16 | Small icon (standard) |
| `16x16@2x.png` | 32x32 | Small icon (high DPI) |
| `32x32.png` or `.svg` | 32x32 | Large icon (standard) |
| `64x64.png` or `.svg` | 64x64 | Large icon (high DPI) |

SVG (Tiny 1.2 profile) preferred over PNG for scalability.

## Custom Events (Cross-Thread)

See `03-custom-event-threading.md` for complete details. Quick reference:

```python
# Register
event = app.registerCustomEvent('myEventId')
handler = MyCustomHandler()
event.add(handler)

# Fire (safe from any thread)
app.fireCustomEvent('myEventId', json.dumps(data))

# Unregister
event.remove(handler)
app.unregisterCustomEvent('myEventId')
```

## Application Events

| Event | Description |
|-------|-------------|
| `app.documentOpened` | Document opened |
| `app.documentCreated` | New document created |
| `app.documentSaving` | Document about to save |
| `app.documentSaved` | Document saved |
| `app.documentClosing` | Document about to close |
| `app.documentActivated` | Document became active |
| `ui.activeSelectionChanged` | Selection changed |
| `ui.commandStarting` | Command about to start |
| `ui.commandTerminated` | Command finished |

## Script with Command (Programmatic Execution)

```python
def run(context):
    # Create command definition
    cmdDef = ui.commandDefinitions.addButtonDefinition(
        'ScriptCmdId', 'My Command', 'tooltip'
    )

    handler = MyCreatedHandler()
    cmdDef.commandCreated.add(handler)
    handlers.append(handler)

    # Execute programmatically (no button click needed)
    cmdDef.execute()
    adsk.autoTerminate(False)  # Keep script alive

# In execute handler:
class MyExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        # Do work...
        adsk.terminate()  # Signal script done
```
