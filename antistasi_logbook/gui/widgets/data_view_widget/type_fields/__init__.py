
from importlib import import_module, util
from .base_type_field import TypeFieldProtocol
import inspect
from typing import Any, Optional
from .standard_type_fields import BoolTypeField, StringTypeField, IntTypeField, ListTypeField, FloatTypeField, DictTypeField
from .special_type_fields import URLTypeField, PathTypeField
from gidapptools import get_logger


TYPE_FIELD_TABLE: dict[str, TypeFieldProtocol] = {}

for field in [BoolTypeField, StringTypeField, IntTypeField, ListTypeField, FloatTypeField, URLTypeField, PathTypeField, DictTypeField]:
    TYPE_FIELD_TABLE = field.add_to_type_field_table(TYPE_FIELD_TABLE)


def get_type_widget(value: Any) -> type["TypeFieldProtocol"]:
    typus = type(value)
    type_widget = TYPE_FIELD_TABLE.get(typus, StringTypeField)

    return type_widget
