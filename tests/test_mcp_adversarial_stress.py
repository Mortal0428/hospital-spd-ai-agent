"""
@file test_mcp_adversarial_stress.py
@description Milestone 1 MCP 工具中心对抗性压力测试与边界校验套件
涵盖空参/缺参校验、未知参数拦截 (extra="forbid")、负数数量越界、超长字符、SQL注入载荷、
不存在工具调度、数据库落盘真实性与 6W 审计日志链路完整性，以及异常回滚防残存记录验证。
全域零 Emoji，函数级中文四要素注释覆盖率 100%。

@param 无
@returns unittest / pytest 自动化对抗测试执行结果
@route tests/test_mcp_adversarial_stress.py
@throws 断言不满足时抛出 AssertionError
"""

import os
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal

# 将工程路径加入 sys.path
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
from app.services.mcp_tools import (
    execute_mcp_tool,
    get_tool,
    list_mcp_tools
)


class TestMcpAdversarialStress(unittest.TestCase):
    """MCP 工具中心对抗压力与边界渗透测试套件"""

    def setUp(self):
        """测试前置配置：初始化数据库独立会话

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/setUp
        @throws 数据库连接异常
        """
        self.db = SessionLocal()

    def tearDown(self):
        """测试后置清理：释放会话与回滚任何未提交事务

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/tearDown
        @throws 无
        """
        if self.db:
            self.db.rollback()
            self.db.close()

    # =========================================================================
    # 维度 1: 空参/缺参调用测试与未知字段拦截 (extra="forbid")
    # =========================================================================

    def test_01_empty_args_on_required_tools(self):
        """验证对包含必填项的工具传入空字典 {} 时，能否精确触发 Pydantic 校验失败而非假执行

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_01_empty_args_on_required_tools
        @throws AssertionError
        """
        required_tools = [
            "mcp_create_product_dict",
            "mcp_create_dispatch_order",
            "mcp_submit_sec_requisition",
            "mcp_freeze_problem_batch",
            "mcp_chroma_global_retrieval",
            "mcp_write_knowledge_graph_triples"
        ]

        for tool_name in required_tools:
            res = execute_mcp_tool(tool_name, {}, self.db)
            self.assertFalse(res.success, f"工具 {tool_name} 传入空字典必须执行失败")
            self.assertEqual(res.error, "INVALID_ARGUMENTS", f"工具 {tool_name} 错误类型必须为 INVALID_ARGUMENTS")
            self.assertIn("validation error", res.message.lower(), f"工具 {tool_name} 错误消息中应包含校验异常描述")
            self.assertIsNone(res.data, f"工具 {tool_name} 校验失败时不应产出业务数据")

    def test_02_optional_tools_with_empty_dict_populate_defaults(self):
        """验证仅含可选参数的工具传入空字典 {} 时正常执行且 input_args 填充默认值，杜绝空字典逃逸

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_02_optional_tools_with_empty_dict_populate_defaults
        @throws AssertionError
        """
        optional_tools = [
            "mcp_query_product_dict",
            "mcp_scan_main_and_sec_stock",
            "mcp_aggregate_dept_cost",
            "mcp_query_knowledge_stats"
        ]

        for tool_name in optional_tools:
            res = execute_mcp_tool(tool_name, {}, self.db)
            self.assertTrue(res.success, f"纯可选参数工具 {tool_name} 传入空参数应能使用默认值成功执行")
            self.assertIsNotNone(res.data, f"工具 {tool_name} 应返回有效数据")
            # 关键验证：res.input_args 绝不能是空字典
            self.assertNotEqual(res.input_args, {}, f"工具 {tool_name} 的 input_args 不应为空字典，应外露默认值")
            dict_rep = res.to_dict()
            self.assertIn("args", dict_rep)
            self.assertIn("input_args", dict_rep)
            self.assertNotEqual(dict_rep["args"], {})

    def test_03_extra_unknown_parameters_blocked_by_forbid(self):
        """验证 extra='forbid' 策略能否有效阻断未声明的异常入参与潜在恶意载荷

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_03_extra_unknown_parameters_blocked_by_forbid
        @throws AssertionError
        """
        tampered_cases = [
            ("mcp_query_product_dict", {"limit": 5, "unknown_field_payload": "hack"}),
            ("mcp_check_supplier_cert", {"supplier_name": "国药", "extra_token": 12345}),
            ("mcp_scan_main_and_sec_stock", {"extra_param": True}),
            ("mcp_aggregate_dept_cost", {"period_month": "2026-11", "tampered_flag": "malicious"}),
            ("mcp_query_knowledge_stats", {"illegal_key": "data"})
        ]

        for tool_name, args in tampered_cases:
            res = execute_mcp_tool(tool_name, args, self.db)
            self.assertFalse(res.success, f"工具 {tool_name} 传入未定义字段应被 extra='forbid' 阻断")
            self.assertEqual(res.error, "INVALID_ARGUMENTS")
            msg_lower = res.message.lower()
            self.assertTrue(
                "extra" in msg_lower or "forbidden" in msg_lower or "extra inputs are not permitted" in msg_lower,
                f"错误提示应明确指明多余字段被禁止: {res.message}"
            )

    # =========================================================================
    # 维度 2: 边界值约束与 SQL 注入渗透测试
    # =========================================================================

    def test_04_negative_and_zero_quantities_boundary(self):
        """验证负数与零数量的边界拦截 (gt=0 / ge=0.0 / ge=1)

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_04_negative_and_zero_quantities_boundary
        @throws AssertionError
        """
        # 1. 调拨数量负数与 0 拦截
        res_disp_neg = execute_mcp_tool("mcp_create_dispatch_order", {
            "main_inventory_id": 1,
            "target_dept_id": 2,
            "target_dept_name": "临床测试病区",
            "dist_qty": -5
        }, self.db)
        self.assertFalse(res_disp_neg.success)
        self.assertEqual(res_disp_neg.error, "INVALID_ARGUMENTS")

        res_disp_zero = execute_mcp_tool("mcp_create_dispatch_order", {
            "main_inventory_id": 1,
            "target_dept_id": 2,
            "target_dept_name": "临床测试病区",
            "dist_qty": 0
        }, self.db)
        self.assertFalse(res_disp_zero.success)
        self.assertEqual(res_disp_zero.error, "INVALID_ARGUMENTS")

        # 2. 申领数量负数拦截
        res_req_neg = execute_mcp_tool("mcp_submit_sec_requisition", {
            "apply_dept_id": 2,
            "apply_dept_name": "手术室",
            "product_id": 1,
            "apply_qty": -10
        }, self.db)
        self.assertFalse(res_req_neg.success)
        self.assertEqual(res_req_neg.error, "INVALID_ARGUMENTS")

        # 3. 单价负数拦截 (ge=0.0)
        res_price_neg = execute_mcp_tool("mcp_create_product_dict", {
            "product_code": "CHALLENGE_NEG_PRICE",
            "product_name": "负单价违规测试物资",
            "udi_di": "06900000000001",
            "unit_price": -15.5
        }, self.db)
        self.assertFalse(res_price_neg.success)
        self.assertEqual(res_price_neg.error, "INVALID_ARGUMENTS")

        # 4. limit 上下限越界拦截 (ge=1, le=100)
        res_limit_zero = execute_mcp_tool("mcp_query_product_dict", {"limit": 0}, self.db)
        self.assertFalse(res_limit_zero.success)
        self.assertEqual(res_limit_zero.error, "INVALID_ARGUMENTS")

        res_limit_overflow = execute_mcp_tool("mcp_query_product_dict", {"limit": 1000}, self.db)
        self.assertFalse(res_limit_overflow.success)
        self.assertEqual(res_limit_overflow.error, "INVALID_ARGUMENTS")

    def test_05_string_length_and_format_boundaries(self):
        """验证字符长度边界与超长字符压力防护

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_05_string_length_and_format_boundaries
        @throws AssertionError
        """
        # 1. 物资编码过短 (min_length=2)
        res_short_code = execute_mcp_tool("mcp_create_product_dict", {
            "product_code": "X",
            "product_name": "有效物资名称",
            "udi_di": "06900000000001"
        }, self.db)
        self.assertFalse(res_short_code.success)
        self.assertEqual(res_short_code.error, "INVALID_ARGUMENTS")

        # 2. UDI-DI 码过短 (min_length=5)
        res_short_di = execute_mcp_tool("mcp_create_product_dict", {
            "product_code": "CHALLENGE_SHORT_DI",
            "product_name": "有效物资名称",
            "udi_di": "123"
        }, self.db)
        self.assertFalse(res_short_di.success)
        self.assertEqual(res_short_di.error, "INVALID_ARGUMENTS")

        # 3. 召回冻结原因过短 (min_length=4)
        res_short_reason = execute_mcp_tool("mcp_freeze_problem_batch", {
            "batch_no": "BATCH_20261105",
            "freeze_reason": "bad"
        }, self.db)
        self.assertFalse(res_short_reason.success)
        self.assertEqual(res_short_reason.error, "INVALID_ARGUMENTS")

        # 4. 超长字符串模糊检索 (5000 字符)，验证参数化安全查询不导致数据库崩溃或抛出 500
        extreme_name = "抗凝管" + "A" * 5000
        res_extreme = execute_mcp_tool("mcp_query_product_dict", {"product_name": extreme_name}, self.db)
        self.assertTrue(res_extreme.success)
        self.assertIsNotNone(res_extreme.data)
        self.assertEqual(len(res_extreme.data.items), 0, "超长无意义字符应安全返回 0 条匹配")

    def test_06_sql_injection_payload_defense(self):
        """验证典型 SQL 注入载荷在各类 MCP 工具输入中的参数化防御安全性

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_06_sql_injection_payload_defense
        @throws AssertionError
        """
        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE spd_product_dict; --",
            "' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21 --",
            "1' AND SLEEP(2) --",
            "\" OR \"\"=\""
        ]

        # 1. 字典查询中的 SQL 注入测试
        for payload in sqli_payloads:
            res_dict = execute_mcp_tool("mcp_query_product_dict", {"product_name": payload}, self.db)
            self.assertTrue(res_dict.success, f"SQLi payload [{payload}] 查询应由 SQLAlchemy 参数化安全处理")
            self.assertIsNotNone(res_dict.data)

        # 2. 库存扫描中的 SQL 注入测试
        for payload in sqli_payloads:
            res_stock = execute_mcp_tool("mcp_scan_main_and_sec_stock", {"product_code": payload}, self.db)
            self.assertTrue(res_stock.success)
            self.assertIsNotNone(res_stock.data)

        # 3. 高值 UDI 溯源中的 SQL 注入测试
        for payload in sqli_payloads:
            res_udi = execute_mcp_tool("mcp_trace_udi_full_logs", {"udi_code": payload, "batch_no": payload}, self.db)
            self.assertTrue(res_udi.success)
            self.assertIsNotNone(res_udi.data)
            self.assertFalse(res_udi.data.item_found, "恶意注入条码不应非法越权命中数据")

        # 4. 确认核心表结构完好存在（证明注入语句未被执行）
        dict_count = self.db.query(SpdProductDict).count()
        self.assertGreater(dict_count, 0, "字典表应完好存在且记录数大于 0")

    def test_07_non_existent_and_invalid_tool_names(self):
        """验证调度未注册工具名、空串或非法类型时的统一拦截处理

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_07_non_existent_and_invalid_tool_names
        @throws AssertionError
        """
        invalid_names = [
            "mcp_fake_non_existent_tool",
            "drop_database_tool",
            "",
            "   ",
            "__import__('os').system('ls')"
        ]

        for name in invalid_names:
            res = execute_mcp_tool(name, {"param": 1}, self.db)
            self.assertFalse(res.success)
            self.assertEqual(res.error, "TOOL_NOT_FOUND")
            self.assertIn("未找到已注册的 MCP 工具", res.message)

    # =========================================================================
    # 维度 3: 数据库真实落盘、6W 流转日志链路与异常回滚零残存验证
    # =========================================================================

    def test_08_create_product_dict_db_and_6w_trace_integrity(self):
        """验证 mcp_create_product_dict 真实写入 MySQL 数据库且与 6W 日志流水号强一致

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_08_create_product_dict_db_and_6w_trace_integrity
        @throws AssertionError
        """
        ts_int = int(datetime.now().timestamp())
        unique_code = f"CHALLENGE_PROD_{ts_int}"
        unique_udi = f"069{ts_int % 100000000000:011d}"
        test_args = {
            "product_code": unique_code,
            "product_name": "对抗性压测验证专用一次性留置针",
            "udi_di": unique_udi,
            "main_dept_code": "CONSUMABLE_DEPT",
            "consumable_type": "GENERAL",
            "category_id": 1,
            "category_name": "通用输注耗材",
            "spec_model": "22G-蓝色",
            "unit": "支",
            "unit_price": 6.80,
            "manufacturer": "山东威高集团医用高分子制品股份有限公司",
            "supplier_name": "国药控股医疗供应链有限公司",
            "reg_cert_no": "国械注准20243140123",
            "reg_cert_expiry": "2029-12-31",
            "operator_name": "质量内控挑战员"
        }

        res = execute_mcp_tool("mcp_create_product_dict", test_args, self.db)
        self.assertTrue(res.success, f"建档应执行成功: {res.message}")
        self.assertIsNotNone(res.trace_no, "必须返回 6W 日志追踪流水号")

        # 1. 穿透检验 SpdProductDict 表实体
        prod = self.db.query(SpdProductDict).filter(
            SpdProductDict.product_code == unique_code,
            SpdProductDict.is_deleted == 0
        ).first()
        self.assertIsNotNone(prod, "SpdProductDict 中必须真实存在建档记录")
        self.assertEqual(prod.product_name, test_args["product_name"])
        self.assertEqual(float(prod.unit_price), 6.80)

        # 2. 穿透检验 SpdWorkflowLog 表实体
        log_entry = self.db.query(SpdWorkflowLog).filter(
            SpdWorkflowLog.trace_no == res.trace_no
        ).first()
        self.assertIsNotNone(log_entry, "SpdWorkflowLog 中必须真实存在对应 trace_no 的流转日志")
        self.assertEqual(log_entry.node_action, "1_DICT_CREATE")
        self.assertEqual(log_entry.product_code, unique_code)
        self.assertEqual(log_entry.from_user_name, "质量内控挑战员")

    def test_09_create_dispatch_order_stock_deduction_and_6w_linkage(self):
        """验证 mcp_create_dispatch_order 扣减主库库存、生成调拨单并闭环联动 6W 日志

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_09_create_dispatch_order_stock_deduction_and_6w_linkage
        @throws AssertionError
        """
        # 寻找可用于分发测试的批次（可用库存 >= 5 且状态 NORMAL）
        target_inv = self.db.query(SpdMainInventory).filter(
            SpdMainInventory.available_qty >= 5,
            SpdMainInventory.quality_status == "NORMAL"
        ).first()

        self.assertIsNotNone(target_inv, "数据库中应存在至少一条可用库存批次用于测试")
        inv_id = target_inv.id
        initial_qty = target_inv.available_qty
        dist_qty = 2

        dispatch_args = {
            "main_inventory_id": inv_id,
            "target_dept_id": 1,
            "target_dept_name": "急诊科二级库",
            "target_type": "TO_SECONDARY_DEPT",
            "dist_qty": dist_qty,
            "dispatcher_id": 99,
            "dispatcher_name": "压力测试发料专员",
            "remark": "对抗性调拨核减压力测试"
        }

        res = execute_mcp_tool("mcp_create_dispatch_order", dispatch_args, self.db)
        self.assertTrue(res.success, f"调拨建单应成功: {res.message}")
        self.assertIsNotNone(res.trace_no)

        # 1. 验证主库库存是否物理核减
        self.db.refresh(target_inv)
        self.assertEqual(
            target_inv.available_qty,
            initial_qty - dist_qty,
            "主库 available_qty 必须精确扣减 dist_qty"
        )

        # 2. 验证 SpdDistributionOrder 是否物理存在
        dist_order = self.db.query(SpdDistributionOrder).filter(
            SpdDistributionOrder.dist_order_no == res.data.dist_order_no
        ).first()
        self.assertIsNotNone(dist_order, "SpdDistributionOrder 表中必须存在对应的调拨单实体")
        self.assertEqual(dist_order.dist_qty, dist_qty)
        self.assertEqual(dist_order.order_status, "DISPATCHED")

        # 3. 验证 6W 审计日志流转项
        wf_log = self.db.query(SpdWorkflowLog).filter(
            SpdWorkflowLog.trace_no == res.trace_no
        ).first()
        self.assertIsNotNone(wf_log, "SpdWorkflowLog 中必须存在对应的 6W 追踪日志")
        self.assertEqual(wf_log.node_action, "3_MAIN_DISPATCH")
        self.assertEqual(wf_log.change_qty, dist_qty)
        self.assertEqual(wf_log.before_stock_snapshot, initial_qty)
        self.assertEqual(wf_log.after_stock_snapshot, initial_qty - dist_qty)

    def test_10_clean_rollback_and_zero_corrupted_records_on_failure(self):
        """验证当操作在参数校验或业务校验阶段失败时，数据库事务安全回滚且绝无半残存记录

        @param 无
        @returns 无
        @route tests/test_mcp_adversarial_stress.py/test_10_clean_rollback_and_zero_corrupted_records_on_failure
        @throws AssertionError
        """
        # 场景 A: 参数校验失败时的零写入验证
        fail_code = f"FAIL_PARAM_{int(datetime.now().timestamp())}"
        invalid_create_args = {
            "product_code": fail_code,
            "product_name": "必将失败的测试品",
            "udi_di": "06900000000000",
            "unit_price": -999.0  # 负数单价导致校验失败
        }
        res_fail_param = execute_mcp_tool("mcp_create_product_dict", invalid_create_args, self.db)
        self.assertFalse(res_fail_param.success)

        # 验证数据库中不存在任何该 code 的记录
        leak_prod = self.db.query(SpdProductDict).filter(SpdProductDict.product_code == fail_code).first()
        self.assertIsNone(leak_prod, "参数校验失败时，SpdProductDict 绝不应残存任何半条记录")

        leak_log = self.db.query(SpdWorkflowLog).filter(SpdWorkflowLog.biz_order_no == f"DICT-{fail_code}").first()
        self.assertIsNone(leak_log, "参数校验失败时，SpdWorkflowLog 绝不应残存任何审计日志")

        # 场景 B: 业务逻辑校验失败 (不存在的主库批次库存 ID) 时的事务回滚
        non_exist_inv_id = 99999999
        fake_dept = f"NON_EXIST_DEPT_{int(datetime.now().timestamp())}"
        res_fail_inv = execute_mcp_tool("mcp_create_dispatch_order", {
            "main_inventory_id": non_exist_inv_id,
            "target_dept_id": 999,
            "target_dept_name": fake_dept,
            "dist_qty": 1
        }, self.db)
        self.assertFalse(res_fail_inv.success)
        self.assertEqual(res_fail_inv.error, "MAIN_BATCH_NOT_FOUND")

        # 验证 SpdDistributionOrder 无任何该科室的脏数据
        leak_dist = self.db.query(SpdDistributionOrder).filter(
            SpdDistributionOrder.target_dept_name == fake_dept
        ).first()
        self.assertIsNone(leak_dist, "批次不存在时，SpdDistributionOrder 绝不应生成调拨记录")

        # 场景 C: 超量调拨 (库存不足) 时的事务保护与零变更
        valid_inv = self.db.query(SpdMainInventory).filter(
            SpdMainInventory.available_qty > 0,
            SpdMainInventory.quality_status == "NORMAL"
        ).first()
        self.assertIsNotNone(valid_inv)
        original_stock = valid_inv.available_qty
        excessive_qty = original_stock + 999999

        res_over_disp = execute_mcp_tool("mcp_create_dispatch_order", {
            "main_inventory_id": valid_inv.id,
            "target_dept_id": 1,
            "target_dept_name": "库存溢出测试科室",
            "dist_qty": excessive_qty
        }, self.db)
        self.assertFalse(res_over_disp.success)
        self.assertEqual(res_over_disp.error, "INSUFFICIENT_STOCK")

        # 验证库存余量未发生任何改变
        self.db.refresh(valid_inv)
        self.assertEqual(valid_inv.available_qty, original_stock, "超量调拨失败时，主库库存必须保持原样")


if __name__ == "__main__":
    unittest.main()
