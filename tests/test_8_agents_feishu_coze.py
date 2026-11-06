"""
@file test_8_agents_feishu_coze.py
@description 全量 8 大业务智能体、飞书双轨通信与 Coze 协同问答自动化回归验证测试
覆盖智能体 7 (飞书协同推送) 与智能体 8 (Coze 开放生态) 的架构落盘、MCP 工具调用与气泡流式契约，全程零 Emoji。

@param pytest 会话与 FastAPI 测试客户端
@returns 断言测试全部通过
@route internal://tests/test_8_agents_feishu_coze.py
@throws 断言失败时抛出 AssertionError
"""

import sys
from pathlib import Path
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.core.database import SessionLocal
from app.services.agents import FeishuSyncAgent, CozeCloudAgent
from app.services.feishu_service import feishu_service
from app.services.coze_service import coze_service, _clean_emoji
from app.services.mcp_tools import list_mcp_tools, execute_mcp_tool
from app.routers.rag_agent_hub_router import get_agent_models

client = TestClient(app)


def test_01_mcp_tools_registration():
    """验证 8 大智能体所需的所有 MCP 工具完备注册
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_01_mcp_tools_registration
    @throws AssertionError
    """
    tools = list_mcp_tools()
    tool_names = [t["name"] for t in tools]
    assert "mcp_feishu_push_card" in tool_names, "mcp_feishu_push_card 未注册"
    assert "mcp_feishu_check_status" in tool_names, "mcp_feishu_check_status 未注册"
    assert "mcp_scan_main_and_sec_stock" in tool_names
    assert "mcp_trace_udi_full_logs" in tool_names
    assert len(tool_names) >= 19, f"期望至少 19 个 MCP 工具，实际只有 {len(tool_names)}"


def test_02_feishu_service_connectivity():
    """验证飞书开放平台 Token 获取与连通性自检
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_02_feishu_service_connectivity
    @throws AssertionError
    """
    res = feishu_service.test_connection()
    assert res.get("connected") is True, f"飞书鉴权未通过: {res}"
    assert "t-" in res.get("token_prefix", "")


def test_03_feishu_agent_dispatch_and_bubbles():
    """验证智能体 7 (FeishuSyncAgent) 真实派发与 3 个子智能体工作流气泡
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_03_feishu_agent_dispatch_and_bubbles
    @throws AssertionError
    """
    db = SessionLocal()
    try:
        agent7 = FeishuSyncAgent(db)
        res = agent7.dispatch("向骨科病区飞书协同群推送最新物资调拨单据卡片", operator="sys_admin")
        assert res["agent_id"] == "agent_7"
        assert len(res["subagent_bubbles"]) == 3, f"期望 3 个子智能体气泡，实际 {len(res['subagent_bubbles'])}"
        bubble_ids = [b["subagent_id"] for b in res["subagent_bubbles"]]
        assert "subagent_7a" in bubble_ids
        assert "subagent_7b" in bubble_ids
        assert "subagent_7c" in bubble_ids
        assert len(res["tools_called"]) >= 1
    finally:
        db.close()


def test_04_coze_emoji_cleaner():
    """验证全域零 Emoji 正则清洗器有效性
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_04_coze_emoji_cleaner
    @throws AssertionError
    """
    dirty = "你好😊！这是测试医疗物资📦，UDI编码为#1234🚀。"
    clean = _clean_emoji(dirty)
    assert "😊" not in clean
    assert "📦" not in clean
    assert "🚀" not in clean
    assert "你好" in clean and "医疗物资" in clean


def test_05_coze_agent_dispatch_and_bubbles():
    """验证智能体 8 (CozeCloudAgent) 真实派发与 3 个子智能体工作流气泡
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_05_coze_agent_dispatch_and_bubbles
    @throws AssertionError
    """
    db = SessionLocal()
    try:
        agent8 = CozeCloudAgent(db)
        res = agent8.dispatch("测试智能体8连通性与法规答疑", operator="sys_admin")
        assert res["agent_id"] == "agent_8"
        assert len(res["subagent_bubbles"]) == 3
        bubble_ids = [b["subagent_id"] for b in res["subagent_bubbles"]]
        assert "subagent_8a" in bubble_ids
        assert "subagent_8b" in bubble_ids
        assert "subagent_8c" in bubble_ids
        assert len(res["final_answer"]) > 0
    finally:
        db.close()


def test_06_router_get_8_agent_models():
    """验证接口 GET /api/v1/rag-hub/agent-models 完整返回全部 8 大智能体
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_06_router_get_8_agent_models
    @throws AssertionError
    """
    resp = client.get("/api/v1/rag-hub/agent-models")
    assert resp.status_code == 200
    data = resp.json()["data"]
    aids = [item["agent_id"] for item in data]
    assert len(aids) == 8, f"期望返回 8 大智能体，实际返回 {len(aids)}"
    for i in range(1, 9):
        assert f"agent_{i}" in aids, f"缺少 agent_{i}"


def test_07_router_execute_agent_7():
    """验证接口 POST /api/v1/rag-hub/agent/execute 执行智能体 7
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_07_router_execute_agent_7
    @throws AssertionError
    """
    payload = {
        "agent_id": "agent_7",
        "query": "请向骨科病区推送高值耗材紧急召回冻结通知卡片",
        "user_role": "sys_admin"
    }
    resp = client.post("/api/v1/rag-hub/agent/execute", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["agent_id"] == "agent_7"
    assert len(data["subagent_bubbles"]) == 3


def test_08_router_feishu_send_test():
    """验证接口 POST /api/v1/rag-hub/feishu/send-test 双向兼容与参数透传
    @param 无
    @returns None
    @route internal://tests/test_8_agents_feishu_coze.py/test_08_router_feishu_send_test
    @throws AssertionError
    """
    payload = {
        "card_type": "dispatch_order",
        "product_name": "经导管主动脉瓣膜系统",
        "receive_id": "ou_test_user_001"
    }
    resp = client.post("/api/v1/rag-hub/feishu/send-test", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert "data" in body
