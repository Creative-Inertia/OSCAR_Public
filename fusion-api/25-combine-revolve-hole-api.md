# Fusion 360 API - Combine, Revolve, and Hole Features Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CombineFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CombineFeatures_createInput.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/RevolveFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/RevolveFeatures_createInput.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/HoleFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/HoleFeatures.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/HoleFeatureSample_Sample.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

This reference covers three feature types: **Combine** (boolean operations on existing bodies), **Revolve** (creating bodies by rotating profiles around an axis), and **Hole** (creating various hole types in solid bodies). All are accessed through `rootComp.features`.

---

## Combine Features (Boolean Operations on Existing Bodies)

Combine features perform boolean operations (join, cut, intersect) on bodies that **already exist** as separate entities. This is distinct from setting a `FeatureOperations` value when creating a new extrude or revolve — those operate during feature creation. Combine is for when you have two or more separate bodies and want to merge, subtract, or intersect them after the fact.

### When to Use Combine vs FeatureOperations on Creation

| Scenario | Use This |
|----------|----------|
| Creating a new extrude that should cut into an existing body | `extrudeFeatures.createInput(profile, CutFeatureOperation)` — the cut happens during creation |
| Creating a new revolve that should join with an existing body | `revolveFeatures.createInput(profile, axis, JoinFeatureOperation)` — the join happens during creation |
| You have two separate bodies that were created independently and need to merge them | `combineFeatures` — boolean operation on existing bodies |
| You imported a body and need to subtract it from another body | `combineFeatures` — the bodies already exist |
| You need to find the intersection volume of two existing bodies | `combineFeatures` with `IntersectFeatureOperation` |

### Accessing the CombineFeatures Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

combines = rootComp.features.combineFeatures
```

### CombineFeatures Collection - Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `createInput(targetBody, toolBodies, operation)` | CombineFeatureInput | Creates a new input object defining the combine parameters |
| `add(input)` | CombineFeature | Creates a combine feature from the given input |
| `item(index)` | CombineFeature | Returns the combine feature at the given index |
| `itemByName(name)` | CombineFeature | Returns the combine feature with the given name |
| `count` | int | Number of combine features in the collection |

### CombineFeatures.createInput Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `targetBody` | BRepBody | The body that survives the combine operation. This is the "primary" body. |
| `toolBodies` | ObjectCollection | Collection of BRepBody objects to combine with the target. These are the "secondary" bodies. |
| `operation` | FeatureOperations | The boolean operation: `JoinFeatureOperation`, `CutFeatureOperation`, or `IntersectFeatureOperation` |

### CombineFeatureInput - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `targetBody` | BRepBody | R/W | The target body that will receive the operation result |
| `toolBodies` | ObjectCollection | R/W | Collection of BRepBody objects used as tools |
| `operation` | FeatureOperations | R/W | The boolean operation type |
| `isKeepToolBodies` | Boolean | R/W | If False (default), tool bodies are consumed/removed after the combine. If True, tool bodies remain as separate bodies. |
| `isNewComponent` | Boolean | R/W | If True, the result is placed in a new component. Default is False. |

### CombineFeature Object - Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | The name of the combine feature as shown in the timeline |
| `healthState` | FeatureHealthStates | Current health state of the feature (HealthyFeatureHealthState, WarningFeatureHealthState, ErrorFeatureHealthState) |
| `timelineObject` | TimelineObject | The feature's position in the design timeline |
| `bodies` | BRepBodies | The bodies produced by this feature |
| `targetBody` | BRepBody | The target body used in the combine |
| `toolBodies` | ObjectCollection | The tool bodies used in the combine |
| `operation` | FeatureOperations | The boolean operation that was performed |
| `isKeepToolBodies` | Boolean | Whether tool bodies were kept |
| `isValid` | Boolean | Whether the feature is still valid |
| `errorOrWarningMessage` | str | Error or warning message if the feature is not healthy |

### Complete Example: Combine Two Boxes with Join

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create first box (target body)
sketch1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch1.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(5, 5, 0)
)
prof1 = sketch1.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
ext1 = extrudes.addSimple(
    prof1,
    adsk.core.ValueInput.createByReal(5),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
targetBody = ext1.bodies.item(0)

# Create second box (tool body) — overlapping the first
sketch2 = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch2.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(3, 3, 0),
    adsk.core.Point3D.create(8, 8, 0)
)
prof2 = sketch2.profiles.item(0)
ext2 = extrudes.addSimple(
    prof2,
    adsk.core.ValueInput.createByReal(5),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
toolBody = ext2.bodies.item(0)

# Combine with Join — merges the two overlapping boxes into one body
toolBodies = adsk.core.ObjectCollection.create()
toolBodies.add(toolBody)

combines = rootComp.features.combineFeatures
combineInput = combines.createInput(targetBody, toolBodies,
    adsk.fusion.FeatureOperations.JoinFeatureOperation)
combineInput.isKeepToolBodies = False  # Remove the tool body after join
combineInput.isNewComponent = False

combineFeat = combines.add(combineInput)
# Result: one merged body remains (targetBody is modified in place)
```

