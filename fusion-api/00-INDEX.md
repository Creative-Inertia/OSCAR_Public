# Fusion 360 API Documentation Package - Index

> Compiled for building a custom MCP (Model Context Protocol) server that controls Autodesk Fusion 360 via its Python API.
>
> Generated: 2026-03-09 | Updated: 2026-03-15

---

## ⚠️ SOURCING DIRECTIVE — READ THIS FIRST

**OSCAR: When working with the Fusion 360 API, use ONLY the information contained in these 36 reference files.** Do not rely on general training knowledge, external web searches, or inferred API patterns. The Fusion 360 API has many undocumented quirks and methods that appear to exist but don't — or behave differently than expected.

**Why this matters:**
- AI training data contains outdated, incomplete, or incorrect Fusion API information
- Method signatures and class names change between Fusion versions
- Some API methods documented online have been retired or renamed
- Guessing at API calls leads to silent failures or crashes inside Fusion

**Rules for OSCAR:**
1. If a method, class, or pattern is NOT documented in files 01–36 below, **do not assume it exists**
2. If you are unsure whether an API call is valid, **say so** — do not guess
3. Files 01-25: verified against official Autodesk documentation. Files 26-36: generated via live API introspection (2026-03-20)
4. Source URLs are provided in each file header for traceability

---

## Documentation Files

