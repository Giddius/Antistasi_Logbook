"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import json
import inspect
import shutil
from typing import TYPE_CHECKING
from pathlib import Path
from collections import Counter
import zipfile
# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtWidgets import QStyle, QWidget, QGridLayout, QPushButton, QApplication
from statistics import mean, stdev, median, median_grouped
# * Third Party Imports --------------------------------------------------------------------------------->
import apsw
from peewee import Model, fn, prefetch
from concurrent.futures import Future, wait, ThreadPoolExecutor, ALL_COMPLETED
from playhouse.shortcuts import model_to_dict
from tempfile import TemporaryDirectory, tempdir
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.meta_data.interface import MetaPaths, get_meta_paths
from gidapptools.general_helper.conversion import bytes2human
from gidapptools.general_helper.timing import time_func

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Mod, ModSet, LogFile, Message, RecordClass, OriginalLogFile, LogLevel, BaseModel, LogRecord, GameMap, ArmaFunction, DatabaseMetaData, ArmaFunctionAuthorPrefix, MeanUpdateTimePerLogFile
from antistasi_logbook.gui.widgets.debug_widgets import DebugDockWidget, ListOfDictsResult

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.storage.database import GidSqliteApswDatabase

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
META_PATHS: MetaPaths = get_meta_paths()
# endregion [Constants]


def disable(in_func):
    in_func.is_disabled = True
    return in_func


def show_parser_argument_full_text_data(argument_index: int):
    parser_argument = QApplication.instance().argument_doc_items[argument_index]

    return parser_argument.get_html()


def show_parser_usage():
    return QApplication.instance().get_argument_parser().format_usage()


def get_all_widgets():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    _out = {}
    for w in app.allWidgets():

        _out[str(w)] = w.metaObject().className()

    return _out


def get_all_windows():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    return {str(i): i for i in app.allWindows()}


def do_incremental_vacuum():
    def _vac_func(*args, **kwargs):
        log.debug("%r || %r", args, kwargs)
        return 100
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database

    cur: apsw.Cursor = db.cursor()
    cur.execute("PRAGMA auto_vacuum(2);")

    conn: apsw.Connection = cur.getconnection()

    conn.autovacuum_pages(None)
    result = conn.changes()
    cur.close()
    return result


def show_average_file_size_per_log_file():
    raw = DatabaseMetaData.get_average_size_per_log_file()
    return bytes2human(raw)


@time_func(output=log.info)
def show_amount_messages_compared_to_amount_records():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    db.connect(True)

    amount_messages = db.connection().execute('SELECT COUNT("md5_hash") from "Message"').fetchone()[0]

    amount_records = db.connection().execute('SELECT COUNT(*) from "LogRecord"').fetchone()[0]

    if amount_records == 0:
        factor = None
    else:
        factor = round(amount_messages / amount_records, ndigits=3)
    return {"messages": amount_messages, "records": amount_records, "messages/record": factor}


def get_longest_message():
    from pympler import asizeof
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    _out_file = META_PATHS.debug_dump_dir.joinpath("longest_messages.txt")
    with db.atomic():
        longest_messages = (i[0] for i in Message.select(Message.text).distinct().order_by(fn.LENGTH(Message.text).desc()).limit(500).tuples().iterator())
        _out = {len(str(longest_message)): str(longest_message) for longest_message in longest_messages}
    with _out_file.open("w", encoding='utf-8', errors='ignore') as f:
        for k, v in _out.items():
            f.write(("#" * 25) + f" lenght: {k!r}  |  size: {bytes2human(asizeof.asizeof(v))}\n\n\n")
            f.write(str(v) + '\n\n\n')
            f.write(("+" * 50) + '\n\n')
    return _out


def most_common_messages():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database

    # with db.atomic():
    #     counter = Counter(i[0] for i in LogRecord.select(Message.text).join_from(LogRecord, Message, on=(LogRecord.message_item == Message.md5_hash)).tuples().iterator())

    # most_common = [{"amount": i[1], "text": i[0]} for i in counter.most_common() if int(i[1]) >= 10_000]
    phrase = """
SELECT "_text","_amount" FROM (
SELECT "t1"."text" AS "_text", COUNT("t1"."text") AS "_amount" FROM "LogRecord" AS "t2" INNER JOIN "Message" AS "t1" ON ("t2"."message_item" = "t1"."md5_hash")
GROUP BY "t1"."text"
ORDER BY "_amount" DESC)
WHERE "_amount">9500
    """.strip()

    _out_file = META_PATHS.debug_dump_dir.joinpath("most_common_messages.txt")
    _out_file_json = META_PATHS.debug_dump_dir.joinpath("message.json")
