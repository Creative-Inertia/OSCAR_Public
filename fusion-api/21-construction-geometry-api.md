# Fusion 360 API - Construction Geometry Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ConstructionPlane.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ConstructionAxis.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ConstructionPoint.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ConstructionPlaneInput.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Construction geometry provides reference planes, axes, and points used to position sketches, features, and other geometry. Every component has built-in origin construction geometry (three planes, three axes, one origin point). Additional construction geometry can be created programmatically through the ConstructionPlanes, ConstructionAxes, and ConstructionPoints collections.

## Built-In Construction Geometry

Every component has default origin construction geometry accessible as properties on the Component object.

### Origin Planes

| Property | Type | Description |
|----------|------|-------------|
| `xYConstructionPlane` | ConstructionPlane | The XY plane (Z = 0) |
| `xZConstructionPlane` | ConstructionPlane | The XZ plane (Y = 0) |
| `yZConstructionPlane` | ConstructionPlane | The YZ plane (X = 0) |

### Origin Axes

| Property | Type | Description |
|----------|------|-------------|
| `xConstructionAxis` | ConstructionAxis | The X axis |
| `yConstructionAxis` | ConstructionAxis | The Y axis |
| `zConstructionAxis` | ConstructionAxis | The Z axis |

### Origin Point

| Property | Type | Description |
|----------|------|-------------|
| `originConstructionPoint` | ConstructionPoint | The origin point (0, 0, 0) |

### Accessing Built-In Geometry

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Access origin planes
xyPlane = rootComp.xYConstructionPlane
xzPlane = rootComp.xZConstructionPlane
yzPlane = rootComp.yZConstructionPlane

# Access origin axes
xAxis = rootComp.xConstructionAxis
yAxis = rootComp.yConstructionAxis
zAxis = rootComp.zConstructionAxis

# Access origin point
origin = rootComp.originConstructionPoint

# Common use: create a sketch on the XY plane
sketch = rootComp.sketches.add(xyPlane)
```

## ConstructionPlane Object

Represents a single construction plane in the design.

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Name displayed in the browser |
| `geometry` | Plane | R | The underlying infinite plane geometry |
| `isVisible` | Boolean | R/W | Whether visible in the canvas |
| `isLightBulbOn` | Boolean | R/W | Light bulb state in the browser |
| `parent` | Component | R | Parent component |
| `healthState` | FeatureHealthStates | R | Health state of the feature |
| `errorOrWarningMessage` | String | R | Error or warning message if unhealthy |
| `timelineObject` | TimelineObject | R | Associated timeline object |
| `definition` | ConstructionPlaneDefinition | R | Definition describing how it was created |

| Method | Description |
|--------|-------------|
| `deleteMe()` | Deletes the construction plane |

## Construction Planes

The `ConstructionPlanes` collection on a component provides access to all user-created construction planes and the ability to create new ones.

```python
constructionPlanes = rootComp.constructionPlanes
```

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput()` | ConstructionPlaneInput | Creates an input object to define a new plane |
| `add(input)` | ConstructionPlane | Creates the construction plane from the input |
| `item(index)` | ConstructionPlane | Gets plane by index |
| `itemByName(name)` | ConstructionPlane | Gets plane by name |
| `count` | Integer | Number of user-created construction planes |

### ConstructionPlaneInput Methods

The `ConstructionPlaneInput` object defines how a construction plane is created. Call one of the `setBy...` methods to configure it before passing to `add()`.

| Method | Parameters | Description |
|--------|-----------|-------------|
| `setByOffset(planarEntity, offset)` | `planarEntity`: ConstructionPlane or BRepFace; `offset`: ValueInput | Offset from an existing plane or planar face |
| `setByAngle(linearEntity, angle, planarEntity)` | `linearEntity`: edge or axis; `angle`: ValueInput; `planarEntity`: plane or face | At an angle to a plane, rotated around an edge/axis |
| `setByTwoPlanes(planeOne, planeTwo)` | `planeOne`, `planeTwo`: ConstructionPlane or BRepFace | Midplane between two parallel planes |
| `setByThreePoints(pointOne, pointTwo, pointThree)` | Three ConstructionPoint, BRepVertex, or SketchPoint objects | Through three points |
| `setByTwoEdges(edgeOne, edgeTwo)` | `edgeOne`, `edgeTwo`: BRepEdge or SketchLine | Through two linear edges |
| `setByTangent(face, angle, tangentFace)` | `face`: cylindrical/conical BRepFace; `angle`: ValueInput; `tangentFace`: planar face for angle reference | Tangent to a cylindrical or conical face |
| `setByTangentAtPoint(face, point)` | `face`: BRepFace; `point`: ConstructionPoint, BRepVertex, or SketchPoint | Tangent to a face at a specific point |
| `setByDistanceOnPath(pathEntity, distance)` | `pathEntity`: BRepEdge or SketchCurve; `distance`: ValueInput | Perpendicular to a path at a distance along it |

