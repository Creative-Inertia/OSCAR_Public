# Fusion MCP Bridge — Advanced Testing Guide

> Levels 8–17: 50 exercises that continue from the base Testing Guide. These cover patterns, organic shapes, 3D-print design, functional mechanisms, text/embossing, iterative design, assemblies, and engineering challenges. Start each level in a fresh design.

---

## Level 8: Patterns & Arrays

Repeating geometry efficiently — circular, rectangular, and path-based.

### Test 8.1 — Rectangular Pattern
> "Create a 100mm x 60mm flat plate, 3mm thick. Add a grid of 3mm holes — 5 columns x 3 rows, evenly spaced with 15mm between centers."

**What to check:**
- 15 holes total in a clean grid
- Pattern feature in the timeline (not 15 individual extrudes)
- Changing the row/column count updates the pattern

### Test 8.2 — Circular Pattern
> "Add a 40mm diameter flange with a 10mm center hole. Place six 4mm bolt holes on a 30mm bolt circle, evenly spaced."

**What to check:**
- 6 holes equally spaced at 60° intervals
- Circular pattern feature used
- Changing to 8 holes updates correctly

### Test 8.3 — Pattern Along Path
> "Create an S-shaped spline on the XY plane. Place 2mm spheres every 10mm along the spline."

**What to check:**
- Spheres follow the spline path
- Spacing looks even
- Works on a curved path, not just straight lines

### Test 8.4 — Mirror with Pattern
> "Create one mounting bracket in the +X, +Y quadrant. Mirror it across the X axis, then mirror both across the Y axis — 4 brackets total from one definition."

**What to check:**
- Only one bracket is hand-modeled
- Two mirror features create the rest
- Editing the original updates all four

### Test 8.5 — Nested Pattern
> "Make a single ventilation slot (20mm x 2mm). Create a rectangular pattern of 6 rows, then circular-pattern the whole set around a center point at 90° intervals."

**What to check:**
- Pattern of patterns
- Clean intersections, no overlapping geometry errors
- Parametric — changing slot size propagates through both patterns

---

## Level 9: Advanced Sketching

Constraints, splines, projections, and construction geometry.

### Test 9.1 — Constrained Sketch
> "Create a sketch with a rectangle whose width is always twice its height. Add a circle tangent to the top edge, centered horizontally. Constrain everything — no blue (under-constrained) lines."

**What to check:**
- All sketch lines are black (fully constrained)
- Changing the height automatically updates width and circle position
- Constraints visible in the sketch palette

### Test 9.2 — Spline Profile
> "Draw an airfoil cross-section (NACA 0012 or similar) using a fitted spline. The chord length should be 100mm."

**What to check:**
- Smooth, aerodynamic shape
- Symmetric top and bottom curves
- Could be extruded or lofted into a wing

### Test 9.3 — Project and Intersect
> "Create a cylinder (30mm diameter, 50mm tall). Create a sketch on a plane that cuts through the cylinder at 45°. Project the cylinder's intersection onto that sketch."

**What to check:**
- The projected curve is an ellipse
- It can be used as a profile for further operations
- Construction plane is at the correct angle

### Test 9.4 — Offset and Shell Pattern
> "Create an organic blob shape using splines. Offset the outer curve inward by 3mm to create a wall thickness. Extrude as a hollow container."

**What to check:**
- Inner curve follows outer curve at consistent 3mm offset
- No self-intersections in the offset
- Resulting extrusion is hollow

### Test 9.5 — Sketch on Curved Face
> "Create a cylinder. Sketch a rectangle on the curved surface and extrude-cut it to create a rectangular window."

**What to check:**
- The sketch wraps onto the cylindrical face
- The cut follows the curvature
- The window edges are clean

---

## Level 10: Lofts & Organic Shapes

Creating complex surfaces by blending between profiles.

### Test 10.1 — Basic Loft
> "Create a circle on the XY plane (30mm diameter) and a square on a plane 50mm above (20mm x 20mm). Loft between them."

**What to check:**
- Smooth transition from circle to square
- Solid body, not a surface
- No twisting or self-intersection

### Test 10.2 — Multi-Section Loft
> "Create a vase shape: 60mm circle at the base, narrow to 30mm circle at 40mm height, widen to 50mm circle at 80mm height, then narrow to 35mm at 120mm. Loft through all four sections."

**What to check:**
- Smooth, vase-like profile
- No sharp transitions between sections
- Could be shelled to create an actual vase

### Test 10.3 — Loft with Guide Rail
> "Create the same circle-to-square loft from 10.1, but add a curved guide rail that makes it bulge outward on one side."

**What to check:**
- The guide rail influences the loft shape
- Asymmetric bulge visible
- Smooth surface quality

### Test 10.4 — Sculpted Handle
> "Design an ergonomic handle (like a tool grip). Use 4-5 cross sections at different heights with varying oval shapes, lofted together."

