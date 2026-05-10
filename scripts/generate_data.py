#!/usr/bin/env python3
# coding: utf-8
"""
金融知识图谱 - 示例数据生成器
生成模拟的产业链知识图谱数据（公司、行业、产品及其关系）
数据规模参考 ChainKnowledgeGraph 项目
"""
import json
import logging
import random
import os
from pathlib import Path

logger = logging.getLogger("financial_kg")
random.seed(42)


# ============================================================
# 申万行业分类（2021版简化）
# ============================================================
SHENWAN_INDUSTRIES_L1 = [
    "农林牧渔", "基础化工", "钢铁", "有色金属", "电子", "家用电器",
    "食品饮料", "纺织服饰", "轻工制造", "医药生物", "公用事业",
    "交通运输", "房地产", "商贸零售", "社会服务", "综合",
    "建筑材料", "建筑装饰", "电力设备", "机械设备", "国防军工",
    "计算机", "传媒", "通信", "银行", "非银金融", "煤炭",
    "石油石化", "环保", "美容护理", "汽车",
]

# 每个一级行业下的二级行业（部分示例）
SHENWAN_INDUSTRIES_L2 = {
    "农林牧渔": ["种植业", "林业", "渔业", "动物保健", "农产品加工", "饲料"],
    "电子": ["半导体", "光学光电子", "电子化学品", "消费电子", "元器件", "被动元件"],
    "医药生物": ["化学制药", "中药", "生物制品", "医疗器械", "医疗服务", "医药商业"],
    "计算机": ["软件开发", "IT服务", "计算机设备", "通信设备"],
    "银行": ["国有大型银行", "股份制银行", "城商行", "农商行"],
    "非银金融": ["证券", "保险", "多元金融"],
    "电力设备": ["电池", "光伏设备", "风电设备", "电网设备", "电机"],
    "汽车": ["乘用车", "商用车", "汽车零部件", "汽车服务"],
    "食品饮料": ["白酒", "啤酒", "肉制品", "乳制品", "调味品", "休闲食品"],
    "有色金属": ["铜", "铝", "黄金", "稀土", "锂", "铅锌"],
    "基础化工": ["化肥", "农药", "涂料", "塑料", "橡胶", "化纤", "化工新材料"],
    "机械设备": ["工程机械", "农业机械", "机床", "机器人", "仪器仪表"],
    "通信": ["电信运营", "通信设备", "通信服务"],
    "传媒": ["游戏", "影视", "广告营销", "出版"],
    "房地产": ["住宅开发", "商业地产", "产业地产"],
    "公用事业": ["电力", "燃气", "水务"],
    "钢铁": ["普钢", "特钢"],
    "建筑材料": ["水泥", "玻璃", "管材", "防水材料"],
    "国防军工": ["航空装备", "航天装备", "船舶制造", "地面兵装"],
    "社会服务": ["酒店餐饮", "旅游", "教育", "体育"],
    "美容护理": ["化妆品", "个护用品"],
    "石油石化": ["石油开采", "油服工程", "石油化工"],
    "煤炭": ["动力煤", "焦煤", "焦炭"],
    "环保": ["大气治理", "水处理", "固废治理"],
    "纺织服饰": ["纺织制造", "服装家纺"],
    "商贸零售": ["百货零售", "超市", "电商"],
    "交通运输": ["航空", "航运", "物流", "公路铁路", "港口"],
    "建筑装饰": ["房屋建设", "基础建设", "专业工程", "装修装饰"],
    "轻工制造": ["造纸", "包装印刷", "家居用品"],
    "综合": ["综合"],
}


