# Fusion 360 API - Joint and Assembly Motion Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Joint.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointOrigin.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/AsBuiltJoint.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointInput.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Overview

Joints define the mechanical relationships between components in an assembly. They constrain how occurrences move relative to each other, enabling simulation of real-world motion such as hinges, sliders, and ball-and-socket connections. The API provides three main joint mechanisms: Joint Origins (defining snap points), Joints (defining constrained motion), and As-Built Joints (defining motion while preserving current position).

All joint-related collections are accessed from a `Component` object (typically `rootComp` or a sub-component).

---

## Joint Origins

Joint Origins define a coordinate system (position + orientation) on a component that can be used as a snap point when creating joints. They are created from geometry such as faces, edges, or points.

### Accessing the JointOrigins Collection

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Access joint origins on root or any component
jointOrigins = rootComp.jointOrigins
# or: jointOrigins = someComponent.jointOrigins
```

### Creating a Joint Origin

```python
# 1. Get geometry to define the origin (e.g., a planar face)
body = rootComp.bRepBodies.item(0)
face = body.faces.item(0)

# 2. Create JointGeometry from the face
jointGeometry = adsk.fusion.JointGeometry.createByPlanarFace(
    face, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint
)

# 3. Create input
jointOriginInput = jointOrigins.createInput(jointGeometry)

# 4. Add the joint origin
jointOrigin = jointOrigins.add(jointOriginInput)
```

### JointGeometry Static Creation Methods

`JointGeometry` wraps a geometric entity and defines how position and orientation are derived from it.

| Method | Description |
|--------|-------------|
| `createByPlanarFace(face, edge, keyPoint)` | Origin on a planar face. `edge` (optional) sets X direction. `keyPoint` sets position on the face. |
| `createByNonPlanarFace(face, keyPoint)` | Origin on a non-planar (cylindrical, conical, etc.) face. |
| `createByEdge(edge, keyPoint)` | Origin from a linear or circular edge. |
| `createByPoint(point)` | Origin at a construction point, sketch point, or vertex. |
| `createByProfile(profile)` | Origin from a sketch profile. |
| `createByCurve(curve, keyPoint)` | Origin from a sketch curve. |

### JointKeyPointTypes Enum

| Value | Description |
|-------|-------------|
| `StartKeyPoint` | Start vertex of an edge or curve |
| `MiddleKeyPoint` | Midpoint of an edge or curve |
| `EndKeyPoint` | End vertex of an edge or curve |
| `CenterKeyPoint` | Center of a circular edge, face, or profile |

### JointOriginInput Properties

| Property | Type | Description |
|----------|------|-------------|
| `geometry` | JointGeometry | The geometry defining origin position and orientation |
| `xDirection` | Vector3D | Custom X-axis direction (optional override) |
| `zDirection` | Vector3D | Custom Z-axis direction (optional override) |
| `angle` | ValueInput | Rotation angle offset (radians) |
| `offsetX` | ValueInput | Offset along X axis (cm) |
| `offsetY` | ValueInput | Offset along Y axis (cm) |
| `offsetZ` | ValueInput | Offset along Z axis (cm) |
| `isFlipped` | bool | Flip the Z direction |

### JointOrigin Properties (After Creation)

| Property | Type | Description |
|----------|------|-------------|
| `geometry` | JointGeometry (R) | The geometry this origin was created from |
| `name` | str (R/W) | Display name in the browser |
| `isFlipped` | bool (R) | Whether Z direction is flipped |
| `isValid` | bool (R) | Whether the origin is still valid (geometry not deleted) |
| `createForAssemblyContext(occurrence)` | JointOrigin | Creates a proxy for use in assembly context |

---

## Joints

Joints constrain the relative motion between two occurrences. Each joint is defined by two geometry references (one per component) and a motion type.

### Accessing the Joints Collection

```python
joints = rootComp.joints
# or: joints = someComponent.joints
```

### Creating a Joint

```python
# 1. Get geometry for each component
# Component one — a cylindrical face on occurrence1
geo1 = adsk.fusion.JointGeometry.createByNonPlanarFace(
    face1, adsk.fusion.JointKeyPointTypes.CenterKeyPoint
)

# Component two — a cylindrical face on occurrence2
geo2 = adsk.fusion.JointGeometry.createByNonPlanarFace(
    face2, adsk.fusion.JointKeyPointTypes.CenterKeyPoint
)

# 2. Create joint input
jointInput = joints.createInput(geo1, geo2)

