"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import TYPE_CHECKING
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import pp
from github import Github

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]
GITHUB_CLIENT = Github("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")


def url_to_identifier(in_url: str) -> str:
    _out = in_url.removeprefix("https://").removeprefix("github.com/").split("/")
    _out = _out[0] + '/' + _out[1]
    return _out


def get_repo(in_url: str):
    return GITHUB_CLIENT.get_repo(url_to_identifier(in_url))


def get_branch(repo, branch_name: str = None):
    branch_name = branch_name or repo.default_branch
    return repo.get_branch(branch_name)


def get_repo_file_list(url: str, branch_name: str = None):
    repo = get_repo(url)
    branch = get_branch(repo, branch_name=branch_name)
    latest_sha = branch.commit.sha
    tree = repo.get_git_tree(latest_sha, True)
    file_items = {}
    for item in tree.tree:
        path = str(item.path)
        name = path.rsplit("/", maxsplit=1)[-1]

        file_items[path] = name
    return file_items


# fi = get_repo_file_list("https://github.com/official-antistasi-community/A3-Antistasi")


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
