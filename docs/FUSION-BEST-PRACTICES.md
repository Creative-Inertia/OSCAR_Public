# Fusion 360 Best Practices for Claude Code / MCP

> These are baseline rules and conventions that Claude Code should follow when controlling Fusion 360 via MCP. They apply unless the user explicitly overrides them in conversation.

---

## Coordinate System & Orientation

1. **Z axis is up/down.** Fusion 360 uses Z-up orientation. When the user says "height," they mean Z.
2. **XY plane is the ground plane.** Use it for top-down layouts, floor plans, and base sketches.
3. **XZ plane is the front plane.** Use it for front-profile sketches.
4. **YZ plane is the side/right plane.** Use it for side-profile sketches.
5. **Place geometry at the origin unless told otherwise.** Center parts on (0, 0, 0) for easier assembly and symmetry.

## Units & Values

6. **Read the document's default units from UnitsManager before modeling.** Do not assume mm — the user may be working in inches, cm, or other units. Use `design.unitsManager.defaultLengthUnits` to check.
7. **The Fusion API uses centimeters internally for length.** Always convert from the user's units to cm when using `ValueInput.createByReal()`.
8. **The Fusion API uses radians internally for angles.** Accept input from the user in degrees and convert with `math.radians()`.
9. **Prefer `ValueInput.createByString()` with explicit units** (e.g., `"50 mm"`, `"2 in"`) over `createByReal()` when possible — it's self-documenting and avoids conversion bugs.
10. **Echo back dimensions in the user's units**, not internal cm/radians, when reporting what was created.

## Naming & Organization

11. **Always name bodies immediately after creation.** Use intuitive, descriptive names like "Sphere 1", "Enclosure Base", "Mounting Bracket" — never leave defaults like "Body1".
12. **Name sketches descriptively.** e.g., "Base Profile", "Hole Pattern Layout", "Lid Outline" — not "Sketch1".
13. **Name user parameters with meaningful names** in the Change Parameters dialog. Use names like `wall_thickness`, `hole_diameter`, `enclosure_height` — not `d0`, `param1`.
14. **Name features when the default isn't clear.** Rename extrusions, fillets, etc. to describe their purpose (e.g., "Base Extrude", "Corner Fillet 3mm").
15. **Name components to reflect the part they represent.** e.g., "Top Cover", "PCB Tray", "Hinge Pin".
16. **Use consistent naming conventions.** Stick to snake_case for parameters, Title Case for bodies/components/features.

## Parametric Design

17. **Always start in parametric modeling mode.** Never switch to direct modeling unless the user explicitly requests it.
18. **Define key dimensions as User Parameters up front.** This makes the design easily adjustable later.
19. **Use parameter expressions instead of hard-coded values.** e.g., set hole positions as `enclosure_length / 2` rather than `50 mm`.
20. **Add comments to user parameters** explaining what they control — the comment field exists for this purpose.
21. **Group related parameters with a naming prefix.** e.g., `lid_thickness`, `lid_width`, `lid_overlap` keeps the parameter table organized.
22. **Never delete or rename a parameter that other features reference** without updating the dependent expressions first.

## Sketching

23. **Fully constrain sketches.** Every sketch should be fully constrained (black lines, not blue) before using it in a feature. Add geometric and dimensional constraints.
24. **Use geometric constraints before dimensional constraints.** Apply coincident, horizontal, vertical, tangent, etc. first, then lock down sizes with dimensions.
25. **Sketch on the most natural plane or face.** Don't sketch on XY and then rotate — sketch directly on the face where the feature belongs.
26. **Keep sketches simple.** One sketch per feature when possible. Avoid mega-sketches that drive multiple unrelated features.
27. **Use construction lines** (set `isConstruction = True`) for reference geometry that shouldn't create profiles.
28. **Verify sketch curves are NOT construction lines before extruding/cutting.** When drawing circles or lines that will be used as profiles for features, explicitly confirm `isConstruction = False`. Construction lines (dashed) do not form cuttable profiles and will cause silent failures. Always check after creation.
29. **Close all profiles.** Open sketch curves cannot be extruded. Verify `sketch.profiles.count > 0` before attempting features.

## Features & Modeling

30. **Check feature health after creation.** Verify `feature.healthState` is `HealthyFeatureHealthState` and report any warnings/errors.
31. **Use the simplest feature that achieves the result.** Don't loft when an extrude will do. Don't sweep when a revolve works.
32. **Apply fillets and chamfers last** (or near-last) in the timeline — they are the most fragile features and depend on edges that may change.
33. **Use Join/Cut/Intersect operations intentionally.** Default to `NewBodyFeatureOperation` when creating new shapes, then combine explicitly if needed.
34. **Check visibility of all bodies/components before any feature operation.** The user may have manually hidden or shown things in Fusion. Before cutting, extruding, or combining: query `isLightBulbOn` on all bodies and occurrences. Ensure target bodies are visible (or the operation will silently skip them) and non-target bodies are hidden (or through-all cuts will damage them). Restore the user's original visibility state when done.
35. **Prefer symmetric features when the design is symmetric.** Use symmetric extrusion or mirror features instead of manually duplicating geometry.
36. **Use patterns (rectangular/circular) instead of copy-pasting geometry.** Patterns are parametric and update automatically.