### Example: Offset Construction Plane

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Create a construction plane offset 3 cm from the XY plane
planes = rootComp.constructionPlanes
planeInput = planes.createInput()

# Offset distance (3 cm = 3.0 internal units)
offsetValue = adsk.core.ValueInput.createByReal(3.0)
planeInput.setByOffset(rootComp.xYConstructionPlane, offsetValue)

offsetPlane = planes.add(planeInput)
offsetPlane.name = 'Offset Plane 3cm'
```

### Example: Construction Plane at Angle

```python
# Create a plane at 45 degrees to the XY plane, rotated around the X axis
planes = rootComp.constructionPlanes
planeInput = planes.createInput()

angle = adsk.core.ValueInput.createByString('45 deg')
planeInput.setByAngle(
    rootComp.xConstructionAxis,   # rotate around this axis
    angle,                         # angle of rotation
    rootComp.xYConstructionPlane   # reference plane
)

angledPlane = planes.add(planeInput)
angledPlane.name = 'Angled 45deg Plane'
```

### Example: Midplane Between Two Planes

```python
# Create a midplane between two offset planes
planes = rootComp.constructionPlanes

# First, create two offset planes to use as references
input1 = planes.createInput()
input1.setByOffset(rootComp.xYConstructionPlane, adsk.core.ValueInput.createByReal(2.0))
plane1 = planes.add(input1)

input2 = planes.createInput()
input2.setByOffset(rootComp.xYConstructionPlane, adsk.core.ValueInput.createByReal(6.0))
plane2 = planes.add(input2)

# Now create the midplane
midInput = planes.createInput()
midInput.setByTwoPlanes(plane1, plane2)
midPlane = planes.add(midInput)
midPlane.name = 'Midplane'
```

### Example: Construction Plane Through Three Points

```python
# Create a plane through three sketch points
planes = rootComp.constructionPlanes

# First create a sketch with three points
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
pt1 = sketch.sketchPoints.add(adsk.core.Point3D.create(0, 0, 0))
pt2 = sketch.sketchPoints.add(adsk.core.Point3D.create(5, 0, 2))
pt3 = sketch.sketchPoints.add(adsk.core.Point3D.create(0, 5, 3))

# Create the plane through the three points
planeInput = planes.createInput()
planeInput.setByThreePoints(pt1, pt2, pt3)
threePtPlane = planes.add(planeInput)
threePtPlane.name = 'Three Point Plane'
```

## ConstructionAxis Object

Represents a single construction axis in the design.

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Name displayed in the browser |
| `geometry` | InfiniteLine3D | R | The underlying infinite line geometry |
| `isVisible` | Boolean | R/W | Whether visible in the canvas |
| `isLightBulbOn` | Boolean | R/W | Light bulb state in the browser |
| `parent` | Component | R | Parent component |
| `healthState` | FeatureHealthStates | R | Health state of the feature |
| `errorOrWarningMessage` | String | R | Error or warning message if unhealthy |
| `timelineObject` | TimelineObject | R | Associated timeline object |
| `definition` | ConstructionAxisDefinition | R | Definition describing how it was created |

| Method | Description |
|--------|-------------|
| `deleteMe()` | Deletes the construction axis |

## Construction Axes

The `ConstructionAxes` collection on a component provides access to all user-created construction axes and the ability to create new ones.

```python
constructionAxes = rootComp.constructionAxes
```

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput()` | ConstructionAxisInput | Creates an input object to define a new axis |
| `add(input)` | ConstructionAxis | Creates the construction axis from the input |
| `item(index)` | ConstructionAxis | Gets axis by index |
| `itemByName(name)` | ConstructionAxis | Gets axis by name |
| `count` | Integer | Number of user-created construction axes |

