# Fusion MCP Bridge — Testing Guide

> A progressive set of exercises to test the bridge, from basic connectivity through advanced modeling. Try these in order — each level builds on skills from the previous one.

---

## Before You Start

1. Make sure Fusion 360 is open with a **new, empty design**
2. The `fusion_bridge` add-in should be running (check Add-Ins dialog)
3. Claude Code should be running in the `C:\OSCAR2` directory

**Tip:** Start each test level in a fresh design so things don't get cluttered. You can always undo in Fusion with Ctrl+Z if something goes wrong.

---

## Level 1: Connectivity & Basics

These confirm the bridge is working at all.

### Test 1.1 — Ping
> "Ping Fusion"

**Expected:** You get a "pong" response. If this fails, nothing else will work — check that the add-in is running.

### Test 1.2 — Read Document Info
> "What document do I have open in Fusion? What units is it set to?"

**Expected:** Claude reads the document name and default units. This confirms the bridge can query Fusion state.

### Test 1.3 — Pin the Document
> "Pin this document so we don't lose it if I switch tabs"

**Expected:** Claude calls `fusion_pin` and confirms which document is pinned. Test it by switching to a different tab in Fusion, then asking Claude to check the pin status.

---

## Level 2: Simple Geometry

Basic shapes to confirm sketching and features work.

### Test 2.1 — Box
> "Create a 50mm x 30mm x 20mm box at the origin"