# 3. Set motion type (see below)
jointInput.setAsRevoluteJointMotion(
    adsk.fusion.JointDirections.ZAxisJointDirection
)

# 4. Optionally set flip, angle, offset
jointInput.isFlipped = False
jointInput.angle = adsk.core.ValueInput.createByString("0 deg")
jointInput.offset = adsk.core.ValueInput.createByString("0 cm")

# 5. Add
joint = joints.add(jointInput)
```

### JointInput Properties

| Property | Type | Description |
|----------|------|-------------|
| `geometryOrOriginOne` | JointGeometry or JointOrigin (R) | Geometry/origin for component one |
| `geometryOrOriginTwo` | JointGeometry or JointOrigin (R) | Geometry/origin for component two |
| `angle` | ValueInput (R/W) | Rotation angle between components (radians) |
| `offset` | ValueInput (R/W) | Offset distance between snap points (cm) |
| `isFlipped` | bool (R/W) | Flip the alignment direction |

### JointInput Motion Type Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `setAsRigidJointMotion()` | (none) | Lock components together — 0 DOF |
| `setAsRevoluteJointMotion(rotationAxis)` | JointDirections | Rotation around one axis — 1 DOF |
| `setAsSliderJointMotion(slideDirection)` | JointDirections | Translation along one axis — 1 DOF |
| `setAsCylindricalJointMotion(rotationAxis)` | JointDirections | Rotation + translation on same axis — 2 DOF |
| `setAsPinSlotJointMotion(rotationAxis, slideDirection)` | JointDirections, JointDirections | Rotation on one axis, translation on another — 2 DOF |
| `setAsPlanarJointMotion(normalDirection)` | JointDirections | Translation in plane + rotation normal to it — 3 DOF |
| `setAsBallJointMotion()` | (none) | Free rotation on all 3 axes — 3 DOF |

### JointDirections Enum

| Value | Description |
|-------|-------------|
| `XAxisJointDirection` | Along the X axis of the joint origin |
| `YAxisJointDirection` | Along the Y axis of the joint origin |
| `ZAxisJointDirection` | Along the Z axis of the joint origin |

### Joint Properties (After Creation)

| Property | Type | Description |
|----------|------|-------------|
| `name` | str (R/W) | Joint name in browser |
| `jointMotion` | JointMotion (R) | The motion object controlling this joint |
| `geometryOrOriginOne` | JointGeometry or JointOrigin (R) | First snap reference |
| `geometryOrOriginTwo` | JointGeometry or JointOrigin (R) | Second snap reference |
| `occurrenceOne` | Occurrence (R) | First occurrence |
| `occurrenceTwo` | Occurrence (R) | Second occurrence |
| `isFlipped` | bool (R) | Whether alignment is flipped |
| `isLocked` | bool (R/W) | Lock the joint to prevent motion |
| `isSuppressed` | bool (R/W) | Suppress the joint |
| `isLightBulbOn` | bool (R/W) | Visibility of joint in graphics |
| `angle` | ModelParameter (R) | Angle parameter |
| `offset` | ModelParameter (R) | Offset parameter |
| `isValid` | bool (R) | Whether the joint is still valid |
| `deleteMe()` | bool | Delete the joint |

---

## Joint Motion Types

Each joint has a `jointMotion` property that returns a specific motion object based on the joint type. These objects expose the degrees of freedom and current values for that motion.

### Motion Types Table

| Type | Class | DOF | Description |
|------|-------|-----|-------------|
| Rigid | `RigidJointMotion` | 0 | Components are locked together; no relative movement |
| Revolute | `RevoluteJointMotion` | 1 | Rotation around a single axis (hinge) |
| Slider | `SliderJointMotion` | 1 | Translation along a single axis (linear slide) |
| Cylindrical | `CylindricalJointMotion` | 2 | Rotation + translation along the same axis (piston) |
| Pin-Slot | `PinSlotJointMotion` | 2 | Rotation on one axis, translation on a different axis |
| Planar | `PlanarJointMotion` | 3 | Two translations in a plane + rotation normal to it |
| Ball | `BallJointMotion` | 3 | Free rotation on all three axes (ball-and-socket) |

### JointTypes Enum

| Value | Description |
|-------|-------------|
| `RigidJointType` | Rigid — 0 DOF |
| `RevoluteJointType` | Revolute — 1 DOF rotation |
| `SliderJointType` | Slider — 1 DOF translation |
| `CylindricalJointType` | Cylindrical — 2 DOF |
| `PinSlotJointType` | Pin-Slot — 2 DOF |
| `PlanarJointType` | Planar — 3 DOF |
| `BallJointType` | Ball — 3 DOF |

### RevoluteJointMotion Properties

| Property | Type | Description |
|----------|------|-------------|
| `rotationAxis` | JointDirections (R) | Axis of rotation |
| `rotationValue` | float (R/W) | Current rotation angle in radians |
| `rotationLimits` | JointLimits (R) | Min/max rotation limits |

### SliderJointMotion Properties

| Property | Type | Description |
|----------|------|-------------|
| `slideDirection` | JointDirections (R) | Axis of translation |
| `slideValue` | float (R/W) | Current slide distance in cm |
| `slideLimits` | JointLimits (R) | Min/max slide limits |

### CylindricalJointMotion Properties

| Property | Type | Description |
|----------|------|-------------|
| `rotationAxis` | JointDirections (R) | Axis of rotation and translation |
| `rotationValue` | float (R/W) | Current rotation angle in radians |
| `rotationLimits` | JointLimits (R) | Min/max rotation limits |
| `slideValue` | float (R/W) | Current slide distance in cm |
| `slideLimits` | JointLimits (R) | Min/max slide limits |

### PinSlotJointMotion Properties

| Property | Type | Description |
|----------|------|-------------|
| `rotationAxis` | JointDirections (R) | Axis of rotation |
| `slideDirection` | JointDirections (R) | Axis of translation |
| `rotationValue` | float (R/W) | Current rotation angle in radians |
| `rotationLimits` | JointLimits (R) | Min/max rotation limits |
| `slideValue` | float (R/W) | Current slide distance in cm |
| `slideLimits` | JointLimits (R) | Min/max slide limits |

### PlanarJointMotion Properties

| Property | Type | Description |
|----------|------|-------------|
| `normalDirection` | JointDirections (R) | Normal to the plane of motion |
| `primarySlideValue` | float (R/W) | Translation along first in-plane axis (cm) |
| `secondarySlideValue` | float (R/W) | Translation along second in-plane axis (cm) |
| `rotationValue` | float (R/W) | Rotation about the normal (radians) |
| `primarySlideLimits` | JointLimits (R) | Limits for primary slide |
| `secondarySlideLimits` | JointLimits (R) | Limits for secondary slide |
| `rotationLimits` | JointLimits (R) | Limits for rotation |

### BallJointMotion Properties

| Property | Type | Description |
|----------|------|-------------|
| `pitchValue` | float (R/W) | Rotation about X axis (radians) |
| `yawValue` | float (R/W) | Rotation about Y axis (radians) |
| `rollValue` | float (R/W) | Rotation about Z axis (radians) |
| `pitchLimits` | JointLimits (R) | Limits for pitch |
| `yawLimits` | JointLimits (R) | Limits for yaw |
| `rollLimits` | JointLimits (R) | Limits for roll |

### RigidJointMotion

`RigidJointMotion` has no motion properties — the components are fully locked together.

---

## JointLimits

Each degree of freedom on a joint motion object has a `JointLimits` object controlling its range.

### JointLimits Properties

| Property | Type | Description |
|----------|------|-------------|
| `minimumValue` | float (R/W) | Lower bound (radians for rotation, cm for translation) |
| `maximumValue` | float (R/W) | Upper bound (radians for rotation, cm for translation) |
| `isMinimumValueEnabled` | bool (R/W) | Whether the minimum limit is enforced |
| `isMaximumValueEnabled` | bool (R/W) | Whether the maximum limit is enforced |
| `restValue` | float (R/W) | Rest position the joint returns to (radians or cm) |

### Setting Joint Limits Example

```python
joint = rootComp.joints.item(0)
motion = adsk.fusion.RevoluteJointMotion.cast(joint.jointMotion)

