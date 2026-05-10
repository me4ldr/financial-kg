#!/usr/bin/env python3
# coding: utf-8
"""
金融知识图谱 - Wind 主营构成数据导入脚本
使用 segment_sales 字段获取公司主营产品分类及其营收占比
将主营类别作为 Product 节点，构建 Company → Product 关系
"""
import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("wind_segment_import")

WIND_PYTHON = "/Users/xinyuan/miniconda3/envs/wind-mcp/bin/python"


def parse_segment_text(raw_text: str) -> dict:
    """解析 segment_sales 返回的百分比字符串。
    输入: "白酒:98.09%;其他业务(行业):1.91%"
    输出: {"白酒": 98.09, "其他业务(行业)": 1.91}
    """
    result = {}
    if not raw_text or not isinstance(raw_text, str):
        return result
    for item in raw_text.strip().split(";"):
        item = item.strip()
        if not item or ":" not in item:
            continue
        name, pct_str = item.rsplit(":", 1)
        name = name.strip()
        pct_str = pct_str.strip().rstrip("%")
        try:
            pct = float(pct_str)
            if name:
                result[name] = pct
        except ValueError:
            continue
    return result


def import_segment_data(data_dir: str, rpt_date: str = "20251231"):
    """从 Wind 获取主营构成数据"""
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

    logger.info(f"📋 共 {len(companies)} 家公司需要查询主营构成")

    # 批量获取 segment_sales
    products = []
    product_set = set()
    company_product_rels = []

    seen_products = {}  # product_name -> product_info

    batch_size = 100
    codes = [c.get("wind_code", "") for c in companies if c.get("wind_code")]
    name_to_code = {c.get("name", ""): c.get("wind_code", "") for c in companies}

    total_batches = (len(codes) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(codes), batch_size):
        batch = codes[batch_idx : batch_idx + batch_size]
        codes_str = ",".join(batch)

        r = w.wss(codes_str, "segment_sales", f"rptDate={rpt_date};order=1;")
        if r.ErrorCode == 0 and r.Data:
            for i, code in enumerate(batch):
                if i >= len(r.Data[0]):
                    continue
                raw = r.Data[0][i]
                segments = parse_segment_text(raw)

                # 找到对应的公司名
                company_name = ""
                for c in companies:
                    if c.get("wind_code") == code:
                        company_name = c.get("name", "")
                        break

                for seg_name, pct in segments.items():
                    # 跳过"其他"类别
                    if seg_name.startswith("其他") or seg_name.startswith("其他业务"):
                        continue

                    # 去重产品
                    if seg_name not in product_set:
                        product_set.add(seg_name)
                        products.append({"name": seg_name, "category": "主营类别"})
                        seen_products[seg_name] = {
                            "name": seg_name,
                            "category": "主营类别",
                            "companies": [],
                            "total_weight": 0,
                        }
                    seen_products[seg_name]["companies"].append(company_name)
                    seen_products[seg_name]["total_weight"] += pct

                    company_product_rels.append({
                        "company_name": company_name,
                        "product_name": seg_name,
                        "rel": "main_product",
                        "rel_weight": pct,
                        "rpt_date": rpt_date,
                    })

        progress = min(batch_idx + batch_size, len(codes))
        batch_num = batch_idx // batch_size + 1
        if batch_num % 10 == 0 or batch_num == total_batches:
            logger.info(f"  进度: {progress}/{len(codes)} (批次 {batch_num}/{total_batches})")
        time.sleep(0.3)

    # 保存数据
    def save_jsonl(filename: str, data: list):
        path = data_path / filename
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"  ✅ {filename}: {len(data)} 条")

    save_jsonl("product.json", products)
    save_jsonl("company_product.json", company_product_rels)

    # 产品-产品关系（暂空，后续可基于行业关联推导）
    save_jsonl("product_product.json", [])

    # 统计
    logger.info("\n" + "=" * 60)
    logger.info("✅ 主营构成数据导入完成!")
    logger.info("=" * 60)
    logger.info(f"  产品实体: {len(products)} 个")
    logger.info(f"  公司→产品关系: {len(company_product_rels)} 条")

    # 热门产品 Top 20
    product_counts = defaultdict(int)
    for rel in company_product_rels:
        product_counts[rel["product_name"]] += 1

    logger.info("\n  热门主营类别 Top 20:")
    for name, count in sorted(product_counts.items(), key=lambda x: -x[1])[:20]:
        logger.info(f"    {name}: {count} 家公司")


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    import_segment_data(data_dir, rpt_date="20251231")
