
from importlib import import_module, util
from .base_type_field import TypeFieldProtocol
import inspect

from .standard_type_fields import BoolTypeField, StringTypeField, IntTypeField, ListTypeField, FloatTypeField
from .special_type_fields import URLTypeField, PathTypeField


TYPE_FIELD_TABLE: dict[str, TypeFieldProtocol] = {}

for field in [BoolTypeField, StringTypeField, IntTypeField, ListTypeField, FloatTypeField, URLTypeField, PathTypeField]:
    TYPE_FIELD_TABLE = field.add_to_type_field_table(TYPE_FIELD_TABLE)
