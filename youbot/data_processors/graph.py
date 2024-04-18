from dataclasses import dataclass
from datetime import date
import os
import pickle
from typing import Optional
import networkx as nx
import matplotlib.pyplot as plt


@dataclass
class Node:
    # class attr
    node_types = []
    name: str

    def __post_init__(self):
        self.node_type = self.__class__.__name__

    @classmethod
    def get_klass(cls, node_type: str) -> type:
        for klass in cls.node_types:
            if klass.__name__ == node_type:
                return klass
        raise ValueError(f"Invalid node type: {node_type}. Valid node types are: {cls.node_types}")

    def node_attrs(self):
        d = {k: v for k, v in vars(self).items()}
        return d

    def __init_subclass__(cls) -> None:
        cls.node_types.append(cls)


@dataclass
class Person(Node):
    birthday: Optional[date] = None


@dataclass
class Pet(Node):
    birthday: Optional[date] = None
    breed: Optional[str] = None


VALID_EDGES = {
    ("Person", "Person"): [
        "married_to",
        "engaged_to",
        "dating",
        "friends_with",
        "enemies_with",
        "family_with",
        "works_with",
    ],
    ("Person", "Pet"): ["adopted", "owns"],
}


class Graph:
    def __init__(self, pickle_path=os.path.join("/tmp", "graph.pickle")):
        self.pickle_path = pickle_path
        if os.path.exists(pickle_path):
            self.G = pickle.load(open(pickle_path, "rb"))
        else:
            self.G = nx.DiGraph()

    def persist(self):
        with open(self.pickle_path, "wb") as f:
            pickle.dump(self.G, f)

    def add_node(self, name: str, node_type: str) -> str:
        if name in self.G.nodes:
            return f"Node {name} already exists"

        klass = Node.get_klass(node_type)
        node = klass(name)
        self.G.add_node(node.name, **node.node_attrs())
        self.persist()
        return f"Added node {name} of type {node_type}"

    def get_node(self, name: str) -> Node:
        node_attrs = self.G.nodes[name]
        node_type = node_attrs["node_type"]
        klass = Node.get_klass(node_type)
        node_attrs["name"] = name

        return klass(**{k: v for k, v in node_attrs.items() if k != "node_type"})

    def add_edge(self, out_node_name: str, in_node_name: str, relationship: str) -> str:
        if out_node_name not in self.G.nodes:
            raise ValueError(f"Node {out_node_name} does not exist")
        elif in_node_name not in self.G.nodes:
            raise ValueError(f"Node {in_node_name} does not exist")

        out_node = self.get_node(out_node_name)
        in_node = self.get_node(in_node_name)

        if (out_node.node_type, in_node.node_type) not in VALID_EDGES:
            valid_in_node_types = [k[1].__name__ for k in VALID_EDGES.keys() if k[0] == out_node.node_type]
            raise ValueError(
                f"out node {out_node_name} of type {out_node.node_type} cannot be connected to in node {in_node_name} of type {in_node.node_type}. Valid edge types from node type {out_node.node_type} are: {valid_in_node_types}"
            )

        valid_relationships = VALID_EDGES[(out_node.node_type, in_node.node_type)]  # type: ignore
        if relationship not in valid_relationships:
            raise ValueError(
                f"Invalid relationship {relationship} connecting node type {out_node.node_type} to node type {in_node.node_type}. Valid relationships are: {valid_relationships}"
            )

        self.G.add_edge(out_node_name, in_node_name, relationship=relationship)
        self.persist()
        return f"Added edge from {out_node_name} to {in_node_name} with relationship {relationship}"

    def add_node_attribute(self, node_name: str, attribute_name: str, attribute_value: str) -> str:
        node = self.get_node(node_name)
        valid_attributes = [k for k, v in node.node_attrs().items() if k != "node_type"]
        if attribute_name not in valid_attributes:
            raise ValueError(
                f"Cannot set attribute {attribute_name}. valid attributes for node of type {node.node_type} are: {valid_attributes}"
            )
        else:
            self.G.nodes[node_name][attribute_name] = attribute_value

        self.persist()
        return f"set attribute {attribute_name} to {attribute_value} for node {node_name}"

    def show(self):
        pos = nx.spring_layout(self.G)
        nx.draw_networkx_edge_labels(self.G, pos)
        nx.draw(self.G, pos, with_labels=True, node_color="lightblue", edge_color="gray")
        plt.show()


if __name__ == "__main__":
    # facts = fetch_facts()
    g = Graph()

    g.add_node("Tom Bedor", "Person")
    g.add_node("Justina Hoang", "Person")

    g.add_edge("Tom Bedor", "Justina Hoang", "married_to")
    g.add_node_attribute("Tom Bedor", "birthday", "2020-01-01")

    g.show()
