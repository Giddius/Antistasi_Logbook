# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys

# * Third Party Imports --------------------------------------------------------------------------------->
# * Third Party Imports -->
from dotenv import load_dotenv

load_dotenv()
# * Standard Library Imports ---------------------------------------------------------------------------->
# * Standard Library Imports -->
from multiprocessing import Pool, cpu_count

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
STARTFOLDER = os.path.dirname(THIS_FILE_DIR)
RESSOURCE_NAME = os.getenv('RESNAME')
RESSOURCE_RELATIVE_PATH = os.getenv('RELRESPATH')


def find_files():
    for dirname, _, filelist in os.walk(STARTFOLDER):
        for _file in filelist:
            if _file.endswith('.py') and _file.startswith('Ui_'):
                _path = os.path.join(dirname, _file).replace('\\\\', '/').replace('\\', '/')
                with open(_path, 'r') as _contentfile:
                    _content = _contentfile.read()
                yield [_path, _content]


def change_files(invars):
    _linecontent = invars[1].splitlines()
    _new_content_lines = []
    for line in _linecontent:
        if "QtCore.QMetaObject.connectSlotsByName(" in line:
            print(f"changing connectbyname in file '{invars[0]}'")
        elif RESSOURCE_NAME in line:
            _new_content_lines.append("import " + RESSOURCE_RELATIVE_PATH)
            print(f"changing ressourcepath in file '{invars[0]}'")
        else:
            _new_content_lines.append(line)
    return [invars[0], '\n'.join(_new_content_lines)]


def save(path, content):
    with open(path, 'w') as newcontent:
        newcontent.write(content)


if __name__ == '__main__':

    results = map(change_files, find_files())
    for _path, _content in results:
        save(_path, _content)