### ConstructionAxisInput Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `setByLine(edge)` | `edge`: BRepEdge or SketchLine | Along a linear edge or sketch line |
| `setByCircularFace(face)` | `face`: cylindrical, conical, or toroidal BRepFace | Through the center of a circular/cylindrical face |
| `setByTwoPlanes(planeOne, planeTwo)` | `planeOne`, `planeTwo`: ConstructionPlane or BRepFace | Along the intersection line of two planes |
| `setByTwoPoints(pointOne, pointTwo)` | Two ConstructionPoint, BRepVertex, or SketchPoint objects | Through two points |
| `setByNormalToFaceAtPoint(face, point)` | `face`: BRepFace; `point`: ConstructionPoint, BRepVertex, or SketchPoint | Normal to a face at a point |
| `setByPerpendicularAtPoint(entity, point)` | `entity`: BRepEdge or SketchCurve; `point`: ConstructionPoint, BRepVertex, or SketchPoint | Perpendicular to an entity at a point |

### Example: Construction Axes

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

axes = rootComp.constructionAxes

# --- Axis through two points ---
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
pt1 = sketch.sketchPoints.add(adsk.core.Point3D.create(0, 0, 0))
pt2 = sketch.sketchPoints.add(adsk.core.Point3D.create(5, 5, 5))

axisInput = axes.createInput()
axisInput.setByTwoPoints(pt1, pt2)
twoPointAxis = axes.add(axisInput)
twoPointAxis.name = 'Diagonal Axis'

# --- Axis along intersection of two planes ---
axisInput2 = axes.createInput()
axisInput2.setByTwoPlanes(rootComp.xYConstructionPlane, rootComp.xZConstructionPlane)
intersectionAxis = axes.add(axisInput2)
intersectionAxis.name = 'XY-XZ Intersection'

# --- Axis through center of cylindrical face ---
# Assumes a cylindrical body already exists
body = rootComp.bRepBodies.item(0)
for face in body.faces:
    if face.geometry.objectType == adsk.core.Cylinder.classType():
        axisInput3 = axes.createInput()
        axisInput3.setByCircularFace(face)
        cylAxis = axes.add(axisInput3)
        cylAxis.name = 'Cylinder Center Axis'
        break

# --- Axis along a linear edge ---
for edge in body.edges:
    if edge.geometry.objectType == adsk.core.Line3D.classType():
        axisInput4 = axes.createInput()
        axisInput4.setByLine(edge)
        edgeAxis = axes.add(axisInput4)
        edgeAxis.name = 'Edge Axis'
        break
```

## ConstructionPoint Object

Represents a single construction point in the design.

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Name displayed in the browser |
| `geometry` | Point3D | R | The 3D location of the construction point |
| `isVisible` | Boolean | R/W | Whether visible in the canvas |
| `isLightBulbOn` | Boolean | R/W | Light bulb state in the browser |
| `parent` | Component | R | Parent component |
| `healthState` | FeatureHealthStates | R | Health state of the feature |
| `errorOrWarningMessage` | String | R | Error or warning message if unhealthy |
| `timelineObject` | TimelineObject | R | Associated timeline object |
| `definition` | ConstructionPointDefinition | R | Definition describing how it was created |

| Method | Description |
|--------|-------------|
| `deleteMe()` | Deletes the construction point |

## Construction Points

The `ConstructionPoints` collection on a component provides access to all user-created construction points and the ability to create new ones.

```python
constructionPoints = rootComp.constructionPoints
```

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput()` | ConstructionPointInput | Creates an input object to define a new point |
| `add(input)` | ConstructionPoint | Creates the construction point from the input |
| `item(index)` | ConstructionPoint | Gets point by index |
| `itemByName(name)` | ConstructionPoint | Gets point by name |
| `count` | Integer | Number of user-created construction points |

### ConstructionPointInput Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `setByPoint(point)` | `point`: SketchPoint, BRepVertex, or ConstructionPoint | At an existing point or vertex |
| `setByCenter(circularEntity)` | `circularEntity`: circular BRepEdge, BRepFace, or SketchCircle | At the center of a circular entity |
| `setByEdgePlane(edge, plane)` | `edge`: BRepEdge; `plane`: ConstructionPlane or BRepFace | At the intersection of an edge and a plane |
| `setByThreePlanes(planeOne, planeTwo, planeThree)` | Three ConstructionPlane or BRepFace objects | At the intersection of three planes |
| `setByTwoEdges(edgeOne, edgeTwo)` | `edgeOne`, `edgeTwo`: BRepEdge or SketchLine | At the intersection of two edges |

### Example: Construction Points

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

points = rootComp.constructionPoints

# --- Point at a sketch point ---
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
skPt = sketch.sketchPoints.add(adsk.core.Point3D.create(3, 4, 0))

ptInput = points.createInput()
ptInput.setByPoint(skPt)
constPoint = points.add(ptInput)
constPoint.name = 'Sketch Reference Point'

