#!/usr/bin/env python3
# coding: utf-8
"""
金融知识图谱 - 一键构建脚本
用法:
  python scripts/build_kg.py              # 使用本地图存储
  python scripts/build_kg.py --store neo4j  # 使用 Neo4j 存储
  python scripts/build_kg.py --gen-data     # 先生成示例数据再构建
"""
import argparse
import logging
import os
import sys

# 添加项目根目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import DataLoader
from src.kg_builder import KGBuildPipeline
from src.schema.ontology import print_schema


def main():
    parser = argparse.ArgumentParser(description="金融知识图谱构建工具")
    parser.add_argument("--store", choices=["local", "neo4j"], default="local", help="存储后端")
    parser.add_argument("--gen-data", action="store_true", help="先生成示例数据")
    parser.add_argument("--viz", action="store_true", help="构建后生成可视化")
    parser.add_argument("--data-dir", type=str, help="数据目录")
    parser.add_argument("--output-dir", type=str, help="输出目录")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )
    logger = logging.getLogger("build_kg")

    project_root = os.path.join(os.path.dirname(__file__), "..")
    data_dir = args.data_dir or os.path.join(project_root, "data")
    output_dir = args.output_dir or os.path.join(project_root, "output")

    # 打印 Schema
    print_schema()

    # 生成数据（可选）
    if args.gen_data:
        logger.info("\n🔄 生成示例数据...")
        from scripts.generate_data import generate_sample_data
        generate_sample_data(data_dir)

    # 检查数据是否存在
    loader = DataLoader(data_dir)
    summary = loader.summary()
    logger.info("\n📂 数据加载状态:")
    for k, v in summary.items():
        status = "✅" if v > 0 else "❌"
        logger.info(f"  {status} {k}: {v}")

    if all(v == 0 for v in summary.values()):
        logger.error("没有找到任何数据！请使用 --gen-data 生成示例数据")
        sys.exit(1)

    # 构建图谱
    logger.info(f"\n🏗️ 使用存储后端: {args.store}")

    if args.store == "local":
        pipeline = KGBuildPipeline(data_dir=data_dir, output_dir=output_dir)
        store = pipeline.build()
        final_summary = store.summary()

    elif args.store == "neo4j":
        from src.storage.neo4j_store import Neo4jStore
        store = Neo4jStore()

        logger.info("\n🔍 创建索引和约束...")
        store.create_indexes_and_constraints()

        logger.info("\n🏗️ 加载实体数据...")
        companies = loader.load_companies()
        industries = loader.load_industries()
        products = loader.load_products()

        logger.info("\n📦 创建节点...")
        store.create_nodes_batch("Industry", industries)
        store.create_nodes_batch("Company", companies)
        store.create_nodes_batch("Product", products)

        logger.info("\n🔗 创建关系...")
        company_industry = loader.load_company_industry()
        industry_industry = loader.load_industry_industry()
        company_product = loader.load_company_product()
        product_product = loader.load_product_product()

        store.create_relations_batch("Company", "Industry", company_industry,
                                      "company_name", "industry_name",
                                      rel_type="belong_to_industry")
        store.create_relations_batch("Industry", "Industry", industry_industry,
                                      "from_industry", "to_industry",
                                      rel_type="parent_of")
        store.create_relations_batch("Company", "Product", company_product,
                                      "company_name", "product_name",
                                      attr_keys=["rel_weight"], rel_type="main_product")
        store.create_relations_batch("Product", "Product", product_product,
                                      "from_entity", "to_entity")

        final_summary = store.summary()
        store.close()

    # 打印最终统计
    logger.info("\n" + "=" * 60)
    logger.info("📊 知识图谱构建完成!")
    logger.info("=" * 60)
    logger.info(f"  总节点数: {final_summary.get('total_nodes', 'N/A')}")
    logger.info(f"  总边数:   {final_summary.get('total_edges', 'N/A')}")

    node_types = final_summary.get("node_types", {})
    if isinstance(node_types, dict):
        for nt, cnt in node_types.items():
            logger.info(f"    [{nt}]: {cnt}")

    edge_types = final_summary.get("edge_types", {})
    if isinstance(edge_types, dict):
        for et, cnt in edge_types.items():
            logger.info(f"    [{et}]: {cnt}")

    # 可视化（可选）
    if args.viz:
        logger.info("\n🎨 生成可视化...")
        from src.visualize.pyvis_viz import visualize_kg
        try:
            viz_path = visualize_kg(store, max_nodes=300)
            logger.info(f"✅ 可视化已保存 → {viz_path}")
        except ImportError:
            logger.warning("pyvis 未安装，跳过可视化 (pip install pyvis)")


if __name__ == "__main__":
    main()
