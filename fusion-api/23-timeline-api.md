# Fusion 360 API - Timeline API Reference

> Sources:
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Timeline.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TimelineObject.htm
> - https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TimelineGroup.htm
>
> ⚠️ **Sourcing:** This file contains ONLY information from official Autodesk documentation. Do not supplement with external sources or inferred API patterns. See [00-INDEX.md](00-INDEX.md) for full sourcing rules.

## Timeline Overview

The Timeline tracks the ordered history of modeling operations in a parametric design. Every sketch, feature, component insertion, and construction element appears as an entry in the timeline. The timeline enables rollback, reordering, suppression, and grouping of features.

**Key constraint:** The timeline is only available in parametric design mode. Direct modeling designs do not have a timeline.

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)

# Timeline is only available in parametric designs
if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
    timeline = design.timeline
else:
    # DirectDesignType — no timeline available
    ui = app.userInterface
    ui.messageBox('Timeline is not available in direct modeling mode.')
```

## Timeline Object (Collection)

The `Timeline` object is accessed via `design.timeline`. It represents the full ordered collection of timeline entries.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `count` | int | The number of items (TimelineObjects) in the timeline |
| `markerPosition` | int | The current position of the rollback marker. 0 = rolled back before all features; `count` = rolled to the end (fully computed). Read/write. |
| `isValid` | bool | Indicates if this object is still valid (not been deleted or invalidated) |

### Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `item(index)` | TimelineObject | Returns the TimelineObject at the specified index (0-based) |
| `moveToEnd()` | bool | Moves the rollback marker to the end of the timeline, computing all features. Returns True on success. |

### Accessing the Timeline

```python
design = adsk.fusion.Design.cast(app.activeProduct)
timeline = design.timeline

# Number of timeline entries
count = timeline.count

# Current rollback marker position
markerPos = timeline.markerPosition

# Get a specific timeline entry
if count > 0:
    firstItem = timeline.item(0)
    lastItem = timeline.item(count - 1)
```

## TimelineObject Properties

Each entry in the timeline is a `TimelineObject`. It represents a single feature, sketch, component, or construction element.

| Property | Type | Description |
|----------|------|-------------|
| `index` | int | The zero-based position of this object in the timeline |
| `name` | str | The display name shown in the timeline (e.g., "Extrude1", "Sketch2") |
| `entity` | Base | The underlying feature, sketch, or component occurrence that this timeline entry represents. Cast to the appropriate type. |
| `isGroup` | bool | True if this timeline object is a group containing other timeline objects |
| `isSuppressed` | bool | True if the feature is suppressed. Suppressed features remain in the timeline but do not contribute to the model. |
| `isRolledBack` | bool | True if this timeline object is currently before the rollback marker position (i.e., it is not computed) |
| `isValid` | bool | Indicates if this object is still valid |
| `healthState` | FeatureHealthStates | The health state of the feature. One of: `HealthyFeatureHealthState`, `WarningFeatureHealthState`, `ErrorFeatureHealthState` |
| `errorOrWarningMessage` | str | The text of any error or warning message associated with this timeline object. Empty string if healthy. |
| `parentGroup` | TimelineGroup | The group that contains this timeline object, or None if it is not in a group |

## TimelineObject Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `rollTo(moveBefore)` | bool | Rolls the timeline marker to this object. If `moveBefore` is True, the marker is placed before this item (item is not computed). If False, the marker is placed after (item is computed). Returns True on success. |
| `moveToIndex(index)` | bool | Reorders this timeline object to the specified index. The feature must be movable to that position (dependencies must be respected). Returns True on success. |
| `deleteMe()` | bool | Deletes the feature from the timeline and the model. Returns True on success. |
| `suppress()` | bool | Suppresses the feature. The feature remains in the timeline but is removed from the model computation. Returns True on success. |
| `unsuppress()` | bool | Unsuppresses a previously suppressed feature, restoring it to the model computation. Returns True on success. |

### Rolling To a Feature

```python
timeline = design.timeline

# Roll to just before the 5th feature (feature is not computed)
item = timeline.item(4)
item.rollTo(True)

# Roll to just after the 5th feature (feature is computed)
item.rollTo(False)

# Roll back to the very beginning (before all features)
timeline.markerPosition = 0

