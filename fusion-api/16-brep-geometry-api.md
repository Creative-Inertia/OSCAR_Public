# Fusion 360 API - B-Rep Geometry and Solids API

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BRepGeometry_UM.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Fusion uses Boundary-Representation (B-Rep) modeling to represent solids as groups of surfaces forming tightly closed volumes. The B-Rep model provides a complete geometric description of solid and surface models.

## B-Rep Topology Hierarchy

```
BRepBody
  └── BRepLump (one per body in Fusion)
       └── BRepShell (one or more: outer + inner voids)
            └── BRepFace (individual surfaces)
                 └── BRepLoop (one outer + zero or more inner)
                      └── BRepCoEdge (oriented curve segments)
                           └── BRepEdge (shared between faces)
                                └── BRepVertex (edge endpoints)
```

## BRepBody

The top-level container for solid geometry. Accessed from Component:

```python
rootComp = design.rootComponent
bodies = rootComp.bRepBodies

for body in bodies:
    print(f'{body.name}: {body.faces.count} faces, {body.edges.count} edges')
```

| Property | Type | Description |
|----------|------|-------------|
| `name` | String (R/W) | Body name |
| `faces` | BRepFaces | All faces |
| `edges` | BRepEdges | All edges |
| `vertices` | BRepVertices | All vertices |
| `shells` | BRepShells | All shells |
| `lumps` | BRepLumps | All lumps |
| `isSolid` | Boolean | Whether watertight solid |
| `volume` | Double | Volume in cm^3 |
| `area` | Double | Surface area in cm^2 |
| `boundingBox` | BoundingBox3D | Bounding box |
| `material` | Material | Physical material |
| `appearance` | Appearance | Visual appearance |
| `meshManager` | MeshManager | For triangular mesh access |
| `physicalProperties` | PhysicalProperties | Mass, volume, area, etc. |

## BRepFace

Individual surfaces within a body.

```python
for face in body.faces:
    geom = face.geometry
    if geom.objectType == adsk.core.Plane.classType():
        print(f'Planar face: normal = {face.evaluator.getNormalAtParameter(...)}')
    elif geom.objectType == adsk.core.Cylinder.classType():
        print(f'Cylindrical face: radius = {geom.radius}')
```

| Property | Type | Description |
|----------|------|-------------|
| `geometry` | Surface | Underlying geometry (Plane, Cylinder, Cone, Sphere, Torus, NurbsSurface) |
| `evaluator` | SurfaceEvaluator | Evaluation methods |
| `loops` | BRepLoops | Face boundary loops |
| `edges` | BRepEdges | All edges of face |
| `vertices` | BRepVertices | All vertices |
| `area` | Double | Face area in cm^2 |
| `centroid` | Point3D | Face centroid |
| `isParamReversed` | Boolean | Parameter direction reversed |
| `appearance` | Appearance | Per-face appearance override |
| `body` | BRepBody | Parent body |
| `shell` | BRepShell | Parent shell |
| `boundingBox` | BoundingBox3D | Face bounds |

### Geometry Types for Faces

| Type | Properties |
|------|-----------|
| `adsk.core.Plane` | `normal`, `origin` (rootPoint) |
| `adsk.core.Cylinder` | `axis`, `origin`, `radius` |
| `adsk.core.Cone` | `axis`, `origin`, `halfAngle` |
| `adsk.core.Sphere` | `center`, `radius` |
| `adsk.core.Torus` | `axis`, `origin`, `majorRadius`, `minorRadius` |
| `adsk.core.NurbsSurface` | Complex freeform surface |

## BRepEdge

Curves connecting faces.

```python
for edge in body.edges:
    geom = edge.geometry
    length = edge.length  # cm
    startVertex = edge.startVertex
    endVertex = edge.endVertex
    faces = edge.faces  # Two faces sharing this edge (or one for open edges)
```

| Property | Type | Description |
|----------|------|-------------|
| `geometry` | Curve3D | Line3D, Circle3D, Arc3D, Ellipse3D, NurbsCurve3D |
| `evaluator` | CurveEvaluator3D | Evaluation methods |
| `length` | Double | Length in cm |
| `startVertex` | BRepVertex | Start vertex |
| `endVertex` | BRepVertex | End vertex |
| `faces` | BRepFaces | Adjacent faces |
| `isDegenerate` | Boolean | Zero-length edge |
| `boundingBox` | BoundingBox3D | Edge bounds |

## BRepVertex

Points at edge endpoints.

```python
for vertex in body.vertices:
    point = vertex.geometry  # Point3D
    edges = vertex.edges     # Connected edges
    faces = vertex.faces     # Connected faces
```

## BRepShell

Connected set of faces. Use `isVoid` to detect internal cavities.

```python
for shell in body.shells:
    if shell.isVoid:
        print('Internal cavity')
    else:
        print(f'Outer shell: {shell.faces.count} faces')
```

