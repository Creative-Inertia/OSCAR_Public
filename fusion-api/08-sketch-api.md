# Fusion 360 API - Sketch API Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CreateSketchLines_Sample.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchLine.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Creating a Sketch

Sketches are created on construction planes or planar faces:

```python
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create sketch on XY plane
sketches = rootComp.sketches
xyPlane = rootComp.xYConstructionPlane
sketch = sketches.add(xyPlane)

# Create sketch on XZ plane
sketch_xz = sketches.add(rootComp.xZConstructionPlane)

# Create sketch on YZ plane
sketch_yz = sketches.add(rootComp.yZConstructionPlane)

# Create sketch on a planar face
face = body.faces.item(0)
sketch_on_face = sketches.add(face)
```

## Sketch Object - Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | String | Name shown in browser/timeline |
| `profiles` | ProfileCollection | Closed regions computed from sketch curves |
| `sketchCurves` | SketchCurves | All sketch geometry (lines, circles, arcs, etc.) |
| `sketchPoints` | SketchPoints | All sketch points |
| `sketchDimensions` | SketchDimensions | All dimensional constraints |
| `geometricConstraints` | GeometricConstraints | All geometric constraints |
| `sketchTexts` | SketchTexts | Text elements in sketch |
| `isFullyConstrained` | Boolean | Whether sketch is fully constrained |
| `isComputeDeferred` | Boolean | Temporarily disable compute for performance |
| `origin` | Point3D | Sketch origin in model space |
| `transform` | Matrix3D | Sketch-to-model-space transform |
| `parentComponent` | Component | Parent component |
| `referencePlane` | Object | The plane or face the sketch is on |

## Sketch Object - Key Methods

| Method | Description |
|--------|-------------|
| `deleteMe()` | Delete the sketch |
| `findConnectedCurves(curve)` | Find curves connected at endpoints |
| `importSVG(filePath, x, y, scale)` | Import SVG into sketch |
| `include(entity)` | Project entity into sketch (create reference) |
| `project2(entities)` | Project entities onto sketch plane |
| `modelToSketchSpace(point)` | Convert model space point to sketch space |
| `sketchToModelSpace(point)` | Convert sketch space point to model space |
| `copy(entities, transform)` | Copy sketch entities with transform |
| `move(entities, transform)` | Move sketch entities |
| `setConstructionState(entities, isConstruction)` | Set construction state |
| `autoConstrain()` | Auto-constrain sketch geometry |
| `saveAsDXF(filePath)` | Export sketch as DXF (retired) |

## Drawing Lines

### SketchLines Collection

Access via `sketch.sketchCurves.sketchLines`

#### addByTwoPoints(startPoint, endPoint)

```python
lines = sketch.sketchCurves.sketchLines
line1 = lines.addByTwoPoints(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(3, 1, 0)
)

# Connect lines using shared sketch points
line2 = lines.addByTwoPoints(
    line1.endSketchPoint,  # Use end point of previous line
    adsk.core.Point3D.create(1, 4, 0)
)
```

#### addTwoPointRectangle(point1, point2)

Creates a rectangle from two diagonal corner points. Returns `SketchLineList` with 4 lines.

```python
lines = sketch.sketchCurves.sketchLines
recLines = lines.addTwoPointRectangle(
    adsk.core.Point3D.create(4, 0, 0),
    adsk.core.Point3D.create(7, 2, 0)
)
# recLines has 4 items: bottom, right, top, left
```

#### addThreePointRectangle(point1, point2, point3)

Creates a rectangle defined by three points (first two define one edge, third defines width).

```python
recLines = lines.addThreePointRectangle(
    adsk.core.Point3D.create(8, 0, 0),
    adsk.core.Point3D.create(11, 1, 0),
    adsk.core.Point3D.create(9, 3, 0)
)
```

#### addCenterPointRectangle(centerPoint, cornerPoint)

Creates a rectangle from center and corner point. Returns `SketchLineList` with 4 lines.

