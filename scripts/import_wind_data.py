#!/usr/bin/env python3
# coding: utf-8
"""
金融知识图谱 - Wind 真实数据导入脚本
从 Wind 金融终端获取真实的 A 股上市公司、行业分类、公司财务数据
"""
import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("wind_import")


# ============================================================
# 申万行业指数代码（2021版）
# ============================================================

SHENWAN_L1 = {
    "801010.SI": "农林牧渔", "801030.SI": "基础化工", "801040.SI": "钢铁",
    "801050.SI": "有色金属", "801080.SI": "电子", "801110.SI": "家用电器",
    "801120.SI": "食品饮料", "801130.SI": "纺织服饰", "801140.SI": "轻工制造",
    "801150.SI": "医药生物", "801160.SI": "公用事业", "801170.SI": "交通运输",
    "801180.SI": "房地产", "801200.SI": "商贸零售", "801210.SI": "社会服务",
    "801230.SI": "综合", "801710.SI": "建筑材料", "801720.SI": "建筑装饰",
    "801730.SI": "电力设备", "801890.SI": "机械设备", "801740.SI": "国防军工",
    "801750.SI": "计算机", "801760.SI": "传媒", "801770.SI": "通信",
    "801780.SI": "银行", "801790.SI": "非银金融", "801950.SI": "煤炭",
    "801960.SI": "石油石化", "801970.SI": "环保", "801980.SI": "美容护理",
    "801880.SI": "汽车",
}

SHENWAN_L2 = {
    "801011.SI": "种植业", "801012.SI": "林业", "801013.SI": "渔业",
    "801014.SI": "饲料", "801015.SI": "农产品加工", "801016.SI": "动物保健",
    "801031.SI": "化学原料", "801032.SI": "化学制品", "801033.SI": "化学纤维",
    "801034.SI": "塑料", "801035.SI": "橡胶", "801036.SI": "农化制品",
    "801037.SI": "非金属材料", "801038.SI": "聚氨酯",
    "801081.SI": "半导体", "801082.SI": "光学光电子", "801083.SI": "电子化学品",
    "801084.SI": "消费电子", "801085.SI": "元器件", "801086.SI": "其他电子",
    "801087.SI": "被动元件",
    "801151.SI": "化学制药", "801152.SI": "中药", "801153.SI": "生物制品",
    "801154.SI": "医药商业", "801155.SI": "医疗器械", "801156.SI": "医疗服务",
    "801121.SI": "白酒", "801122.SI": "啤酒", "801123.SI": "肉制品",
    "801124.SI": "乳制品", "801125.SI": "调味发酵品", "801126.SI": "休闲食品",
    "801127.SI": "预加工食品", "801128.SI": "其他酒类", "801129.SI": "软饮料",
    "801731.SI": "电池", "801732.SI": "光伏设备", "801733.SI": "风电设备",
    "801734.SI": "电网设备", "801735.SI": "电机", "801736.SI": "其他电源设备",
    "801881.SI": "乘用车", "801882.SI": "商用车", "801883.SI": "汽车零部件",
    "801884.SI": "汽车服务",
    "801781.SI": "国有大型银行", "801782.SI": "股份制银行",
    "801783.SI": "城商行", "801784.SI": "农商行",
    "801791.SI": "证券", "801792.SI": "保险", "801793.SI": "多元金融",
    "801751.SI": "软件开发", "801752.SI": "IT服务",
    "801753.SI": "计算机设备", "801754.SI": "通信设备",
    "801051.SI": "铜", "801052.SI": "铝", "801053.SI": "铅锌",
    "801054.SI": "黄金", "801055.SI": "稀土", "801056.SI": "锂",
    "801057.SI": "其他金属",
    "801761.SI": "游戏", "801762.SI": "影视", "801763.SI": "广告营销",
    "801764.SI": "出版",
    "801771.SI": "电信运营", "801772.SI": "通信设备", "801773.SI": "通信服务",
    "801891.SI": "工程机械", "801892.SI": "专用设备",
    "801893.SI": "通用设备", "801894.SI": "自动化设备",
    "801895.SI": "轨交设备", "801896.SI": "仪器仪表",
    "801181.SI": "住宅开发", "801182.SI": "商业地产", "801183.SI": "产业地产",
    "801161.SI": "电力", "801162.SI": "燃气", "801163.SI": "水务",
    "801164.SI": "环境治理",
    "801041.SI": "普钢", "801042.SI": "特钢",
    "801711.SI": "水泥", "801712.SI": "玻璃玻纤", "801713.SI": "管材",
    "801714.SI": "其他建材",
    "801721.SI": "房屋建设", "801722.SI": "基础建设",
    "801723.SI": "专业工程", "801724.SI": "装修装饰",
    "801741.SI": "航空装备", "801742.SI": "航天装备",
    "801743.SI": "地面兵装", "801744.SI": "航海装备",
    "801951.SI": "动力煤", "801952.SI": "焦煤", "801953.SI": "焦炭",
    "801961.SI": "石油开采", "801962.SI": "油服工程", "801963.SI": "石油化工",
    "801971.SI": "大气治理", "801972.SI": "水处理", "801973.SI": "固废治理",
    "801131.SI": "纺织制造", "801132.SI": "服装家纺",
    "801201.SI": "百货零售", "801202.SI": "超市", "801203.SI": "电商",
    "801171.SI": "航空", "801172.SI": "航运", "801173.SI": "物流",
    "801174.SI": "公路铁路", "801175.SI": "港口",
    "801211.SI": "酒店餐饮", "801212.SI": "旅游",
    "801213.SI": "教育", "801214.SI": "体育",
    "801981.SI": "化妆品", "801982.SI": "个护用品",
    "801141.SI": "造纸", "801142.SI": "包装印刷", "801143.SI": "家居用品",
}