# ============================================================
# 上市公司数据（模拟）
# ============================================================
COMPANY_SAMPLES = [
    # 银行
    {"name": "工商银行", "fullname": "中国工商银行股份有限公司", "code": "601398", "location": "上海证券交易所", "time": "2006-10-27"},
    {"name": "建设银行", "fullname": "中国建设银行股份有限公司", "code": "601939", "location": "上海证券交易所", "time": "2007-09-25"},
    {"name": "招商银行", "fullname": "招商银行股份有限公司", "code": "600036", "location": "上海证券交易所", "time": "2002-04-09"},
    {"name": "平安银行", "fullname": "平安银行股份有限公司", "code": "000001", "location": "深圳证券交易所", "time": "1991-04-03"},
    {"name": "农业银行", "fullname": "中国农业银行股份有限公司", "code": "601288", "location": "上海证券交易所", "time": "2010-07-15"},
    {"name": "中国银行", "fullname": "中国银行股份有限公司", "code": "601988", "location": "上海证券交易所", "time": "2006-07-05"},
    # 非银金融
    {"name": "中国平安", "fullname": "中国平安保险（集团）股份有限公司", "code": "601318", "location": "上海证券交易所", "time": "2007-03-01"},
    {"name": "中信证券", "fullname": "中信证券股份有限公司", "code": "600030", "location": "上海证券交易所", "time": "2003-01-06"},
    {"name": "华泰证券", "fullname": "华泰证券股份有限公司", "code": "601688", "location": "上海证券交易所", "time": "2010-02-26"},
    {"name": "中国太保", "fullname": "中国太平洋保险（集团）股份有限公司", "code": "601601", "location": "上海证券交易所", "time": "2007-12-25"},
    # 电子
    {"name": "中芯国际", "fullname": "中芯国际集成电路制造有限公司", "code": "688981", "location": "上海证券交易所", "time": "2020-07-16"},
    {"name": "立讯精密", "fullname": "立讯精密工业股份有限公司", "code": "002475", "location": "深圳证券交易所", "time": "2010-09-15"},
    {"name": "京东方A", "fullname": "京东方科技集团股份有限公司", "code": "000725", "location": "深圳证券交易所", "time": "1997-06-10"},
    {"name": "韦尔股份", "fullname": "上海韦尔半导体股份有限公司", "code": "603501", "location": "上海证券交易所", "time": "2017-05-04"},
    {"name": "兆易创新", "fullname": "兆易创新科技集团股份有限公司", "code": "603986", "location": "上海证券交易所", "time": "2016-08-18"},
    # 医药
    {"name": "恒瑞医药", "fullname": "江苏恒瑞医药股份有限公司", "code": "600276", "location": "上海证券交易所", "time": "2000-10-18"},
    {"name": "迈瑞医疗", "fullname": "深圳迈瑞生物医疗电子股份有限公司", "code": "300760", "location": "深圳证券交易所", "time": "2018-10-16"},
    {"name": "药明康德", "fullname": "无锡药明康德新药开发股份有限公司", "code": "603259", "location": "上海证券交易所", "time": "2018-05-08"},
    {"name": "片仔癀", "fullname": "漳州片仔癀药业股份有限公司", "code": "600436", "location": "上海证券交易所", "time": "2003-06-16"},
    {"name": "云南白药", "fullname": "云南白药集团股份有限公司", "code": "000538", "location": "深圳证券交易所", "time": "1993-12-15"},
    # 电力设备/新能源
    {"name": "宁德时代", "fullname": "宁德时代新能源科技股份有限公司", "code": "300750", "location": "深圳证券交易所", "time": "2018-06-11"},
    {"name": "比亚迪", "fullname": "比亚迪股份有限公司", "code": "002594", "location": "深圳证券交易所", "time": "2011-06-30"},
    {"name": "隆基绿能", "fullname": "隆基绿能科技股份有限公司", "code": "601012", "location": "上海证券交易所", "time": "2012-04-11"},
    {"name": "阳光电源", "fullname": "阳光电源股份有限公司", "code": "300274", "location": "深圳证券交易所", "time": "2011-12-06"},
    {"name": "亿纬锂能", "fullname": "惠州亿纬锂能股份有限公司", "code": "300014", "location": "深圳证券交易所", "time": "2009-10-30"},
    # 食品饮料
    {"name": "贵州茅台", "fullname": "贵州茅台酒股份有限公司", "code": "600519", "location": "上海证券交易所", "time": "2001-08-27"},
    {"name": "五粮液", "fullname": "宜宾五粮液股份有限公司", "code": "000858", "location": "深圳证券交易所", "time": "1998-04-27"},
    {"name": "伊利股份", "fullname": "内蒙古伊利实业集团股份有限公司", "code": "600887", "location": "上海证券交易所", "time": "1996-03-20"},
    {"name": "海天味业", "fullname": "佛山市海天调味食品股份有限公司", "code": "603288", "location": "上海证券交易所", "time": "2014-02-11"},
    # 计算机
    {"name": "科大讯飞", "fullname": "科大讯飞股份有限公司", "code": "002230", "location": "深圳证券交易所", "time": "2008-05-12"},
    {"name": "金山办公", "fullname": "北京金山办公软件股份有限公司", "code": "688111", "location": "上海证券交易所", "time": "2019-11-18"},
    {"name": "恒生电子", "fullname": "恒生电子股份有限公司", "code": "600570", "location": "上海证券交易所", "time": "2003-12-16"},
    {"name": "用友网络", "fullname": "用友网络科技股份有限公司", "code": "600588", "location": "上海证券交易所", "time": "2001-05-18"},
    # 汽车
    {"name": "长城汽车", "fullname": "长城汽车股份有限公司", "code": "601633", "location": "上海证券交易所", "time": "2011-09-28"},
    {"name": "长安汽车", "fullname": "重庆长安汽车股份有限公司", "code": "000625", "location": "深圳证券交易所", "time": "1997-06-26"},
    {"name": "福耀玻璃", "fullname": "福耀玻璃工业集团股份有限公司", "code": "600660", "location": "上海证券交易所", "time": "1993-06-10"},
    # 有色金属
    {"name": "紫金矿业", "fullname": "紫金矿业集团股份有限公司", "code": "601899", "location": "上海证券交易所", "time": "2008-04-25"},
    {"name": "赣锋锂业", "fullname": "江西赣锋锂业集团股份有限公司", "code": "002460", "location": "深圳证券交易所", "time": "2010-08-10"},
    {"name": "天齐锂业", "fullname": "天齐锂业股份有限公司", "code": "002466", "location": "深圳证券交易所", "time": "2010-09-13"},
    # 基础化工
    {"name": "万华化学", "fullname": "万华化学集团股份有限公司", "code": "600309", "location": "上海证券交易所", "time": "2001-01-05"},
    {"name": "荣盛石化", "fullname": "荣盛石化股份有限公司", "code": "002493", "location": "深圳证券交易所", "time": "2010-11-02"},
    {"name": "恒力石化", "fullname": "恒力石化股份有限公司", "code": "600346", "location": "上海证券交易所", "time": "2016-09-09"},
    # 机械设备
    {"name": "三一重工", "fullname": "三一重工股份有限公司", "code": "600031", "location": "上海证券交易所", "time": "2003-07-03"},
    {"name": "汇川技术", "fullname": "深圳市汇川技术股份有限公司", "code": "300124", "location": "深圳证券交易所", "time": "2010-09-28"},
    {"name": "徐工机械", "fullname": "徐工集团工程机械股份有限公司", "code": "000425", "location": "深圳证券交易所", "time": "1996-08-28"},
    # 通信
    {"name": "中兴通讯", "fullname": "中兴通讯股份有限公司", "code": "000063", "location": "深圳证券交易所", "time": "1997-11-18"},
    {"name": "中国移动", "fullname": "中国移动通信集团有限公司", "code": "600941", "location": "上海证券交易所", "time": "2022-01-05"},
    # 传媒
    {"name": "芒果超媒", "fullname": "芒果超媒传媒股份有限公司", "code": "300413", "location": "深圳证券交易所", "time": "2015-06-02"},
    {"name": "分众传媒", "fullname": "分众传媒信息技术股份有限公司", "code": "002027", "location": "深圳证券交易所", "time": "2004-08-04"},
    # 房地产
    {"name": "万科A", "fullname": "万科企业股份有限公司", "code": "000002", "location": "深圳证券交易所", "time": "1991-01-29"},
    {"name": "保利发展", "fullname": "保利发展控股集团股份有限公司", "code": "600048", "location": "上海证券交易所", "time": "1994-03-23"},
    # 更多公司...
    {"name": "中国石油", "fullname": "中国石油天然气股份有限公司", "code": "601857", "location": "上海证券交易所", "time": "2007-11-05"},
    {"name": "中国石化", "fullname": "中国石油化工股份有限公司", "code": "600028", "location": "上海证券交易所", "time": "2001-08-08"},
    {"name": "长江电力", "fullname": "中国长江电力股份有限公司", "code": "600900", "location": "上海证券交易所", "time": "2003-11-18"},
    {"name": "中国神华", "fullname": "中国神华能源股份有限公司", "code": "601088", "location": "上海证券交易所", "time": "2007-10-09"},
    {"name": "宝钢股份", "fullname": "宝山钢铁股份有限公司", "code": "600019", "location": "上海证券交易所", "time": "2000-02-24"},
    {"name": "海螺水泥", "fullname": "安徽海螺水泥股份有限公司", "code": "600585", "location": "上海证券交易所", "time": "2002-02-07"},
    {"name": "顺丰控股", "fullname": "顺丰控股股份有限公司", "code": "002352", "location": "深圳证券交易所", "time": "2010-03-05"},
    {"name": "中远海控", "fullname": "中远海运控股股份有限公司", "code": "601919", "location": "上海证券交易所", "time": "2007-06-26"},
]