#     phrase = """
# SELECT "t1"."text" AS "text", COUNT("t1"."text") AS "amount" FROM "LogRecord" AS "t2" INNER JOIN "Message" AS "t1" ON ("t2"."message_item" = "t1"."md5_hash") GROUP BY "t1"."text" ORDER BY "amount" DESC
# """.strip()
    _out = []
    most_common = []
    idx = 0

    cursor: apsw.Cursor = db.connection().execute(phrase)

    with _out_file.open("w", encoding='utf-8', errors='ignore') as f:
        with _out_file_json.open("w", encoding='utf-8', errors='ignore') as f_json:

            for text, amount in cursor:
                idx += 1
                if idx % 10 == 0 or idx == 1:
                    log.debug("dumped %r of the most common messages", idx)

                text = Message.text.python_value(text)
                most_common.append({"amount": amount, "text": text})
                f.write(f'{amount:<10} {text!r}\n\n{"-"*50}\n\n')
                _out.append({"md5_hash": Message.hash_text(text), "text": text})

            for item_hash, item in db.most_common_messages.items():
                if item_hash not in {i["md5_hash"] for i in _out}:
                    _out.append({"md5_hash": item.md5_hash, "text": item.text})
            json.dump(_out[:100], f_json, default=str, indent=4, sort_keys=True)
    return most_common


def show_database_file_size():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    raw = db.database_file_size
    return bytes2human(raw)


def mod_hash_lengths():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        counter = Counter(i[0] for i in Mod.select(fn.length(Mod.mod_hash)).tuples().iterator())

    return {f"length {i[0]}": f"amount {i[1]}" for i in counter.most_common()}


def mod_hash_short_lengths():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        counter = Counter(i[0] for i in Mod.select(fn.length(Mod.mod_hash_short)).tuples().iterator())

    return {f"length {i[0]}": f"amount {i[1]}" for i in counter.most_common()}


def mod_dir_lengths():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        counter = Counter(i[0] for i in Mod.select(fn.length(Mod.mod_dir)).tuples().iterator())

    _out = list(counter.most_common())
    _out = sorted(_out, key=lambda x: int(x[0]), reverse=True)
    return {f"length {l}": f"amount {a}" for l, a in _out}


def mod_name_lengths():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        counter = Counter(i[0] for i in Mod.select(fn.length(Mod.name)).tuples().iterator())

    _out = list(counter.most_common())
    _out = sorted(_out, key=lambda x: int(x[0]), reverse=True)
    return {f"length {l}": f"amount {a}" for l, a in _out}


def mod_full_path_lengths():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        counter = Counter(len(i[0].as_posix()) for i in Mod.select(Mod.full_path).where((Mod.full_path != None)).tuples().iterator())

    _out = list(counter.most_common())
    _out = sorted(_out, key=lambda x: int(x[0]), reverse=True)
    return {f"length {l}": f"amount {a}" for l, a in _out}


def message_text_lengths():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        counter = Counter(i[0] for i in Message.select(fn.length(Message.text)).tuples().iterator())

    _out = list(counter.most_common())
    _out = sorted(_out, key=lambda x: int(x[0]), reverse=True)
    return {f"length {l}": f"amount {a}" for l, a in _out}


def show_screens_output():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    _out = {}
    for idx, screen in enumerate(app.screens()):
        screen_data = {"index": idx,
                       "model": screen.model(),
                       "manufacturer": screen.manufacturer(),
                       "orientation": screen.orientation(),
                       "physical_size": screen.physicalSize(),
                       "refresh_rate": screen.refreshRate(),
                       "serial_number": screen.serialNumber(),
                       "depth": screen.depth(),
                       "geometry": screen.geometry()}
        _out[screen.name()] = screen_data

    return _out


def release_memory():
    return apsw.releasememory(1_000_000)


def show_mean_update_time_per_log_file():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database

    return str(round(db.session_meta_data.mean_update_time_per_log_file.total_seconds(), ndigits=3)) + ' seconds'


