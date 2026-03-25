# Fusion 360 API - Python Add-In Template

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonTemplate_UM.htm

## Overview

The Python Add-In Template provides the recommended architecture for building Fusion 360 add-ins. It demonstrates the bare minimum functionality through `run()` and `stop()` functions, plus a modular command architecture.

## Template Folder Structure

```
MyFirstAddIn/
├── config.py                    # Global variables
├── MyFirstAddIn.py              # Main entry point
├── MyFirstAddIn.manifest        # Metadata
├── lib/
│   ├── event_utils.py           # Event handling helpers
│   ├── general_utils.py         # General utilities
│   └── fusion360utils.py        # Main utility library (imported as futil)
└── commands/
    ├── __init__.py              # Command registry
    ├── commandDialog/
    │   ├── __init__.py
    │   ├── entry.py             # Command definition & event handlers
    │   └── resources/           # Icons (16x16, 32x32, etc.)
    ├── paletteShow/
    │   ├── __init__.py
    │   ├── entry.py
    │   └── resources/
    └── paletteSend/
        ├── __init__.py
        ├── entry.py
        └── resources/
```

## Core Files

### Main Entry Point (MyFirstAddIn.py)

```python
from . import commands
from .lib import fusion360utils as futil

def run(context):
    try:
        # This will run the start function in each of your
        # commands as defined in commands/__init__.py
        commands.start()
    except:
        futil.handle_error('run')

def stop(context):
    try:
        # Remove all of the event handlers your app has created.
        futil.clear_handlers()

        # This will run the stop function in each of your
        # commands as defined in commands/__init__.py
        commands.stop()
    except:
        futil.handle_error('stop')
```

### config.py (Global Variables)

```python
import os

# Flag for Debug mode - more info written to Text Command window
DEBUG = True

# Gets the name of the add-in from the folder name
ADDIN_NAME = os.path.basename(os.path.dirname(__file__))
COMPANY_NAME = 'ACME'

# Palettes
sample_palette_id = f'{COMPANY_NAME}_{ADDIN_NAME}_palette_id'
```

### commands/__init__.py (Command Registry)

```python
from .commandDialog import entry as commandDialog
from .paletteShow import entry as paletteShow
from .paletteSend import entry as paletteSend

# Add imported modules to this list
commands = [
    commandDialog,
    paletteShow,
    paletteSend
]

def start():
    for command in commands:
        command.start()

def stop():
    for command in commands:
        command.stop()
```

## Command Entry Pattern (entry.py)

### Command Identity

```python
import adsk.core, adsk.fusion
from ... import config
from ...lib import fusion360utils as futil

# Command identity
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'Command Dialog Sample'
CMD_Description = 'A Fusion Add-in Command with a dialog'

# UI placement
IS_PROMOTED = True
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Icon folder path
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local event handlers (cleared on command destroy)
local_handlers = []
```

### Start Function

```python
def start():
    # Create a command Definition
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )

    # Connect to commandCreated event
    futil.add_handler(cmd_def.commandCreated, command_created)

    # Add button to UI
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED
```

### Stop Function

```python
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()
```

### Event Handlers

```python
def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')

    inputs = args.command.commandInputs

    # Create dialog inputs
    inputs.addTextBoxCommandInput('text_box', 'Some Text', 'Enter some text.', 1, False)

    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('1')
    inputs.addValueInput('value_input', 'Some Value', defaultLengthUnits, default_value)

    # Connect to command events
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs
    # Read inputs and perform operations
    text_box = inputs.itemById('text_box')
    value_input = inputs.itemById('value_input')


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    futil.log(f'{CMD_NAME} Input Changed: {changed_input.id}')


def command_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Preview Event')


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    args.areInputsValid = True


def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event')
    local_handlers.clear()
```

## Event Utility (futil)

The `fusion360utils` library simplifies event handling:

```python
# Simple handler connection
futil.add_handler(event, handler_function)

# With local handler list (for command-scoped handlers)
futil.add_handler(event, handler_function, local_handlers=local_handlers)

# Clear all handlers (called in stop())
futil.clear_handlers()

# Debug logging
futil.log('Message here')

# Error handling
futil.handle_error('context_name')
```

## Adding a New Command

1. Copy an existing command folder (e.g., `commandDialog/`)
2. Rename the folder to your command name
3. Edit `entry.py`:
   - Update `CMD_ID`, `CMD_NAME`, `CMD_Description`
   - Update UI placement (`WORKSPACE_ID`, `PANEL_ID`, `COMMAND_BESIDE_ID`)
   - Modify `command_created` to define your dialog inputs
   - Implement `command_execute` with your logic
4. Add import to `commands/__init__.py`:
   ```python
   from .myNewCommand import entry as myNewCommand
   ```
5. Add to the commands list:
   ```python
   commands = [commandDialog, paletteShow, paletteSend, myNewCommand]
   ```

## Common Workspace IDs

| Workspace | ID |
|-----------|-----|
| Design (Solid) | `FusionSolidEnvironment` |
| Render | `FusionRenderEnvironment` |
| Animation | `FusionAnimationEnvironment` |
| Simulation | `SimulationEnvironment` |
| Manufacturing (CAM) | `CAMEnvironment` |
| Drawing | `FusionDrawingEnvironment` |

## Common Panel IDs

| Panel | ID | Workspace |
|-------|-----|-----------|
| Scripts and Add-Ins | `SolidScriptsAddinsPanel` | Design |
| Create | `SolidCreatePanel` | Design |
| Modify | `SolidModifyPanel` | Design |
| Construct | `ConstructPanel` | Design |
| Inspect | `InspectPanel` | Design |