# ============================================================
# 产品数据
# ============================================================
PRODUCT_SAMPLES = [
    # 银行产品
    "个人贷款", "企业贷款", "信用卡业务", "理财产品", "存款业务", "国际结算",
    # 保险产品
    "人寿保险", "财产保险", "健康保险", "车险", "养老保险",
    # 证券业务
    "证券经纪", "投资银行", "资产管理", "自营业务", "融资融券",
    # 电子/半导体
    "芯片", "晶圆代工", "LED芯片", "OLED面板", "LCD面板", "CIS传感器",
    "存储芯片", "MCU芯片", "功率半导体", "射频芯片", "模拟芯片",
    # 医药产品
    "抗肿瘤药", "心血管药", "疫苗", "血液制品", "诊断试剂", "医疗器械",
    "中药处方药", "OTC药品", "CRO服务", "CDMO服务",
    # 新能源
    "动力电池", "储能电池", "光伏组件", "光伏逆变器", "风电整机",
    "锂电池正极材料", "锂电池负极材料", "电解液", "隔膜",
    # 汽车
    "乘用车", "SUV", "新能源汽车", "动力电池系统", "汽车玻璃",
    "汽车发动机", "变速器", "底盘系统", "智能驾驶系统",
    # 食品饮料
    "茅台酒", "五粮液酒", "液态奶", "奶粉", "酱油", "调味品",
    # 软件/IT
    "语音识别", "AI大模型", "办公软件", "ERP系统", "金融IT系统",
    # 化工
    "MDI", "TDI", "PTA", "聚酯切片", "化肥", "农药",
    # 机械
    "挖掘机", "起重机", "工业机器人", "伺服电机", "变频器",
    # 通信
    "5G基站", "光模块", "光纤光缆", "通信网络服务",
    # 有色金属
    "铜精矿", "电解铜", "氧化铝", "电解铝", "金锭", "碳酸锂",
    # 钢铁建材
    "热轧板", "冷轧板", "螺纹钢", "水泥", "浮法玻璃",
    # 传媒
    "网络游戏", "影视剧", "广告", "出版发行",
    # 地产
    "住宅地产", "商业地产", "物业管理",
    # 公用事业
    "电力供应", "天然气", "自来水",
    # 物流
    "快递物流", "冷链物流", "跨境物流",
    # 石油
    "原油开采", "成品油", "石化产品",
    # 煤炭
    "动力煤", "焦煤", "焦炭",
    # 原材料
    "碳酸钠", "烧碱", "硫酸", "盐酸", "纯碱", "钛白粉",
    "硅料", "硅片", "铜箔", "铝箔", "钢材", "橡胶",
    "塑料粒子", "玻璃纤维", "碳纤维",
    # 农产品
    "玉米", "大豆", "小麦", "棉花", "白糖", "猪肉",
]


