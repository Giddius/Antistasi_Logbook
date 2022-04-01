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
from antistasi_logbook.storage.models.models import GameMap, Version, LogLevel, ArmaFunction, RecordOrigin
from frozendict import frozendict
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
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

    __slots__ = ("update_map",
                 "database",
                 "log_levels_blocker",
                 "game_map_model_blocker",
                 "arma_file_model_blocker",
                 "origin_blocker",
                 "version_blocker",
                 "_all_log_levels",
                 "_all_log_levels_by_id",
                 "_all_arma_file_objects",
                 "_all_arma_file_objects_by_id",
                 "_all_game_map_objects",
                 "_all_game_map_objects_by_id",
                 "_all_origin_objects",
                 "_all_origin_objects_by_id",
                 "_all_version_objects",
                 "_all_version_objects_by_id",
                 "_all_game_map_objects_case_insensitive")

    def __init__(self, database: "GidSqliteApswDatabase") -> None:
        self.log_levels_blocker = BlockingEvent()
        self.game_map_model_blocker = BlockingEvent()
        self.arma_file_model_blocker = BlockingEvent()
        self.origin_blocker = BlockingEvent()
        self.version_blocker = BlockingEvent()

        self._all_log_levels: dict[str, LogLevel] = None
        self._all_log_levels_by_id: dict[int, LogLevel] = None

        self._all_arma_file_objects: dict[tuple[str, str], ArmaFunction] = None
        self._all_arma_file_objects_by_id: dict[str, ArmaFunction] = None

        self._all_game_map_objects: frozendict[str, GameMap] = None
        self._all_game_map_objects_case_insensitive: frozendict[str, GameMap] = None
        self._all_game_map_objects_by_id: dict[str, GameMap] = None

        self._all_origin_objects: dict[str, RecordOrigin] = None
        self._all_origin_objects_by_id: dict[str, RecordOrigin] = None

        self._all_version_objects: dict[str, Version] = None
        self._all_version_objects_by_id: dict[str, Version] = None
        self.database = database
        self.update_map = frozendict({ArmaFunction: (self.arma_file_model_blocker, ("_all_arma_file_objects", "_all_arma_file_objects_by_id")),
                                      GameMap: (self.game_map_model_blocker, ("_all_game_map_objects", "_all_game_map_objects_by_id")),
                                      LogLevel: (self.log_levels_blocker, ("_all_log_levels", "_all_log_levels_by_id")),
                                      RecordOrigin: (self.origin_blocker, ("_all_origin_objects", "_all_origin_objects_by_id")),
                                      Version: (self.version_blocker, ("_all_version_objects", "_all_version_objects_by_id"))})
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

        if self._all_log_levels is None:
            self.log_levels_blocker.wait()
            self._all_log_levels = frozendict({log_level.name: log_level for log_level in self.database.get_all_log_levels()})

        return self._all_log_levels

    @property
    def all_arma_file_objects(self) -> dict[tuple[str, str], ArmaFunction]:

        if self._all_arma_file_objects is None:
            self.arma_file_model_blocker.wait()
            self._all_arma_file_objects = frozendict({(antistasi_file.name, antistasi_file.author_prefix.name): antistasi_file for antistasi_file in self.database.get_all_arma_functions()})

        return self._all_arma_file_objects

    @property
    def all_game_map_objects(self) -> dict[str, GameMap]:

        if self._all_game_map_objects is None:
            self.game_map_model_blocker.wait()
            self._all_game_map_objects = frozendict({game_map.name: game_map for game_map in self.database.get_all_game_maps()})

        return self._all_game_map_objects

    @property
    def all_game_map_objects_case_insensitive(self) -> frozendict[str, GameMap]:
        if self._all_game_map_objects_case_insensitive is None:
            self.game_map_model_blocker.wait()
            self._all_game_map_objects_case_insensitive = frozendict({game_map.name.casefold(): game_map for game_map in self.database.get_all_game_maps()})
        return self._all_game_map_objects_case_insensitive

    @property
    def all_log_levels_by_id(self) -> dict[str, LogLevel]:

        if self._all_log_levels_by_id is None:
            self.log_levels_blocker.wait()
            self._all_log_levels_by_id = frozendict({log_level.id: log_level for log_level in self.database.get_all_log_levels()})

        return self._all_log_levels_by_id

    @property
    def all_arma_file_objects_by_id(self) -> dict[str, ArmaFunction]:

        if self._all_arma_file_objects_by_id is None:

            self.arma_file_model_blocker.wait()
            self._all_arma_file_objects_by_id = frozendict({antistasi_file.id: antistasi_file for antistasi_file in self.database.get_all_arma_functions()})

        return self._all_arma_file_objects_by_id

    @property
    def all_game_map_objects_by_id(self) -> dict[str, GameMap]:

        if self._all_game_map_objects_by_id is None:
            self.game_map_model_blocker.wait()
            self._all_game_map_objects_by_id = frozendict({game_map.id: game_map for game_map in self.database.get_all_game_maps()})

        return self._all_game_map_objects_by_id

    @property
    def all_origin_objects(self) -> dict[str, RecordOrigin]:
        if self._all_origin_objects is None:
            self.origin_blocker.wait()
            self._all_origin_objects = frozendict({origin.identifier: origin for origin in self.database.get_all_origins()})
            for origin in self._all_origin_objects.values():
                _ = origin.record_family
        return self._all_origin_objects

    @property
    def all_origin_objects_by_id(self) -> dict[str, RecordOrigin]:
        if self._all_origin_objects_by_id is None:
            self.origin_blocker.wait()
            self._all_origin_objects_by_id = frozendict({origin.id: origin for origin in self.database.get_all_origins()})
            for origin in self._all_origin_objects_by_id.values():
                _ = origin.record_family
        return self._all_origin_objects_by_id

    @property
    def all_version_objects(self) -> dict[str, Version]:
        if self._all_version_objects is None:
            self.version_blocker.wait()
            self._all_version_objects = frozendict({version: version for version in self.database.get_all_versions()})
        return self._all_version_objects

    @property
    def all_version_objects_by_id(self) -> dict[str, Version]:
        if self._all_version_objects_by_id is None:
            self.version_blocker.wait()
            self._all_version_objects_by_id = frozendict({version.id: Version for version in self.database.get_all_versions()})
        return self._all_version_objects_by_id

    def get_log_level_by_id(self, model_id: int) -> Optional[LogLevel]:
        if model_id is None:
            return
        log_level = self.all_log_levels_by_id.get(model_id)
        if log_level is None:
            log_level = LogLevel.select().where(LogLevel.id == model_id).execute(self.database)[0]
        return log_level

    def get_arma_file_by_id(self, model_id: int) -> Optional[ArmaFunction]:
        if model_id is None:
            return
        arma_file = self.all_arma_file_objects_by_id.get(model_id)
        if arma_file is None:
            arma_file = ArmaFunction.select().where(ArmaFunction.id == model_id).execute(self.database)[0]
        return arma_file

    def get_game_map_by_id(self, model_id: int) -> Optional[GameMap]:
        if model_id is None:
            return
        game_map = self.all_game_map_objects_by_id.get(model_id)
        if game_map is None:
            game_map = GameMap.select().where(GameMap.id == model_id).execute(self.database)[0]
        return game_map

    def get_game_map_case_insensitive(self, name: str) -> Optional[GameMap]:
        if name is None:
            return
        return self.all_game_map_objects_case_insensitive.get(name.casefold())

    def get_origin_by_id(self, model_id: int) -> Optional[RecordOrigin]:
        if model_id is None:
            return
        origin = self.all_origin_objects_by_id.get(model_id)
        if origin is None:
            origin = RecordOrigin.select().where(RecordOrigin.id == model_id).execute(self.database)[0]
        return origin

    def get_version_by_id(self, model_id: int) -> Optional[Version]:
        if model_id is None:
            return
        version = self.all_version_objects_by_id.get(model_id)
        if version is None:
            version = Version.select().where(Version.id == model_id).execute(self.database)[0]
        return version

    def reset_all(self) -> None:
        """
        Invalidate each cache.

        """
        self._all_log_levels = None
        self._all_arma_file_objects = None
        self._all_game_map_objects = None
        self._all_game_map_objects_case_insensitive = None
        self._all_log_levels_by_id = None
        self._all_arma_file_objects_by_id = None
        self._all_game_map_objects_by_id = None
        self._all_origin_objects = None
        self._all_origin_objects_by_id = None
        self._all_version_objects = None
        self._all_version_objects_by_id = None
        log.info("all cached foreign keys were reseted.")

    def preload_all(self) -> None:
        _ = self.all_log_levels
        _ = self.all_arma_file_objects
        _ = self.all_game_map_objects
        _ = self.all_game_map_objects_case_insensitive
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
                    setattr(self, attr_name, None)
            log.warning(" reseted %r, because %r of %r was created: %r", class_attr_names, model_to_dict(instance, recurse=False), sender.__name__, created)
        else:
            log.debug(" reseted, because %r of %r was created: %r", model_to_dict(instance, recurse=False), sender.__name__, created)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
