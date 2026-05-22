import requests, json

app_id = "cli_a911024fabb85bce"
app_secret = "ozzfZ3cFj7X5CyOXvIn5XcVsmhMOU6yM"
receive_id = "ou_7e8c1b7bbc074e829ee77ae062b865b7"
receive_id_type = "open_id"

def get_access_token():
    resp = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", json={
        "app_id": app_id,
        "app_secret": app_secret
    })
    return resp.json().get("tenant_access_token")

def send_post(access_token, content_list, title=""):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "receive_id": receive_id,
        "receive_id_type": receive_id_type,
        "msg_type": "post",
        "content": json.dumps({"zh_cn": {"title": title, "content": content_list}}),
    }
    resp = requests.post("https://open.feishu.cn/open-apis/im/v1/messages", headers=headers, json=body)
    return resp.json()

token = get_access_token()

content = [
    [{"tag": "text", "text": f"📊 知识图谱进度汇报\n汇报时间: 2026-05-11 02:20\n\n"}],
    [{"tag": "text", "text": "✅ 已完成:\n"}],
    [{"tag": "text", "text": "• Wind 数据导入完成: 5199公司, 157行业, 52931产品\n"}],
    [{"tag": "text", "text": "• 图谱构建完成: 58071节点, 73328边\n"}],
    [{"tag": "text", "text": "• 交互式HTML可视化: kg_full_graph.html (3000节点采样)\n"}],
    [{"tag": "text", "text": "• 8个行业子图谱已生成: 电子/医药/电力设备/计算机/银行/食品/汽车/化工\n"}],
    [{"tag": "text", "text": "• 7家公司关联链已生成: 宁德时代/茅台/药明康德/工行/比亚迪/恒瑞/中芯国际\n"}],
    [{"tag": "text", "text": "• 项目报告/README/任务文档均已完成\n\n"}],
    [{"tag": "text", "text": "🔄 进行中:\n"}],
    [{"tag": "text", "text": "• Tushare 数据接入受阻: Token无效, 转接API超时\n"}],
    [{"tag": "text", "text": "• 产品→产品关系: 0条 (需数据源补充)\n\n"}],
    [{"tag": "text", "text": "⏳ 待完成:\n"}],
    [{"tag": "text", "text": "• Tushare Token需若若姐提供正确的\n"}],
    [{"tag": "text", "text": "• Neo4j 图数据库对接\n\n"}],
    [{"tag": "text", "text": "📊 数据量:\n"}],
    [{"tag": "text", "text": "• 数据文件: 7个, ~14.7MB\n"}],
    [{"tag": "text", "text": "• 输出文件: 22个 (含JSON/HTML/PNG)\n"}],
    [{"tag": "text", "text": "• 知识图谱: 18MB (58071节点, 73328边)"}],
]

result = send_post(token, content, title="📊 知识图谱进度汇报")
print(json.dumps(result, indent=2, ensure_ascii=False))
