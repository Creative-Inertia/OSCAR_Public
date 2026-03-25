# Fusion 360 API - Fillet and Chamfer Feature API Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/FilletFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ChamferFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/FilletFeatures_createInput.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ChamferFeatures_createInput2.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Fillet features round edges by replacing them with curved surfaces. Chamfer features bevel edges by replacing them with angled flat surfaces. Both operate on BRepEdge objects selected from existing solid or surface bodies.

---

## Fillet Features

### Accessing the FilletFeatures Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

fillets = rootComp.features.filletFeatures
```

### FilletFeatures Collection - Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput()` | FilletFeatureInput | Creates a new input object to define the fillet parameters |
| `add(input)` | FilletFeature | Creates a fillet feature from the given input |
| `item(index)` | FilletFeature | Returns the fillet feature at the given index |
| `itemByName(name)` | FilletFeature | Returns the fillet feature with the given name |
| `count` | int | Number of fillet features in the collection |

### FilletFeatureInput - Properties and Methods

The `FilletFeatureInput` object is created by `filletFeatures.createInput()` and configured before passing to `add()`.

| Property / Method | Type | Description |
|-------------------|------|-------------|
| `addConstantRadiusEdgeSet(edges, radius, isTangentChain)` | ConstantRadiusFilletEdgeSet | Adds a set of edges to be filleted with a constant radius |
| `addVariableRadiusEdgeSet(edges, startRadius, isTangentChain)` | VariableRadiusFilletEdgeSet | Adds a set of edges with a variable radius along the edge |
| `addChordLengthEdgeSet(edges, chordLength, isTangentChain)` | ChordLengthFilletEdgeSet | Adds a set of edges filleted by chord length |
| `edgeSets` | ObjectCollection | Collection of all edge sets added to this input |
| `isRollingBallCorner` | Boolean | True = rolling ball corner type; False = setback corner type |
| `isG2` | Boolean | True for curvature-continuous (G2) fillets; False for tangent-continuous (G1) |
| `isTangentChain` | Boolean | Default tangent chain setting for edge sets |

### FilletEdgeSet Types

#### ConstantRadiusFilletEdgeSet

Applies the same radius along the entire length of each selected edge.

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `edges` | BRepEdges | R | The edges in this set |
| `radius` | ValueInput | R/W | The fillet radius |
| `isTangentChain` | Boolean | R/W | Whether tangent-connected edges are automatically included |

#### VariableRadiusFilletEdgeSet

Allows the fillet radius to change along the edge length. Positions are defined as proportional values (0.0 to 1.0) along the edge.

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `edges` | BRepEdges | R | The edges in this set |
| `startRadius` | ValueInput | R/W | Radius at the start of the edge |
| `endRadius` | ValueInput | R/W | Radius at the end of the edge |
| `isTangentChain` | Boolean | R/W | Whether tangent-connected edges are automatically included |
| `addRadiusAtPosition(position, radius)` | — | — | Adds a radius value at a proportional position along the edge |

#### ChordLengthFilletEdgeSet

Specifies the fillet by chord length rather than radius. The chord length is the straight-line distance across the fillet surface.

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `edges` | BRepEdges | R | The edges in this set |
| `chordLength` | ValueInput | R/W | The chord length value |
| `isTangentChain` | Boolean | R/W | Whether tangent-connected edges are automatically included |

### Quick Start: Constant Radius Fillet

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Assume a body already exists — get its edges
body = rootComp.bRepBodies.item(0)
edges = adsk.core.ObjectCollection.create()
edges.add(body.edges.item(0))
edges.add(body.edges.item(1))

# Create fillet input
fillets = rootComp.features.filletFeatures
filletInput = fillets.createInput()

# Add constant radius edge set: 3mm radius, tangent chain enabled
radius = adsk.core.ValueInput.createByString("3 mm")
filletInput.addConstantRadiusEdgeSet(edges, radius, True)

# Optionally set corner type
filletInput.isRollingBallCorner = True

