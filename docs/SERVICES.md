# Writing Calculation Services

[Overview](../README.md) · [Architecture](ARCHITECTURE.md)

## Service contract

Place a Python file in the extension's `lib/hdl_runtime/services` directory and reference its filename from `config/parameters.json`.

The module must expose:

```python
def calculate(doc, element, parameters):
    # Calculate values from the current document and instance.
    # Return an empty dictionary if this instance cannot be evaluated.
    return {}
```

| Argument / result | Meaning |
| --- | --- |
| `doc` | Current Revit project document |
| `element` | Added or geometry-modified element matching the configured rule |
| `parameters` | List of dictionaries containing `name` and lowercase `guid_text` |
| Return value | Dictionary mapping configured GUID strings to values compatible with their target storage types |

Return data rather than opening a transaction or modifying the model inside the service. The dispatcher handles parameter resolution and writes within the triggering transaction.

## Absolute Elevation service

`absolute_elevation.py` is a working example of the interface. It:

1. Finds the instance's associated Level.
2. Reads `BuiltInParameter.INSTANCE_ELEVATION_PARAM` as a Double.
3. Adds the offset to `Level.Elevation`.
4. Returns the result for specifications named `SP_BOM_Absolute_Elevation`, keyed by their configured GUIDs.

The configured name is significant to this service; the dispatcher itself resolves shared parameters by GUID. Changing only the name in JSON will therefore prevent this particular service from producing its expected output.

## Adding a new calculation

1. Define the output shared instance parameter and obtain its actual GUID.
2. Add a service module with the `calculate` interface.
3. Add an enabled entry in the JSON configuration with the filename, target parameter and applicable families/categories.
4. Activate a project view to refresh registration after saving configuration.
5. Perform an applicable element-addition or geometry-change action.
6. Check the stored value and Undo/Redo in Revit.

Use exact names. A family selector and a category selector have OR semantics, so a category can substantially broaden the service's scope.

## Units and values

Return Double values in the units expected by Revit parameter storage. Length values generally use internal feet. This mechanism does not convert display units or format numeric values automatically. String outputs should already contain the intended text.

Return `{}` when the calculation is inapplicable; return `None` for an output to preserve its current value. Return `""` to clear a String output. Missing/read-only parameters are skipped. This mechanism does not create parameters or prevent users from editing them manually.

## Trigger dependencies

A service runs for additions and geometry changes in its registered scope. Reading another parameter does not automatically subscribe the service to changes in that parameter. Likewise, reading a Level does not establish a trigger that recalculates every dependent instance when that Level changes.

A calculation requiring such behavior needs additional trigger/dependency design. The current service interface should not be described as a complete formula or dependency engine.

## Shape-dependent Opening Size

`op_opening_size.py` is the second included service. It recognizes exact family names:

- Rectangular: `BL Opening Rect Floor`, `BL Opening Rect Wall`.
- Round: `BL Opening Round Floor`, `BL Opening Round Wall`.

Rectangular inputs are `SP_OP_Width` and `SP_OP_Height` (Double lengths) and `SP_OP_Description` (String). Output contains the trimmed description, a newline, and `width x height(H)` in centimeters. Round inputs are `SP_OP_Diameter` (Double length) and `SP_OP_Description`; output is `ødiameter" description` with diameter in inches.

The service converts feet to centimeters using 30.48 and feet to inches using 12. Numbers are formatted to at most two fractional digits, with trailing zeros removed and negative zero normalized to `0`. Empty descriptions are accepted, but a missing description parameter is not. Missing or wrong-storage-type inputs and unrecognized families produce `{}`, preserving the previous output.

Input resolution uses `LookupParameter` on the instance, falling back to the family symbol only when the instance parameter is absent. An existing instance parameter with the wrong storage type does not fall back to the type. The service does not convert arbitrary display strings to lengths.

Output is selected by fixed `TARGET_GUID = "51c5bd0e-4839-43aa-80f8-ffe67faa1a7e"`, rather than the configured parameter name. JSON must contain that GUID for `SP_OP_Size`, and the corresponding shared Text instance parameter must exist. To use a different shared parameter definition, update both the constant and configuration. The dispatcher writes the result; the service opens no transaction and writes no parameters itself.

Changes to a description alone, or type-level inputs that do not cause an instance geometry event, are not guaranteed to trigger recalculation under the current registration rules. The calculation service supports reading these inputs; trigger dependency handling remains the runtime mechanism's separate concern.
