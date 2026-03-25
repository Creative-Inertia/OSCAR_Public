# Fusion 360 API - Component, Occurrence, and Assembly API

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ComponentsProxies_UM.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Component.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Occurrence.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/AssemblyTraversalUsingRecursion_Sample.htm

## Key Concepts

### Document > Product > Design > Component Hierarchy

```
Document (file)
  └── Products
       ├── Design (modeling data)
       │    └── rootComponent
       │         ├── geometry (sketches, bodies, features)
       │         └── occurrences (instances of sub-components)
       │              └── component → more geometry & occurrences
       └── CAM (manufacturing data)
```

### Component vs. Occurrence

| Aspect | Component | Occurrence |
|--------|-----------|-----------|
| Geometry | Contains geometry (sketches, bodies, features) | References a component; has NO independent geometry |
| Positioning | Defined in model space; cannot be repositioned | Can be repositioned, oriented, constrained |
| Visibility | Not shown in browser/graphics (except root) | Shown in browser and graphics window |
| Uniqueness | One component can be referenced by many occurrences | Each occurrence is unique |
| Editing | Edits affect ALL occurrences | Position/appearance overrides are per-occurrence |

### Critical API Rule

**When creating geometry using the API, the active component is NOT used.** You must explicitly specify which component receives new geometry by accessing its Component object.

```python
# WRONG: relies on active component (UI concept)
# RIGHT: explicitly access the component
rootComp = design.rootComponent
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
```

## Accessing the Design

```python
app = adsk.core.Application.get()
ui = app.userInterface

design = adsk.fusion.Design.cast(app.activeProduct)
if not design:
    ui.messageBox('No active Fusion design', 'No Design')
    return

rootComp = design.rootComponent
```

## Component Object - Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | String (R/W) | Component name in browser |
| `description` | String (R/W) | Description |
| `id` | String (R) | Persistent unique ID within design |
| `sketches` | Sketches (R) | All sketches (supports `add()`) |
| `features` | Features (R) | All features |
| `bRepBodies` | BRepBodies (R) | Solid/surface bodies |
| `meshBodies` | MeshBodies (R) | Mesh bodies |
| `occurrences` | Occurrences (R) | Child occurrences (supports `addNewComponent()`, `addExistingComponent()`) |
| `allOccurrences` | OccurrenceList (R) | All occurrences at any nesting level |
| `constructionPlanes` | ConstructionPlanes (R) | Construction planes |
| `constructionAxes` | ConstructionAxes (R) | Construction axes |
| `constructionPoints` | ConstructionPoints (R) | Construction points |
| `joints` | Joints (R) | Assembly joints |
| `jointOrigins` | JointOrigins (R) | Joint origins |
| `modelParameters` | ModelParameters (R) | Feature-driven parameters |
| `material` | Material (R/W) | Physical material |
| `boundingBox` | BoundingBox3D (R) | Bounding box in world space |
| `xYConstructionPlane` | ConstructionPlane (R) | XY origin plane |
| `xZConstructionPlane` | ConstructionPlane (R) | XZ origin plane |
| `yZConstructionPlane` | ConstructionPlane (R) | YZ origin plane |
| `xConstructionAxis` | ConstructionAxis (R) | X origin axis |
| `yConstructionAxis` | ConstructionAxis (R) | Y origin axis |
| `zConstructionAxis` | ConstructionAxis (R) | Z origin axis |
| `originConstructionPoint` | ConstructionPoint (R) | Origin point |
| `parentDesign` | Design (R) | Parent design |
| `opacity` | Double (R/W) | Opacity (1.0=opaque, 0.0=transparent) |
| `partNumber` | String (R/W) | Part number |
| `attributes` | Attributes (R) | Custom attributes |
| `customGraphicsGroups` | CustomGraphicsGroups (R) | Custom visualization |
| `physicalProperties` | PhysicalProperties (R) | Area, density, mass, volume |

## Component Object - Key Methods

| Method | Description |
|--------|-------------|
| `allOccurrencesByComponent(component)` | All occurrences referencing a specific component |
| `occurrencesByComponent(component)` | Top-level occurrences only |
| `getPhysicalProperties(accuracy)` | Physical properties with specified accuracy |
| `saveCopyAs(name, dataFolder)` | Save component as new document |
| `transformOccurrences(occurrences, transforms)` | Batch transform (root only) |
| `findBRepUsingPoint(point, entityType, proximity)` | Find B-Rep at point |
| `findBRepUsingRay(origin, direction, entityType)` | Find B-Rep along ray |

## Creating Components

Components can only exist through occurrences (except root component):

```python
# Create a new component (creates occurrence + component)
trans = adsk.core.Matrix3D.create()  # Identity = at origin
occ = rootComp.occurrences.addNewComponent(trans)
newComp = occ.component

# Create geometry in the new component
sketch = newComp.sketches.add(newComp.xYConstructionPlane)
sketch.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 5.0
)

# Extrude in the new component
extInput = newComp.features.extrudeFeatures.createInput(
    sketch.profiles.item(0),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
distance = adsk.core.ValueInput.createByReal(10.0)
extInput.setDistanceExtent(False, distance)
ext = newComp.features.extrudeFeatures.add(extInput)
```

