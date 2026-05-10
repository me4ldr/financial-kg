"""
Cypher 查询接口
提供常用金融知识图谱查询模板
"""
import logging
from typing import List, Optional

logger = logging.getLogger("financial_kg")


class KGQuery:
    """知识图谱查询接口"""

    def __init__(self, store):
        self.store = store

    # ============================================================
    # 公司相关查询
    # ============================================================

    def get_company_info(self, company_name: str) -> dict:
        """获取公司基本信息"""
        return self.store.get_node(company_name)

    def get_company_industries(self, company_name: str) -> List[str]:
        """获取公司所属行业"""
        return self.store.get_neighbors(company_name, "belong_to_industry")

    def get_company_products(self, company_name: str) -> List[str]:
        """获取公司主营产品"""
        return self.store.get_neighbors(company_name, "main_product")

    def get_companies_by_industry(self, industry_name: str) -> List[str]:
        """获取某行业下的所有公司"""
        # 反向查找
        companies = []
        for node_id in self.store.graph.nodes():
            neighbors = self.store.get_neighbors(node_id, "belong_to_industry")
            if industry_name in neighbors:
                companies.append(node_id)
        return companies

    # ============================================================
    # 行业相关查询
    # ============================================================

    def get_industry_parent(self, industry_name: str) -> List[str]:
        """获取行业的上级行业"""
        return self.store.get_neighbors(industry_name, "parent_of")

    def get_industry_children(self, industry_name: str) -> List[str]:
        """获取行业的子行业"""
        # 反向查找
        children = []
        for node_id in self.store.graph.nodes():
            parents = self.store.get_neighbors(node_id, "parent_of")
            if industry_name in parents:
                children.append(node_id)
        return children

    def get_industry_companies(self, industry_name: str) -> List[str]:
        """获取某行业的所有上市公司"""
        return self.get_companies_by_industry(industry_name)

    # ============================================================
    # 产品相关查询
    # ============================================================

    def get_product_upstream(self, product_name: str) -> List[str]:
        """获取产品的上游原材料
        关系方向: upstream_of 表示 A 是 B 的上游，即 A→B
        所以要找指向该产品的上游原料
        """
        upstream = []
        for u, v, k, data in self.store.graph.edges(data=True, keys=True):
            if data.get("relation") == "upstream_of" and v == product_name:
                upstream.append(u)
        return upstream

    def get_product_downstream(self, product_name: str) -> List[str]:
        """获取产品的下游产品
        关系方向: downstream_of 表示 A 是 B 的下游
        """
        downstream = []
        for u, v, k, data in self.store.graph.edges(data=True, keys=True):
            if data.get("relation") == "downstream_of" and u == product_name:
                downstream.append(v)
        return downstream

    def get_product_companies(self, product_name: str) -> List[str]:
        """获取生产某产品的所有公司"""
        companies = []
        for node_id in self.store.graph.nodes():
            products = self.store.get_neighbors(node_id, "main_product")
            if product_name in products:
                companies.append(node_id)
        return companies

    # ============================================================
    # 产业链查询
    # ============================================================

    def get_supply_chain(self, product_name: str, max_depth: int = 5) -> dict:
        """获取产品的完整供应链（向上追溯）"""
        chain = {"product": product_name, "upstream": [], "depth": 0}
        visited = set()

        def _trace(product, depth):
            if depth >= max_depth or product in visited:
                return
            visited.add(product)
            upstream = self.get_product_upstream(product)
            for up in upstream:
                chain["upstream"].append({"name": up, "depth": depth + 1})
                _trace(up, depth + 1)

        _trace(product_name, 0)
        return chain

    def find_common_suppliers(self, company_a: str, company_b: str) -> List[str]:
        """查找两家公司的共同供应商（通过产品上游关系）"""
        products_a = set(self.get_company_products(company_a))
        products_b = set(self.get_company_products(company_b))

        suppliers_a = set()
        for p in products_a:
            suppliers_a.update(self.get_product_upstream(p))

        suppliers_b = set()
        for p in products_b:
            suppliers_b.update(self.get_product_upstream(p))

        return list(suppliers_a & suppliers_b)

    def find_competitors(self, company_name: str) -> List[str]:
        """查找同行业竞争公司"""
        industries = self.get_company_industries(company_name)
        competitors = set()
        for ind in industries:
            competitors.update(self.get_industry_companies(ind))
        competitors.discard(company_name)
        return list(competitors)
