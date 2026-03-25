# Fusion 360 API - Basic Concepts

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BasicConcepts_UM.htm

## Objects

The Fusion API employs an object-oriented design where each component maps to familiar user-interface elements. For instance, an extrusion in a Fusion model is represented in the API by the `ExtrudeFeature` object. Through these objects, developers can replicate UI capabilities like creating features, renaming timeline items, suppressing elements, and deleting them.

Beyond standard UI-mapped objects, the API offers specialized capabilities. These enable developers to query models for geometric extraction and create custom commands integrated into the Fusion interface.

## Object Model (Hierarchy)

The critical distinction between UI and API usage involves object access patterns. Where the interface relies on graphical selection, the API employs a hierarchical "Object Model" structure.

The hierarchy flows as follows:

```
Application (top-level, representing all Fusion functionality)
  └── Documents (contain modeling or CAM data)
       └── Design (represents modeling data)
            └── Root Component (top-level component within Design)
                 ├── Sketches
                 ├── Features (ExtrudeFeatures, RevolveFeatures, etc.)
                 ├── Construction Geometry (Planes, Axes, Points)
                 ├── BRepBodies (solid/surface bodies)
                 ├── Occurrences (instances of other components)
                 │    └── Component (referenced component)
                 │         ├── Sketches
                 │         ├── Features
                 │         └── ...
                 └── Parameters (ModelParameters, UserParameters)
```

From the root component, developers access sketches, features, construction geometry, and nested components. This parent-child structure typically mirrors the browser's organizational layout.

### Traversal Pattern (Python)

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
ui = app.userInterface

# Get the active document and design
doc = app.activeDocument
design = adsk.fusion.Design.cast(app.activeProduct)

# Get the root component
rootComp = design.rootComponent

# Access sketches
sketches = rootComp.sketches

# Access features
features = rootComp.features
extrudeFeatures = features.extrudeFeatures

# Access bodies
bodies = rootComp.bRepBodies

# Access construction planes
xyPlane = rootComp.xYConstructionPlane
xzPlane = rootComp.xZConstructionPlane
yzPlane = rootComp.yZConstructionPlane

# Access occurrences (sub-components)
occurrences = rootComp.occurrences
for occ in occurrences:
    childComp = occ.component
    childBodies = childComp.bRepBodies
```

## Common Object Functionality

All objects support:

| Property/Method | Description |
|----------------|-------------|
| `objectType` | Identifies object type via string (e.g., `"adsk::fusion::ExtrudeFeature"`) |
| `classType()` | Static function returning class name string for type comparison |
| `isValid` | Returns Boolean confirming object validity (objects become invalid when deleted or document closed) |

## Static Functions (Transient Objects)

"Transient" objects lack owners and use static functions for instantiation. These are objects that exist independently of the document (points, vectors, matrices, etc.).

```python
# Create a transient Point3D
point = adsk.core.Point3D.create(0, 0, 0)

# Create a transient Vector3D
vector = adsk.core.Vector3D.create(1, 0, 0)

# Create a transient Matrix3D (identity)
matrix = adsk.core.Matrix3D.create()

# Create an ObjectCollection
objColl = adsk.core.ObjectCollection.create()
```

## Collections

Collections aggregate related objects and support:

| Member | Description |
|--------|-------------|
| `count` property | Quantity of items in the collection |
| `item(index)` method | Retrieves object at specified index (zero-based) |
| `itemByName(name)` method | Retrieves object by its name |
| `itemById(id)` method | Retrieves object by unique identifier |
| `add()` methods | Creates new objects within the collection |

### Example: Creating Sketch Elements via Collections

```python
# Get sketch curves collections
circles = sketch.sketchCurves.sketchCircles
circle1 = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2)

lines = sketch.sketchCurves.sketchLines
axis = lines.addByTwoPoints(
    adsk.core.Point3D.create(-1, -4, 0),
    adsk.core.Point3D.create(1, -4, 0)
)
```

### Python Collection Iteration

Collections support standard Python iteration:

```python
# Iterate over collection items
for item in collection:
    print(item.name)

# Get count
length = len(collection)

# Index access
first = collection[0]
last = collection[-1]
slice = collection[:2]
```

## Lists (Read-Only Collections)

Lists represent read-only collections supporting `count` and `item` methods but lacking add capabilities. They typically return multiple objects from single operations.

Example: Creating rectangles generates four lines returned as `SketchLineList`.

```python
recLines = lines.addTwoPointRectangle(
    adsk.core.Point3D.create(4, 0, 0),
    adsk.core.Point3D.create(7, 2, 0)
)
# recLines is a SketchLineList with 4 items
line0 = recLines.item(0)  # bottom
line1 = recLines.item(1)  # right
line2 = recLines.item(2)  # top
line3 = recLines.item(3)  # left
```

## Input Objects

Input objects function as API equivalents of command dialogs, collecting parameters needed for complex feature creation. The pattern is:

1. Call `createInput()` on the collection to get an Input object
2. Configure the Input via methods and properties
3. Call `add()` on the collection, passing the Input, to create the feature

### Example: Creating a Revolve Feature

```python
prof = sketch.profiles.item(0)
revolves = rootComp.features.revolveFeatures

# Step 1: Create input
revInput = revolves.createInput(
    prof,
    axis,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# Step 2: Configure input
angle = adsk.core.ValueInput.createByReal(math.pi * 2)
revInput.setAngleExtent(False, angle)

# Step 3: Add (execute)
rev = revolves.add(revInput)
```

## ValueInput Objects

ValueInput objects define parametric values for features. They accept:

| Creation Method | Input Type | Behavior |
|----------------|-----------|----------|
| `createByReal(value)` | Float | Always interpreted as Fusion internal units: **centimeters** for length, **radians** for angles |
| `createByString("5")` | String (no units) | Interpreted per document default units |
| `createByString("15 mm")` | String with units | Explicit unit specification |
| `createByString("d0 / 2")` | Expression | References existing parameters by name |
| `createByBoolean(True)` | Boolean | For boolean parameters |

### CRITICAL: Internal Units

- **Length**: Always centimeters (cm). `createByReal(5.0)` = 5 cm
- **Angles**: Always radians. `createByReal(math.pi)` = 180 degrees

```python
# 5 cm distance
distance = adsk.core.ValueInput.createByReal(5.0)

# 25.4 mm (= 2.54 cm) using string with explicit units
distance = adsk.core.ValueInput.createByString("25.4 mm")

# Use document default units
distance = adsk.core.ValueInput.createByString("5")

# Reference a parameter
distance = adsk.core.ValueInput.createByString("d0 / 2")

# Boolean
boolVal = adsk.core.ValueInput.createByBoolean(True)
```

## Definition Objects

Definition objects parallel Input objects but are used for editing existing features rather than creation. A key distinction: properties that accept `ValueInput` during creation become read-only on the Definition, returning `Parameter` objects instead.

```python
# Edit an existing extrude feature's distance
disDef = adsk.fusion.DistanceExtentDefinition.cast(extrudeFeature.extentOne)
distanceParam = adsk.fusion.ModelParameter.cast(disDef.distance)
distanceParam.value = 5.0  # 5 cm (internal units)
```

## FeatureOperations Enum

When creating features, you specify the operation type:

| Value | Description |
|-------|-------------|
| `NewBodyFeatureOperation` | Creates a new body |
| `JoinFeatureOperation` | Adds material to existing body |
| `CutFeatureOperation` | Removes material from existing body |
| `IntersectFeatureOperation` | Keeps only intersection of new and existing geometry |
| `NewComponentFeatureOperation` | Creates feature in a new component |
