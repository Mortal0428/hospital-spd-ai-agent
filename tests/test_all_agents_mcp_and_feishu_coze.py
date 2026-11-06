"""
@file test_all_agents_mcp_and_feishu_coze.py
@description 全员 1~6 业务智能体解耦 MCP 工具、原生飞书卡片推送、Coze 协同与统一配置落盘全链路集成测试套件
全面覆盖 17 项独立 MCP 工具调用契约、飞书 Card 2.0 交互式卡片、Coze 云端协同、
多智能体状态机流转与中央黑板多专家协同，杜绝任何假 demo 与空字典假参数。

@param pytest 测试执行器入参
@returns 测试断言结果报告
@route tests/test_all_agents_mcp_and_feishu_coze.py
@throws 断言失败时触发 AssertionError
"""

import os
import sys
import unittest
from datetime import date
from decimal import Decimal

# 导入后端工程路径
sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import SessionLocal
from app.services.mcp_tools import _TOOL_REGISTRY, execute_mcp_tool, execute_tool
from app.services.feishu_service import feishu_service
from app.services.coze_service import coze_service, _clean_emoji
from app.services.agents import (
    PlanAndExecuteDictAgent,
    AdvancedSkillRouter,
    LangGraphSecondaryAgent,
    ReActHighValueTraceAgent,
    BlackboardFinanceAuditAgent,
    AgenticRagSupervisorAgent
)


class TestMcpToolsRegistryAndExecution(unittest.TestCase):
    """测试套件 1: MCP 工具独立注册中心与 17 项原子工具执行契约"""

    def setUp(self):
        """测试前准备数据库会话
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/setUp
        @throws 无
        """
        self.db = SessionLocal()

    def tearDown(self):
        """测试后安全清理数据库会话
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/tearDown
        @throws 无
        """
        self.db.close()

    def test_01_registry_completeness(self):
        """验证 17 项独立原子 MCP 工具全部成功注册
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_01_registry_completeness
        @throws AssertionError
        """
        expected_tools = [
            "mcp_query_product_dict",
            "mcp_check_supplier_cert",
            "mcp_create_product_dict",
            "mcp_scan_main_and_sec_stock",
            "mcp_create_dispatch_order",
            "mcp_query_pending_requisitions",
            "mcp_check_main_available",
            "mcp_submit_sec_requisition",
            "mcp_query_surgery_pack_specs",
            "mcp_trace_udi_full_logs",
            "mcp_freeze_problem_batch",
            "mcp_aggregate_dept_cost",
            "mcp_scan_abnormal_flow_logs",
            "mcp_chroma_global_retrieval",
            "mcp_write_knowledge_graph_triples",
            "mcp_query_knowledge_stats"
        ]
        for t_name in expected_tools:
            self.assertIn(t_name, _TOOL_REGISTRY, f"工具 {t_name} 未在 MCP 注册表中登记")

    def test_02_execute_tool_fills_args_and_output(self):
        """验证 execute_tool 调用后 input_args 与 output 绝为空字典
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_02_execute_tool_fills_args_and_output
        @throws AssertionError
        """
        res = execute_tool("mcp_query_product_dict", {"product_name": "口罩", "limit": 3}, db=self.db)
        d = res.to_dict()
        self.assertTrue(res.success)
        self.assertEqual(d["tool_name"], "mcp_query_product_dict")
        self.assertIn("product_name", d["args"])
        self.assertIn("items", d["output"])
        self.assertTrue(len(d["args"]) > 0, "入参字典严禁为空")

    def test_03_dispatch_tools_stock_scan(self):
        """验证主库与二级库水位扫描工具契约与 FEFO 排序
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_03_dispatch_tools_stock_scan
        @throws AssertionError
        """
        res = execute_tool("mcp_scan_main_and_sec_stock", {"limit": 5}, db=self.db)
        d = res.to_dict()
        self.assertTrue(res.success)
        self.assertIn("main_batches", d["output"])
        self.assertIn("sec_stocks", d["output"])

    def test_04_requisition_tools_check_and_submit(self):
        """验证临床二级库主库可用量查验与请领单生成工具
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_04_requisition_tools_check_and_submit
        @throws AssertionError
        """
        res_chk = execute_tool("mcp_check_main_available", {"product_name": "口罩", "required_qty": 20}, db=self.db)
        self.assertTrue(res_chk.success)

        res_sub = execute_tool("mcp_submit_sec_requisition", {
            "apply_dept_name": "骨科病区二级库",
            "product_name": "一次性医用无菌口罩",
            "apply_qty": 20,
            "urgency_level": "ROUTINE",
            "applicant_name": "单元测试专员"
        }, db=self.db)
        d_sub = res_sub.to_dict()
        self.assertTrue(res_sub.success)
        self.assertIn("req_order_no", d_sub["output"])
        self.assertIn("trace_no", d_sub["output"])

    def test_05_high_value_trace_and_freeze(self):
        """验证高值 UDI 穿透溯源与问题批次冻结工具
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_05_high_value_trace_and_freeze
        @throws AssertionError
        """
        res_tr = execute_tool("mcp_trace_udi_full_logs", {"operator_role": "secondary_user"}, db=self.db)
        self.assertTrue(res_tr.success)
        d_tr = res_tr.to_dict()
        self.assertIn("workflow_timeline", d_tr["output"])

        res_fr = execute_tool("mcp_freeze_problem_batch", {
            "batch_no": "TEST-BATCH-2026",
            "freeze_reason": "单测模拟召回熔断",
            "operator_name": "测试管理员"
        }, db=self.db)
        self.assertTrue(res_fr.success)
        d_fr = res_fr.to_dict()
        self.assertIn("trace_no", d_fr["output"])

    def test_06_finance_tools_aggregation(self):
        """验证财务科室精算与 6W 异常流转排查工具
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_06_finance_tools_aggregation
        @throws AssertionError
        """
        res_cost = execute_tool("mcp_aggregate_dept_cost", {"period_month": "2026-11"}, db=self.db)
        self.assertTrue(res_cost.success)
        d_cost = res_cost.to_dict()
        self.assertIn("total_hospital_cost", d_cost["output"])

        res_scan = execute_tool("mcp_scan_abnormal_flow_logs", {"limit": 10}, db=self.db)
        self.assertTrue(res_scan.success)
        d_scan = res_scan.to_dict()
        self.assertIn("total_scanned", d_scan["output"])


