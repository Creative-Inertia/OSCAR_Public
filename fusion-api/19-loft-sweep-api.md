# Fusion 360 API - Loft & Sweep Feature API Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/LoftFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/LoftFeatures_createInput.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SweepFeature.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SweepFeatures_createInput.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Loft features create shapes by blending between two or more cross-section profiles. Sweep features create shapes by moving a profile along a path curve. Both are accessed through `rootComp.features`.

---

## Loft Features

### Accessing the LoftFeatures Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

loftFeats = rootComp.features.loftFeatures
```

### LoftFeatures Collection - Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `createInput(operation)` | LoftFeatureInput | Creates a LoftFeatureInput object to define the loft |
| `add(input)` | LoftFeature | Creates a loft feature from the input |
| `item(index)` | LoftFeature | Returns loft feature at given index |
| `itemByName(name)` | LoftFeature | Returns loft feature by name |
| `count` | int | Number of loft features |

### Creating a Loft: Input Pattern

```python
# 1. Create input
loftInput = loftFeats.createInput(
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# 2. Add sections (profiles)
loftSections = loftInput.loftSections
loftSections.add(profile1)
loftSections.add(profile2)

# 3. Optionally configure rails, end conditions, etc.
# 4. Add feature
loftFeature = loftFeats.add(loftInput)
```

### LoftFeatureInput - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `loftSections` | LoftSections | R | Collection of cross-section profiles for the loft |
| `centerLineOrRails` | LoftCenterLineOrRails | R | Collection for center line or guide rails |
| `isSolid` | Boolean | R/W | True to create solid body, False for surface |
| `isClosed` | Boolean | R/W | True to close the loft (connect last section back to first) |
| `isTangentEdgesMerged` | Boolean | R/W | True to merge tangent edges in the result |
| `operation` | FeatureOperations | R/W | NewBody, Join, Cut, Intersect, or NewComponent |

### LoftSections Collection - Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add(profileOrEntity)` | LoftSection | Adds a profile or planar face as a loft section |
| `item(index)` | LoftSection | Returns loft section at given index |
| `count` | int | Number of sections |

The `add` method accepts a `Profile`, `BRepFace`, `SketchPoint`, or `ConstructionPoint` as the section entity.

### LoftSection - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `entity` | Base | R/W | The profile, face, or point defining this section |
| `endCondition` | LoftEndCondition | R/W | End condition for this section |
| `isFreeEnd` | Boolean | R | Whether this section has a free end condition |
| `isTangentEnd` | Boolean | R | Whether this section has a tangent end condition |
| `isDirectionEnd` | Boolean | R | Whether this section has a direction end condition |
| `isSmoothEnd` | Boolean | R | Whether this section has a smooth end condition |

### LoftCenterLineOrRails Collection - Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `addRail(entity)` | LoftCenterLineOrRail | Adds a guide rail (sketch curve or edge) |
| `addCenterLine(entity)` | LoftCenterLineOrRail | Adds a center line to guide the loft |
| `item(index)` | LoftCenterLineOrRail | Returns item at given index |
| `count` | int | Number of rails/center lines |

### LoftEndCondition Types

End conditions control how the loft surface meets each section profile.

| Type | Description |
|------|-------------|
| `LoftFreeEndCondition` | Default. No tangency constraint at the section. |
| `LoftDirectionEndCondition` | Loft meets the section at a specified angle. Has `angle` property (ValueInput). |
| `LoftPointTangentEndCondition` | Tangent to an adjacent face at a point section. |
| `LoftPointSharpEndCondition` | Sharp (no tangency) at a point section. |
| `LoftSmoothEndCondition` | Smooth (G2 curvature continuity) transition at the section. Has `weight` property. |
| `LoftTangentEndCondition` | Tangent (G1) to an adjacent face at the section. Has `weight` property. |

#### Setting End Conditions

```python
# Get the first section
section = loftInput.loftSections.item(0)

# Free end (default)
freeEnd = adsk.fusion.LoftFreeEndCondition.create()
section.endCondition = freeEnd

# Direction end condition with angle
dirEnd = adsk.fusion.LoftDirectionEndCondition.create()
dirEnd.angle = adsk.core.ValueInput.createByString("45 deg")
section.endCondition = dirEnd

# Tangent end condition with weight
tangentEnd = adsk.fusion.LoftTangentEndCondition.create()
tangentEnd.weight = adsk.core.ValueInput.createByReal(1.0)
section.endCondition = tangentEnd

# Smooth end condition with weight
smoothEnd = adsk.fusion.LoftSmoothEndCondition.create()
smoothEnd.weight = adsk.core.ValueInput.createByReal(1.0)
section.endCondition = smoothEnd
```

### Complete Loft Example: Two Profiles

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # --- Create first sketch on XY plane ---
        sketch1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
        sketch1.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), 5.0  # 5 cm radius
        )

        # --- Create offset plane for second sketch ---
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()
        offsetVal = adsk.core.ValueInput.createByReal(10.0)  # 10 cm offset
        planeInput.setByOffset(rootComp.xYConstructionPlane, offsetVal)
        offsetPlane = planes.add(planeInput)

        # --- Create second sketch on offset plane ---
        sketch2 = rootComp.sketches.add(offsetPlane)
        sketch2.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), 2.0  # 2 cm radius
        )

        # --- Get profiles ---
        prof1 = sketch1.profiles.item(0)
        prof2 = sketch2.profiles.item(0)

        # --- Create loft ---
        loftFeats = rootComp.features.loftFeatures
        loftInput = loftFeats.createInput(
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        loftSections = loftInput.loftSections
        loftSections.add(prof1)
        loftSections.add(prof2)

        loftInput.isSolid = True

        loftFeature = loftFeats.add(loftInput)

        app.log("Loft created: " + loftFeature.name)

    except:
        app.log("Loft failed:\n" + traceback.format_exc())
```

### Loft with Guide Rail Example

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # --- Create first sketch (rectangle) on XY plane ---
        sketch1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
        lines1 = sketch1.sketchCurves.sketchLines
        lines1.addTwoPointRectangle(
            adsk.core.Point3D.create(-3, -2, 0),
            adsk.core.Point3D.create(3, 2, 0)
        )

        # --- Create offset plane ---
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()
        planeInput.setByOffset(
            rootComp.xYConstructionPlane,
            adsk.core.ValueInput.createByReal(8.0)
        )
        offsetPlane = planes.add(planeInput)

        # --- Create second sketch (circle) on offset plane ---
        sketch2 = rootComp.sketches.add(offsetPlane)
        sketch2.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), 2.0
        )

        # --- Create guide rail sketch on XZ plane ---
        sketchRail = rootComp.sketches.add(rootComp.xZConstructionPlane)
        splines = sketchRail.sketchCurves.sketchFittedSplines
        points = adsk.core.ObjectCollection.create()
        points.add(adsk.core.Point3D.create(3, 0, 0))
        points.add(adsk.core.Point3D.create(4, 4, 0))
        points.add(adsk.core.Point3D.create(2, 8, 0))
        railCurve = splines.add(points)

        # --- Get profiles ---
        prof1 = sketch1.profiles.item(0)
        prof2 = sketch2.profiles.item(0)

        # --- Create loft with guide rail ---
        loftFeats = rootComp.features.loftFeatures
        loftInput = loftFeats.createInput(
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        loftInput.loftSections.add(prof1)
        loftInput.loftSections.add(prof2)

        # Add guide rail
        loftInput.centerLineOrRails.addRail(railCurve)

        loftInput.isSolid = True

        loftFeature = loftFeats.add(loftInput)

    except:
        app.log("Loft with rail failed:\n" + traceback.format_exc())
```

### LoftFeature Object - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Feature name in browser/timeline |
| `bodies` | BRepBodies | R | Bodies modified or created by the loft |
| `faces` | BRepFaces | R | All faces created by the loft |
| `sideFaces` | BRepFaces | R | Side faces of the loft |
| `endFaces` | BRepFaces | R | End faces of the loft |
| `startFaces` | BRepFaces | R | Start faces of the loft |
| `isSolid` | Boolean | R/W | Whether the loft creates a solid body |
| `isClosed` | Boolean | R | Whether the loft is closed |
| `isTangentEdgesMerged` | Boolean | R/W | Whether tangent edges are merged |
| `operation` | FeatureOperations | R/W | NewBody, Join, Cut, Intersect |
| `loftSections` | LoftSections | R | The loft sections (read-only after creation) |
| `centerLineOrRails` | LoftCenterLineOrRails | R | Guide rails or center line |
| `isSuppressed` | Boolean | R/W | Whether the feature is suppressed |
| `healthState` | FeatureHealthStates | R | Feature health state |
| `errorOrWarningMessage` | String | R | Error or warning message if unhealthy |
| `timelineObject` | TimelineObject | R | Timeline entry for this feature |
| `parentComponent` | Component | R | Component containing this feature |
| `isParametric` | Boolean | R | Whether in parametric design mode |

### LoftFeature Object - Methods

| Method | Description |
|--------|-------------|
| `deleteMe()` | Delete the loft feature |
| `dissolve()` | Remove feature from timeline, keep geometry |

---

## Sweep Features

### Accessing the SweepFeatures Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

sweepFeats = rootComp.features.sweepFeatures
```

### SweepFeatures Collection - Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `createInput(profile, path, operation)` | SweepFeatureInput | Creates a SweepFeatureInput to define the sweep |
| `add(input)` | SweepFeature | Creates a sweep feature from the input |
| `item(index)` | SweepFeature | Returns sweep feature at given index |
| `itemByName(name)` | SweepFeature | Returns sweep feature by name |
| `count` | int | Number of sweep features |

### SweepFeatures.createInput Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile` | Profile | The profile to sweep along the path |
| `path` | Path | The path curve to sweep along |
| `operation` | FeatureOperations | NewBody, Join, Cut, Intersect, or NewComponent |

### Creating a Path Object

Before creating a sweep, you need a `Path` object from sketch curves or edges:

```python
# Create a Path from a sketch curve
path = rootComp.features.createPath(sketchCurve)

# createPath can also accept an edge or a collection of connected edges
path = rootComp.features.createPath(edge, isChain=True)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `curve` | Base | A SketchCurve, BRepEdge, or ObjectCollection of connected curves/edges |
| `isChain` | Boolean | True to automatically chain connected curves/edges |

### Creating a Sweep: Input Pattern

```python
# 1. Create path from sketch curve
path = rootComp.features.createPath(sketchLine)

# 2. Create input
sweepInput = sweepFeats.createInput(
    profile, path,
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)

# 3. Optionally configure orientation, taper, distance, guide rail
# 4. Add feature
sweepFeature = sweepFeats.add(sweepInput)
```

### SweepFeatureInput - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `profile` | Profile | R/W | The profile to sweep |
| `path` | Path | R/W | The sweep path |
| `operation` | FeatureOperations | R/W | Feature operation type |
| `orientation` | SweepOrientationTypes | R/W | How the profile is oriented along the path |
| `distanceOne` | ValueInput | R/W | Distance for partial sweep (side one). If unset, sweeps full path. |
| `distanceTwo` | ValueInput | R/W | Distance for partial sweep (side two, for two-sided sweeps) |
| `taperAngleOne` | ValueInput | R/W | Taper angle for side one |
| `taperAngleTwo` | ValueInput | R/W | Taper angle for side two |
| `guideRail` | Path | R/W | Optional guide rail to control the sweep shape |
| `isSolid` | Boolean | R/W | True for solid, False for surface |
| `isDirectionFlipped` | Boolean | R/W | Flip the sweep direction along the path |
| `profileScaling` | SweepProfileScalingOptions | R/W | How the profile scales along the sweep |

### SweepOrientationTypes Enum

| Value | Description |
|-------|-------------|
| `PerpendicularOrientationType` | Profile stays perpendicular to the path at all points (default) |
| `ParallelOrientationType` | Profile stays parallel to its original orientation |
| `KeepNormalOrientationType` | Profile normal is maintained relative to the surface |

```python
sweepInput.orientation = adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
```

### SweepProfileScalingOptions Enum

| Value | Description |
|-------|-------------|
| `SweepProfileScaleOption` | Profile scales along the path |
| `SweepProfileNoScaleOption` | Profile does not scale |

### Complete Sweep Example: Circle Along a Path

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # --- Create path sketch on XZ plane ---
        sketchPath = rootComp.sketches.add(rootComp.xZConstructionPlane)
        lines = sketchPath.sketchCurves.sketchLines

        # Create an L-shaped path
        line1 = lines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(10, 0, 0)
        )
        line2 = lines.addByTwoPoints(
            adsk.core.Point3D.create(10, 0, 0),
            adsk.core.Point3D.create(10, 10, 0)
        )

        # --- Create profile sketch on XY plane ---
        sketchProfile = rootComp.sketches.add(rootComp.xYConstructionPlane)
        sketchProfile.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), 1.0  # 1 cm radius
        )

        # --- Get profile ---
        prof = sketchProfile.profiles.item(0)

        # --- Create path from sketch curve (chained) ---
        path = rootComp.features.createPath(line1, isChain=True)

        # --- Create sweep ---
        sweepFeats = rootComp.features.sweepFeatures
        sweepInput = sweepFeats.createInput(
            prof, path,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        sweepInput.orientation = (
            adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
        )
        sweepInput.isSolid = True

        sweepFeature = sweepFeats.add(sweepInput)

        app.log("Sweep created: " + sweepFeature.name)

    except:
        app.log("Sweep failed:\n" + traceback.format_exc())
```

### Sweep with Taper Angle Example

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # --- Create path sketch (straight line on XZ plane) ---
        sketchPath = rootComp.sketches.add(rootComp.xZConstructionPlane)
        pathLine = sketchPath.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(15, 0, 0)
        )

        # --- Create profile sketch (rectangle on XY plane) ---
        sketchProfile = rootComp.sketches.add(rootComp.xYConstructionPlane)
        sketchProfile.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-1, -1, 0),
            adsk.core.Point3D.create(1, 1, 0)
        )

        prof = sketchProfile.profiles.item(0)
        path = rootComp.features.createPath(pathLine)

        # --- Create sweep with taper ---
        sweepFeats = rootComp.features.sweepFeatures
        sweepInput = sweepFeats.createInput(
            prof, path,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        sweepInput.taperAngleOne = adsk.core.ValueInput.createByString("5 deg")
        sweepInput.isSolid = True

        sweepFeature = sweepFeats.add(sweepInput)

    except:
        app.log("Tapered sweep failed:\n" + traceback.format_exc())
```

### Sweep with Guide Rail Example

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # --- Create path sketch (line on XZ plane) ---
        sketchPath = rootComp.sketches.add(rootComp.xZConstructionPlane)
        pathLine = sketchPath.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(12, 0, 0)
        )

        # --- Create guide rail sketch (spline on XZ plane) ---
        sketchRail = rootComp.sketches.add(rootComp.xZConstructionPlane)
        points = adsk.core.ObjectCollection.create()
        points.add(adsk.core.Point3D.create(0, 2, 0))
        points.add(adsk.core.Point3D.create(4, 4, 0))
        points.add(adsk.core.Point3D.create(8, 3, 0))
        points.add(adsk.core.Point3D.create(12, 2, 0))
        railCurve = sketchRail.sketchCurves.sketchFittedSplines.add(points)

        # --- Create profile sketch (circle on XY plane) ---
        sketchProfile = rootComp.sketches.add(rootComp.xYConstructionPlane)
        sketchProfile.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), 2.0
        )

        prof = sketchProfile.profiles.item(0)
        path = rootComp.features.createPath(pathLine)
        guideRail = rootComp.features.createPath(railCurve)

        # --- Create sweep with guide rail ---
        sweepFeats = rootComp.features.sweepFeatures
        sweepInput = sweepFeats.createInput(
            prof, path,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        sweepInput.guideRail = guideRail
        sweepInput.isSolid = True

        sweepFeature = sweepFeats.add(sweepInput)

    except:
        app.log("Guided sweep failed:\n" + traceback.format_exc())
```

### SweepFeature Object - Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `name` | String | R/W | Feature name in browser/timeline |
| `bodies` | BRepBodies | R | Bodies modified or created by the sweep |
| `faces` | BRepFaces | R | All faces created by the sweep |
| `sideFaces` | BRepFaces | R | Side faces of the sweep |
| `endFaces` | BRepFaces | R | End faces of the sweep |
| `startFaces` | BRepFaces | R | Start faces of the sweep |
| `profile` | Profile | R/W | The sweep profile |
| `path` | Path | R | The sweep path |
| `orientation` | SweepOrientationTypes | R/W | Profile orientation type |
| `distanceOne` | ModelParameter | R | Distance parameter for side one |
| `distanceTwo` | ModelParameter | R | Distance parameter for side two |
| `taperAngleOne` | ModelParameter | R | Taper angle parameter for side one |
| `taperAngleTwo` | ModelParameter | R | Taper angle parameter for side two |
| `guideRail` | Path | R | Guide rail path (if used) |
| `isSolid` | Boolean | R | Whether the sweep creates a solid body |
| `operation` | FeatureOperations | R/W | Feature operation type |
| `isSuppressed` | Boolean | R/W | Whether the feature is suppressed |
| `healthState` | FeatureHealthStates | R | Feature health state |
| `errorOrWarningMessage` | String | R | Error or warning message if unhealthy |
| `timelineObject` | TimelineObject | R | Timeline entry for this feature |
| `parentComponent` | Component | R | Component containing this feature |
| `isParametric` | Boolean | R | Whether in parametric design mode |
| `profileScaling` | SweepProfileScalingOptions | R/W | How profile scales along the path |

### SweepFeature Object - Methods

| Method | Description |
|--------|-------------|
| `deleteMe()` | Delete the sweep feature |
| `dissolve()` | Remove feature from timeline, keep geometry |

---

## FeatureOperations Enum (Shared)

| Value | Description |
|-------|-------------|
| `NewBodyFeatureOperation` | Creates a new body |
| `JoinFeatureOperation` | Adds material to existing body |
| `CutFeatureOperation` | Removes material from existing body |
| `IntersectFeatureOperation` | Keeps only intersection |
| `NewComponentFeatureOperation` | Creates in new component |

## Feature Health Check (Shared Pattern)

```python
# Works for both LoftFeature and SweepFeature
health = feature.healthState
if health == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
    msg = feature.errorOrWarningMessage
elif health == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
    msg = feature.errorOrWarningMessage
```