**What to check:**
- Comfortable-looking grip shape
- Smooth transitions
- Could be 3D printed and held in a hand

### Test 10.5 — Bottle Shape
> "Design a water bottle — 70mm diameter body, tapering to a 25mm threaded neck. Use loft for the taper transition."

**What to check:**
- Clean taper from body to neck
- Proportions look realistic
- Could be shelled to create hollow interior

---

## Level 11: Design for 3D Printing

Tests that focus on printability, tolerances, and manufacturing constraints.

### Test 11.1 — Wall Thickness Check
> "Create a hollow box (60x40x30mm outer, 2mm walls). Add a thin vertical divider inside — 0.4mm thick (one nozzle width). Tell me if this is printable and what the minimum wall thickness should be."

**What to check:**
- Claude identifies 0.4mm as risky (single wall, fragile)
- Recommends minimum 0.8–1.2mm for structural walls
- Explains the difference between perimeter count and wall thickness

### Test 11.2 — Overhang Analysis
> "Create a T-shaped bracket where the horizontal arm extends 30mm with no support underneath. Analyze whether this needs support material for FDM printing."

**What to check:**
- Claude identifies the 90° overhang as unprintable without supports
- Suggests alternatives: chamfer the underside to 45°, add a support rib, or split into two parts
- Demonstrates the fix

### Test 11.3 — Tolerance Fit
> "Create a box with a lid. The lid should slide on with a snug fit. What clearance do you recommend for PLA?"

**What to check:**
- Claude discusses 0.2–0.3mm clearance per side for PLA
- Lid and box dimensions account for this
- Parameters named clearly (e.g., `fit_clearance`)

### Test 11.4 — Bridge Test
> "Design a test print with bridges at 10mm, 20mm, 30mm, and 40mm spans. Each bridge should be 5mm wide and connect two towers."

**What to check:**
- Four distinct bridge spans
- Claude explains that bridges over 20–25mm may sag
- Clean geometry suitable for slicing

### Test 11.5 — Print Orientation Advice
> "Here's a hook that mounts to a wall with two screw holes, and the hook part curves downward to hold 5kg. How should I orient this for printing, and why?"

**What to check:**
- Claude considers layer adhesion direction vs load direction
- Recommends orientation where layers are NOT perpendicular to the load
- Explains that Z-axis (layer) bonds are the weakest point

---

## Level 12: Functional Mechanisms

Moving parts, snap-fits, and mechanical features.

### Test 12.1 — Snap-Fit Clip
> "Design a cantilever snap-fit clip that attaches a 3mm thick panel to a 2mm thick rail. It should click on and be removable."

**What to check:**
- Flexible cantilever arm with a hook/catch
- Deflection is reasonable for PLA (< 5% strain)
- Dimensions account for print tolerances

### Test 12.2 — Living Hinge
> "Create a box with an attached lid connected by a living hinge. The hinge should be thin enough to flex (0.3–0.5mm for PLA) and allow the lid to open 90°."

**What to check:**
- Hinge geometry is a thin, flat section between box and lid
- Claude explains material considerations (PLA vs PP for hinge life)
- The hinge doesn't create an L-shaped cross-section that would crack

### Test 12.3 — Press-Fit Pin Joint
> "Design two flat links connected by a press-fit pin. The pin should be 5mm diameter. What interference fit do you recommend?"

**What to check:**
- Pin is slightly oversized (0.1–0.2mm) relative to the hole
- Claude explains this varies by printer calibration
- Parts are designed to be printed separately and assembled

### Test 12.4 — Threaded Cap
> "Create a bottle with external M20x2 threads on the neck, and a matching cap with internal threads."

**What to check:**
- Thread profile is correct (60° V-thread or similar)
- Clearance allows the cap to screw on when printed
- Thread pitch and major diameter are parametric

### Test 12.5 — Ratchet Mechanism
> "Design a simple one-way ratchet — a gear wheel with angled teeth and a pawl that allows rotation in one direction only."

**What to check:**
- Teeth are angled correctly (easy slope one way, catch the other)
- Pawl has a spring-like cantilever or is designed to flex
- Could actually be printed and function

---

## Level 13: Text & Surface Details

Embossing, engraving, and decorative elements.

### Test 13.1 — Embossed Text
> "Create a 60x20x5mm nameplate. Emboss the text 'OSCAR2' raised 1mm from the surface, centered."

**What to check:**
- Text is legible and raised above the surface
- Centered both horizontally and vertically
- Font is clean and suitable for 3D printing

### Test 13.2 — Engraved Text
> "On the bottom of a cylindrical jar (50mm diameter), engrave 'v0.2.0' cut 0.5mm into the surface."

**What to check:**
- Text is recessed into the flat bottom face
- Legible at the small cut depth
- On the correct face (bottom, not side)

