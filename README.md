# Financial Knowledge Graph (financial_kg)

金融领域知识图谱项目

## 项目简介

构建面向金融领域的知识图谱，支持实体关系抽取、图谱存储、查询分析和可视化。

## 技术栈

- **Python 3.10+**
- **NetworkX** — 图计算与分析
- **py2neo / Neo4j** — 图数据库
- **spaCy / LLM** — NLP 实体识别与关系抽取
- **Streamlit / D3.js** — 图谱可视化

## 项目结构

```
financial_kg/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── pipeline.py         # 数据处理流水线
│   ├── extractor/          # 实体与关系抽取
│   ├── storage/            # 图存储（Neo4j/本地）
│   ├── query/              # 查询接口
│   └── visualize/          # 可视化
├── config/                 # 配置文件
├── data/                   # 原始数据
├── output/                 # 输出结果
├── scripts/                # 辅助脚本
├── tests/                  # 测试
├── docs/                   # 文档
├── requirements.txt
└── README.md
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp config/.env.example config/.env
# 编辑 .env 填入必要配置

# 3. 运行示例
python src/pipeline.py
```

## 开发规范

- 使用 Black 格式化代码
- 单元测试覆盖率 > 80%
- Commit message 遵循 conventional commits

## License

Private
