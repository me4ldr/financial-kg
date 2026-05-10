"""
金融知识图谱 - PyVis 可视化
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("financial_kg")

# 节点颜色映射
NODE_COLORS = {
    "company": "#4CAF50",    # 绿色
    "industry": "#2196F3",   # 蓝色
    "product": "#FF9800",    # 橙色
}

# 节点大小映射
NODE_SIZES = {
    "company": 20,
    "industry": 30,
    "product": 15,
}


def visualize_kg(
    graph_store,
    output_path: str = "output/kg_visualization.html",
    max_nodes: int = 500,
    title: str = "金融产业链知识图谱",
):
    """使用 PyVis 可视化知识图谱"""
    try:
        from pyvis.network import Network
    except ImportError:
        logger.error("请安装 pyvis: pip install pyvis")
        raise

    net = Network(height="800px", width="100%", directed=True, bgcolor="#222222", font_color="white")
    net.barnes_hut(
        gravity=-80000,
        central_gravity=0.3,
        spring_length=250,
        spring_strength=0.001,
        damping=0.09,
        overlap=0,
    )

    # 添加节点
    nodes = graph_store.get_all_nodes()
    if len(nodes) > max_nodes:
        logger.info(f"节点数 {len(nodes)} > {max_nodes}，随机采样 {max_nodes} 个")
        import random
        nodes = random.sample(nodes, max_nodes)

    node_id_set = set()
    for node in nodes:
        nid = node["id"]
        node_type = node.get("node_type", "unknown")
        color = NODE_COLORS.get(node_type, "#999999")
        size = NODE_SIZES.get(node_type, 15)

        # 显示标签（简称优先）
        label = node.get("name", nid)
        if len(label) > 20:
            label = label[:20] + "..."

        net.add_node(
            nid,
            label=label,
            title=f"{node_type}: {node.get('name', nid)}",
            color=color,
            size=size,
            shape="dot",
        )
        node_id_set.add(nid)

    # 添加边
    edges = graph_store.get_all_edges()
    edge_count = 0
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source in node_id_set and target in node_id_set:
            relation = edge.get("relation", "related_to")
            net.add_edge(source, target, title=relation, width=1)
            edge_count += 1

    # 保存
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(output))
    logger.info(f"✅ 可视化已保存 → {output}")

    return str(output)


def visualize_company_chain(
    graph_store,
    company_name: str,
    output_path: str = "output/company_chain.html",
    max_depth: int = 3,
):
    """可视化单个公司的关联链"""
    try:
        from pyvis.network import Network
    except ImportError:
        logger.error("请安装 pyvis: pip install pyvis")
        raise

    chain = graph_store.query_chain(company_name, max_depth=max_depth)

    net = Network(height="600px", width="100%", directed=True, bgcolor="#222222", font_color="white")
    net.barnes_hut()

    node_id_set = set()
    for node in chain["nodes"]:
        nid = node["id"]
        node_type = node.get("node_type", "unknown")
        color = NODE_COLORS.get(node_type, "#999999")
        size = NODE_SIZES.get(node_type, 15) * (2 if nid == company_name else 1)

        net.add_node(nid, label=nid, color=color, size=size, shape="dot")
        node_id_set.add(nid)

    for edge in chain["edges"]:
        if edge["source"] in node_id_set and edge["target"] in node_id_set:
            net.add_edge(edge["source"], edge["target"], title=edge.get("relation", ""))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(output))
    logger.info(f"✅ 公司关联链已保存 → {output}")

    return str(output)
