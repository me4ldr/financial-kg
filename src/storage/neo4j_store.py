"""
图存储 - 基于 Neo4j 的图数据库存储
"""
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger("financial_kg")


class Neo4jStore:
    """Neo4j 图数据库存储"""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.environ.get("NEO4J_USER", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "password")
        self._driver = None

    def _get_driver(self):
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    self.uri, auth=(self.user, self.password)
                )
                # 测试连接
                self._driver.verify_connectivity()
                logger.info(f"Neo4j 连接成功: {self.uri}")
            except ImportError:
                logger.error("请安装 neo4j: pip install neo4j")
                raise
            except Exception as e:
                logger.error(f"Neo4j 连接失败: {e}")
                raise
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            logger.info("Neo4j 连接已关闭")

    def run(self, query: str, **params):
        """执行 Cypher 查询"""
        driver = self._get_driver()
        with driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]

    def create_indexes_and_constraints(self):
        """创建索引和约束"""
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Company) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Industry) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.name IS UNIQUE",
        ]
        for q in queries:
            try:
                self.run(q)
                logger.info(f"✅ 约束创建成功: {q}")
            except Exception as e:
                logger.warning(f"约束创建失败: {q} - {e}")

    def create_nodes_batch(self, label: str, nodes: List[Dict]):
        """批量创建节点"""
        if not nodes:
            return

        query = f"""
        UNWIND $batch AS row
        MERGE (n:{label} {{name: row.name}})
        SET n += row
        """
        self.run(query, batch=nodes)
        logger.info(f"Created {len(nodes)} nodes of type '{label}'")

    def create_relations_batch(
        self,
        start_label: str,
        end_label: str,
        edges: List[Dict],
        from_key: str = "from",
        to_key: str = "to",
        rel_type: Optional[str] = None,
        attr_keys: Optional[List[str]] = None,
    ):
        """批量创建关系"""
        if not edges:
            return

        # 按关系类型分组
        rel_groups = {}
        for edge in edges:
            rt = rel_type or edge.get("rel", "RELATED")
            if rt not in rel_groups:
                rel_groups[rt] = []
            item = {"from": str(edge[from_key]), "to": str(edge[to_key])}
            if attr_keys:
                for k in attr_keys:
                    if k in edge:
                        item[k] = edge[k]
            rel_groups[rt].append(item)

        for rt, batch in rel_groups.items():
            set_clause = ""
            if attr_keys:
                existing_attrs = set()
                for item in batch:
                    existing_attrs.update(k for k in attr_keys if k in item)
                if existing_attrs:
                    set_items = [f"rel.{k} = row.{k}" for k in existing_attrs]
                    set_clause = " SET " + ", ".join(set_items)

            query = f"""
            UNWIND $batch AS row
            MATCH (a:{start_label} {{name: row.from}})
            MATCH (b:{end_label} {{name: row.to}})
            MERGE (a)-[rel:`{rt}`]->(b)
            {set_clause}
            """
            try:
                self.run(query, batch=batch)
                logger.info(f"✅ Created {len(batch)} relationships of type '{rt}'")
            except Exception as e:
                logger.error(f"❌ Failed to create relationship '{rt}': {e}")

    def summary(self) -> Dict:
        """图谱统计"""
        node_counts = {}
        for label in ["Company", "Industry", "Product"]:
            result = self.run(f"MATCH (n:{label}) RETURN count(n) as cnt")
            if result:
                node_counts[label] = result[0]["cnt"]

        edge_counts = {}
        edge_query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as cnt
        """
        for row in self.run(edge_query):
            edge_counts[row["rel_type"]] = row["cnt"]

        return {
            "node_types": node_counts,
            "edge_types": edge_counts,
            "total_nodes": sum(node_counts.values()),
            "total_edges": sum(edge_counts.values()),
        }

    def query_chain(self, start_node: str, max_depth: int = 3) -> List[Dict]:
        """查询关联链"""
        query = f"""
        MATCH path = (start {{name: $start_node}})-[*1..{max_depth}]-(other)
        RETURN path
        LIMIT 100
        """
        return self.run(query, start_node=start_node)