if motion:
    limits = motion.rotationLimits
    limits.isMinimumValueEnabled = True
    limits.minimumValue = 0  # radians

    limits.isMaximumValueEnabled = True
    limits.maximumValue = 3.14159  # radians (~180 degrees)

    limits.restValue = 0  # rest at 0 degrees
```

---

## As-Built Joints

As-Built Joints create joints that preserve the current spatial relationship between components. Unlike regular joints (which snap geometry together), as-built joints define motion constraints without moving anything.

### Accessing the AsBuiltJoints Collection

```python
asBuiltJoints = rootComp.asBuiltJoints
# or: asBuiltJoints = someComponent.asBuiltJoints
```

### Creating an As-Built Joint

```python
# 1. Create input — takes the occurrence to constrain
asBuiltJointInput = asBuiltJoints.createInput(occurrence1, occurrence2)

# 2. Set motion type (same method names as JointInput)
asBuiltJointInput.setAsRevoluteJointMotion(
    adsk.fusion.JointDirections.ZAxisJointDirection,
    adsk.fusion.JointKeyPointTypes.CenterKeyPoint
)

# 3. Add the as-built joint
asBuiltJoint = asBuiltJoints.add(asBuiltJointInput)
```

### AsBuiltJointInput Motion Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `setAsRigidJointMotion()` | (none) | Rigid — 0 DOF |
| `setAsRevoluteJointMotion(rotationAxis, keyPoint)` | JointDirections, JointKeyPointTypes | Revolute — 1 DOF rotation |
| `setAsSliderJointMotion(slideDirection, keyPoint)` | JointDirections, JointKeyPointTypes | Slider — 1 DOF translation |
| `setAsCylindricalJointMotion(rotationAxis, keyPoint)` | JointDirections, JointKeyPointTypes | Cylindrical — 2 DOF |
| `setAsPinSlotJointMotion(rotationAxis, slideDirection, keyPoint)` | JointDirections, JointDirections, JointKeyPointTypes | Pin-Slot — 2 DOF |
| `setAsPlanarJointMotion(normalDirection, keyPoint)` | JointDirections, JointKeyPointTypes | Planar — 3 DOF |
| `setAsBallJointMotion(keyPoint)` | JointKeyPointTypes | Ball — 3 DOF |

### AsBuiltJoint Properties (After Creation)

| Property | Type | Description |
|----------|------|-------------|
| `name` | str (R/W) | Joint name in the browser |
| `jointMotion` | JointMotion (R) | The motion object (same types as regular joints) |
| `occurrenceOne` | Occurrence (R) | First occurrence |
| `occurrenceTwo` | Occurrence (R) | Second occurrence |
| `isLocked` | bool (R/W) | Lock the joint |
| `isSuppressed` | bool (R/W) | Suppress the joint |
| `isLightBulbOn` | bool (R/W) | Visibility toggle |
| `isValid` | bool (R) | Whether the joint is still valid |
| `deleteMe()` | bool | Delete the as-built joint |

---

## Driving Joint Motion Programmatically

You can animate or position joints by setting values on their `jointMotion` object. The design must be in Direct Design mode or the joint must be unsuppressed.

### Setting Rotation (Revolute)

```python
joint = rootComp.joints.item(0)
motion = adsk.fusion.RevoluteJointMotion.cast(joint.jointMotion)
if motion:
    import math
    motion.rotationValue = math.radians(45)  # Rotate to 45 degrees
