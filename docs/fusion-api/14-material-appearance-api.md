# Fusion 360 API - Material and Appearance API Reference

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/MaterialSample_Sample.htm

## Overview

Materials define physical properties (density, strength) while Appearances define visual properties (color, texture, reflectivity). Both can be applied to components, bodies, faces, and occurrences.

## Materials vs. Appearances

| Concept | Purpose | Applied To |
|---------|---------|-----------|
| Material | Physical properties (density, strength, thermal) | Components |
| Appearance | Visual properties (color, texture, reflectivity) | Components, Bodies, Faces, Occurrences |

## Applying Appearances

### To a Body

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)

# Load a material library
materialLibs = app.materialLibraries
matLib = materialLibs.load('/path/to/APISampleMaterialLibrary2.adsklib')

# Get an appearance from the library
appear = matLib.appearances.item(0)

# Copy the appearance into the design
appear = design.appearances.addByCopy(appear, f'{appear.name}_Copied')

# Apply to first body in root component
root = design.rootComponent
body = root.bRepBodies.item(0)
body.appearance = appear

# Unload the library
if not matLib.isNative:
    matLib.unload()
```

### To a Face

```python
# Apply appearance to a specific face
face = body.faces.item(0)
face.appearance = appear
```

### To an Occurrence (Override)

```python
# Apply override appearance to an occurrence
occ = rootComp.occurrences.item(0)
occ.appearance = appear

# Remove override (use component's appearance)
occ.appearance = None
```

### To a Component

```python
# Set component-level appearance
component.material = materialObj  # Physical material
# Visual appearance comes from the material or can be overridden
```

## Material Libraries

### Loading Libraries

```python
materialLibs = app.materialLibraries

# Load external library
matLib = materialLibs.load('/path/to/library.adsklib')

# Access built-in libraries
for lib in materialLibs:
    print(f'{lib.name}: {lib.appearances.count} appearances, {lib.materials.count} materials')
```

### Built-in Library Names

Common Autodesk material libraries:
- `Fusion Material Library`
- `Fusion Appearance Library`
- `Autodesk Material Library`

### Browsing Appearances

```python
# List all appearances in a library
for i in range(matLib.appearances.count):
    appear = matLib.appearances.item(i)
    print(f'{appear.name}: {appear.id}')
```

### Getting Appearances by Name

```python
# From library
appear = matLib.appearances.itemByName('Red')

# From design (already imported)
appear = design.appearances.itemByName('Red_Copied')
```

## Physical Materials

### Setting Material on Component

```python
# Get material from library
mat = matLib.materials.itemByName('Aluminum')

# Copy into design
mat = design.materials.addByCopy(mat, f'{mat.name}_Copy')

# Apply to component
component.material = mat
```

### Reading Physical Properties

```python
props = component.getPhysicalProperties(
    adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy
)
print(f'Mass: {props.mass} kg')
print(f'Volume: {props.volume} cm^3')
print(f'Area: {props.area} cm^2')
print(f'Density: {props.density} kg/cm^3')
```

### CalculationAccuracy Enum

| Value | Description |
|-------|-------------|
| `LowCalculationAccuracy` | Fastest, least accurate |
| `MediumCalculationAccuracy` | Balanced |
| `HighCalculationAccuracy` | Most accurate, slower |
| `VeryHighCalculationAccuracy` | Highest accuracy |

## Key Objects

### MaterialLibrary

| Property/Method | Description |
|----------------|-------------|
| `name` | Library name |
| `appearances` | Collection of appearances |
| `materials` | Collection of physical materials |
| `isNative` | Whether built-in (don't unload native libraries) |
| `load(filePath)` | Static: load from file |
| `unload()` | Unload library |

### Appearance

| Property/Method | Description |
|----------------|-------------|
| `name` | Appearance name |
| `id` | Unique ID |
| `appearanceProperties` | Collection of visual properties |
| `usedByCount` | Number of entities using this appearance |

### Material

| Property/Method | Description |
|----------------|-------------|
| `name` | Material name |
| `id` | Unique ID |
| `materialProperties` | Collection of physical properties |

## Design Appearances Collection

```python
# List all appearances in the active design
for i in range(design.appearances.count):
    appear = design.appearances.item(i)
    print(f'{appear.name} (used by {appear.usedByCount} entities)')

# Add by copy from library
newAppear = design.appearances.addByCopy(libraryAppear, 'MyCustomName')

# Remove unused appearance
if appear.usedByCount == 0:
    appear.deleteMe()
```

## Complete Example

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Load library
        materialLibs = app.materialLibraries
        matLib = materialLibs.load('/tmp/APISampleMaterialLibrary2.adsklib')

        # Get first appearance
        appear = matLib.appearances.item(0)

        # Copy into design
        des = adsk.fusion.Design.cast(app.activeProduct)
        appear = des.appearances.addByCopy(appear, f'{appear.name}_Copied')

        # Apply to first body
        root = des.rootComponent
        body = root.bRepBodies.item(0)
        body.appearance = appear

        # Unload if not native
        if not matLib.isNative:
            matLib.unload()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```
