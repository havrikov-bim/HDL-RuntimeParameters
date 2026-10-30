# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import (
    BuiltInParameter,
    ElementId,
    Level,
    StorageType,
)


TARGET_PARAMETER_NAME = "SP_BOM_Absolute_Elevation"


def _get_level(doc, element):
    try:
        level_id = element.LevelId

        if level_id and level_id != ElementId.InvalidElementId:
            level = doc.GetElement(level_id)

            if isinstance(level, Level):
                return level
    except Exception:
        pass

    return None


def _get_elevation_from_level(element):
    try:
        parameter = element.get_Parameter(
            BuiltInParameter.INSTANCE_ELEVATION_PARAM
        )

        if parameter and parameter.StorageType == StorageType.Double:
            return parameter.AsDouble()
    except Exception:
        pass

    return None


def calculate(doc, element, parameters):
    level = _get_level(doc, element)

    if level is None:
        return {}

    elevation_from_level = _get_elevation_from_level(element)

    if elevation_from_level is None:
        return {}

    absolute_elevation = level.Elevation + elevation_from_level

    result = {}

    for parameter in parameters:
        if parameter["name"] == TARGET_PARAMETER_NAME:
            result[parameter["guid_text"]] = absolute_elevation

    return result
