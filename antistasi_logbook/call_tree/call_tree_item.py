"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import networkx as nx

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import LogFile, LogRecord, AntstasiFunction

# endregion[Imports]

# region [TODO]

# TODO: This is Proof-of-Concept!

# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class CallTreeNode:

    def __init__(self, function: AntstasiFunction):
        self.function = function
        self.amount_called = 0
        self.amount_called_by = 0
        self.nodes_called: set["CallTreeNode"] = set()
        self.called_by_nodes: set["CallTreeNode"] = set()

    def add_called_node(self, node):
        self.amount_called += 1
        self.nodes_called.add(node)

    def add_called_by_node(self, node):
        self.amount_called_by += 1
        self.called_by_nodes.add(node)

    def __hash__(self) -> int:
        return hash(self.function.id)


class CallTree:

    def __init__(self, log_file: LogFile) -> None:
        self.log_file = log_file
        self.root = nx.DiGraph(nodesep=10.0)
        self.init_server_node = None
        self.label_dict = {}

    def populate(self):
        all_records = tuple(LogRecord.select().where((LogRecord.log_file_id == self.log_file.id) & (LogRecord.logged_from != None) & (LogRecord.called_by != None)).order_by(LogRecord.recorded_at))
        all_functions = {r.logged_from for r in all_records}.union({r.called_by for r in all_records})
        nodes = {f.name: CallTreeNode(f) for f in all_functions}

        for record in all_records:
            logged_from_node = nodes[record.logged_from.name]
            called_by_node = nodes[record.called_by.name]
            logged_from_node.add_called_by_node(called_by_node)
            called_by_node.add_called_node(logged_from_node)
        add_list = []
        all_again = set()
        for name, node in nodes.items():
            all_again.add(node)
            if name.casefold().split('_')[-1] == "initserver":
                self.init_server_node = node
            for calling_node in node.called_by_nodes:
                all_again.add(calling_node)
                add_list.append((calling_node, node, node.amount_called_by + calling_node.amount_called))
            for called_node in node.nodes_called:
                all_again.add(called_node)
                add_list.append((node, called_node, called_node.amount_called_by + node.amount_called))

        self.root.add_weighted_edges_from(add_list)
        for node in nodes.values():
            self.label_dict[node] = f"{node.function.pretty_name}\n{node.amount_called_by!r}"
            self.root.add_node(node, label=f"{node.function.pretty_name}: {node.amount_called_by!r}")


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