# Create the fillet feature
filletFeature = fillets.add(filletInput)
```

### Variable Radius Fillet Example

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

body = rootComp.bRepBodies.item(0)
edges = adsk.core.ObjectCollection.create()
edges.add(body.edges.item(0))

fillets = rootComp.features.filletFeatures
filletInput = fillets.createInput()

# Add variable radius edge set
startRadius = adsk.core.ValueInput.createByString("2 mm")
edgeSet = filletInput.addVariableRadiusEdgeSet(edges, startRadius, True)

# Set the end radius
edgeSet.endRadius = adsk.core.ValueInput.createByString("5 mm")

# Optionally add intermediate radius at midpoint (position 0.5)
midRadius = adsk.core.ValueInput.createByString("3.5 mm")
edgeSet.addRadiusAtPosition(0.5, midRadius)

filletFeature = fillets.add(filletInput)
```

### Chord Length Fillet Example

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

body = rootComp.bRepBodies.item(0)
edges = adsk.core.ObjectCollection.create()
edges.add(body.edges.item(2))

fillets = rootComp.features.filletFeatures
filletInput = fillets.createInput()

# Add chord length edge set
chordLength = adsk.core.ValueInput.createByString("4 mm")
filletInput.addChordLengthEdgeSet(edges, chordLength, True)

filletFeature = fillets.add(filletInput)
```

---

## Chamfer Features

### Accessing the ChamferFeatures Collection

```python
chamfers = rootComp.features.chamferFeatures
```

### ChamferFeatures Collection - Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `createInput2(edges, chamferType)` | ChamferFeatureInput | Creates a new input object for the chamfer (preferred over deprecated `createInput`) |
| `add(input)` | ChamferFeature | Creates a chamfer feature from the given input |
| `item(index)` | ChamferFeature | Returns the chamfer feature at the given index |
| `itemByName(name)` | ChamferFeature | Returns the chamfer feature with the given name |
| `count` | int | Number of chamfer features in the collection |

> **Note:** `createInput()` is deprecated. Always use `createInput2()` which accepts a `ChamferTypeDefinition` object for clearer type specification.

### ChamferTypeDefinition Types

#### EqualDistanceChamferTypeDefinition

Both sides of the chamfer have the same distance from the edge.

```python
chamferType = adsk.fusion.EqualDistanceChamferTypeDefinition.create(
    adsk.core.ValueInput.createByString("2 mm")
)
```

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `distance` | ValueInput | R/W | The equal distance on both sides of the edge |

#### TwoDistancesChamferTypeDefinition

Each side of the chamfer has a different distance.

```python
chamferType = adsk.fusion.TwoDistancesChamferTypeDefinition.create(
    adsk.core.ValueInput.createByString("2 mm"),
    adsk.core.ValueInput.createByString("4 mm")
)
```

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `distanceOne` | ValueInput | R/W | Distance on the first face |
| `distanceTwo` | ValueInput | R/W | Distance on the second face |

#### DistanceAndAngleChamferTypeDefinition

Defines the chamfer by one distance and an angle.

```python
chamferType = adsk.fusion.DistanceAndAngleChamferTypeDefinition.create(
    adsk.core.ValueInput.createByString("3 mm"),
    adsk.core.ValueInput.createByString("45 deg")
)
```

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `distance` | ValueInput | R/W | Distance from the edge |
| `angle` | ValueInput | R/W | Angle of the chamfer |

### Quick Start: Equal Distance Chamfer

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

body = rootComp.bRepBodies.item(0)
edges = adsk.core.ObjectCollection.create()
edges.add(body.edges.item(0))

chamfers = rootComp.features.chamferFeatures

# Create equal distance chamfer type definition
chamferType = adsk.fusion.EqualDistanceChamferTypeDefinition.create(
    adsk.core.ValueInput.createByString("2 mm")
)

# Create chamfer input using createInput2
chamferInput = chamfers.createInput2(edges, chamferType)

# Create the chamfer feature
chamferFeature = chamfers.add(chamferInput)
```

