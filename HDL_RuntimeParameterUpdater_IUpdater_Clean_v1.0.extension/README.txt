HDL Runtime Parameter Updater - CLEAN IUpdater v1.0

IMPORTANT:
Delete the previous HDL_RuntimeParameterUpdater.extension completely.
Do NOT merge this over the old DocumentChanged/Idling version.

This clean extension contains NO:
- doc-changed.py
- app-idling.py
- queue
- separate runtime Transaction
- Schema
- full-model rebuild

Runtime:
Revit transaction
-> IUpdater trigger
-> exact Family.Name filter
-> service.calculate()
-> parameter.Set() inside the SAME Revit transaction

Hooks:
- doc-opened.py
- view-activated.py

These hooks only register/refresh IUpdater. They do not modify the model.

SP_BOM_Absolute_Elevation service uses:
Level.Elevation + INSTANCE_ELEVATION_PARAM

Installation:
1. Delete the old extension folder.
2. Extract this extension.
3. Put your actual GUID and family names into config/parameters.json.
4. Reload pyRevit once.
5. Test move + Undo/Redo.

Editing service .py files does not require Reload.
parameters.json is watched by mtime; view activation refreshes trigger registration.

Additional supplied service: op_opening_size.py
SP_OP_Size target GUID: 51c5bd0e-4839-43aa-80f8-ffe67faa1a7e
Rectangles: description + newline + width x height(H), in cm.
Round openings: diameter in inches + description.
See repository README.md and docs/SERVICES.md for input names and setup.
