# -*- coding: utf-8 -*-

import imp
import os


def load_service(extension_root, filename):
    path = os.path.join(extension_root, "lib", "hdl_runtime", "services", filename)

    if not os.path.isfile(path):
        return None

    stamp = os.path.getmtime(path)
    module_name = "hdl_rpu_{0}_{1}".format(
        os.path.splitext(filename)[0],
        str(stamp).replace(".", "_")
    )

    try:
        module = imp.load_source(module_name, path)
    except Exception:
        return None

    return module if hasattr(module, "calculate") else None
