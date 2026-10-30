# HDL Runtime Parameters

Automatic calculation and updating of shared instance parameters in Autodesk Revit using configurable Python services and Revit `IUpdater`.

**Version: 1.0** · Author: Dmytro Havrikov · Delivery: pyRevit extension

## Concept

A shared parameter normally stores a value. HDL Runtime Parameters connects that value to a calculation service and updates it when a configured instance is added or its geometry changes.

The computed result remains a shared parameter value, available to Revit tags, schedules, filters and downstream workflows. This gives shared parameters calculated behavior similar to selected system parameters, without converting them into native system parameters.

The runtime mechanism is independent of the calculation itself. JSON defines target parameters and applicable families/categories; Python services define how values are calculated.

## Included capability

- Revit `IUpdater` registration for individual project documents.
- Element-addition and geometry-change triggers in the relevant categories.
- Exact family/category name filtering before calculation.
- Shared-parameter lookup and identity validation by GUID.
- Plug-in Python services exposing `calculate(doc, element, parameters)`.
- Double, Integer and String result writing, skipping missing/read-only parameters, `None` results and unchanged values.
- Updates within the transaction that triggered the updater, without a separate runtime transaction or Idling queue.
- Cached JSON configuration and service loading from external Python files.

The supplied calculation service is **Absolute Elevation**:

```text
SP_BOM_Absolute_Elevation = Level.Elevation + INSTANCE_ELEVATION_PARAM
```

This formula uses the level's API elevation and the instance's elevation-from-level parameter. It does not perform an explicit survey/shared-coordinate transformation. Confirm that its coordinate convention matches your project's elevation requirements.

**Opening Size is not included in this source package.** A shape-dependent size service can use the same interface, but the corresponding implementation was not part of the supplied v1.0 archive.

## Download and installation

1. [Download the original v1.0 extension ZIP](https://github.com/havrikov-bim/HDL-RuntimeParameters/raw/refs/heads/main/downloads/HDL_RuntimeParameterUpdater_IUpdater_Clean_v1.0.zip), or use **Code → Download ZIP** for source and documentation.
2. Remove the previous `HDL_RuntimeParameterUpdater.extension` if installed. Do not merge this package with an earlier DocumentChanged/Idling-based version or keep duplicate runtime updaters active.
3. Extract `HDL_RuntimeParameterUpdater_IUpdater_Clean_v1.0.extension` into your pyRevit extensions directory, normally `%APPDATA%\pyRevit\Extensions`.
4. Edit `config/parameters.json` inside the extension. Replace the placeholder GUID with the actual shared parameter GUID and enter exact family names or category names.
5. Make sure the shared instance parameter already exists and can be written through the API. This extension does not create or bind parameters.
6. Reload pyRevit once. Open or activate the target project to register its updater.
7. Add or move a configured instance, inspect the computed value, then check Undo/Redo in the target Revit session.

The distributed configuration intentionally contains placeholders. It must be customized before the example service can update project data. There is no ribbon command or initial full-model recalculation in this package.

Requires Autodesk Revit and pyRevit. The implementation uses IronPython-era APIs (`imp`, `ElementId.IntegerValue`); a supported Revit/pyRevit version matrix has not yet been established.

## Configuration example

```json
{
  "version": 1,
  "services": [
    {
      "service": "absolute_elevation.py",
      "parameters": [
        {
          "name": "SP_BOM_Absolute_Elevation",
          "guid": "REPLACE-WITH-ACTUAL-SHARED-PARAMETER-GUID"
        }
      ],
      "scope": {
        "categories": [],
        "families": ["BL Opening Rect Wall", "BL Opening Round Wall"]
      },
      "enabled": true
    }
  ]
}
```

Use real GUIDs and the names loaded in your project. Parameter names identify calculation outputs inside the service; the updater resolves and verifies target shared parameters by GUID.

Family and category selectors use **OR** semantics: either a matching family or a matching category makes the rule applicable. Adding a category therefore broadens scope to that category, rather than restricting the listed families. Name comparisons are exact and category names depend on the Revit language.

## How it works

1. Startup, document-open and view-activation hooks register or refresh the document's updater. The hooks themselves do not modify model data.
2. Revit calls the updater when an element is added or its geometry changes in a registered category.
3. The updater checks each added/modified element against enabled rules, resolves its shared parameters and loads the relevant calculation service.
4. The service returns a dictionary mapping parameter GUID strings to calculated values.
5. Changed writable values are set within the triggering transaction. Double values use a comparison tolerance of `1e-9` in their stored units.

See [Architecture and limitations](docs/ARCHITECTURE.md) and [Writing calculation services](docs/SERVICES.md).

## Current limitations

- Existing elements are not automatically recalculated when the extension is installed or a document is opened. An applicable addition/geometry change is needed.
- Parameter-only changes that do not affect geometry are not explicitly registered as triggers.
- Changes to levels, project location or other dependent elements do not have a dedicated dependency mechanism to refresh every affected instance.
- No expression parser, formula editor, dependency graph, cycle detection, unit conversion layer or read-only protection for calculated values is included.
- Calculation failures are generally skipped without a diagnostic report. Malformed configuration is not handled by a comprehensive validation layer.
- Service files are executable Python code. Use services you trust and keep their calculations predictable.

## Validation

Repository preparation checks Python syntax, JSON readability and byte-for-byte preservation of the supplied extension. Revit is unavailable in the preparation environment. Actual updater registration, trigger behavior, parameter writes, performance and Undo/Redo require verification in Revit. No automated Revit runtime test suite is included.

Report reproducible behavior in [Issues](https://github.com/havrikov-bim/HDL-RuntimeParameters/issues), including Revit/pyRevit versions, sanitized configuration, affected family and the steps that should trigger an update.
