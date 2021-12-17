"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from playhouse.signals import post_save
from playhouse.shortcuts import model_to_dict
from antistasi_logbook.storage.models.models import GameMap, LogLevel, AntstasiFunction

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.concurrency.events import BlockingEvent

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.storage.database import GidSqliteApswDatabase

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class ForeignKeyCache:
    log_levels_blocker = BlockingEvent()
    game_map_model_blocker = BlockingEvent()
    antistasi_file_model_blocker = BlockingEvent()
    _all_log_levels: dict[str, LogLevel] = None
    _all_log_levels_by_id: dict[int, LogLevel] = None

    _all_antistasi_file_objects: dict[str, AntstasiFunction] = None
    _all_antistasi_file_objects_by_id: dict[str, AntstasiFunction] = None

    _all_game_map_objects: dict[str, GameMap] = None
    _all_game_map_objects_by_id: dict[str, GameMap] = None

    __slots__ = ("update_map", "database")

    def __init__(self, database: "GidSqliteApswDatabase") -> None:
        self.database = database
        self.update_map = {AntstasiFunction: (self.antistasi_file_model_blocker, ("_all_antistasi_file_objects", "_all_antistasi_file_objects_by_id")),
                           GameMap: (self.game_map_model_blocker, ("_all_game_map_objects", "_all_game_map_objects_by_id")),
                           LogLevel: (self.log_levels_blocker, ("_all_log_levels", "_all_log_levels_by_id"))}
        self._register_signals()

    def _register_signals(self) -> None:
        for model_class in self.update_map:
            try:
                post_save.connect(self.on_save_handler, sender=model_class)
            except ValueError:
                continue

    @property
    def all_log_levels(self) -> dict[str, LogLevel]:

        if self.__class__._all_log_levels is None:
            self.log_levels_blocker.wait()
            self.__class__._all_log_levels = {log_level.name: log_level for log_level in self.database.get_all_log_levels()}

        return self.__class__._all_log_levels

    @property
    def all_antistasi_file_objects(self) -> dict[str, AntstasiFunction]:

        if self.__class__._all_antistasi_file_objects is None:
            self.antistasi_file_model_blocker.wait()
            self.__class__._all_antistasi_file_objects = {antistasi_file.name: antistasi_file for antistasi_file in self.database.get_all_antistasi_functions()}

        return self.__class__._all_antistasi_file_objects

    @property
    def all_game_map_objects(self) -> dict[str, GameMap]:

        if self.__class__._all_game_map_objects is None:
            self.game_map_model_blocker.wait()
            self.__class__._all_game_map_objects = {game_map.name: game_map for game_map in self.database.get_all_game_maps()}

        return self.__class__._all_game_map_objects

    @property
    def all_log_levels_by_id(self) -> dict[str, LogLevel]:

        if self.__class__._all_log_levels_by_id is None:
            self.log_levels_blocker.wait()
            self.__class__._all_log_levels_by_id = {log_level.id: log_level for log_level in self.database.get_all_log_levels()}

        return self.__class__._all_log_levels_by_id

    @property
    def all_antistasi_file_objects_by_id(self) -> dict[str, AntstasiFunction]:

        if self.__class__._all_antistasi_file_objects_by_id is None:
            self.antistasi_file_model_blocker.wait()
            self.__class__._all_antistasi_file_objects_by_id = {str(antistasi_file.id): antistasi_file for antistasi_file in self.database.get_all_antistasi_functions()}

        return self.__class__._all_antistasi_file_objects_by_id

    @property
    def all_game_map_objects_by_id(self) -> dict[str, GameMap]:

        if self.__class__._all_game_map_objects_by_id is None:
            self.game_map_model_blocker.wait()
            self.__class__._all_game_map_objects_by_id = {str(game_map.id): game_map for game_map in self.database.get_all_game_maps()}

        return self.__class__._all_game_map_objects_by_id

    def get_log_level_by_id(self, model_id: int) -> Optional[LogLevel]:
        if model_id is None:
            return None
        return self.all_log_levels_by_id.get(model_id)

    def get_antistasi_file_by_id(self, model_id: int) -> Optional[AntstasiFunction]:
        if model_id is None:
            return None
        return self.all_antistasi_file_objects_by_id.get(str(model_id))

    def get_game_map_by_id(self, model_id: int) -> Optional[GameMap]:
        if model_id is None:
            return None
        return self.all_game_map_objects_by_id.get(str(model_id))

    def reset_all(self) -> None:
        self.__class__._all_log_levels = None
        self.__class__._all_antistasi_file_objects = None
        self.__class__._all_game_map_objects = None
        self.__class__._all_log_levels_by_id = None
        self.__class__._all_antistasi_file_objects_by_id = None
        self.__class__._all_game_map_objects_by_id = None
        log.info("all cached foreign keys were reseted.")

    def on_save_handler(self, sender, instance, created):
        if created:
            event, class_attr_names = self.update_map.get(sender, (None, None))
            if event is None:
                return
            with event:
                for attr_name in class_attr_names:
                    setattr(self.__class__, attr_name, None)
            log.warning(" reseted %r, because %r of %r was created: %r", class_attr_names, model_to_dict(instance, recurse=False), sender.__name__, created)
        else:
            log.debug(" reseted, because %r of %r was created: %r", model_to_dict(instance, recurse=False), sender.__name__, created)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