def dump_arma_functions():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    author_prefix_data = []
    function_data = []
    function_data_out_file = META_PATHS.debug_dump_dir.joinpath("armafunction.json")
    author_prefix_data_out_file = META_PATHS.debug_dump_dir.joinpath("armafunctionauthorprefix.json")

    with db.connection_context() as ctx:
        for item in ArmaFunctionAuthorPrefix.select(ArmaFunctionAuthorPrefix.name, ArmaFunctionAuthorPrefix.full_name).dicts().iterator():

            author_prefix_data.append(item)
        for item in ArmaFunction.select(ArmaFunction, ArmaFunctionAuthorPrefix).join_from(ArmaFunction, ArmaFunctionAuthorPrefix).iterator():
            item_data = model_to_dict(item, exclude=[ArmaFunction.id,
                                                     ArmaFunctionAuthorPrefix.id,
                                                     ArmaFunction.marked,
                                                     ArmaFunctionAuthorPrefix.marked,
                                                     ArmaFunction.comments,
                                                     ArmaFunctionAuthorPrefix.comments,
                                                     ArmaFunctionAuthorPrefix.local_folder_path,
                                                     ArmaFunctionAuthorPrefix.github_link,
                                                     ArmaFunction.local_path,
                                                     ArmaFunction.link])
            function_data.append(item_data)

    with function_data_out_file.open("w", encoding='utf-8', errors='ignore') as f:
        json.dump(function_data, f, default=str, sort_keys=False, indent=4)
    with author_prefix_data_out_file.open("w", encoding='utf-8', errors='ignore') as f:
        json.dump(author_prefix_data, f, default=str, sort_keys=False, indent=4)

    return True


def dump_most_common_messages():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    data = []
    with db.connection_context() as ctx:
        for item in db.most_common_messages.values():
            data.append(model_to_dict(item, exclude=[Message.id]))

    _out_file = META_PATHS.debug_dump_dir.joinpath("message.json")
    with _out_file.open("w", encoding='utf-8', errors='ignore') as f:
        json.dump(data, f, default=str, sort_keys=False, indent=4)
    return True


def dump_mod_sets():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    data = []
    with db.connection_context() as ctx:
        for item in ModSet.select().iterator():
            data.append(model_to_dict(item, exclude=[ModSet.id]))

    _out_file = META_PATHS.debug_dump_dir.joinpath("modset.json")
    with _out_file.open("w", encoding='utf-8', errors='ignore') as f:
        json.dump(data, f, default=str, sort_keys=False, indent=4)
    return True


def show_all_models():

    def _meta_to_dict(in_meta):
        names_to_exclude = {"__doc__",
                            "__module__",
                            "__str__",
                            "__repr__",
                            "__getattribute__",
                            "__getattr__",
                            "__delattr__",
                            "__delitem__",
                            "__delslice__",
                            "__setattr__",
                            "__setitem__",
                            "__setslice__",
                            "__missing__",
                            "__getitem__",
                            "__getslice__",
                            "__eq__",
                            "__ge__",
                            "__gt__",
                            "__le__",
                            "__ne__",
                            "__lt__",
                            "__hash__",
                            "__add__",
                            "__and__",
                            "__divmod__",
                            "__floordiv__",
                            "__lshift__",
                            "__matmul__",
                            "__mod__",
                            "__mul__",
                            "__or__",
                            "__pow__",
                            "__rshift__",
                            "__sub__",
                            "__truediv__",
                            "__xor__",
                            "__radd__",
                            "__rand__",
                            "__rdiv__",
                            "__rdivmod__",
                            "__rfloordiv__",
                            "__rlshift__",
                            "__rmatmul__",
                            "__rmod__",
                            "__rmul__",
                            "__ror__",
                            "__rpow__",
                            "__rrshift__",
                            "__rsub__",
                            "__rtruediv__",
                            "__rxor__",
                            "__iadd__",
                            "__iand__",
                            "__ifloordiv__",
                            "__ilshift__",
                            "__imatmul__",
                            "__imod__",
                            "__imul__",
                            "__ior__",
                            "__ipow__",
                            "__irshift__",
                            "__isub__",
                            "__itruediv__",
                            "__ixor__",
                            "__abs__",
                            "__neg__",
                            "__pos__",
                            "__invert__",
                            "__index__",
                            "__trunc__",
                            "__floor__",
                            "__ceil__",
                            "__round__",
                            "__iter__",
                            "__reversed__",
                            "__contains__",
                            "__next__",
                            "__int__",
                            "__bool__",
                            "__nonzero__",
                            "__complex__",
                            "__float__",
                            "__format__",
                            "__cmp__",
                            "__enter__",
                            "__exit__",
                            "__aenter__",
                            "__aexit__",
                            "__aiter__",
                            "__anext__",
                            "__await__",
                            "__call__",
                            "__class__",
                            "__dir__",
                            "__init__",
                            "__init_subclass__",
                            "__prepare__",
                            "__len__",
                            "__new__",
                            "__subclasses__",
                            "__instancecheck__",
                            "__subclasscheck__",
                            "__class_getitem__",
                            "__import__",
                            "__bytes__",
                            "__fspath__",
                            "__getnewargs__",
                            "__reduce__f",
                            "__reduce__",
                            "__reduce_ex__",
                            "__sizeof__",
                            "__length_hint__",
                            "__dict__",
                            "__slots__",
                            "__subclasshook__",
                            "__weakref__"}

        names_to_get = {"fields", "indexes", "columns", "constraints", "schema", "table_settings", "_db_hooks", "options"}
        _out = {"other_names": {}}

        def _exclude_descriptor(in_o: object):
            return all(check(in_o) is False for check in [inspect.isgetsetdescriptor, inspect.isdatadescriptor, inspect.ismethoddescriptor, inspect.isfunction, inspect.ismethod, inspect.ismemberdescriptor])

        for _name, _value in inspect.getmembers(in_meta):

            if _name in names_to_exclude:
                continue
            if _name not in names_to_get:
                _out["other_names"][_name] = {"is_method": inspect.ismethod(_value) or inspect.isfunction(_value), "is_descriptor": inspect.isdatadescriptor(_value)}
                continue
            _out[_name] = _value

        return _out
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    data = []
    for model in db._base_model.get_all_models(False):
        model: Model
        m_data = {"name": model.__name__,
                  "meta": _meta_to_dict(model._meta),
                  "table_exists": model.table_exists(),
                  "amount": len(model)}
        data.append(m_data)
    return ListOfDictsResult(data)


