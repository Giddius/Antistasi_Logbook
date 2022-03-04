"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import attr
from sortedcontainers import SortedSet

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.base_record import BaseRecord, RecordFamily
from antistasi_logbook.storage.models.models import LogRecord, RecordClass

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

RECORD_CLASS_TYPE = Union[type["AbstractRecord"], type["BaseRecord"]]


@attr.s(auto_attribs=True, auto_detect=True, frozen=True, slots=True, weakref_slot=True)
class StoredRecordClass:
    concrete_class: RECORD_CLASS_TYPE = attr.ib()
    model: RecordClass = attr.ib()

    def check(self, log_record: "LogRecord") -> bool:
        return self.concrete_class.check(log_record=log_record)


class RecordClassManager:
    record_class_registry: dict[str, StoredRecordClass] = {}
    record_class_registry_by_id: dict[str, StoredRecordClass] = {}
    generic_record_classes: SortedSet[StoredRecordClass] = SortedSet(key=lambda x: -x.concrete_class.___specificity___)
    antistasi_record_classes: SortedSet[StoredRecordClass] = SortedSet(key=lambda x: -x.concrete_class.___specificity___)

    def __init__(self, foreign_key_cache: "ForeignKeyCache", default_record_class: RECORD_CLASS_TYPE = None) -> None:
        self.foreign_key_cache = foreign_key_cache
        BaseRecord.foreign_key_cache = self.foreign_key_cache
        self._default_record_concrete_class = BaseRecord if default_record_class is None else default_record_class
        self._default_record_class: "StoredRecordClass" = None

    @property
    def default_record_class(self) -> StoredRecordClass:
        if self._default_record_class is None:
            try:
                model = RecordClass.select().where(RecordClass.name == self._default_record_concrete_class.__name__)[0]
            except IndexError:
                model = RecordClass(name=self._default_record_concrete_class.__name__)
                model.save()
            self._default_record_class = StoredRecordClass(self._default_record_concrete_class, model)
        return self._default_record_class

    @classmethod
    def register_record_class(cls, record_class: RECORD_CLASS_TYPE) -> None:
        name = record_class.__name__
        if name in cls.record_class_registry:
            return
        try:
            model = RecordClass.select().where(RecordClass.name == name)[0]
        except IndexError:
            model = RecordClass(name=name)
            model.save()
        stored_item = StoredRecordClass(record_class, model)
        cls.record_class_registry[name] = stored_item
        cls.record_class_registry_by_id[str(model.id)] = stored_item
        if RecordFamily.GENERIC in record_class.___record_family___:
            cls.generic_record_classes.add(stored_item)
        if RecordFamily.ANTISTASI in record_class.___record_family___:
            cls.antistasi_record_classes.add(stored_item)

    def get_by_name(self, name: str) -> RECORD_CLASS_TYPE:
        return self.record_class_registry.get(name, self.default_record_class).concrete_class

    def get_by_id(self, model_id: int) -> RECORD_CLASS_TYPE:
        return self.record_class_registry_by_id.get(str(model_id), self.default_record_class).concrete_class

    def determine_record_class(self, log_record: LogRecord) -> "RecordClass":
        # TODO: make generic regarding record_classes selection
        record_classes = self.antistasi_record_classes if log_record.origin_id == 1 else self.generic_record_classes
        for stored_class in record_classes:
            if stored_class.check(log_record) is True:
                return stored_class.model
        return self.default_record_class.model

    def reset(self) -> None:
        all_registered_classes = list(self.record_class_registry.values())
        self.record_class_registry.clear()
        self.record_class_registry_by_id.clear()
        self.antistasi_record_classes.clear()
        self.generic_record_classes.clear()
        self._default_record_class = None
        for registered_class in all_registered_classes:
            self.register_record_class(registered_class.concrete_class)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
