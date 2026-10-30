# -*- coding: utf-8 -*-

import os

from Autodesk.Revit.DB import (
    Element,
    ElementCategoryFilter,
    FamilySymbol,
    FilteredElementCollector,
    UpdaterRegistry,
)
from pyrevit import script

from hdl_runtime.config import load_rules, get_mtime
from hdl_runtime.updater import RuntimeParameterUpdater


STATE_KEY = "HDL_RPU_IUPDATER_CLEAN_STATE_V1"


def _extension_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc_key(doc):
    return str(doc.GetHashCode())


def _scope(rules):
    families = set()
    categories = set()

    for rule in rules:
        families.update(rule["families"])
        categories.update(rule["categories"])

    return families, categories


def _category_ids(doc, family_names, category_names):
    result = {}

    if family_names:
        for symbol in FilteredElementCollector(doc).OfClass(FamilySymbol):
            try:
                family = symbol.Family
                category = symbol.Category

                if family and category and family.Name in family_names:
                    result[category.Id.IntegerValue] = category.Id
            except Exception:
                pass

    if category_names:
        for element in FilteredElementCollector(doc).WhereElementIsNotElementType():
            try:
                category = element.Category
                if category and category.Name in category_names:
                    result[category.Id.IntegerValue] = category.Id
            except Exception:
                pass

    return result


def ensure_current_document(uiapp):
    if uiapp is None or uiapp.ActiveUIDocument is None:
        return

    ensure_document(uiapp, uiapp.ActiveUIDocument.Document)


def ensure_document(uiapp, doc):
    if uiapp is None or doc is None or doc.IsFamilyDocument:
        return

    extension_root = _extension_root()
    rules = load_rules(extension_root)

    if not rules:
        return

    family_names, category_names = _scope(rules)
    category_ids = _category_ids(doc, family_names, category_names)

    if not category_ids:
        return

    updater = RuntimeParameterUpdater(uiapp.Application.ActiveAddInId)
    updater_id = updater.GetUpdaterId()

    signature = "{0}|{1}".format(
        repr(get_mtime(extension_root)),
        ",".join(str(x) for x in sorted(category_ids.keys()))
    )

    state = script.get_envvar(STATE_KEY) or {}
    key = _doc_key(doc)

    try:
        registered = UpdaterRegistry.IsUpdaterRegistered(updater_id, doc)
    except Exception:
        registered = False

    if registered and state.get(key) == signature:
        return

    if registered:
        try:
            UpdaterRegistry.UnregisterUpdater(updater_id, doc)
        except Exception:
            return

    try:
        UpdaterRegistry.RegisterUpdater(updater, doc, True)
    except Exception:
        return

    geometry_change = Element.GetChangeTypeGeometry()
    element_addition = Element.GetChangeTypeElementAddition()

    for category_id in category_ids.values():
        try:
            element_filter = ElementCategoryFilter(category_id)

            UpdaterRegistry.AddTrigger(
                updater_id,
                doc,
                element_filter,
                geometry_change
            )

            UpdaterRegistry.AddTrigger(
                updater_id,
                doc,
                element_filter,
                element_addition
            )
        except Exception:
            pass

    state[key] = signature
    script.set_envvar(STATE_KEY, state)
