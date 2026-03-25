# Move, Scale, Copy & Remove API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

These features manipulate existing bodies by moving, scaling, copying, or removing them. They are parametric alternatives to direct manipulation and appear in the timeline.

---

## MoveFeature

Moves or rotates bodies or faces as a parametric feature in the timeline. Supports six different move definition types.

### Creating a MoveFeature

```python
moveFeats = rootComponent.features.moveFeatures

# Create input with entities to move
entities = adsk.core.ObjectCollection.create()
entities.add(someBody)  # Can contain BRepBody or BRepFace objects (not mixed)

moveInput = moveFeats.createInput(entities)

# Define the move type (pick ONE):
# Option 1: Free move via transformation matrix
moveInput.defineAsFreeMove(transform)  # Matrix3D

# Option 2: Point to point translation
moveInput.defineAsPointToPoint(originPoint, targetPoint)

# Option 3: Point with XYZ offsets
moveInput.defineAsPointToPosition(point, xDistance, yDistance, zDistance)
# xDistance/yDistance/zDistance are ValueInput objects

# Option 4: Rotate around an axis
moveInput.defineAsRotate(axisEntity, angle)
# axisEntity: linear edge, construction axis, etc.
# angle: ValueInput

# Option 5: Translate along an entity direction
moveInput.defineAsTranslateAlongEntity(linearEntity, distance)

# Option 6: Translate by XYZ distances
moveInput.defineAsTranslateXYZ(xDistance, yDistance, zDistance)

moveFeat = moveFeats.add(moveInput)
```

### MoveFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputEntities` | ObjectCollection | RW | Bodies or faces to move (not mixed) |
| `transform` | Matrix3D | RW | The transform matrix (for free move) |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### Move Definition Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `defineAsFreeMove` | transform (Matrix3D) | Arbitrary translation + rotation via matrix |
| `defineAsPointToPoint` | originPoint, targetPoint | Translate from one point to another |
| `defineAsPointToPosition` | point, xDist, yDist, zDist | Offset from a point by XYZ distances |
| `defineAsRotate` | axisEntity, angle | Rotate around an axis |
| `defineAsTranslateAlongEntity` | linearEntity, distance | Translate along a direction |
| `defineAsTranslateXYZ` | xDist, yDist, zDist | Translate by XYZ offsets |

### Note: createInput2

`moveFeatures` also has a `createInput2` method — this is an alternative constructor. Use `createInput` for standard usage.

---

## ScaleFeature

Scales bodies, sketches, or T-Spline bodies uniformly or non-uniformly (per-axis).

### Creating a ScaleFeature

```python
scaleFeats = rootComponent.features.scaleFeatures

# Collect entities to scale
entities = adsk.core.ObjectCollection.create()
entities.add(someBody)  # BRepBody, Sketch, or TSplineBody

# Create input: entities, reference point, scale factor
scaleInput = scaleFeats.createInput(
    entities,
    referencePoint,  # BRepVertex, SketchPoint, or ConstructionPoint
    adsk.core.ValueInput.createByReal(2.0)  # uniform scale factor
)

# For non-uniform scaling:
scaleInput.setToNonUniform(
    adsk.core.ValueInput.createByReal(2.0),  # X scale
    adsk.core.ValueInput.createByReal(1.0),  # Y scale
    adsk.core.ValueInput.createByReal(0.5)   # Z scale
)

scaleFeat = scaleFeats.add(scaleInput)
```

### ScaleFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputEntities` | ObjectCollection | RW | Sketches, BRep bodies, T-Spline bodies |
| `point` | Entity | RW | Scale reference point (BRepVertex, SketchPoint, ConstructionPoint) |
| `scaleFactor` | ValueInput | RW | Uniform scale factor (sets isUniform=true) |
| `isUniform` | bool | RO | Whether scale is uniform |
| `xScale`, `yScale`, `zScale` | ValueInput | RO | Per-axis scale factors (when non-uniform) |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### Methods

| Method | Description |
|--------|-------------|
| `setToNonUniform(xScale, yScale, zScale)` | Set per-axis scale factors |

---

## CopyPasteBody

Copies one or more bodies into a component. This is how you duplicate bodies (e.g., to create symmetric halves, or to move a body into a different component).

### Creating a CopyPasteBody

```python
copyPasteBodies = targetComponent.features.copyPasteBodies

# Copy a single body
copyPasteFeat = copyPasteBodies.add(sourceBody)  # BRepBody

# Copy multiple bodies
bodiesCollection = adsk.core.ObjectCollection.create()
bodiesCollection.add(body1)
bodiesCollection.add(body2)
copyPasteFeat = copyPasteBodies.add(bodiesCollection)
```

### CopyPasteBody Output Properties

| Property | Type | Description |
|----------|------|-------------|
| `sourceBody` | ObjectCollection | The original bodies that were copied |
| `bodies` | BRepBodies | The newly created copy bodies |

### Key Usage

CopyPasteBody is the standard way to:
- Move a body from root component into a sub-component
- Duplicate a body for symmetric designs
- Create a working copy before destructive operations

---

## RemoveFeature

Removes a body or component occurrence from the design. Appears in the timeline and can be suppressed to bring the body back.

### Creating a RemoveFeature

```python
removeFeats = rootComponent.features.removeFeatures

# Remove a body
removeFeat = removeFeats.add(bodyToRemove)  # BRepBody

# Remove a component occurrence
removeFeat = removeFeats.add(occurrenceToRemove)  # Occurrence
```

### RemoveFeature Output Properties

| Property | Type | Description |
|----------|------|-------------|
| `itemToRemove` | Entity | The body or occurrence that was removed |

### Note

This is different from `deleteMe()` — RemoveFeature is parametric and appears in the timeline. You can suppress it to restore the removed item. `deleteMe()` is permanent.

---

## DeleteFaceFeature (Surface Delete Face)

Deletes faces from a body and attempts to heal the remaining body. Equivalent to selecting and deleting faces in the Patch workspace.

### Creating a DeleteFaceFeature

```python
deleteFaceFeats = rootComponent.features.deleteFaceFeatures

# Delete specific faces
faces = adsk.core.ObjectCollection.create()
faces.add(faceToDelete)
deleteFaceFeat = deleteFaceFeats.add(faces)  # BRepFace or ObjectCollection
```

### Note

The operation will fail if the body cannot be healed after face deletion. This is primarily a surface modeling tool.