| # | File | Description |
|---|------|-------------|
| 01 | [01-basic-concepts.md](01-basic-concepts.md) | **START HERE** - Object model hierarchy (Application > Document > Design > Component), collections, input objects, ValueInput, FeatureOperations enum, and the core traversal pattern |
| 02 | [02-python-specifics.md](02-python-specifics.md) | Python-specific patterns: threading constraints, `adsk.doEvents()`, return value tuples for out params, type checking/casting, module bundling, event handler GC rules |
| 03 | [03-custom-event-threading.md](03-custom-event-threading.md) | **CRITICAL FOR MCP** - Complete working code for background thread to main thread communication via custom events. This IS the pattern for MCP-to-Fusion bridging. Includes bidirectional communication pattern. |
| 04 | [04-fire-custom-event-api.md](04-fire-custom-event-api.md) | `Application.fireCustomEvent()` method reference - the ONLY Fusion API call safe from background threads. Signature, parameters, queueing behavior. |
| 05 | [05-creating-addins.md](05-creating-addins.md) | How to create/install scripts and add-ins: file structure, manifest format, installation locations (macOS/Windows), script vs. add-in differences |
| 06 | [06-addin-template.md](06-addin-template.md) | Modern add-in template architecture: run/stop lifecycle, modular command system, config.py, fusion360utils library, adding new commands, workspace/panel IDs |
| 07 | [07-api-reference-overview.md](07-api-reference-overview.md) | API namespace organization (adsk.core, adsk.fusion, adsk.cam), full user manual topic index, key objects quick reference, what's new in Jan 2026 |
| 08 | [08-sketch-api.md](08-sketch-api.md) | Sketch API: creating sketches on planes/faces, drawing lines/circles/arcs/splines/rectangles, geometric constraints (horizontal, vertical, tangent, etc.), dimensional constraints, profiles |
| 09 | [09-extrude-api.md](09-extrude-api.md) | Extrude feature API: addSimple, all 6 extent types (distance, from-entity, to-entity, through-all, symmetric, two-sided), taper angles, editing existing extrusions, health checks |
| 10 | [10-component-assembly-api.md](10-component-assembly-api.md) | Components, Occurrences, and Assemblies: creating/duplicating components, positioning via transforms, proxy objects for assembly context, recursive traversal, design types |
| 11 | [11-parameter-api.md](11-parameter-api.md) | Parameter API: UserParameters (create/read/modify/delete), ModelParameters, expressions, units, UnitsManager, CSV-driven parametric export example |
| 12 | [12-export-import-api.md](12-export-import-api.md) | Export/Import: ExportManager for STEP/IGES/SAT/SMT/F3D/STL/USD, STL mesh refinement options, per-component export, file import, document creation |
| 13 | [13-cam-api.md](13-cam-api.md) | CAM/Manufacturing API: setup creation, operation strategies, toolpath generation (async), NC post-processing, setup sheets, CAM parameters, tool libraries |
| 14 | [14-material-appearance-api.md](14-material-appearance-api.md) | Materials and Appearances: loading libraries, copying appearances into design, applying to bodies/faces/occurrences, physical material properties, calculation accuracy |
| 15 | [15-events-and-commands.md](15-events-and-commands.md) | Events system and Commands: full command lifecycle, all event handlers (created/execute/preview/inputChanged/validate/destroy/select), command input types, UI customization, toolbar/panel structure, icon requirements |
| 16 | [16-brep-geometry-api.md](16-brep-geometry-api.md) | B-Rep solid/surface geometry: topology hierarchy (Body>Lump>Shell>Face>Loop>Edge>Vertex), surface/curve evaluators, parametric space, geometry types, mesh representation, ray/point queries |
| 17 | [17-github-samples.md](17-github-samples.md) | GitHub repositories: official AutodeskFusion360 org, community libraries (tapnair/Fusion360Utilities, Fusion360AddinSkeleton), built-in samples list, MCP-relevant patterns |
| 18 | [18-fillet-chamfer-api.md](18-fillet-chamfer-api.md) | Fillet & Chamfer features: FilletFeatures, ChamferFeatures, edge set types (constant/variable/chord), chamfer type definitions (equal/two-distance/distance-angle), editing existing fillets/chamfers |
| 19 | [19-loft-sweep-api.md](19-loft-sweep-api.md) | Loft & Sweep features: LoftFeatures with sections/rails/end conditions, SweepFeatures with path/orientation/taper, guide rails, all LoftEndCondition types |
| 20 | [20-shell-mirror-pattern-api.md](20-shell-mirror-pattern-api.md) | Shell, Mirror & Pattern features: ShellFeatures, MirrorFeatures, RectangularPatternFeatures, CircularPatternFeatures, PatternComputeOptions |
| 21 | [21-construction-geometry-api.md](21-construction-geometry-api.md) | Construction geometry: ConstructionPlanes (offset/angle/midplane/3-point), ConstructionAxes (line/2-plane/2-point/circular face), ConstructionPoints (point/center/edge-plane/3-plane) |
| 22 | [22-joint-assembly-api.md](22-joint-assembly-api.md) | Joints & Assembly motion: JointOrigins, Joints (all 7 motion types), JointLimits, AsBuiltJoints, driving joint motion programmatically |
| 23 | [23-timeline-api.md](23-timeline-api.md) | Timeline API: TimelineObject traversal, health states, rollback pattern, suppress/unsuppress, TimelineGroups, reordering features |
| 24 | [24-surface-modeling-api.md](24-surface-modeling-api.md) | **Surface modeling**: Patch, Trim, Stitch, Unstitch, Extend, Thicken, OffsetFaces, ReplaceFace, ReverseNormal, RuledSurface, BoundaryFill, SurfaceDeleteFace — plus surface→solid workflows |
| 25 | [25-combine-revolve-hole-api.md](25-combine-revolve-hole-api.md) | Combine (boolean ops on existing bodies: join/cut/intersect), Revolve (full/angle/symmetric/two-side), Hole (simple/counterbore/countersink, position definitions, tapped holes) |
| 26 | [26-splitbody-splitface-api.md](26-splitbody-splitface-api.md) | SplitBody, SplitFace, SilhouetteSplit: splitting bodies/faces with planes, surfaces, or silhouette projections. Essential for sculpt-then-split workflows |
| 27 | [27-move-scale-copy-remove-api.md](27-move-scale-copy-remove-api.md) | Move (6 definition types), Scale (uniform/non-uniform), CopyPasteBody, RemoveFeature, DeleteFaceFeature |
| 28 | [28-thread-api.md](28-thread-api.md) | Thread features: ThreadDataQuery for looking up thread standards, ThreadInfo creation, cosmetic vs modeled threads, full/partial threading |
| 29 | [29-emboss-draft-api.md](29-emboss-draft-api.md) | Emboss (text/profiles onto curved surfaces) and Draft (taper angles for manufacturing) |
| 30 | [30-pipe-pathpattern-api.md](30-pipe-pathpattern-api.md) | Pipe (tube along path — replaces sketch+sweep), PathPattern (repeat along arbitrary curves) |
| 31 | [31-basefeature-form-api.md](31-basefeature-form-api.md) | BaseFeature (bridge TemporaryBRepManager/direct edits into parametric timeline), FormFeature (T-Spline sculpting — limited API) |
| 32 | [32-canvas-decal-snapshot-api.md](32-canvas-decal-snapshot-api.md) | Canvas (reference images for tracing), Decal (images on surfaces), Snapshot (joint position capture), MeasureManager |
| 33 | [33-mesh-operations-api.md](33-mesh-operations-api.md) | All 13 mesh features: Convert, Repair, Reduce, Remesh, Smooth, Shell, PlaneCut, Combine, Separate, Remove, ReverseNormal, GenerateFaceGroups, CombineFaceGroups |
| 34 | [34-boss-arrange-derive-boundaryfill-api.md](34-boss-arrange-derive-boundaryfill-api.md) | Boss (screw bosses for plastic parts), Arrange (auto-nesting), Derive (linked import), BoundaryFill (solid from intersecting surfaces) |
| 35 | [35-offset-tessellate-mergeface-api.md](35-offset-tessellate-mergeface-api.md) | OffsetFeature (new body from face offset), Tessellate (BRep→mesh), MergeFaces, CustomFeature, VolumetricModelToMesh |
| 36 | [36-readonly-features-api.md](36-readonly-features-api.md) | Read-only features (Box, Cylinder, Sphere, Torus, Coil, Rib, Web, RuleFillet, Sheet Metal) — cannot create via API, with documented alternatives |

