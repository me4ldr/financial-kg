"""
金融知识图谱 - 图谱本体定义
定义 3 类实体和 6 类关系的 Schema
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================
# 实体类型定义
# ============================================================

@dataclass
class EntityType:
    name: str
    label: str
    description: str
    attributes: Dict[str, str] = field(default_factory=dict)


ENTITY_TYPES = {
    "company": EntityType(
        name="company",
        label="Company",
        description="A股上市公司",
        attributes={
            "name": "股票简称",
            "code": "股票代码",
            "fullname": "公司全称",
            "location": "上市交易所",
            "list_date": "上市日期",
            "industry_l1": "申万一级行业",
            "industry_l2": "申万二级行业",
            "industry_l3": "申万三级行业",
        },
    ),
    "industry": EntityType(
        name="industry",
        label="Industry",
        description="申万行业分类",
        attributes={
            "name": "行业名称",
            "code": "行业代码",
            "level": "行业层级(1/2/3)",
            "level1": "一级行业",
            "level2": "二级行业",
            "level3": "三级行业",
        },
    ),
    "product": EntityType(
        name="product",
        label="Product",
        description="公司主营产品/业务",
        attributes={
            "name": "产品名称",
            "category": "产品类别",
            "revenue_ratio": "营收占比",
            "is_main": "是否主营",
        },
    ),
}


# ============================================================
# 关系类型定义
# ============================================================

@dataclass
class RelationType:
    name: str
    start_entity: str
    end_entity: str
    description: str
    attributes: Dict[str, str] = field(default_factory=dict)


RELATION_TYPES = {
    "belong_to_industry": RelationType(
        name="belong_to_industry",
        start_entity="company",
        end_entity="industry",
        description="公司所属行业",
    ),
    "parent_of": RelationType(
        name="parent_of",
        start_entity="industry",
        end_entity="industry",
        description="行业上级（父行业→子行业）",
    ),
    "main_product": RelationType(
        name="main_product",
        start_entity="company",
        end_entity="product",
        description="公司主营产品",
        attributes={"rel_weight": "营收占比权重"},
    ),
    "upstream_of": RelationType(
        name="upstream_of",
        start_entity="product",
        end_entity="product",
        description="产品上游原材料",
    ),
    "downstream_of": RelationType(
        name="downstream_of",
        start_entity="product",
        end_entity="product",
        description="产品下游成品",
    ),
    "subclass_of": RelationType(
        name="subclass_of",
        start_entity="product",
        end_entity="product",
        description="产品小类关系（子类→父类）",
    ),
}


def get_entity_labels() -> List[str]:
    return list(ENTITY_TYPES.keys())


def get_relation_labels() -> List[str]:
    return list(RELATION_TYPES.keys())


def print_schema():
    """打印图谱 Schema"""
    print("=" * 60)
    print("金融产业链知识图谱 - Schema")
    print("=" * 60)
    print("\n【实体类型】")
    for et in ENTITY_TYPES.values():
        print(f"  {et.label} ({et.name}): {et.description}")
        for attr, desc in et.attributes.items():
            print(f"    - {attr}: {desc}")
    print("\n【关系类型】")
    for rt in RELATION_TYPES.values():
        print(f"  {rt.name}: {ENTITY_TYPES[rt.start_entity].label} → "
              f"{ENTITY_TYPES[rt.end_entity].label} ({rt.description})")
        for attr, desc in rt.attributes.items():
            print(f"    - {attr}: {desc}")


if __name__ == "__main__":
    print_schema()
