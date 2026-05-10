"""
金融知识图谱 - 图谱构建器
核心模块：数据加载 → 实体构建 → 关系构建 → 存储
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.data_loader import DataLoader
from src.storage.local_store import LocalGraphStore
from src.schema.ontology import ENTITY_TYPES, RELATION_TYPES

logger = logging.getLogger("financial_kg")


class KGBuildPipeline:
    """知识图谱构建流水线"""

    def __init__(self, data_dir: Optional[str] = None, output_dir: Optional[str] = None):
        self.data_dir = data_dir or str(Path(__file__).parent.parent / "data")
        self.output_dir = output_dir or str(Path(__file__).parent.parent / "output")
        self.loader = DataLoader(self.data_dir)
        self.store = LocalGraphStore()

        # 统计数据
        self.stats = {
            "companies": 0,
            "industries": 0,
            "products": 0,
            "relations": 0,
        }

    def build(self):
        """执行完整的构建流水线"""
        logger.info("=" * 60)
        logger.info("🚀 开始构建金融产业链知识图谱...")
        logger.info("=" * 60)

        # Step 1: 加载实体数据
        self._load_entities()

        # Step 2: 构建节点
        self._build_nodes()

        # Step 3: 加载并构建关系
        self._build_relations()

        # Step 4: 保存和统计
        self._save_and_summary()

        logger.info("=" * 60)
        logger.info("✅ 知识图谱构建完成!")
        logger.info("=" * 60)

        return self.store

    def _load_entities(self):
        """Step 1: 加载实体数据"""
        logger.info("\n📂 Step 1: 加载实体数据...")

        companies = self.loader.load_companies()
        industries = self.loader.load_industries()
        products = self.loader.load_products()

        self._companies = companies
        self._industries = industries
        self._products = products

        logger.info(f"  公司实体: {len(companies)} 条")
        logger.info(f"  行业实体: {len(industries)} 条")
        logger.info(f"  产品实体: {len(products)} 条")

    def _build_nodes(self):
        """Step 2: 构建图谱节点"""
        logger.info("\n🏗️ Step 2: 构建图谱节点...")

        # ⚠️ 先创建产品节点，再创建行业节点
        # 因为有些行业名和产品名相同（如"白酒"、"铜"、"半导体"等）
        # 后创建的节点会覆盖同名节点，所以行业优先

        # 创建产品节点（先）
        for prod in self._products:
            self.store.add_node(
                node_id=prod["name"],
                node_type="product",
                **{k: v for k, v in prod.items() if v},
            )
        self.stats["products"] = len(self._products)
        logger.info(f"  ✅ 产品节点: {len(self._products)} 个")

        # 创建行业节点（后，会覆盖同名产品节点）
        for ind in self._industries:
            self.store.add_node(
                node_id=ind["name"],
                node_type="industry",
                **{k: v for k, v in ind.items() if v},
            )
        self.stats["industries"] = len(self._industries)
        logger.info(f"  ✅ 行业节点: {len(self._industries)} 个")

        # 创建公司节点
        for comp in self._companies:
            self.store.add_node(
                node_id=comp["name"],
                node_type="company",
                **{k: v for k, v in comp.items() if v},
            )
        self.stats["companies"] = len(self._companies)
        logger.info(f"  ✅ 公司节点: {len(self._companies)} 个")

    def _build_relations(self):
        """Step 3: 构建图谱关系"""
        logger.info("\n🔗 Step 3: 构建图谱关系...")

        # 公司所属行业
        company_industry = self.loader.load_company_industry()
        for rel in company_industry:
            self.store.add_edge(
                source=rel["company_name"],
                target=rel["industry_name"],
                relation="belong_to_industry",
            )
        logger.info(f"  ✅ 公司→行业 (belong_to_industry): {len(company_industry)} 条")
        self.stats["relations"] += len(company_industry)

        # 行业上级关系
        industry_industry = self.loader.load_industry_industry()
        for rel in industry_industry:
            self.store.add_edge(
                source=rel["from_industry"],
                target=rel["to_industry"],
                relation="parent_of",
            )
        logger.info(f"  ✅ 行业→行业 (parent_of): {len(industry_industry)} 条")
        self.stats["relations"] += len(industry_industry)

        # 公司主营产品
        company_product = self.loader.load_company_product()
        for rel in company_product:
            attrs = {}
            if "rel_weight" in rel:
                attrs["rel_weight"] = rel["rel_weight"]
            self.store.add_edge(
                source=rel["company_name"],
                target=rel["product_name"],
                relation="main_product",
                **attrs,
            )
        logger.info(f"  ✅ 公司→产品 (main_product): {len(company_product)} 条")
        self.stats["relations"] += len(company_product)

        # 产品关系（上游、下游、小类）
        product_product = self.loader.load_product_product()
        for rel in product_product:
            rel_type = rel.get("rel", "related_to")
            self.store.add_edge(
                source=rel["from_entity"],
                target=rel["to_entity"],
                relation=rel_type,
            )
        logger.info(f"  ✅ 产品→产品 (upstream/downstream/subclass): {len(product_product)} 条")
        self.stats["relations"] += len(product_product)

    def _save_and_summary(self):
        """Step 4: 保存图谱并打印统计"""
        logger.info("\n💾 Step 4: 保存图谱...")

        # 保存图谱
        output_path = Path(self.output_dir) / "financial_kg.json"
        self.store.save(str(output_path))

        # 打印统计
        summary = self.store.summary()
        logger.info("\n📊 图谱统计摘要:")
        logger.info(f"  总节点数: {summary['total_nodes']}")
        logger.info(f"  总边数: {summary['total_edges']}")
        logger.info(f"  节点类型分布:")
        for nt, cnt in summary["node_types"].items():
            logger.info(f"    - {nt}: {cnt}")
        logger.info(f"  关系类型分布:")
        for rt, cnt in summary["edge_types"].items():
            logger.info(f"    - {rt}: {cnt}")
