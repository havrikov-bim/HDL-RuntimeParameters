# -*- coding: utf-8 -*-

import json
import os

_CACHE_PATH = None
_CACHE_MTIME = None
_CACHE_DATA = None


def _path(extension_root):
    return os.path.join(extension_root, "config", "parameters.json")


def load_rules(extension_root):
    global _CACHE_PATH, _CACHE_MTIME, _CACHE_DATA

    path = _path(extension_root)
    mtime = os.path.getmtime(path)

    if _CACHE_DATA is not None and _CACHE_PATH == path and _CACHE_MTIME == mtime:
        return _CACHE_DATA

    with open(path, "r") as stream:
        data = json.load(stream)

    rules = []

    for item in data.get("services", []):
        if not item.get("enabled", True):
            continue

        service_name = str(item.get("service") or "").strip()
        parameters = item.get("parameters") or []
        scope = item.get("scope") or {}

        families = set(str(x).strip() for x in (scope.get("families") or []) if str(x).strip())
        categories = set(str(x).strip() for x in (scope.get("categories") or []) if str(x).strip())

        if not service_name or not parameters or (not families and not categories):
            continue

        clean_parameters = []

        for parameter in parameters:
            name = str(parameter.get("name") or "").strip()
            guid_text = str(parameter.get("guid") or "").strip().lower()

            if name and guid_text:
                clean_parameters.append({
                    "name": name,
                    "guid_text": guid_text
                })

        if clean_parameters:
            rules.append({
                "service": service_name,
                "parameters": clean_parameters,
                "families": families,
                "categories": categories
            })

    _CACHE_PATH = path
    _CACHE_MTIME = mtime
    _CACHE_DATA = rules

    return rules


def get_mtime(extension_root):
    return os.path.getmtime(_path(extension_root))
