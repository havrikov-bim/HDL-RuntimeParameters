"""Calculation checks using minimal Revit API substitutes, not runtime tests."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


PATH = (Path(__file__).resolve().parents[1]
        / 'HDL_RuntimeParameterUpdater_IUpdater_Clean_v1.0.extension'
        / 'lib/hdl_runtime/services/op_opening_size.py')
db = ModuleType('Autodesk.Revit.DB')
db.StorageType = SimpleNamespace(Double='Double', String='String')
with patch.dict(sys.modules, {'Autodesk': ModuleType('Autodesk'),
                             'Autodesk.Revit': ModuleType('Autodesk.Revit'),
                             'Autodesk.Revit.DB': db}):
    spec = importlib.util.spec_from_file_location('opening_size_service', PATH)
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)


class Parameter:
    def __init__(self, value):
        self.value = value
        self.StorageType = 'String' if isinstance(value, str) else 'Double'

    def AsDouble(self):
        return self.value

    def AsString(self):
        return self.value


def element(family, values, type_values=None):
    def lookup(data):
        return lambda name: Parameter(data[name]) if name in data else None
    return SimpleNamespace(
        LookupParameter=lookup(values),
        Symbol=SimpleNamespace(Family=SimpleNamespace(Name=family),
                               LookupParameter=lookup(type_values or {})))


class OpeningSizeTests(unittest.TestCase):
    def calculate(self, family, values, type_values=None, guid=None):
        return service.calculate(None, element(family, values, type_values),
                                 [{'guid_text': guid or service.TARGET_GUID}])

    def test_rectangular_centimeters_and_height_marker(self):
        for family in service.RECT_FAMILIES:
            result = self.calculate(family, {'SP_OP_Width': 400 / 304.8,
                'SP_OP_Height': 250 / 304.8, 'SP_OP_Description': ' Opening '})
            self.assertEqual(result[service.TARGET_GUID], 'Opening\n40 x 25(H)')

    def test_round_inches_and_diameter_symbol(self):
        for family in service.ROUND_FAMILIES:
            result = self.calculate(family, {'SP_OP_Diameter': 4 / 12.0,
                                             'SP_OP_Description': 'Opening'})
            self.assertEqual(result[service.TARGET_GUID], 'ø4" Opening')

    def test_type_fallback(self):
        result = self.calculate('BL Opening Round Wall', {},
                                {'SP_OP_Diameter': 0.5, 'SP_OP_Description': 'Type'})
        self.assertEqual(result[service.TARGET_GUID], 'ø6" Type')

    def test_missing_description_preserves_output(self):
        self.assertEqual(self.calculate('BL Opening Round Wall',
                                       {'SP_OP_Diameter': 0.5}), {})

    def test_wrong_instance_type_does_not_fall_back(self):
        self.assertEqual(self.calculate('BL Opening Round Wall',
            {'SP_OP_Diameter': '6', 'SP_OP_Description': ''},
            {'SP_OP_Diameter': 0.5}), {})

    def test_unsupported_family(self):
        self.assertEqual(self.calculate('Other', {}), {})

    def test_unconfigured_guid(self):
        self.assertEqual(self.calculate('BL Opening Round Wall',
            {'SP_OP_Diameter': 0.5, 'SP_OP_Description': ''},
            guid='00000000-0000-0000-0000-000000000000'), {})

    def test_empty_description(self):
        result = self.calculate('BL Opening Rect Wall', {'SP_OP_Width': 1,
            'SP_OP_Height': 1, 'SP_OP_Description': ''})
        self.assertEqual(result[service.TARGET_GUID], '30.48 x 30.48(H)')

    def test_decimal_formatting(self):
        self.assertEqual(service._number(12.3456), '12.35')
        self.assertEqual(service._number(12.0), '12')
        self.assertEqual(service._number(-0.00001), '0')
