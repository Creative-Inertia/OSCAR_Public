# Fusion 360 API - CAM (Manufacturing) API Reference

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CAMIntroduction_UM.htm

## Overview

The CAM API enables automation of manufacturing workflows including setup creation, toolpath operations, toolpath generation, NC file post-processing, and setup sheet generation.

## Imports

```python
import adsk.core, adsk.fusion, adsk.cam, traceback
```

## Accessing the CAM Product

A Fusion document can contain both Design and CAM products.

### Method 1: From Document (CAM data may not exist)

```python
app = adsk.core.Application.get()
doc = app.activeDocument
cam = doc.products.itemByProductType('CAMProductType')
if cam is None:
    ui.messageBox('There is no CAM data in the active document')
    return
```

### Method 2: From Active Product (Manufacturing workspace must be active)

```python
cam = adsk.cam.CAM.cast(app.activeProduct)
if cam is None:
    ui.messageBox('The Manufacturing workspace must be active')
    return
```

## CAM Object Model

```
CAM
  └── Setups (collection)
       └── Setup
            ├── Operations (collection)
            │    └── Operation (toolpath)
            ├── Folders (collection)
            │    └── Folder
            │         ├── Operations
            │         └── Folders (nested)
            └── Patterns (collection)
                 └── Pattern
                      ├── Operations
                      └── Patterns (nested)
```

## Navigating Setups and Operations

### By Index

```python
setups = cam.setups
setup = setups.item(0)

operations = setup.operations
operation = operations.item(0)

folders = setup.folders
folder = folders.item(0)
folderOperations = folder.operations
operation = folderOperations.item(0)
```

### By Name

```python
setup = cam.setups.itemByName('Setup1')
folder = setup.folders.itemByName('Folder1')
operation = folder.operations.itemByName('2D Adaptive1')
```

## Creating Setups

```python
setups = cam.setups

# Create setup input
setupInput = setups.createInput(adsk.cam.OperationTypes.MillingOperation)

# Configure model selection
camOcc = cam.designRootOccurrence
setupInput.models = [camOcc.bRepBodies[0]]

# Configure WCS origin
originParam = setupInput.parameters.itemByName('wcs_origin_mode')
choiceVal = originParam.value
choiceVal.value = 'modelPoint'

originPoint = setupInput.parameters.itemByName('wcs_origin_boxPoint')
choiceVal = originPoint.value
choiceVal.value = 'top center'

# Set comment
commentParam = setupInput.parameters.itemByName('job_programComment')
commentParam.value.value = 'This is the comment.'

# Create the setup
setup = setups.add(setupInput)
```

### OperationTypes Enum

| Value | Description |
|-------|-------------|
| `MillingOperation` | Milling setup |
| `TurningOperation` | Turning setup |
| `CuttingOperation` | Cutting setup |

## Creating Operations

```python
# Find compatible strategies
strategies = setup.operations.compatibleStrategies

# Create operation input
opInput = setup.operations.createInput('scallop')  # strategy name

# Configure parameters
stepoverParam = opInput.parameters.itemByName('stepover')
stepoverParam.expression = '0.1 in'

overrideParam = opInput.parameters.itemByName('overrideModel')
overrideParam.expression = 'true'

# Set tool
opInput.tool = cam.documentToolLibrary.item(0)

# Select geometry
body = cam.designRootOccurrence.bRepBodies.item(0)
sphereFaces = []
for face in body.faces:
    if face.geometry.objectType == adsk.core.Sphere.classType():
        sphereFaces.append(face)

modelParam = opInput.parameters.itemByName('model')
geomSelect = modelParam.value
geomSelect.value = sphereFaces

# Create the operation
op = setup.operations.add(opInput)
```

## Generating Toolpaths

### Generate All Toolpaths

```python
# False = regenerate all; True = skip valid ones
future = cam.generateAllToolpaths(False)
```

### Generate Specific Toolpaths

```python
# Single operation
future = cam.generateToolpath(operation)

# Collection of operations
future = cam.generateToolpath(collectionOfOperations)

# Entire setup
future = cam.generateToolpath(setup)

# Collection of setups
future = cam.generateToolpath(collectionOfSetups)
```

### GenerateToolpathFuture Object

Returns a future object for tracking async generation:

| Property | Description |
|----------|-------------|
| `operationCount` | Total number of operations |
| `numberOfCompleted` | Number of completed operations |
| `isGenerationCompleted` | Whether all are done |

## Post-Processing (NC File Generation)

### Post-Process All

```python
programName = '101'
outputFolder = '/tmp/nc_output'
postConfig = cam.genericPostFolder + '/' + 'fanuc.cps'
units = adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput

postInput = adsk.cam.PostProcessInput.create(
    programName, postConfig, outputFolder, units
)
postInput.isOpenInEditor = True
cam.postProcessAll(postInput)
```

### Post-Process Specific Operation

```python
setup = cam.setups[0]
operations = setup.allOperations
operation = operations[0]

if operation.hasToolpath:
    cam.postProcess(operation, postInput)
else:
    ui.messageBox('Operation has no toolpath to post.')
```

### PostOutputUnitOptions Enum

| Value | Description |
|-------|-------------|
| `DocumentUnitsOutput` | Use document units |
| `MillimetersOutput` | Force millimeters |
| `InchesOutput` | Force inches |

### Post Processor Properties

```python
postInput = adsk.cam.PostProcessInput.create(
    programName, postProcessor, outputFolder, units
)

# Configure post properties
postProperties = adsk.core.NamedValues.create()
disableSeqNums = adsk.core.ValueInput.createByBoolean(False)
postProperties.add("showSequenceNumbers", disableSeqNums)
postInput.postProperties = postProperties
```

## Setup Sheets

### Generate All Setup Sheets

```python
outputFolder = '/tmp/setup_sheets'
sheetFormat = adsk.cam.SetupSheetFormats.HTMLFormat
cam.generateAllSetupSheets(sheetFormat, outputFolder, True)
```

### Generate Specific Setup Sheet

```python
operation = setup.allOperations[0]
if operation.hasToolpath:
    cam.generateSetupSheet(operation, sheetFormat, outputFolder, True)
```

### SetupSheetFormats Enum

| Value | Description |
|-------|-------------|
| `HTMLFormat` | HTML format (cross-platform) |
| `ExcelFormat` | Excel format (Windows only) |

## CAM Parameters

CAM parameters control operation settings. Access via the `parameters` collection on setups and operations.

```python
# Get parameter by name
param = operation.parameters.itemByName('stepover')

# Set value via expression
param.expression = '0.1 in'

# Set value directly
param.value.value = 0.254  # internal units

# Get parameter value
currentValue = param.expression
```

### Common Parameter Names

| Parameter | Description |
|-----------|-------------|
| `wcs_origin_mode` | WCS origin mode |
| `wcs_origin_boxPoint` | WCS origin box point |
| `job_programComment` | Program comment |
| `stepover` | Stepover distance |
| `stepdown` | Stepdown distance |
| `feedrate` | Cutting feed rate |
| `spindleSpeed` | Spindle RPM |
| `overrideModel` | Override model selection |
| `model` | Model/geometry selection |

## Tool Libraries

```python
# Document tool library
docToolLib = cam.documentToolLibrary

# Get a tool
tool = docToolLib.item(0)

# Assign tool to operation input
opInput.tool = tool
```