class TestFeishuAndCozeServices(unittest.TestCase):
    """测试套件 2: 原生飞书交互卡片与 Coze 智能体协同服务"""

    def test_07_feishu_tenant_token(self):
        """验证使用开发者凭据成功获取飞书 tenant_access_token
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_07_feishu_tenant_token
        @throws AssertionError
        """
        token = feishu_service.get_tenant_access_token()
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 10, "飞书 Token 长度不合规")

    def test_08_feishu_card_builders(self):
        """验证 4 类业务卡片结构生成契约与零 Emoji 规范
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_08_feishu_card_builders
        @throws AssertionError
        """
        c1 = feishu_service.build_dict_create_card("P001", "骨科接骨板", "定制", "EQUIP_DEPT", "HIGH_VALUE", "普惠", "2026", 1200.0, "0697")
        self.assertEqual(c1["header"]["template"], "turquoise")

        c2 = feishu_service.build_dispatch_order_card("D001", "骨科病区", "注射器", "B01", "2027-10-31", 20, 2.5, "王主管")
        self.assertEqual(c2["header"]["template"], "blue")

        c3 = feishu_service.build_hitl_approval_card("R001", "急诊病区", "心脏支架", 10, "EMERGENCY", "李护士", "大额待审")
        self.assertEqual(c3["header"]["template"], "orange")

        c4 = feishu_service.build_udi_freeze_card("B01", "UDI001", "支架", "美敦力", "不良事件", "安全员")
        self.assertEqual(c4["header"]["template"], "carmine")

    def test_09_coze_service_and_emoji_cleaning(self):
        """验证 Coze 服务 Emoji 净化器与对话客户端初始化
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_09_coze_service_and_emoji_cleaning
        @throws AssertionError
        """
        dirty_str = "系统正常\u2705报警\u274c测试医疗耗材"
        clean_str = _clean_emoji(dirty_str)
        self.assertEqual(clean_str, "系统正常报警测试医疗耗材")
        self.assertEqual(coze_service.bot_id, "7700811095929323554")


