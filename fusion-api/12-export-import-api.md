# Fusion 360 API - Export and Import API Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportToOtherFormats_Sample.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportManager_Sample.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/STLExport_Sample.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportManager_createSTEPExportOptions.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/OpeningFilesFromWebPage_UM.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Export Manager

The `ExportManager` handles all file export operations. Access it from the Design object.

```python
design = adsk.fusion.Design.cast(app.activeProduct)
exportMgr = design.exportManager
```

## Supported Export Formats

| Format | Method | Extension |
|--------|--------|-----------|
| IGES | `createIGESExportOptions(filename)` | `.igs` |
| STEP | `createSTEPExportOptions(filename)` | `.step`, `.stp` |
| SAT | `createSATExportOptions(filename)` | `.sat` |
| SMT | `createSMTExportOptions(filename)` | `.smt` |
| Fusion Archive | `createFusionArchiveExportOptions(filename)` | `.f3d` |
| STL | `createSTLExportOptions(component_or_body)` | `.stl` |
| USD | `createUSDExportOptions(filename)` | `.usd` |

## Basic Export (Entire Design)

```python
import adsk.core, adsk.fusion, traceback, tempfile

def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    exportMgr = design.exportManager
    tmpDir = tempfile.gettempdir()

    # IGES export
    igesOptions = exportMgr.createIGESExportOptions(tmpDir + '/test.igs')
    exportMgr.execute(igesOptions)

    # STEP export
    stepOptions = exportMgr.createSTEPExportOptions(tmpDir + '/test.step')
    exportMgr.execute(stepOptions)

    # SAT export
    satOptions = exportMgr.createSATExportOptions(tmpDir + '/test.sat')
    exportMgr.execute(satOptions)

    # SMT export
    smtOptions = exportMgr.createSMTExportOptions(tmpDir + '/test.smt')
    exportMgr.execute(smtOptions)

    # Fusion Archive (.f3d)
    f3dOptions = exportMgr.createFusionArchiveExportOptions(tmpDir + '/test.f3d')
    exportMgr.execute(f3dOptions)
```

## Export Individual Components

```python
design = adsk.fusion.Design.cast(app.activeProduct)
exportMgr = design.exportManager
allComps = design.allComponents

for comp in allComps:
    compName = comp.name
    fileName = f'/tmp/{compName}'

    # Export each component individually
    stpOptions = exportMgr.createSTEPExportOptions(fileName, comp)
    exportMgr.execute(stpOptions)

    igesOptions = exportMgr.createIGESExportOptions(fileName, comp)
    exportMgr.execute(igesOptions)
```

## createSTEPExportOptions - Full Signature

```python
stepOptions = exportMgr.createSTEPExportOptions(filename)
stepOptions = exportMgr.createSTEPExportOptions(filename, geometry)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | string | Output file path |
| `geometry` | Base | Optional. Component to export. Defaults to root component + all contents. |

Returns: `STEPExportOptions` object (or `None` on failure)

## STL Export

STL export has additional options for mesh quality and can export bodies, occurrences, or the root component.

```python
rootComp = design.rootComponent
exportMgr = design.exportManager

# Export root component to STL
stlOptions = exportMgr.createSTLExportOptions(rootComp)
stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
stlOptions.filename = '/tmp/output.stl'
exportMgr.execute(stlOptions)

# Export a single body
body = rootComp.bRepBodies.item(0)
stlOptions = exportMgr.createSTLExportOptions(body)
stlOptions.filename = '/tmp/body.stl'
exportMgr.execute(stlOptions)

# Export individual occurrences
for occ in rootComp.occurrences:
    stlOptions = exportMgr.createSTLExportOptions(occ)
    stlOptions.filename = f'/tmp/{occ.name}.stl'
    exportMgr.execute(stlOptions)
```

### STL Export Options

| Property | Type | Description |
|----------|------|-------------|
| `filename` | String | Output file path |
| `meshRefinement` | MeshRefinementSettings | Low, Medium, High, or Custom |
| `isBinaryFormat` | Boolean | Binary (True) or ASCII (False) |

### MeshRefinementSettings Enum

| Value | Description |
|-------|-------------|
| `MeshRefinementLow` | Coarse mesh, small file |
| `MeshRefinementMedium` | Balanced quality/size |
| `MeshRefinementHigh` | Fine mesh, larger file |
| `MeshRefinementCustom` | Custom settings |

## Send to 3D Print Utility

```python
# Get available print utilities
for printUtil in app.printUtilities:
    stlOptions = exportMgr.createSTLExportOptions(rootComp)
    stlOptions.sendToPrintUtility = True
    stlOptions.printUtility = printUtil
    exportMgr.execute(stlOptions)
```

## Importing Files

### Via Protocol Handler (External)

Fusion supports opening files via URL protocol handler:

```
fusion360://host/?command=open&file=c%3A%2Ftemp%2Fmodel.f3d
fusion360://host/?command=insert&file=c%3A%2Ftemp%2Fpart.step
```

### Supported Import Formats

| Format | Result |
|--------|--------|
| `.f3d` | Full model history copied into design |
| `.step`, `.stp` | Creates new bodies |
| `.iges`, `.igs` | Creates new bodies |
| `.sat` | Creates new bodies |
| `.smt` | Creates new bodies |
| `.stl` | Creates mesh body (direct modeling) |
| `.obj` | Creates mesh body (direct modeling) |

### Import via API

```python
# Import options
importManager = app.importManager

# STEP import
stepOptions = importManager.createSTEPImportOptions(filePath)
importManager.importToTarget(stepOptions, rootComp)

# Fusion archive import
f3dOptions = importManager.createFusionArchiveImportOptions(filePath)
importManager.importToTarget(f3dOptions, rootComp)
```

### Opening/Creating Documents

```python
# Create new design document
doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)

# Open existing document
doc = app.documents.open(filePath)
```

### DocumentTypes Enum

| Value | Description |
|-------|-------------|
| `FusionDesignDocumentType` | Fusion design document |
| `FusionDrawingDocumentType` | Fusion drawing document |

## Export All Components Example

```python
import adsk.core, adsk.fusion, traceback
import os

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    exportMgr = design.exportManager

    scriptDir = os.path.dirname(os.path.realpath(__file__))

    for comp in design.allComponents:
        compName = comp.name
        fileName = os.path.join(scriptDir, compName)

        # STEP
        stpOptions = exportMgr.createSTEPExportOptions(fileName, comp)
        exportMgr.execute(stpOptions)

        # IGES
        igesOptions = exportMgr.createIGESExportOptions(fileName, comp)
        exportMgr.execute(igesOptions)

        # F3D
        archOptions = exportMgr.createFusionArchiveExportOptions(fileName, comp)
        exportMgr.execute(archOptions)

        # USD
        usdOptions = exportMgr.createUSDExportOptions(fileName, comp)
        exportMgr.execute(usdOptions)

    ui.messageBox(f'Exported to: {scriptDir}')
```