# Roll forward to compute everything
timeline.moveToEnd()
```

### Reordering Features

```python
timeline = design.timeline

# Move the last feature to index 2
lastItem = timeline.item(timeline.count - 1)
success = lastItem.moveToIndex(2)
if not success:
    ui.messageBox('Cannot move feature to that position — dependency conflict.')
```

### Deleting a Feature

```python
timeline = design.timeline

# Delete the feature at index 3
item = timeline.item(3)
success = item.deleteMe()
if success:
    ui.messageBox('Feature deleted.')
```

## Suppressing and Unsuppressing Features

Suppression removes a feature from the model computation without deleting it from the timeline. This is useful for testing alternate configurations or temporarily disabling features.

```python
timeline = design.timeline

# Suppress a feature
item = timeline.item(5)
if not item.isSuppressed:
    item.suppress()

# Unsuppress it later
if item.isSuppressed:
    item.unsuppress()
```

### Bulk Suppress/Unsuppress Example

```python
timeline = design.timeline

# Suppress all fillet features
for i in range(timeline.count):
    item = timeline.item(i)
    entity = item.entity
    if entity and isinstance(entity, adsk.fusion.FilletFeature):
        if not item.isSuppressed:
            item.suppress()
```

## Checking Feature Health

Each timeline object reports its health state, which indicates whether the feature computed successfully, produced a warning, or failed with an error.

```python
timeline = design.timeline

for i in range(timeline.count):
    item = timeline.item(i)

    if item.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
        msg = item.errorOrWarningMessage
        ui.messageBox(f'ERROR in "{item.name}": {msg}')

    elif item.healthState == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
        msg = item.errorOrWarningMessage
        ui.messageBox(f'WARNING in "{item.name}": {msg}')

    # HealthyFeatureHealthState means no issues
```

## Iterating the Timeline

### Print All Timeline Entries

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
ui = app.userInterface

if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
    ui.messageBox('Timeline not available in direct modeling mode.')
else:
    timeline = design.timeline
    lines = []

    for i in range(timeline.count):
        item = timeline.item(i)

        # Determine health status
        if item.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
            health = 'ERROR'
        elif item.healthState == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
            health = 'WARNING'
        else:
            health = 'OK'

        # Determine suppression state
        suppressed = ' [SUPPRESSED]' if item.isSuppressed else ''

        # Determine rollback state
        rolledBack = ' [ROLLED BACK]' if item.isRolledBack else ''

        # Determine if it is a group
        group = ' [GROUP]' if item.isGroup else ''

        line = f'{i}: {item.name} — {health}{suppressed}{rolledBack}{group}'

        # Add error/warning message if present
        if item.errorOrWarningMessage:
            line += f' — {item.errorOrWarningMessage}'

        lines.append(line)

    ui.messageBox(
        f'Timeline ({timeline.count} items, marker at {timeline.markerPosition}):\n\n'
        + '\n'.join(lines)
    )
```

### Getting the Entity Behind a Timeline Entry

```python
timeline = design.timeline

for i in range(timeline.count):
    item = timeline.item(i)
    entity = item.entity

    if entity is None:
        continue

    # Check what type the entity is
    if isinstance(entity, adsk.fusion.Sketch):
        sketch = adsk.fusion.Sketch.cast(entity)
        profileCount = sketch.profiles.count
        # Work with sketch...

    elif isinstance(entity, adsk.fusion.ExtrudeFeature):
        extrude = adsk.fusion.ExtrudeFeature.cast(entity)
        # Work with extrude feature...

    elif isinstance(entity, adsk.fusion.FilletFeature):
        fillet = adsk.fusion.FilletFeature.cast(entity)
        # Work with fillet feature...

    elif isinstance(entity, adsk.fusion.Occurrence):
        occurrence = adsk.fusion.Occurrence.cast(entity)
        # Work with component occurrence...
```

## Timeline Groups

Timeline groups let you visually collapse consecutive timeline entries into a named group. Groups do not affect computation order — they are purely organizational.

### TimelineGroups Collection

Access via `timeline.timelineGroups`.

| Property/Method | Return Type | Description |
|----------------|-------------|-------------|
| `count` | int | Number of groups in the timeline |
| `item(index)` | TimelineGroup | Returns the TimelineGroup at the specified index |
| `createGroup(startIndex, endIndex)` | TimelineGroup | Creates a new group from consecutive timeline entries between startIndex and endIndex (inclusive) |