## Duplicating Components (Multiple Occurrences)

```python
# Create second occurrence of same component, offset 15 cm in X
trans = adsk.core.Matrix3D.create()
trans.setCell(0, 3, 15.0)  # X translation = 15 cm
newOcc = rootComp.occurrences.addExistingComponent(newComp, trans)

# Both occurrences share the same component
# Editing the component affects both
```

## Occurrence Object - Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | String (R) | Display name with counter (e.g., "Component1:1") |
| `component` | Component (R) | Referenced component |
| `transform2` | Matrix3D (R/W) | Position/orientation in assembly |
| `appearance` | Appearance (R/W) | Override appearance (null = use component's) |
| `isGrounded` | Boolean (R/W) | Whether grounded (fixed) |
| `isVisible` | Boolean (R) | Visibility state |
| `isLightBulbOn` | Boolean (R/W) | Browser visibility toggle |
| `childOccurrences` | OccurrenceList (R) | Sub-occurrences |
| `bRepBodies` | BRepBodies (R) | Proxy bodies from referenced component |
| `joints` | Joints (R) | Affecting joint constraints |
| `fullPathName` | String (R) | Complete hierarchical path name |
| `assemblyContext` | Occurrence (R) | Assembly context |
| `nativeObject` | Object (R) | Non-proxy object |
| `entityToken` | String (R) | Persistent retrieval token |
| `timelineObject` | TimelineObject (R) | Creation timeline entry |

## Occurrence Object - Key Methods

| Method | Description |
|--------|-------------|
| `activate()` | Set as active edit target |
| `deleteMe()` | Delete (removes component if last reference) |
| `moveToComponent(targetOccurrence)` | Move to another component |
| `replace(newComponent, replaceAll)` | Replace with different component |
| `breakLink()` | Convert external reference to local |
| `createForAssemblyContext(occurrence)` | Create proxy for assembly context |

## Positioning Occurrences (Transform)

```python
# Get current transform
trans = occ.transform2

# Set translation (position)
trans.setCell(0, 3, 10.0)  # X = 10 cm
trans.setCell(1, 3, 5.0)   # Y = 5 cm
trans.setCell(2, 3, 0.0)   # Z = 0 cm

# Apply
occ.transform2 = trans

# Or create new transform with rotation
trans = adsk.core.Matrix3D.create()
axis = adsk.core.Vector3D.create(0, 0, 1)  # Z axis
origin = adsk.core.Point3D.create(0, 0, 0)
trans.setToRotation(math.pi / 4, axis, origin)  # 45 degrees
trans.setCell(0, 3, 10.0)  # also translate X
occ.transform2 = trans
```

## Proxies

When working with assemblies, geometry from sub-components must be accessed through proxies to maintain correct context.

### Why Proxies Are Needed

If Component9 has a face called "RedFace" and two occurrences exist (Component9:1 and Component9:2), you need proxies to distinguish between the two instances of RedFace.

### Creating Proxies

```python
# Get the actual face from the component
actualFace = component.bRepBodies.item(0).faces.item(0)

# Create proxy for a specific occurrence context
proxyFace = actualFace.createForAssemblyContext(occurrence)

# Now proxyFace can be used in root component operations
sketch = rootComp.sketches.add(proxyFace)  # Sketch on that specific face
```

### Proxy Properties

| Property | Description |
|----------|-------------|
| `assemblyContext` | The occurrence providing context |
| `nativeObject` | The actual entity in the component |

### Common Proxy Pattern

```python
# When working with faces from sub-components in root context:
for occ in rootComp.occurrences:
    for body in occ.bRepBodies:
        for face in body.faces:
            # face is already a proxy (has assembly context)
            normal = face.evaluator.getNormalAtParameter(...)
```

## Assembly Traversal (Recursive)

```python
def traverseAssembly(occurrences, currentLevel, inputString):
    for i in range(0, occurrences.count):
        occ = occurrences.item(i)
        inputString += ' ' * (currentLevel * 5) + occ.name + '\n'

        if occ.childOccurrences:
            inputString = traverseAssembly(
                occ.childOccurrences,
                currentLevel + 1,
                inputString
            )
    return inputString

def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    rootComp = design.rootComponent

    result = 'Root (' + design.parentDocument.name + ')\n'
    result = traverseAssembly(rootComp.occurrences.asList, 1, result)

    # Output to Text Commands palette
    textPalette = app.userInterface.palettes.itemById('TextCommands')
    if not textPalette.isVisible:
        textPalette.isVisible = True
    textPalette.writeText(result)
```

## Design Types (January 2026)

The API now distinguishes between three design types:

```python
intent = design.designIntent
# Returns: DesignTypes.HybridDesignType, PartDesignType, or AssemblyDesignType

# For assembly designs, check if modeling is enabled
if design.isModelingInAssemblyEnabled:
    # Can create geometry in assembly context
```
