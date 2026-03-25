---
name: Face sketches default cut direction goes away from body
type: lesson
tags: [sketch, extrude, cut, face-sketch, direction]
---

**What:** When you sketch on a face and try to cut, the default extrude direction points away from the body (outward along the face normal), not into it.

**Details:** Sketching on the top face of a box and attempting a CutFeatureOperation with `setDistanceExtent` fails with "No target body found to cut or intersect!" because the extrude goes upward into empty space. Attempting to flip with `setOneSideExtent(..., NegativeExtentDirection)` also failed in testing. `ProfilePlaneStartDefinition.create()` takes no arguments despite what you might expect.

**Workaround:** Instead of sketching on a face and cutting inward, sketch on a construction plane (like XY at Z=0) and extrude in the positive direction to intersect the body. For hollowing a box, use the Shell feature instead of manual cut — it's simpler and more reliable.

**Why it matters:** Face-sketch cuts are a common source of "no target body" errors that waste multiple retry cycles. Prefer Shell for hollowing, or sketch on origin planes when you need directional control.
