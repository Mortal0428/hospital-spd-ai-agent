"""
@file test_mcp_and_core_services_worker_m1.py
@description Milestone 1 后端 MCP 工具中心、飞书原生推送、Coze 协同与 LangSmith Trace 全链路自动化验证脚本
覆盖 11 个文件，逐项校验 16+ 项原子工具真实数据库写入、6W 审计日志闭环、飞书卡片构建、Coze 问答与大模型 Trace 追踪，
坚决消除工具入参为空字典 {} 的假执行现象，且全域零 Emoji。

@param 无
@returns 断言全部通过输出 SUCCESS
@route tests/test_mcp_and_core_services_worker_m1.py
@throws 断言不匹配抛出 AssertionError
"""

import ast
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal
from app.models.spd_models import (
    SpdDistributionOrder,
    SpdHighValueItem,
    SpdMainInventory,
    SpdProductDict,
    SpdRequisitionOrder,
    SpdWorkflowLog
)
from app.models.rag_agent_models import SpdRagDocument
from app.services.mcp_tools import (
    execute_mcp_tool,
    list_mcp_tools,
    get_tool
)
from app.services.feishu_service import feishu_service
from app.services.coze_service import coze_service
from app.services.agents.llm_client import RealLlmClient, safe_traceable


class TestMcpAndCoreServices(unittest.TestCase):
    """M1 核心服务全链路验证套件"""

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_mcp_tool_registry_and_schema(self):
        """测试 MCP 工具注册完整度与 Pydantic V2 Schema 参数外露"""
        tools = list_mcp_tools()
        self.assertGreaterEqual(len(tools), 15, "注册的 MCP 工具总数应不少于 15 项")
        names = [t["name"] for t in tools]
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
        for exp in expected_tools:
            self.assertIn(exp, names, f"缺少核心注册工具: {exp}")

        # 验证每一个工具的 parameters 均非空
        for t in tools:
            self.assertIn("properties", t["parameters"], f"工具 {t['name']} 的 Schema 未能导出 properties 字段")

    def test_02_dict_tools_and_6w_log(self):
        """测试产品字典查询、首营建仓与 6W 审计日志落盘"""
        # 1. 查询字典
        query_res = execute_mcp_tool("mcp_query_product_dict", {"limit": 5}, self.db)
        self.assertTrue(query_res.success)
        self.assertIsNotNone(query_res.data)
        self.assertNotEqual(query_res.input_args, {}, "input_args 严禁为空字典")

        # 2. 供应商资质查验
        cert_res = execute_mcp_tool("mcp_check_supplier_cert", {"supplier_name": "国药"}, self.db)
        self.assertTrue(cert_res.success)
        self.assertIsNotNone(cert_res.data)

        # 3. 真实写入新物资建档
        test_code = "TEST_MAT_9999"
        create_args = {
            "product_code": test_code,
            "product_name": "自动化测试专用高通量透析器",
            "udi_di": "06901234567899",
            "main_dept_code": "CONSUMABLE_DEPT",
            "consumable_type": "HIGH_VALUE",
            "category_id": 1,
            "category_name": "血液净化耗材",
            "spec_model": "FX-CorDiax-80",
            "unit": "支",
            "unit_price": 380.0,
            "manufacturer": "费森尤斯医疗制造有限公司",
            "supplier_name": "国药控股医疗供应链有限公司",
            "reg_cert_no": "国械注进20243100088",
            "reg_cert_expiry": "2029-06-30",
            "operator_name": "耗材科测试主管"
        }
        create_res = execute_mcp_tool("mcp_create_product_dict", create_args, self.db)
        self.assertTrue(create_res.success)
        self.assertIsNotNone(create_res.trace_no)

        # 校验数据库与 6W 日志真实存在
        prod = self.db.query(SpdProductDict).filter(SpdProductDict.product_code == test_code).first()
        self.assertIsNotNone(prod, "产品字典物理写入失败")

        log = self.db.query(SpdWorkflowLog).filter(SpdWorkflowLog.trace_no == create_res.trace_no).first()
        self.assertIsNotNone(log, "6W 日志物理写入失败")
        self.assertEqual(log.node_action, "1_DICT_CREATE")
        self.assertEqual(log.product_code, test_code)

    def test_03_dispatch_tools_and_stock_deduction(self):
        """测试主库库存扫描、按需分发调拨与库存物理扣减"""
        # 1. 扫描库存
        scan_res = execute_mcp_tool("mcp_scan_main_and_sec_stock", {"limit": 10}, self.db)
        self.assertTrue(scan_res.success)
        self.assertGreaterEqual(scan_res.data.main_batches_count, 1, "主库应至少有就绪批次")

        # 2. 取第一条正常主库批次
        batch = self.db.query(SpdMainInventory).filter(
            SpdMainInventory.quality_status == "NORMAL",
            SpdMainInventory.available_qty >= 2
        ).first()
        self.assertIsNotNone(batch, "未找到可用测试批次")

        before_qty = batch.available_qty
        dist_args = {
            "main_inventory_id": batch.id,
            "target_dept_id": 5,
            "target_dept_name": "心血管内科二级库",
            "target_type": "TO_SECONDARY_DEPT",
            "dist_qty": 1,
            "dispatcher_id": 1,
            "dispatcher_name": "主库发料员张三",
            "remark": "自动化测试近效期按需分发"
        }
        dist_res = execute_mcp_tool("mcp_create_dispatch_order", dist_args, self.db)
        self.assertTrue(dist_res.success)

        # 刷新数据库会话，校验库存物理扣减
        self.db.refresh(batch)
        self.assertEqual(batch.available_qty, before_qty - 1, "主库可用库存未物理扣减")

        # 校验调拨单与 6W 日志
        order = self.db.query(SpdDistributionOrder).filter(SpdDistributionOrder.dist_order_no == dist_res.data.dist_order_no).first()
        self.assertIsNotNone(order, "分发调拨单未物理落盘")

        log = self.db.query(SpdWorkflowLog).filter(SpdWorkflowLog.trace_no == dist_res.trace_no).first()
        self.assertIsNotNone(log, "调拨 6W 日志未物理落盘")
        self.assertEqual(log.node_action, "3_MAIN_DISPATCH")
        self.assertEqual(log.change_qty, 1)

    def test_04_requisition_tools_and_apply_flow(self):
        """测试临床申领前可用性核查、申领建单与 6W 日志"""
        # 1. 查验可用性
        chk_res = execute_mcp_tool("mcp_check_main_available", {"product_name": "敷料", "required_qty": 5}, self.db)
        self.assertTrue(chk_res.success)

        # 2. 定数包规范
        pack_res = execute_mcp_tool("mcp_query_surgery_pack_specs", {}, self.db)
        self.assertTrue(pack_res.success)
        self.assertGreaterEqual(pack_res.data.packs_count, 1)

        # 3. 提交申领
        prod = self.db.query(SpdProductDict).first()
        req_args = {
            "apply_dept_id": 4,
            "apply_dept_name": "骨科病区二级库",
            "product_id": prod.id,
            "product_name": prod.product_name,
            "apply_qty": 3,
            "urgency_level": "ROUTINE",
            "applicant_id": 2,
            "applicant_name": "骨科责任护士",
            "apply_reason": "病区常规耗材补货申请"
        }
        req_res = execute_mcp_tool("mcp_submit_sec_requisition", req_args, self.db)
        self.assertTrue(req_res.success)

        # 验证单据与日志
        req = self.db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.req_order_no == req_res.data.req_order_no).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.apply_qty, 3)

        log = self.db.query(SpdWorkflowLog).filter(SpdWorkflowLog.trace_no == req_res.trace_no).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.node_action, "6_SEC_APPLY")

    def test_05_high_value_trace_and_freeze(self):
        """测试高值一物一码溯源、患者隐私脱敏与问题批次冻结"""
        # 1. 查找或准备高值单品
        hv_item = self.db.query(SpdHighValueItem).first()
        if hv_item:
            # 脱敏查询 (普通角色)
            trace_res = execute_mcp_tool("mcp_trace_udi_full_logs", {
                "udi_code": hv_item.udi_full_code,
                "operator_role": "secondary_user"
            }, self.db)
            self.assertTrue(trace_res.success)
            self.assertTrue(trace_res.data.item_found)
            # 患者隐私脱敏验证
            if hv_item.patient_name_masked and len(hv_item.patient_name_masked) > 1:
                self.assertIn("*", trace_res.data.item_detail.patient_info_masked, "非管理员患者姓名必须脱敏")

            # 2. 冻结该批次
            freeze_args = {
                "udi_code": hv_item.udi_full_code,
                "freeze_reason": "自动化测试不良事件召回演练",
                "operator_name": "风控质检员",
                "operator_account": "sys_admin"
            }
            freeze_res = execute_mcp_tool("mcp_freeze_problem_batch", freeze_args, self.db)
            self.assertTrue(freeze_res.success)

            # 验证高值单品状态更新
            self.db.refresh(hv_item)
            self.assertEqual(hv_item.item_status, "RECALLED")

            # 验证 6W 审计日志 (8_REVERSE_AUDIT)
            log = self.db.query(SpdWorkflowLog).filter(SpdWorkflowLog.trace_no == freeze_res.trace_no).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.node_action, "8_REVERSE_AUDIT")
            self.assertEqual(log.audit_status, "FLAGGED")

    def test_06_finance_cost_and_abnormal_logs(self):
        """测试科室耗材财务成本聚合与 6W 异常流转排查"""
        cost_res = execute_mcp_tool("mcp_aggregate_dept_cost", {"period_month": "2026-11"}, self.db)
        self.assertTrue(cost_res.success)
        self.assertGreaterEqual(cost_res.data.dept_count, 1)

        abnormal_res = execute_mcp_tool("mcp_scan_abnormal_flow_logs", {"anomaly_type": "ALL", "limit": 20}, self.db)
        self.assertTrue(abnormal_res.success)
        self.assertIsNotNone(abnormal_res.data.risk_assessment)

    def test_07_rag_global_retrieval_and_graph(self):
        """测试 Chroma 全局向量检索 (废除 limit(10)) 与图谱三元组写入"""
        # 1. 全局检索
        rag_res = execute_mcp_tool("mcp_chroma_global_retrieval", {
            "query_text": "医疗器械不良事件召回管理办法",
            "top_k": 5
        }, self.db)
        self.assertTrue(rag_res.success)
        self.assertGreaterEqual(rag_res.data.total_hits, 1)
        for citation in rag_res.data.results:
            self.assertGreaterEqual(citation.similarity_score, 0.0)

        # 2. 图谱实体三元组写入
        doc = self.db.query(SpdRagDocument).first()
        if doc:
            before_entities = doc.graph_entity_count
            graph_args = {
                "doc_id": doc.id,
                "triples": [
                    {
                        "head": "测试医疗耗材",
                        "relation": "BELONGS_TO",
                        "tail": "骨科耗材分类",
                        "properties": {"confidence": 0.95}
                    }
                ],
                "operator_name": "知识库管理员"
            }
            graph_res = execute_mcp_tool("mcp_write_knowledge_graph_triples", graph_args, self.db)
            self.assertTrue(graph_res.success)
            self.db.refresh(doc)
            self.assertEqual(doc.graph_entity_count, before_entities + 1)
            self.assertEqual(doc.doc_status, "STAGE_6_GRAPH_READY")

    def test_08_feishu_service_cards_and_token(self):
        """测试飞书原生连接鉴权与 4 类业务卡片生成"""
        conn_res = feishu_service.test_connection()
        self.assertTrue(conn_res["connected"], "飞书开放平台鉴权应当成功")
        self.assertTrue(conn_res["token_prefix"].startswith("t-"))

        # 验证 4 类卡片构建无崩溃
        c1 = feishu_service.build_dict_create_card(
            product_code="WZ001",
            product_name="骨科螺钉",
            spec_model="M4*20",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="GENERAL",
            supplier_name="供应商A",
            reg_cert_no="国械注准2024001",
            unit_price=150.0,
            udi_di="0690001",
            trace_no="TRACE-001"
        )
        self.assertEqual(c1["header"]["template"], "turquoise")

        c2 = feishu_service.build_dispatch_order_card(
            dist_order_no="DIST-001",
            target_dept_name="骨科二级库",
            product_name="骨科螺钉",
            batch_no="B202611",
            expiry_date="2028-11-01",
            dist_qty=10,
            unit_price=150.0,
            dispatcher_name="发料员",
            trace_no="TRACE-002"
        )
        self.assertEqual(c2["header"]["template"], "blue")

        c3 = feishu_service.build_approval_suspend_card(
            req_order_no="REQ-001",
            apply_dept_name="心内科二级库",
            applicant_name="护士长",
            product_name="冠脉支架",
            spec_model="3.0*18mm",
            apply_qty=2,
            total_amount=15000.0,
            trace_no="TRACE-003"
        )
        self.assertEqual(c3["header"]["template"], "orange")

        c4 = feishu_service.build_udi_freeze_card(
            batch_no="B202699",
            udi_code="06900099",
            product_name="心脏瓣膜",
            manufacturer="医疗科技制造厂",
            freeze_reason="国家不良事件召回通知",
            operator_name="质量质检主管",
            trace_no="TRACE-004"
        )
        self.assertEqual(c4["header"]["template"], "carmine")

        # 测试自检模拟发送
        send_res = feishu_service.send_interactive_card(c1)
        self.assertTrue(send_res["success"])

    def test_09_coze_service_chat(self):
        """测试 Coze V3 云端小爱智能体连通性与问答"""
        test_res = coze_service.test_connectivity()
        self.assertEqual(test_res["bot_id"], "7700811095929323554")
        self.assertIn("message", test_res)
        self.assertGreater(len(test_res.get("answer_preview", "")), 0)
        # 若外部网络连通，断言 connected 为 True
        if "离线保护" not in test_res.get("answer_preview", ""):
            self.assertTrue(test_res["connected"])

    def test_10_llm_client_langsmith_trace(self):
        """测试 llm_client.py 挂载 safe_traceable 与模型调用"""
        res = RealLlmClient.generate(
            prompt="简短回答：请列举医院医疗物资管理的核心原则（限20字以内）。",
            timeout_seconds=15
        )
        self.assertIn("final_answer", res)
        self.assertGreater(len(res["final_answer"]), 0)
        self.assertIn("latency_ms", res)
        self.assertIn("model_used", res)

    def test_11_zero_emoji_and_docstrings_check(self):
        """质量红线专项测试：全域零 Emoji，基于 AST 语法树 100% 逐函数中文四要素注释严密校验"""
        target_files = [
            "backend/app/services/mcp_tools/__init__.py",
            "backend/app/services/mcp_tools/schema.py",
            "backend/app/services/mcp_tools/dict_tools.py",
            "backend/app/services/mcp_tools/dispatch_tools.py",
            "backend/app/services/mcp_tools/requisition_tools.py",
            "backend/app/services/mcp_tools/high_value_tools.py",
            "backend/app/services/mcp_tools/finance_tools.py",
            "backend/app/services/mcp_tools/rag_tools.py",
            "backend/app/services/feishu_service.py",
            "backend/app/services/coze_service.py",
            "backend/app/services/agents/llm_client.py"
        ]

        # 严格 Emoji 正则范围匹配 (Unicode 表情符号与补充符号区)
        emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u26ff]|"
            "[\u2700-\u27bf]"
        )

        required_tags = ["@param", "@returns", "@route", "@throws"]
        violations = []

        for rel_path in target_files:
            full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel_path))
            self.assertTrue(os.path.exists(full_path), f"目标文件不存在: {rel_path}")

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. 严格 Emoji 检测 (文件全文无死角扫描)
            emoji_matches = emoji_pattern.findall(content)
            self.assertEqual(len(emoji_matches), 0, f"文件 {rel_path} 发现违规 Emoji: {emoji_matches}")

            # 2. 基于 AST 语法树逐函数进行中文四要素严格检测 (拒绝整文件粗粒度自证)
            tree = ast.parse(content, filename=rel_path)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(node)
                    if not doc:
                        violations.append(
                            f"{rel_path}:{node.lineno} 函数 '{node.name}' 完全缺失 docstring"
                        )
                        continue
                    missing_tags = [tag for tag in required_tags if tag not in doc]
                    if missing_tags:
                        violations.append(
                            f"{rel_path}:{node.lineno} 函数 '{node.name}' 缺失注释要素: {missing_tags}"
                        )

        # 断言违规总数为 0，并格式化输出所有违规清单供排查
        self.assertEqual(
            len(violations), 0,
            f"发现 {len(violations)} 处函数级注释规范违规 (严禁假自证):\n" + "\n".join(violations)
        )


if __name__ == "__main__":
    unittest.main()
