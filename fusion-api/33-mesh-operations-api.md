# Mesh Operations API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

Mesh features operate on mesh (triangulated) bodies — typically imported STL/OBJ/3MF files. These tools repair, modify, and convert mesh geometry. All are creatable via API.

**When to use:** Working with imported STL files, preparing mesh bodies for conversion to BRep (solid), or cleaning up scanned geometry.

---

## MeshConvertFeature

Converts mesh bodies to BRep (solid/surface) bodies. This is the key tool for working with imported STL files in parametric modeling.

### Creating a MeshConvert

```python
meshConvertFeats = rootComponent.features.meshConvertFeatures

meshBodies = adsk.core.ObjectCollection.create()
meshBodies.add(meshBody)  # MeshBody object

meshConvertInput = meshConvertFeats.createInput(meshBodies)

# Conversion method
meshConvertInput.meshConvertMethodType = adsk.fusion.MeshConvertMethodTypes.FacetedMeshConvertMethodType
# Options: Faceted (0), Prismatic (1), Organic (2)

# Operation type
meshConvertInput.meshConvertOperationType = adsk.fusion.MeshConvertOperationTypes.ParametricFeatureMeshConvertOperationType

# Resolution (for Organic method)
meshConvertInput.meshConvertResolutionType = adsk.fusion.MeshConvertResolutionTypes.ByAccuracyMeshConvertResolutionType
meshConvertInput.meshConvertAccuracyType = ...  # Medium default

# Preprocessing
meshConvertInput.isPreprocessHoles = True  # smooth hole boundaries for better conversion

meshConvertFeat = meshConvertFeats.add(meshConvertInput)
```

### MeshConvertMethodTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `FacetedMeshConvertMethodType` | 0 | Direct facet-to-BRep (fast, preserves facets) |
| `PrismaticMeshConvertMethodType` | 1 | For mechanical parts with flat/cylindrical faces |
| `OrganicMeshConvertMethodType` | 2 | For organic/sculpted shapes (smooths surfaces) |

---

## MeshRepairFeature

Repairs mesh defects (holes, non-manifold edges, self-intersections).

```python
meshRepairFeats = rootComponent.features.meshRepairFeatures
meshRepairInput = meshRepairFeats.createInput(meshBody)

meshRepairInput.meshRepairType = adsk.fusion.MeshRepairTypes.CloseHolesMeshRepairType
# Options: CloseHoles (0), StitchAndRemove (1), Wrap (2), Rebuild (3)

# For Rebuild mode:
meshRepairInput.meshRepairRebuildType = adsk.fusion.MeshRepairRebuildTypes.FastMeshRepairRebuildType
meshRepairInput.density = 128  # 8-256, controls triangle density
meshRepairInput.offset = 0     # offset from original mesh

meshRepairFeat = meshRepairFeats.add(meshRepairInput)
```

### MeshRepairTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `CloseHolesMeshRepairType` | 0 | Fill holes in the mesh |
| `StitchAndRemoveMeshRepairType` | 1 | Stitch close edges, remove defects |
| `WrapMeshRepairType` | 2 | Wrap mesh in a new surface |
| `RebuildMeshRepairType` | 3 | Completely rebuild the mesh |

---

## MeshReduceFeature

Reduces triangle count while preserving shape.

```python
meshReduceFeats = rootComponent.features.meshReduceFeatures
meshReduceInput = meshReduceFeats.createInput(meshBody)

meshReduceInput.meshReduceMethodType = adsk.fusion.MeshReduceMethodTypes.AdaptiveReduceType
meshReduceInput.meshReduceTargetType = adsk.fusion.MeshReduceTargetTypes.ProportionMeshReduceTargetType
meshReduceInput.proportion = 0.5  # keep 50% of faces

# Alternative targets:
# meshReduceInput.facecount = 1000  # target face count
# meshReduceInput.maximumDeviation = 0.01  # max distance from original

meshReduceFeat = meshReduceFeats.add(meshReduceInput)
```

### MeshReduceTargetTypes Enum

| Value | Int | Description |
|-------|-----|-------------|
| `MaximumDeviationMeshReduceTargetType` | 0 | Reduce until max deviation reached |
| `ProportionMeshReduceTargetType` | 1 | Keep a proportion of faces (0-1) |
| `FaceCountMeshReduceTargetType` | 2 | Target specific face count |

---

## MeshRemeshFeature

Recreates the mesh with more uniform triangles.

