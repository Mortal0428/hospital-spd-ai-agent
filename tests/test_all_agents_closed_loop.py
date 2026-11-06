"""
@file test_all_agents_closed_loop.py
@description 1~5号业务智能体全链路闭环与6号智能体全库巡检重切压力验证脚本
@param 无
@returns None
@route tests/test_all_agents_closed_loop.py
@throws 断言失败异常
"""

import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1/rag-hub"

def post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=== 开始执行 1~6 号业务智能体全链路闭环与人机回环验证 ===")

# 1. 验证 Agent 1: 动态品规归类与落盘
print("\n[测试 1: 智能体 1 (Plan & Execute 动态建仓与查验)]")
res1 = post("/agent/execute", {
    "agent_id": "agent_1",
    "query": "帮我新增一款高值耗材【微创经皮穿刺套针】，规格 16G，单价 420 元",
    "user_role": "dept_manager"
})
print("Agent 1 状态码:", res1.get("code"))
print("Agent 1 产出摘要:", res1["data"]["final_summary"][:120], "...")
assert res1["code"] == 200, "Agent 1 调用失败"

# 2. 验证 Agent 2: FEFO 调拨单落盘
print("\n[测试 2: 智能体 2 (Router + Skill FEFO 物理调拨单落盘)]")
res2 = post("/agent/execute", {
    "agent_id": "agent_2",
    "query": "执行 FEFO 近效期分发调拨，向骨科二级库补充低水位耗材",
    "user_role": "dept_manager"
})
print("Agent 2 选定技能:", res2["data"]["chosen_skill"])
print("Agent 2 物理落盘依据包含 DISPATCHED:", "DISPATCHED" in res2["data"]["final_answer"] or "DIST-" in res2["data"]["final_answer"])
assert "DIST-" in res2["data"]["final_answer"], "Agent 2 未能在物理数据库落盘调拨单"

# 3. 验证 Agent 3: LangGraph 状态图与 HITL 中断 + 恢复审批落盘
print("\n[测试 3.1: 智能体 3 (LangGraph 意图提取与人机回环中断挂起)]")
res3_step1 = post("/agent/execute", {
    "agent_id": "agent_3",
    "query": "向耗材主库申领 50 包一次性医用无菌口罩",
    "user_role": "secondary_user"
})
hitl_status = res3_step1["data"]["state"]["human_in_the_loop_status"]
print("Agent 3 中断状态:", hitl_status)
print("Agent 3 当前节点:", res3_step1["data"]["state"]["current_node"])
assert hitl_status == "PENDING_CONFIRMATION", f"Agent 3 未能触发人机回环挂起: {hitl_status}"

print("\n[测试 3.2: 智能体 3 (护士长人工审批 CONFIRM + 批示意见恢复落盘)]")
res3_step2 = post("/agent/execute", {
    "agent_id": "agent_3",
    "query": "确认提交申领单",
    "resume_action": "CONFIRM",
    "state_payload": res3_step1["data"]["state"],
    "review_comment": "科室夜班储备不足，准予紧急下发申领"
})
final_ans_3 = res3_step2["data"]["final_answer"]
print("Agent 3 审批恢复状态:", res3_step2["data"]["state"]["human_in_the_loop_status"])
print("Agent 3 物理请领单号:", res3_step2["data"]["state"].get("requisition_order_no"))
print("Agent 3 审批意见回显:", "准予紧急下发申领" in final_ans_3)
assert res3_step2["data"]["state"]["human_in_the_loop_status"] == "APPROVED", "Agent 3 审批恢复未通过"
assert "REQ-" in final_ans_3, "Agent 3 审批通过后未物理落盘请领单"

# 4. 验证 Agent 4: ReAct 溯源与真实物理批次冻结
print("\n[测试 4: 智能体 4 (ReAct 溯源与紧急质量召回物理冻结)]")
res4 = post("/agent/execute", {
    "agent_id": "agent_4",
    "query": "追溯高值耗材 UDI-202611-0012 并在发生严重不良事件时紧急冻结该批次",
    "user_role": "sys_admin"
})
print("Agent 4 调用工具:", res4["data"]["tools_called"])
print("Agent 4 包含物理冻结凭据:", "FROZEN" in res4["data"]["final_answer"])
assert "mcp_freeze_problem_batch" in res4["data"]["tools_called"], "Agent 4 未调用物理冻结工具"

# 5. 验证 Agent 5: Blackboard 动态 SQL 财务精算
print("\n[测试 5: 智能体 5 (Blackboard 动态 SQL 财务精算与角色权限)]")
res5 = post("/agent/execute", {
    "agent_id": "agent_5",
    "query": "对 2026-11 周期全院科室耗材调拨与高值核销进行财务精算审计",
    "user_role": "finance_auditor"
})
bb_data = res5["data"]["blackboard_data"]
print("Agent 5 黑板统计事实:", bb_data.get("realtime_stats"))
print("Agent 5 专家建议数量:", len(bb_data.get("experts", [])))
assert "realtime_stats" in bb_data, "Agent 5 黑板未包含动态 SQL 事实"

# 6. 验证 Agent 6: 知识库切片健康度巡检与自动重新切片
print("\n[测试 6.1: 智能体 6 (全库切片健康度巡检 API)]")
inspect_res = get("/maintenance/inspect")
print("全库巡检状态:", inspect_res["code"], inspect_res["data"]["status"])
print("文档总数:", inspect_res["data"]["total_documents"], "健康度:", inspect_res["data"]["health_score"])

print("\n[测试 6.2: 智能体 6 (自然语言触发巡检与自省重切报告)]")
res6 = post("/agent/execute", {
    "agent_id": "agent_6",
    "query": "全库未切片健康巡检与自动重新切片",
    "user_role": "sys_admin"
})
print("Agent 6 巡检输出前 150 字:\n", res6["data"]["final_answer"][:150], "...")
assert "知识库切片健康度全库巡检报告" in res6["data"]["final_answer"], "Agent 6 未能生成规范巡检报告"

print("\n=== 所有 1~6 号智能体后端全链路闭环与物理落盘验证 100% 成功通过！ ===")
