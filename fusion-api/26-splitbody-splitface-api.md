# Split Body, Split Face & Silhouette Split API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20
> Verified against: adsk.fusion Python module

## Overview

Split features divide existing geometry into multiple parts. These are essential for multi-component designs where you model one unified shape and then split it into separate bodies or components (the "sculpt-then-split" workflow seen in professional designs).

**When to use instead of building separately:**
- When parts need to mate perfectly (split guarantees matching surfaces)
- When visual flow must be continuous across part boundaries
- When splitting an imported or sculpted body into functional components

---

## SplitBodyFeature

Splits one or more solid/open bodies using a splitting tool (plane, surface, or body).

### Creating a SplitBody

```python
# Get the features collection
splitBodyFeats = rootComponent.features.splitBodyFeatures

# Create input
splitBodyInput = splitBodyFeats.createInput(
    splitBodies,      # BRepBody or ObjectCollection of bodies to split
    splittingTool,    # BRepBody, ConstructionPlane, or BRepFace
    isSplitToolExtended  # bool: auto-extend the tool to fully intersect?
)

# Execute
splitBodyFeat = splitBodyFeats.add(splitBodyInput)
```

### SplitBodyFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `splitBodies` | BRepBody or ObjectCollection | RW | Bodies to be split |
| `splittingTool` | BRepBody, ConstructionPlane, or BRepFace | RW | Entity that defines where to cut |
| `isSplittingToolExtended` | bool | RW | Auto-extend tool to fully intersect the body |
| `targetBaseFeature` | BaseFeature | RW | Associate with a base feature (for base feature context) |

### SplitBodyFeature Output Properties

| Property | Type | Description |
|----------|------|-------------|
| `bodies` | BRepBodies | Bodies created/modified by the split |
| `splitBodies` | ObjectCollection | The input bodies that were split |
| `splittingTool` | Entity | The splitting tool used |
| `isSplittingToolExtended` | bool | Whether tool was auto-extended |

### Typical Usage Pattern

```python
# Split a sculpted form at the midplane to create left/right halves
body = rootComponent.bRepBodies.item(0)
midplane = rootComponent.yZConstructionPlane  # or a custom ConstructionPlane

splitInput = splitBodyFeats.createInput(body, midplane, True)
splitFeat = splitBodyFeats.add(splitInput)

# Result: original body is split into two bodies
# Access them via splitFeat.bodies or rootComponent.bRepBodies
```

---

## SplitFaceFeature

Splits faces on a body without splitting the entire body. Useful for applying different appearances to different regions of the same body.

### Creating a SplitFace

```python
splitFaceFeats = rootComponent.features.splitFaceFeatures
splitFaceInput = splitFaceFeats.createInput(
    facesToSplit,     # ObjectCollection of BRepFace objects
    splittingTool,    # ObjectCollection: bodies, planes, sketch curves, edges
    isSplitToolExtended  # bool
)

# Set split type (determines how tool projects onto faces)
splitFaceInput.setSurfaceIntersectionSplitType()  # default
# OR
splitFaceInput.setAlongVectorSplitType(directionEntity)  # project along a direction
# OR
splitFaceInput.setClosestPointSplitType()  # project to closest point

splitFaceFeat = splitFaceFeats.add(splitFaceInput)
```

### SplitFaceFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `facesToSplit` | ObjectCollection of BRepFace | RW | Faces to split |
| `splittingTool` | ObjectCollection | RW | Tools: bodies, planes, sketch curves, edges |
| `isSplittingToolExtended` | bool | RW | Auto-extend tool |
| `splitType` | SplitFaceSplitTypes | RO | Current split type |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### Split Type Methods

| Method | Description |
|--------|-------------|
| `setSurfaceIntersectionSplitType()` | Surface-to-surface intersection (default) |
| `setAlongVectorSplitType(directionEntity)` | Project tool along a direction |
| `setClosestPointSplitType()` | Project to closest point on surface |

### SplitFaceSplitTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `surfaceIntersectionSplitType` | 0 | Surface intersection |
| `alongVectorSplitType` | 1 | Along a vector direction |
| `closestPointSplitType` | 2 | Closest point projection |

---

## SilhouetteSplitFeature

Splits a body along its silhouette from a given view direction. Useful for creating mold parting lines or separating a body into "top" and "bottom" halves based on draft direction.

### Creating a SilhouetteSplit

```python
silSplitFeats = rootComponent.features.silhouetteSplitFeatures
silSplitInput = silSplitFeats.createInput(
    targetBody,      # BRepBody to split
    viewDirection    # ConstructionAxis, linear BRepEdge, planar BRepFace, or ConstructionPlane
)
silSplitInput.operation = adsk.fusion.SilhouetteSplitOperations.SilhouetteSplitSolidBodyOperation

silSplitFeat = silSplitFeats.add(silSplitInput)
```

### SilhouetteSplitFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `targetBody` | BRepBody | RW | Solid body to split |
| `viewDirection` | Entity | RW | Defines the silhouette view direction |
| `operation` | SilhouetteSplitOperations | RW | Type of split operation |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### SilhouetteSplitOperations Enum

| Value | Int | Description |
|-------|-----|-------------|
| `SilhouetteSplitFacesOnlyOperation` | 0 | Split faces only (no body split) |
| `SilhouetteSplitShelledBodyOperation` | 1 | Split and shell the body |
| `SilhouetteSplitSolidBodyOperation` | 2 | Split the solid body |
