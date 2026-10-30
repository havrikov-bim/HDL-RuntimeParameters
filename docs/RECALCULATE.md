# Recalculate Parameters

[Project overview](../README.md) · [Services](SERVICES.md) · [Architecture](ARCHITECTURE.md)

## Purpose

The separate `HDL_Recalculate_Parameters.extension` adds **HDL → Parameters → Recalculate Parameters** with an icon. It performs an explicit recalculation using the installed runtime extension's configuration and calculation services.

Use it for existing instances after installation, after changing calculation rules, or after changes to project/level/reference data that do not cause the instances' geometry-change triggers to run. It can also refresh text outputs after description changes that do not affect geometry.

The command recalculates according to each service's formula. It does not alter coordinate conventions: Absolute Elevation still uses `Level.Elevation + INSTANCE_ELEVATION_PARAM`, without an additional survey/shared-coordinate transform. A recalculation only changes the stored value if that formula produces a different result.

## Installation

1. Install and configure the runtime extension as described in the [README](../README.md).
2. Copy the entire `HDL_Recalculate_Parameters.extension` folder into the **same parent extensions directory** as the runtime extension, normally `%APPDATA%\pyRevit\Extensions`.
3. Keep only one intended runtime extension installed in that directory. The command discovers sibling folders containing both `config/parameters.json` and `lib/hdl_runtime/config.py`.
4. Reload pyRevit once to load the button.

The combined download contains both extension folders. Copy both folders individually into the extensions directory; do not place the manual extension inside the runtime extension.

If discovery finds a single candidate, it uses it. If exactly one candidate is named `HDL_RuntimeParameterUpdater.extension`, that name is preferred. Otherwise zero or multiple candidates produce an alert and no recalculation. Do not resolve ambiguity by keeping multiple active updaters installed; remove obsolete copies instead.

## Running the command

1. Open the Revit project whose parameters need updating.
2. Confirm the runtime configuration contains the correct parameter GUIDs, scope and enabled services.
3. Click **HDL → Parameters → Recalculate Parameters**.
4. Review the summary: matched elements checked, elements updated, parameters updated and element-level errors.
5. Inspect representative values in Properties, tags or schedules. The command runs in one `HDL | Recalculate Parameters` transaction; review Undo in the target Revit session.

The command processes the active project. It does not use the current selection, active-view visibility or a Scope Box, and it does not edit linked models or other open projects.

## Execution details

- The command locates the sibling runtime, imports its configuration and service loader and reads its enabled rules. There is no second independent configuration file for manual recalculation.
- Service modules are loaded once before beginning the model transaction.
- With family-only rules, collection is limited to FamilyInstance elements. If any rule has category scope, the command collects non-type elements and then applies exact family/category matching.
- As in runtime mode, family/category matching has **OR** semantics.
- Targets are looked up by configured GUID and must be shared, writable parameters.
- Each matching service returns GUID-to-value mappings. Missing targets, absent modules, non-dictionary results and unchanged values are skipped.
- Double comparison uses `1e-9`; Integer and String comparisons use their stored values. Unlike the runtime writer, this manual writer also supports ElementId outputs.
- All changes use one project transaction; there is no transaction per element, Idling queue, DocumentChanged hook or explicit updater re-registration.

## Summary and error handling

The displayed checked count refers to elements matching at least one rule, not every element visited by the collector. An update count is incremented when the command calls its write path for a changed value; it is not an independent post-write verification report.

Exceptions during processing of an element increment the error count and processing continues. Changes already made before an element-level exception are not explicitly rolled back for that element. A nonzero error count therefore requires inspection; the command does not provide detailed per-element error messages.

Missing parameters and skipped services do not necessarily increment the error count. In particular, an unavailable service module can be skipped. A summary with zero errors is not proof that every configured output was calculated.

The supplied command and dialogs are preserved as provided, including Russian summary/error text. The documentation is in English. Updating dialog language or changing error-reporting behavior would be a separate code change.

## Validation boundary

The command's Python syntax and package contents can be checked outside Revit. Actual sibling discovery under pyRevit, import resolution, service execution, parameter writes, interaction with active updaters and Undo/Redo must be checked inside Revit. The existing Opening Size unit tests validate that service's calculations, not the manual command's Revit execution.