# ============================================================
# 产品上下游关系
# ============================================================
PRODUCT_RELATIONS = [
    # 锂电池产业链
    {"from_entity": "碳酸锂", "to_entity": "锂电池正极材料", "rel": "upstream_of"},
    {"from_entity": "正极材料", "to_entity": "动力电池", "rel": "upstream_of"},
    {"from_entity": "负极材料", "to_entity": "动力电池", "rel": "upstream_of"},
    {"from_entity": "电解液", "to_entity": "动力电池", "rel": "upstream_of"},
    {"from_entity": "隔膜", "to_entity": "动力电池", "rel": "upstream_of"},
    {"from_entity": "铜箔", "to_entity": "锂电池负极材料", "rel": "upstream_of"},
    {"from_entity": "铝箔", "to_entity": "锂电池正极材料", "rel": "upstream_of"},
    {"from_entity": "动力电池", "to_entity": "新能源汽车", "rel": "upstream_of"},
    {"from_entity": "动力电池", "to_entity": "储能电池", "rel": "subclass_of"},
    # 光伏产业链
    {"from_entity": "硅料", "to_entity": "硅片", "rel": "upstream_of"},
    {"from_entity": "硅片", "to_entity": "光伏组件", "rel": "upstream_of"},
    {"from_entity": "光伏组件", "to_entity": "光伏逆变器", "rel": "upstream_of"},
    # 汽车产业链
    {"from_entity": "钢材", "to_entity": "汽车发动机", "rel": "upstream_of"},
    {"from_entity": "钢材", "to_entity": "底盘系统", "rel": "upstream_of"},
    {"from_entity": "橡胶", "to_entity": "汽车玻璃", "rel": "upstream_of"},
    {"from_entity": "汽车发动机", "to_entity": "乘用车", "rel": "upstream_of"},
    {"from_entity": "动力电池系统", "to_entity": "新能源汽车", "rel": "upstream_of"},
    {"from_entity": "智能驾驶系统", "to_entity": "新能源汽车", "rel": "upstream_of"},
    # 半导体产业链
    {"from_entity": "晶圆代工", "to_entity": "芯片", "rel": "upstream_of"},
    {"from_entity": "芯片", "to_entity": "CIS传感器", "rel": "subclass_of"},
    {"from_entity": "芯片", "to_entity": "MCU芯片", "rel": "subclass_of"},
    {"from_entity": "芯片", "to_entity": "存储芯片", "rel": "subclass_of"},
    {"from_entity": "芯片", "to_entity": "功率半导体", "rel": "subclass_of"},
    # 显示面板
    {"from_entity": "LED芯片", "to_entity": "OLED面板", "rel": "upstream_of"},
    {"from_entity": "LED芯片", "to_entity": "LCD面板", "rel": "upstream_of"},
    # 化工
    {"from_entity": "原油开采", "to_entity": "PTA", "rel": "upstream_of"},
    {"from_entity": "PTA", "to_entity": "聚酯切片", "rel": "upstream_of"},
    {"from_entity": "纯碱", "to_entity": "浮法玻璃", "rel": "upstream_of"},
    {"from_entity": "钛白粉", "to_entity": "塑料粒子", "rel": "upstream_of"},
    # 医药
    {"from_entity": "CRO服务", "to_entity": "抗肿瘤药", "rel": "upstream_of"},
    {"from_entity": "CDMO服务", "to_entity": "疫苗", "rel": "upstream_of"},
    # 钢铁
    {"from_entity": "热轧板", "to_entity": "冷轧板", "rel": "upstream_of"},
    {"from_entity": "螺纹钢", "to_entity": "钢材", "rel": "subclass_of"},
    # 白酒
    {"from_entity": "高粱", "to_entity": "茅台酒", "rel": "upstream_of"},
    {"from_entity": "小麦", "to_entity": "五粮液酒", "rel": "upstream_of"},
    {"from_entity": "大豆", "to_entity": "酱油", "rel": "upstream_of"},
    # 物流
    {"from_entity": "快递物流", "to_entity": "冷链物流", "rel": "subclass_of"},
    # 通信
    {"from_entity": "光模块", "to_entity": "5G基站", "rel": "upstream_of"},
    {"from_entity": "光纤光缆", "to_entity": "5G基站", "rel": "upstream_of"},
    # 机械
    {"from_entity": "伺服电机", "to_entity": "工业机器人", "rel": "upstream_of"},
    {"from_entity": "变频器", "to_entity": "工业机器人", "rel": "upstream_of"},
    # 传媒
    {"from_entity": "影视剧", "to_entity": "网络游戏", "rel": "subclass_of"},
]


