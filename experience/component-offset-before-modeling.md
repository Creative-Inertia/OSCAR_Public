---
name: Create multi-part components with offset transforms to avoid interference
type: lesson
tags: [component, transform, interference, cut, multi-body]
---

**What:** When creating multiple components in a design, position each component AWAY from others before adding geometry — don't create at the origin and move later.

**Details:** If you create a second component (e.g., a lid) at the same origin as an existing component (e.g., a box), any cut operations on the new component can bleed through and cut the existing body too. The Fusion timeline records these cuts on the victim component, damaging it.

The fix: pass an offset `Matrix3D` transform to `occurrences.addNewComponent(transform)` BEFORE sketching or extruding in the new component. This ensures the component's local geometry never physically overlaps other components during creation.

```python
offsetTransform = adsk.core.Matrix3D.create()
offsetTransform.translation = adsk.core.Vector3D.create(0, -(box_width + gap), 0)
lidOcc = rootComp.occurrences.addNewComponent(offsetTransform)
```

**Why it matters:** Overlapping components during creation causes silent cross-component cut interference. The stray cut feature appears on the wrong component's timeline, corrupting its geometry. This is hard to notice until you visually inspect the model and see unexpected notches in the victim body.
