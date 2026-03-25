# Thread Feature API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

Thread features add internal or external threads to cylindrical faces. Threads can be **cosmetic** (visual only, fast) or **modeled** (actual geometry, slow but exportable for 3D printing).

**When to use:**
- Screw threads on bolts, nuts, bottle caps
- Tapped holes (threads on internal cylindrical faces)
- Any threaded connection

**Instead of modeling thread geometry manually** (helix + sweep), use this feature — it handles pitch, depth, and thread profile automatically from standard thread databases.

---

## Creating a Thread

### Step 1: Query Available Thread Types

```python
threadFeats = rootComponent.features.threadFeatures

# Get the thread data query object
query = threadFeats.threadDataQuery

# List all thread types (families)
allTypes = query.allThreadTypes
# Returns: ['ACME General Purpose', 'ANSI Metric M Profile', 'ISO Metric profile', ...]

# Get sizes for a type
sizes = query.allSizes('ISO Metric profile')
# Returns: ['M1', 'M1.1', 'M1.2', ..., 'M100']

# Get designations for a type and size
designations = query.allDesignations(False, 'ISO Metric profile', 'M10')
# Returns: ['M10x1.5', 'M10x1.25', 'M10x1', 'M10x0.75', 'M10x0.5']

# Get classes for a designation
classes = query.allClasses(False, 'ISO Metric profile', 'M10x1.5')
# Returns: ['6g', '6h', etc.]

# Get recommended thread data for a diameter
recommendedInfo = query.recommendThreadData(1.0)  # diameter in cm
```

### Step 2: Create ThreadInfo

```python
# Method 1: Using createThreadInfo on the collection
threadInfo = threadFeats.createThreadInfo(
    isInternal,        # bool: True for tapped hole, False for bolt
    threadType,        # str: 'ISO Metric profile'
    threadDesignation, # str: 'M10x1.5'
    threadClass        # str: '6g'
)

# Method 2: Using ThreadInfo.create (static method)
threadInfo = adsk.fusion.ThreadInfo.create(
    threadType,
    threadDesignation,
    threadClass
)
threadInfo.isInternal = False
threadInfo.isRightHanded = True
```

### Step 3: Create the Thread Feature

```python
# Create input
threadInput = threadFeats.createInput(
    cylindricalFace,  # BRepFace (must be cylindrical)
    threadInfo        # ThreadInfo object
)

# Configure
threadInput.isModeled = False        # True = physical geometry, False = cosmetic
threadInput.isFullLength = True      # Thread entire cylinder
threadInput.isRightHanded = True     # Right-handed thread

# For partial threads:
threadInput.isFullLength = False
threadInput.threadLength = adsk.core.ValueInput.createByString('20 mm')
threadInput.threadOffset = adsk.core.ValueInput.createByString('5 mm')
threadInput.threadLocation = adsk.fusion.ThreadLocations.HighEndThreadLocation

# Add the feature
threadFeat = threadFeats.add(threadInput)
```

---

## ThreadFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputCylindricalFace` | BRepFace | RW | Single cylindrical face to thread |
| `inputCylindricalFaces` | ObjectCollection | RW | Multiple faces (for multi-face threads) |
| `threadInfo` | ThreadInfo | RW | Thread type, size, and designation |
| `isModeled` | bool | RW | True = physical geometry, False = cosmetic (default: False) |
| `isFullLength` | bool | RW | Thread the entire cylinder length (default: True) |
| `isRightHanded` | bool | RW | Right-handed thread (default: True) |
| `threadLength` | ValueInput | RW | Length when not full-length |
| `threadOffset` | ValueInput | RW | Offset from the edge to start of thread |
| `threadLocation` | ThreadLocations | RW | Which end to measure from |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

## ThreadLocations Enum

| Value | Int | Description |
|-------|-----|-------------|
| `HighEndThreadLocation` | 0 | Measured from the high end of the cylinder |
| `LowEndThreadLocation` | 1 | Measured from the low end of the cylinder |

## ThreadInfo Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `threadType` | str | RW | Thread family (e.g., 'ISO Metric profile') |
| `threadDesignation` | str | RW | Size + pitch (e.g., 'M10x1.5') |
| `threadClass` | str | RW | Tolerance class (e.g., '6g') |
| `isInternal` | bool | RW | True = internal (tapped hole), False = external (bolt) |
| `isRightHanded` | bool | RW | True = right-handed |
| `isTapered` | bool | RO | Whether thread is tapered (e.g., pipe threads) |
| `majorDiameter` | float | RO | Major diameter in cm |
| `minorDiameter` | float | RO | Minor diameter in cm |
| `pitchDiameter` | float | RO | Pitch diameter in cm |
| `threadPitch` | float | RO | Pitch in cm |
| `threadAngle` | float | RO | Thread angle in degrees |
| `threadSize` | str | RO | Thread size string |

## ThreadDataQuery Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `allThreadTypes` | — | list[str] | All available thread families |
| `allSizes` | threadType | list[str] | All sizes for a thread type |
| `allDesignations` | isInternal, threadType, size | list[str] | All designations |
| `allClasses` | isInternal, threadType, designation | list[str] | All classes |
| `recommendThreadData` | modelDiameter (cm) | ThreadInfo | Recommended thread for a diameter |
| `defaultMetricThreadType` | — | str | Default metric thread type name |
| `defaultInchThreadType` | — | str | Default inch thread type name |
| `isTapered` | — | bool | Whether querying tapered threads |
| `threadTypeCustomName` | threadType | str | Localized name |
| `threadTypeUnit` | threadType | str | Unit for thread type |

## Cosmetic vs. Modeled Threads

- **Cosmetic** (`isModeled = False`): Displays thread indicator lines but no actual geometry. Fast. Good for visualization. Does NOT export to STL.
- **Modeled** (`isModeled = True`): Creates actual helical thread geometry. Slow and heavy. Required for 3D printing or CNC export.

**For 3D printing: always use `isModeled = True`.**