def generate_sample_data(output_dir: str):
    """生成示例数据"""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # 1. 生成行业数据
    industries = []
    industry_relations = []

    for l1 in SHENWAN_INDUSTRIES_L1:
        # 一级行业
        industries.append({
            "name": l1,
            "level": 1,
            "level1": l1,
        })
        l2_list = SHENWAN_INDUSTRIES_L2.get(l1, [])
        for l2 in l2_list:
            # 二级行业
            industries.append({
                "name": l2,
                "level": 2,
                "level1": l1,
                "level2": l2,
            })
            # 行业上级关系
            industry_relations.append({
                "from_industry": l1,
                "to_industry": l2,
                "rel": "parent_of",
            })

    logger.info(f"行业实体: {len(industries)} 个")
    logger.info(f"行业关系: {len(industry_relations)} 条")

    # 保存行业数据
    _save_jsonl(output / "industry.json", industries)
    _save_jsonl(output / "industry_industry.json", industry_relations)

    # 2. 生成公司数据
    companies = []
    company_industry_rels = []

    industry_assignments = {
        "工商银行": "国有大型银行", "建设银行": "国有大型银行", "农业银行": "国有大型银行",
        "中国银行": "国有大型银行", "招商银行": "股份制银行", "平安银行": "股份制银行",
        "中国平安": "保险", "中国太保": "保险",
        "中信证券": "证券", "华泰证券": "证券",
        "中芯国际": "半导体", "立讯精密": "消费电子", "京东方A": "光学光电子",
        "韦尔股份": "半导体", "兆易创新": "半导体",
        "恒瑞医药": "化学制药", "迈瑞医疗": "医疗器械", "药明康德": "CRO服务",
        "片仔癀": "中药", "云南白药": "中药",
        "宁德时代": "电池", "比亚迪": "乘用车", "隆基绿能": "光伏设备",
        "阳光电源": "光伏设备", "亿纬锂能": "电池",
        "贵州茅台": "白酒", "五粮液": "白酒", "伊利股份": "乳制品",
        "海天味业": "调味品",
        "科大讯飞": "软件开发", "金山办公": "软件开发", "恒生电子": "软件开发",
        "用友网络": "软件开发",
        "长城汽车": "乘用车", "长安汽车": "乘用车", "福耀玻璃": "汽车零部件",
        "紫金矿业": "黄金", "赣锋锂业": "锂", "天齐锂业": "锂",
        "万华化学": "化工新材料", "荣盛石化": "化纤", "恒力石化": "化纤",
        "三一重工": "工程机械", "汇川技术": "仪器仪表", "徐工机械": "工程机械",
        "中兴通讯": "通信设备", "中国移动": "电信运营",
        "芒果超媒": "游戏", "分众传媒": "广告营销",
        "万科A": "住宅开发", "保利发展": "住宅开发",
        "中国石油": "石油开采", "中国石化": "石油化工",
        "长江电力": "电力", "中国神华": "动力煤",
        "宝钢股份": "普钢", "海螺水泥": "水泥",
        "顺丰控股": "物流", "中远海控": "航运",
    }

    for comp in COMPANY_SAMPLES:
        companies.append(comp)
        ind = industry_assignments.get(comp["name"], "综合")
        company_industry_rels.append({
            "company_name": comp["name"],
            "industry_name": ind,
            "rel": "belong_to_industry",
        })

    logger.info(f"公司实体: {len(companies)} 个")
    logger.info(f"公司-行业关系: {len(company_industry_rels)} 条")

    # 保存公司数据
    _save_jsonl(output / "company.json", companies)
    _save_jsonl(output / "company_industry.json", company_industry_rels)

    # 3. 生成产品数据
    products = [{"name": p} for p in PRODUCT_SAMPLES]
    logger.info(f"产品实体: {len(products)} 个")
    _save_jsonl(output / "product.json", products)

    # 4. 生成公司-产品关系
    company_product_rels = []
    company_products = {
        "工商银行": ["个人贷款", "企业贷款", "信用卡业务", "理财产品"],
        "招商银行": ["个人贷款", "信用卡业务", "理财产品"],
        "中国平安": ["人寿保险", "财产保险", "健康保险", "养老保险"],
        "中信证券": ["证券经纪", "投资银行", "资产管理"],
        "宁德时代": ["动力电池", "储能电池"],
        "比亚迪": ["新能源汽车", "动力电池系统"],
        "隆基绿能": ["光伏组件", "光伏逆变器"],
        "恒瑞医药": ["抗肿瘤药", "心血管药"],
        "迈瑞医疗": ["医疗器械", "诊断试剂"],
        "药明康德": ["CRO服务", "CDMO服务"],
        "贵州茅台": ["茅台酒"],
        "科大讯飞": ["语音识别", "AI大模型"],
        "金山办公": ["办公软件"],
        "汇川技术": ["伺服电机", "变频器"],
        "紫金矿业": ["金锭", "电解铜"],
        "赣锋锂业": ["碳酸锂"],
        "万华化学": ["MDI", "TDI"],
        "三一重工": ["挖掘机", "起重机"],
        "中兴通讯": ["5G基站"],
        "福耀玻璃": ["汽车玻璃"],
        "顺丰控股": ["快递物流", "冷链物流"],
        "中国石油": ["原油开采", "成品油"],
        "中国神华": ["动力煤"],
        "宝钢股份": ["热轧板", "冷轧板"],
        "海螺水泥": ["水泥"],
        "伊利股份": ["液态奶", "奶粉"],
        "五粮液": ["五粮液酒"],
        "海天味业": ["酱油", "调味品"],
    }

    for comp_name, prod_list in company_products.items():
        for prod in prod_list:
            company_product_rels.append({
                "company_name": comp_name,
                "product_name": prod,
                "rel": "main_product",
                "rel_weight": round(random.uniform(0.1, 0.8), 2),
            })

    logger.info(f"公司-产品关系: {len(company_product_rels)} 条")
    _save_jsonl(output / "company_product.json", company_product_rels)

    # 5. 保存产品关系
    logger.info(f"产品关系: {len(PRODUCT_RELATIONS)} 条")
    _save_jsonl(output / "product_product.json", PRODUCT_RELATIONS)

    # 打印统计
    logger.info("\n📊 数据生成完成:")
    logger.info(f"  公司实体: {len(companies)} 个")
    logger.info(f"  行业实体: {len(industries)} 个")
    logger.info(f"  产品实体: {len(products)} 个")
    logger.info(f"  公司→行业: {len(company_industry_rels)} 条")
    logger.info(f"  行业→行业: {len(industry_relations)} 条")
    logger.info(f"  公司→产品: {len(company_product_rels)} 条")
    logger.info(f"  产品→产品: {len(PRODUCT_RELATIONS)} 条")


def _save_jsonl(path: Path, data: list):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info(f"✅ 保存 → {path} ({len(data)} 条)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    generate_sample_data(data_dir)