### Complete Example: Combine with Cut (Subtract Cylinder from Box)

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create a box (target)
sketch1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch1.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(-5, -5, 0),
    adsk.core.Point3D.create(5, 5, 0)
)
prof1 = sketch1.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
ext1 = extrudes.addSimple(
    prof1,
    adsk.core.ValueInput.createByReal(5),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
targetBody = ext1.bodies.item(0)

# Create a cylinder (tool) — positioned inside the box
sketch2 = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch2.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 2.0
)
prof2 = sketch2.profiles.item(0)
ext2 = extrudes.addSimple(
    prof2,
    adsk.core.ValueInput.createByReal(5),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
toolBody = ext2.bodies.item(0)

# Combine with Cut — subtracts the cylinder from the box
toolBodies = adsk.core.ObjectCollection.create()
toolBodies.add(toolBody)

combines = rootComp.features.combineFeatures
combineInput = combines.createInput(targetBody, toolBodies,
    adsk.fusion.FeatureOperations.CutFeatureOperation)
combineInput.isKeepToolBodies = False  # Tool body is consumed

combineFeat = combines.add(combineInput)
# Result: box with a cylindrical hole cut through it
```

### Combine with Intersect Example

```python
# Using Intersect — keeps only the volume shared by both bodies
combineInput = combines.createInput(targetBody, toolBodies,
    adsk.fusion.FeatureOperations.IntersectFeatureOperation)
combineInput.isKeepToolBodies = False
combineFeat = combines.add(combineInput)
# Result: only the overlapping region remains
```

---

## Revolve Features

Revolve features create solid or surface bodies by rotating a 2D profile around an axis. This is essential for creating cylindrical, conical, and rotationally symmetric shapes like vases, bowls, wheels, and turned parts.

### Accessing the RevolveFeatures Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

revolves = rootComp.features.revolveFeatures
```

### RevolveFeatures Collection - Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `createInput(profile, axis, operation)` | RevolveFeatureInput | Creates a new input object defining the revolve parameters |
| `add(input)` | RevolveFeature | Creates a revolve feature from the given input |
| `item(index)` | RevolveFeature | Returns the revolve feature at the given index |
| `itemByName(name)` | RevolveFeature | Returns the revolve feature with the given name |
| `count` | int | Number of revolve features in the collection |

### RevolveFeatures.createInput Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile` | Profile | A sketch profile to revolve. Must be a closed profile on one side of the axis. |
| `axis` | Base | The axis of revolution. Can be a SketchLine (in the same sketch), a ConstructionAxis, or a linear BRepEdge. |
| `operation` | FeatureOperations | NewBodyFeatureOperation, JoinFeatureOperation, CutFeatureOperation, IntersectFeatureOperation, or NewComponentFeatureOperation |

### Axis Requirements

The axis for a revolve must be one of the following:

| Axis Type | Description |
|-----------|-------------|
| SketchLine | A construction line or regular line **in the same sketch** as the profile. The profile must be entirely on one side of the axis line. |
| ConstructionAxis | A construction axis from `rootComp.constructionAxes` (e.g., X, Y, or Z axis, or a custom construction axis) |
| BRepEdge | A linear edge of an existing body. Must be a straight/linear edge. |

**Important:** If using a SketchLine as the axis, the line and profile must be in the **same sketch**. The profile cannot cross or touch the axis line (it must be entirely on one side).

### RevolveFeatureInput - Properties and Methods

| Property / Method | Type | R/W | Description |
|-------------------|------|-----|-------------|
| `setAngleExtent(isSymmetric, angle)` | — | — | Sets a single angle extent. If `isSymmetric` is True, revolves half the angle on each side of the sketch plane. |
| `setTwoSideAngleExtent(angleOne, angleTwo)` | — | — | Sets different angles on each side of the sketch plane |
| `setFullFeatureExtent()` | — | — | Revolves the full 360° |
| `setOneSideToExtentExtent(toEntity, directionHint)` | — | — | Revolves until it reaches a face, plane, or body |
| `isSolid` | Boolean | R/W | True creates a solid body; False creates a surface body. Default is True. |
| `profile` | Profile | R/W | The sketch profile being revolved |
| `axis` | Base | R/W | The axis of revolution |
| `operation` | FeatureOperations | R/W | The feature operation type |
| `participantBodies` | list of BRepBody | R/W | For Join/Cut/Intersect operations, specifies which existing bodies participate |
| `creationOccurrence` | Occurrence | R/W | The target occurrence when creating in a component context |

### Angle Extent Methods - Detail

#### setAngleExtent(isSymmetric, angle)

| Parameter | Type | Description |
|-----------|------|-------------|
| `isSymmetric` | Boolean | If True, revolves `angle/2` on each side of the sketch plane. If False, revolves `angle` in the positive direction only. |
| `angle` | ValueInput | The angle of revolution (in radians when using `createByReal`, or use `createByString("180 deg")`) |

#### setTwoSideAngleExtent(angleOne, angleTwo)

| Parameter | Type | Description |
|-----------|------|-------------|
| `angleOne` | ValueInput | Angle on the first side of the sketch plane |
| `angleTwo` | ValueInput | Angle on the second side of the sketch plane |

#### setOneSideToExtentExtent(toEntity, directionHint)

| Parameter | Type | Description |
|-----------|------|-------------|
| `toEntity` | Base | The face, plane, or body to revolve to (BRepFace, ConstructionPlane, or BRepBody) |
| `directionHint` | Point3D | A point indicating which direction to revolve toward the target entity |

### RevolveFeature Object - Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Name of the revolve feature in the timeline |
| `healthState` | FeatureHealthStates | Current health state of the feature |
| `timelineObject` | TimelineObject | Position in the design timeline |
| `bodies` | BRepBodies | Bodies produced by this feature |
| `profile` | Profile | The profile that was revolved |
| `axis` | Base | The axis of revolution |
| `isSolid` | Boolean | Whether the result is a solid body |
| `angle` | ModelParameter | The revolve angle (read-only ModelParameter) |
| `isValid` | Boolean | Whether the feature is still valid |
| `errorOrWarningMessage` | str | Error or warning message if unhealthy |
| `faces` | BRepFaces | All faces created or modified by this feature |
| `startFaces` | BRepFaces | Faces at the start of the revolve |
| `endFaces` | BRepFaces | Faces at the end of the revolve |
| `sideFaces` | BRepFaces | Faces along the sides of the revolve |

### Complete Example: Full 360° Revolve to Create a Vase Shape

```python
import adsk.core, adsk.fusion, math

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create sketch on XZ plane (profile will revolve around Y axis)
sketch = rootComp.sketches.add(rootComp.xZConstructionPlane)
lines = sketch.sketchCurves.sketchLines
arcs = sketch.sketchCurves.sketchArcs

# Draw a vase profile (half cross-section)
# Bottom flat
p0 = adsk.core.Point3D.create(0, 0, 0)
p1 = adsk.core.Point3D.create(3, 0, 0)
p2 = adsk.core.Point3D.create(3, 1, 0)
p3 = adsk.core.Point3D.create(2, 3, 0)
p4 = adsk.core.Point3D.create(2.5, 6, 0)
p5 = adsk.core.Point3D.create(3.5, 8, 0)
p6 = adsk.core.Point3D.create(3.5, 9, 0)
p7 = adsk.core.Point3D.create(3, 9, 0)
p8 = adsk.core.Point3D.create(2, 7, 0)
p9 = adsk.core.Point3D.create(1.5, 4, 0)
p10 = adsk.core.Point3D.create(1.5, 1, 0)
p11 = adsk.core.Point3D.create(0, 1, 0)

# Draw the profile lines
lines.addByTwoPoints(p0, p1)
lines.addByTwoPoints(p1, p2)
lines.addByTwoPoints(p2, p3)
lines.addByTwoPoints(p3, p4)
lines.addByTwoPoints(p4, p5)
lines.addByTwoPoints(p5, p6)
lines.addByTwoPoints(p6, p7)
lines.addByTwoPoints(p7, p8)
lines.addByTwoPoints(p8, p9)
lines.addByTwoPoints(p9, p10)
lines.addByTwoPoints(p10, p11)
# Axis line (close the profile along the Y axis)
axisLine = lines.addByTwoPoints(p11, p0)

# Get the profile
prof = sketch.profiles.item(0)

# Create revolve input — full 360°
revolves = rootComp.features.revolveFeatures
revInput = revolves.createInput(
    prof,
    axisLine,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
revInput.setFullFeatureExtent()
revInput.isSolid = True

# Create the revolve
revFeat = revolves.add(revInput)
```

### Complete Example: 180° Symmetric Revolve

```python
import adsk.core, adsk.fusion, math

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create sketch on XY plane
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
lines = sketch.sketchCurves.sketchLines

# Draw a rectangular profile to the right of the Y axis
p0 = adsk.core.Point3D.create(2, -1, 0)
p1 = adsk.core.Point3D.create(5, -1, 0)
p2 = adsk.core.Point3D.create(5, 1, 0)
p3 = adsk.core.Point3D.create(2, 1, 0)

lines.addByTwoPoints(p0, p1)
lines.addByTwoPoints(p1, p2)
lines.addByTwoPoints(p2, p3)
lines.addByTwoPoints(p3, p0)

# Draw axis line along Y axis (must be in same sketch)
axisLine = lines.addByTwoPoints(
    adsk.core.Point3D.create(0, -3, 0),
    adsk.core.Point3D.create(0, 3, 0)
)
# Make the axis a construction line (best practice)
axisLine.isConstruction = True

prof = sketch.profiles.item(0)

# Create revolve — 180° symmetric (90° each side of sketch plane)
revolves = rootComp.features.revolveFeatures
revInput = revolves.createInput(
    prof,
    axisLine,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# 180 degrees = pi radians
angle = adsk.core.ValueInput.createByReal(math.pi)
revInput.setAngleExtent(True, angle)  # True = symmetric
revInput.isSolid = True

revFeat = revolves.add(revInput)
```

### Revolve with Two-Side Angles

```python
# Different angles on each side of the sketch plane
angleOne = adsk.core.ValueInput.createByString("120 deg")
angleTwo = adsk.core.ValueInput.createByString("60 deg")
revInput.setTwoSideAngleExtent(angleOne, angleTwo)
```

### Revolve as Surface Body

```python
# Create a surface of revolution instead of a solid
revInput.isSolid = False
revFeat = revolves.add(revInput)
# Result is a surface body, not a solid
```

---

## Hole Features

Hole features create standard machining holes in solid bodies, including simple holes, counterbore holes, and countersink holes. They can be positioned using sketch points, 3D points, or offsets from edges.

### Accessing the HoleFeatures Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

holes = rootComp.features.holeFeatures
```

### HoleFeatures Collection - Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `createSimpleInput(distance)` | HoleFeatureInput | Creates input for a simple drilled hole with given depth |
| `createCounterboreInput(holeDiameter, counterboreDiameter, counterboreDepth)` | HoleFeatureInput | Creates input for a counterbore hole |
| `createCountersinkInput(holeDiameter, countersinkDiameter, countersinkAngle)` | HoleFeatureInput | Creates input for a countersink hole |
| `add(input)` | HoleFeature | Creates a hole feature from the given input |
| `item(index)` | HoleFeature | Returns the hole feature at the given index |
| `itemByName(name)` | HoleFeature | Returns the hole feature with the given name |
| `count` | int | Number of hole features in the collection |

### createSimpleInput Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `distance` | ValueInput | The depth of the hole. The diameter is set separately via the `holeDiameter` property on the returned input. |

### createCounterboreInput Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `holeDiameter` | ValueInput | Diameter of the main hole |
| `counterboreDiameter` | ValueInput | Diameter of the counterbore (must be larger than holeDiameter) |
| `counterboreDepth` | ValueInput | Depth of the counterbore from the surface |

### createCountersinkInput Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `holeDiameter` | ValueInput | Diameter of the main hole |
| `countersinkDiameter` | ValueInput | Diameter of the countersink at the surface |
| `countersinkAngle` | ValueInput | Angle of the countersink cone (commonly 82° or 90°) |

### HoleFeatureInput - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `holeDiameter` | ValueInput | R/W | The diameter of the hole |
| `tipAngle` | ValueInput | R/W | Drill tip angle at the bottom of the hole. Default is 118°. |
| `isDefaultDirection` | Boolean | R/W | If True, hole goes in default direction (into the face). Set to False to flip direction. |
| `participantBodies` | ObjectCollection | R/W | Collection of BRepBody objects the hole should cut into. Required for multi-body scenarios. |

### HoleFeatureInput - Position Methods

The position of the hole(s) must be set before calling `add()`. Use exactly one of these methods:

| Method | Description |
|--------|-------------|
| `setPositionBySketchPoint(sketchPoint)` | Places a single hole at a sketch point location |
| `setPositionBySketchPoints(sketchPoints)` | Places multiple holes at a collection of sketch points |
| `setPositionAtCenter(circularEdge)` | Places a hole at the center of a circular edge |
| `setPositionByPoint(point)` | Places a hole at a Point3D location on a planar face |
| `setPositionByPlaneAndOffsets(planarFace, offsetOne, offsetTwo)` | Places a hole on a face at specified offsets from two edges |

#### setPositionBySketchPoint(sketchPoint)

| Parameter | Type | Description |
|-----------|------|-------------|
| `sketchPoint` | SketchPoint | A sketch point that defines where the hole center will be. The point must lie on a planar face of a solid body. |

#### setPositionBySketchPoints(sketchPoints)

| Parameter | Type | Description |
|-----------|------|-------------|
| `sketchPoints` | ObjectCollection | Collection of SketchPoint objects. Each point creates a hole at that location. All points must lie on planar faces. |

#### setPositionAtCenter(circularEdge)

| Parameter | Type | Description |
|-----------|------|-------------|
| `circularEdge` | BRepEdge | A circular edge whose center defines the hole position. The edge must be on a planar face. |

#### setPositionByPoint(point)

| Parameter | Type | Description |
|-----------|------|-------------|
| `point` | Point3D | A 3D point on a planar face. The point must lie exactly on a face of a solid body. |

#### setPositionByPlaneAndOffsets(planarFace, offsetOne, offsetTwo)

| Parameter | Type | Description |
|-----------|------|-------------|
| `planarFace` | BRepFace | The planar face where the hole will be placed |
| `offsetOne` | HoleEdgeReference | Offset distance from the first reference edge |
| `offsetTwo` | HoleEdgeReference | Offset distance from the second reference edge |

### HoleFeatureInput - Extent Methods

The extent determines how deep/far the hole goes. Set one of these after setting the position:

| Method | Description |
|--------|-------------|
| `setDistanceExtent(distance)` | Hole goes to a specific depth |
| `setAllExtent(direction)` | Hole goes through the entire body (through-all) |
| `setToExtent(toEntity)` | Hole goes to a specific face or plane |

#### setAllExtent Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `direction` | ExtentDirections | `PositiveExtentDirection` or `NegativeExtentDirection` or `SymmetricExtentDirection` |

### HolePositionDefinition Types

After a hole feature is created, its position can be queried. The `position` property returns one of these types:

| Type | Description |
|------|-------------|
| `SketchPointHolePositionDefinition` | Hole positioned by a single sketch point |
| `SketchPointsHolePositionDefinition` | Hole positioned by multiple sketch points |
| `AtCenterHolePositionDefinition` | Hole positioned at the center of a circular edge |
| `PointHolePositionDefinition` | Hole positioned by a 3D point |
| `PlaneAndOffsetsHolePositionDefinition` | Hole positioned by planar face offsets |
| `OnEdgeHolePositionDefinition` | Hole positioned on an edge |

### ExtentDefinition Types for Holes

| Type | Description |
|------|-------------|
| `DistanceExtentDefinition` | Hole extends to a specified depth |
| `ThroughAllExtentDefinition` | Hole extends through the entire body |
| `ToEntityExtentDefinition` | Hole extends to a specified face, plane, or body |

### Tapped Holes

To create tapped (threaded) holes, use the `holeTapInfo` property on the HoleFeatureInput:

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `holeTapInfo` | HoleTapInfo | R | Returns the tap information object for configuring threads |
| `isTapped` | Boolean | R/W | Set to True to make this a tapped hole |

#### HoleTapInfo Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `threadPitch` | str | R/W | The thread pitch (e.g., "1.5 mm" for M10x1.5) |
| `threadClass` | str | R/W | The thread class/fit (e.g., "6H") |
| `threadDesignation` | str | R/W | Full thread designation (e.g., "M10x1.5") |
| `isModeled` | Boolean | R/W | Whether to model the thread geometry (True) or just mark it (False) |

### HoleFeature Object - Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Name of the hole feature in the timeline |
| `healthState` | FeatureHealthStates | Current health state of the feature |
| `timelineObject` | TimelineObject | Position in the design timeline |
| `bodies` | BRepBodies | Bodies affected by this feature |
| `holeDiameter` | ModelParameter | Diameter of the hole |
| `holeDepth` | ModelParameter | Depth of the hole (for distance extent) |
| `position` | HolePositionDefinition | The position definition used |
| `holeType` | HoleTypes | SimpleHoleType, CounterboreHoleType, or CountersinkHoleType |
| `tipAngle` | ModelParameter | The drill tip angle |
| `counterboreDiameter` | ModelParameter | Counterbore diameter (if counterbore type) |
| `counterboreDepth` | ModelParameter | Counterbore depth (if counterbore type) |
| `countersinkDiameter` | ModelParameter | Countersink diameter (if countersink type) |
| `countersinkAngle` | ModelParameter | Countersink angle (if countersink type) |
| `isValid` | Boolean | Whether the feature is still valid |
| `errorOrWarningMessage` | str | Error or warning message if unhealthy |
| `faces` | BRepFaces | All faces created or modified by this feature |

### Complete Example: Simple Through-All Hole by Sketch Point

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create a box to put a hole in
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(10, 10, 0)
)
prof = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
ext = extrudes.addSimple(
    prof,
    adsk.core.ValueInput.createByReal(3),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# Create a sketch point on the top face for hole position
topFace = ext.endFaces.item(0)
holeSketch = rootComp.sketches.add(topFace)
holeCenter = holeSketch.sketchPoints.add(
    adsk.core.Point3D.create(5, 5, 0)
)

# Create a simple hole — through all
holes = rootComp.features.holeFeatures
holeInput = holes.createSimpleInput(
    adsk.core.ValueInput.createByReal(3)  # depth (used as fallback)
)

# Set hole diameter
holeInput.holeDiameter = adsk.core.ValueInput.createByString("5 mm")

# Set position by sketch point
holeInput.setPositionBySketchPoint(holeCenter)

# Set extent to through-all
holeInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)

# Set tip angle
holeInput.tipAngle = adsk.core.ValueInput.createByString("118 deg")

# Create the hole
holeFeat = holes.add(holeInput)
```

### Complete Example: Counterbore Holes at Multiple Sketch Points

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create a plate (box)
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(20, 10, 0)
)
prof = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
ext = extrudes.addSimple(
    prof,
    adsk.core.ValueInput.createByReal(2),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# Create sketch points for hole locations on the top face
topFace = ext.endFaces.item(0)
holeSketch = rootComp.sketches.add(topFace)

# Add four mounting hole positions
pt1 = holeSketch.sketchPoints.add(adsk.core.Point3D.create(3, 3, 0))
pt2 = holeSketch.sketchPoints.add(adsk.core.Point3D.create(17, 3, 0))
pt3 = holeSketch.sketchPoints.add(adsk.core.Point3D.create(3, 7, 0))
pt4 = holeSketch.sketchPoints.add(adsk.core.Point3D.create(17, 7, 0))

# Collect points
pointCollection = adsk.core.ObjectCollection.create()
pointCollection.add(pt1)
pointCollection.add(pt2)
pointCollection.add(pt3)
pointCollection.add(pt4)

# Create counterbore hole input
holes = rootComp.features.holeFeatures
holeInput = holes.createCounterboreInput(
    adsk.core.ValueInput.createByString("5 mm"),    # hole diameter
    adsk.core.ValueInput.createByString("10 mm"),   # counterbore diameter
    adsk.core.ValueInput.createByString("3 mm")     # counterbore depth
)

# Position at multiple sketch points
holeInput.setPositionBySketchPoints(pointCollection)

# Through-all extent
holeInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)