### Two Distances Chamfer Example

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

body = rootComp.bRepBodies.item(0)
edges = adsk.core.ObjectCollection.create()
edges.add(body.edges.item(3))
edges.add(body.edges.item(4))

chamfers = rootComp.features.chamferFeatures

# Two different distances
chamferType = adsk.fusion.TwoDistancesChamferTypeDefinition.create(
    adsk.core.ValueInput.createByString("1 mm"),
    adsk.core.ValueInput.createByString("3 mm")
)

chamferInput = chamfers.createInput2(edges, chamferType)
chamferFeature = chamfers.add(chamferInput)
```

### Distance and Angle Chamfer Example

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

body = rootComp.bRepBodies.item(0)
edges = adsk.core.ObjectCollection.create()
edges.add(body.edges.item(5))

chamfers = rootComp.features.chamferFeatures

# Distance + angle
chamferType = adsk.fusion.DistanceAndAngleChamferTypeDefinition.create(
    adsk.core.ValueInput.createByString("2 mm"),
    adsk.core.ValueInput.createByString("60 deg")
)

chamferInput = chamfers.createInput2(edges, chamferType)
chamferFeature = chamfers.add(chamferInput)
```

---

## FilletFeature Object - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Feature name in the browser/timeline |
| `bodies` | BRepBodies | R | Bodies modified or created by the feature |
| `faces` | BRepFaces | R | All faces created by the fillet |
| `edges` | BRepEdges | R | All edges created by the fillet |
| `edgeSets` | ObjectCollection | R | Collection of FilletEdgeSet objects defining the fillet |
| `isRollingBallCorner` | Boolean | R/W | Corner type: rolling ball (True) or setback (False) |
| `isSuppressed` | Boolean | R/W | Whether the feature is suppressed |
| `isValid` | Boolean | R | Whether the feature is still valid |
| `healthState` | FeatureHealthStates | R | Current health state of the feature |
| `errorOrWarningMessage` | String | R | Error or warning message if unhealthy |
| `timelineObject` | TimelineObject | R | The feature's timeline entry |
| `parentComponent` | Component | R | The component containing the feature |
| `isParametric` | Boolean | R | Whether the feature belongs to a parametric design |

## FilletFeature Object - Methods

| Method | Description |
|--------|-------------|
| `deleteMe()` | Delete the fillet feature |
| `dissolve()` | Remove the feature from the timeline, keeping only the resulting geometry |

## ChamferFeature Object - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Feature name in the browser/timeline |
| `bodies` | BRepBodies | R | Bodies modified or created by the feature |
| `faces` | BRepFaces | R | All faces created by the chamfer |
| `edges` | BRepEdges | R | All edges created by the chamfer |
| `chamferType` | ChamferTypeDefinition | R | The type definition used to create the chamfer |
| `isSuppressed` | Boolean | R/W | Whether the feature is suppressed |
| `isValid` | Boolean | R | Whether the feature is still valid |
| `healthState` | FeatureHealthStates | R | Current health state of the feature |
| `errorOrWarningMessage` | String | R | Error or warning message if unhealthy |
| `timelineObject` | TimelineObject | R | The feature's timeline entry |
| `parentComponent` | Component | R | The component containing the feature |
| `isParametric` | Boolean | R | Whether the feature belongs to a parametric design |

## ChamferFeature Object - Methods

| Method | Description |
|--------|-------------|
| `deleteMe()` | Delete the chamfer feature |
| `dissolve()` | Remove the feature from the timeline, keeping only the resulting geometry |

---

## Editing Existing Fillets

### Change Fillet Radius

```python
# Get an existing fillet feature
filletFeature = rootComp.features.filletFeatures.item(0)

# Access the first edge set (constant radius)
edgeSet = adsk.fusion.ConstantRadiusFilletEdgeSet.cast(filletFeature.edgeSets.item(0))

# Modify the radius via its parameter
radiusParam = edgeSet.radius
radiusParam.expression = "5 mm"
```

### Change Corner Type

