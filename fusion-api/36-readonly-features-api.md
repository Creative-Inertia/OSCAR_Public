# Read-Only Features Reference

> Source: Live API introspection from Fusion 360 v2701.1.27, 2026-03-20

## Overview

These features exist in the Fusion API but have **no `createInput` or `add` method** — they cannot be created programmatically. They can only be created through the Fusion UI. However, you can **read and sometimes modify** existing instances of these features via the API.

Understanding what these features are helps you know when to suggest the user create them manually in the UI, and when to choose an API-creatable alternative.

---

## Primitive Features (UI-only creation)

### BoxFeature
Creates a parametric box. **API alternative:** Use ExtrudeFeature on a rectangular sketch profile.

### CylinderFeature
Creates a parametric cylinder. **API alternative:** Use ExtrudeFeature on a circular sketch profile, or RevolveFeature.

### SphereFeature
Creates a parametric sphere. **API alternative:** Use RevolveFeature on a semicircle profile, or TemporaryBRepManager.createSphere().

### TorusFeature
Creates a parametric torus. **API alternative:** Use RevolveFeature on a circular profile offset from the axis.

> **Note:** These primitive features have empty API surfaces — no unique properties beyond the standard Feature properties (name, bodies, timelineObject, etc.). They're thin wrappers around the parametric primitive creation in the UI.

---

## CoilFeature (UI-only creation)

Creates helical geometry — springs, threaded rods, spirals. This is the feature OSCAR has been building manually via TemporaryBRepManager + helixWire + sweep.

**API alternative (documented in memory):**
```
reference_coil_spring_recipe.md — TemporaryBRepManager.createHelixWire + BaseFeature + sweep
```

If CoilFeature were API-creatable, it would be ONE call instead of a multi-step recipe. For now, the manual approach is required.

---

## RibFeature (UI-only creation)

Creates structural ribs — thin wall reinforcements that connect to a body. Common in injection-molded plastic parts.

**API alternative:** Create a sketch on the face, extrude a thin wall, and join to the body. More steps but achieves the same result.

---

## WebFeature (UI-only creation)

Creates structural webs — similar to ribs but spanning between walls/features.

**API alternative:** Same as Rib — sketch + extrude + join.

---

## RuleFilletFeature (UI-only creation)

Applies fillets automatically based on selection rules (all edges, all concave edges, etc.) rather than picking individual edges.

**API alternative:** Use FilletFeature (doc 18) and programmatically collect edges that match the desired rule. For example:

```python
# Emulate "fillet all concave edges" by iterating
edges_to_fillet = adsk.core.ObjectCollection.create()
for i in range(body.edges.count):
    edge = body.edges.item(i)
    if edge.isDegenerate:
        continue
    # Check concavity or other criteria
    edges_to_fillet.add(edge)

filletInput = filletFeats.createInput()
filletInput.addConstantRadiusEdgeSet(edges_to_fillet, radius, True)
```

---

## Sheet Metal Features (UI-only creation)

These features are part of the Sheet Metal workspace and cannot be created via the API. They can be read and sometimes modified.

### FlangeFeature
Creates a flange (bent edge) on sheet metal. No API surface beyond standard properties.

### HemFeature
Creates hems (folded edges) on sheet metal. Has some modifiable properties:

| Method | Description |
|--------|-------------|
| `redefineAsFlatHem(length, isFlipped)` | Change to flat hem |
| `redefineAsRolledHem(radius, angle, isFlipped)` | Change to rolled hem |
| `redefineAsOpenHem(length, gap, isFlipped)` | Change to open hem |
| `redefineAsDoubleHem(gap, length, setback)` | Change to double hem |
| `redefineAsRopeHem(length, gap, radius)` | Change to rope hem |
| `redefineAsTeardropHem(radius, length)` | Change to teardrop hem |

### CornerClosureFeature
Closes corners in sheet metal bends. Has `definition` and `definitionType` properties.

### UnfoldFeature / RefoldFeature
Unfolds/refolds sheet metal bends for flat pattern creation. No API surface.

### RipFeature
Tears/rips sheet metal edges. Can be created via `ripFeatures.add(edges)`.

---

## Summary: What to Use Instead

| Read-Only Feature | API Alternative |
|-------------------|----------------|
| Box | Sketch rectangle → Extrude |
| Cylinder | Sketch circle → Extrude |
| Sphere | Sketch semicircle → Revolve |
| Torus | Sketch circle (offset) → Revolve |
| Coil | TemporaryBRepManager.createHelixWire → sweep |
| Rib | Sketch on face → thin Extrude → Join |
| Web | Sketch on face → thin Extrude → Join |
| RuleFillet | Collect edges programmatically → Fillet |
| Sheet Metal | Must be created in UI; some can be edited via API |
