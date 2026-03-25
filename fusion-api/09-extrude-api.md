# Fusion 360 API - Extrude Feature API Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExtrudeFeatureSample_Sample.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExtrudeFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExtrudeFeatures_add.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExtrudeFeatures_addSimple.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Extrude features create solid or surface bodies by extending a profile along a direction. This is the most commonly used feature in parametric modeling.

## Quick Start: Simple Extrusion

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create sketch with circle
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 5.0
)

# Get profile and extrude
prof = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures

# Simple extrusion: 5 cm
distance = adsk.core.ValueInput.createByReal(5)
extrude = extrudes.addSimple(
    prof, distance,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
```

## ExtrudeFeatures.addSimple Method

The simplest way to create an extrusion.

```python
extrude = extrudeFeatures.addSimple(profile, distance, operation)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile` | Base | Profile, planar face, SketchText, or ObjectCollection of co-planar items. Solid extrusions only. |
| `distance` | ValueInput | Positive = positive sketch normal direction; Negative = opposite direction |
| `operation` | FeatureOperations | NewBody, Join, Cut, Intersect, or NewComponent |

## ExtrudeFeatures.add Method (Full Control)

For complex extrusions, use the Input pattern:

```python
# 1. Create input
extrudeInput = extrudes.createInput(profile, operation)

# 2. Configure input (see extent types below)
extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5))

# 3. Add feature
extrude = extrudes.add(extrudeInput)
```

## Extent Types

### 1. Distance Extent (One Side)

```python
extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extent_distance = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString("100 mm")
)
extrudeInput.setOneSideExtent(
    extent_distance,
    adsk.fusion.ExtentDirections.PositiveExtentDirection
)
extrude = extrudes.add(extrudeInput)
```

### 2. Distance Extent from Entity (Offset Start)

Start extrusion from a face with an offset:

```python
extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extent_distance = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString("10 mm")
)

# Start from a face with 10mm offset
start_from = adsk.fusion.FromEntityStartDefinition.create(
    body.faces.item(0),
    adsk.core.ValueInput.createByString("10 mm")
)

extrudeInput.setOneSideExtent(
    extent_distance,
    adsk.fusion.ExtentDirections.PositiveExtentDirection
)
extrudeInput.startExtent = start_from
extrude = extrudes.add(extrudeInput)
```

### 3. To Entity Extent

Extrude until reaching another body:

```python
extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
isChained = True
extent_toentity = adsk.fusion.ToEntityExtentDefinition.create(targetBody, isChained)
extrudeInput.setOneSideExtent(
    extent_toentity,
    adsk.fusion.ExtentDirections.PositiveExtentDirection
)

