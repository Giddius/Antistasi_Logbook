"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING, Union
from pathlib import Path
from threading import RLock
from collections import defaultdict

# * Third Party Imports --------------------------------------------------------------------------------->
import attr
from frozendict import frozendict
from sortedcontainers import SortedSet

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.base_record import BaseRecord, RecordFamily
from antistasi_logbook.parsing.py_raw_record import RawRecord
from antistasi_logbook.storage.models.models import LogRecord, RecordClass
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend, GidSqliteApswDatabase

# endregion [Imports]

# region [TODO]

# TODO: Make record-class checking available with LogRecords, RawRecords and just a Record-dict

# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion [Constants]

RECORD_CLASS_TYPE = Union[type[BaseRecord], type["BaseRecord"]]


@attr.s(auto_attribs=True, auto_detect=True, frozen=True, slots=True, weakref_slot=True)
class StoredRecordClass:
    concrete_class: RECORD_CLASS_TYPE = attr.ib()
    model: RecordClass = attr.ib()

    def check(self, log_record: "LogRecord") -> bool:
        return self.concrete_class.check(log_record=log_record)


def new_sorted_set() -> SortedSet:
    return SortedSet(key=lambda x: -x.concrete_class.___specificity___)


class RecordClassChecker:
    __slots__ = ("default_record_class", "generic_record_classes", "antistasi_record_classes", "family_handler_table", "cache")

    def __init__(self, default_record_class: StoredRecordClass, generic_record_classes: SortedSet[StoredRecordClass], antistasi_record_classes: dict[str, Union[SortedSet[StoredRecordClass], StoredRecordClass]]) -> None:

        self.default_record_class = default_record_class
        self.generic_record_classes = generic_record_classes
        self.antistasi_record_classes = frozendict(**antistasi_record_classes)
        self.family_handler_table = frozendict({RecordFamily.GENERIC: self._determine_generic_record_class,
                                                RecordFamily.ANTISTASI: self._determine_antistasi_record_class})

    def _determine_generic_record_class(self, log_record: LogRecord) -> "RecordClass":
        for stored_class in self.generic_record_classes:
            if stored_class.concrete_class.check(log_record) is True:
                return stored_class.model

    def _determine_antistasi_record_class(self, log_record: LogRecord) -> "RecordClass":
        try:
            function_name = log_record.logged_from.function_name
        except AttributeError:
            function_name = log_record.parsed_data.get("logged_from").function_name
        try:

            sub_set = self.antistasi_record_classes[function_name]
            for stored_class in sub_set:
                if stored_class.concrete_class.check(log_record) is True:
                    return stored_class.model
        except KeyError:
            pass

        return self.antistasi_record_classes["DEFAULT"].model

    def _determine_record_class(self, log_record: LogRecord) -> "RecordClass":

        if log_record is None:
            log.critical("Log record %r is None", log_record)
            return
        try:
            origin = log_record.origin.record_family
        except AttributeError:
            origin = log_record.record_origin.record_family
        record_class = self.family_handler_table.get(origin, self._determine_generic_record_class)(log_record)
        if record_class is None:
            _out = self.default_record_class.model
        else:
            _out = record_class
        if isinstance(log_record, RawRecord):
            log_record.record_class = _out

        return _out


class RecordClassManager:
    __slots__ = ("backend", "foreign_key_cache", "_default_record_concrete_class", "_default_record_class", "family_handler_table", "_record_class_checker", "_is_set_up")
    record_class_registry: dict[str, StoredRecordClass] = {}
    record_class_registry_by_id: dict[str, StoredRecordClass] = {}
    generic_record_classes: SortedSet[StoredRecordClass] = SortedSet(key=lambda x: -x.concrete_class.___specificity___)
    antistasi_record_classes: dict[str, Union[SortedSet, StoredRecordClass]] = defaultdict(new_sorted_set)
    _default_record_class_lock = RLock()
    _register_lock = RLock()

    def __init__(self, backend: "Backend", foreign_key_cache: "ForeignKeyCache", default_record_class: RECORD_CLASS_TYPE = None) -> None:
        self.backend = backend
        self.foreign_key_cache = foreign_key_cache
        BaseRecord.foreign_key_cache = self.foreign_key_cache
        self._default_record_concrete_class = BaseRecord if default_record_class is None else default_record_class
        self._default_record_class: "StoredRecordClass" = None

        self._record_class_checker: RecordClassChecker = None
        self._is_set_up: bool = False

    @property
    def record_class_checker(self) -> RecordClassChecker:

        if self._record_class_checker is None:
            self.create_record_checker()
        return self._record_class_checker

    def create_record_checker(self) -> RecordClassChecker:

        if self._record_class_checker is None:
            self._record_class_checker = RecordClassChecker(default_record_class=self.default_record_class,
                                                            generic_record_classes=tuple(self.generic_record_classes.copy()),
                                                            antistasi_record_classes=self.antistasi_record_classes.copy())
        return self._record_class_checker

    def get_record_checker(self) -> RecordClassChecker:

        while self._is_set_up is False:
            log.debug("waiting for %r '_is_set_up' to turn True (now: %r)", self, self._is_set_up)
            sleep(0.5)
        checker = RecordClassChecker(default_record_class=self.default_record_class,
                                     generic_record_classes=tuple(self.generic_record_classes.copy()),
                                     antistasi_record_classes=self.antistasi_record_classes.copy())
        return checker

    @property
    def default_record_class(self) -> StoredRecordClass:
        with self._default_record_class_lock:
            if self._default_record_class is None:
                model = RecordClass.get_or_create(name=self._default_record_concrete_class.__name__)[0]

                self._default_record_class = StoredRecordClass(self._default_record_concrete_class, model)
        return self._default_record_class

    @classmethod
    def register_record_class(cls, record_class: RECORD_CLASS_TYPE, database: "GidSqliteApswDatabase") -> None:
        with cls._register_lock:
            name = record_class.__name__
            if name in cls.record_class_registry:
                return

            model = RecordClass.get_or_create(name=name)[0]

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

    def get_model_by_id(self, model_id: int) -> RecordClass:

        return self.record_class_registry_by_id.get(str(model_id), self.default_record_class).model

    def determine_record_class(self, log_record: LogRecord) -> tuple["RECORD_CLASS_TYPE", LogRecord]:

        return self.record_class_checker._determine_record_class(log_record), log_record

    def reset(self) -> None:
        self._default_record_class = None
        self._record_class_checker = self.get_record_checker()
# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
