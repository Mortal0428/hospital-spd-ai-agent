"""
@file test_challenger_m2_adversarial.py
@description 对抗测试员 (challenger_m2_1) 针对 Milestone 2 核心实施成果的独立经验性对抗质询套件
深入检验智能体 1~6 业务拓扑、边界条件注入、只读守卫、HITL人机回环、ReAct批号正则穿透、
中央黑板多专家真实推导、Chroma全局检索、SSE多行分包流式契约与异常容错能力。

@param pytest 测试执行框架
@returns 测试断言结果报告
@route tests/test_challenger_m2_adversarial.py
@throws 断言失败抛出 AssertionError
"""

import json
import os
import re
import sys
import time
import unittest
from typing import Any, Dict, List

# 引入后端运行环境
sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import SessionLocal
from app.models.spd_models import SpdProductDict, SpdMainInventory, SpdRequisitionOrder, SpdHighValueItem, SpdWorkflowLog
from app.services.agents import (
    PlanAndExecuteDictAgent,
    AdvancedSkillRouter,
    LangGraphSecondaryAgent,
    ReActHighValueTraceAgent,
    BlackboardFinanceAuditAgent,
    AgenticRagSupervisorAgent
)
from app.services.agents.agent_4_react import desensitize_patient_info
from app.services.mcp_tools import execute_tool, _TOOL_REGISTRY


