# -*- coding: utf-8 -*-

from hdl_runtime.registration import ensure_current_document

try:
    ensure_current_document(__revit__)
except Exception:
    pass
