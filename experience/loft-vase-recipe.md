---
name: Modern vase via loft with organic cross-sections
type: recipe
tags: [vase, loft, shell, organic, 3d-print, parametric]
---

**What:** Step-by-step recipe for a parametric hollow vase using lofted circular cross-sections.

**Details:**

Parameters to define up front:
- `vase_height` (total height)
- `base_radius`, `waist_radius`, `mid_radius`, `rim_radius` (radii at each cross-section)
- `waist_height`, `mid_height` (Z positions of intermediate sections)
- `wall_thickness` (for shell)
- `base_thickness` (solid floor, optional)

**Steps:**
1. Create offset construction planes at each height (base uses XY plane directly)
2. Sketch a circle on each plane — verify `isConstruction = False`
3. Loft through all profiles in order (base → waist → mid → rim), `isSolid = True`
4. Shell: remove the top face, set `insideThickness = wall_thickness`
5. Fillet rim edges (~0.5mm) and base edge (~1mm) for a polished finish

**Tips:**
- 4 cross-sections gives a nice organic S-curve. Add more for finer control.
- The waist radius should be significantly smaller than base and mid for dramatic shape.
- Shell AFTER loft — shelling preserves the outer loft surface and hollows inward.
- Top face for shell is found by matching `boundingBox.minPoint.z` to `vase_height`.

**Why it matters:** Lofts are the go-to for organic/curved shapes. This recipe avoids the revolve approach (which only produces rotationally symmetric profiles from a single sketch) and gives more control over the silhouette at each height.
