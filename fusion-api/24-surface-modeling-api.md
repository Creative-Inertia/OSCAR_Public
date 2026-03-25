# Fusion 360 API - Surface Modeling Features Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PatchFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TrimFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/StitchFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UnstitchFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExtendFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ThickenFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ThickenFeatureSample_Sample.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/OffsetFacesFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ReplaceFaceFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BoundaryFillFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/RuledSurfaceFeature.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Surface modeling in Fusion 360 creates open (non-watertight) sheet bodies composed of individual faces. Surfaces are used to define complex shapes, trim or split solids, and can be stitched and thickened into solid bodies. The API provides dedicated feature collections for each surface operation, all accessed through `rootComp.features`.

Key distinction: a BRepBody with `isSolid == True` is a solid body; a BRepBody with `isSolid == False` is a surface body. All surface features operate on or produce surface bodies unless the result is watertight (in which case Fusion auto-promotes to solid).

---

## Creating Surface Bodies

Surface bodies are created using the same feature types as solid bodies (Extrude, Loft, Revolve, Sweep) but with `isSolid` set to `False` on the feature input. This produces an open sheet body instead of a closed solid.

### ExtrudeFeature — Surface Mode

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create a sketch with a single line (open profile) or closed profile
sketches = rootComp.sketches
xyPlane = rootComp.xYConstructionPlane
sketch = sketches.add(xyPlane)
lines = sketch.sketchCurves.sketchLines
# Draw a rectangle profile
p0 = adsk.core.Point3D.create(0, 0, 0)
p1 = adsk.core.Point3D.create(4, 0, 0)
p2 = adsk.core.Point3D.create(4, 3, 0)
p3 = adsk.core.Point3D.create(0, 3, 0)
lines.addByTwoPoints(p0, p1)
lines.addByTwoPoints(p1, p2)
lines.addByTwoPoints(p2, p3)
lines.addByTwoPoints(p3, p0)

prof = sketch.profiles.item(0)

# Create a surface extrusion (isSolid = False)
extrudes = rootComp.features.extrudeFeatures
extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
distance = adsk.core.ValueInput.createByReal(2.0)
extInput.setDistanceExtent(False, distance)

# KEY: Set isSolid to False to create a surface body
extInput.isSolid = False

extFeature = extrudes.add(extInput)
surfaceBody = extFeature.bodies.item(0)
# surfaceBody.isSolid will be False
```

### LoftFeature — Surface Mode

```python
# Create two sketch profiles on different planes, then loft as surface
lofts = rootComp.features.loftFeatures
loftInput = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

# Add loft sections (sketch profiles)
loftInput.loftSections.add(profile1)
loftInput.loftSections.add(profile2)

# KEY: Set isSolid to False for a surface loft
loftInput.isSolid = False