### Test 13.3 — Logo Extrusion
> "Create a simple geometric logo (overlapping circles, a star, or initials) as a sketch, then extrude it as a raised emblem on a flat plate."

**What to check:**
- Logo is clean geometry (no overlapping or broken profiles)
- Raised above the plate surface
- Could be used as a stamp or brand mark

### Test 13.4 — Surface Pattern
> "Add a diamond knurl pattern to the grip area of a cylindrical handle (20mm diameter, 40mm long grip section)."

**What to check:**
- Diamond pattern wraps around the cylinder
- Consistent depth and spacing
- Functional as a grip texture

### Test 13.5 — QR Code
> "Generate a simplified QR-code-like pattern (grid of raised/recessed squares) on a 30x30mm plate. It doesn't need to scan — just look like a QR code."

**What to check:**
- Grid of small squares, some raised, some flat
- Clean edges suitable for printing
- Demonstrates ability to create fine grid patterns

---

## Level 14: Sheet Metal & Flat Bodies

Thin-walled designs, bends, and flat patterns.

### Test 14.1 — Simple Bracket
> "Create an L-bracket from 2mm sheet metal: 40mm x 30mm base, 40mm x 25mm vertical leg, with a 3mm bend radius."

**What to check:**
- Clean bend with correct radius (not a sharp corner)
- Uniform wall thickness throughout
- Dimensions are to the outside or inside faces (clarify which)

### Test 14.2 — U-Channel
> "Create a U-channel: 50mm wide, 20mm deep, 100mm long, 1.5mm wall thickness, with 2mm bend radii."

**What to check:**
- Two parallel bends creating the U shape
- Consistent wall thickness
- Internal dimensions are correct

### Test 14.3 — Box with Tabs
> "Create an open-top box from sheet metal (60x40x25mm) with interlocking tabs on the corners for assembly."

**What to check:**
- Flat pattern could be cut from a single sheet
- Tabs interlock at corners
- Bend allowances are accounted for

### Test 14.4 — Formed Feature
> "Add a stiffening bead (embossed ridge) along the center of a 100x50mm flat plate, 1mm thick."

**What to check:**
- Raised ridge running the length of the plate
- No thinning or tearing at the formed edges
- Adds rigidity to the thin plate

### Test 14.5 — Multi-Bend Enclosure
> "Design a simple electronics enclosure from 1.5mm sheet with a removable top panel. The base has 4 bends forming a tray. Include mounting holes."

**What to check:**
- Tray shape with correct bend sequence
- Mounting holes positioned logically
- Top panel fits with appropriate clearance

---

## Level 15: Iterative Design

Modify existing designs based on feedback — tests the ability to work with existing geometry.

### Test 15.1 — Resize Proportionally
> Create a simple cup (cylinder, shelled). Then: "Make it 30% taller but keep the same proportions."

**What to check:**
- All dimensions scale together
- Wall thickness stays the same (not scaled)
- Parameters are used, not manual edits

### Test 15.2 — Add Feature to Existing
> Create a flat plate with holes. Then: "Add reinforcing ribs between each pair of holes on the underside."

**What to check:**
- Ribs connect between the correct holes
- Ribs are on the underside only
- Feature survives if hole positions change

### Test 15.3 — Change Design Intent
> Create a solid cylindrical post. Then: "Actually, make this a tube instead — 2mm wall thickness."

**What to check:**
- Claude uses Shell or modifies the sketch, not starting over
- Outer dimensions preserved
- Timeline is clean

### Test 15.4 — Fix a Broken Design
> Create a box, fillet all edges, then manually move the timeline marker back and change the box height. The fillets will break. Then: "The fillets broke after I changed the height — fix them."

**What to check:**
- Claude diagnoses the issue (fillet radius too large for new dimensions)
- Fixes by adjusting fillet radius or reapplying
- Explains why it broke

### Test 15.5 — Version a Design
> "Take this phone stand and create a 'mini' version for a tablet stylus. Same style, but 30mm wide and 15mm deep."

**What to check:**
- Proportions and style match the original
- Functional requirements still met (stability, cradle)
- Parameters adjusted, not a from-scratch rebuild

---

## Level 16: Multi-Part Assemblies

Multiple components designed to fit together.

### Test 16.1 — Box and Lid (Clearance Fit)
> "Design a rectangular box (80x50x30mm) with a separate lid that sits on top with 0.3mm clearance per side."

**What to check:**
- Two separate bodies/components
- Lid outer dimensions = box inner dimensions + clearance
- Lip or overlap to prevent the lid from sliding off

### Test 16.2 — Dowel Joint
> "Design two flat panels that connect at 90° using two 6mm dowel pins. Include the dowel holes in both panels."

