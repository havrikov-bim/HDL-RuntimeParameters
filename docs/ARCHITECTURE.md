# Architecture and Implementation Notes

[Overview and installation](../README.md) · [Calculation service interface](SERVICES.md)

## Components

All paths below are relative to `HDL_RuntimeParameterUpdater_IUpdater_Clean_v1.0.extension`.

| Component | Responsibility |
| --- | --- |
| `startup.py` | Attempt registration for the active project when the extension starts |
| `hooks/doc-opened.py` | Attempt registration for an opened project |
| `hooks/view-activated.py` | Register or refresh the updater for the active project |
| `config/parameters.json` | List services, parameter names/GUIDs and family/category scope |
| `lib/hdl_runtime/config.py` | Read enabled rules and cache them by configuration path and modification time |
| `lib/hdl_runtime/registration.py` | Discover category IDs, register a document-specific updater and attach triggers |
| `lib/hdl_runtime/updater.py` | Match instances, resolve targets, invoke services and write changed values |
| `lib/hdl_runtime/service_loader.py` | Load Python modules from the services directory |
| `lib/hdl_runtime/services/absolute_elevation.py` | Calculate level elevation plus instance elevation from level |
| `lib/hdl_runtime/services/op_opening_size.py` | Format a round or rectangular opening size and description into `SP_OP_Size` |

## Registration

Family documents are excluded. Scope is collected across enabled services. Family names are resolved through loaded FamilySymbol elements; explicit category names are resolved through project instances. A category with no matching instance might therefore not be discovered until a later registration refresh. Families/categories must be available in the project for registration to find their category IDs.

`RuntimeParameterUpdater` implements Revit `IUpdater`. Its identity combines the active add-in ID with fixed updater GUID `37E74469-2CC0-4A14-8A9D-D64A1C9F9A31`. Priority is `FreeStandingComponents` and registration is optional for the document.

The registration signature combines configuration modification time and resolved category IDs. If that signature matches the remembered state and the updater is already registered, registration is left unchanged. Otherwise the existing registration is removed and rebuilt.

Each category receives two triggers: `Element.GetChangeTypeGeometry()` and `Element.GetChangeTypeElementAddition()`. There is no parameter-specific trigger. View activation refreshes registration after configuration edits; it does not recalculate all instances.

An empty rule set or unresolved category set returns before unregistering an existing updater. Do not treat an empty configuration as an explicit uninstall operation. Although existing callbacks normally do no work when there are no enabled rules, the registration lifecycle still needs more explicit management for a future release.

## Execution and writes

Execute gathers modified and added element IDs from UpdaterData. For each element, a rule matches if its exact family name is listed **or** its exact category name is listed. These selectors are not combined as an intersection.

Each configured GUID is converted to `System.Guid` and resolved with `element.get_Parameter`. The result must be a shared parameter with the same GUID. A service is invoked only when at least one of its configured targets exists on the element. The service receives the complete configured parameter specification list, including targets that may be absent on this particular element; writes remain restricted to the resolved target map.

Loaded service modules are retained in a dictionary for the current Execute call. `calculate` must return a dictionary. Returned GUID keys are normalized to lowercase and matched to the configured targets; unconfigured outputs are ignored.

Writing supports:

| Storage type | Conversion and equality |
| --- | --- |
| Double | `float(value)`; skip when difference is at most `1e-9` |
| Integer | `int(value)`; exact integer comparison |
| String | `str(value)`; compare with the current string, treating an empty current value as `""` |

`None`, missing targets and API-read-only parameters are skipped. ElementId values are not supported. A `None` result means “leave the current value unchanged”, rather than clearing it. To clear a String parameter, return an empty string.

Values are set within the triggering Revit transaction. The implementation does not create a second transaction, queue work to Idling, use DocumentChanged or store calculation rules in Extensible Storage.

## Configuration and service refresh

The configuration cache uses path and `os.path.getmtime`. It does not hash content or check size. Edits that preserve the timestamp may not be noticed. JSON version is present in the example but is not enforced as a schema version by the parser. The parser filters incomplete rules; it does not provide strict type, GUID or duplicate-rule validation.

Service modules are loaded through `imp.load_source`; their names include the file modification timestamp. Saved service changes can be loaded on a later updater execution without reloading the whole extension. New service files still need a matching configured rule and usable registration scope. Importing a service executes its top-level Python code.

## Absolute elevation service

The supplied service reads `element.LevelId`, requires a Level, reads the Double `INSTANCE_ELEVATION_PARAM` and calculates `level.Elevation + elevation_from_level`. It returns the result for configured specifications named `SP_BOM_Absolute_Elevation`. Values stay in Revit's internal length units.

If a level or the instance elevation parameter is unavailable, the service returns an empty dictionary and leaves existing values unchanged. This formula does not add an explicit project/survey coordinate transform. Its meaning must be checked against the elevation convention of the target family and project.

## Opening Size service

The second service classifies four exact BL Opening family names and reads `SP_OP_*` dimensions and description from the instance, with type fallback for absent inputs. It converts dimensions to centimeters for rectangles and inches for round openings, then returns formatted text for fixed target GUID `51c5bd0e-4839-43aa-80f8-ffe67faa1a7e`. See [the service guide](SERVICES.md#shape-dependent-opening-size) for the precise input/output contract.

## Boundaries and future work

This version provides event-driven dispatch and shared-parameter writing. It does not implement a dependency graph, ordered formula evaluation, automatic downstream propagation or cycle detection. Rule list order alone does not establish a dependency system.

Broad exception handling currently suppresses many registration, loading, calculation and write failures. Future diagnostics should distinguish inapplicable instances from invalid configuration and failed calculations. Initial/batch recalculation, parameter-specific triggers, level/location dependencies, stricter validation, explicit unregistration and runtime compatibility checks are possible improvements; they are not included capabilities.

The fixed updater GUID and session state key are another reason not to run duplicate versions of this extension side by side.
