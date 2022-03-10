import re

pat = re.compile(r"self\.(?P<name>\w+)\s?[\:\=]")


a = """
    self.log_levels_blocker = BlockingEvent()
    self.game_map_model_blocker = BlockingEvent()
    self.arma_file_model_blocker = BlockingEvent()
    self.origin_blocker = BlockingEvent()
    self.version_blocker = BlockingEvent()

    self._all_log_levels: dict[str, LogLevel] = None
    self._all_log_levels_by_id: dict[int, LogLevel] = None

    self._all_arma_file_objects: dict[tuple[str, str], ArmaFunction] = None
    self._all_arma_file_objects_by_id: dict[str, ArmaFunction] = None

    self._all_game_map_objects: dict[str, GameMap] = None
    self._all_game_map_objects_by_id: dict[str, GameMap] = None

    self._all_origin_objects: dict[str, RecordOrigin] = None
    self._all_origin_objects_by_id: dict[str, RecordOrigin] = None

    self._all_version_objects: dict[str, Version] = None
    self._all_version_objects_by_id: dict[str, Version]
""".strip()


a = '\n'.join(line.strip() for line in a.splitlines() if line)


for i in pat.findall(a):
    print(f'"{i}",')