# Optional: start with offset
start_offset = adsk.fusion.OffsetStartDefinition.create(
    adsk.core.ValueInput.createByString("10 mm")
)
extrudeInput.startExtent = start_offset
extrude = extrudes.add(extrudeInput)
```

### 4. Through-All Extent

Extrude through all geometry:

```python
extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extent_all = adsk.fusion.ThroughAllExtentDefinition.create()
taperAngle = adsk.core.ValueInput.createByString("2 deg")
extrudeInput.setOneSideExtent(
    extent_all,
    adsk.fusion.ExtentDirections.NegativeExtentDirection,
    taperAngle
)
extrude = extrudes.add(extrudeInput)
```

### 5. Symmetric Extent

Equal distance in both directions from profile:

```python
extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
isFullLength = True  # True = total distance, False = distance per side
taperAngle = adsk.core.ValueInput.createByString("5 deg")
extrudeInput.setSymmetricExtent(
    adsk.core.ValueInput.createByString("10 mm"),
    isFullLength,
    taperAngle
)
extrude = extrudes.add(extrudeInput)
```

### 6. Two-Sided Extent

Different distances and taper angles on each side:

```python
extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
extent_side1 = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString("100 mm")
)
extent_side2 = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString("20cm")
)
taper1 = adsk.core.ValueInput.createByString("5 deg")
taper2 = adsk.core.ValueInput.createByString("0 deg")
extrudeInput.setTwoSidesExtent(extent_side1, extent_side2, taper1, taper2)
extrude = extrudes.add(extrudeInput)
```

## ExtrudeFeature Object - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Feature name in browser/timeline |
| `bodies` | BRepBodies | R | Bodies modified or created by feature |
| `endFaces` | BRepFaces | R | Faces capping end of extrusion |
| `startFaces` | BRepFaces | R | Faces coincident with sketch plane |
| `sideFaces` | BRepFaces | R | Side faces perpendicular to extrude direction |
| `faces` | BRepFaces | R | All faces created by feature |
| `extentOne` | ExtentDefinition | R/W | Extent for side one |
| `extentTwo` | ExtentDefinition | R/W | Extent for side two (if two-sided) |
| `extentType` | FeatureExtentTypes | R | How extent is defined |
| `hasTwoExtents` | Boolean | R | Whether two-sided |
| `operation` | FeatureOperations | R/W | NewBody/Join/Cut/Intersect |
| `profile` | Profile | R/W | Profile defining extrude shape |
| `startExtent` | StartDefinition | R/W | Where extrusion starts |
| `taperAngleOne` | Parameter | R | Taper angle for side one |
| `taperAngleTwo` | Parameter | R | Taper angle for side two |
| `isSolid` | Boolean | R | Whether solid or surface |
| `isSuppressed` | Boolean | R/W | Whether suppressed |
| `healthState` | FeatureHealthStates | R | Feature health |
| `errorOrWarningMessage` | String | R | Error/warning message |
| `timelineObject` | TimelineObject | R | Timeline entry |
| `parentComponent` | Component | R | Parent component |
| `isParametric` | Boolean | R | Whether in parametric design |

## ExtrudeFeature Object - Methods

| Method | Description |
|--------|-------------|
| `deleteMe()` | Delete the feature (works for parametric and non-parametric) |
| `dissolve()` | Remove feature, keep only geometry |
| `setOneSideExtent(extentDef, direction, taperAngle)` | Redefine as one-sided |
| `setSymmetricExtent(distance, isFullLength, taperAngle)` | Redefine as symmetric |
| `setTwoSidesExtent(extentOne, extentTwo, taper1, taper2)` | Redefine as two-sided |
| `setThinExtrude(...)` | Change to thin extrude |

## Editing Existing Extrusions

### Edit Distance

```python
disDef = adsk.fusion.DistanceExtentDefinition.cast(extrude.extentOne)
distanceParam = adsk.fusion.ModelParameter.cast(disDef.distance)
distanceParam.value = 5.0  # 5 cm
# or
distanceParam.expression = "80 mm"
```

### Edit Taper Angle

```python
taperParam = adsk.fusion.ModelParameter.cast(extrude.taperAngleOne)
taperParam.expression = "30 deg"
```

### Edit Start Offset

```python
startDef = adsk.fusion.FromEntityStartDefinition.cast(extrude.startExtent)
offsetParam = adsk.fusion.ModelParameter.cast(startDef.offset)
offsetParam.value = 1.5  # 1.5 cm
```

### Edit To-Entity Target

```python
toDef = adsk.fusion.ToEntityExtentDefinition.cast(extrude.extentOne)
extrude.timelineObject.rollTo(True)  # Roll timeline back
toDef.entity = newTargetBody
toDef.isMinimumSolution = False
toDef.isChained = False
design.timeline.moveToEnd()  # Roll forward
```

## Feature Health Check

```python
health = extrude.healthState
if health == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
    msg = extrude.errorOrWarningMessage
elif health == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
    msg = extrude.errorOrWarningMessage
```

## FeatureOperations Enum

| Value | Description |
|-------|-------------|
| `NewBodyFeatureOperation` | Creates a new body |
| `JoinFeatureOperation` | Adds material to existing body |
| `CutFeatureOperation` | Removes material from existing body |
| `IntersectFeatureOperation` | Keeps only intersection |
| `NewComponentFeatureOperation` | Creates in new component |

## ExtentDirections Enum

| Value | Description |
|-------|-------------|
| `PositiveExtentDirection` | Normal direction of sketch plane |
| `NegativeExtentDirection` | Opposite of sketch plane normal |

## Complete 7-Sample Example

See the full working code at the source URL. The sample demonstrates:

1. Simple distance extrusion (`addSimple`)
2. One-side distance extent (`setOneSideExtent` with `DistanceExtentDefinition`)
3. Distance from entity (`FromEntityStartDefinition`)
4. To-entity extent (`ToEntityExtentDefinition`)
5. Through-all extent (`ThroughAllExtentDefinition`)
6. Symmetric extent (`setSymmetricExtent`)
7. Two-sided with different taper angles (`setTwoSidesExtent`)
