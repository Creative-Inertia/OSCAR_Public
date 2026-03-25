# Offset, Tessellate, MergeFaces & Custom Feature API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

Utility features for geometry manipulation:
- **OffsetFeature**: Offset faces to create a new surface body (different from OffsetFacesFeature)
- **TessellateFeature**: Convert BRep bodies to mesh bodies
- **MergeFacesFeature**: Merge adjacent faces into one
- **CustomFeature**: Define your own parametric features

---

## OffsetFeature

Creates a new surface body by offsetting faces at a specified distance. **This is different from OffsetFacesFeature** (doc 24) — OffsetFeature creates a NEW body, while OffsetFacesFeature modifies existing faces in place.

### Creating an OffsetFeature

```python
offsetFeats = rootComponent.features.offsetFeatures

# Select faces to offset
faces = adsk.core.ObjectCollection.create()
faces.add(someFace)  # BRepFace

offsetInput = offsetFeats.createInput(
    faces,
    adsk.core.ValueInput.createByString('2 mm'),  # offset distance
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation  # or NewComponentFeatureOperation
)

# Chain tangent faces
offsetInput.isChainSelection = True

offsetFeat = offsetFeats.add(offsetInput)
```

### OffsetFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `entities` | ObjectCollection of BRepFace | RW | Faces to offset |
| `distance` | ValueInput | RW | Offset distance (+/- for direction) |
| `operation` | FeatureOperations | RW | NewBody or NewComponent only |
| `isChainSelection` | bool | RW | Include tangent-connected faces |
| `targetBaseFeature` | BaseFeature | RW | Base feature context |

### OffsetFeature vs OffsetFacesFeature

| | OffsetFeature | OffsetFacesFeature |
|---|---|---|
| Creates new body | Yes | No |
| Modifies existing | No | Yes |
| Operation types | NewBody, NewComponent | N/A (modifies in place) |
| Use case | Create a shell/offset surface | Push/pull faces |

---

## TessellateFeature

Converts BRep (solid/surface) bodies to mesh bodies. The reverse of MeshConvertFeature.

### Creating a TessellateFeature

```python
tessFeats = rootComponent.features.tessellateFeatures

bodies = adsk.core.ObjectCollection.create()
bodies.add(solidBody)  # BRepBody

tessInput = tessFeats.createInput(bodies)

# Refinement level
tessInput.tessellateRefinementType = adsk.fusion.TessellateRefinementTypes.MediumTessellateRefinementType

# For custom refinement:
tessInput.tessellateRefinementType = adsk.fusion.TessellateRefinementTypes.CustomTessellateRefinementType
tessInput.surfaceDeviation = ...     # max distance from original surface
tessInput.normalDeviation = ...      # max angle between normals
tessInput.maximumEdgeLength = ...    # max edge length
tessInput.aspectRatio = ...          # height/width ratio of faces

# Quad faces
tessInput.createQuads = True  # create quads where possible

tessFeat = tessFeats.add(tessInput)
```

### TessellateRefinementTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `HighTessellateRefinementType` | 0 | Highest fidelity (most triangles) |
| `MediumTessellateRefinementType` | 1 | Balanced |
| `LowTessellateRefinementType` | 2 | Fewest triangles |
| `CustomTessellateRefinementType` | 3 | Manual control |

---

## MergeFacesFeature

Merges adjacent faces on a body into a single face. Useful for cleaning up geometry after splits or boolean operations that leave unnecessary face boundaries.

### Creating a MergeFacesFeature

```python
mergeFeats = rootComponent.features.mergeFacesFeatures

faces = [face1, face2, face3]  # adjacent BRepFace objects from the same body

mergeInput = mergeFeats.createInput(faces)
mergeInput.isChainSelection = True  # include tangent-connected faces

mergeFeat = mergeFeats.add(mergeInput)
```

### MergeFacesFeatureInput Properties

| Property | Type | R/W | Description |
|----------|------|-----|-------------|
| `inputFaces` | array of BRepFace | RW | Adjacent faces to merge (must be from same body) |
| `isChainSelection` | bool | RW | Include tangent-connected faces |
| `creationOccurrence` | Occurrence | RW | Assembly context |

---

## CustomFeature

Defines a custom parametric feature that groups other features together with custom parameters. This is an advanced API for building reusable parametric components.

### Creating a Custom Feature

```python
customFeats = rootComponent.features.customFeatures

customInput = customFeats.createInput('MyCustomFeature')

# Add custom parameters
customInput.addCustomParameter('width', adsk.core.ValueInput.createByString('10 mm'), 'mm', False)

# Add dependencies
customInput.addDependency(someEntity)  # entity this feature depends on

# Set grouped features (timeline range)
customInput.setStartAndEndFeatures(startFeature, endFeature)

customFeat = customFeats.add(customInput)
```

### CustomFeatureInput Methods

| Method | Description |
|--------|-------------|
| `addCustomParameter(name, value, units, isUserModifiable)` | Add a parameter |
| `addDependency(entity)` | Add an entity dependency |
| `setStartAndEndFeatures(start, end)` | Group timeline features |

### CustomFeature Properties

| Property | Type | Description |
|----------|------|-------------|
| `features` | collection | Features grouped by this custom feature |

---

## SilhouetteSplitFeature (Summary)

Documented in detail in `26-splitbody-splitface-api.md`. Splits a body along its silhouette from a view direction — useful for mold parting lines.

---

## VolumetricCustomFeature & VolumetricModelToMeshFeature

Advanced features for volumetric modeling workflows (lattice structures, generative design). These operate on volumetric model representations.

### VolumetricModelToMeshFeature
Converts a volumetric model to a mesh body.

```python
volToMeshFeats = rootComponent.features.volumetricModelToMeshFeatures
volInput = volToMeshFeats.createInput(volumetricModel)
volInput.refinementType = ...  # Low, Medium, High, Custom
volInput.meshingApproach = ...  # Basic or Advanced
volInput.elementSize = ...  # custom element size (when Custom)
volInput.isSmallShellsRemoved = False
volInput.isVolumetricModelRemoved = True  # remove source after conversion
```
