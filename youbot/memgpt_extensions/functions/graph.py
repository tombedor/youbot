from networkx import Graph


def add_node(self, name: str, node_type: str) -> str:
    """Adds a node to the graph

    Args:
        name (str): Name of the node.
        node_type (str): Type of the node

    Returns:
        str: result of the attempt to add the node.
    """
    return self._get_graph().add_node(name, node_type)

def _get_graph(self):
    self.graph = Graph()
    return self.graph