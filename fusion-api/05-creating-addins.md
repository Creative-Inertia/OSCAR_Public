# Fusion 360 API - Creating Scripts and Add-Ins

> Sources:
> - https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-9701BBA7-EC0E-4016-A9C8-964AA4838954
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Scripts vs. Add-Ins

| Feature | Script | Add-In |
|---------|--------|--------|
| Execution | Runs once, then terminates | Loads at startup, runs continuously |
| UI | Can show dialogs but temporary | Creates persistent toolbar buttons |
| Lifecycle | `run()` function only | `run()` and `stop()` functions |
| Startup | Manual execution via Scripts dialog | Can auto-start with Fusion |
| Use case | One-off automation tasks | Persistent tools and commands |
| Undo | All changes are one undo operation | Each command is separate undo |

## Creating a New Script/Add-In

1. Open Fusion 360
2. Navigate to **UTILITIES** tab > **ADD-INS** panel > **Scripts and Add-Ins**
3. Click the **+** (Create) button next to either "My Scripts" or "My Add-Ins"
4. Choose **Python** as the language
5. Enter a name for your script/add-in
6. Click **Create**

Fusion creates the complete file structure with template code.

## File Structure

### Script Structure

```
MyScript/
├── MyScript.py          # Main script file with run() function
├── MyScript.manifest    # Metadata file
└── Resources/           # Icons folder (optional)
```

### Add-In Structure (New Template)

```
MyAddIn/
├── MyAddIn.py           # Main entry point (run/stop)
├── MyAddIn.manifest     # Metadata file
├── config.py            # Global variables
├── lib/
│   ├── fusion360utils.py    # Event handling utilities
│   ├── event_utils.py       # Event helper functions
│   └── general_utils.py     # General utilities
├── commands/
│   ├── __init__.py          # Command registry
│   ├── commandDialog/
│   │   ├── __init__.py
│   │   ├── entry.py         # Command definition & handlers
│   │   └── resources/       # Command icons
│   └── ... (more commands)
└── Resources/               # Add-in icons
```

## Manifest File Format

The `.manifest` file is a JSON file with metadata:

```json
{
    "autodeskProduct": "Fusion",
    "type": "addin",
    "id": "unique-guid-here",
    "author": "Your Name",
    "description": {
        "": "Description of your add-in"
    },
    "version": "1.0.0",
    "runOnStartup": true,
    "supportedOS": "windows|mac"
}
```

Key fields:
- `type`: `"script"` or `"addin"`
- `runOnStartup`: If `true`, add-in loads automatically when Fusion starts
- `supportedOS`: `"windows"`, `"mac"`, or `"windows|mac"`

## Installation Locations

### Default Locations (Auto-discovered by Fusion)

**macOS:**
- Scripts: `~/Library/Application Support/Autodesk/Autodesk Fusion/API/Scripts/`
- Add-Ins: `~/Library/Application Support/Autodesk/Autodesk Fusion/API/AddIns/`

**Windows:**
- Scripts: `%APPDATA%\Autodesk\Autodesk Fusion\API\Scripts\`
- Add-Ins: `%APPDATA%\Autodesk\Autodesk Fusion\API\AddIns\`

### Installing from External Location

You can also point Fusion to scripts/add-ins in other locations by using the "Add Existing Script" or "Add Existing Add-In" button.

## Running Scripts

1. Open Scripts and Add-Ins dialog
2. Select the script
3. Click **Run**

## Running Add-Ins

1. Open Scripts and Add-Ins dialog
2. Select the add-in
3. Click **Run** to load it
4. Optionally check **Run on Startup** for auto-loading
5. To stop: select the add-in and click **Stop**

## Minimal Script Example

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Hello script!')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

## Minimal Add-In Example

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Hello addin')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Stop addin')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

## Important Notes

- The `context` parameter passed to `run()` and `stop()` is a JSON string with context information
- Scripts and add-ins share the same Python interpreter within Fusion
- All Fusion API modules must be imported: `import adsk.core, adsk.fusion, adsk.cam`
- Error handling with `traceback.format_exc()` is essential for debugging
- The `app.activeProduct` may be `None` if no document is open