```python
filletFeature = rootComp.features.filletFeatures.item(0)
filletFeature.isRollingBallCorner = False  # Switch to setback corner
```

### Suppress/Unsuppress a Fillet

```python
filletFeature = rootComp.features.filletFeatures.itemByName("Fillet1")
filletFeature.isSuppressed = True   # Suppress
filletFeature.isSuppressed = False  # Unsuppress
```

## Editing Existing Chamfers

### Change Chamfer Distance

```python
# Get an existing chamfer feature
chamferFeature = rootComp.features.chamferFeatures.item(0)

# Access the chamfer type definition
typeDef = chamferFeature.chamferType

# Cast to the specific type and modify
equalDist = adsk.fusion.EqualDistanceChamferTypeDefinition.cast(typeDef)
if equalDist:
    equalDist.distance.expression = "3 mm"
```

### Suppress/Unsuppress a Chamfer

```python
chamferFeature = rootComp.features.chamferFeatures.itemByName("Chamfer1")
chamferFeature.isSuppressed = True   # Suppress
chamferFeature.isSuppressed = False  # Unsuppress
```

---

## Feature Health Check

Works identically for both fillet and chamfer features:

```python
feature = rootComp.features.filletFeatures.item(0)  # or chamferFeatures

health = feature.healthState
if health == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
    pass  # Feature is healthy
elif health == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
    msg = feature.errorOrWarningMessage
elif health == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
    msg = feature.errorOrWarningMessage
```

## Edge Selection Patterns

### Select All Edges of a Body

```python
edges = adsk.core.ObjectCollection.create()
body = rootComp.bRepBodies.item(0)
for i in range(body.edges.count):
    edges.add(body.edges.item(i))
```

### Select Edges of a Specific Face

```python
edges = adsk.core.ObjectCollection.create()
face = body.faces.item(0)
for i in range(face.edges.count):
    edges.add(face.edges.item(i))
```

### Select Edges by Length (Filter Pattern)

```python
edges = adsk.core.ObjectCollection.create()
body = rootComp.bRepBodies.item(0)
for i in range(body.edges.count):
    edge = body.edges.item(i)
    evaluator = edge.evaluator
    (retVal, startPt, endPt) = evaluator.getEndPoints()
    if retVal:
        length = startPt.distanceTo(endPt)
        if length < 1.0:  # edges shorter than 1 cm
            edges.add(edge)
```

## Complete Example: Fillet and Chamfer on a Box

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # Create a sketch and extrude a box
        sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(5, 5, 0)
        )
        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(3.0)
        extrudeFeature = extrudes.addSimple(
            prof, distance,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        body = extrudeFeature.bodies.item(0)

        # --- Apply fillet to top edges ---
        topFace = extrudeFeature.endFaces.item(0)
        filletEdges = adsk.core.ObjectCollection.create()
        for i in range(topFace.edges.count):
            filletEdges.add(topFace.edges.item(i))

        fillets = rootComp.features.filletFeatures
        filletInput = fillets.createInput()
        filletInput.addConstantRadiusEdgeSet(
            filletEdges,
            adsk.core.ValueInput.createByString("2 mm"),
            True
        )
        filletInput.isRollingBallCorner = True
        filletFeature = fillets.add(filletInput)

        # --- Apply chamfer to bottom edges ---
        bottomFace = extrudeFeature.startFaces.item(0)
        chamferEdges = adsk.core.ObjectCollection.create()
        for i in range(bottomFace.edges.count):
            chamferEdges.add(bottomFace.edges.item(i))

        chamfers = rootComp.features.chamferFeatures
        chamferType = adsk.fusion.EqualDistanceChamferTypeDefinition.create(
            adsk.core.ValueInput.createByString("1 mm")
        )
        chamferInput = chamfers.createInput2(chamferEdges, chamferType)
        chamferFeature = chamfers.add(chamferInput)

        app.activeViewport.refresh()

    except:
        app.userInterface.messageBox(traceback.format_exc())
```