**What to check:**
- Box appears centered at origin
- Dimensions are correct (use Fusion's Inspect > Measure tool)
- Body has a meaningful name (not "Body1")
- A user parameter or two should exist in Modify > Change Parameters

### Test 2.2 — Cylinder
> "Add a cylinder next to the box — 25mm diameter, 40mm tall, centered at (60, 0, 0)"

**What to check:**
- Cylinder is separate from the box (its own body)
- Position is correct (not overlapping the box)
- Named something intuitive like "Cylinder 1"

### Test 2.3 — Sphere
> "Create a 30mm diameter sphere at the origin of a new component called 'Ball Joint'"

**What to check:**
- New component appears in the browser tree
- Sphere is inside that component
- Named descriptively

---

## Level 3: Modifications & Features

Adding detail to existing geometry.

### Test 3.1 — Fillets
> "Add 3mm fillets to all edges of the box"

**What to check:**
- All 12 edges are filleted
- Radius looks correct
- Feature appears in timeline as something like "Edge Fillet 3mm"

### Test 3.2 — Holes
> "Put a 5mm through-hole in the center of the top face of the box"

**What to check:**
- Hole goes all the way through
- Centered on the top face
- Named meaningfully

### Test 3.3 — Shell
> "Shell the box to 2mm wall thickness, removing the top face"

**What to check:**
- Box becomes hollow
- Walls are 2mm thick (measure with Inspect)
- Top is open

### Test 3.4 — Chamfer
> "Add a 1mm chamfer to the top edges of the cylinder"

**What to check:**
- Only the top circular edge is chamfered
- Size looks right

---

## Level 4: Parametric Design

Testing that the design is truly parametric and adjustable.

### Test 4.1 — Check Parameters
> "Show me all the user parameters in this design"

**Expected:** Claude reads back the parameter table with meaningful names like `box_length`, `box_width`, etc.

### Test 4.2 — Change a Parameter
> "Change the box height to 40mm"

**What to check:**
- The box updates in the viewport
- The hole and fillet features survive the change (no errors in timeline)
- The parameter value updates in Modify > Change Parameters

### Test 4.3 — Expression-Driven Parameter
> "Add a parameter called 'hole_count' set to 4, then create a circular pattern of holes on the top face of the box"

**What to check:**
- `hole_count` parameter exists
- 4 holes appear in a circular pattern
- Changing `hole_count` to 6 updates the pattern

---

## Level 5: Multi-Body & Components

Testing assembly-style work.

### Test 5.1 — Lid for the Box
> "Create a lid that fits over the open top of the shelled box, with a 0.5mm clearance gap. Put it in its own component called 'Lid'."

**What to check:**
- Lid is a separate component
- It's slightly larger than the box opening (by 0.5mm per side for clearance)
- It sits on top of the box visually

### Test 5.2 — Mounting Tabs
> "Add 4 mounting tabs with screw holes to the bottom of the box, one on each side"

**What to check:**
- Tabs extend outward from the box base
- Each has a hole
- Symmetry looks right

### Test 5.3 — Mirror Feature
> "I only want to define one mounting tab and mirror it to all four sides"

**What to check:**
- Only one tab is modeled manually
- Mirror features create the rest
- Changes to the original tab propagate

---

## Level 6: Real-World Objects

These test Claude's ability to interpret vague requests and make design decisions.

### Test 6.1 — Phone Stand
> "Design a simple phone stand that holds a phone at a 60-degree angle. Make it about 80mm wide."

**What to look for:**
- Claude asks clarifying questions (phone thickness? material?)
- Design is parametric
- Angle is approximately 60 degrees
- It looks like it would actually hold a phone

### Test 6.2 — Cable Clip
> "Make a cable management clip that snaps onto a desk edge (25mm thick desk) and holds a 6mm cable"

**What to look for:**
- Two functional features: desk clamp and cable holder
- Dimensions make physical sense
- Could actually be 3D printed and used

### Test 6.3 — Enclosure
> "Design an enclosure for a Raspberry Pi 4. It should have ventilation slots and holes for all the ports."

**What to look for:**
- Approximate Pi 4 dimensions (85mm x 56mm x 17mm)
- Port cutouts on the correct sides
- Ventilation pattern
- Lid that can be removed
- This is a complex test — expect it to take multiple steps

---

## Level 7: Stress Tests

These push the limits of the bridge and Claude's modeling ability.

### Test 7.1 — Tab Switching (Pin Test)
> Start a multi-step build, then switch to a different Fusion tab mid-operation.

**Expected:** Operations continue on the pinned document, not the new tab.

### Test 7.2 — Error Recovery
> "Extrude sketch 'nonexistent_sketch' by 10mm"

**Expected:** Claude handles the error gracefully, explains what went wrong, and suggests a fix.

### Test 7.3 — Complex Sweep
> "Create a coil spring — 10mm wire diameter, 50mm coil diameter, 80mm tall, 8 turns"

**What to look for:**
- This requires a helix path and a swept circle
- Geometry is complex but should be achievable
- Named and parametric

### Test 7.4 — Undo Request
> After building something, say: "That's not what I wanted, undo the last 3 features"

**Expected:** Claude rolls back the timeline or removes the features. Should ask for confirmation first.

---

## Tips for Working with Claude + Fusion

1. **Be specific about dimensions and positions.** "Make a box" is vague. "Make a 50x30x20mm box at the origin" is clear.

2. **Say what it's for.** "I need an enclosure for electronics" gives Claude context to make better design decisions than just "make a box."

3. **Start simple, then add detail.** Get the basic shape right, then ask for fillets, holes, patterns, etc. in separate steps. This matches how parametric modeling works best.

4. **Check the timeline after each step.** The Fusion timeline (bottom of the viewport) shows every operation. If something looks wrong, you can roll back there.

5. **Use Modify > Change Parameters often.** This is where you'll see all the named parameters Claude created. Changing values here updates the whole model.

6. **Ask Claude to explain what it did.** If you're learning, say "explain what you just did in Fusion terms" — it'll break down the sketches, features, and constraints it used.

7. **Don't be afraid to say "undo that."** Claude can roll back features or start over on a step.

8. **Pin your document** before any multi-step operation. It's a good habit.

9. **One thing at a time** works better than a paragraph of instructions. Claude handles complex requests, but step-by-step gives you more control and lets you course-correct.

10. **Save your Fusion file periodically.** Git tracks the code, but your Fusion design file is separate. Use Ctrl+S or File > Save in Fusion.
