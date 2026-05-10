"""
图存储后端 - 基于 NetworkX 的本地存储
"""
import json
from pathlib import Path
from typing import Optional

import networkx as nx


class LocalGraphStore:
    """本地图存储，使用 NetworkX"""

    def __init__(self, graph_path: Optional[Path] = None):
        self.graph = nx.MultiDiGraph()
        self.graph_path = graph_path
        if graph_path and graph_path.exists():
            self.load(graph_path)

    def add_node(self, node_id: str, **attrs):
        self.graph.add_node(node_id, **attrs)

    def add_edge(self, source: str, target: str, relation: str, **attrs):
        self.graph.add_edge(source, target, relation=relation, **attrs)

    def get_neighbors(self, node_id: str):
        return list(self.graph.neighbors(node_id))

    def get_edges(self):
        return list(self.graph.edges(data=True))

    def save(self, path: Optional[Path] = None):
        path = path or self.graph_path
        if not path:
            raise ValueError("No path specified for saving")
        path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_json(self.graph, str(path))

    def load(self, path: Optional[Path] = None):
        path = path or self.graph_path
        if not path:
            raise ValueError("No path specified for loading")
        self.graph = nx.read_json(str(path), multigraph=True)

    def summary(self) -> dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
        }
