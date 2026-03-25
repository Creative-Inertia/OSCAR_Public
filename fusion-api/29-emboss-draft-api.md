# Emboss & Draft Feature API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

- **Emboss**: Projects sketch profiles (text, logos, shapes) onto curved surfaces, creating raised or recessed geometry.
- **Draft**: Adds draft angles to faces, essential for injection molding and manufacturing.

---

## EmbossFeature

Wraps sketch geometry onto a body's faces, creating raised (positive depth) or engraved (negative depth) features that follow the surface curvature.

### When to Use

- Adding text/logos to curved surfaces (bottles, handles, cases)
- Creating raised or recessed patterns that conform to a surface
- Any geometry that needs to "wrap" onto a non-planar face

**Use Emboss instead of Decals when** the text/logo needs actual 3D geometry (visible in STL export for 3D printing). Use Decals for visual-only branding.

### Creating an EmbossFeature

```python
embossFeats = rootComponent.features.embossFeatures

# Create a sketch with text or profile on a plane near the target face
sketch = rootComponent.sketches.add(somePlane)
texts = sketch.sketchTexts
textInput = texts.createInput2('OSCAR', 1.0)  # text, height in cm
textInput.setAsMultiLine(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(5, 0, 0),
    adsk.core.Point3D.create(5, 1, 0),
    adsk.core.Point3D.create(0, 1, 0),
    adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
    adsk.core.VerticalAlignments.MiddleVerticalAlignment
)
text = texts.add(textInput)

# Get the profile from the sketch text
profiles = []
profiles.append(text)  # SketchText objects work directly

# Set up the target faces
targetFaces = []
targetFaces.append(curvedFace)  # BRepFace on the target body

# Create emboss input
embossInput = embossFeats.createInput(profiles, targetFaces)

# Configure
embossInput.depth = adsk.core.ValueInput.createByString('0.5 mm')  # positive = raised
embossInput.isTangentChain = True  # include tangent-connected faces

# Optional: offset position
embossInput.horizontalDistance = adsk.core.ValueInput.createByString('0 mm')
embossInput.verticalDistance = adsk.core.ValueInput.createByString('0 mm')
embossInput.rotationAngle = adsk.core.ValueInput.createByString('0 deg')

embossFeat = embossFeats.add(embossInput)
```

### EmbossFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `profiles` | array of Profile/SketchText | RW | Shape(s) to emboss |
| `inputFaces` | array of BRepFace | RW | Target faces for embossing |
| `depth` | ValueInput | RW | Emboss depth (positive = raised, negative = recessed) |
| `isTangentChain` | bool | RW | Include tangent-connected faces (default: True) |
| `horizontalDistance` | ValueInput | RW | Horizontal offset (default: 0) |
| `verticalDistance` | ValueInput | RW | Vertical offset (default: 0) |
| `rotationAngle` | ValueInput | RW | Rotation angle (default: 0) |
| `creationOccurrence` | Occurrence | RW | For assembly context |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### Notes

- Emboss profiles can be `Profile` objects from sketches OR `SketchText` objects
- When using multiple profiles, they must all be from the same sketch
- The emboss wraps the 2D profile onto the 3D surface — it follows curvature
- For large text on tight curves, the geometry may fail if the wrapping distortion is too extreme

---

## DraftFeature

Adds draft angles to selected faces. Draft is the slight taper added to vertical walls so that parts can be ejected from molds. Also useful for aesthetic tapers on 3D-printed parts.

### When to Use

- Injection-molded part design (standard 1-3° draft)
- Creating tapered walls on containers, boxes, enclosures
- Adding visual taper to extruded features

### Creating a DraftFeature

```python
draftFeats = rootComponent.features.draftFeatures

# Select faces to draft
faces = adsk.core.ObjectCollection.create()
faces.add(verticalFace)  # BRepFace objects

# Create input: faces, pull direction plane, angle
draftInput = draftFeats.createInput(
    faces,
    pullDirectionPlane  # ConstructionPlane, BRepFace — defines the "pull" direction
)

# Single angle draft (same angle both sides)
draftInput.setSingleAngle(
    False,  # isSymmetric: if True, faces are split along the plane
    adsk.core.ValueInput.createByString('2 deg')  # draft angle
)

# OR two-angle draft (different angles on each side of the plane)
draftInput.setTwoAngles(
    adsk.core.ValueInput.createByString('2 deg'),   # angle one
    adsk.core.ValueInput.createByString('3 deg')    # angle two
)

# Optional: flip direction
draftInput.isDirectionFlipped = False

draftFeat = draftFeats.add(draftInput)
```

### DraftFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputFaces` | ObjectCollection of BRepFace | RW | Faces to apply draft to |
| `plane` | ConstructionPlane or BRepFace | RW | Pull direction (draft reference plane) |
| `angleOne` | ValueInput | RO | First/only angle (use setSingleAngle/setTwoAngles to set) |
| `angleTwo` | ValueInput | RO | Second angle (only for two-angle mode) |
| `isTangentChain` | bool | RW | Include tangent-connected faces (default: True) |
| `isDirectionFlipped` | bool | RW | Flip the draft direction (default: False) |
| `isSymmetric` | bool | RO | Whether symmetric mode is active |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### Draft Definition Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `setSingleAngle` | isSymmetric (bool), angle (ValueInput) | Single angle for all faces |
| `setTwoAngles` | angle1 (ValueInput), angle2 (ValueInput) | Different angles each side of plane |

### Typical Draft Angles

| Application | Typical Angle |
|-------------|---------------|
| Injection molding | 1-3° |
| 3D printing (FDM) | Not required, but 1-2° improves overhangs |
| Die casting | 1-3° |
| Visual taper | 3-10° |
