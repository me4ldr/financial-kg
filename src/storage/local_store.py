"""
图存储 - 基于 NetworkX 的本地存储
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx

logger = logging.getLogger("financial_kg")


class LocalGraphStore:
    """本地图存储，使用 NetworkX"""

    def __init__(self, graph_path: Optional[str] = None):
        self.graph = nx.MultiDiGraph()
        self.graph_path = Path(graph_path) if graph_path else None
        if self.graph_path and self.graph_path.exists():
            self.load(self.graph_path)

    def add_node(self, node_id: str, node_type: str, **attrs):
        """添加节点"""
        self.graph.add_node(node_id, node_type=node_type, **attrs)

    def add_edge(self, source: str, target: str, relation: str, **attrs):
        """添加边"""
        self.graph.add_edge(source, target, relation=relation, **attrs)

    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取节点属性"""
        if self.graph.has_node(node_id):
            return self.graph.nodes[node_id]
        return None

    def get_neighbors(self, node_id: str, relation: Optional[str] = None) -> List[str]:
        """获取邻居节点"""
        if not self.graph.has_node(node_id):
            return []
        neighbors = []
        seen = set()
        for u, v, k, data in self.graph.edges(node_id, data=True, keys=True):
            if relation and data.get("relation") != relation:
                continue
            if v not in seen:
                neighbors.append(v)
                seen.add(v)
        return neighbors

    def get_edges_by_relation(self, relation: str) -> List[Dict]:
        """按关系类型获取边"""
        edges = []
        for u, v, data in self.graph.edges(data=True):
            if data.get("relation") == relation:
                edges.append({
                    "source": u,
                    "target": v,
                    "relation": relation,
                    "attrs": {k: v for k, v in data.items() if k != "relation"},
                })
        return edges

    def get_all_edges(self) -> List[Dict]:
        """获取所有边"""
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                **data,
            })
        return edges

    def get_all_nodes(self) -> List[Dict]:
        """获取所有节点"""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({"id": node_id, **data})
        return nodes

    def save(self, path: Optional[str] = None):
        """保存图到文件"""
        path = Path(path) if path else self.graph_path
        if not path:
            raise ValueError("No path specified for saving")
        path.parent.mkdir(parents=True, exist_ok=True)
        # 使用自定义 JSON 格式（NetworkX 的 JSON 不够直观）
        data = {
            "nodes": [{"id": nid, **d} for nid, d in self.graph.nodes(data=True)],
            "edges": [{"source": u, "target": v, **d} for u, v, d in self.graph.edges(data=True)],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"图已保存 → {path}")

    def load(self, path: Optional[str] = None):
        """从文件加载图"""
        path = Path(path) if path else self.graph_path
        if not path or not path.exists():
            logger.warning(f"文件不存在: {path}")
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.graph.clear()
        for node in data.get("nodes", []):
            nid = node.pop("id")
            self.graph.add_node(nid, **node)
        for edge in data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            self.graph.add_edge(source, target, **edge)
        logger.info(f"图已加载 ← {path}")

    def summary(self) -> Dict:
        """图谱统计摘要"""
        # 按节点类型统计
        node_counts = {}
        for _, data in self.graph.nodes(data=True):
            nt = data.get("node_type", "unknown")
            node_counts[nt] = node_counts.get(nt, 0) + 1

        # 按关系类型统计
        edge_counts = {}
        for _, _, data in self.graph.edges(data=True):
            rt = data.get("relation", "unknown")
            edge_counts[rt] = edge_counts.get(rt, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": node_counts,
            "edge_types": edge_counts,
        }

    def query_chain(self, start_node: str, max_depth: int = 3) -> Dict:
        """查询从某个节点出发的关联链"""
        chain = {"start": start_node, "nodes": [], "edges": []}
        visited = set()

        def _dfs(node, depth):
            if depth > max_depth or node in visited:
                return
            visited.add(node)
            chain["nodes"].append({"id": node, **self.graph.nodes.get(node, {})})
            for neighbor in self.graph.neighbors(node):
                for _, _, data in self.graph.edges(node, neighbor, data=True):
                    chain["edges"].append({
                        "source": node,
                        "target": neighbor,
                        **data,
                    })
                _dfs(neighbor, depth + 1)

        _dfs(start_node, 0)
        return chain
