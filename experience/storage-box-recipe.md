---
name: Storage box with lift-off lid recipe
type: recipe
tags: [box, lid, shell, 3d-print, parametric]
---

**What:** Step-by-step recipe for a parametric 3D-printable storage box with a separate lift-off lid.

**Details:**

Parameters to define up front:
- `box_length`, `box_width`, `box_height` (outer dimensions)
- `wall_thickness` (walls and floor)
- `lid_height` (total lid thickness)
- `lid_lip_depth` (how deep the lip inserts into the box)
- `lid_clearance` (gap between lip and box inner wall, 0.2mm works well)
- `fillet_radius` (corner rounding)

**Box (component: "Storage Box"):**
1. Sketch outer rectangle on XY, centered on origin
2. Extrude up by `box_height`
3. Fillet the 4 vertical corner edges by `fillet_radius`
4. Shell: remove top face, `insideThickness = wall_thickness`

**Lid (component: "Box Lid"):**
1. Sketch outer rectangle on XY (same size as box)
2. Extrude up by `lid_height`
3. Fillet the 4 vertical corner edges by `fillet_radius`
4. Sketch ring on XY plane (outer = lid outer, inner = box interior minus `lid_clearance`)
5. Extrude-cut the ring upward by `lid_lip_depth` (creates the recessed lip)
6. Optional: fillet top edges ~1mm for nice touch feel

**Key:** Fillet corners BEFORE shell on the box. Use XY plane sketches for cuts, not face sketches.

**Why it matters:** This is a common starting point for enclosures, organizers, and gift boxes. Having the recipe avoids the shell/fillet ordering trap and face-sketch direction issues.
