# -*- coding: utf-8 -*-

import os
from System import Guid

from Autodesk.Revit.DB import (
    ChangePriority,
    IUpdater,
    StorageType,
    UpdaterId,
)

from hdl_runtime.config import load_rules
from hdl_runtime.service_loader import load_service


UPDATER_GUID = Guid("37E74469-2CC0-4A14-8A9D-D64A1C9F9A31")
DOUBLE_TOLERANCE = 1.0e-9


def _extension_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _family_name(element):
    try:
        return element.Symbol.Family.Name
    except Exception:
        return None


def _category_name(element):
    try:
        return element.Category.Name if element.Category else None
    except Exception:
        return None


def _matches(rule, element):
    family_name = _family_name(element)
    category_name = _category_name(element)

    if rule["families"] and family_name in rule["families"]:
        return True

    if rule["categories"] and category_name in rule["categories"]:
        return True

    return False


def _same(parameter, value):
    if value is None:
        return True

    if parameter.StorageType == StorageType.Double:
        return abs(parameter.AsDouble() - float(value)) <= DOUBLE_TOLERANCE

    if parameter.StorageType == StorageType.Integer:
        return parameter.AsInteger() == int(value)

    if parameter.StorageType == StorageType.String:
        return (parameter.AsString() or "") == str(value)

    return False


def _set_value(parameter, value):
    if parameter is None or parameter.IsReadOnly or value is None:
        return False

    if _same(parameter, value):
        return False

    if parameter.StorageType == StorageType.Double:
        parameter.Set(float(value))
        return True

    if parameter.StorageType == StorageType.Integer:
        parameter.Set(int(value))
        return True

    if parameter.StorageType == StorageType.String:
        parameter.Set(str(value))
        return True

    return False


class RuntimeParameterUpdater(IUpdater):

    def __init__(self, addin_id):
        self._id = UpdaterId(addin_id, UPDATER_GUID)

    def GetUpdaterId(self):
        return self._id

    def GetUpdaterName(self):
        return "HDL Runtime Parameter Updater"

    def GetAdditionalInformation(self):
        return "Updates configured shared instance parameters."

    def GetChangePriority(self):
        return ChangePriority.FreeStandingComponents

    def Execute(self, data):
        doc = data.GetDocument()

        if doc is None or doc.IsFamilyDocument:
            return

        extension_root = _extension_root()
        rules = load_rules(extension_root)

        if not rules:
            return

        element_ids = []

        try:
            element_ids.extend(list(data.GetModifiedElementIds()))
        except Exception:
            pass

        try:
            element_ids.extend(list(data.GetAddedElementIds()))
        except Exception:
            pass

        if not element_ids:
            return

        services = {}

        for element_id in element_ids:
            element = doc.GetElement(element_id)

            if element is None:
                continue

            for rule in rules:
                if not _matches(rule, element):
                    continue

                parameter_map = {}

                for spec in rule["parameters"]:
                    try:
                        parameter = element.get_Parameter(Guid(spec["guid_text"]))
                    except Exception:
                        parameter = None

                    if parameter is None:
                        continue

                    try:
                        if not parameter.IsShared:
                            continue
                        if str(parameter.GUID).lower() != spec["guid_text"]:
                            continue
                    except Exception:
                        continue

                    parameter_map[spec["guid_text"]] = parameter

                if not parameter_map:
                    continue

                service_name = rule["service"]
                service = services.get(service_name)

                if service is None:
                    service = load_service(extension_root, service_name)
                    services[service_name] = service

                if service is None:
                    continue

                try:
                    values = service.calculate(doc, element, rule["parameters"])
                except Exception:
                    continue

                if not isinstance(values, dict):
                    continue

                for guid_text, value in values.items():
                    parameter = parameter_map.get(str(guid_text).lower())

                    if parameter is not None:
                        try:
                            _set_value(parameter, value)
                        except Exception:
                            pass
