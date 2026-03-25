# Fusion 360 API - Reference Manual Overview

> Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ReferenceManual_UM.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## API Namespaces

The Fusion 360 API is organized into three main namespaces (Python modules):

| Module | Import | Purpose |
|--------|--------|---------|
| `adsk.core` | `import adsk.core` | Core functionality: Application, UI, geometry, events, materials |
| `adsk.fusion` | `import adsk.fusion` | Design functionality: components, features, sketches, BRep |
| `adsk.cam` | `import adsk.cam` | CAM/Manufacturing: setups, operations, toolpaths, post-processing |

### Standard Import Pattern

```python
import adsk.core, adsk.fusion, adsk.cam, traceback
```

## User's Manual Topics Index

### Core Topics
- Basic Concepts of Fusion's API (`BasicConcepts_UM.htm`)
- Creating Scripts and Add-Ins (`WritingDebugging_UM.htm`)
- Python Specific Issues (`PythonSpecific_UM.htm`)
- Python Add-in Template (`PythonTemplate_UM.htm`)
- Units in Fusion (`Units_UM.htm`)
- Document and Assembly Structure (`ComponentsProxies_UM.htm`)
- Fusion Solids and Surfaces (`BRepGeometry_UM.htm`)
- Programming for Design Intent (`DesignIntent_UM.htm`)
- Custom Features (`CustomFeatures_UM.htm`)

### User Interface Topics
- User-Interface Customization (`UserInterface_UM.htm`)
- Commands (`Commands_UM.htm`)
- Command Inputs (`CommandInputs_UM.htm`)
- Palettes and Browser Command Inputs (`Palettes_UM.htm`)
- Events (`Events_UM.htm`)
- Attributes (`Attributes_UM.htm`)
- Custom Graphics (`CustomGraphics_UM.htm`)
- Canvases (`Canvases_UM.htm`)
- Configurations (`Configurations_UM.htm`)

### Manufacturing API (CAM)
- Introduction to the CAM API (`CAMIntroduction_UM.htm`)
- CAM Parameters (`CAMParameters_UM.htm`)
- CAM Libraries (`CAMLibraries_UM.htm`)
- Feature Recognition (`FeatureRecognition_UM.htm`)
- Document Properties and MFGDM API (`MFGDMAPI_UM.htm`)

### Special Topics
- Opening Files from a Web Page (`OpeningFilesFromWebPage_UM.htm`)
- Working in a Separate Thread (`Threading_UM.htm`)
- Selection Filters (`SelectionFilters_UM.htm`)

## Key Objects Quick Reference

### adsk.core Namespace

| Object | Description |
|--------|-------------|
| `Application` | Top-level object representing the Fusion application |
| `UserInterface` | Access to UI: message boxes, selections, toolbars |
| `Document` | Represents a Fusion document (file) |
| `Point3D` | 3D point with x, y, z coordinates |
| `Vector3D` | 3D vector for directions |
| `Matrix3D` | 4x4 transformation matrix |
| `ValueInput` | Parametric value input for features |
| `ObjectCollection` | General-purpose collection |
| `Color` | RGBA color |
| `CustomEvent` | Custom event for threading |
| `CommandDefinition` | Definition for UI commands |

### adsk.fusion Namespace

| Object | Description |
|--------|-------------|
| `Design` | Represents the design product |
| `Component` | Contains geometry, features, parameters |
| `Occurrence` | Instance of a component in assembly |
| `Sketch` | 2D sketch on a plane or face |
| `Profile` | Closed region in a sketch |
| `ExtrudeFeature` | Extrusion feature |
| `RevolveFeature` | Revolution feature |
| `BRepBody` | Boundary-representation solid/surface body |
| `BRepFace` | Face on a body |
| `BRepEdge` | Edge on a body |
| `UserParameter` | User-defined parameter |
| `ModelParameter` | Feature-driven parameter |
| `ExportManager` | File export operations |
| `Timeline` | Design history timeline |
| `Joint` | Assembly joint/constraint |

### adsk.cam Namespace

| Object | Description |
|--------|-------------|
| `CAM` | Top-level CAM product |
| `Setup` | Manufacturing setup with coordinate system |
| `Operation` | Machining operation (toolpath) |
| `PostProcessInput` | NC file generation settings |
| `GenerateToolpathFuture` | Async toolpath generation handle |

## API Documentation URL Pattern

Individual object pages follow this pattern:
```
https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/{ObjectName}.htm
```

For example:
- Component: `https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Component.htm`
- ExtrudeFeature: `https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExtrudeFeature.htm`

## What's New (January 2026)

- **Python 3.14** upgrade (was 3.12)
- **Design Intent**: Three types - hybrid, part, assembly
- **Derive Feature API**: Create, query, edit derive features
- **Sketch Auto Constraint**: `autoConstrain()` method
- **New method**: `SketchLines.addByMidpoint()`
- **New method**: `Occurrences.addNewExternalComponent()`
- **UI Themes**: Only light gray and dark blue supported
