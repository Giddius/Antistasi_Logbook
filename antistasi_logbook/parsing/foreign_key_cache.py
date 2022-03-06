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

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.concurrency.events import BlockingEvent

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import GameMap, Version, LogLevel, RecordOrigin, ArmaFunction

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
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
    """
    Stores contents of auxilliary tables that do not change often.

    Listens to changes on those tables and updates itself lazily if necessary.

    Is Thread-safe.

    Should only be auto-instantiated by the Backend.

    Args:
        backend (`Backend`) = The current Backend instance.
    """

    log_levels_blocker = BlockingEvent()
    game_map_model_blocker = BlockingEvent()
    arma_file_model_blocker = BlockingEvent()
    origin_blocker = BlockingEvent()
    version_blocker = BlockingEvent()

    _all_log_levels: dict[str, LogLevel] = None
    _all_log_levels_by_id: dict[int, LogLevel] = None

    _all_arma_file_objects: dict[tuple[str, str], ArmaFunction] = None
    _all_arma_file_objects_by_id: dict[str, ArmaFunction] = None

    _all_game_map_objects: dict[str, GameMap] = None
    _all_game_map_objects_by_id: dict[str, GameMap] = None

    _all_origin_objects: dict[str, RecordOrigin] = None
    _all_origin_objects_by_id: dict[str, RecordOrigin] = None

    _all_version_objects: dict[str, Version] = None
    _all_version_objects_by_id: dict[str, Version]

    __slots__ = ("update_map", "database")

    def __init__(self, database: "GidSqliteApswDatabase") -> None:
        self.database = database
        self.update_map = {ArmaFunction: (self.arma_file_model_blocker, ("_all_arma_file_objects", "_all_arma_file_objects_by_id")),
                           GameMap: (self.game_map_model_blocker, ("_all_game_map_objects", "_all_game_map_objects_by_id")),
                           LogLevel: (self.log_levels_blocker, ("_all_log_levels", "_all_log_levels_by_id")),
                           RecordOrigin: (self.origin_blocker, ("_all_origin_objects", "_all_origin_objects_by_id")),
                           Version: (self.version_blocker, ("_all_version_objects", "_all_version_objects_by_id"))}
        self._register_signals()

    def _register_signals(self) -> None:
        """
        Registers the Change signals of the Models with the method that invalidates the specific cache.

        """
        for model_class in self.update_map:
            try:
                post_save.connect(self._on_save_handler, sender=model_class)
            except ValueError:
                continue

    @property
    def all_log_levels(self) -> dict[str, LogLevel]:

        if self.__class__._all_log_levels is None:
            self.log_levels_blocker.wait()
            self.__class__._all_log_levels = {log_level.name: log_level for log_level in self.database.get_all_log_levels()}

        return self.__class__._all_log_levels

    @property
    def all_arma_file_objects(self) -> dict[tuple[str, str], ArmaFunction]:

        if self.__class__._all_arma_file_objects is None:
            log.debug("all_arma_file_objects is None")
            self.arma_file_model_blocker.wait()
            self.__class__._all_arma_file_objects = {(antistasi_file.name, antistasi_file.author_prefix.name): antistasi_file for antistasi_file in self.database.get_all_arma_functions()}

        return self.__class__._all_arma_file_objects

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
    def all_arma_file_objects_by_id(self) -> dict[str, ArmaFunction]:

        if self.__class__._all_arma_file_objects_by_id is None:
            log.debug("all_arma_file_objects_by_id is None")

            self.arma_file_model_blocker.wait()
            self.__class__._all_arma_file_objects_by_id = {str(antistasi_file.id): antistasi_file for antistasi_file in self.database.get_all_arma_functions()}

        return self.__class__._all_arma_file_objects_by_id

    @property
    def all_game_map_objects_by_id(self) -> dict[str, GameMap]:

        if self.__class__._all_game_map_objects_by_id is None:
            self.game_map_model_blocker.wait()
            self.__class__._all_game_map_objects_by_id = {str(game_map.id): game_map for game_map in self.database.get_all_game_maps()}

        return self.__class__._all_game_map_objects_by_id

    @property
    def all_origin_objects(self) -> dict[str, RecordOrigin]:
        if self.__class__._all_origin_objects is None:
            self.origin_blocker.wait()
            self.__class__._all_origin_objects = {origin.identifier: origin for origin in self.database.get_all_origins()}
            for origin in self.__class__._all_origin_objects.values():
                _ = origin.record_family
        return self.__class__._all_origin_objects

    @property
    def all_origin_objects_by_id(self) -> dict[str, RecordOrigin]:
        if self.__class__._all_origin_objects_by_id is None:
            self.origin_blocker.wait()
            self.__class__._all_origin_objects_by_id = {str(origin.id): origin for origin in self.database.get_all_origins()}
            for origin in self.__class__._all_origin_objects_by_id.values():
                _ = origin.record_family
        return self.__class__._all_origin_objects_by_id

    @property
    def all_version_objects(self) -> dict[str, Version]:
        if self.__class__._all_version_objects is None:
            self.version_blocker.wait()
            self.__class__._all_version_objects = {str(version): version for version in self.database.get_all_versions()}
        return self.__class__._all_version_objects

    @property
    def all_version_objects_by_id(self) -> dict[str, Version]:
        if self.__class__._all_version_objects_by_id is None:
            self.version_blocker.wait()
            self.__class__._all_version_objects_by_id = {str(version.id): Version for version in self.database.get_all_versions()}
        return self.__class__._all_version_objects_by_id

    def get_log_level_by_id(self, model_id: int) -> Optional[LogLevel]:

        return self.all_log_levels_by_id.get(model_id)

    def get_arma_file_by_id(self, model_id: int) -> Optional[ArmaFunction]:

        return self.all_arma_file_objects_by_id.get(str(model_id))

    def get_game_map_by_id(self, model_id: int) -> Optional[GameMap]:

        return self.all_game_map_objects_by_id.get(str(model_id))

    def get_origin_by_id(self, model_id: int) -> Optional[RecordOrigin]:
        return self.all_origin_objects_by_id.get(str(model_id))

    def get_version_by_id(self, model_id: int) -> Optional[Version]:
        return self.all_version_objects_by_id.get(str(model_id))

    def reset_all(self) -> None:
        """
        Invalidate each cache.

        """
        self.__class__._all_log_levels = None
        self.__class__._all_arma_file_objects = None
        self.__class__._all_game_map_objects = None
        self.__class__._all_log_levels_by_id = None
        self.__class__._all_arma_file_objects_by_id = None
        self.__class__._all_game_map_objects_by_id = None
        self.__class__._all_origin_objects = None
        self.__class__._all_origin_objects_by_id = None
        self.__class__._all_version_objects = None
        self.__class__._all_version_objects_by_id = None
        log.info("all cached foreign keys were reseted.")

    def preload_all(self) -> None:
        _ = self.all_log_levels
        _ = self.all_arma_file_objects
        _ = self.all_game_map_objects
        _ = self.all_log_levels_by_id
        _ = self.all_arma_file_objects_by_id
        _ = self.all_game_map_objects_by_id
        _ = self.all_origin_objects
        _ = self.all_origin_objects_by_id
        _ = self.all_version_objects
        _ = self.all_version_objects_by_id
        log.info("all cached foreign keys preloaded.")

    def _on_save_handler(self, sender, instance, created):
        """
        Invalidates the cache of the Model that was changed.

        Handles the Models, `post_save`-Signal.


        """
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
