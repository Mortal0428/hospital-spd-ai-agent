"""
@file test_challenger_m1_adversarial.py
@description 对抗性质量挑战测试套件：针对飞书服务、Coze服务、LangSmith链路、AST语法树注释突变证伪及Card 2.0双轨兼容性的严苛健壮性压测
覆盖 22 项严苛对抗测试用例，100% 覆盖函数级中文四要素注释，全域零 Emoji。

@param 无
@returns unittest.TestResult 测试执行结果
@route tests/test_challenger_m1_adversarial.py
@throws AssertionError 若任一对抗防御断言未通过
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import httpx

# 导入路径修正，确保能定位 backend 源码
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.feishu_service import FeishuService, feishu_service
from app.services.coze_service import CozeService, coze_service
from app.services.agents.llm_client import RealLlmClient, safe_traceable


class TestM1AdversarialChallenge(unittest.TestCase):
    """Milestone 1 核心服务对抗性压力与容错验证测试用例集"""

    def setUp(self):
        """测试前置初始化
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/setUp
        @throws 无
        """
        # 保存原始环境变量用于测试后复原
        self._orig_env = os.environ.copy()

    def tearDown(self):
        """测试后置环境清理
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/tearDown
        @throws 无
        """
        os.environ.clear()
        os.environ.update(self._orig_env)

    # =========================================================================
    # 一、飞书服务 (FeishuService) 逆向与对抗测试
    # =========================================================================

    def test_01_feishu_token_network_connection_error(self):
        """对抗测试 01: 飞书 Token 获取时遭遇完全网络断开 (ConnectError)
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_01_feishu_token_network_connection_error
        @throws AssertionError
        """
        svc = FeishuService(app_id="cli_mock_test", app_secret="secret_mock_test")
        with patch("httpx.Client.post", side_effect=httpx.ConnectError("网络不可达")):
            with self.assertRaises(RuntimeError) as ctx:
                svc.get_tenant_access_token(force_refresh=True)
            self.assertIn("飞书鉴权连接失败", str(ctx.exception))
            self.assertIn("网络不可达", str(ctx.exception))

    def test_02_feishu_token_http_500_status(self):
        """对抗测试 02: 飞书 Token 端点返回 HTTP 500 服务端内部错误
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_02_feishu_token_http_500_status
        @throws AssertionError
        """
        svc = FeishuService()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("httpx.Client.post", return_value=mock_resp):
            with self.assertRaises(RuntimeError) as ctx:
                svc.get_tenant_access_token(force_refresh=True)
            self.assertIn("飞书 Token HTTP 异常状态码: 500", str(ctx.exception))

    def test_03_feishu_token_api_error_code(self):
        """对抗测试 03: 飞书 Token 端点返回业务级错误码 (如 99991663 密钥无效)
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_03_feishu_token_api_error_code
        @throws AssertionError
        """
        svc = FeishuService()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": 99991663,
            "msg": "app secret invalid",
            "error": "bad credential"
        }

        with patch("httpx.Client.post", return_value=mock_resp):
            with self.assertRaises(RuntimeError) as ctx:
                svc.get_tenant_access_token(force_refresh=True)
            self.assertIn("飞书 Token 接口返回错误: code=99991663", str(ctx.exception))

    def test_04_feishu_test_connection_under_network_failure(self):
        """对抗测试 04: 验证网络断开时 test_connection 返回规范字典且绝不崩溃抛出
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_04_feishu_test_connection_under_network_failure
        @throws AssertionError
        """
        svc = FeishuService()
        with patch.object(svc, "get_tenant_access_token", side_effect=RuntimeError("DNS 解析超时")):
            res = svc.test_connection()
            # 严格断言结构体字段契约
            self.assertIsInstance(res, dict)
            self.assertFalse(res.get("connected"))
            self.assertIn("latency_ms", res)
            self.assertGreaterEqual(res["latency_ms"], 0)
            self.assertIn("DNS 解析超时", res.get("error", ""))
            self.assertIn("飞书连接检测未通过", res.get("message", ""))

    def test_05_feishu_send_card_with_token_failure(self):
        """对抗测试 05: 当 Token 获取失败时，调用 send_interactive_card 必须安全捕获并降级
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_05_feishu_send_card_with_token_failure
        @throws AssertionError
        """
        svc = FeishuService()
        card = {"header": {"title": {"content": "测试"}}}
        with patch.object(svc, "get_tenant_access_token", side_effect=RuntimeError("Token 服务离线")):
            res = svc.send_interactive_card(card_content=card, receive_id="ou_test_user_id")
            self.assertIsInstance(res, dict)
            self.assertFalse(res.get("success"))
            self.assertEqual(res.get("method"), "open_api")
            self.assertIn("Token 服务离线", res.get("error", ""))
            self.assertEqual(res.get("card"), card)

    def test_06_feishu_send_card_invalid_schema_unserializable(self):
        """对抗测试 06: 传入包含不可 JSON 序列化对象的畸形卡片，验证安全捕获
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_06_feishu_send_card_invalid_schema_unserializable
        @throws AssertionError
        """
        svc = FeishuService()
        # set 集合对象在 json.dumps 时会触发 TypeError
        malformed_card = {
            "invalid_field": {1, 2, 3},
            "header": "malformed"
        }
        with patch.object(svc, "get_tenant_access_token", return_value="t-mock-token-xyz"):
            res = svc.send_interactive_card(card_content=malformed_card, receive_id="ou_mock_id")
            self.assertIsInstance(res, dict)
            self.assertFalse(res.get("success"))
            self.assertIn("is not JSON serializable", res.get("error", ""))

    def test_07_feishu_send_card_unknown_receive_id_type(self):
        """对抗测试 07: 传入未知的 receive_id_type 导致开放平台 HTTP 400 校验拦截
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_07_feishu_send_card_unknown_receive_id_type
        @throws AssertionError
        """
        svc = FeishuService()
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "code": 94999,
            "msg": "invalid receive_id_type"
        }

        with patch.object(svc, "get_tenant_access_token", return_value="t-mock-token-xyz"):
            with patch("httpx.Client.post", return_value=mock_resp):
                res = svc.send_interactive_card(
                    card_content={"elements": []},
                    receive_id="fake_id",
                    receive_id_type="unknown_type_param"
                )
                self.assertIsInstance(res, dict)
                self.assertFalse(res.get("success"))
                self.assertEqual(res.get("status_code"), 400)
                self.assertEqual(res.get("method"), "open_api")

    def test_08_feishu_send_card_webhook_timeout(self):
        """对抗测试 08: 自定义群机器人 Webhook 遭遇连接超时
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_08_feishu_send_card_webhook_timeout
        @throws AssertionError
        """
        svc = FeishuService()
        with patch("httpx.Client.post", side_effect=httpx.ConnectTimeout("Webhook 路由连接超时")):
            res = svc.send_interactive_card(
                card_content={"elements": []},
                webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/mock_hook"
            )
            self.assertIsInstance(res, dict)
            self.assertFalse(res.get("success"))
            self.assertEqual(res.get("method"), "webhook")
            self.assertIn("Webhook 路由连接超时", res.get("error", ""))

    def test_09_feishu_card_builders_null_and_boundary(self):
        """对抗测试 09: 飞书 4 类卡片构造器边界极值与 None 入参安全性
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_09_feishu_card_builders_null_and_boundary
        @throws AssertionError
        """
        # 测试不传 trace_no 的空值场景与极端长文本
        c1 = FeishuService.build_dict_create_card(
            product_code="P-EXTREME-99999",
            product_name="极长耗材名称" * 20,
            spec_model="SPEC-001",
            main_dept_code="DEVICE_DEPT",
            consumable_type="HIGH_VALUE",
            supplier_name="医疗科技供应商",
            reg_cert_no="国械注准20260000000",
            unit_price=999999.99,
            udi_di="06900000000000",
            trace_no=None
        )
        self.assertEqual(c1["header"]["template"], "turquoise")
        self.assertIn("config", c1)
        self.assertIsInstance(c1["elements"], list)

        # 验证调拨单负数/0单价与0数量边界
        c2 = FeishuService.build_dispatch_order_card(
            dist_order_no="DIST-0",
            target_dept_name="急诊科",
            product_name="无菌棉签",
            batch_no="B0",
            expiry_date="2026-01-01",
            dist_qty=0,
            unit_price=0.0,
            dispatcher_name="智能分发系统",
            trace_no=None
        )
        self.assertEqual(c2["header"]["template"], "blue")

    # =========================================================================
    # 二、Coze 服务 (CozeService) 逆向与对抗测试
    # =========================================================================

    def test_10_coze_chat_stream_timeout_fallback(self):
        """对抗测试 10: Coze 流式打字机请求遭遇 ReadTimeout 超时，验证平滑切入离线兜底
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_10_coze_chat_stream_timeout_fallback
        @throws AssertionError
        """
        svc = CozeService()
        with patch("httpx.Client.stream", side_effect=httpx.ReadTimeout("流式读取分包超时")):
            chunks = list(svc.chat_stream(prompt="测试超时兜底", timeout=0.1))
            self.assertGreater(len(chunks), 0)
            final_chunk = chunks[-1]
            self.assertTrue(final_chunk.get("done"))
            self.assertIn("【Coze 小爱智能体离线保护】", final_chunk.get("delta", ""))
            self.assertEqual(final_chunk.get("role"), "assistant")

    def test_11_coze_chat_sync_timeout_fallback(self):
        """对抗测试 11: Coze 同步非流式问答遭遇网络超时，验证返回保底字典与模型标识
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_11_coze_chat_sync_timeout_fallback
        @throws AssertionError
        """
        svc = CozeService()
        with patch("httpx.Client.stream", side_effect=httpx.ConnectTimeout("Coze 握手超时")):
            res = svc.chat(prompt="高值耗材审批流程是什么？", timeout=0.1)
            self.assertIsInstance(res, dict)
            self.assertIn("【Coze 小爱智能体离线保护】", res.get("answer", ""))
            self.assertIn("thought_process", res)
            self.assertEqual(res.get("model_used"), f"coze:{svc.bot_id}")
            self.assertGreaterEqual(res.get("latency_ms", 0), 0)
            self.assertGreater(res.get("tokens", 0), 0)

    def test_12_coze_chat_stream_http_502_bad_gateway(self):
        """对抗测试 12: Coze API 返回 HTTP 502 Bad Gateway 异常状态码
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_12_coze_chat_stream_http_502_bad_gateway
        @throws AssertionError
        """
        svc = CozeService()
        mock_resp = MagicMock()
        mock_resp.status_code = 502

        # 模拟 with client.stream(...) 上下文管理器
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        mock_client.stream.return_value.__exit__.return_value = False

        with patch("httpx.Client", return_value=mock_client):
            chunks = list(svc.chat_stream(prompt="测试502网关异常", timeout=1.0))
            self.assertEqual(len(chunks), 2)
            self.assertIn("【Coze 响应异常 502】", chunks[0].get("delta", ""))
            self.assertFalse(chunks[0].get("done"))
            self.assertTrue(chunks[-1].get("done"))

    def test_13_coze_empty_and_whitespace_prompt(self):
        """对抗测试 13: 传入纯空字符串与纯空白字符提示词
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_13_coze_empty_and_whitespace_prompt
        @throws AssertionError
        """
        svc = CozeService()
        # 验证纯空与纯空格不会导致未捕获异常抛出
        res_empty = svc.chat(prompt="", timeout=5.0)
        self.assertIsInstance(res_empty, dict)
        self.assertIn("answer", res_empty)

        res_space = svc.chat(prompt="    \t\n   ", timeout=5.0)
        self.assertIsInstance(res_space, dict)
        self.assertIn("answer", res_space)

    def test_14_coze_special_characters_and_injections(self):
        """对抗测试 14: 注入恶劣特殊字符集 (SQL注入、XSS、控制符、超长字符串)
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_14_coze_special_characters_and_injections
        @throws AssertionError
        """
        svc = CozeService()
        adversarial_prompts = [
            "'; DROP TABLE spd_product_dict; --",
            "<script>alert('xss')</script><svg onload=alert(1)>",
            "\x00\x01\x02\r\n\t\b\f",
            "测试\u202e反向文字\ufeff零宽空格",
            "A" * 20000  # 2万字符大报文
        ]

        for p in adversarial_prompts:
            # 在离线/在线双模下调用，必须确保不出致命异常
            with patch("httpx.Client.stream", side_effect=httpx.ConnectTimeout("模拟断网")):
                res = svc.chat(prompt=p, timeout=0.1)
                self.assertIsInstance(res, dict)
                self.assertIn("answer", res)
                self.assertGreater(len(res["answer"]), 0)

    def test_15_coze_test_connectivity_structure(self):
        """对抗测试 15: 验证 test_connectivity 结构契约完整性与离线兜底标识
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_15_coze_test_connectivity_structure
        @throws AssertionError
        """
        svc = CozeService()
        with patch.object(svc, "chat", side_effect=Exception("底层通道被强制切断")):
            res = svc.test_connectivity()
            self.assertIsInstance(res, dict)
            self.assertFalse(res.get("connected"))
            self.assertEqual(res.get("bot_id"), svc.bot_id)
            self.assertIn("底层通道被强制切断", res.get("error", ""))

    # =========================================================================
    # 三、LangSmith 与 RealLlmClient 链路降级与鲁棒性测试
    # =========================================================================

    def test_16_langsmith_safe_traceable_when_disabled(self):
        """对抗测试 16: 当 LANGCHAIN_TRACING_V2='false' 时 safe_traceable 必须返回无损直通函数
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_16_langsmith_safe_traceable_when_disabled
        @throws AssertionError
        """
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGCHAIN_API_KEY"] = "lsv2_pt_dummykey_12345"

        @safe_traceable(name="test_func_disabled", run_type="llm")
        def sample_add(a: int, b: int) -> int:
            return a + b

        result = sample_add(10, 20)
        self.assertEqual(result, 30)

    def test_17_langsmith_safe_traceable_when_api_key_unset(self):
        """对抗测试 17: 当 LANGCHAIN_API_KEY 为空或未设置时 safe_traceable 必须优雅降级为 noop
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_17_langsmith_safe_traceable_when_api_key_unset
        @throws AssertionError
        """
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if "LANGCHAIN_API_KEY" in os.environ:
            del os.environ["LANGCHAIN_API_KEY"]

        @safe_traceable(name="test_func_nokey", run_type="chain")
        def sample_echo(msg: str) -> str:
            return f"ECHO:{msg}"

        result = sample_echo("hello_langsmith")
        self.assertEqual(result, "ECHO:hello_langsmith")

    def test_18_real_llm_client_generate_without_langchain_env(self):
        """对抗测试 18: 当完全未配置 LangChain 环境变量时，RealLlmClient.generate 依然能顺畅执行
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_18_real_llm_client_generate_without_langchain_env
        @throws AssertionError
        """
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGCHAIN_API_KEY"] = ""

        # 调用本地模型分支，模拟 Ollama 离线以快速验证全链路兜底
        with patch("httpx.Client.post", side_effect=httpx.ConnectError("Ollama 守护进程未启动")):
            res = RealLlmClient.generate(
                prompt="测试离线指令执行",
                provider="ollama",
                model_name="deepseek-r1:1.5b",
                timeout_seconds=5
            )
            self.assertIsInstance(res, dict)
            self.assertIn("【本地模型离线兜底", res.get("final_answer", ""))
            self.assertIn("本地 Ollama 响应受阻", res.get("thought_process", ""))
            self.assertGreater(res.get("latency_ms", 0), 0)
            self.assertGreater(res.get("total_tokens", 0), 0)

    def test_19_real_llm_client_mimo_timeout_and_http_error(self):
        """对抗测试 19: 云端小米 MiMo 模型遭遇连接超时及 HTTP 500 时平滑兜底
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_19_real_llm_client_mimo_timeout_and_http_error
        @throws AssertionError
        """
        # 1. 模拟网络超时
        with patch("httpx.Client.post", side_effect=httpx.ReadTimeout("MiMo 响应超时")):
            res_timeout = RealLlmClient.generate(
                prompt="请核算心内科耗占比",
                provider="mimo",
                model_name="mimo-v2.6-flash",
                timeout_seconds=5
            )
            self.assertIn("【云端 MiMo 离线保护】", res_timeout.get("final_answer", ""))
            self.assertIn("调用大模型在", res_timeout.get("thought_process", ""))

        # 2. 模拟 HTTP 500 异常状态码
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with patch("httpx.Client.post", return_value=mock_resp):
            res_500 = RealLlmClient.generate(
                prompt="测试 500 状态码",
                provider="mimo",
                model_name="mimo-v2.6-flash",
                timeout_seconds=5
            )
            self.assertIn("【小米 MiMo 返回异常 500】", res_500.get("final_answer", ""))

    def test_20_real_llm_client_generate_stream_adverse(self):
        """对抗测试 20: RealLlmClient.generate_stream 流式管道弱网断开测试
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_20_real_llm_client_generate_stream_adverse
        @throws AssertionError
        """
        with patch("httpx.stream", side_effect=httpx.ConnectTimeout("MiMo 流式长连接握手超时")):
            stream_gen = RealLlmClient.generate_stream(
                prompt="测试流式断开",
                provider="mimo",
                timeout_seconds=5
            )
            chunks = list(stream_gen)
            self.assertGreater(len(chunks), 0)
            # 必须包含兜底 reasoning 或 content
            content_chunks = [c for c in chunks if c.get("type") == "content"]
            self.assertGreater(len(content_chunks), 0)
            self.assertIn("【云端 MiMo 平滑兜底】", content_chunks[0].get("delta", ""))

    # =========================================================================
    # 四、Iteration 2 核心攻防复验：AST 四要素注入证伪与卡片 2.0 双轨同构压测
    # =========================================================================

    def test_21_ast_docstring_mutation_rejects_missing_tags(self):
        """对抗测试 21: AST 注释完整性突变证伪，注入缺失 @route 与 @throws 证实必定拦截
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_21_ast_docstring_mutation_rejects_missing_tags
        @throws AssertionError
        """
        import io
        from tests.test_mcp_and_core_services_worker_m1 import TestMcpAndCoreServices

        test_worker_instance = TestMcpAndCoreServices()

        # 1. 突变注入 1：缺失 @route 注释标签
        dummy_missing_route = (
            "\n"
            "def dummy_adversarial_func_no_route(x: int) -> int:\n"
            '    """测试缺少 route 标签\n'
            "    @param x: int 测试参数\n"
            "    @returns int 测试返回值\n"
            "    @throws ValueError 测试异常\n"
            '    """\n'
            "    return x + 1\n"
        )

        orig_open = open

        def mock_open_missing_route(filepath, *args, **kwargs):
            f = orig_open(filepath, *args, **kwargs)
            if "schema.py" in str(filepath):
                content = f.read() + dummy_missing_route
                return io.StringIO(content)
            return f

        with patch("builtins.open", side_effect=mock_open_missing_route):
            with self.assertRaises(AssertionError) as ctx_route:
                test_worker_instance.test_11_zero_emoji_and_docstrings_check()
            err_text_route = str(ctx_route.exception)
            self.assertIn("dummy_adversarial_func_no_route", err_text_route)
            self.assertIn("@route", err_text_route)

        # 2. 突变注入 2：缺失 @throws 注释标签
        dummy_missing_throws = (
            "\n"
            "def dummy_adversarial_func_no_throws(y: str) -> str:\n"
            '    """测试缺少 throws 标签\n'
            "    @param y: str 测试入参\n"
            "    @returns str 测试返回值\n"
            "    @route internal://services/dummy_no_throws\n"
            '    """\n'
            "    return y.strip()\n"
        )

        def mock_open_missing_throws(filepath, *args, **kwargs):
            f = orig_open(filepath, *args, **kwargs)
            if "schema.py" in str(filepath):
                content = f.read() + dummy_missing_throws
                return io.StringIO(content)
            return f

        with patch("builtins.open", side_effect=mock_open_missing_throws):
            with self.assertRaises(AssertionError) as ctx_throws:
                test_worker_instance.test_11_zero_emoji_and_docstrings_check()
            err_text_throws = str(ctx_throws.exception)
            self.assertIn("dummy_adversarial_func_no_throws", err_text_throws)
            self.assertIn("@throws", err_text_throws)

        # 3. 突变注入 3：完全缺失 docstring
        dummy_missing_doc = (
            "\n"
            "def dummy_adversarial_completely_undocumented():\n"
            "    return 42\n"
        )

        def mock_open_no_doc(filepath, *args, **kwargs):
            f = orig_open(filepath, *args, **kwargs)
            if "schema.py" in str(filepath):
                content = f.read() + dummy_missing_doc
                return io.StringIO(content)
            return f

        with patch("builtins.open", side_effect=mock_open_no_doc):
            with self.assertRaises(AssertionError) as ctx_doc:
                test_worker_instance.test_11_zero_emoji_and_docstrings_check()
            err_text_doc = str(ctx_doc.exception)
            self.assertIn("dummy_adversarial_completely_undocumented", err_text_doc)
            self.assertIn("完全缺失 docstring", err_text_doc)

    def test_22_feishu_card_2_0_backward_forward_dual_schema_equivalence(self):
        """对抗测试 22: 飞书 Card 2.0 深度双轨验证，断言 body.elements 与顶层 elements 双向访问且完全同构
        @param 无
        @returns 无
        @route tests/test_challenger_m1_adversarial.py/test_22_feishu_card_2_0_backward_forward_dual_schema_equivalence
        @throws AssertionError
        """
        cards = [
            (
                "build_dict_create_card",
                FeishuService.build_dict_create_card(
                    product_code="HC-TEST-999",
                    product_name="人工心脏起搏器",
                    spec_model="Dual-Chamber",
                    main_dept_code="CONSUMABLE_DEPT",
                    consumable_type="HIGH_VALUE",
                    supplier_name="美敦力医疗",
                    reg_cert_no="国械注进20233120101",
                    unit_price=35000.0,
                    udi_di="00643169001122",
                    trace_no="TR-TEST-999"
                )
            ),
            (
                "build_dispatch_order_card",
                FeishuService.build_dispatch_order_card(
                    dist_order_no="DO-TEST-999",
                    target_dept_name="重症监护室ICU",
                    product_name="中心静脉穿刺导管包",
                    batch_no="B20261105",
                    expiry_date="2027-11-04",
                    dist_qty=50,
                    unit_price=280.0,
                    dispatcher_name="耗材科保管员",
                    trace_no="TR-TEST-998"
                )
            ),
            (
                "build_approval_suspend_card",
                FeishuService.build_approval_suspend_card(
                    req_order_no="REQ-TEST-999",
                    apply_dept_name="心血管外科",
                    applicant_name="李主任医师",
                    product_name="主动脉覆膜支架",
                    spec_model="Valiant-Captivia",
                    apply_qty=1,
                    total_amount=68000.0,
                    suspend_reason="超大额高值耗材审批触发 HITL",
                    trace_no="TR-TEST-997"
                )
            ),
            (
                "build_udi_freeze_card",
                FeishuService.build_udi_freeze_card(
                    batch_no="B20260901-ALERT",
                    udi_code="(01)00643169001122(17)271104(10)B20260901-ALERT(21)SN100200",
                    product_name="人工心脏起搏器",
                    manufacturer="美敦力",
                    freeze_reason="电极接头接触不良不良事件一级召回",
                    operator_name="质量风控处",
                    trace_no="TR-TEST-996"
                )
            )
        ]

        for card_name, card in cards:
            # 1. 检验 Card 2.0 顶层 schema 标识
            self.assertEqual(card.get("schema"), "2.0", f"{card_name} 必须包含 schema: 2.0")

            # 2. 检验 2.0 规范的 body 容器属性
            self.assertIn("body", card, f"{card_name} 必须包含 body 容器")
            self.assertIsInstance(card["body"], dict, f"{card_name} body 必须为字典类型")
            self.assertEqual(card["body"].get("direction"), "vertical", f"{card_name} body.direction 必须为 vertical")
            self.assertIn("elements", card["body"], f"{card_name} body 必须包含 elements 列表")

            # 3. 检验向下兼容的顶层 elements 属性
            self.assertIn("elements", card, f"{card_name} 顶层必须包含 elements 列表以维持向下兼容")

            # 4. 核心同构断言：body['elements'] 与顶层 elements 完全一致
            body_elements = card["body"]["elements"]
            top_elements = card["elements"]
            self.assertEqual(
                body_elements, top_elements,
                f"{card_name} 的 body.elements 与顶层 elements 内容不一致"
            )

            # 5. 检验 elements 列表非空且包含交互元素
            self.assertGreater(len(body_elements), 0, f"{card_name} elements 不得为空")

            # 6. 检验 JSON 序列化反序列化一致性
            serialized = json.dumps(card, ensure_ascii=False)
            deserialized = json.loads(serialized)
            self.assertEqual(
                deserialized["body"]["elements"],
                deserialized["elements"],
                f"{card_name} 序列化后双轨 elements 必须依然同构"
            )


if __name__ == "__main__":
    unittest.main()