## Surface Evaluator

Evaluate geometric properties of faces.

```python
face = body.faces.item(0)
surfEval = face.evaluator

# Get parametric range
paramRange = surfEval.parametricRange()
minU, maxU = paramRange.minPoint.x, paramRange.maxPoint.x
minV, maxV = paramRange.minPoint.y, paramRange.maxPoint.y

# Get center point
midU = (minU + maxU) / 2
midV = (minV + maxV) / 2
paramPoint = adsk.core.Point2D.create(midU, midV)

# Get normal at parametric center
(retVal, normal) = surfEval.getNormalAtParameter(paramPoint)

# Get 3D point at parametric location
(retVal, modelPoint) = surfEval.getPointAtParameter(paramPoint)

# Get parametric location from 3D point
(retVal, paramPt) = surfEval.getParameterAtPoint(modelPoint)

# Check if parameter is on face (accounting for trim boundaries)
(retVal, isOnFace) = surfEval.isParameterOnFace(paramPoint)
```

### SurfaceEvaluator Methods

| Method | Description |
|--------|-------------|
| `getNormalAtParameter(Point2D)` | Normal vector at parametric point |
| `getNormalAtPoint(Point3D)` | Normal at model space point |
| `getParameterAtPoint(Point3D)` | Convert 3D to parametric |
| `getPointAtParameter(Point2D)` | Convert parametric to 3D |
| `isParameterOnFace(Point2D)` | Check if point is on trimmed face |
| `parametricRange()` | Min/max parametric range |
| `getFirstDerivative(Point2D)` | Tangent vectors at parameter |
| `getCurvature(Point2D)` | Curvature at parameter |

## Curve Evaluator

Evaluate properties along edges.

```python
edge = body.edges.item(0)
curveEval = edge.evaluator

# Get endpoints
(retVal, startPt, endPt) = curveEval.getEndPoints()

# Get point at parameter
(retVal, point) = curveEval.getPointAtParameter(0.5)

# Get parameter from point
(retVal, param) = curveEval.getParameterAtPoint(point)

# Get length between parameters
(retVal, length) = curveEval.getLengthAtParameter(startParam, endParam)

# Approximate curve as polyline (for visualization)
(retVal, points) = curveEval.getStrokes(startParam, endParam, tolerance)
```

## Finding Specific Geometry

### Find Planar Faces

```python
planarFaces = []
for face in body.faces:
    if face.geometry.objectType == adsk.core.Plane.classType():
        planarFaces.append(face)
```

### Find Faces by Normal Direction

```python
upFaces = []
upDir = adsk.core.Vector3D.create(0, 0, 1)
for face in body.faces:
    if face.geometry.objectType == adsk.core.Plane.classType():
        normal = face.geometry.normal
        if normal.isParallelTo(upDir) and normal.z > 0:
            upFaces.append(face)
```

### Find B-Rep at Point

```python
entities = rootComp.findBRepUsingPoint(
    adsk.core.Point3D.create(5, 5, 5),
    adsk.fusion.BRepEntityTypes.BRepFaceEntityType,
    0.1  # proximity tolerance in cm
)
```

### Find B-Rep Using Ray

```python
entities = rootComp.findBRepUsingRay(
    adsk.core.Point3D.create(0, 0, 10),    # origin
    adsk.core.Vector3D.create(0, 0, -1),    # direction
    adsk.fusion.BRepEntityTypes.BRepFaceEntityType
)
```

## Mesh Representation

For visualization or STL-like access:

```python
meshManager = body.meshManager

# Get display mesh (current quality)
displayMesh = meshManager.displayMeshes.item(0)

# Create custom mesh
meshCalc = meshManager.createMeshCalculator()
meshCalc.setQuality(
    adsk.fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh
)
mesh = meshCalc.calculate()

# Access triangles
nodeCoords = mesh.nodeCoordinatesAsFloat  # Flat array [x1,y1,z1, x2,y2,z2, ...]
nodeIndices = mesh.nodeIndices            # Triangle indices [i1,i2,i3, i4,i5,i6, ...]
normals = mesh.normalVectorsAsFloat       # Per-node normals
triangleCount = mesh.triangleCount
nodeCount = mesh.nodeCount
```

## Example: Get Face Normal at Center

```python
def getNormalAtParametricCenter(face):
    surfEval = face.evaluator
    range = surfEval.parametricRange()

    midU = (range.minPoint.x + range.maxPoint.x) / 2
    midV = (range.minPoint.y + range.maxPoint.y) / 2
    paramPoint = adsk.core.Point2D.create(midU, midV)

    (retVal, normal) = surfEval.getNormalAtParameter(paramPoint)
    (retVal, position) = surfEval.getPointAtParameter(paramPoint)

    return (normal, position)
```