L1_TO_L2 = defaultdict(list)
for code, name in SHENWAN_L2.items():
    l1_code = code[:5] + "0.SI"
    L1_TO_L2[l1_code].append((code, name))


def parse_wset_result(r):
    """正确解析 WSET 结果（关键：忽略 Times 属性，直接 zip Data 列）"""
    if r.ErrorCode != 0:
        logger.warning(f"Wind 错误码: {r.ErrorCode}")
        return []
    if not r.Data or not r.Data[0]:
        return []
    # Data 是按列存储的: Data[0]=date列, Data[1]=wind_code列, ...
    data_rows = list(zip(*r.Data))
    return [dict(zip(r.Fields, row)) for row in data_rows]


def parse_wss_result(r):
    """解析 WSS 截面结果"""
    if r.ErrorCode != 0:
        logger.warning(f"Wind 错误码: {r.ErrorCode}")
        return []
    if not r.Data or not r.Data[0]:
        return []
    data_rows = list(zip(*r.Data))
    return [dict(zip(r.Fields, row)) for row in data_rows]


def import_from_wind(data_dir: str):
    """从 Wind 导入真实数据"""
    from WindPy import w

    w.start()
    logger.info("✅ Wind 登录成功")

    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # Step 1: 获取申万一级行业成分股（公司→行业映射）
    # ============================================================
    logger.info("\n🏭 Step 1: 获取申万行业成分股...")
    company_industry_map = {}

    for code, name in SHENWAN_L1.items():
        r = w.wset("IndexConstituent", f"date=20260510;windcode={code}")
        if r.ErrorCode == 0:
            items = parse_wset_result(r)
            for item in items:
                wc = item.get("wind_code", "")
                industry = item.get("industry", "")
                if wc:
                    company_industry_map[wc] = {"l1": name, "l1_code": code, "l2": industry}
            logger.info(f"  ✅ {name}: {len(items)} 只")
        time.sleep(0.3)

    logger.info(f"  行业映射: {len(company_industry_map)} 家公司")

    # ============================================================
    # Step 2: 获取公司基础信息 + 行情截面数据
    # ============================================================
    logger.info("\n📊 Step 2: 获取公司信息 + 行情数据...")

    companies = []
    company_industry_rels = []
    stock_codes = list(company_industry_map.keys())

    batch_size = 100  # 减小批量避免超时
    for i in range(0, len(stock_codes), batch_size):
        batch = stock_codes[i : i + batch_size]
        codes_str = ",".join(batch)

        r = w.wss(
            codes_str,
            "sec_name,ipo_date,total_shares,mkt_cap,pe_ttm,pe_lyr,pb_lf,close",
        )
        if r.ErrorCode == 0:
            items = parse_wss_result(r)
            # WSS 返回没有 wind_code 字段，需要按顺序对应
            for idx, item in enumerate(items):
                if idx < len(batch):
                    wc = batch[idx]
                else:
                    continue

                info = company_industry_map.get(wc, {})
                ipo_date = item.get("IPO_DATE", "")
                if ipo_date and hasattr(ipo_date, "strftime"):
                    ipo_date = ipo_date.strftime("%Y-%m-%d")

                exchange = "上海证券交易所" if ".SH" in wc else "深圳证券交易所"

                sec_name = item.get("SEC_NAME", "")

                comp = {
                    "name": sec_name,
                    "code": wc.split(".")[0],
                    "wind_code": wc,
                    "fullname": sec_name,
                    "location": exchange,
                    "time": ipo_date if ipo_date else "",
                    "total_shares": item.get("TOTAL_SHARES", ""),
                    "mkt_cap": item.get("MKT_CAP", ""),
                    "pe_ttm": item.get("PE_TTM", ""),
                    "pe_lyr": item.get("PE_LYR", ""),
                    "pb_lf": item.get("PB_LF", ""),
                    "close": item.get("CLOSE", ""),
                }
                companies.append(comp)

                if info.get("l1"):
                    company_industry_rels.append(
                        {
                            "company_name": comp["name"],
                            "industry_name": info["l1"],
                            "rel": "belong_to_industry",
                        }
                    )

        if (i // batch_size + 1) % 10 == 0:
            logger.info(f"  进度: {min(i + batch_size, len(stock_codes))}/{len(stock_codes)}")
        time.sleep(0.3)

    logger.info(f"  公司信息: {len(companies)} 条")
    logger.info(f"  公司-行业关系: {len(company_industry_rels)} 条")

    # ============================================================
    # Step 3: 构建行业实体
    # ============================================================
    logger.info("\n🏗️ Step 3: 构建行业实体...")
    industries = []

    for code, name in SHENWAN_L1.items():
        industries.append({"name": name, "code": code, "level": 1, "level1": name})

    for code, name in SHENWAN_L2.items():
        l1_code = code[:5] + "0.SI"
        l1_name = SHENWAN_L1.get(l1_code, "")
        industries.append(
            {
                "name": name,
                "code": code,
                "level": 2,
                "level1": l1_name,
                "level2": name,
            }
        )

    industry_rels = []
    for l1_code, l2_list in L1_TO_L2.items():
        l1_name = SHENWAN_L1.get(l1_code, "")
        for l2_code, l2_name in l2_list:
            industry_rels.append(
                {"from_industry": l1_name, "to_industry": l2_name, "rel": "parent_of"}
            )

    logger.info(f"  行业实体: {len(industries)} 个")
    logger.info(f"  行业关系: {len(industry_rels)} 条")

    # ============================================================
    # Step 4: 保存数据
    # ============================================================
    logger.info("\n💾 Step 4: 保存数据...")

    def save_jsonl(filename: str, data: list):
        path = data_path / filename
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"  ✅ {filename}: {len(data)} 条")

    save_jsonl("company.json", companies)
    save_jsonl("company_industry.json", company_industry_rels)
    save_jsonl("industry.json", industries)
    save_jsonl("industry_industry.json", industry_rels)
    save_jsonl("product.json", [])
    save_jsonl("company_product.json", [])
    save_jsonl("product_product.json", [])

    # ============================================================
    # 统计摘要
    # ============================================================
    logger.info("\n" + "=" * 60)
    logger.info("✅ Wind 数据导入完成!")
    logger.info("=" * 60)
    logger.info(f"  公司实体: {len(companies)} 个")
    logger.info(f"  行业实体: {len(industries)} 个")
    logger.info(f"  公司→行业: {len(company_industry_rels)} 条")
    logger.info(f"  行业→行业: {len(industry_rels)} 条")

    l1_counts = defaultdict(int)
    for rel in company_industry_rels:
        l1_counts[rel["industry_name"]] += 1

    logger.info("\n  行业分布 Top 10:")
    for name, count in sorted(l1_counts.items(), key=lambda x: -x[1])[:10]:
        logger.info(f"    {name}: {count} 家")


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    import_from_wind(data_dir)
