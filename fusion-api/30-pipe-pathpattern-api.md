# Pipe & Path Pattern API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

- **Pipe**: Creates a tube/pipe along a path — replaces the sketch-circle + sweep-along-path pattern with a single feature.
- **PathPattern**: Duplicates features/bodies/faces along a path curve.

---

## PipeFeature

Creates a solid or hollow tube following a path. Supports circular, square, and triangular cross-sections.

### When to Use Instead of Sweep

Use Pipe when you need a simple tube along a path. Use Sweep when you need a custom cross-section profile or more control over orientation/twist.

**Pipe is one feature. The equivalent sweep requires: sketch a circle → sweep along path → shell (if hollow). Pipe does it all in one step.**

### Creating a Pipe

```python
pipeFeats = rootComponent.features.pipeFeatures

# Path can be: sketch curves, edges, or a Path object
path = rootComponent.features.createPath(edgeOrCurve)

pipeInput = pipeFeats.createInput(path)

# Configure section
pipeInput.sectionType = adsk.fusion.PipeSectionTypes.CircularPipeSectionType
pipeInput.sectionSize = adsk.core.ValueInput.createByString('5 mm')  # diameter/width

# Make hollow (optional)
pipeInput.isHollow = True
pipeInput.sectionThickness = adsk.core.ValueInput.createByString('1 mm')

# Distance along path (optional — default uses full path)
pipeInput.distanceOne = adsk.core.ValueInput.createByReal(1.0)  # 0-1 fraction or distance
# pipeInput.distanceTwo = ...  # for extending in reverse direction

# Boolean operation
pipeInput.operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation

pipeFeat = pipeFeats.add(pipeInput)
```

### PipeFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `path` | Path | RW | The path to follow |
| `sectionType` | PipeSectionTypes | RW | Cross-section shape |
| `sectionSize` | ValueInput | RW | Size (diameter for circular, width for square/triangle) |
| `isHollow` | bool | RW | Solid or hollow pipe |
| `sectionThickness` | ValueInput | RW | Wall thickness (when hollow) |
| `distanceOne` | ValueInput | RW | Distance along path (forward direction) |
| `distanceTwo` | ValueInput | RW | Distance along path (reverse direction) |
| `operation` | FeatureOperations | RW | Boolean operation type |
| `participantBodies` | ObjectCollection | RW | Bodies for cut/intersect operations |
| `creationOccurrence` | Occurrence | RW | Assembly context |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### PipeSectionTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `CircularPipeSectionType` | 0 | Round tube |
| `SquarePipeSectionType` | 1 | Square tube |
| `TriangularPipeSectionType` | 2 | Triangular tube |

---

## PathPatternFeature

Duplicates entities along a path curve. Like rectangular/circular patterns, but follows any arbitrary path.

### When to Use

- Rivets along a curved edge
- Mounting holes following a spline
- Decorative elements along a path
- Any repetition that follows a non-linear path

### Creating a PathPattern

```python
pathPatternFeats = rootComponent.features.pathPatternFeatures

# Entities to pattern (must be all same type)
entities = adsk.core.ObjectCollection.create()
entities.add(someBody)  # Can be faces, features, bodies, or occurrences

# Path to follow
path = rootComponent.features.createPath(edgeOrCurve)

pathPatternInput = pathPatternFeats.createInput(
    entities,
    path,
    adsk.core.ValueInput.createByReal(5),           # quantity
    adsk.core.ValueInput.createByString('100 mm'),   # distance
    adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
)

# Configure
pathPatternInput.isOrientationAlongPath = True   # rotate elements to follow path
pathPatternInput.isSymmetric = False              # one direction only
pathPatternInput.isFlipDirection = False          # direction from start
pathPatternInput.startPoint = 0.0                # 0=start, 1=end of path

# For features: set compute option
pathPatternInput.patternComputeOption = adsk.fusion.PatternComputeOptions.AdjustPatternCompute

pathPatternFeat = pathPatternFeats.add(pathPatternInput)
```

### PathPatternFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputEntities` | ObjectCollection | RW | Entities to pattern (faces, features, bodies, or occurrences — all same type) |
| `path` | Path | RW | Path curve to follow |
| `quantity` | ValueInput | RW | Number of pattern elements |
| `distance` | ValueInput | RW | Total distance or spacing between elements |
| `patternDistanceType` | PatternDistanceType | RW | How distance is interpreted |
| `isOrientationAlongPath` | bool | RW | Rotate elements to follow path (True) or keep identical orientation (False) |
| `isSymmetric` | bool | RW | Pattern in both directions from start point |
| `isFlipDirection` | bool | RW | Reverse the direction |
| `startPoint` | float (0-1) | RW | Start position on path (0=start, 1=end) |
| `patternComputeOption` | PatternComputeOptions | RW | How features are computed |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### PatternDistanceType Enum

| Value | Int | Description |
|-------|-----|-------------|
| `ExtentPatternDistanceType` | 0 | Distance = total extent (elements evenly distributed) |
| `SpacingPatternDistanceType` | 1 | Distance = spacing between each element |

### PatternComputeOptions Enum

| Value | Int | Description |
|-------|-----|-------------|
| `OptimizedPatternCompute` | 0 | Fastest — may not adapt to local geometry |
| `IdenticalPatternCompute` | 1 | All elements identical to original |
| `AdjustPatternCompute` | 2 | Each element recomputed for local context |

### FeatureOperations Enum (shared)

| Value | Int | Description |
|-------|-----|-------------|
| `JoinFeatureOperation` | 0 | Join/union with existing body |
| `CutFeatureOperation` | 1 | Cut/subtract from existing body |
| `IntersectFeatureOperation` | 2 | Intersect with existing body |
| `NewBodyFeatureOperation` | 3 | Create as new body |
| `NewComponentFeatureOperation` | 4 | Create as new component |
