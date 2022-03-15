"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union
from pathlib import Path
from collections import defaultdict

# * Third Party Imports --------------------------------------------------------------------------------->
import attr
from sortedcontainers import SortedSet

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.general_classes import GenericThreadsafePool

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.base_record import BaseRecord, RecordFamily
from antistasi_logbook.storage.models.models import LogRecord, RecordClass
from frozendict import frozendict
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
log = get_logger(__name__)
# endregion[Constants]

RECORD_CLASS_TYPE = Union[type["AbstractRecord"], type["BaseRecord"]]


@attr.s(auto_attribs=True, auto_detect=True, frozen=True, slots=True, weakref_slot=True)
class StoredRecordClass:
    concrete_class: RECORD_CLASS_TYPE = attr.ib()
    model: RecordClass = attr.ib()

    def check(self, log_record: "LogRecord") -> bool:
        return self.concrete_class.check(log_record=log_record)


def new_sorted_set() -> SortedSet:
    return SortedSet(key=lambda x: -x.concrete_class.___specificity___)


class RecordClassChecker:
    __slots__ = ("foreign_key_cache", "default_record_class", "generic_record_classes", "antistasi_record_classes", "family_handler_table")

    def __init__(self, foreign_key_cache: "ForeignKeyCache", default_record_class: StoredRecordClass, generic_record_classes: SortedSet[StoredRecordClass], antistasi_record_classes: dict[str, Union[SortedSet[StoredRecordClass], StoredRecordClass]]) -> None:
        self.foreign_key_cache = foreign_key_cache
        self.default_record_class = default_record_class
        self.generic_record_classes = generic_record_classes
        self.antistasi_record_classes = antistasi_record_classes
        self.family_handler_table = frozendict({RecordFamily.GENERIC: self._determine_generic_record_class,
                                                RecordFamily.ANTISTASI: self._determine_antistasi_record_class})
        self.foreign_key_cache.preload_all()

    def _determine_generic_record_class(self, log_record: LogRecord) -> "RecordClass":
        for stored_class in self.generic_record_classes:
            if stored_class.check(log_record) is True:
                return stored_class.model

    def _determine_antistasi_record_class(self, log_record: LogRecord) -> "RecordClass":
        try:
            function_name = log_record.logged_from.function_name
        except AttributeError as e:
            log.critical("Error %r with log_record %r, of log_file %r from server %r", e, log_record, log_record.log_file, log_record.log_file.server)
            return self.antistasi_record_classes["DEFAULT"].model

        sub_set = self.antistasi_record_classes.get(function_name, None)
        if sub_set is None:
            return self.antistasi_record_classes["DEFAULT"].model

        for stored_class in sub_set:
            if stored_class.check(log_record) is True:
                return stored_class.model

        return self.antistasi_record_classes["DEFAULT"].model

    def _determine_record_class(self, log_record: LogRecord) -> "RecordClass":

        family = self.foreign_key_cache.get_origin_by_id(log_record.origin_id).record_family
        handler = self.family_handler_table.get(family, self._determine_generic_record_class)
        _out = handler(log_record)
        if _out is None:
            _out = self.default_record_class.model
        return _out


class RecordClassManager:
    __slots__ = ("foreign_key_cache", "_default_record_concrete_class", "_default_record_class", "family_handler_table", "record_class_checker_pool")
    record_class_registry: dict[str, StoredRecordClass] = {}
    record_class_registry_by_id: dict[str, StoredRecordClass] = {}
    generic_record_classes: SortedSet[StoredRecordClass] = SortedSet(key=lambda x: -x.concrete_class.___specificity___)
    antistasi_record_classes: dict[str, Union[SortedSet, StoredRecordClass]] = defaultdict(new_sorted_set)

    def __init__(self, foreign_key_cache: "ForeignKeyCache", default_record_class: RECORD_CLASS_TYPE = None) -> None:
        self.foreign_key_cache = foreign_key_cache
        BaseRecord.foreign_key_cache = self.foreign_key_cache
        self._default_record_concrete_class = BaseRecord if default_record_class is None else default_record_class
        self._default_record_class: "StoredRecordClass" = None

        self.record_class_checker_pool: GenericThreadsafePool = GenericThreadsafePool(obj_creator=self._create_record_checker, max_size=10)

    def _create_record_checker(self) -> RecordClassChecker:

        return RecordClassChecker(foreign_key_cache=self.foreign_key_cache,
                                  default_record_class=self.default_record_class,
                                  generic_record_classes=self.generic_record_classes.copy(),
                                  antistasi_record_classes=self.antistasi_record_classes.copy())

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
        model._record_class = record_class
        stored_item = StoredRecordClass(record_class, model)
        cls.record_class_registry[name] = stored_item
        cls.record_class_registry_by_id[str(model.id)] = stored_item
        if RecordFamily.GENERIC in record_class.___record_family___:
            cls.generic_record_classes.add(stored_item)
        if RecordFamily.ANTISTASI in record_class.___record_family___:
            if record_class.___function___ is None:
                cls.antistasi_record_classes["DEFAULT"] = stored_item
            elif isinstance(record_class.___function___, tuple):
                for f in record_class.___function___:
                    cls.antistasi_record_classes[f].add(stored_item)
            else:
                cls.antistasi_record_classes[record_class.___function___].add(stored_item)

    def get_by_name(self, name: str) -> RECORD_CLASS_TYPE:
        return self.record_class_registry.get(name, self.default_record_class).concrete_class

    def get_by_id(self, model_id: int) -> RECORD_CLASS_TYPE:
        return self.record_class_registry_by_id.get(str(model_id), self.default_record_class).concrete_class

    def determine_record_class(self, log_record: LogRecord) -> "RecordClass":
        with self.record_class_checker_pool() as record_checker:
            _out = record_checker._determine_record_class(log_record)
        return _out

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