**What to check:**
- Hole positions match between the two panels
- Hole depth is appropriate (half the dowel length + tolerance)
- Clearance allows assembly but keeps it snug

### Test 16.3 — Stacking System
> "Design three identical trays that stack on top of each other. Each tray should have alignment features (pins and sockets) so they don't slide."

**What to check:**
- Pins on top of each tray match sockets on the bottom
- Clearance allows easy stacking
- All three trays are identical (one design, patterned)

### Test 16.4 — Hinge Assembly
> "Design a simple door hinge with two leaves and a removable pin. All three are separate components."

**What to check:**
- Knuckles interleave correctly
- Pin fits through all knuckles
- Door leaf can rotate freely when assembled

### Test 16.5 — Modular Connector
> "Design a set of modular blocks (like simplified LEGO) — a 2x2 brick with studs on top and tubes underneath that grip the studs of the brick below."

**What to check:**
- Studs and tubes dimensioned for interference fit
- Two blocks actually connect when printed
- Tolerances specified for FDM printing

---

## Level 17: Engineering Challenges

Complex geometry, real engineering problems, multi-step solutions.

### Test 17.1 — Spur Gear
> "Create a spur gear: 20 teeth, module 2, 14.5° pressure angle, 10mm face width, 8mm bore."

**What to check:**
- Involute tooth profile (not triangles)
- Pitch diameter = module × teeth = 40mm
- Bore is centered, keyway optional
- Two meshing gears can be created and positioned

### Test 17.2 — Cam and Follower
> "Design a cam with a flat follower. The cam should produce 15mm of lift over 180° of rotation, with dwell at top and bottom."

**What to check:**
- Cam profile is smooth (no sudden jumps)
- Follower travel matches specification
- Could be animated to verify motion

### Test 17.3 — Structural Truss
> "Design a simple Warren truss bridge: 200mm long, 30mm tall, made of 3mm diameter round members."

**What to check:**
- Triangular pattern of members
- All joints connected cleanly
- Could be 3D printed as a single piece for testing

### Test 17.4 — Pipe Routing
> "Route a 10mm OD pipe from point A (0,0,0) to point B (80, 40, 60) with 90° bends and a minimum bend radius of 15mm. The pipe must avoid a 30mm cube obstacle at (40, 20, 30)."

**What to check:**
- Pipe reaches from A to B
- All bends are smooth with correct radius
- Path avoids the obstacle with clearance
- Pipe wall thickness is uniform

### Test 17.5 — Topology-Inspired Bracket
> "Design an L-bracket that supports a 50N downward load at the tip. Remove as much material as possible while maintaining structural integrity — think lightweight, organic, topology-optimized style."

**What to check:**
- Material removed from low-stress areas
- Load path is maintained (material stays along stress lines)
- Result looks organic/optimized, not just swiss-cheesed
- Claude explains the reasoning for material placement

---

## Scoring Guide

For each test, score on these criteria:

| Criteria | Points | Description |
|----------|--------|-------------|
| **Functional** | 0–3 | Does it work? Does it meet the stated requirements? |
| **Parametric** | 0–2 | Are dimensions driven by named parameters? Can they be changed? |
| **Clean Timeline** | 0–2 | Is the feature tree organized? Meaningful names? Minimal failed features? |
| **Engineering** | 0–2 | Did Claude consider physics, materials, manufacturing before modeling? |
| **Recovery** | 0–1 | If something failed, did Claude recover gracefully? |

**Total: 10 points per test, 500 points maximum across all 50 tests.**

### Rating Scale
| Score | Rating |
|-------|--------|
| 450–500 | Master — production-ready CAD agent |
| 350–449 | Advanced — handles most real-world tasks |
| 250–349 | Intermediate — solid on basics, struggles with complexity |
| 150–249 | Developing — needs guidance on multi-step tasks |
| 0–149 | Learning — stick to Levels 8–10 and build up |

---

## Tips for Advanced Testing

1. **Start each level in a fresh design.** Complex tests can leave artifacts that interfere with later tests.

2. **Run the pre-build checklist.** For Level 11+ tests, Claude should perform an engineering analysis before touching Fusion. If it doesn't, ask "what should we check before building?"

3. **Test parametric changes after each build.** The best designs survive dimension changes without breaking. Try changing a key parameter after each test.

4. **Check the timeline, not just the result.** A beautiful model with a messy timeline full of failed features and workarounds is a partial pass at best.

5. **Push back on designs.** Say "that won't work because..." or "what about the cable?" — testing Claude's ability to iterate is as important as testing first-attempt quality.

6. **Compare Level 6 and Level 16.** Both involve real-world objects, but Level 16 requires multi-part thinking, tolerances, and assembly. The gap in quality shows how much Claude has learned.

7. **Save your scores.** Track improvement across sessions. As Claude's memory accumulates lessons, scores on repeated tests should improve.
