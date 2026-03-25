# Fusion 360 API - GitHub Repositories and Sample Code

## Official Autodesk Organization

**GitHub Organization:** [AutodeskFusion360](https://github.com/AutodeskFusion360)

The official repository hosts documentation and source code for the Fusion Client API, Design Automation samples, and various utility add-ins.

### Key Official Repositories

| Repository | Description |
|-----------|-------------|
| [ParameterIO_Python](https://github.com/AutodeskFusion360/ParameterIO_Python) | Add-in to read/write parameters from CSV files |
| Fusion360DevTools | Developer utilities for add-in development |
| SketchChecker_Python | Validates active sketch for open curves |

## Community Repositories

### tapnair (Patrick Rainsberry) - Most Popular

Patrick Rainsberry (Autodesk employee) maintains the most comprehensive community libraries:

| Repository | Description | URL |
|-----------|-------------|-----|
| Fusion360Utilities | Utility library simplifying add-in development | https://github.com/tapnair/Fusion360Utilities |
| Fusion360AddinSkeleton | Framework/template for creating add-ins | https://github.com/tapnair/Fusion360AddinSkeleton |
| AppearanceUtility | Simplified appearance/material handling | https://github.com/tapnair/AppearanceUtility |
| FusionMesher | Mesh utilities | https://github.com/tapnair/FusionMesher |
| FusionSheeter | Google Sheets connector for Fusion 360 | https://github.com/tapnair/FusionSheeter |
| FusionPlayer | Custom timeline playback | https://github.com/tapnair/FusionPlayer |

### Other Notable Projects

| Repository | Description | URL |
|-----------|-------------|-----|
| fusion2urdf | Export Fusion 360 designs to URDF (robot description) | https://github.com/syuntoku14/fusion2urdf |
| Fusion360_Python | Collection of Fusion 360 Python scripts | https://github.com/AmieDD/Fusion360_Python |
| fusion360-thomasa88lib | Helper library for scripts/add-ins | https://github.com/thomasa88/fusion360-thomasa88lib |
| Fusion-360-API | Various API scripts | https://github.com/baltgabo/Fusion-360-API |

## GitHub Topics for Discovery

- [fusion-360-api](https://github.com/topics/fusion-360-api) - Main topic tag
- [fusion360](https://github.com/topics/fusion360?l=python&o=desc&s=updated) - Python, sorted by updated
- [fusion-360](https://github.com/topics/fusion-360?l=python) - Python projects

## Fusion360AddinSkeleton (Framework)

The `Fusion360AddinSkeleton` project by tapnair provides a more advanced version of the official template with:

- Base command class with event handling pre-wired
- Simplified input creation
- Utility functions for common operations
- Template for multi-command add-ins

### Key File: Fusion360CommandBase.py

This provides a base class that wraps all the event handler boilerplate:

```python
class Fusion360CommandBase:
    """Base class for Fusion 360 commands with event handling."""

    def on_create(self, command, inputs):
        """Override to define command inputs."""
        pass

    def on_execute(self, command, inputs, args):
        """Override to implement command logic."""
        pass

    def on_preview(self, command, inputs, args):
        """Override for preview."""
        pass

    def on_input_changed(self, command, inputs, changed_input):
        """Override for input change handling."""
        pass

    def on_destroy(self, command, inputs, reason):
        """Override for cleanup."""
        pass
```

## Built-in Samples (Shipped with Fusion)

Fusion 360 includes sample scripts accessible via the Scripts and Add-Ins dialog. Key samples:

| Sample | Demonstrates |
|--------|-------------|
| CreateSketchLines | Line and rectangle creation |
| ExtrudeFeatureSample | All extrusion types |
| CustomEventSample | Background thread communication |
| AssemblyTraversal | Recursive assembly tree walking |
| ExportToOtherFormats | Multi-format export |
| MaterialSample | Material and appearance manipulation |
| STLExport | STL export with options |
| SetParametersFromCSV | Parameter-driven design |
| CustomGraphics | Custom visualization |
| UICustomization | Toolbar/panel/button creation |

### Accessing Built-in Samples

1. Open Scripts and Add-Ins dialog
2. Look under "Samples" section (or access via GitHub link in documentation)
3. Samples are also available at: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UsingSamplesFromGitHub_UM.htm

## MCP-Relevant Patterns from Community

### Socket-Based Communication (Pattern for MCP)

Several community projects implement socket-based communication with Fusion 360, similar to what an MCP server would need:

1. **Add-in registers custom event** on startup
2. **Background thread opens socket/pipe** and listens for commands
3. **Incoming commands** are forwarded via `fireCustomEvent()`
4. **Event handler** executes Fusion API calls on main thread
5. **Results** are sent back through the socket

This is the exact pattern needed for an MCP server bridge.

### Parameter-Driven Design (Common MCP Use Case)

The ParameterIO and CSV parameter samples show how to:
- Read parameter values from external sources
- Update design parameters programmatically
- Export modified designs
- This maps directly to MCP "modify design" commands

### Assembly Manipulation (Common MCP Use Case)

Community projects demonstrate:
- Creating/positioning occurrences programmatically
- Modifying transforms for assembly arrangement
- Reading assembly structure for status queries
- These map to MCP "query/modify assembly" commands
