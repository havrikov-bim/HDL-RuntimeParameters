# -*- coding: utf-8 -*-
"""Manual one-shot recalculation using existing HDL services."""
import os
import sys
from System import Guid
from Autodesk.Revit.DB import FamilyInstance, FilteredElementCollector, StorageType
from pyrevit import revit, forms


def find_extension_dir(path):
    folder = os.path.abspath(os.path.dirname(path))
    while True:
        if folder.lower().endswith('.extension'):
            return folder
        parent = os.path.dirname(folder)
        if parent == folder:
            raise Exception('Extension root not found')
        folder = parent


def same(parameter, value):
    if value is None:
        return True
    kind = parameter.StorageType
    if kind == StorageType.Double:
        return abs(parameter.AsDouble() - float(value)) <= 1e-9
    if kind == StorageType.Integer:
        return parameter.AsInteger() == int(value)
    if kind == StorageType.String:
        return (parameter.AsString() or '') == str(value)
    if kind == StorageType.ElementId:
        return parameter.AsElementId() == value
    return True


def write(parameter, value):
    if value is None or parameter.IsReadOnly or same(parameter, value):
        return False
    kind = parameter.StorageType
    if kind == StorageType.Double:
        parameter.Set(float(value))
    elif kind == StorageType.Integer:
        parameter.Set(int(value))
    elif kind == StorageType.String:
        parameter.Set(str(value))
    elif kind == StorageType.ElementId:
        parameter.Set(value)
    else:
        return False
    return True


# This button lives in a separate extension. Find the runtime extension
# beside it rather than searching inside this button's own extension.
button_root = find_extension_dir(__file__)
extensions_folder = os.path.dirname(button_root)

candidates = []
for folder_name in os.listdir(extensions_folder):
    candidate = os.path.join(extensions_folder, folder_name)
    if not os.path.isdir(candidate) or candidate == button_root:
        continue
    if not folder_name.lower().endswith(".extension"):
        continue
    config_candidate = os.path.join(candidate, "config", "parameters.json")
    library_candidate = os.path.join(candidate, "lib", "hdl_runtime", "config.py")
    if os.path.isfile(config_candidate) and os.path.isfile(library_candidate):
        candidates.append(candidate)

preferred = [p for p in candidates
             if os.path.basename(p).lower() == "hdl_runtimeparameterupdater.extension"]
if len(preferred) == 1:
    root = preferred[0]
elif len(candidates) == 1:
    root = candidates[0]
else:
    detail = ("\\n".join(candidates) if candidates else "Не найдено подходящих расширений.")
    forms.alert(
        "Не удалось однозначно найти HDL Runtime Parameter Updater.\\n"
        "Проверьте папки в Extensions.\\n\\n" + detail,
        title="HDL Recalculate Parameters")
    sys.exit()

lib = os.path.join(root, "lib")
if lib not in sys.path:
    sys.path.insert(0, lib)

from hdl_runtime.config import load_rules
from hdl_runtime.service_loader import load_service

try:
    rules = load_rules(root)
except Exception as exc:
    forms.alert('Ошибка конфигурации:\n' + str(exc),
                title='HDL Recalculate Parameters')
    sys.exit()

if not rules:
    forms.alert('Нет активных сервисов.', title='HDL Recalculate Parameters')
    sys.exit()

doc = revit.doc
if doc is None or doc.IsFamilyDocument:
    forms.alert('Откройте проект Revit.', title='HDL Recalculate Parameters')
    sys.exit()

# Each family is visited once; no full geometry calculation or per-element transaction.
family_rules = {}
category_rules = []
for rule in rules:
    for name in rule['families']:
        family_rules.setdefault(name, []).append(rule)
    if rule['categories']:
        category_rules.append(rule)

if category_rules:
    collector = FilteredElementCollector(doc).WhereElementIsNotElementType()
else:
    collector = FilteredElementCollector(doc).OfClass(FamilyInstance)

# Resolve services once, and before beginning the model transaction.
modules = {}
for rule in rules:
    name = rule['service']
    if name not in modules:
        modules[name] = load_service(root, name)

scanned = updated_elements = updated_parameters = errors = 0
with revit.Transaction('HDL | Recalculate Parameters'):
    for element in collector:
        try:
            family = None
            if isinstance(element, FamilyInstance):
                family = element.Symbol.Family.Name
            category = element.Category.Name if element.Category else None
            matching = []
            for rule in rules:
                if (family and family in rule['families']) or (category and category in rule['categories']):
                    matching.append(rule)
            if not matching:
                continue
            scanned += 1
            element_updated = False
            for rule in matching:
                targets = {}
                for spec in rule['parameters']:
                    try:
                        param = element.get_Parameter(Guid(spec['guid_text']))
                        if param is not None and param.IsShared and not param.IsReadOnly:
                            targets[spec['guid_text'].lower()] = param
                    except Exception:
                        continue
                if not targets:
                    continue
                module = modules.get(rule['service'])
                if module is None:
                    continue
                values = module.calculate(doc, element, rule['parameters'])
                if not isinstance(values, dict):
                    continue
                for guid, value in values.items():
                    p = targets.get(str(guid).lower())
                    if p is not None and write(p, value):
                        updated_parameters += 1
                        element_updated = True
            if element_updated:
                updated_elements += 1
        except Exception:
            errors += 1

forms.alert('Проверено экземпляров: {0}\nОбновлено экземпляров: {1}\nОбновлено параметров: {2}\nОшибок: {3}'.format(
    scanned, updated_elements, updated_parameters, errors), title='HDL Recalculate Parameters')