loftFeature = lofts.add(loftInput)
```

### RevolveFeature — Surface Mode

```python
revolves = rootComp.features.revolveFeatures
revInput = revolves.createInput(profile, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
revAngle = adsk.core.ValueInput.createByString('180 deg')
revInput.setAngleExtent(False, revAngle)

# KEY: Set isSolid to False for a surface revolve
revInput.isSolid = False

revolveFeature = revolves.add(revInput)
```

---

## Patch Features

Patch features create a surface body that fills a closed boundary defined by edges. This is used to close holes, fill gaps between surfaces, or create surface patches from edge loops.

### Accessing the PatchFeatures Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

patchFeats = rootComp.features.patchFeatures
```

### PatchFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(boundaryEdges, operation)` | PatchFeatureInput | Creates an input object. `boundaryEdges` is an ObjectCollection of BRepEdges forming a closed loop. `operation` is a FeatureOperations enum. |
| `add(input)` | PatchFeature | Creates the patch feature from the input definition |
| `item(index)` | PatchFeature | Returns the patch feature at the given index |
| `itemByName(name)` | PatchFeature | Returns the patch feature with the given name |
| `count` | int | Number of patch features in the collection |

### PatchFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `boundaryEdges` | ObjectCollection | R | The collection of BRepEdges that define the closed boundary loop |
| `continuity` | SurfaceContinuityTypes | R/W | The continuity type for the patch surface relative to adjacent faces |
| `operation` | FeatureOperations | R/W | The feature operation type (NewBodyFeatureOperation, JoinFeatureOperation, etc.) |

### SurfaceContinuityTypes Enum

| Value | Description |
|-------|-------------|
| `ConnectedSurfaceContinuityType` | G0 — positional continuity. The patch meets adjacent faces at the boundary but may have a crease. |
| `TangentSurfaceContinuityType` | G1 — tangent continuity. The patch is tangent to adjacent faces at the boundary (smooth transition). |
| `CurvatureSurfaceContinuityType` | G2 — curvature continuity. The patch matches curvature of adjacent faces (smoothest result). |

### Complete Example — Patch Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Assume we have a surface body with an open edge loop (a hole)
# Get the edges that form the closed boundary of the hole
surfaceBody = rootComp.bRepBodies.item(0)

# Collect edges that form the boundary loop to patch
boundaryEdges = adsk.core.ObjectCollection.create()
for edge in surfaceBody.edges:
    # Add edges that form the open boundary (application-specific selection logic)
    # For example, select edges adjacent to only one face (boundary edges)
    if edge.faces.count == 1:
        boundaryEdges.add(edge)

# Create the patch feature input
patchFeats = rootComp.features.patchFeatures
patchInput = patchFeats.createInput(
    boundaryEdges,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# Set continuity — tangent for a smooth blend
patchInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType

# Create the patch
patchFeature = patchFeats.add(patchInput)
patchBody = patchFeature.bodies.item(0)
```

---

## Trim Features

Trim features use a surface body or construction plane as a cutting tool to split another body, then remove selected regions (cells). This is commonly used to trim surfaces against each other.

### Accessing the TrimFeatures Collection

```python
trimFeats = rootComp.features.trimFeatures
```

### TrimFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(trimTool)` | TrimFeatureInput | Creates an input. `trimTool` is a BRepBody (surface) or ConstructionPlane used to split the target body. |
| `add(input)` | TrimFeature | Creates the trim feature |
| `item(index)` | TrimFeature | Returns the trim feature at the given index |
| `itemByName(name)` | TrimFeature | Returns the trim feature with the given name |
| `count` | int | Number of trim features in the collection |

### TrimFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `trimTool` | BRepBody or ConstructionPlane | R | The tool used to trim/split the target body |
| `cellsToRemove` | BRepCells | R/W | The cells (regions) to remove after the trim operation splits the body |

### Complete Example — Trim Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Assume we have two surface bodies — one to trim, one as the tool
# surfaceToTrim = rootComp.bRepBodies.item(0)
# trimmingTool = rootComp.bRepBodies.item(1)
# Or use a construction plane as the trimming tool:
trimmingPlane = rootComp.xYConstructionPlane

trimFeats = rootComp.features.trimFeatures
trimInput = trimFeats.createInput(trimmingPlane)

# After creating input, cells are computed — select which cells to remove
# cellsToRemove identifies the regions on the side of the trim tool to discard
# The cells are available after the input is created with the tool
cells = trimInput.bRepCells

# Select the cell(s) to remove (typically the cell on one side of the cutting tool)
cellsToRemove = adsk.core.ObjectCollection.create()
for i in range(cells.count):
    cell = cells.item(i)
    # Application logic to decide which cell to remove
    # For example, remove the cell below the XY plane
    cellsToRemove.add(cell)

trimInput.cellsToRemove = cellsToRemove

trimFeature = trimFeats.add(trimInput)
```

---

## Stitch Features

Stitch features join multiple surface bodies along shared edges into a single quilted surface body. If the stitched result forms a completely closed (watertight) volume, Fusion automatically converts it to a solid body.

### Accessing the StitchFeatures Collection

```python
stitchFeats = rootComp.features.stitchFeatures
```

### StitchFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(inputBodies, tolerance, operation)` | StitchFeatureInput | Creates an input. `inputBodies` is an ObjectCollection of BRepBody surface bodies. `tolerance` is a ValueInput for edge matching tolerance. `operation` is a FeatureOperations enum. |
| `add(input)` | StitchFeature | Creates the stitch feature |
| `item(index)` | StitchFeature | Returns the stitch feature at the given index |
| `itemByName(name)` | StitchFeature | Returns the stitch feature with the given name |
| `count` | int | Number of stitch features in the collection |

### StitchFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputBodies` | ObjectCollection | R | Collection of BRepBody surface bodies to stitch together |
| `tolerance` | ValueInput | R/W | The maximum distance between edges that will be considered coincident and stitched. Typical value: 0.001 cm. |
| `operation` | FeatureOperations | R/W | The feature operation (NewBodyFeatureOperation or JoinFeatureOperation) |

### Important Behavior

- If the stitched surfaces form a **watertight** (fully closed) volume, the resulting body is automatically promoted to a **solid body** (`isSolid == True`).
- If edges remain unstitched (gap exceeds tolerance), the result remains a surface body.
- The tolerance value is in centimeters (Fusion's internal unit).

### Complete Example — Stitch Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Collect all surface bodies to stitch together
surfaceBodies = adsk.core.ObjectCollection.create()
for body in rootComp.bRepBodies:
    if not body.isSolid:
        surfaceBodies.add(body)

# Create stitch input with a tolerance of 0.001 cm
stitchFeats = rootComp.features.stitchFeatures
tolerance = adsk.core.ValueInput.createByReal(0.001)
stitchInput = stitchFeats.createInput(
    surfaceBodies,
    tolerance,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# Create the stitch feature
stitchFeature = stitchFeats.add(stitchInput)
resultBody = stitchFeature.bodies.item(0)

# Check if the result is solid (watertight) or still a surface
if resultBody.isSolid:
    print('Stitch produced a solid body (watertight)')
else:
    print('Stitch produced a surface body (edges remain open)')
```

---

## Unstitch Features

Unstitch features split a body into its individual constituent faces, producing separate surface bodies for each face. This is the inverse of stitching.

### Accessing the UnstitchFeatures Collection

```python
unstitchFeats = rootComp.features.unstitchFeatures
```

### UnstitchFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(inputEntities)` | UnstitchFeatureInput | Creates an input. `inputEntities` is an ObjectCollection of BRepFace objects or BRepBody objects to unstitch. |
| `add(input)` | UnstitchFeature | Creates the unstitch feature |
| `item(index)` | UnstitchFeature | Returns the unstitch feature at the given index |
| `itemByName(name)` | UnstitchFeature | Returns the unstitch feature with the given name |
| `count` | int | Number of unstitch features in the collection |

### UnstitchFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputEntities` | ObjectCollection | R | Collection of BRepFace or BRepBody objects to unstitch |

### Complete Example — Unstitch Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Get a body to unstitch (solid or surface)
body = rootComp.bRepBodies.item(0)

# Prepare input — unstitch the entire body
inputEntities = adsk.core.ObjectCollection.create()
inputEntities.add(body)

unstitchFeats = rootComp.features.unstitchFeatures
unstitchInput = unstitchFeats.createInput(inputEntities)

# Create the unstitch feature
unstitchFeature = unstitchFeats.add(unstitchInput)

# The original body is consumed; individual surface bodies are created
# Each face becomes its own surface body
print(f'Unstitch produced {unstitchFeature.bodies.count} surface bodies')
for i in range(unstitchFeature.bodies.count):
    surfBody = unstitchFeature.bodies.item(i)
    print(f'  Body {i}: isSolid={surfBody.isSolid}, faces={surfBody.faces.count}')
```

You can also unstitch specific faces rather than entire bodies:

```python
# Unstitch only selected faces from the body
inputEntities = adsk.core.ObjectCollection.create()
inputEntities.add(body.faces.item(0))
inputEntities.add(body.faces.item(1))

unstitchInput = unstitchFeats.createInput(inputEntities)
unstitchFeature = unstitchFeats.add(unstitchInput)
```

---

## Extend Features

Extend features lengthen surface body boundary edges outward by a specified distance. This is used to grow surfaces beyond their current boundaries for trimming or intersection operations.

### Accessing the ExtendFeatures Collection

```python
extendFeats = rootComp.features.extendFeatures
```

### ExtendFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(edges, distance, extendType)` | ExtendFeatureInput | Creates an input. `edges` is an ObjectCollection of BRepEdges on surface body boundaries. `distance` is a ValueInput. `extendType` is a SurfaceExtendTypes enum. |
| `add(input)` | ExtendFeature | Creates the extend feature |
| `item(index)` | ExtendFeature | Returns the extend feature at the given index |
| `itemByName(name)` | ExtendFeature | Returns the extend feature with the given name |
| `count` | int | Number of extend features in the collection |

### ExtendFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `edges` | ObjectCollection | R | Collection of BRepEdge objects on the boundary of a surface body |
| `distance` | ValueInput | R/W | The distance to extend the surface from each selected edge |
| `extendType` | SurfaceExtendTypes | R/W | The type of surface extension |

### SurfaceExtendTypes Enum

| Value | Description |
|-------|-------------|
| `NaturalSurfaceExtendType` | Extends the surface using its natural shape (follows the curvature of the original surface) |
| `TangentSurfaceExtendType` | Extends the surface tangent to the boundary edge (produces a flat or ruled extension) |

### Complete Example — Extend Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Get a surface body and select boundary edges to extend
surfaceBody = None
for body in rootComp.bRepBodies:
    if not body.isSolid:
        surfaceBody = body
        break

if surfaceBody:
    # Collect boundary edges (edges adjacent to only one face)
    edgesToExtend = adsk.core.ObjectCollection.create()
    for edge in surfaceBody.edges:
        if edge.faces.count == 1:
            edgesToExtend.add(edge)
            break  # Extend one edge for this example

    # Create extend input — extend 1 cm using natural extension
    extendFeats = rootComp.features.extendFeatures
    distance = adsk.core.ValueInput.createByReal(1.0)  # 1 cm
    extendInput = extendFeats.createInput(
        edgesToExtend,
        distance,
        adsk.fusion.SurfaceExtendTypes.NaturalSurfaceExtendType
    )

    extendFeature = extendFeats.add(extendInput)
```

---

## Thicken Features

Thicken features convert a surface body into a solid body by adding material thickness in one or both directions from the surface. This is one of the most common surface-to-solid workflows.

### Accessing the ThickenFeatures Collection

```python
thickenFeats = rootComp.features.thickenFeatures
```

### ThickenFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(inputSurfaces, thickness, isSymmetric, operation)` | ThickenFeatureInput | Creates an input. `inputSurfaces` is an ObjectCollection of BRepBody surface bodies. `thickness` is a ValueInput. `isSymmetric` is a Boolean. `operation` is a FeatureOperations enum. |
| `add(input)` | ThickenFeature | Creates the thicken feature |
| `item(index)` | ThickenFeature | Returns the thicken feature at the given index |
| `itemByName(name)` | ThickenFeature | Returns the thicken feature with the given name |
| `count` | int | Number of thicken features in the collection |

### ThickenFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputSurfaces` | ObjectCollection | R | Collection of BRepBody surface bodies to thicken |
| `thickness` | ValueInput | R/W | The thickness distance. Positive = normal direction, negative = opposite to normal. |
| `isSymmetric` | Boolean | R/W | If True, thickness is applied equally on both sides of the surface (half the value each side). If False, full thickness is applied in the direction indicated by the sign. |
| `operation` | FeatureOperations | R/W | The feature operation (NewBodyFeatureOperation, JoinFeatureOperation, CutFeatureOperation, IntersectFeatureOperation) |

### Complete Example — Surface Extrusion then Thicken to Solid

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Step 1: Create a surface body via extrusion
sketches = rootComp.sketches
xyPlane = rootComp.xYConstructionPlane
sketch = sketches.add(xyPlane)

# Draw a closed profile
lines = sketch.sketchCurves.sketchLines
p0 = adsk.core.Point3D.create(0, 0, 0)
p1 = adsk.core.Point3D.create(5, 0, 0)
p2 = adsk.core.Point3D.create(5, 3, 0)
p3 = adsk.core.Point3D.create(0, 3, 0)
lines.addByTwoPoints(p0, p1)
lines.addByTwoPoints(p1, p2)
lines.addByTwoPoints(p2, p3)
lines.addByTwoPoints(p3, p0)

prof = sketch.profiles.item(0)

extrudes = rootComp.features.extrudeFeatures
extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3.0))
extInput.isSolid = False  # Surface body
extFeature = extrudes.add(extInput)

surfaceBody = extFeature.bodies.item(0)
print(f'Surface body created: isSolid={surfaceBody.isSolid}')  # False

# Step 2: Thicken the surface body into a solid
thickenFeats = rootComp.features.thickenFeatures
inputSurfaces = adsk.core.ObjectCollection.create()
inputSurfaces.add(surfaceBody)

thickness = adsk.core.ValueInput.createByReal(0.2)  # 0.2 cm = 2 mm
isSymmetric = False  # Thicken in one direction only

thickenInput = thickenFeats.createInput(
    inputSurfaces,
    thickness,
    isSymmetric,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

thickenFeature = thickenFeats.add(thickenInput)
solidBody = thickenFeature.bodies.item(0)
print(f'Thickened body: isSolid={solidBody.isSolid}')  # True
```

### Symmetric Thicken Example

```python
# Thicken 0.5 cm symmetrically (0.25 cm each side of the surface)
thickness = adsk.core.ValueInput.createByReal(0.5)
isSymmetric = True

thickenInput = thickenFeats.createInput(
    inputSurfaces,
    thickness,
    isSymmetric,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
thickenFeature = thickenFeats.add(thickenInput)
```

---

## Offset Faces Features

Offset Faces features move selected faces of a body inward or outward by a specified distance. This works on both solid and surface bodies and adjusts adjacent faces to maintain connectivity.

### Accessing the OffsetFacesFeatures Collection

```python
offsetFacesFeats = rootComp.features.offsetFacesFeatures
```

### OffsetFacesFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(inputFaces, distance)` | OffsetFacesFeatureInput | Creates an input. `inputFaces` is an ObjectCollection of BRepFace. `distance` is a ValueInput. |
| `add(input)` | OffsetFacesFeature | Creates the offset faces feature |
| `item(index)` | OffsetFacesFeature | Returns the feature at the given index |
| `itemByName(name)` | OffsetFacesFeature | Returns the feature with the given name |
| `count` | int | Number of offset faces features in the collection |

### OffsetFacesFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputFaces` | ObjectCollection | R | Collection of BRepFace objects to offset |
| `distance` | ValueInput | R/W | The offset distance. Positive = outward (along face normal), negative = inward. |

### Complete Example — Offset Faces Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Get a body and select faces to offset
body = rootComp.bRepBodies.item(0)

# Select the top face (for example, the face with the highest Z centroid)
facesToOffset = adsk.core.ObjectCollection.create()
topFace = None
maxZ = -1e10
for face in body.faces:
    centroid = face.centroid
    if centroid.z > maxZ:
        maxZ = centroid.z
        topFace = face

if topFace:
    facesToOffset.add(topFace)

    offsetFacesFeats = rootComp.features.offsetFacesFeatures
    distance = adsk.core.ValueInput.createByReal(0.5)  # Offset outward 0.5 cm
    offsetInput = offsetFacesFeats.createInput(facesToOffset, distance)

    offsetFeature = offsetFacesFeats.add(offsetInput)
```

---

## Replace Face Features

Replace Face features substitute one or more faces of a solid body with a different surface. The solid body is reshaped so that the replacement surface defines the new face geometry while maintaining the solid's topology.

### Accessing the ReplaceFaceFeatures Collection

```python
replaceFaceFeats = rootComp.features.replaceFaceFeatures
```

### ReplaceFaceFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(sourceFaces, targetFaces)` | ReplaceFaceFeatureInput | Creates an input. `sourceFaces` is an ObjectCollection of BRepFace on the solid to replace. `targetFaces` is an ObjectCollection of BRepFace defining the replacement surface. |
| `add(input)` | ReplaceFaceFeature | Creates the replace face feature |
| `item(index)` | ReplaceFaceFeature | Returns the feature at the given index |
| `itemByName(name)` | ReplaceFaceFeature | Returns the feature with the given name |
| `count` | int | Number of replace face features in the collection |

### ReplaceFaceFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `sourceFaces` | ObjectCollection | R | Collection of BRepFace objects on the solid body to be replaced |
| `targetFaces` | ObjectCollection | R | Collection of BRepFace objects that define the replacement surface geometry |
| `isTangentChain` | Boolean | R/W | If True, tangent-connected faces are automatically included in the selection |

### Complete Example — Replace Face Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Assume body 0 is a solid box, body 1 is a curved surface body
solidBody = rootComp.bRepBodies.item(0)
surfaceBody = rootComp.bRepBodies.item(1)

# Select the top face of the solid as the source to replace
sourceFaces = adsk.core.ObjectCollection.create()
topFace = None
maxZ = -1e10
for face in solidBody.faces:
    if face.centroid.z > maxZ:
        maxZ = face.centroid.z
        topFace = face
sourceFaces.add(topFace)

# Select the face of the surface body as the replacement
targetFaces = adsk.core.ObjectCollection.create()
targetFaces.add(surfaceBody.faces.item(0))

replaceFaceFeats = rootComp.features.replaceFaceFeatures
replaceInput = replaceFaceFeats.createInput(sourceFaces, targetFaces)
replaceInput.isTangentChain = False

replaceFeature = replaceFaceFeats.add(replaceInput)
```

---

## Reverse Normal Features

Reverse Normal features flip the normal direction of surface bodies. The normal direction determines the "front" and "back" of a surface and affects operations like thicken direction.

### Accessing the ReverseNormalFeatures Collection

```python
reverseNormalFeats = rootComp.features.reverseNormalFeatures
```

### ReverseNormalFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(inputBodies)` | ReverseNormalFeatureInput | Creates an input. `inputBodies` is an ObjectCollection of BRepBody surface bodies. |
| `add(input)` | ReverseNormalFeature | Creates the reverse normal feature |
| `item(index)` | ReverseNormalFeature | Returns the feature at the given index |
| `count` | int | Number of reverse normal features in the collection |

### ReverseNormalFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputBodies` | ObjectCollection | R | Collection of BRepBody surface bodies whose normals will be flipped |

### Code Example — Reverse Normal

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Find a surface body and reverse its normal
surfaceBodies = adsk.core.ObjectCollection.create()
for body in rootComp.bRepBodies:
    if not body.isSolid:
        surfaceBodies.add(body)
        break

if surfaceBodies.count > 0:
    reverseNormalFeats = rootComp.features.reverseNormalFeatures
    reverseInput = reverseNormalFeats.createInput(surfaceBodies)
    reverseFeature = reverseNormalFeats.add(reverseInput)
```

---

## Ruled Surface Features

Ruled Surface features create a surface by extending edges or curves along a direction defined by the surface normal or tangent, with a specified distance and angle. This is useful for creating flanges, draft surfaces, or extensions from existing edges.

### Accessing the RuledSurfaceFeatures Collection

```python
ruledSurfaceFeats = rootComp.features.ruledSurfaceFeatures
```

### RuledSurfaceFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(profile)` | RuledSurfaceFeatureInput | Creates an input. `profile` is an ObjectCollection of BRepEdges or sketch curves. |
| `add(input)` | RuledSurfaceFeature | Creates the ruled surface feature |
| `item(index)` | RuledSurfaceFeature | Returns the feature at the given index |
| `itemByName(name)` | RuledSurfaceFeature | Returns the feature with the given name |
| `count` | int | Number of ruled surface features in the collection |

### RuledSurfaceFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `profile` | ObjectCollection | R | The edges or sketch curves that define the base profile for the ruled surface |
| `ruledSurfaceType` | RuledSurfaceTypes | R/W | The direction type for the ruled surface |
| `distance` | ValueInput | R/W | The distance (height) of the ruled surface from the profile edge |
| `angle` | ValueInput | R/W | The angle of the ruled surface relative to the profile edge normal or tangent |

### RuledSurfaceTypes Enum

| Value | Description |
|-------|-------------|
| `NormalRuledSurfaceType` | The ruled surface extends in the direction of the face normal at each point along the profile edge |
| `TangentRuledSurfaceType` | The ruled surface extends tangent to the adjacent face at each point along the profile edge |

### Code Example — Ruled Surface

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Select an edge from an existing body as the profile
body = rootComp.bRepBodies.item(0)
profileEdges = adsk.core.ObjectCollection.create()
profileEdges.add(body.edges.item(0))

ruledSurfaceFeats = rootComp.features.ruledSurfaceFeatures
ruledInput = ruledSurfaceFeats.createInput(profileEdges)
ruledInput.ruledSurfaceType = adsk.fusion.RuledSurfaceTypes.NormalRuledSurfaceType
ruledInput.distance = adsk.core.ValueInput.createByReal(1.0)  # 1 cm
ruledInput.angle = adsk.core.ValueInput.createByString('0 deg')  # No angle

ruledFeature = ruledSurfaceFeats.add(ruledInput)
```

---

## Boundary Fill Features

Boundary Fill features create solid or surface bodies by filling enclosed regions (cells) defined by intersecting surfaces, faces, and construction planes. This is the API equivalent of the Boundary Fill command in the UI.

### Accessing the BoundaryFillFeatures Collection

```python
boundaryFillFeats = rootComp.features.boundaryFillFeatures
```

### BoundaryFillFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(tools, operation)` | BoundaryFillFeatureInput | Creates an input. `tools` is an ObjectCollection of BRepBody (surface bodies), BRepFace, or ConstructionPlane that define enclosed regions. `operation` is a FeatureOperations enum. |
| `add(input)` | BoundaryFillFeature | Creates the boundary fill feature |
| `item(index)` | BoundaryFillFeature | Returns the feature at the given index |
| `itemByName(name)` | BoundaryFillFeature | Returns the feature with the given name |
| `count` | int | Number of boundary fill features in the collection |

### BoundaryFillFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `tools` | ObjectCollection | R | Collection of surface bodies, faces, or construction planes that define the boundary regions |
| `operation` | FeatureOperations | R/W | The feature operation type |
| `bRepCells` | BRepCells | R | The cells (enclosed regions) computed from the intersecting tools. Select which cells to keep. |

### BRepCells — Selecting Regions

After creating the input, the `bRepCells` property contains all computed enclosed regions. Each cell can be toggled for inclusion in the result.

| Property / Method | Type | Description |
|-------------------|------|-------------|
| `count` | int | Number of cells |
| `item(index)` | BRepCell | Returns the cell at the given index |

Each `BRepCell` has:

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `isSelected` | Boolean | R/W | Set to True to include this cell in the result, False to exclude |

### Complete Example — Boundary Fill Feature

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Assume we have multiple surface bodies that intersect and form enclosed regions
# Collect them as tools
tools = adsk.core.ObjectCollection.create()
for body in rootComp.bRepBodies:
    if not body.isSolid:
        tools.add(body)

# Optionally add a construction plane as a bounding tool
tools.add(rootComp.xYConstructionPlane)

boundaryFillFeats = rootComp.features.boundaryFillFeatures
bfInput = boundaryFillFeats.createInput(
    tools,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# After creating input, cells are computed — select which to fill
cells = bfInput.bRepCells
for i in range(cells.count):
    cell = cells.item(i)
    # Select all cells (or use application logic to pick specific ones)
    cell.isSelected = True

boundaryFillFeature = boundaryFillFeats.add(bfInput)

# Check the result
for i in range(boundaryFillFeature.bodies.count):
    resultBody = boundaryFillFeature.bodies.item(i)
    print(f'Result body {i}: isSolid={resultBody.isSolid}')
```

---

## Surface Delete Face Features

Surface Delete Face features remove selected faces from a surface body, leaving an open boundary where the face was removed. This is used to open up closed surfaces or remove unwanted patches.

### Accessing the SurfaceDeleteFaceFeatures Collection

```python
surfDelFeats = rootComp.features.surfaceDeleteFaceFeatures
```

### SurfaceDeleteFaceFeatures Collection — Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput(inputFaces)` | SurfaceDeleteFaceFeatureInput | Creates an input. `inputFaces` is an ObjectCollection of BRepFace objects to delete. |
| `add(input)` | SurfaceDeleteFaceFeature | Creates the feature |
| `item(index)` | SurfaceDeleteFaceFeature | Returns the feature at the given index |
| `count` | int | Number of surface delete face features in the collection |

### SurfaceDeleteFaceFeatureInput — Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputFaces` | ObjectCollection | R | Collection of BRepFace objects to remove from the surface body |

### Code Example — Surface Delete Face

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Get a surface body and remove a specific face
surfaceBody = None
for body in rootComp.bRepBodies:
    if not body.isSolid:
        surfaceBody = body
        break

if surfaceBody and surfaceBody.faces.count > 1:
    facesToDelete = adsk.core.ObjectCollection.create()
    facesToDelete.add(surfaceBody.faces.item(0))  # Remove the first face

    surfDelFeats = rootComp.features.surfaceDeleteFaceFeatures
    delInput = surfDelFeats.createInput(facesToDelete)
    delFeature = surfDelFeats.add(delInput)
```

---

## Practical Patterns

### Surface to Solid Workflow

The most common surface modeling workflow: create surfaces, stitch them together, then thicken into a solid.

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Step 1: Create multiple surface bodies (extrudes, lofts, patches, etc.)
# ... (create surfaces as shown in earlier sections) ...

# Step 2: Stitch all surface bodies together
surfaceBodies = adsk.core.ObjectCollection.create()
for body in rootComp.bRepBodies:
    if not body.isSolid:
        surfaceBodies.add(body)

stitchFeats = rootComp.features.stitchFeatures
tolerance = adsk.core.ValueInput.createByReal(0.001)
stitchInput = stitchFeats.createInput(
    surfaceBodies,
    tolerance,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
stitchFeature = stitchFeats.add(stitchInput)
stitchedBody = stitchFeature.bodies.item(0)

if stitchedBody.isSolid:
    # Already watertight — we have a solid
    print('Stitching produced a solid body directly')
else:
    # Step 3: Thicken the stitched surface into a solid
    thickenFeats = rootComp.features.thickenFeatures
    inputSurfaces = adsk.core.ObjectCollection.create()
    inputSurfaces.add(stitchedBody)

    thickness = adsk.core.ValueInput.createByReal(0.2)  # 2 mm
    thickenInput = thickenFeats.createInput(
        inputSurfaces,
        thickness,
        False,  # isSymmetric
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    thickenFeature = thickenFeats.add(thickenInput)
    solidBody = thickenFeature.bodies.item(0)
    print(f'Thickened to solid: isSolid={solidBody.isSolid}')
```

### Checking if a Body is Solid or Surface

```python
# body.isSolid returns True for solid bodies, False for surface bodies
for i in range(rootComp.bRepBodies.count):
    body = rootComp.bRepBodies.item(i)
    bodyType = 'Solid' if body.isSolid else 'Surface'
    print(f'Body "{body.name}": {bodyType}, faces={body.faces.count}, edges={body.edges.count}')
```

### Iterating Surface Bodies Only

```python
# Filter to only surface bodies
surfaceBodies = []
for i in range(rootComp.bRepBodies.count):
    body = rootComp.bRepBodies.item(i)
    if not body.isSolid:
        surfaceBodies.append(body)

print(f'Found {len(surfaceBodies)} surface bodies')
```

### Checking Open Edges on a Surface Body

Open edges (boundary edges adjacent to only one face) indicate where a surface body is not closed.

```python
def getOpenEdges(body):
    """Returns a list of edges that are on the boundary (open) of a surface body."""
    openEdges = []
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        if edge.faces.count == 1:
            openEdges.append(edge)
    return openEdges

surfaceBody = rootComp.bRepBodies.item(0)
openEdges = getOpenEdges(surfaceBody)
print(f'Body has {len(openEdges)} open (boundary) edges')
```