```python
recLines = lines.addCenterPointRectangle(
    adsk.core.Point3D.create(14, 3, 0),  # center
    adsk.core.Point3D.create(16, 4, 0)   # corner
)
```

## Drawing Circles

### SketchCircles Collection

Access via `sketch.sketchCurves.sketchCircles`

#### addByCenterRadius(center, radius)

```python
circles = sketch.sketchCurves.sketchCircles
circle = circles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0),  # center
    5.0  # radius in cm (internal units)
)
```

#### addByTwoTangents(line1, line2, radius, hintPoint)

Creates a circle tangent to two lines.

```python
lines = sketch.sketchCurves.sketchLines
line1 = lines.addByTwoPoints(
    adsk.core.Point3D.create(-10, 0, 0),
    adsk.core.Point3D.create(10, 0, 0)
)
line2 = lines.addByTwoPoints(
    adsk.core.Point3D.create(0, -10, 0),
    adsk.core.Point3D.create(0, 10, 0)
)

hintPoint = adsk.core.Point3D.create(5, 5, 0)
circles = sketch.sketchCurves.sketchCircles
circle = circles.addByTwoTangents(line1, line2, 5, hintPoint)

# Add tangent constraints explicitly
geomConstraints = sketch.geometricConstraints
geomConstraints.addTangent(line1, circle)
geomConstraints.addTangent(line2, circle)
```

#### addByThreePoints(point1, point2, point3)

Creates a circle through three points.

#### addByTwoPoints(point1, point2)

Creates a circle with the two points defining the diameter.

## Drawing Arcs

### SketchArcs Collection

Access via `sketch.sketchCurves.sketchArcs`

| Method | Description |
|--------|-------------|
| `addByCenterStartSweep(center, startPt, sweepAngle)` | Arc from center, start point, sweep angle |
| `addByThreePoints(startPt, midPt, endPt)` | Arc through three points |
| `addFillet(curve1, curve2, radius)` | Fillet arc between two curves |

```python
arcs = sketch.sketchCurves.sketchArcs
arc = arcs.addByCenterStartSweep(
    adsk.core.Point3D.create(0, 0, 0),   # center
    adsk.core.Point3D.create(5, 0, 0),   # start
    math.pi / 2                           # 90 degrees in radians
)
```

## Drawing Splines

### SketchFittedSplines Collection

Access via `sketch.sketchCurves.sketchFittedSplines`

```python
splines = sketch.sketchCurves.sketchFittedSplines

# Create points collection
points = adsk.core.ObjectCollection.create()
points.add(adsk.core.Point3D.create(0, 0, 0))
points.add(adsk.core.Point3D.create(2, 3, 0))
points.add(adsk.core.Point3D.create(5, 2, 0))
points.add(adsk.core.Point3D.create(7, 5, 0))

spline = splines.add(points)
```

## Sketch Constraints

### Geometric Constraints

Access via `sketch.geometricConstraints`

| Method | Description |
|--------|-------------|
| `addHorizontal(line)` | Make line horizontal |
| `addVertical(line)` | Make line vertical |
| `addPerpendicular(line1, line2)` | Make lines perpendicular |
| `addParallel(line1, line2)` | Make lines parallel |
| `addCoincident(point, entity)` | Coincidence constraint |
| `addConcentric(circle1, circle2)` | Make circles concentric |
| `addCollinear(line1, line2)` | Make lines collinear |
| `addTangent(curve1, curve2)` | Tangent constraint |
| `addEqual(curve1, curve2)` | Equal length/radius |
| `addSymmetry(entity1, entity2, line)` | Symmetry about line |
| `addMidPoint(point, line)` | Point at midpoint |
| `addSmooth(curve1, curve2)` | Smooth (G2) continuity |
| `addFix(entity)` | Fix entity position |

```python
geom = sketch.geometricConstraints

# Make rectangle edges horizontal/vertical
geom.addHorizontal(recLines.item(0))
geom.addHorizontal(recLines.item(2))
geom.addVertical(recLines.item(1))
geom.addVertical(recLines.item(3))
```