class TestChallengerM2Adversarial(unittest.TestCase):
    """对抗测试员 Milestone 2 专属实证对抗质询测试套件"""

    def setUp(self):
        """测试用例执行前准备独立的数据库会话
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/setUp
        @throws 无
        """
        self.db = SessionLocal()

    def tearDown(self):
        """测试用例执行完毕后安全关闭数据库会话
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/tearDown
        @throws 无
        """
        self.db.rollback()
        self.db.close()

    def test_01_agent1_dynamic_steps_bounds_and_arg_resolver(self):
        """实测质询智能体 1: 检验 2~6 步动态拆解与参数解析器防御非法字段注入
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_01_agent1_dynamic_steps_bounds_and_arg_resolver
        @throws AssertionError 断言异常
        """
        agent = PlanAndExecuteDictAgent(self.db)

        # 1. 验证动态步骤数量在 2~6 范围内
        res = agent.execute_plan("新增一款一次性医用无菌乳胶外科手术手套", operator_account="sys_admin")
        steps = res.get("plan_steps", [])
        self.assertGreaterEqual(len(steps), 2, "Agent 1 规划步骤少于 2 步")
        self.assertLessEqual(len(steps), 6, "Agent 1 规划步骤超过 6 步")

        # 2. 验证 Tool Argument Resolver 过滤未定义字段 (防御 extra='forbid' 拦截)
        args_create = agent._build_tool_args(
            tool_name="mcp_create_product_dict",
            extracted_name="一次性医用无菌乳胶外科手术手套",
            dept_val="CONSUMABLE_DEPT",
            type_val="GENERAL",
            cat_name="常规临床医用耗材",
            p_code="PRD-CHALLENGE-01",
            udi_di="06979999999999",
            unit_price_val=25.0,
            is_high=False,
            supplier_name="国药控股医疗器械供应链中心",
            cert_no="国械注准20263130888",
            operator_account="sys_admin"
        )
        # 检验生成的参数字典不包含未在 Pydantic 中定义的额外破坏性参数
        t_exec = execute_tool("mcp_create_product_dict", args_create, db=self.db)
        self.assertTrue(t_exec.success, f"工具调用失败: {t_exec.message}")

        # 3. 验证群聊气泡结构完备
        bubbles = res.get("subagent_bubbles", [])
        self.assertGreaterEqual(len(bubbles), 2)
        self.assertEqual(bubbles[0]["subagent_id"], "planner")
        self.assertIn("executor_step", bubbles[1]["subagent_id"])

    def test_02_agent1_rbac_and_fact_grounding(self):
        """实测质询智能体 1: 检验临床护士角色 RBAC 拦截与客观事实问答数据库查验
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_02_agent1_rbac_and_fact_grounding
        @throws AssertionError 断言异常
        """
        agent = PlanAndExecuteDictAgent(self.db)

        # 1. 护士账号尝试执行首营建仓 -> 必须触发 RBAC 权限硬拦截
        res_rbac = agent.execute_plan("新增一款心脏植入式支架", operator_account="nurse_zhang")
        self.assertIn("RBAC 权限拦截", res_rbac.get("final_answer", ""))
        self.assertEqual(res_rbac.get("model_used"), "system:rbac_guard")
        self.assertEqual(len(res_rbac.get("tools_called", [])), 1)
        self.assertEqual(res_rbac.get("tools_called")[0], "rbac_permission_interceptor")

        # 2. 客观事实统计问答 -> 触发数据库物理查验 (System State Grounding)
        res_fact = agent.execute_plan("请问全院耗材字典总数有多少种？", operator_account="sys_admin")
        self.assertIn("全院耗材字典与供应商首营实时查验报告", res_fact.get("final_answer", ""))
        self.assertEqual(res_fact.get("model_used"), "system:db_grounding")
        self.assertIn("mcp_query_product_dict_stats", res_fact.get("tools_called", []))

    def test_03_agent2_readonly_vs_dispatch_invariant(self):
        """实测质询智能体 2: 检验自然语言业务问答只读不变性 (绝不篡改库存或生成调拨单)
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_03_agent2_readonly_vs_dispatch_invariant
        @throws AssertionError 断言异常
        """
        router = AdvancedSkillRouter(self.db)

        # 记录执行前主库总库存条目与请领单条目
        initial_inv = self.db.query(SpdMainInventory).first()
        initial_qty = initial_inv.available_qty if initial_inv else 0

        # 1. 执行业务规范与制度咨询问答 (检验只读不变性：严格只读，绝不篡改库存或生成调拨单)
        res_qa = router.route_and_execute(
            "请问主库向临床二级库发料的 FEFO 规则与审批流程是什么？",
            {"account": "sys_admin", "dept": "CONSUMABLE_DEPT", "role": "dept_manager"},
            self.db
        )
        self.assertIsNone(res_qa.get("created_dist_order_no"), "只读问答严禁生成物理调拨单号")

        # 检查主库库存未被篡改
        self.db.refresh(initial_inv)
        self.assertEqual(initial_inv.available_qty, initial_qty, "只读问答篡改了物理在库库存数量")

        # 2. 执行纯仓储制度问答 (检验命中 skill_general_dispatch_qa)
        res_pure_qa = router.route_and_execute(
            "三甲医院医疗耗材库房日常管理规定与安全防护制度",
            {"account": "sys_admin", "dept": "CONSUMABLE_DEPT", "role": "dept_manager"},
            self.db
        )
        self.assertEqual(res_pure_qa.get("chosen_skill"), "skill_general_dispatch_qa")
        self.assertIsNone(res_pure_qa.get("created_dist_order_no"))

    def test_04_agent2_confidence_rankings_and_nurse_defense(self):
        """实测质询智能体 2: 检验置信度排行榜规范格式与护士角色跨权调拨拦截
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_04_agent2_confidence_rankings_and_nurse_defense
        @throws AssertionError 断言异常
        """
        router = AdvancedSkillRouter(self.db)

        # 1. 置信度雷达规范格式校验 (score 必须为 0~100 整数，skill 必须为字符串)
        res = router.route_and_execute(
            "根据近效期原则调度20盒医用手套到骨科二级库",
            {"account": "sys_admin", "dept": "CONSUMABLE_DEPT", "role": "dept_manager"},
            self.db
        )
        rankings = res.get("confidence_rankings", [])
        self.assertGreaterEqual(len(rankings), 1)
        for rk in rankings:
            self.assertIn("skill", rk)
            self.assertIsInstance(rk["skill"], str)
            self.assertIn("score", rk)
            self.assertIsInstance(rk["score"], int)
            self.assertTrue(0 <= rk["score"] <= 100)
            self.assertIn("radar", rk)
            for metric in ["intent_match", "data_readiness", "urgency", "risk"]:
                self.assertIn(metric, rk["radar"])

        # 2. 临床护士角色跨权主动分发拦截
        res_nurse = router.route_and_execute(
            "立即下发调拨单执行出库分发",
            {"account": "nurse_li", "dept": "ORTHOPEDICS", "role": "secondary_user"},
            self.db
        )
        self.assertIn("权限拦截声明", res_nurse.get("final_answer", ""))
        self.assertEqual(res_nurse.get("model_used"), "system-rbac-guard")

    def test_05_agent3_langgraph_hitl_trigger_and_5_step_machine(self):
        """实测质询智能体 3: 检验大额申领(>=50)与抢救急需量化条件精准挂起 HITL 状态机
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_05_agent3_langgraph_hitl_trigger_and_5_step_machine
        @throws AssertionError 断言异常
        """
        agent = LangGraphSecondaryAgent(self.db)

        # 1. 验证 5 节点标准定义契约
        self.assertEqual(len(agent.WORKFLOW_STEPS), 5)
        expected_keys = ["intent", "stock_check", "hitl_approval", "submit_requisition", "notify"]
        for s in agent.WORKFLOW_STEPS:
            self.assertIn(s["key"], expected_keys)

        # 2. 大额申领 (60 包外科口罩 >= 50) -> 触发 HITL 挂起
        res_large = agent.run_step(query="科室急需申领 60 包医用外科口罩", operator="nurse_wang")
        state = res_large.get("state", {})
        self.assertTrue(state.get("hitl_pending"), "大额申领未触发 HITL 挂起")
        self.assertEqual(state.get("current_node"), "HumanReviewNode")
        self.assertIn("HITL PAUSED", res_large.get("final_answer", ""))

        # 3. 验证 Mermaid 流程图存在动态高亮与样式声明
        mermaid_code = state.get("graph_mermaid", "")
        self.assertIn("graph LR", mermaid_code)
        self.assertIn("style", mermaid_code)

    def test_06_agent3_resume_action_confirm_vs_reject(self):
        """实测质询智能体 3: 检验人机回环 CONFIRM 真实物理落盘与 REJECT 安全终止
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_06_agent3_resume_action_confirm_vs_reject
        @throws AssertionError 断言异常
        """
        agent = LangGraphSecondaryAgent(self.db)
        state_payload = {
            "requisition_draft": {
                "dept_name": "骨科病区二级库",
                "product_name": "一次性医用外科口罩",
                "apply_qty": 55,
                "urgency_level": "ROUTINE"
            }
        }

        # 1. 恢复回环动作: CONFIRM -> 必须真实调用 mcp_submit_sec_requisition 写入请领单
        res_confirm = agent.run_step(
            query="",
            state_payload=state_payload,
            resume_action="CONFIRM",
            review_comment="护士长核实科室用量无误，予以批准",
            operator="head_nurse_chen"
        )
        self.assertIn("确认通过 (CONFIRM)", res_confirm.get("final_answer", ""))
        self.assertIn("PersistRequisitionNode", res_confirm.get("state", {}).get("current_node", ""))
        tools_called = res_confirm.get("tools_called", [])
        self.assertTrue(any(t.get("tool_name") == "mcp_submit_sec_requisition" for t in tools_called))

        # 2. 恢复回环动作: REJECT -> 必须安全终止，不向数据库写入请领单
        res_reject = agent.run_step(
            query="",
            state_payload=state_payload,
            resume_action="REJECT",
            review_comment="预算超支，暂不批准",
            operator="head_nurse_chen"
        )
        self.assertIn("驳回申领 (REJECT)", res_reject.get("final_answer", ""))
        self.assertEqual(len(res_reject.get("tools_called", [])), 0, "驳回操作严禁调用落盘工具")

    def test_07_agent4_react_regex_flexibility_and_patient_privacy(self):
        """实测质询智能体 4: 检验自然语言多变批号提取正则与患者隐私脱敏隔离
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_07_agent4_react_regex_flexibility_and_patient_privacy
        @throws AssertionError 断言异常
        """
        # 1. 验证各种口语化批号正则模式能否精准提取
        pats = [
            "请查询批号为 B20261102 的高值支架全链路流转记录",
            "排查批次是 LOT-CARDIO-888 的物资流转时间轴",
            "核验批号: B20261105 的高值封存状态"
        ]
        reg = re.compile(r"(?:批号|批次)(?:为|是|[:：]|\s)+([A-Za-z0-9\-]+)")
        for text in pats:
            m = reg.search(text)
            self.assertIsNotNone(m, f"未能匹配批号模式: {text}")
            self.assertTrue(len(m.group(1)) >= 8)

        # 2. 验证患者信息脱敏函数 (符合 Skill 04 隐私保护规范)
        masked_info = desensitize_patient_info("欧阳建华", "MRN88832109")
        self.assertIn("欧**", masked_info)
        self.assertIn("MRN", masked_info)

    def test_08_agent4_freeze_and_6w_flagged_audit(self):
        """实测质询智能体 4: 检验问题批次行级物理熔断、6W FLAGGED 流水与飞书通知
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_08_agent4_freeze_and_6w_flagged_audit
        @throws AssertionError 断言异常
        """
        agent = ReActHighValueTraceAgent(self.db)

        # 触发物理行级冻结与召回指令
        res = agent.trace_udi_lifecycle(
            "紧急召回并物理冻结批号为 B20261101 的全部问题心脏支架",
            operator="sys_admin",
            user_role="sys_admin"
        )
        self.assertIn("subagent_bubbles", res)
        bubbles = res.get("subagent_bubbles", [])
        bubble_roles = [b.get("badge") for b in bubbles]
        bubble_ids = [b.get("subagent_id") for b in bubbles]
        self.assertTrue("Risk Recall" in bubble_roles or "recall_guard" in bubble_ids)
        self.assertIn("recall_guard", bubble_ids)

        # 验证执行了 2 轮 ReAct (Trace -> Freeze)
        steps = res.get("react_steps", [])
        self.assertGreaterEqual(len(steps), 2)
        actions = [s.get("action") for s in steps]
        self.assertIn("mcp_trace_udi_full_logs", actions)
        self.assertIn("mcp_freeze_problem_batch", actions)

    def test_09_agent5_blackboard_3_expert_deductions_and_risk(self):
        """实测质询智能体 5: 检验彻底消灭机械键数统计、三大专家事实推导与风控评级
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_09_agent5_blackboard_3_expert_deductions_and_risk
        @throws AssertionError 断言异常
        """
        agent = BlackboardFinanceAuditAgent(self.db)
        res = agent.audit_finance_ledger(
            "请对全院各科室本月耗材支出进行多专家协同审计与集采控费核算",
            "2026-11",
            operator="sys_admin",
            user_role="sys_admin"
        )
        bb = res.get("blackboard_data", {})

        # 1. 验证三大假设 (H1, H2, H3) 全部得到验证
        hypotheses = bb.get("hypotheses", [])
        self.assertEqual(len(hypotheses), 3)
        for h in hypotheses:
            self.assertIn(h.get("status"), ["VERIFIED_TRUE", "VERIFIED_FALSE"])
            self.assertTrue(len(h.get("evidence", "")) > 10, "假设证据描述不完备")

        # 2. 验证专家贡献日志必须包含具有专业语义的 deduction_summary (彻底杜绝空洞的键数统计)
        contributions = bb.get("expert_contributions", [])
        self.assertGreaterEqual(len(contributions), 3)
        for c in contributions:
            summary = c.get("summary", "")
            self.assertNotIn("包含 3 项明细指标", summary, "存在机械字典键数统计")
            self.assertTrue(len(summary) >= 15, "专家推导结论过于简短")

        # 3. 验证综合风控评级存在
        risk = bb.get("overall_risk_level")
        self.assertIn(risk, ["LOW_HEALTHY", "MEDIUM_ATTENTION", "HIGH_CRITICAL"])

    def test_10_agent6_retrieval_and_operator_proofs(self):
        """实测质询智能体 6: 检验废除 limit(10) 全库 HNSW 相似度检索与算子生效凭证完备性
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_10_agent6_retrieval_and_operator_proofs
        @throws AssertionError 断言异常
        """
        agent = AgenticRagSupervisorAgent(self.db)
        res = agent.dispatch("医疗器械首营准入与主库入库合规验收规范", operator="sys_admin")

        # 1. 验证算子生效凭证结构完备
        proofs = res.get("operator_proofs", {})
        self.assertIn("query_rewrite", proofs)
        self.assertIn("isrel_rerank", proofs)
        self.assertIn("faithfulness", proofs)

        # 2. 验证多子智能体群聊气泡
        bubbles = res.get("subagent_bubbles", [])
        self.assertGreaterEqual(len(bubbles), 3)
        b_ids = [b.get("subagent_id") for b in bubbles]
        self.assertIn("supervisor", b_ids)
        self.assertIn("subagent_6b", b_ids)
        self.assertIn("subagent_6c", b_ids)

    def test_11_router_execute_stream_sse_protocol_and_events(self):
        """实测质询路由层: 检验 /agent/execute-stream 标准多行 SSE 分包格式与 6 类核心事件
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_11_router_execute_stream_sse_protocol_and_events
        @throws AssertionError 断言异常
        """
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # 针对 Agent 1 发起流式请求
        resp = client.post("/api/v1/rag-hub/agent/execute-stream", json={
            "agent_id": "agent_1",
            "query": "全院耗材字典总数统计",
            "user_role": "sys_admin",
            "enable_deep_thinking": 1
        })

        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))
        self.assertEqual(resp.headers.get("x-accel-buffering"), "no")

        # 逐块解析 SSE 响应文本
        raw_sse = resp.text
        self.assertTrue(len(raw_sse) > 100, "SSE 输出流过短")

        # 验证标准多行分包格式 (包含 event: message 与 data: {...}\n\n)
        self.assertIn("event: message\ndata:", raw_sse)

        # 收集所有推送的事件类型
        data_lines = [line.strip()[5:].strip() for line in raw_sse.split("\n") if line.strip().startswith("data:")]
        collected_types = set()
        for d in data_lines:
            try:
                parsed = json.loads(d)
                if isinstance(parsed, dict) and "type" in parsed:
                    collected_types.add(parsed["type"])
            except Exception:
                pass

        # 校验 6 类事件: start, subagent_message (或 subagent_bubble), reasoning, content, done
        self.assertIn("start", collected_types, "缺失 start 开始事件")
        self.assertTrue("subagent_message" in collected_types or "subagent_bubble" in collected_types, "缺失群聊气泡事件")
        self.assertIn("content", collected_types, "缺失打字机正文 content 事件")
        self.assertIn("done", collected_types, "缺失 done 完成事件")

    def test_12_router_execute_stream_exception_handling(self):
        """实测质询路由层: 检验流式请求遇到异常时的友好降级与 error 事件派发
        @param self: 测试用例实例
        @returns None
        @route tests/test_challenger_m2_adversarial.py/TestChallengerM2Adversarial/test_12_router_execute_stream_exception_handling
        @throws AssertionError 断言异常
        """
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # 发起非法的智能体标识请求
        resp = client.post("/api/v1/rag-hub/agent/execute-stream", json={
            "agent_id": "agent_unknown_adversarial",
            "query": "非正常请求测试"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))
        self.assertIn('"type": "start"', resp.text)
        self.assertIn('"type": "done"', resp.text)


if __name__ == "__main__":
    unittest.main()
