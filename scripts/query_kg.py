#!/usr/bin/env python3
# coding: utf-8
"""
金融知识图谱 - 查询示例
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import DataLoader
from src.kg_builder import KGBuildPipeline
from src.query.cypher_query import KGQuery


def main():
    project_root = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.join(project_root, "data")

    # 构建图谱
    pipeline = KGBuildPipeline(data_dir=data_dir)
    store = pipeline.build()

    # 查询接口
    q = KGQuery(store)

    print("\n" + "=" * 60)
    print("🔍 金融知识图谱查询示例")
    print("=" * 60)

    # 1. 公司信息
    print("\n--- 公司信息 ---")
    info = q.get_company_info("宁德时代")
    print(f"宁德时代: {info}")

    # 2. 公司所属行业
    print("\n--- 公司所属行业 ---")
    for company in ["宁德时代", "贵州茅台", "工商银行", "科大讯飞"]:
        industries = q.get_company_industries(company)
        print(f"  {company} → {industries}")

    # 3. 公司主营产品
    print("\n--- 公司主营产品 ---")
    for company in ["宁德时代", "贵州茅台", "药明康德", "汇川技术"]:
        products = q.get_company_products(company)
        print(f"  {company} → {products}")

    # 4. 行业下的公司
    print("\n--- 行业下的公司 ---")
    for ind in ["电池", "白酒", "半导体"]:
        companies = q.get_industry_companies(ind)
        print(f"  {ind} → {companies}")

    # 5. 产品上游
    print("\n--- 产品上游原材料 ---")
    for product in ["动力电池", "光伏组件", "5G基站"]:
        upstream = q.get_product_upstream(product)
        print(f"  {product} ← {upstream}")

    # 6. 竞争公司
    print("\n--- 竞争公司（同行业） ---")
    for company in ["宁德时代", "贵州茅台"]:
        competitors = q.find_competitors(company)
        print(f"  {company} 的竞争对手: {competitors}")

    # 7. 供应链追溯
    print("\n--- 供应链追溯 ---")
    chain = q.get_supply_chain("动力电池", max_depth=3)
    print(f"  {chain['product']} 的供应链:")
    for item in chain["upstream"]:
        print(f"    [{item['depth']}级] {item['name']}")

    # 8. 公司关联链可视化
    print("\n--- 生成公司关联链可视化 ---")
    try:
        from src.visualize.pyvis_viz import visualize_company_chain
        output_dir = os.path.join(project_root, "output")
        for company in ["宁德时代", "恒瑞医药"]:
            viz_path = visualize_company_chain(
                store, company,
                output_path=os.path.join(output_dir, f"{company}_chain.html"),
                max_depth=3,
            )
            print(f"  ✅ {company} 关联链 → {viz_path}")
    except ImportError:
        print("  pyvis 未安装，跳过可视化")


if __name__ == "__main__":
    main()