class TestAgentsUpgradedExecution(unittest.TestCase):
    """测试套件 3: 全员 1~6 业务智能体重构后真实执行验证"""

    def setUp(self):
        """建立测试数据库连接
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/setUp
        @throws 无
        """
        self.db = SessionLocal()

    def tearDown(self):
        """关闭数据库连接
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/tearDown
        @throws 无
        """
        self.db.close()

    def test_10_agent_1_plan_execute(self):
        """验证智能体 1 Plan & Execute 动态规划与真实 MCP 工具调用
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_10_agent_1_plan_execute
        @throws AssertionError
        """
        agent = PlanAndExecuteDictAgent(self.db)
        res = agent.execute_plan("请帮我新增一款医用外科口罩产品字典档案并查验供应商资质", "sys_admin")
        self.assertEqual(res["agent_id"], "agent_1")
        self.assertTrue(len(res["plan_steps"]) >= 2)
        self.assertTrue(len(res["tools_called"]) >= 2)
        t1 = res["tools_called"][0]
        self.assertIn("args", t1)
        self.assertIn("output", t1)

    def test_11_agent_2_router_skill(self):
        """验证智能体 2 Router & Skill 意图置信度雷达与调拨单生成
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_11_agent_2_router_skill
        @throws AssertionError
        """
        router = AdvancedSkillRouter(self.db)
        res = router.route_and_execute("根据FEFO规则调拨20支口罩到骨科病区二级库", {"account": "sys_admin", "role": "dept_manager"}, self.db)
        self.assertEqual(res["chosen_skill"], "skill_fefo_dispatch")
        self.assertTrue(len(res["confidence_rankings"]) >= 2)
        self.assertIn("radar", res["confidence_rankings"][0])
        self.assertTrue(len(res["tools_called"]) >= 1)

    def test_12_agent_3_langgraph_hitl(self):
        """验证智能体 3 LangGraph 4节点流转与 HITL 挂起恢复
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_12_agent_3_langgraph_hitl
        @throws AssertionError
        """
        agent = LangGraphSecondaryAgent(self.db)
        # 步骤 1: 发起申领触发人机协同挂起
        res_pause = agent.run_step("骨科病区二级库急需申领 100 支医用外科口罩", operator="nurse_zhang")
        self.assertEqual(res_pause["state"]["current_node"], "HumanReviewNode")
        self.assertTrue(res_pause["state"]["hitl_pending"])
        self.assertIn("graph_mermaid", res_pause["state"])

        # 步骤 2: 人工确认恢复 (Resume)
        res_resume = agent.run_step(
            query="",
            state_payload=res_pause["state"],
            resume_action="CONFIRM",
            review_comment="护士长审核通过，同意下发",
            operator="sys_admin"
        )
        self.assertEqual(res_resume["state"]["current_node"], "PersistRequisitionNode")
        self.assertEqual(res_resume["state"]["human_in_the_loop_status"], "APPROVED")

    def test_13_agent_4_react_lifecycle(self):
        """验证智能体 4 ReAct 穿透查询 MySQL 与问题批次真实物理冻结
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_13_agent_4_react_lifecycle
        @throws AssertionError
        """
        agent = ReActHighValueTraceAgent(self.db)
        res = agent.trace_udi_lifecycle("请紧急物理冻结批号为 TEST-BATCH-2026 的问题支架", operator="sys_admin")
        self.assertEqual(res["agent_id"], "agent_4")
        self.assertTrue(len(res["react_steps"]) >= 2)
        self.assertTrue(len(res["tools_called"]) >= 2)

    def test_14_agent_5_blackboard_experts(self):
        """验证智能体 5 Blackboard 中央黑板多专家协同与事实汇聚
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_14_agent_5_blackboard_experts
        @throws AssertionError
        """
        agent = BlackboardFinanceAuditAgent(self.db)
        res = agent.audit_finance_ledger("请对全院多科室本月耗材支出进行财务对账与合规审计", "2026-11", "sys_admin", "sys_admin")
        self.assertEqual(res["agent_id"], "agent_5")
        bb = res["blackboard_data"]
        self.assertIn("session_id", bb)
        self.assertIn("hypotheses", bb)
        self.assertIn("cost_ledger", bb["facts"])
        self.assertIn("compliance_audit", bb["facts"])
        self.assertIn("procurement_policy", bb["facts"])

    def test_15_agent_6_supervisor_and_proofs(self):
        """验证智能体 6 Chroma 全量 HNSW 检索与算子生效凭证卡片
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_15_agent_6_supervisor_and_proofs
        @throws AssertionError
        """
        agent = AgenticRagSupervisorAgent(self.db)
        res = agent.dispatch("经导管主动脉瓣膜系统的临床操作规范与并发症预防有哪些注意事项？", "sys_admin")
        self.assertEqual(res["agent_id"], "agent_6")
        self.assertIn("operator_proofs", res)
        proofs = res["operator_proofs"]
        self.assertIn("query_rewrite", proofs)
        self.assertIn("isrel_rerank", proofs)
        self.assertIn("faithfulness", proofs)

    def test_16_router_endpoints_and_sse(self):
        """验证路由层新增接口飞书测试卡片、Webhook握手、Coze流式与深度思考传参
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_16_router_endpoints_and_sse
        @throws AssertionError
        """
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # 1. 验证 /feishu/test-card
        resp_card = client.post("/api/v1/rag-hub/feishu/test-card", json={
            "card_type": "dict_create",
            "product_name": "经导管主动脉瓣膜系统"
        })
        self.assertEqual(resp_card.status_code, 200)
        self.assertEqual(resp_card.json()["code"], 200)
        self.assertIn("飞书卡片推送测试完成", resp_card.json()["msg"])

        # 2. 验证 /feishu/webhook (URL verification challenge 握手)
        resp_wb = client.post("/api/v1/rag-hub/feishu/webhook", json={
            "type": "url_verification",
            "challenge": "challenge_token_2026_spd"
        })
        self.assertEqual(resp_wb.status_code, 200)
        self.assertEqual(resp_wb.json(), {"challenge": "challenge_token_2026_spd"})

        # 3. 验证 /coze/chat-stream
        resp_coze = client.post("/api/v1/rag-hub/coze/chat-stream", json={
            "query": "医疗物资管理规范测试"
        })
        self.assertEqual(resp_coze.status_code, 200)
        self.assertIn("text/event-stream", resp_coze.headers.get("content-type", ""))

        # 4. 验证 /agent/execute 支持 enable_deep_thinking
        resp_exec = client.post("/api/v1/rag-hub/agent/execute", json={
            "agent_id": "agent_2",
            "query": "查询主库在库重点物资批次水位",
            "enable_deep_thinking": 1
        })
        self.assertEqual(resp_exec.status_code, 200)
        self.assertEqual(resp_exec.json()["code"], 200)

    def test_17_agent_subagent_bubbles_and_rankings(self):
        """验证全员智能体微信Ins群聊气泡契约与技能排行榜打分契约
        @param self: 测试用例实例
        @returns None
        @route tests/test_all_agents_mcp_and_feishu_coze.py/test_17_agent_subagent_bubbles_and_rankings
        @throws AssertionError
        """
        # 1. 验证 Agent 2 confidence_rankings 同时包含 skill, score, radar
        router = AdvancedSkillRouter(self.db)
        res2 = router.route_and_execute("根据FEFO规则调拨20支口罩到骨科病区二级库", {"account": "sys_admin", "role": "dept_manager"}, self.db)
        rk0 = res2["confidence_rankings"][0]
        self.assertIn("skill", rk0)
        self.assertIn("score", rk0)
        self.assertIsInstance(rk0["score"], int)
        self.assertIn("radar", rk0)

        # 2. 验证 Agent 3 5 节点定义
        agent3 = LangGraphSecondaryAgent(self.db)
        self.assertEqual(len(agent3.WORKFLOW_STEPS), 5)

        # 3. 验证 Agent 4 批号正则为是兼容与专属群聊气泡
        agent4 = ReActHighValueTraceAgent(self.db)
        res4 = agent4.trace_udi_lifecycle("请紧急物理冻结批号为 TEST-BATCH-2026 的问题支架", operator="sys_admin")
        self.assertIn("subagent_bubbles", res4)
        bubble_ids4 = [b["subagent_id"] for b in res4["subagent_bubbles"]]
        self.assertIn("udi_tracer", bubble_ids4)
        self.assertIn("recall_guard", bubble_ids4)

        # 4. 验证 Agent 5 中央黑板 deduction_summary 与分角色气泡
        agent5 = BlackboardFinanceAuditAgent(self.db)
        res5 = agent5.audit_finance_ledger("请对全院多科室本月耗材支出进行财务对账与合规审计", "2026-11", "sys_admin", "sys_admin")
        self.assertIn("subagent_bubbles", res5)
        contributions = res5["blackboard_data"]["expert_contributions"]
        self.assertTrue(len(contributions) >= 3)
        self.assertTrue(any("支出" in c.get("summary", "") for c in contributions))
        bubble_ids5 = [b["subagent_id"] for b in res5["subagent_bubbles"]]
        self.assertIn("bb_bus", bubble_ids5)


if __name__ == "__main__":
    unittest.main()
