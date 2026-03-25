# BaseFeature & Form (T-Spline Sculpting) API

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

- **BaseFeature**: The bridge between non-parametric (direct, sculpted, or imported) geometry and the parametric timeline. Wraps "raw" bodies so they participate in the timeline.
- **FormFeature**: T-Spline (Sculpt mode) bodies. Limited API — primarily for creating empty forms and loading TSM files, not for interactive sculpting.

---

## BaseFeature

A BaseFeature is a parametric container for non-parametric geometry. When you import a body, receive a body from TemporaryBRepManager, or need to inject direct-edited geometry into the parametric timeline, you wrap it in a BaseFeature.

### When to Use

- Importing bodies from TemporaryBRepManager into the design
- Moving bodies between components (CopyPasteBody creates a BaseFeature)
- Any time you have a "raw" BRepBody that needs to exist in the timeline
- After splitting a sculpted form into components

### Creating a BaseFeature

```python
baseFeats = rootComponent.features.baseFeatures

# Step 1: Create an empty base feature and start editing
baseFeat = baseFeats.add()
baseFeat.startEdit()

# Step 2: Add bodies while in edit mode
# Option A: Add from TemporaryBRepManager
tempBRepMgr = adsk.fusion.TemporaryBRepManager.get()
# ... create temp body ...
rootComponent.bRepBodies.add(tempBody, baseFeat)

# Option B: Add construction geometry, sketches, etc.
# (while baseFeat is being edited, new geometry gets associated with it)

# Step 3: Finish editing
baseFeat.finishEdit()
```

### Updating a BaseFeature Body

```python
# To replace the geometry of an existing BaseFeature body:
baseFeat.startEdit()
baseFeat.updateBody(existingSourceBody, newTempBody)
baseFeat.finishEdit()
```

### BaseFeature Properties

| Property | Type | Description |
|----------|------|-------------|
| `sourceBodies` | BRepBodies | The B-Rep bodies owned by this base feature |
| `bodies` | BRepBodies | Bodies created/modified by this feature |
| `sketches` | list | Sketches associated with this base feature |
| `constructionPlanes` | list | Construction planes in this base feature |
| `constructionAxes` | list | Construction axes in this base feature |
| `constructionPoints` | list | Construction points in this base feature |
| `meshBodies` | list | Mesh bodies associated with this base feature |

### BaseFeature Methods

| Method | Description |
|--------|-------------|
| `startEdit()` | Enter edit mode — new geometry will be associated with this base feature |
| `finishEdit()` | Exit edit mode |
| `updateBody(existingBody, newBody)` | Replace an existing source body's geometry |

### Key Pattern: TemporaryBRepManager → BaseFeature

```python
# This is the standard pattern for creating complex geometry via code:

# 1. Create geometry using TemporaryBRepManager
tempBRepMgr = adsk.fusion.TemporaryBRepManager.get()
tempBody = tempBRepMgr.createBox(...)  # or any temp operation

# 2. Wrap in BaseFeature to add to design
baseFeat = rootComponent.features.baseFeatures.add()
baseFeat.startEdit()
rootComponent.bRepBodies.add(tempBody, baseFeat)
baseFeat.finishEdit()

# Now the body is in the design and appears in the timeline
```

### targetBaseFeature on Other Features

Many feature input objects have a `targetBaseFeature` property. This associates the new feature with an existing base feature rather than creating it as a standalone timeline entry. Use this when building complex geometry step-by-step inside a single base feature context.

---

## FormFeature (T-Spline / Sculpt Mode)

T-Spline forms are Fusion's sculpting/organic modeling system. The API support is **limited** — you can create empty forms and import TSM files, but you cannot programmatically push/pull vertices or perform sculpting operations.

### What You CAN Do

```python
formFeats = rootComponent.features.formFeatures

# Create an empty form (enters sculpt mode in the UI)
formFeat = formFeats.add()

# Access T-Spline bodies within the form
tsBodies = formFeat.tSplineBodies

# Load a T-Spline body from a TSM file
tsBody = tsBodies.addByTSMFile('C:/path/to/model.tsm')

# Load from TSM description string
tsBody = tsBodies.addByTSMDescription(tsmString)

# Enter/exit edit mode
formFeat.startEdit()   # puts UI into sculpt mode
formFeat.finishEdit()  # exits sculpt mode, converts to BRep
```

### What You CANNOT Do (API Limitations)

- Programmatically sculpt (push/pull vertices, insert edge loops, crease edges)
- Modify T-Spline topology
- Create primitive T-Spline bodies (box, cylinder, sphere) via API
- Any of the interactive sculpting operations from the Sculpt workspace

### FormFeature Properties

| Property | Type | Description |
|----------|------|-------------|
| `tSplineBodies` | TSplineBodies | Collection of T-Spline bodies in this form |
| `bodies` | BRepBodies | Resulting B-Rep bodies (after form is finished) |

### FormFeature Methods

| Method | Description |
|--------|-------------|
| `startEdit()` | Enter sculpt edit mode |
| `finishEdit()` | Exit sculpt mode (converts T-Spline → BRep) |

### TSplineBodies Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `addByTSMFile` | filename (str) | Load from a .tsm file |
| `addByTSMDescription` | tsmString (str) | Load from TSM-formatted text |

### Practical Implication

For organic shapes, FormFeature is primarily useful for **importing** pre-made T-Spline models, not for creating them programmatically. For organic shapes via API, use lofts with many sections, or TemporaryBRepManager operations instead.
