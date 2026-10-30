# HDL Runtime Parameters

**Status: In development. Core functionality is implemented; testing and further development are ongoing.**

English · [Русский](README.ru.md)

Automatic calculation and updating of shared instance parameters in Autodesk Revit using configurable Python services and Revit `IUpdater`.

**Version: 1.0** · Author: Dmytro Havrikov · Delivery: pyRevit extensions

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
- **Recalculate Parameters**: a separate ribbon command for manually recalculating configured outputs across the active project using the same services.

Two calculation services are included.

### Absolute Elevation — `absolute_elevation.py`

```text
SP_BOM_Absolute_Elevation = Level.Elevation + INSTANCE_ELEVATION_PARAM
```

This formula uses the level's API elevation and the instance's elevation-from-level parameter. It does not perform an explicit survey/shared-coordinate transformation. Confirm that its coordinate convention matches your project's elevation requirements.

### Opening Size — `op_opening_size.py`

Calculates `SP_OP_Size` as text for the four supported round/rectangular wall/floor families:

| Shape | Inputs | Output format |
| --- | --- | --- |
| Rectangular | `SP_OP_Width`, `SP_OP_Height`, `SP_OP_Description` | Description on the first line, then `width x height(H)` in centimeters |
| Round | `SP_OP_Diameter`, `SP_OP_Description` | `ødiameter" description`, with diameter in inches |

For example, a 400 × 250 mm rectangular opening described as `Opening` produces `Opening` followed by `40 x 25(H)` on a second line. A 4-inch round opening produces `ø4" Opening`. Numbers use up to two decimal places without trailing zeros.

Input lookup first checks the instance and then the family type if the named parameter is absent. The output must be a shared Text instance parameter with GUID `51c5bd0e-4839-43aa-80f8-ffe67faa1a7e`. This GUID is also fixed in the service's `TARGET_GUID`; change both the service constant and JSON if you use another parameter definition.

The included implementation recognizes the exact four family names in its `RECT_FAMILIES` and `ROUND_FAMILIES` sets. Other families or shapes need corresponding service changes.

## Download and installation

1. [Download the complete v1.0 package](https://github.com/havrikov-bim/HDL-RuntimeParameters/raw/refs/heads/main/downloads/HDL_RuntimeParameters_v1.0_complete.zip), or use **Code → Download ZIP** for source and documentation.
2. Remove the previous `HDL_RuntimeParameterUpdater.extension` if installed. Do not merge this package with an earlier DocumentChanged/Idling-based version or keep duplicate runtime updaters active.
3. Copy both `HDL_RuntimeParameterUpdater_IUpdater_Clean_v1.0.extension` and `HDL_Recalculate_Parameters.extension` into your pyRevit extensions directory, normally `%APPDATA%\pyRevit\Extensions`. Keep them as sibling folders.
4. Edit `config/parameters.json` inside the extension. Replace the Absolute Elevation placeholder GUID and family names with your project values. The Opening Size entry already lists the four supported families and its fixed output GUID.
5. Make sure the shared instance parameter already exists and can be written through the API. This extension does not create or bind parameters.
6. Reload pyRevit once. Open or activate the target project to register its updater.
7. Add or move a configured instance, inspect the computed value, then check Undo/Redo in the target Revit session.

The Absolute Elevation configuration intentionally contains placeholders and must be customized. The Opening Size configuration is supplied with its actual target GUID; the parameter and supported families must exist in the project. Opening a document does not automatically recalculate all existing values. Use **HDL → Parameters → Recalculate Parameters** for a manual refresh.

Requires Autodesk Revit and pyRevit. The supplied code uses `imp` to load Python services and `ElementId.IntegerValue` to access Revit category IDs. Compatibility with specific Revit versions and pyRevit Python engines has not yet been systematically verified.

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
          "guid": "REPLACE-WITH-SP-BOM-ABSOLUTE-ELEVATION-GUID"
        }
      ],
      "scope": {
        "categories": [],
        "families": [
          "REPLACE-WITH-FAMILY-NAME-01"
        ]
      },
      "enabled": true
    },
    {
      "service": "op_opening_size.py",
      "parameters": [
        {
          "name": "SP_OP_Size",
          "guid": "51c5bd0e-4839-43aa-80f8-ffe67faa1a7e"
        }
      ],
      "scope": {
        "categories": [],
        "families": [
          "BL Opening Rect Floor",
          "BL Opening Rect Wall",
          "BL Opening Round Floor",
          "BL Opening Round Wall"
        ]
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

## Manual recalculation

**HDL → Parameters → Recalculate Parameters** processes matching elements in the active project using the runtime extension's existing rules and services. Use it after configuration changes, for existing instances, or when a level/project-reference or description change has not triggered an instance update. It runs in one transaction and reports checked/updated elements, updated parameters and errors.

The button discovers the runtime extension in the same parent extensions directory. It does not process only the current selection or view. See [Recalculate Parameters](docs/RECALCULATE.md) for installation, scope, discovery and error-handling details.

See also [Architecture and limitations](docs/ARCHITECTURE.md) and [Writing calculation services](docs/SERVICES.md).

## Current limitations

- Existing elements are not automatically recalculated when the extension is installed or a document is opened. Use the manual command or an applicable instance addition/geometry change.
- Parameter-only changes that do not affect geometry are not explicitly registered as runtime triggers; the manual command can refresh their outputs.
- Changes to levels, project location or other dependent elements do not have dedicated runtime dependency propagation. Use the manual command where needed, retaining the coordinate convention implemented by each service.
- No expression parser, formula editor, dependency graph, cycle detection, unit conversion layer or read-only protection for calculated values is included.
- Calculation failures are generally skipped without a diagnostic report. Malformed configuration is not handled by a comprehensive validation layer.
- Service files are executable Python code. Use services you trust and keep their calculations predictable.

## Validation

Repository preparation checks Python syntax, JSON readability and preservation of the supplied Python source files, including the manual command. Opening Size calculation tests check formatting, units, type fallback, missing inputs and target GUID matching with Revit API substitutes. Run `python -m unittest discover -s tests -v` from the repository root. Revit is unavailable in the preparation environment. Actual updater registration, trigger behavior, parameter writes, performance and Undo/Redo require verification in Revit. No automated Revit runtime test suite is included.

Report reproducible behavior in [Issues](https://github.com/havrikov-bim/HDL-RuntimeParameters/issues), including Revit/pyRevit versions, sanitized configuration, affected family and the steps that should trigger an update.