## Components & Assemblies

37. **Create a new component for each distinct part** in multi-part designs. Don't model everything in the root component.
38. **Activate the correct component before adding sketches/features.** Geometry goes into the active component.
39. **Ground one component as the fixed reference** in assemblies — typically the base or frame.
40. **Use joints instead of manually positioning with transforms.** Joints express design intent and allow motion simulation.
41. **Use proxies when working across component boundaries.** Always call `createForAssemblyContext()` when referencing sub-component geometry from the root.

## Construction Geometry

42. **Create offset construction planes** for features that don't sit on the standard origin planes.
43. **Use construction axes for revolve and pattern operations** — don't rely on sketch lines when a construction axis is more semantically correct.
44. **Name construction geometry to indicate its purpose.** e.g., "Midplane for Mirror", "Hinge Axis".

## Timeline & History

45. **Respect the timeline.** Don't suppress or reorder features without the user's permission — it can break downstream dependencies.
46. **Use rollback sparingly.** When inserting features mid-timeline, always restore the marker to the end when done.
47. **Check `design.designType` before using timeline operations.** Timeline only exists in parametric mode, not direct mode.

## Materials & Appearances

48. **Apply materials for physical simulation, appearances for visuals.** They serve different purposes.
49. **Copy appearances into the design before applying.** Library appearances must be copied into the document first via `design.appearances.addByCopy()`.
50. **Apply appearance at the most specific level needed.** Body-level for single bodies, face-level for multi-material surfaces, component-level for uniform parts.

## Error Handling & Safety

51. **Verify geometry exists before operating on it.** Check that `sketch.profiles.count > 0`, `body.faces.count > 0`, etc. before passing to features.
52. **Never call Fusion API from a background thread** except `Application.fireCustomEvent()` — all other calls must happen on the main thread.
53. **Validate that referenced objects are still valid** (`obj.isValid`) before using them — features and geometry can become invalid after timeline edits.
54. **Report what was created after every operation.** Print body name, volume, bounding box, or other relevant confirmation so the user knows it worked.

## Export & Output

55. **Ask the user for export format and resolution preferences** before exporting. Don't assume STL or default mesh quality.
56. **Use binary STL over ASCII** for smaller file sizes unless the user needs human-readable output.
57. **Export individual components** when the user asks for "the lid" or "the base" — don't export the whole assembly.
58. **Include units in exported filenames** when relevant (e.g., `bracket_50mm.step`).

## Communication & UX

59. **Signal working/done state to the user.** Before multi-step operations, say "Working on [X] — hold tight..." and after, say "Done — safe to poke around." The user may click around in Fusion during operations, causing the active component to change.
60. **Re-verify the active component at the start of every code block.** Never assume the active component is still what you set it to previously. The user may have clicked on a different component between calls. Always check and re-activate explicitly.
61. **Describe what you're about to create before doing it** for complex operations. A quick "I'll create a 50mm sphere at the origin using a semicircle revolve" sets expectations.
60. **After creation, report key metrics**: body name, volume, bounding box dimensions, face/edge counts if relevant.
61. **When a feature fails, explain why and suggest alternatives.** Don't silently retry with different parameters.
62. **Confirm destructive operations before executing.** Deleting bodies, removing features, or clearing sketches should get user approval first.

## Performance

63. **Use `sketch.isComputeDeferred = True`** when adding many sketch entities, then set to `False` when done — this avoids recomputing profiles after every line.
64. **Batch related operations** rather than making many small individual calls when building complex geometry.
65. **Minimize unnecessary `adsk.doEvents()` calls.** Only use them when you need the viewport to update mid-operation.

## Document Pinning (Tab Safety)

66. **Always pin the document before starting a modeling session.** Call `fusion_pin` at the start of any multi-step operation. If the user switches tabs in Fusion while Claude is working, the pinned document will remain the target for all operations.
67. **Unpin when the session is complete** or when the user explicitly wants to switch to a different document. Call `fusion_unpin` to release the lock.
68. **Check pin status if operations seem to target the wrong file.** Call `fusion_pin_status` to confirm which document is pinned.
69. **If the pinned document is closed, the pin auto-clears.** The bridge detects this and falls back to the active document, but will report a warning.

## Document Management

70. **Save the document before and after major operations** if the user requests it. Never auto-save without asking.
71. **Check if a design already has content before starting fresh.** Ask the user whether to add to the existing design or create a new one.
72. **Use `NewComponentFeatureOperation`** when the user wants a feature isolated in its own component from the start.