### Dimensional Constraints

Access via `sketch.sketchDimensions`

| Method | Description |
|--------|-------------|
| `addDistanceDimension(point1, point2, orientation, textPosition)` | Distance between entities |
| `addAngularDimension(line1, line2, textPosition)` | Angle between lines |
| `addDiameterDimension(circle, textPosition)` | Circle/arc diameter |
| `addRadialDimension(circle, textPosition)` | Circle/arc radius |
| `addConcentricCircleDimension(circle1, circle2, textPos)` | Between concentric circles |
| `addOffsetDimension(line1, line2, textPosition)` | Offset between parallel lines |
| `addEllipseMajorRadiusDimension(ellipse, textPosition)` | Ellipse major radius |
| `addEllipseMinorRadiusDimension(ellipse, textPosition)` | Ellipse minor radius |

```python
dims = sketch.sketchDimensions

# Distance dimension
dims.addDistanceDimension(
    recLines.item(0).startSketchPoint,
    recLines.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(5.5, -1, 0)  # text position
)
```

### DimensionOrientations Enum

| Value | Description |
|-------|-------------|
| `HorizontalDimensionOrientation` | Horizontal dimension |
| `VerticalDimensionOrientation` | Vertical dimension |
| `AlignedDimensionOrientation` | Aligned to entities |

## Sketch Profiles

Profiles are automatically computed closed regions from sketch curves:

```python
# Get all profiles in sketch
profiles = sketch.profiles

# Get first profile (for single-profile sketches)
prof = sketch.profiles.item(0)

# For sketches with concentric shapes (like ring profiles):
# profiles.item(0) is typically the inner region
# profiles.item(1) is typically the outer ring region
```

## Performance Optimization

For complex sketches with many operations, defer computation:

```python
sketch.isComputeDeferred = True

# ... create many sketch entities ...

sketch.isComputeDeferred = False  # triggers recompute
```

## SketchLine Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `startSketchPoint` | SketchPoint | Start point (shared with connected lines) |
| `endSketchPoint` | SketchPoint | End point (shared with connected lines) |
| `geometry` | Line3D | Transient line geometry in sketch space |
| `worldGeometry` | Line3D | Line geometry in world (model) space |
| `length` | Double | Length in centimeters |
| `isConstruction` | Boolean | Whether construction line |
| `isCenterLine` | Boolean | Whether center line |
| `isFixed` | Boolean | Whether fixed (immovable) |
| `isFullyConstrained` | Boolean | Whether fully constrained |
| `parentSketch` | Sketch | Parent sketch |

## Complete Example: Sketch with Lines, Rectangle, Constraints, Dimensions

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = app.activeProduct
        rootComp = design.rootComponent

        # Create sketch on XY plane
        sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)

        # Draw two connected lines
        lines = sketch.sketchCurves.sketchLines
        line1 = lines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(3, 1, 0)
        )
        line2 = lines.addByTwoPoints(
            line1.endSketchPoint,
            adsk.core.Point3D.create(1, 4, 0)
        )

        # Draw rectangle
        recLines = lines.addTwoPointRectangle(
            adsk.core.Point3D.create(4, 0, 0),
            adsk.core.Point3D.create(7, 2, 0)
        )

        # Add constraints
        sketch.geometricConstraints.addHorizontal(recLines.item(0))
        sketch.geometricConstraints.addHorizontal(recLines.item(2))
        sketch.geometricConstraints.addVertical(recLines.item(1))
        sketch.geometricConstraints.addVertical(recLines.item(3))

        # Add dimension
        sketch.sketchDimensions.addDistanceDimension(
            recLines.item(0).startSketchPoint,
            recLines.item(0).endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            adsk.core.Point3D.create(5.5, -1, 0)
        )

        # Draw center-point rectangle
        recLines2 = lines.addCenterPointRectangle(
            adsk.core.Point3D.create(14, 3, 0),
            adsk.core.Point3D.create(16, 4, 0)
        )
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```