## Reading Order for MCP Server Development

1. **01-basic-concepts.md** - Understand the object model
2. **02-python-specifics.md** - Python threading constraints and patterns
3. **03-custom-event-threading.md** - THE bridge pattern (background thread <-> main thread)
4. **04-fire-custom-event-api.md** - The key API method
5. **05-creating-addins.md** + **06-addin-template.md** - How the add-in will be structured
6. **15-events-and-commands.md** - Event system deep dive
7. Then reference specific API docs (08-14, 16, 18-36) as needed for implementing commands

## Reading Order for Design Work

When OSCAR is designing models, read docs in this order based on what the task requires:
1. **08** (Sketch) + **09** (Extrude) + **25** (Revolve/Hole) — Basic geometry creation
2. **19** (Loft/Sweep) + **30** (Pipe/PathPattern) — Path-based and multi-section geometry
3. **18** (Fillet/Chamfer) + **20** (Shell/Mirror/Pattern) + **29** (Emboss/Draft) — Finishing features
4. **26** (SplitBody/SplitFace) + **27** (Move/Scale/Copy) — Body manipulation
5. **31** (BaseFeature/Form) + **28** (Thread) — Advanced features
6. **22** (Joints) + **32** (Canvas/Decal/Snapshot) — Assembly and visual
7. **14** (Materials) + **33** (Mesh Ops) — Materials and mesh workflows
8. **34** (Boss/Arrange/Derive) + **35** (Offset/Tessellate) + **36** (Read-only reference) — Specialized

## Key Architecture Decision for MCP Server

The MCP server MUST be structured as a Fusion 360 **add-in** (not a script) because:
- Add-ins persist across sessions (run/stop lifecycle)
- Add-ins can register background threads that survive
- Add-ins can register custom events for thread communication

The recommended architecture:

```
┌──────────────────────────────────────────────┐
│  Fusion 360 Add-In                           │
│                                              │
│  run() →                                     │
│    1. Register custom event                  │
│    2. Start MCP server on background thread  │
│                                              │
│  Background Thread (MCP Server):             │
│    - Listen for MCP protocol messages        │
│    - Parse commands                          │
│    - fireCustomEvent() with command JSON     │
│    - Wait for response on queue/event        │
│                                              │
│  Main Thread (Custom Event Handler):         │
│    - Receive command from event              │
│    - Execute Fusion API calls                │
│    - Put response on shared queue            │
│                                              │
│  stop() →                                    │
│    1. Signal thread to stop                  │
│    2. Unregister custom event                │
│    3. Clean up UI elements                   │
└──────────────────────────────────────────────┘
```

## Source URLs

All documentation was scraped from the official Autodesk Fusion 360 API documentation:
- Base URL: `https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/`
- Viewer URL: `https://help.autodesk.com/view/fusion360/ENU/`
- GitHub: `https://github.com/AutodeskFusion360`
