# -*- coding: utf-8 -*-
"""HDL IUpdater service: SP_OP_Size for rectangular and round openings.

Input parameters: LookupParameter (instance, fallback to type).
Output: {shared_parameter_guid: text}. No transactions or parameter writes.
"""

from Autodesk.Revit.DB import StorageType

RECT_FAMILIES = frozenset((
    "BL Opening Rect Floor",
    "BL Opening Rect Wall",
))
ROUND_FAMILIES = frozenset((
    "BL Opening Round Floor",
    "BL Opening Round Wall",
))
TARGET_GUID = "51c5bd0e-4839-43aa-80f8-ffe67faa1a7e"
FEET_TO_CM = 30.48
FEET_TO_INCHES = 12.0


def _parameter(element, name):
    param = element.LookupParameter(name)
    if param is not None:
        return param
    symbol = getattr(element, "Symbol", None)
    if symbol is not None:
        return symbol.LookupParameter(name)
    return None


def _length(element, name):
    param = _parameter(element, name)
    if param is None or param.StorageType != StorageType.Double:
        return None
    return param.AsDouble()


def _string(element, name):
    param = _parameter(element, name)
    if param is None or param.StorageType != StorageType.String:
        return None
    return (param.AsString() or "").strip()


def _number(value):
    """Decimal number with at most two fractional digits, no trailing zeros."""
    result = "{0:.2f}".format(value).rstrip("0").rstrip(".")
    return "0" if result == "-0" else result


def calculate(doc, element, parameters):
    try:
        family_name = element.Symbol.Family.Name
    except Exception:
        return {}

    if family_name in RECT_FAMILIES:
        width = _length(element, "SP_OP_Width")
        height = _length(element, "SP_OP_Height")
        description = _string(element, "SP_OP_Description")
        if None in (width, height, description):
            return {}
        size = u"{0}\n{1} x {2}(H)".format(
            description,
            _number(width * FEET_TO_CM),
            _number(height * FEET_TO_CM),
        ).strip()
    elif family_name in ROUND_FAMILIES:
        diameter = _length(element, "SP_OP_Diameter")
        description = _string(element, "SP_OP_Description")
        if None in (diameter, description):
            return {}
        size = u'ø{0}" {1}'.format(
            _number(diameter * FEET_TO_INCHES),
            description,
        ).rstrip()
    else:
        return {}

    # The engine decides which configured shared parameters exist and are writable.
    return {
        spec["guid_text"]: size
        for spec in parameters
        if spec.get("guid_text", "").lower() == TARGET_GUID
    }
