# 金融知识图谱项目 - 任务清单

> 创建时间: 2026-05-11 00:36
> 目标: 构建完整的金融产业链知识图谱并生成可视化

## 📊 当前状态

- ✅ 项目已初始化 (`~/projects/financial_kg/`)
- ✅ Wind 数据导入完成 (5199 公司, 157 行业, 52931 产品, 68003 关系)
- ✅ 图谱构建通过 (58071 节点, 73328 边)
- ✅ pyvis 已安装
- ✅ 完整图谱可视化已生成 (kg_full_graph.html, 采样 3000 节点)
- ✅ 7 家公司关联链可视化已生成
- ❌ 产品→产品关系 (0 条)
- ❌ Tushare 数据源 (Token 无效/转接 API 超时)
- ❌ Neo4j 未对接

## 🔧 接下来的任务

### 1. 安装依赖 [✅ 完成]
- [x] `pip install pyvis networkx`
- [x] 验证导入成功

### 2. 生成可视化 [✅ 完成]
- [x] 使用 pyvis 生成完整图谱 HTML（采样 3000 节点）
- [x] 生成 7 家重点公司关联链可视化
  - 宁德时代、贵州茅台、药明康德、工商银行、比亚迪、恒瑞医药、中芯国际

### 3. Tushare 数据接入 [❌ 受阻]
- [x] 查看 Dr.X 项目的 Tushare 使用方式
- [x] 测试 Tushare 原生 API (Token 无效)
- [x] 测试 Tushare 转接 API (超时不可用)
- [ ] 需要若若姐提供正确的 Tushare Token 或 API 地址

### 4. 输出交付物 [✅ 完成]
- [x] 完整图谱 JSON 文件 (financial_kg.json, 18MB)
- [x] 交互式 HTML 可视化 (8 个文件)
- [x] 项目 README 更新
- [x] 任务文档 (TASKS.md)

## 📝 笔记

- Wind 可用字段: `segment_sales`, `majorproductname`, `majorproducttype`
- Wind 不可用: `segment_profit` (权限不足)
- Tushare Token 需要确认（当前 token 无效）
- Tushare 转接 API: `https://tushare.indevs.in/tushare/pro` (超时)
- Dr.X 项目路径: `/Users/xinyuan/projects/medical-announcement-scraper/`
- Dr.X 有 Wind segment.py 模块可以参考
- 定时任务已设置：每 10 分钟汇报进度
