# -*- coding: utf-8 -*-

from hdl_runtime.registration import ensure_document

try:
    doc = __eventargs__.Document
except Exception:
    doc = None

if doc is not None:
    try:
        ensure_document(__revit__, doc)
    except Exception:
        pass