```

### Setting Slide (Slider)

```python
joint = rootComp.joints.item(0)
motion = adsk.fusion.SliderJointMotion.cast(joint.jointMotion)
if motion:
    motion.slideValue = 2.5  # Slide 2.5 cm
```

### Animating a Joint (Step Through Values)

```python
import math, time
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

joint = rootComp.joints.item(0)
motion = adsk.fusion.RevoluteJointMotion.cast(joint.jointMotion)

if motion:
    for deg in range(0, 360, 5):
        motion.rotationValue = math.radians(deg)
        adsk.doEvents()  # Update the viewport
```

### Driving Cylindrical Motion (Two DOF)

```python
motion = adsk.fusion.CylindricalJointMotion.cast(joint.jointMotion)
if motion:
    motion.rotationValue = math.radians(90)
    motion.slideValue = 3.0  # cm
```

---

## Complete Example: Creating a Revolute Joint Between Two Components

This example creates two box components and connects them with a revolute (hinge) joint.

```python
import adsk.core, adsk.fusion, traceback, math

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # --- Create Component One (base) ---
        occ1 = rootComp.occurrences.addNewComponent(
            adsk.core.Matrix3D.create()
        )
        comp1 = occ1.component
        comp1.name = "Base"

        sketch1 = comp1.sketches.add(comp1.xYConstructionPlane)
        sketch1.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-2, -2, 0),
            adsk.core.Point3D.create(2, 2, 0)
        )
        prof1 = sketch1.profiles.item(0)
        ext1Input = comp1.features.extrudeFeatures.createInput(
            prof1,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext1Input.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(1.0)
        )
        comp1.features.extrudeFeatures.add(ext1Input)

        # --- Create Component Two (arm) ---
        transform2 = adsk.core.Matrix3D.create()
        transform2.translation = adsk.core.Vector3D.create(0, 0, 1.0)
        occ2 = rootComp.occurrences.addNewComponent(transform2)
        comp2 = occ2.component
        comp2.name = "Arm"

        sketch2 = comp2.sketches.add(comp2.xYConstructionPlane)
        sketch2.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-0.5, -0.5, 0),
            adsk.core.Point3D.create(0.5, 5, 0)
        )
        prof2 = sketch2.profiles.item(0)
        ext2Input = comp2.features.extrudeFeatures.createInput(
            prof2,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext2Input.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(0.5)
        )
        comp2.features.extrudeFeatures.add(ext2Input)

        # --- Get faces for joint geometry ---
        # Top face of base component (Z = 1.0)
        topFace1 = None
        for face in comp1.bRepBodies.item(0).faces:
            normal = face.geometry.normal if hasattr(face.geometry, 'normal') else None
            if normal and abs(normal.z - 1.0) < 0.001:
                topFace1 = face
                break

        # Bottom face of arm component (Z = 0)
        bottomFace2 = None
        for face in comp2.bRepBodies.item(0).faces:
            normal = face.geometry.normal if hasattr(face.geometry, 'normal') else None
            if normal and abs(normal.z + 1.0) < 0.001:
                bottomFace2 = face
                break

        if not topFace1 or not bottomFace2:
            ui.messageBox("Could not find joint faces")
            return

        # --- Create proxies for assembly context ---
        topFace1Proxy = topFace1.createForAssemblyContext(occ1)
        bottomFace2Proxy = bottomFace2.createForAssemblyContext(occ2)

        # --- Create joint geometry ---
        geo1 = adsk.fusion.JointGeometry.createByPlanarFace(
            topFace1Proxy, None,
            adsk.fusion.JointKeyPointTypes.CenterKeyPoint
        )
        geo2 = adsk.fusion.JointGeometry.createByPlanarFace(
            bottomFace2Proxy, None,
            adsk.fusion.JointKeyPointTypes.CenterKeyPoint
        )

        # --- Create revolute joint ---
        jointInput = rootComp.joints.createInput(geo1, geo2)
        jointInput.setAsRevoluteJointMotion(
            adsk.fusion.JointDirections.ZAxisJointDirection
        )

        joint = rootComp.joints.add(jointInput)
        joint.name = "Hinge"

        # --- Set limits ---
        motion = adsk.fusion.RevoluteJointMotion.cast(joint.jointMotion)
        if motion:
            limits = motion.rotationLimits
            limits.isMinimumValueEnabled = True
            limits.minimumValue = math.radians(-90)
            limits.isMaximumValueEnabled = True
            limits.maximumValue = math.radians(90)
            limits.restValue = 0

        # --- Drive the joint to 45 degrees ---
        if motion:
            motion.rotationValue = math.radians(45)

        ui.messageBox(
            f"Created revolute joint '{joint.name}' between "
            f"'{comp1.name}' and '{comp2.name}'\n"
            f"Current angle: 45 degrees"
        )

    except:
        if ui:
            ui.messageBox(f"Failed:\n{traceback.format_exc()}")
