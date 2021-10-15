import os
import sys
from pathlib import Path
import tomlkit


THIS_FILE_DIR = Path(os.path.dirname(__file__)).absolute()
WORKSPACE_FOLDER = THIS_FILE_DIR.parent
PYPROJECT_FILE = WORKSPACE_FOLDER.joinpath('pyproject.toml')

VENV_FOLDER = WORKSPACE_FOLDER.joinpath('.venv')
SITE_PACKAGES_FOLDER = VENV_FOLDER.joinpath('lib', 'site-packages')


PTH_TEMPLATE = """import os;
os.environ['IS_DEV'] ='true';
os.environ['WORKSPACEDIR']=r'{WORKSPACEDIR}';
os.environ['TOPLEVELMODULE']=r'{TOPLEVELMODULE}';
os.environ['MAIN_SCRIPT_FILE']=r'{MAIN_SCRIPT_FILE}';
os.environ['PROJECT_NAME']='{PROJECT_NAME}';
os.environ['PROJECT_AUTHOR']='{PROJECT_AUTHOR}';"""


def collect_project_data() -> dict[str, str]:
    data = {'WORKSPACEDIR': WORKSPACE_FOLDER,
            "TOPLEVELMODULE": "",
            "MAIN_SCRIPT_FILE": "",
            "PROJECT_NAME": "",
            "PROJECT_AUTHOR": ""}
    pyproject_data = tomlkit.parse(PYPROJECT_FILE.read_text())
    data["PROJECT_AUTHOR"] = pyproject_data.get('project').get('authors')[0].get('name')

    data["PROJECT_NAME"] = pyproject_data.get('project').get('name')
    data["TOPLEVELMODULE"] = WORKSPACE_FOLDER.joinpath(data["PROJECT_NAME"])
    data['MAIN_SCRIPT_FILE'] = data["TOPLEVELMODULE"].joinpath('__main__.py')
    return data


def create_pth(in_data: dict[str, str]) -> str:
    return ''.join(PTH_TEMPLATE.format(**in_data).split('\n'))


def write_pth(in_pth: str, in_name: str) -> None:
    pth_path = SITE_PACKAGES_FOLDER.joinpath(f'_{in_name.casefold()}.pth')
    pth_path.parent.mkdir(exist_ok=True, parents=True)
    pth_path.write_text(in_pth)


def main():
    data = collect_project_data()
    pth = create_pth(data)
    write_pth(pth, data["PROJECT_NAME"])


if __name__ == '__main__':

    main()
