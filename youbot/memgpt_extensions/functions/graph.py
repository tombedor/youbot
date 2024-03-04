from networkx import Graph


def _get_graph(self) -> Graph:
    if "graph" not in vars(self):
        self.graph = Graph()
    return self.graph


def add_node(self, name: str, node_type: str) -> str:
    """Adds a node to the graph

    Args:
        name (str): Name of the node.
        node_type (str): Type of the node

    Returns:
        str: result of the attempt to add the node.
    """
    return self._get_graph().add_node(name, node_type)


def add_edge(self, out_node_name: str, in_node_name: str, relationship: str) -> str:
    """Adds an edge to the graph

    Args:
        out_node_name (str): Name of the out node.
        in_node_name (str): Name of the in node.
        relationship (str): Relationship between the out and in nodes.

    Returns:
        str: result of the attempt to add the edge.
    """
    return self._get_graph().add_edge(out_node_name, in_node_name, relationship=relationship)
