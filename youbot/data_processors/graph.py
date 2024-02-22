from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional
from cycler import V
import networkx as nx
import matplotlib.pyplot as plt


@dataclass
class Node:
    node_types = []
    name: str

    @classmethod
    def get_klass(cls, node_type: str) -> type:
        for klass in cls.node_types:
            if klass.__name__ == node_type:
                return klass
        raise ValueError(
            f"Invalid node type: {node_type}. Valid node types are: {cls.node_types}"
        )

    def get_node_type(self) -> type:
        return self.__class__

    def node_attrs(self):
        d = {k: v for k, v in vars(self).items() if k != "name"}
        d["node_type"] = self.get_node_type().__name__
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
    (Person, Person): [
        "married_to",
        "engaged_to",
        "dating",
        "friends_with",
        "enemies_with",
        "family_with",
        "works_with",
    ],
    (Person, Pet): ["adopted", "owns"],
}


class Graph:
    def __init__(self):
        self.G = nx.DiGraph()

    def add_node(self, name: str, node_type: str) -> str:
        if name in self.G.nodes:
            raise ValueError(f"Node {name} already exists")

        klass = Node.get_klass(node_type)
        node = klass(name)
        self.G.add_node(node.name, **node.node_attrs())
        return f"Added node {name} of type {node_type}"

    def get_node(self, name: str) -> Node:
        node_attrs = self.G.nodes[name]
        node_type = node_attrs["node_type"]
        klass = Node.get_klass(node_type)
        node_attrs["name"] = name
        
        return klass(**{k:v for k,v in node_attrs.items() if k != "node_type"})

    def add_edge(self, out_node_name: str, in_node_name: str, relationship: str) -> str:
        if out_node_name not in self.G.nodes:
            raise ValueError(f"Node {out_node_name} does not exist")
        elif in_node_name not in self.G.nodes:
            raise ValueError(f"Node {in_node_name} does not exist")

        out_node = self.get_node(out_node_name)
        in_node = self.get_node(in_node_name)

        if (out_node.get_node_type(), in_node.get_node_type()) not in VALID_EDGES:
            valid_in_node_types = [
                k[1].__name__
                for k in VALID_EDGES.keys()
                if k[0] == out_node.get_node_type()
            ]
            raise ValueError(
                f"out node {out_node_name} of type {out_node.get_node_type()} cannot be connected to in node {in_node_name} of type {in_node.get_node_type()}. Valid edge types from node type {out_node.get_node_type()} are: {valid_in_node_types}"
            )

        valid_relationships = VALID_EDGES[(out_node.get_node_type(), in_node.get_node_type())]
        if relationship not in valid_relationships:
            raise ValueError(
                f"Invalid relationship {relationship} connecting node type {out_node.get_node_type()} to node type {in_node.get_node_type()}. Valid relationships are: {valid_relationships}"
            )

        self.add_edge(out_node_name, in_node_name, relationship=relationship)
        return f"Added edge from {out_node_name} to {in_node_name} with relationship {relationship}"

    def add_node_attribute(
        self, name: str, attribute_name: str, attribute_value: str
    ) -> str:
        node = self.get_node(name)
        return "foo"

    def show(self):
        pos = nx.spring_layout(self.G)
        # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        nx.draw(
            self.G, pos, with_labels=True, node_color="lightblue", edge_color="gray"
        )
        plt.show()


if __name__ == "__main__":
    g = Graph()

    g.add_node("Tom Bedor", "Person")
    g.add_node("Justina Hoang", "Person")

    g.add_edge("Tom Bedor", "Justina Hoang", "married_to")

    g.show()
