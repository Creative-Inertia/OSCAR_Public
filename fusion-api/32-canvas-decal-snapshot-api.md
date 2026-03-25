# Canvas, Decal & Snapshot API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

- **Canvas**: Reference images placed on planes for tracing designs
- **Decal**: Images applied to body surfaces for branding/labels (visual only, not geometry)
- **Snapshot**: Captures a specific position state of an assembly with joints

---

## Canvas

A reference image placed on a plane or face. Used for tracing real-world objects — place a photo and sketch over it.

### Creating a Canvas

```python
canvases = rootComponent.canvases

# Create input
canvasInput = canvases.createInput(
    'C:/path/to/reference_photo.png',  # image filename
    xyPlane  # planar entity: ConstructionPlane or planar BRepFace
)

# Configure
canvasInput.opacity = 50                    # 0=transparent, 100=opaque
canvasInput.isDisplayedThrough = True       # visible through model
canvasInput.isSelectable = False            # non-selectable in viewport
canvasInput.isRenderable = False            # don't include in renders

# Position/scale via transform (Matrix3D)
# The transform controls position, rotation, scale, and flip
# X and Y axes of the matrix define the image's orientation on the plane
canvasInput.transform = someMatrix3D

# Flip helpers
canvasInput.flipHorizontal()
canvasInput.flipVertical()

canvas = canvases.add(canvasInput)
```

### CanvasInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `imageFilename` | str | RW | Full path to the image file |
| `planarEntity` | ConstructionPlane/BRepFace | RW | Plane to place the canvas on |
| `opacity` | int (0-100) | RW | Transparency (0=invisible, 100=solid) |
| `isDisplayedThrough` | bool | RW | Visible through the model (default: True) |
| `isSelectable` | bool | RW | Selectable in viewport (default: False) |
| `isRenderable` | bool | RW | Include in ray-traced renders (default: False) |
| `transform` | Matrix3D | RW | Position, rotation, scale, flip |
| `plane` | Plane | RO | The geometric plane (derived from planarEntity) |
| `creationOccurrence` | Occurrence | RW | Assembly context |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### Canvas Output Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | str | RW | Name in browser/timeline |
| `opacity` | int | RW | Transparency |
| `isLightBulbOn` | bool | RW | Visibility toggle |
| `isVisible` | bool | RO | Whether currently visible (considers parent visibility) |
| `isDisplayedThrough` | bool | RW | Show through model |
| `isSelectable` | bool | RW | Selectable in graphics |
| `isRenderable` | bool | RW | Include in renders |
| `imageFilename` | str | RW | Image file (setting changes the image) |
| `transform` | Matrix3D | RW | Position/scale/orientation |
| `planarEntity` | Entity | RW | The associated plane |
| `plane` | Plane | RO | Geometric plane object |
| `timelineObject` | TimelineObject | RO | Timeline entry |

### Canvas Methods

| Method | Description |
|--------|-------------|
| `flipHorizontal()` | Mirror the image horizontally |
| `flipVertical()` | Mirror the image vertically |
| `saveImage(filename)` | Export the canvas image to a file |
| `deleteMe()` | Remove the canvas |

---

## Decal

An image applied to body surfaces for visual branding. Decals are NOT geometry — they don't export to STL. For geometry text/logos, use EmbossFeature instead.

### Creating a Decal

```python
decals = rootComponent.decals

# Create input
decalInput = decals.createInput(
    'C:/path/to/logo.png',   # image filename
    targetFace               # BRepFace to place decal on
)

# Configure
decalInput.opacity = 1.0        # 0=transparent, 1.0=opaque
decalInput.isChainFaces = True   # wrap onto connected faces

# Position/scale via transform
decalInput.transform = someMatrix3D

# Set specific faces (optional — overrides single face)
faces = [face1, face2]
decalInput.faces = faces

decal = decals.add(decalInput)
```

### DecalInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `imageFilename` | str | RW | Full path to image (PNG recommended) |
| `faces` | list of BRepFace | RW | Faces the decal is placed on |
| `opacity` | float (0-1.0) | RW | Transparency |
| `isChainFaces` | bool | RW | Wrap onto tangent-connected faces |
| `transform` | Matrix3D | RW | Position, rotation, scale |
| `creationOccurrence` | Occurrence | RW | Assembly context |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### Decal Output Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | str | RW | Name in browser/timeline |
| `imageFilename` | str | RW | Image file |
| `faces` | list of BRepFace | RO | Faces the decal covers |
| `isChainFaces` | bool | RO | Whether face chaining is on |
| `isLightBulbOn` | bool | RW | Visibility toggle |
| `isVisible` | bool | RO | Whether currently visible |
| `opacity` | float | RW | Transparency |
| `transform` | Matrix3D | RO | Position/orientation |
| `timelineObject` | TimelineObject | RO | Timeline entry |

### Decal Methods

| Method | Description |
|--------|-------------|
| `redefine(imageFilename, face)` | Change the image and/or target face |
| `saveImage(filename)` | Export the decal image |
| `deleteMe()` | Remove the decal |

### Canvas vs Decal

| Feature | Canvas | Decal |
|---------|--------|-------|
| Purpose | Reference tracing | Visual branding |
| Placed on | Planes | Body faces |
| Follows curvature | No (flat on plane) | Yes (wraps on surface) |
| Opacity range | 0-100 (int) | 0-1.0 (float) |
| Exports to STL | No | No |
| Appears in render | Optional | Yes |

---

## Snapshot

Captures a specific position state of joints in an assembly. Used to record open/closed positions, different configurations, etc.

### Creating a Snapshot

```python
snapshots = design.snapshots  # Note: accessed from Design, not Component

# Create a snapshot of current joint positions
snapshot = snapshots.add()
snapshot.name = 'Open Position'

# Snapshots capture the current state of all joints
# To create different positions:
# 1. Drive joints to position A
# 2. snapshot1 = snapshots.add()
# 3. Drive joints to position B
# 4. snapshot2 = snapshots.add()
```

### Snapshot Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | str | RW | Snapshot name (shown in timeline) |
| `timelineObject` | TimelineObject | RO | Timeline entry |

### Snapshot Methods

| Method | Description |
|--------|-------------|
| `deleteMe()` | Remove the snapshot |

### Snapshots Collection Methods

| Method | Description |
|--------|-------------|
| `add()` | Capture current joint state as a new snapshot |
| `hasPendingSnapshot` | Whether there are unsaved joint position changes |
| `revertPendingSnapshot()` | Revert unsaved joint position changes |

### MeasureManager

Utility for measuring distances and angles between geometry.

```python
mm = app.measureManager

# Measure minimum distance between two entities
result = mm.measureMinimumDistance(entity1, entity2)
# entity can be: Occurrence, BRepBody, BRepFace, BRepEdge, BRepVertex,
#                SketchPoint, ConstructionPoint, ConstructionPlane, etc.
# Returns a MeasureResults object with .value (distance in cm)

# Measure angle between two entities
result = mm.measureAngle(entity1, entity2)
# Returns angle result

# Get oriented bounding box
bbox = mm.getOrientedBoundingBox(geometry, directionOne, directionTwo)
# Returns an OrientedBoundingBox3D
```