```python
meshRemeshFeats = rootComponent.features.meshRemeshFeatures
meshRemeshInput = meshRemeshFeats.createInput(meshBody)

meshRemeshInput.meshRemeshMethodType = adsk.fusion.MeshRemeshMethodTypes.AdaptiveRemeshType
meshRemeshInput.density = 0.25          # 0-1, triangle density
meshRemeshInput.shapePreservation = 0.5  # 0-1, how closely to match original
meshRemeshInput.isPreserveBoundariesEnabled = False
meshRemeshInput.isPreserveSharpEdgesEnabled = False

meshRemeshFeat = meshRemeshFeats.add(meshRemeshInput)
```

---

## MeshSmoothFeature

Smooths mesh surface.

```python
meshSmoothFeats = rootComponent.features.meshSmoothFeatures
meshSmoothInput = meshSmoothFeats.createInput(meshBody)
meshSmoothInput.smoothness = 0.02  # 0-1, higher = stronger smoothing

meshSmoothFeat = meshSmoothFeats.add(meshSmoothInput)
```

---

## MeshShellFeature

Creates a hollow shell from a mesh body.

```python
meshShellFeats = rootComponent.features.meshShellFeatures
meshShellInput = meshShellFeats.createInput(meshBody)
meshShellInput.thickness = 0.2  # wall thickness in cm

meshShellFeat = meshShellFeats.add(meshShellInput)
```

---

## MeshPlaneCutFeature

Cuts a mesh body with a plane.

```python
meshPlaneCutFeats = rootComponent.features.meshPlaneCutFeatures
meshPlaneCutInput = meshPlaneCutFeats.createInput(meshBody)
meshPlaneCutInput.cutPlane = constructionPlane  # or core.Plane

meshPlaneCutInput.meshPlaneCutType = adsk.fusion.MeshPlaneCutTypes.TrimMeshPlaneCutType
# Options: Trim (0), SplitBody (1), SplitFaces (2)

meshPlaneCutInput.meshPlaneCutFillType = adsk.fusion.MeshPlaneCutFillTypes.UniformMeshPlaneCutFillType
# Options: NoFill (0), Minimal (1), Uniform (2)

meshPlaneCutInput.isFlip = False  # which side to keep

meshPlaneCutFeat = meshPlaneCutFeats.add(meshPlaneCutInput)
```

---

## MeshCombineFeature

Boolean operations on mesh bodies (join, cut, intersect, merge).

```python
meshCombineFeats = rootComponent.features.meshCombineFeatures

meshCombineInput = meshCombineFeats.createInput(targetMeshBody)

toolBodies = adsk.core.ObjectCollection.create()
toolBodies.add(toolMeshBody)
meshCombineInput.toolBodies = toolBodies

meshCombineInput.meshCombineOperationType = adsk.fusion.MeshCombineOperationTypes.JoinMeshCombineType
# Options: Join (0), Cut (1), Intersect (2), Merge (3)

meshCombineInput.isKeepToolBodies = False
meshCombineInput.isNewComponent = False

meshCombineFeat = meshCombineFeats.add(meshCombineInput)
```

---

## Other Mesh Features

### MeshSeparateFeature
Separates a mesh body into individual shells or face groups.

```python
meshSepInput = meshSeparateFeats.createInput(meshBody)
meshSepInput.meshSeparateType = adsk.fusion.MeshSeparateTypes.ShellMeshSeparateType
# Options: Shell (0), FaceGroup (1)
meshSepInput.isKeepBody = False
```

### MeshRemoveFeature
Removes mesh bodies from the design.

```python
meshRemoveInput = meshRemoveFeats.createInput(meshBodiesCollection)
```

### MeshReverseNormalFeature
Flips face normals on a mesh body or face groups.

```python
meshRevInput = meshReverseNormalFeats.createInput(meshBodyOrFaceGroups)
```

### MeshGenerateFaceGroupsFeature
Automatically segments a mesh into face groups based on surface normals.

```python
meshGenInput = meshGenFaceGroupFeats.createInput(meshBody)
meshGenInput.meshGenerateFaceGroupsMethodType = adsk.fusion.MeshGenerateFaceGroupsMethodTypes.FastGenerateFaceGroupsType
meshGenInput.angleThreshold = 0.436  # radians, 0 to pi/2
meshGenInput.minimumFaceGroupSize = 0.01  # fraction of total area
```

### MeshCombineFaceGroupsFeature
Combines face groups into one.

```python
meshCombFGInput = meshCombineFaceGroupsFeats.createInput(faceGroupsCollection)
```
