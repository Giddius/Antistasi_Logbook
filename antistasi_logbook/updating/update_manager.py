"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING
from pathlib import Path
from threading import Event, Thread

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.updating.updater import Updater
    from antistasi_logbook.updating.time_handling import TimeClock

    # * Gid Imports ----------------------------------------------------------------------------------------->
    from gidapptools.gid_config.interface import GidIniConfig

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class UpdateManager(Thread):
    config_name = "updating"

    def __init__(self,
                 updater: "Updater",
                 config: "GidIniConfig",
                 time_clock: "TimeClock",
                 pause_event: Event,
                 stop_event: Event) -> None:
        super().__init__(name=f"{self.__class__.__name__}Thread")
        self.updater = updater
        self.config = config
        self.time_clock = time_clock
        self.pause_event = pause_event
        self.stop_event = stop_event

    @ property
    def updates_enabled(self) -> bool:
        return self.config.get(self.config_name, "updates_enabled", default=False)

    def _pause_loop(self) -> None:
        log.debug("%r is paused", self)
        while self.pause_event.is_set() is True:
            sleep(1)
            if self.stop_event.is_set() is True:
                return
        log.debug("%r continues after being paused")

    def run(self) -> None:
        log.info("starting %r", self)

        while self.stop_event.is_set() is False:

            if self.pause_event.is_set() is True:
                self._pause_loop()
                continue

            if self.updates_enabled is True:
                self.updater()

            self.time_clock.wait_for_trigger()

    def shutdown(self) -> None:
        log.debug("shutting down %s", self)
        self.stop_event.set()
        self.join()
        log.debug("%s finished shutting down", self)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