class CopyPushButton(QPushButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pressed.connect(self.copy_data)

    def copy_data(self):
        app: "AntistasiLogbookApplication" = QApplication.instance()
        clipboard = app.clipboard()
        text = f"{self.text()}"
        clipboard.setText(text)


def show_default_icons():
    app: "AntistasiLogbookApplication" = QApplication.instance()

    icons = sorted([attr for attr in dir(QStyle.StandardPixmap) if attr.startswith("SP_")])
    layout = QGridLayout()
    for n, name in enumerate(icons):
        label = CopyPushButton(name)

        pixmapi = getattr(QStyle.StandardPixmap, name)
        icon = app.style().standardIcon(pixmapi)
        label.setIcon(icon)
        layout.addWidget(label, n / 4, n % 4)
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def check_query_object_method():

    def _fake_constructor(*args, **kwargs):
        log.debug("name: %r", kwargs.get("message"))
        log.debug("name: %r", kwargs.get("message_item"))

        log.debug("------------")
        return kwargs
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database

    query = LogRecord.select().limit(1).objects(_fake_constructor).iterator()

    return list(query)[0]


def check_some_model_data():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database

    def get_unique_columns(in_model: BaseModel):

        _out = {"unique_columns": [], "unique_indexes": [], "options": None, "table_settings": None, "combined": None}

        for c in in_model.get_meta().sorted_fields:
            if c.unique is True:
                _out["unique_columns"].append(c)

        for ind in in_model.get_meta().indexes:
            if ind[-1] is True:
                _out["unique_indexes"].append(ind)

        _out["options"] = in_model.get_meta().options
        _out["table_settings"] = in_model.get_meta().table_settings
        _out["combined"] = in_model.get_meta().combined

        return _out

    return {m.__name__: get_unique_columns(m) for m in db._base_model.get_all_models()}


def show_and_dump_meta_attrs():
    model = LogFile
    data = [i for i in dir(model.get_meta()) if not i.startswith("__")]
    with META_PATHS.debug_dump_dir.joinpath("meta_attrs.json").open("w", encoding='utf-8', errors='ignore') as f:
        json.dump(data, f, default=str, indent=4)

    return data


def count_error_records_by_group():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database

    query = """SELECT lr.log_file ,COUNT()  FROM LogRecord lr WHERE lr.log_level == 5 GROUP BY lr.log_file"""
    conn: apsw.Connection = db.connection()
    result = conn.execute(query).fetchall()

    return {LogFile.get_by_id(i[0]).name: i[1] for i in result}


def count_records_by_group():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database

    query = """SELECT lr.log_file ,COUNT()  FROM LogRecord lr GROUP BY lr.log_file"""
    conn: apsw.Connection = db.connection()
    result = conn.execute(query).fetchall()

    return {LogFile.get_by_id(i[0]).name: i[1] for i in result}


def all_update_durations():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database
    data = []
    with db.connection_context():
        for item in MeanUpdateTimePerLogFile.select().order_by(-MeanUpdateTimePerLogFile.recorded_at).iterator():
            data.append({"recorded_at": item.recorded_at.strftime("%Y-%m-%d %H:%M:%S"), "time_taken_per_log_file": round(item.time_taken_per_log_file, ndigits=2), "amount_updated": item.amount_updated, "overall_time_taken": round(item.time_taken_per_log_file * item.amount_updated, ndigits=2)})

    return data


def show_cache_stats():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database

    conn: apsw.Connection = db.connection()
    return conn.cache_stats(include_entries=True)


def show_message_hash_stats():
    from pympler import asizeof
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database
    with db.connection_context():
        log.debug("starting collecting all text-hashes")
        all_hashes = {m[0] for m in Message.select(Message.md5_hash).tuples().iterator()}
        log.debug("finished collecting all text-hashes")
    log.debug("starting calculating size of all text-hashes")
    size = asizeof.asizeof(all_hashes)
    log.debug("finished calculating size of all text-hashes")

    log.debug("starting calculating amount of all text-hashes")
    amount = len(all_hashes)
    log.debug("finished calculating amount of all text-hashes")

    log.debug("returning stats about all text-hashes")
    return {"raw_size": size, "size": bytes2human(size), "amount": amount}


def show_map_coords():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database
    with db.connection_context():
        all_maps = tuple(i for i in GameMap.select().iterator())

        _out = []
        for game_map in all_maps:
            _out.append({"name": game_map.name,
                         "coords": game_map.coordinates})
    return _out


def get_upsmon_init_time():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database
    with db.connection_context():
        all_log_files = tuple(i for i in LogFile.select().where(LogFile.unparsable != True).order_by(LogFile.server_id, -LogFile.created_at).iterator())

    _out = []
    all_durations = []
    for log_file in all_log_files:
        try:
            upsmon_started = LogRecord.select(LogRecord.recorded_at).join(Message).where((LogRecord.log_file_id == log_file.id) & (LogRecord.message_item.text == "UPSMON init started")).limit(1).tuples()[0][0]
            upsmon_ended = LogRecord.select(LogRecord.recorded_at).join(Message).where((LogRecord.log_file_id == log_file.id) & (LogRecord.message_item.text == "Background init completed")).limit(1).tuples()[0][0]
            _out.append({"log_file": log_file.name, "server": log_file.server.name, "seconds": (upsmon_ended - upsmon_started).total_seconds(), "started": upsmon_started.isoformat(), "ended": upsmon_ended.isoformat()})
            all_durations.append((upsmon_ended - upsmon_started).total_seconds())
        except IndexError:
            pass

    mean_duration = mean(all_durations)
    std_dev_duration = stdev(all_durations)
    median_duration = median(all_durations)
    median_grouped_duration = median_grouped(all_durations)
    _out_file = META_PATHS.debug_dump_dir.joinpath("upsmon_init_times.json")
    with _out_file.open("w", encoding='utf-8', errors='ignore') as f:
        _out = {"mean_seconds": mean_duration,
                "median_seconds": median_duration,
                "median_grouped": median_grouped_duration,
                "stdev_seconds": std_dev_duration,
                "items": _out}
        json.dump(_out, f, indent=4, default=str)
    return _out


def show_db_file_names():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database

    return db.connection().db_filename("main")


def get_all_flag_capture_completed_records():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database

    record_class = RecordClass.get(name="FlagCaptureCompleted")
    query = prefetch(LogRecord.select(LogRecord, LogFile).join_from(LogRecord, LogFile).where((LogFile.campaign_id == 85576) & (LogRecord.record_class_id == record_class.id)), LogFile, RecordClass, Message, LogLevel, ArmaFunction)

    return [i.to_record_class() for i in query]


@time_func(output=log.info)
def export_all_log_files_to_zip():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db: "GidSqliteApswDatabase" = app.backend.database
    with ThreadPoolExecutor() as pool:
        all_files: list[Path] = list(pool.map(lambda x: x.to_file(), list(OriginalLogFile.select().iterator())))
    if not all_files:
        return None
    common_path = all_files[0].parent.parent.resolve()
    dump_folder = META_PATHS.debug_dump_dir.resolve()
    zip_path = dump_folder.joinpath("all_log_files.zip").resolve()

    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_LZMA, allowZip64=True) as zippy:
        for orig_file_path in all_files:
            zippy.write(orig_file_path, orig_file_path.relative_to(common_path))

    return zip_path