### TimelineGroup Properties

| Property | Type | Description |
|----------|------|-------------|
| `count` | int | The number of timeline objects within this group |
| `item(index)` | TimelineObject | Returns the TimelineObject at the specified index within the group |
| `name` | str | The display name of the group. Read/write. |
| `isValid` | bool | Indicates if this group is still valid |

### Creating a Group

```python
timeline = design.timeline

# Group timeline entries from index 2 through index 5 (inclusive)
groups = timeline.timelineGroups
group = groups.createGroup(2, 5)
group.name = 'Base Shape Features'
```

### Iterating Group Contents

```python
timeline = design.timeline
groups = timeline.timelineGroups

for g in range(groups.count):
    group = groups.item(g)
    lines = []
    for i in range(group.count):
        item = group.item(i)
        lines.append(f'  {item.name}')

    ui.messageBox(f'Group "{group.name}" ({group.count} items):\n' + '\n'.join(lines))
```

## Rollback Pattern

The rollback pattern is essential for inserting features at a specific point in the timeline history, or for inspecting the model state at a previous point in time.

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
timeline = design.timeline

# Save the current marker position
originalPosition = timeline.markerPosition

# Roll back to just after feature at index 3
timeline.item(3).rollTo(False)

# --- Perform operations at this rolled-back state ---
# Any new features created here will be inserted at the current marker position
rootComp = design.rootComponent
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 2.0
)
prof = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.0))
extrudes.add(extInput)

# Roll forward to the end to recompute everything
timeline.moveToEnd()
```

### Setting Marker Position Directly

```python
timeline = design.timeline

# Roll back to the very beginning (before all features)
timeline.markerPosition = 0

# Roll forward to after the 10th feature
timeline.markerPosition = 10

# Roll to the end
timeline.markerPosition = timeline.count
# Or equivalently:
timeline.moveToEnd()
```

## Design Type Check

Always verify the design type before accessing the timeline. Attempting to access the timeline on a direct modeling design will fail.

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)

if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
    timeline = design.timeline
    ui = app.userInterface
    ui.messageBox(f'Timeline has {timeline.count} entries.')
else:
    ui = app.userInterface
    ui.messageBox('This design uses direct modeling. No timeline is available.')
```

## Common Patterns

### Find a Feature by Name

```python
def findTimelineItem(timeline, name):
    """Find a timeline item by its display name. Returns None if not found."""
    for i in range(timeline.count):
        item = timeline.item(i)
        if item.name == name:
            return item
    return None

# Usage
timeline = design.timeline
item = findTimelineItem(timeline, 'Extrude1')
if item:
    entity = adsk.fusion.ExtrudeFeature.cast(item.entity)
```

### Count Errors in Timeline

```python
def countTimelineErrors(timeline):
    """Count features with errors or warnings."""
    errors = 0
    warnings = 0
    for i in range(timeline.count):
        item = timeline.item(i)
        if item.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
            errors += 1
        elif item.healthState == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
            warnings += 1
    return errors, warnings

timeline = design.timeline
errors, warnings = countTimelineErrors(timeline)
ui.messageBox(f'Timeline health: {errors} errors, {warnings} warnings out of {timeline.count} features.')
```

### Delete All Suppressed Features

```python
timeline = design.timeline

# Iterate in reverse to avoid index shifts during deletion
for i in range(timeline.count - 1, -1, -1):
    item = timeline.item(i)
    if item.isSuppressed:
        item.deleteMe()
```

## Important Notes

- **Index shifts:** When deleting or reordering timeline items, indices of subsequent items change. Always iterate in reverse when deleting multiple items.
- **Dependency constraints:** `moveToIndex()` will fail if moving a feature before one of its dependencies or after a feature that depends on it.
- **Rollback state:** Features that are rolled back (`isRolledBack == True`) are not computed and do not contribute to the current model state.
- **Groups are organizational only:** Grouping features does not change their computation order or dependencies.
- **Suppression vs. deletion:** `suppress()` keeps the feature in the timeline for later restoration; `deleteMe()` permanently removes it.
- **Direct modeling:** If `design.designType` is `DirectDesignType`, the `design.timeline` property returns None. Always check the design type first.