# --- Point at intersection of three planes ---
# Use the three origin planes: their intersection is the origin
ptInput2 = points.createInput()
ptInput2.setByThreePlanes(
    rootComp.xYConstructionPlane,
    rootComp.xZConstructionPlane,
    rootComp.yZConstructionPlane
)
originPoint = points.add(ptInput2)
originPoint.name = 'Three-Plane Intersection'

# --- Point at center of a circular edge ---
# Assumes a body with a circular edge exists
body = rootComp.bRepBodies.item(0)
for edge in body.edges:
    geom = edge.geometry
    if geom.objectType == adsk.core.Circle3D.classType() or \
       geom.objectType == adsk.core.Arc3D.classType():
        ptInput3 = points.createInput()
        ptInput3.setByCenter(edge)
        centerPoint = points.add(ptInput3)
        centerPoint.name = 'Circle Center'
        break

# --- Point at intersection of edge and plane ---
for edge in body.edges:
    ptInput4 = points.createInput()
    ptInput4.setByEdgePlane(edge, rootComp.xYConstructionPlane)
    edgePlanePoint = points.add(ptInput4)
    edgePlanePoint.name = 'Edge-Plane Intersection'
    break
```

## Practical Patterns

### Using Construction Geometry as Sketch References

```python
# Create an offset plane, then sketch on it
planes = rootComp.constructionPlanes
planeInput = planes.createInput()
planeInput.setByOffset(
    rootComp.xYConstructionPlane,
    adsk.core.ValueInput.createByString('25 mm')
)
offsetPlane = planes.add(planeInput)

# Sketch on the offset plane
sketch = rootComp.sketches.add(offsetPlane)
sketch.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 2.0
)
```

### Iterating Over All Construction Geometry

```python
# List all construction planes (user-created)
for i in range(rootComp.constructionPlanes.count):
    plane = rootComp.constructionPlanes.item(i)
    print(f'Plane: {plane.name}, Visible: {plane.isVisible}')

# List all construction axes (user-created)
for i in range(rootComp.constructionAxes.count):
    axis = rootComp.constructionAxes.item(i)
    print(f'Axis: {axis.name}, Visible: {axis.isVisible}')

# List all construction points (user-created)
for i in range(rootComp.constructionPoints.count):
    point = rootComp.constructionPoints.item(i)
    geom = point.geometry
    print(f'Point: {point.name} at ({geom.x}, {geom.y}, {geom.z})')
```

### Construction Plane from Face Offset

```python
# Create a construction plane offset from a body face
body = rootComp.bRepBodies.item(0)
topFace = None
for face in body.faces:
    if face.geometry.objectType == adsk.core.Plane.classType():
        normal = face.geometry.normal
        if abs(normal.z - 1.0) < 0.001:  # top-facing face
            topFace = face
            break

if topFace:
    planes = rootComp.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(topFace, adsk.core.ValueInput.createByString('10 mm'))
    abovePlane = planes.add(planeInput)
    abovePlane.name = 'Above Top Face'
```

### Visibility Control

```python
# Hide all user-created construction planes
for i in range(rootComp.constructionPlanes.count):
    rootComp.constructionPlanes.item(i).isVisible = False

# Hide origin construction geometry
rootComp.xYConstructionPlane.isVisible = False
rootComp.xZConstructionPlane.isVisible = False
rootComp.yZConstructionPlane.isVisible = False
rootComp.xConstructionAxis.isVisible = False
rootComp.yConstructionAxis.isVisible = False
rootComp.zConstructionAxis.isVisible = False
rootComp.originConstructionPoint.isVisible = False
```

## Key Notes

- Construction geometry is **parametric** — if the input references change, the construction geometry updates automatically.
- Built-in origin geometry (planes, axes, origin point) cannot be deleted. Only user-created construction geometry supports `deleteMe()`.
- The `ConstructionPlanes`, `ConstructionAxes`, and `ConstructionPoints` collections only contain **user-created** items. Built-in origin geometry is accessed through dedicated properties on the Component.
- All distance values use **internal units (cm)**. Use `ValueInput.createByString('25 mm')` for explicit unit specification or `ValueInput.createByReal(2.5)` for cm.
- Angle values for `setByAngle` use `ValueInput` — specify with `ValueInput.createByString('45 deg')` or `ValueInput.createByReal(math.pi / 4)` (radians).
- Construction planes, axes, and points all appear in the **timeline** and can be rolled back, suppressed, or reordered like other features.
