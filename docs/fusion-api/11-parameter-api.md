# Fusion 360 API - Parameter API Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserParameters_add.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SetParametersFromACsvFileAndExportToSTEP_Sample.htm

## Overview

Fusion 360 has two types of parameters:
- **Model Parameters**: Automatically created by features (e.g., extrusion distance). Accessed via `component.modelParameters`.
- **User Parameters**: Manually created by users or API. Accessed via `design.userParameters`.

Both inherit from the Parameter base class.

## Accessing Parameters

```python
design = adsk.fusion.Design.cast(app.activeProduct)

# User parameters (design-level)
userParams = design.userParameters

# Model parameters (component-level)
modelParams = design.rootComponent.modelParameters

# All parameters (both types)
allParams = design.allParameters
```

## User Parameters

### Creating User Parameters

```python
userParams = design.userParameters

# Create with real value (internal units: cm for length, radians for angles)
lengthParam = userParams.add(
    'MyLength',                                    # name
    adsk.core.ValueInput.createByReal(5.0),        # value (5 cm)
    'cm',                                          # units
    'Length of the box'                             # comment
)

# Create with string expression
widthParam = userParams.add(
    'MyWidth',
    adsk.core.ValueInput.createByString('25.4 mm'),
    'mm',
    'Width of the box'
)

# Create with expression referencing other parameters
heightParam = userParams.add(
    'MyHeight',
    adsk.core.ValueInput.createByString('MyLength / 2'),
    'cm',
    'Half the length'
)

# Create unitless parameter
countParam = userParams.add(
    'HoleCount',
    adsk.core.ValueInput.createByReal(4),
    '',                                           # empty = no units
    'Number of holes'
)

# Create boolean parameter
boolParam = userParams.add(
    'IncludeHoles',
    adsk.core.ValueInput.createByBoolean(True),
    '',
    'Whether to include holes'
)

# Create text parameter
textParam = userParams.add(
    'MaterialName',
    adsk.core.ValueInput.createByString('Aluminum'),
    'Text',                                       # "Text" = text type
    'Material selection'
)
```

### UserParameters.add Method Signature

```python
returnValue = userParameters.add(name, value, units, comment)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Name shown in Parameters dialog |
| `value` | ValueInput | Parameter value. Real = internal units. String = expression. Boolean = `createByBoolean`. |
| `units` | string | Unit type: `"cm"`, `"mm"`, `"in"`, `""` (unitless), `"Text"` (text type), `"deg"`, `"rad"` |
| `comment` | string | Comment in Parameters dialog. Empty string for none. |

Returns: `UserParameter` or `None` if creation failed.

### Reading User Parameters

```python
# By name (CASE SENSITIVE)
param = design.userParameters.itemByName('MyLength')
if param:
    value = param.value          # Float in internal units (cm)
    expression = param.expression  # String expression (e.g., "5 cm")
    name = param.name
    comment = param.comment
    units = param.unit            # Unit string

# By index
param = design.userParameters.item(0)

# Iterate all
for i in range(design.userParameters.count):
    param = design.userParameters.item(i)
    print(f'{param.name} = {param.expression}')
```

### Modifying User Parameters

```python
param = design.userParameters.itemByName('MyLength')

# Set by expression (respects units)
param.expression = '10 cm'
param.expression = '50 mm'
param.expression = '2 in'
param.expression = 'MyWidth * 2'

# Set by value (internal units: cm for length)
param.value = 10.0  # 10 cm

# For text parameters
textParam = design.userParameters.itemByName('MaterialName')
textParam.textValue = 'Steel'

# Delete a parameter
param.deleteMe()
```

## Model Parameters

Model parameters are created automatically by features and typically named `d0`, `d1`, `d2`, etc.

```python
modelParams = rootComp.modelParameters

# By name
param = modelParams.itemByName('d0')

# Iterate
for i in range(modelParams.count):
    param = modelParams.item(i)
    print(f'{param.name}: {param.expression} ({param.role})')
```

### Modifying Model Parameters

```python
param = modelParams.itemByName('d0')

# Set expression
param.expression = '50 mm'
param.expression = 'MyLength'  # Reference user parameter

# Set value (internal units)
param.value = 5.0  # 5 cm
```

## Parameter Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | String (R/W) | Parameter name (model params: d0, d1...; user params: user-defined) |
| `value` | Double (R/W) | Current value in internal units |
| `expression` | String (R/W) | Expression (e.g., "5 cm", "d0 / 2") |
| `unit` | String (R) | Unit type string |
| `comment` | String (R/W) | User comment |
| `role` | String (R) | Purpose/role of parameter (model params only) |
| `isDeletable` | Boolean (R) | Whether parameter can be deleted |
| `isFavorite` | Boolean (R/W) | Whether marked as favorite |
| `createdBy` | String (R) | Feature name that created this parameter |

## Practical Example: CSV-Driven Parametric Export

```python
import adsk.core, adsk.fusion, traceback
import csv

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)

    # Read CSV with parameter values
    with open('/tmp/values.csv', 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            length, width, height = row[0], row[1], row[2]

            # Set parameters (case sensitive!)
            design.userParameters.itemByName('Length').expression = length
            design.userParameters.itemByName('Width').expression = width
            design.userParameters.itemByName('Height').expression = height

            # Export to STEP
            exportMgr = design.exportManager
            stepOptions = exportMgr.createSTEPExportOptions(
                f'/tmp/test_box{i}.stp'
            )
            exportMgr.execute(stepOptions)
```

## Units Reference

### Length Units
| Unit | String |
|------|--------|
| Centimeter | `"cm"` |
| Millimeter | `"mm"` |
| Meter | `"m"` |
| Inch | `"in"` |
| Foot | `"ft"` |

### Angle Units
| Unit | String |
|------|--------|
| Radian | `"rad"` |
| Degree | `"deg"` |

### Internal Units (for `createByReal`)
- **Length**: centimeters
- **Angle**: radians

### UnitsManager

```python
unitsManager = design.unitsManager

# Get default length units
defaultUnits = unitsManager.defaultLengthUnits  # e.g., "mm"

# Convert between units
value_cm = unitsManager.convert(25.4, 'mm', 'cm')  # 2.54
value_in = unitsManager.convert(5, 'cm', 'in')      # ~1.97

# Evaluate expression
value = unitsManager.evaluateExpression('5 in + 10 mm', 'cm')
```
