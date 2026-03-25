# Boss, Arrange, Derive & BoundaryFill API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

Specialized features for specific design workflows:
- **Boss**: Creates screw boss connections for plastic part design (injection molding)
- **Arrange**: Automatically arranges components within an envelope (nesting/packing)
- **Derive**: Imports and links geometry from another Fusion design
- **BoundaryFill**: Creates solid regions from intersecting surfaces/planes

---

## BossFeature

Creates screw boss connections — the mounting posts and holes used to fasten plastic enclosures with screws. This is a manufacturing-specific feature for injection-molded parts.

### Creating a Boss

```python
bossFeats = rootComponent.features.bossFeatures

# Position using sketch points
bossInput = bossFeats.createInput()
bossInput.setPositionBySketchPoints(sketchPointOrCollection)

# Configure sides
side1Input = bossInput.createSideInput()
# Side1 = screw head side, Side2 = screw thread side
bossInput.side1 = side1Input
# bossInput.side2 = side2Input  # optional

# Set participating bodies
bossInput.participantBodies = bodiesCollection

bossFeat = bossFeats.add(bossInput)
```

### Boss Output Properties (extensive)

The BossFeature has many parametric properties for controlling:
- **Shank**: `diameter`, `draftAngle`, `rootRadius`, `tipRadius`
- **Hole**: `holeDiameter`, `holeDepth`, `holeDraftAngle`, `holeType`, `holeExtentType`
- **Alignment**: `alignmentType`, `alignmentDepth`, `alignmentDiameter`, `alignmentDraftAngle`
- **Ribs**: `ribCount`, `ribLength`, `ribThickness`, `ribDraftAngle`, `ribRotation`, `ribType`
- **Offset**: `offset`, `offsetClearance`

### BossShapeTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `BossBlank` | 0 | No boss shape |
| `BossConstDiameter` | 1 | Constant diameter boss |
| `BossConstThickness` | 2 | Constant wall thickness boss |

### BossAlignmentTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `BossAlignFlat` | 0 | Flat alignment |
| `BossAlignStepOut` | 1 | Step out alignment |
| `BossAlignStepIn` | 2 | Step in alignment |

---

## ArrangeFeature

Automatically arranges (nests/packs) components within an envelope — useful for optimizing 3D print bed layouts or material cutting.

### Creating an Arrange

```python
arrangeFeats = rootComponent.features.arrangeFeatures

arrangeInput = arrangeFeats.createInput()

# Define the envelope (build plate / material)
# Option 1: Plane envelope (e.g., print bed)
arrangeInput.setPlaneEnvelope(plane)

# Option 2: Profile/face envelope
arrangeInput.setProfileOrFaceEnvelope(profilesOrFaces)

# Option 3: 3D envelope
arrangeInput.set3DEnvelope(...)

# Add components to arrange
arrangeComponents = arrangeInput.arrangeComponents
# Add components via the arrangeComponents collection

arrangeFeat = arrangeFeats.add(arrangeInput)
```

### ArrangeFeature Output Properties

| Property | Type | Description |
|----------|------|-------------|
| `arrangeComponents` | ArrangeComponents | The components being arranged |
| `arrangeStatistics` | str (JSON) | Statistics about the arrangement |
| `definition` | object | The arrangement definition |
| `envelopeDefinition` | object | The envelope definition |
| `resultEnvelopes` | collection | Resulting envelope contents |
| `unusedComponents` | list | Components that didn't fit |

### ArrangeSolverTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `Arrange2DTrueShapeSolverType` | 0 | 2D nesting using true shapes |
| `Arrange2DRectangularSolverType` | 1 | 2D nesting using bounding rectangles |
| `Arrange3DSolverType` | 2 | 3D packing |

---

## DeriveFeature

Imports geometry from another Fusion design and maintains a live link. When the source design changes, the derived geometry can be updated.

### Creating a Derive

```python
deriveFeats = rootComponent.features.deriveFeatures

# Need a DataFile reference to the source design
# dataFile = ... (obtained from app.data)

deriveInput = deriveFeats.createInput(dataFile)

# Access the source design to select what to derive
sourceDesign = deriveInput.sourceDesign

# Select specific entities to bring in
deriveInput.sourceEntities = [someBody, someSketch]

# Exclude specific entities
deriveInput.excludedEntities = [unwantedBody]

# Options
deriveInput.isIncludeComponentParameters = False
deriveInput.isIncludeFavoriteParameters = True
deriveInput.isPlaceObjectsAtOrigin = True

deriveFeat = deriveFeats.add(deriveInput)
```

### DeriveFeature Output Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `sourceDesign` | Design | RO | The source design |
| `sourceEntities` | list | RO | Entities being derived |
| `excludedEntities` | list | RO | Excluded entities |
| `documentReference` | DocumentReference | RO | Link to source document (version control) |
| `isIncludeComponentParameters` | bool | RW | Derive component parameters |
| `isIncludeFavoriteParameters` | bool | RW | Derive favorite parameters |
| `isPlaceObjectsAtOrigin` | bool | RW | Place at origin |

### DeriveFeature Methods

| Method | Description |
|--------|-------------|
| `breakLink()` | Sever connection to source (derived objects become standalone) |
| `getDerivedEntity(sourceEntity)` | Get the derived copy of a source entity |
| `getSourceEntity(derivedEntity)` | Get the source of a derived entity |
| `setSourceEntities(entities)` | Change what's derived |

---

## BoundaryFillFeature

Creates solid bodies from regions defined by intersecting surfaces and construction planes. Useful for creating complex shapes at the intersection of multiple surfaces.

### Creating a BoundaryFill

```python
bfFeats = rootComponent.features.boundaryFillFeatures

# Tools define the boundaries (surfaces, planes, bodies)
tools = adsk.core.ObjectCollection.create()
tools.add(surface1)
tools.add(constructionPlane1)

bfInput = bfFeats.createInput(tools)
bfInput.operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation

# After creating input, query available cells (regions)
cells = bfInput.bRepCells
# Each cell is a closed region — select which ones to keep
for i in range(cells.count):
    cell = cells.item(i)
    cell.isSelected = True  # or False to exclude

bfInput.isRemoveTools = False  # keep the tool surfaces

bfFeat = bfFeats.add(bfInput)
```

### BoundaryFillFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `tools` | ObjectCollection | RW | Surfaces and planes that define boundaries |
| `bRepCells` | BRepCells | RO | Computed closed regions (select which to fill) |
| `operation` | FeatureOperations | RW | Boolean operation |
| `isRemoveTools` | bool | RW | Remove tool surfaces after creation |
| `creationOccurrence` | Occurrence | RW | Assembly context |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### BoundaryFillFeature Methods

| Method | Description |
|--------|-------------|
| `applyCellChanges()` | Must be called after modifying cell selections |

### Important Note

After creating the input and before adding, you must:
1. Access `bfInput.bRepCells` to trigger computation
2. Select which cells to keep (`cell.isSelected = True`)
3. Call `bfInput.cancel()` if you want to abort, or proceed to `add()`
