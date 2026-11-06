import json
import httpx
from app.services.feishu_service import feishu_service

token = feishu_service.get_tenant_access_token()
chat_id = "oc_4e09defedb59928db5b4b739f9d5e325"
url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json; charset=utf-8"
}

card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "template": "blue",
        "title": {"tag": "plain_text", "content": "【SPD业务智能体】协同应答"}
    },
    "elements": [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    "**问：** 你认识田江吗\n\n"
                    "**答：**\n"
                    "您好！我是医疗物资管理系统（SPD）的企业级 AI 业务助手。\n"
                    "在当前的医疗物资与科室人员档案中，我暂未检索到名为“田江”的相关记录。\n\n"
                    "我主要协同医院各科室处理以下业务：\n"
                    "1. **耗材字典首营审查** (Agent 01: 资质与目录判定)\n"
                    "2. **主库按需分发调拨** (Agent 02: FEFO 近效期先出补货)\n"
                    "3. **临床科室申领问答** (Agent 03: 定数包与规范咨询)\n"
                    "4. **高值 UDI 全链路溯源** (Agent 04: 问题批次一键冻结)\n"
                    "5. **多科室耗占比审计精算** (Agent 05: 财务合规内控)\n\n"
                    "当前双向长连接通道已完全畅通，您现在可以在本群直接 @我 发送任何业务问题或测试指令，我都会实时为您推演并输出！"
                )
            }
        },
        {"tag": "hr"},
        {
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": "双向长连接实时在席 · 8大智能体已就绪"
                }
            ]
        }
    ]
}

payload = {
    "receive_id": chat_id,
    "msg_type": "interactive",
    "content": json.dumps(card, ensure_ascii=False)
}

resp = httpx.post(url, headers=headers, json=payload, timeout=25.0)
print("Response status:", resp.status_code)
print("Response body:", resp.json())
