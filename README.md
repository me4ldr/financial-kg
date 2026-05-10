# Financial Chain Knowledge Graph (Financial_KG)

全行业知识图谱 - 面向 A 股上市公司的产业链图谱

## 项目简介

参考刘焕勇老师的 [ChainKnowledgeGraph](https://github.com/liuhuanyong/ChainKnowledgeGraph)，构建面向金融领域的上市公司产业链知识图谱。

## 知识图谱 Schema

### 3 类实体

| 实体类型 | 说明 | 属性 |
|---------|------|------|
| **公司 (Company)** | A 股上市公司 | name, code, fullname, location, list_date, industry_code |
| **行业 (Industry)** | 申万三级行业分类 | name, level, level1, level2, level3, code |
| **产品 (Product)** | 公司主营产品/业务 | name, category, revenue_ratio |

### 6 类关系

| 关系类型 | 起点 | 终点 | 说明 | 属性 |
|---------|------|------|------|------|
| **belong_to_industry** | Company | Industry | 公司所属行业 | - |
| **parent_of** | Industry | Industry | 行业上级（三级分类） | - |
| **main_product** | Company | Product | 公司主营产品 | rel_weight（营收占比） |
| **upstream_of** | Product | Product | 产品上游原材料 | - |
| **downstream_of** | Product | Product | 产品下游成品 | - |
| **subclass_of** | Product | Product | 产品小类关系 | - |

### 图谱规模（目标）

| 实体/关系 | 数量 |
|----------|------|
| 上市公司 | ~5,300 家 |
| 行业 | ~511 个 |
| 产品 | ~95,000 条 |
| 上游材料 | ~56,000 条 |
| 上级行业 | ~480 条 |
| 下游产品 | ~390 条 |
| 产品小类 | ~52,000 条 |
| 所属行业 | ~3,900 条 |

## 数据来源

- **申万行业分类**: http://www.swsindex.com
- **上交所**: http://www.sse.com.cn
- **深交所**: http://www.szse.cn
- **Tushare Pro**: https://tushare.pro
- **公司公告/年报**: 巨潮资讯、东方财富

## 项目结构

```
financial_kg/
├── src/
│   ├── __init__.py
│   ├── kg_builder.py         # 知识图谱构建器
│   ├── data_loader.py        # 数据加载（Tushare/本地文件）
│   ├── extractor/
│   │   ├── __init__.py
│   │   ├── base.py           # 抽取器基类
│   │   ├── rule_extractor.py  # 基于规则的抽取
│   │   └── llm_extractor.py  # 基于 LLM 的抽取
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── local_store.py    # NetworkX 本地图存储
│   │   └── neo4j_store.py    # Neo4j 图数据库存储
│   ├── query/
│   │   ├── __init__.py
│   │   └── cypher_query.py   # Cypher 查询接口
│   ├── visualize/
│   │   ├── __init__.py
│   │   └── pyvis_viz.py      # PyVis 可视化
│   └── schema/
│       ├── __init__.py
│       └── ontology.py       # 图谱本体定义
├── data/                     # 原始数据 & 构建后的 JSON
├── output/                   # 输出结果（图谱可视化、分析报告）
├── config/
│   └── .env.example          # 环境变量配置
├── scripts/
│   ├── build_kg.py           # 一键构建图谱
│   └── query_kg.py           # 查询示例
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp config/.env.example config/.env
# 编辑 .env 填入 Tushare Token、Neo4j 配置等
```

### 3. 构建图谱

```bash
# 使用本地存储（无需 Neo4j）
python scripts/build_kg.py --store local

# 使用 Neo4j 存储
python scripts/build_kg.py --store neo4j
```

### 4. 查询示例

```bash
python scripts/query_kg.py
```

## Neo4j 配置

本项目使用 Neo4j 作为主图数据库，支持本地 Docker 或远程部署。

### 本地 Docker 快速启动

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| NEO4J_URI | Neo4j 连接 URI | bolt://localhost:7687 |
| NEO4J_USER | 用户名 | neo4j |
| NEO4J_PASSWORD | 密码 | password |

## 技术架构

1. **数据获取**: Tushare API + 爬虫 → 原始数据
2. **实体抽取**: 规则匹配 + LLM → 结构化实体
3. **关系构建**: 启发式规则 + 模式匹配 → 关系三元组
4. **图谱存储**: NetworkX（本地）/ Neo4j（生产）
5. **查询分析**: Cypher 查询 + Python 接口
6. **可视化**: PyVis 交互式图谱展示

## License

Private
