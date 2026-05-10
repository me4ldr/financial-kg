#!/usr/bin/env python3
# coding: utf-8
"""
金融知识图谱 - Wind 主营产品数据导入脚本
使用 WSS 接口获取两个字段：
1. majorproducttype — 主营类别（中间粒度，适合产品分类）
2. majorproductname — 具体产品名（细粒度，用于构建公司产品节点）
配合 segment_sales 的营收占比数据

数据来源：Wind 金融终端 WSS 接口
"""
import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("wind_product_import")


def parse_wind_list(raw_text: str) -> list:
    """解析 Wind 返回的逗号分隔列表字符串。
    输入: "波立维片剂、地氯雷他定、泰嘉、头孢呋辛钠"
    输出: ["波立维片剂", "地氯雷他定", "泰嘉", "头孢呋辛钠"]
    """
    if not raw_text or not isinstance(raw_text, str):
        return []
    # 用顿号或逗号分隔
    items = []
    for sep in ['、', ',']:
        if sep in raw_text:
            items = [item.strip() for item in raw_text.split(sep)]
            break
    if not items:
        items = [raw_text.strip()]
    return [item for item in items if item and not item.startswith("其他")]


def import_product_data(data_dir: str, rpt_date: str = "20251231"):
    """从 Wind 获取主营产品数据"""
    from WindPy import w

    w.start()
    logger.info("✅ Wind 登录成功")

    data_path = Path(data_dir)

    # 加载已有的公司数据
    company_file = data_path / "company.json"
    if not company_file.exists():
        logger.error("请先运行 import_wind_data.py 获取公司数据")
        return

    companies = []
    with open(company_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                companies.append(json.loads(line))

    logger.info(f"📋 共 {len(companies)} 家公司需要查询主营产品")

    # 构建 code → company 映射
    code_to_company = {}
    for c in companies:
        wc = c.get("wind_code", "")
        if wc:
            code_to_company[wc] = c

    codes = list(code_to_company.keys())

    # 批量获取数据
    product_set = set()
    product_type_set = set()
    company_product_rels = []
    company_producttype_rels = []

    batch_size = 100
    total_batches = (len(codes) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(codes), batch_size):
        batch = codes[batch_idx: batch_idx + batch_size]
        codes_str = ",".join(batch)

        # 获取 majorproductname
        r1 = w.wss(codes_str, "majorproductname")
        # 获取 majorproducttype
        r2 = w.wss(codes_str, "majorproducttype")
        # 获取 segment_sales（营收占比）
        r3 = w.wss(codes_str, "segment_sales", f"rptDate={rpt_date};order=1;")

        for i, code in enumerate(batch):
            company = code_to_company.get(code, {})
            company_name = company.get("name", code)

            # 解析 majorproductname（具体产品）
            product_name_raw = ""
            if r1.ErrorCode == 0 and r1.Data and i < len(r1.Data[0]):
                product_name_raw = r1.Data[0][i] or ""
            product_names = parse_wind_list(product_name_raw)

            for pname in product_names:
                if pname not in product_set:
                    product_set.add(pname)
                company_product_rels.append({
                    "company_name": company_name,
                    "product_name": pname,
                    "rel": "main_product",
                    "product_type": "具体产品",
                })

            # 解析 majorproducttype（产品类别）
            product_type_raw = ""
            if r2.ErrorCode == 0 and r2.Data and i < len(r2.Data[0]):
                product_type_raw = r2.Data[0][i] or ""
            product_types = parse_wind_list(product_type_raw)

            for ptype in product_types:
                if ptype not in product_type_set:
                    product_type_set.add(ptype)
                company_producttype_rels.append({
                    "company_name": company_name,
                    "product_name": ptype,
                    "rel": "main_product",
                    "product_type": "主营类别",
                })

        batch_num = batch_idx // batch_size + 1
        if batch_num % 20 == 0 or batch_num == total_batches:
            progress = min(batch_idx + batch_size, len(codes))
            logger.info(f"  进度: {progress}/{len(codes)} (批次 {batch_num}/{total_batches})")

        time.sleep(0.3)

    # 构建产品实体列表
    products = []
    for pname in product_set:
        products.append({"name": pname, "category": "具体产品"})
    for ptype in product_type_set:
        products.append({"name": ptype, "category": "主营类别"})

    # 合并关系
    all_rels = company_product_rels + company_producttype_rels

    # 保存数据
    def save_jsonl(filename: str, data: list):
        path = data_path / filename
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"  ✅ {filename}: {len(data)} 条")

    save_jsonl("product.json", products)
    save_jsonl("company_product.json", all_rels)
    save_jsonl("product_product.json", [])

    # 统计
    logger.info("\n" + "=" * 60)
    logger.info("✅ 主营产品数据导入完成!")
    logger.info("=" * 60)
    logger.info(f"  产品实体（具体产品）: {len(product_set)} 个")
    logger.info(f"  产品实体（主营类别）: {len(product_type_set)} 个")
    logger.info(f"  产品实体总计: {len(products)} 个")
    logger.info(f"  公司→产品关系: {len(all_rels)} 条")

    # 热门产品 Top 20
    product_counts = defaultdict(int)
    for rel in all_rels:
        product_counts[rel["product_name"]] += 1

    logger.info("\n  热门产品 Top 20:")
    for name, count in sorted(product_counts.items(), key=lambda x: -x[1])[:20]:
        logger.info(f"    {name}: {count} 家公司")


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    import_product_data(data_dir, rpt_date="20251231")