def setup_debug_widget(debug_dock_widget: "DebugDockWidget") -> None:
    log.debug("running setup_debug_widget")
    app: AntistasiLogbookApplication = QApplication.instance()
    debug_dock_widget.add_show_attr_button(attr_name="amount_log_records", obj=LogRecord)
    debug_dock_widget.add_show_attr_button(attr_name="amount_log_files", obj=LogFile)
    debug_dock_widget.add_show_attr_button(attr_name="get_amount_meta_data_items", obj=DatabaseMetaData)
    for attr_name in ["applicationVersion",
                      "organizationName",
                      "applicationDisplayName",
                      "desktopFileName",
                      "font",
                      "applicationDirPath",
                      "applicationFilePath",
                      "applicationPid",
                      "arguments",
                      "libraryPaths",
                      "isQuitLockEnabled"]:
        debug_dock_widget.add_show_attr_button(attr_name=attr_name, obj=app)

    debug_dock_widget.add_show_func_result_button(get_all_widgets, "widgets")
    debug_dock_widget.add_show_func_result_button(get_all_windows, "widgets")
    debug_dock_widget.add_show_func_result_button(do_incremental_vacuum, "database")
    debug_dock_widget.add_show_func_result_button(show_average_file_size_per_log_file, "database")
    debug_dock_widget.add_show_func_result_button(show_database_file_size, "database")
    debug_dock_widget.add_show_func_result_button(show_amount_messages_compared_to_amount_records, "database")
    debug_dock_widget.add_show_func_result_button(mod_hash_lengths, "models")
    debug_dock_widget.add_show_func_result_button(mod_hash_short_lengths, "models")
    debug_dock_widget.add_show_func_result_button(mod_dir_lengths, "models")
    debug_dock_widget.add_show_func_result_button(mod_full_path_lengths, "models")
    debug_dock_widget.add_show_func_result_button(show_map_coords, "models")

    debug_dock_widget.add_show_func_result_button(mod_name_lengths, "models")
    debug_dock_widget.add_show_func_result_button(message_text_lengths, "models")
    debug_dock_widget.add_show_func_result_button(get_longest_message, "message")
    debug_dock_widget.add_show_func_result_button(show_screens_output, "gui")
    debug_dock_widget.add_show_func_result_button(most_common_messages, "message")
    debug_dock_widget.add_show_func_result_button(show_message_hash_stats, "message")

    debug_dock_widget.add_show_func_result_button(release_memory, "apsw")
    debug_dock_widget.add_show_func_result_button(show_mean_update_time_per_log_file, "database-meta")
    debug_dock_widget.add_show_func_result_button(all_update_durations, "database-meta")
    debug_dock_widget.add_show_func_result_button(show_cache_stats, "database-meta")
    debug_dock_widget.add_show_func_result_button(show_db_file_names, "database-meta")

    debug_dock_widget.add_show_func_result_button(dump_arma_functions, "setup-data")
    debug_dock_widget.add_show_func_result_button(dump_most_common_messages, "setup-data")
    debug_dock_widget.add_show_func_result_button(dump_mod_sets, "setup-data")
    debug_dock_widget.add_show_func_result_button(show_all_models, "database-meta")
    debug_dock_widget.add_show_func_result_button(show_default_icons, "PySide")
    debug_dock_widget.add_show_func_result_button(check_query_object_method, "models")
    debug_dock_widget.add_show_func_result_button(check_some_model_data, "models")
    debug_dock_widget.add_show_func_result_button(show_and_dump_meta_attrs, "models")
    debug_dock_widget.add_show_func_result_button(count_error_records_by_group, "queries")
    debug_dock_widget.add_show_func_result_button(count_records_by_group, "queries")
    debug_dock_widget.add_show_func_result_button(get_upsmon_init_time, "extra")
    debug_dock_widget.add_show_func_result_button(get_all_flag_capture_completed_records, "records")
    debug_dock_widget.add_show_func_result_button(export_all_log_files_to_zip, "data")

    log.debug("finished setup_debug_widget")


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