```

---

## Common Patterns and Tips

### Iterating Over All Joints

```python
for i in range(rootComp.joints.count):
    joint = rootComp.joints.item(i)
    motionType = joint.jointMotion.jointType
    print(f"{joint.name}: type={motionType}")
```

### Checking Joint Motion Type

```python
joint = rootComp.joints.item(0)
jm = joint.jointMotion

if jm.jointType == adsk.fusion.JointTypes.RevoluteJointType:
    motion = adsk.fusion.RevoluteJointMotion.cast(jm)
    print(f"Rotation: {math.degrees(motion.rotationValue)} deg")
elif jm.jointType == adsk.fusion.JointTypes.SliderJointType:
    motion = adsk.fusion.SliderJointMotion.cast(jm)
    print(f"Slide: {motion.slideValue} cm")
```

### Assembly Context (Proxy Objects)

When creating joints in the root component between faces/edges that belong to sub-components, you must use proxy objects. Proxies represent the geometry in the assembly context (with correct transforms).

```python
# Get the face from the component
face = comp.bRepBodies.item(0).faces.item(0)

# Create a proxy for the assembly context
faceProxy = face.createForAssemblyContext(occurrence)

# Use the proxy for joint geometry
geo = adsk.fusion.JointGeometry.createByPlanarFace(
    faceProxy, None,
    adsk.fusion.JointKeyPointTypes.CenterKeyPoint
)
```

### Units

- **Rotation values** are always in **radians**. Use `math.radians()` and `math.degrees()` for conversion.
- **Translation values** (slide, offset) are always in **centimeters** (Fusion internal units).
