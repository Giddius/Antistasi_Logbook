
from importlib import import_module, util
from .base_type_field import TypeFieldProtocol
import inspect

MODULES = {"standard_type_fields", "special_type_fields"}


TYPE_FIELD_TABLE: dict[str, TypeFieldProtocol] = {}

for _module in MODULES:
    module = import_module('.' + _module, package=__name__)
    for name, obj in inspect.getmembers(module):
        if hasattr(obj, "add_to_type_field_table") and name not in {"AllResourceItems", "TypeFieldProtocol"}:

            TYPE_FIELD_TABLE = obj.add_to_type_field_table(TYPE_FIELD_TABLE)
