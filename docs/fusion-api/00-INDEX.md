# Fusion 360 API Documentation Package - Index

> Compiled for building a custom MCP (Model Context Protocol) server that controls Autodesk Fusion 360 via its Python API.
>
> Generated: 2026-03-09

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

## Reading Order for MCP Server Development

1. **01-basic-concepts.md** - Understand the object model
2. **02-python-specifics.md** - Python threading constraints and patterns
3. **03-custom-event-threading.md** - THE bridge pattern (background thread <-> main thread)
4. **04-fire-custom-event-api.md** - The key API method
5. **05-creating-addins.md** + **06-addin-template.md** - How the add-in will be structured
6. **15-events-and-commands.md** - Event system deep dive
7. Then reference specific API docs (08-14, 16) as needed for implementing commands

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