# Tip angle
holeInput.tipAngle = adsk.core.ValueInput.createByString("118 deg")

# Create the holes
holeFeat = holes.add(holeInput)
# Result: four counterbore holes at the specified locations
```

### Example: Countersink Hole

```python
# Create countersink hole input
holeInput = holes.createCountersinkInput(
    adsk.core.ValueInput.createByString("5 mm"),    # hole diameter
    adsk.core.ValueInput.createByString("10 mm"),   # countersink diameter
    adsk.core.ValueInput.createByString("82 deg")   # countersink angle
)

# Position and extent must still be set
holeInput.setPositionBySketchPoint(sketchPoint)
holeInput.setDistanceExtent(adsk.core.ValueInput.createByString("15 mm"))

holeFeat = holes.add(holeInput)
```

### Example: Hole at Center of Circular Edge

```python
# If you have a cylindrical boss or circular edge, place hole at its center
circularEdge = someFace.edges.item(0)  # get a circular edge

holeInput = holes.createSimpleInput(
    adsk.core.ValueInput.createByString("20 mm")
)
holeInput.holeDiameter = adsk.core.ValueInput.createByString("6 mm")
holeInput.setPositionAtCenter(circularEdge)
holeInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)

holeFeat = holes.add(holeInput)
```

---

## Common Patterns and Tips

### FeatureOperations Enum Values

All three feature types use the same `FeatureOperations` enum:

| Value | Description |
|-------|-------------|
| `adsk.fusion.FeatureOperations.NewBodyFeatureOperation` | Creates a new body (Combine: N/A) |
| `adsk.fusion.FeatureOperations.JoinFeatureOperation` | Joins with an existing body |
| `adsk.fusion.FeatureOperations.CutFeatureOperation` | Cuts from an existing body |
| `adsk.fusion.FeatureOperations.IntersectFeatureOperation` | Keeps only the intersection |
| `adsk.fusion.FeatureOperations.NewComponentFeatureOperation` | Creates a new component |

### Error Handling Pattern

```python
# Always check feature health after creation
feature = combines.add(combineInput)  # or revolves.add() or holes.add()
if feature.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
    app.userInterface.messageBox(
        f'Feature "{feature.name}" has issues: {feature.errorOrWarningMessage}'
    )
```

### Getting Bodies for Combine Operations

```python
# From the root component body list
body1 = rootComp.bRepBodies.item(0)
body2 = rootComp.bRepBodies.item(1)

# From a specific feature
body1 = extrudeFeature1.bodies.item(0)
body2 = extrudeFeature2.bodies.item(0)

# From an occurrence (component instance)
body1 = occurrence.bRepBodies.item(0)
```

### ValueInput Convenience

```python
# By real number (internal units: cm for length, radians for angle)
dist = adsk.core.ValueInput.createByReal(5.0)       # 5 cm
angle = adsk.core.ValueInput.createByReal(3.14159)   # pi radians = 180°

# By string (with units — more readable)
dist = adsk.core.ValueInput.createByString("50 mm")
angle = adsk.core.ValueInput.createByString("180 deg")
diameter = adsk.core.ValueInput.createByString("0.25 in")
```
