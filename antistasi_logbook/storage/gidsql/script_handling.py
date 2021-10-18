# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import logging
from pprint import pformat

# * Gid Imports ----------------------------------------------------------------------------------------->

from pathlib import Path
# * Local Imports --------------------------------------------------------------------------------------->


# endregion [Imports]

__updated__ = '2020-11-22 15:00:32'


# region [Logging]
log = logging.getLogger('gidsql')


# endregion [Logging]


class GidSqliteScriptProvider:
    def __init__(self, script_folder):
        self.script_folder = Path(script_folder)
        self.setup_prefix = 'setup'

    @property
    def scripts(self):
        _out_dict = {}
        for _file in os.scandir(self.script_folder):
            if _file.is_file() is True and _file.name.endswith('.sql') and not _file.name.startswith(self.setup_prefix):
                _bare_name = _file.name.split('.')[0]
                _out_dict[_bare_name] = _file.path
        return _out_dict

    @property
    def setup_scripts(self):
        # sourcery skip: inline-immediately-returned-variable, list-comprehension
        setup_scripts = []
        base_setup_script = None
        for _file in os.scandir(self.script_folder):
            if os.path.isfile(_file.path) is True and _file.name.endswith('.sql') and _file.name.startswith(self.setup_prefix):
                if _file.name.removeprefix(self.setup_prefix).split('.')[0] == 'base':
                    base_setup_script = Path(_file.path).read_text(encoding='utf-8', errors='ignore')
                else:
                    setup_scripts.append(Path(_file.path).read_text(encoding='utf-8', errors='ignore'))
        return [script for script in [base_setup_script] + setup_scripts if script is not None]

    def __getitem__(self, key):
        _file = self.scripts.get(key, None)
        if _file:
            return Path(_file).read_text(encoding='utf-8', errors='ignore')

    def __contains__(self, key):
        return key in self.scripts

    def __len__(self):
        return len(self.scripts)

    def __setitem__(self, key, value):
        _name = key + '.sql'
        _path = self.script_folder.joinpath(_name)
        _path.write_text(value, encoding='utf-8', errors='ignore')

    def get(self, key, default=None):
        _out = self[key]
        if _out is None:
            _out = default

        return _out

    def __repr__(self):
        return f"{self.__class__.__name__}({self.script_folder})"

    def __str__(self):
        _out = []
        for _file in os.scandir(self.script_folder):
            if _file.name.endswith('.sql'):
                _out.append(_file.name)
        return pformat(_out)


if __name__ == '__main__':
    pass
