"""
@file test_coze_adversarial_challenge.py
@description 对抗性质询测试套件: 针对 Coze 服务的 Emoji 清洗器与流式终止状态实施压力对抗
重点覆盖:
1. 恶劣 dirty emoji (多字节emoji、肤色调节符、星光闪烁、医疗类表情、符号及组合序列) 过滤与保留测试;
2. 异常中断与非200状态下的流式终止标识 (done: True) 履约校验;
3. 确保零 Emoji 污染与函数级四要素注释规范。

@param 无 独立单元测试
@returns unittest 运行断言结果
@route tests/test_coze_adversarial_challenge.py
@throws AssertionError 断言失败时抛出
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.coze_service import _clean_emoji, CozeService


class TestCozeAdversarialChallenge(unittest.TestCase):
    """Coze 服务对抗性质询测试集"""

    def setUp(self):
        """测试前置初始化
        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/setUp
        @throws 无
        """
        self.svc = CozeService()

    # ----------------------------------------------------------------------
    # 质询维度 1: Emoji 清洗器对抗压测 (Emoji Sanitizer Stress Test)
    # ----------------------------------------------------------------------

    def test_01_emoji_sanitizer_preserves_medical_chinese_english_numbers(self):
        """压测 01: 校验中英数及医疗专业术语在清洗后 100% 完整保留
        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_01_emoji_sanitizer_preserves_medical_chinese_english_numbers
        @throws AssertionError
        """
        raw_text = (
            "无菌注射器 20ml (批号: 20261105-A) 规格合格, "
            "冠状动脉支架 (Cobalt-Chromium Stent, 3.0x18mm) 数量: 500支, "
            "单价: 12500.00元, FEFO效期: 2028-12-31, 院内调拨编码: DIST-2026-X01."
        )
        cleaned = _clean_emoji(raw_text)
        self.assertEqual(cleaned, raw_text, "纯中英数医疗文本被意外篡改")

    def test_02_emoji_sanitizer_strips_smp_and_dingbats(self):
        """压测 02: 校验标准 SMP 平面与 Dingbats 常用 Emoji 能被正确剔除
        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_02_emoji_sanitizer_strips_smp_and_dingbats
        @throws AssertionError
        """
        # 测试SMP平面医疗表情与闪烁字符
        # \U0001f3e5 医院, \U0001f489 注射器, \U0001f48a 药丸, \u2728 闪烁星光, \U0001f44d 点赞
        dirty_text = "\u2728 耗材入库审查合格 \U0001f3e5 批号核验无误 \U0001f489 \U0001f48a \U0001f44d"
        cleaned = _clean_emoji(dirty_text)

        self.assertNotIn("\u2728", cleaned)
        self.assertNotIn("\U0001f3e5", cleaned)
        self.assertNotIn("\U0001f489", cleaned)
        self.assertNotIn("\U0001f48a", cleaned)
        self.assertNotIn("\U0001f44d", cleaned)
        self.assertIn("耗材入库审查合格", cleaned)
        self.assertIn("批号核验无误", cleaned)

    def test_03_emoji_sanitizer_leaks_zwj_and_variation_selectors(self):
        """压测 03: 校验复合 Emoji 序列中的 ZWJ (\\u200d) 与变体选择符 (\\ufe0f) 已被彻底剥离
        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_03_emoji_sanitizer_leaks_zwj_and_variation_selectors
        @throws AssertionError
        """
        # 复合 Emoji: 医生 (\U0001f468\u200d\u2695\ufe0f) 以及带变体符的符号: 警示 (\u26a0\ufe0f), 医疗杖 (\u2695\ufe0f)
        doctor_composite = "主治医师 \U0001f468\u200d\u2695\ufe0f 已双人复核"
        cleaned_doctor = _clean_emoji(doctor_composite)

        # 检查是否遗留了不可见的零宽连接符 ZWJ (U+200D) 或变体选择符 (U+FE0F)
        has_zwj = "\u200d" in cleaned_doctor
        has_fe0f = "\ufe0f" in cleaned_doctor

        # 验证修复效果: 已彻底移除 ZWJ 与变体选择符
        self.assertFalse(
            has_zwj,
            "修复验证: _clean_emoji 已彻底剥离 ZWJ (\\u200d)"
        )
        self.assertFalse(
            has_fe0f,
            "修复验证: _clean_emoji 已彻底剥离变体选择符 (\\ufe0f)"
        )

    def test_04_emoji_sanitizer_leaks_star_and_miscellaneous_symbols(self):
        """压测 04: 校验符号字符如五角星 (\\u2b50) 等杂项符号已成功过滤
        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_04_emoji_sanitizer_leaks_star_and_miscellaneous_symbols
        @throws AssertionError
        """
        star_text = "医疗物资评级: \u2b50\u2b50\u2b50\u2b50\u2b50 五星特优"
        cleaned_star = _clean_emoji(star_text)

        # 验证修复效果: U+2B50 杂项符号已被清洗
        has_star = "\u2b50" in cleaned_star
        self.assertFalse(
            has_star,
            "修复验证: _clean_emoji 已成功过滤 U+2B50 (五角星符号)"
        )

    # ----------------------------------------------------------------------
    # 质询维度 2: Coze 流式终止状态对抗压测 (Stream Termination & Hanging)
    # ----------------------------------------------------------------------

    def test_05_chat_stream_chat_failed_event_yields_done_true(self):
        """压测 05: conversation.chat.failed 事件下必须正常推送 done: True 终结包
        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_05_chat_stream_chat_failed_event_yields_done_true
        @throws AssertionError
        """
        failed_payload = json.dumps({
            "last_error": {"code": 7001, "msg": "API rate limit reached"},
            "conversation_id": "conv-fail-001"
        })
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            "event: conversation.chat.failed",
            f"data: {failed_payload}"
        ]

        with patch("httpx.Client.stream") as mock_stream:
            mock_stream.return_value.__enter__.return_value = mock_resp
            chunks = list(self.svc.chat_stream(prompt="请求高频测试"))
            done_flags = [c.get("done") for c in chunks]
            self.assertIn(True, done_flags, "chat.failed 必须推送至少一个 done: True 终结包")
            self.assertEqual(chunks[-1].get("done"), True, "最后一个分包必须为 done: True")

    def test_06_chat_stream_non_200_fails_to_yield_done_true_bug(self):
        """压测 06: 校验 HTTP 非 200 状态下 chat_stream 正常推送 done: True 闭环终结包
        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_06_chat_stream_non_200_fails_to_yield_done_true_bug
        @throws AssertionError
        """
        for code in [500, 502, 401, 403, 404]:
            mock_resp = MagicMock()
            mock_resp.status_code = code

            with patch("httpx.Client.stream") as mock_stream:
                mock_stream.return_value.__enter__.return_value = mock_resp
                chunks = list(self.svc.chat_stream(prompt="测试非200状态中断"))

                # 验证修复效果: 必须包含 content 包和 completed 终结包，终结包携带 done: True
                has_done_true = any(c.get("done") is True for c in chunks)
                self.assertTrue(
                    has_done_true,
                    f"修复验证: 在 HTTP {code} 异常时，chat_stream 成功推送 done: True 终结包"
                )
                self.assertEqual(len(chunks), 2)
                self.assertEqual(chunks[0].get("done"), False)
                self.assertEqual(chunks[-1].get("done"), True)

    def test_07_chat_stream_http_status_codes_exhaustive(self):
        """压测 07: 校验 HTTP 500/502/504/401/403/429 等全量异常状态码下 chat_stream 100% 推送 done: True 终结包

        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_07_chat_stream_http_status_codes_exhaustive
        @throws AssertionError
        """
        for code in [500, 502, 504, 401, 403, 429]:
            mock_resp = MagicMock()
            mock_resp.status_code = code

            with patch("httpx.Client.stream") as mock_stream:
                mock_stream.return_value.__enter__.return_value = mock_resp
                chunks = list(self.svc.chat_stream(prompt=f"测试 HTTP {code} 状态码", timeout=1.0))
                self.assertEqual(len(chunks), 2, f"HTTP {code} 预期返回 2 个分包")
                self.assertFalse(chunks[0].get("done"), f"HTTP {code} 分包 0 必须为 done: False")
                self.assertTrue(chunks[-1].get("done"), f"HTTP {code} 终结包必须为 done: True")
                self.assertEqual(chunks[-1].get("type"), "completed")
                self.assertIn(f"【Coze 响应异常 {code}】", chunks[0].get("delta", ""))

    def test_08_chat_stream_mid_stream_network_exception_yields_done_true(self):
        """压测 08: 校验流式中途网络截断 (RemoteProtocolError) 时通过重试与离线兜底保证最终包 done: True

        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_08_chat_stream_mid_stream_network_exception_yields_done_true
        @throws AssertionError
        """
        import httpx

        def truncated_stream():
            """模拟中途抛出网络异常的生成器
            @param 无
            @returns Generator 抛出异常的模拟数据流
            @route tests/test_coze_adversarial_challenge.py/test_08/truncated_stream
            @throws RemoteProtocolError
            """
            yield "event: conversation.message.delta"
            yield 'data: {"type": "answer", "content": "部分分包正文"}'
            raise httpx.RemoteProtocolError("中途网络强行中断")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.side_effect = truncated_stream

        with patch("httpx.Client.stream") as mock_stream:
            mock_stream.return_value.__enter__.return_value = mock_resp
            chunks = list(self.svc.chat_stream(prompt="测试流式中途网络截断", timeout=0.5))
            self.assertGreaterEqual(len(chunks), 2, "中途截断后重试与离线兜底必须产出分包")
            self.assertTrue(chunks[-1].get("done"), "中途网络截断后最终分包必须为 done: True")
            self.assertIn("【Coze 小爱智能体离线保护】", chunks[-1].get("delta", ""))

    def test_09_chat_stream_downstream_consumer_non_blocking_and_deadlock_free(self):
        """压测 09: 验证下游多线程消费者在各种网络异常注入下绝不发生死锁或无响应挂起

        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_09_chat_stream_downstream_consumer_non_blocking_and_deadlock_free
        @throws AssertionError
        """
        import concurrent.futures
        import httpx

        def consume(timeout_val: float):
            """模拟下游消费者拉取生成器
            @param timeout_val: float 超时时间
            @returns list 消费的所有分包
            @route tests/test_coze_adversarial_challenge.py/test_09/consume
            @throws 无
            """
            result = []
            for chunk in self.svc.chat_stream(prompt="下游死锁验证", timeout=timeout_val):
                result.append(chunk)
                if chunk.get("done"):
                    break
            return result

        with patch("httpx.Client.stream", side_effect=httpx.ReadTimeout("强制读取超时")):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future = executor.submit(consume, 0.5)
                # 必须在 3.0s 内正常终结返回，绝不死锁或挂起
                chunks = future.result(timeout=3.0)
                self.assertGreaterEqual(len(chunks), 1)
                self.assertTrue(chunks[-1].get("done"))

    def test_10_chat_stream_empty_body_fails_to_yield_done_true_bug(self):
        """压测 10: 验证 HTTP 200 空 Body 异常场景下，chat_stream 正常推送兜底包含 done: True 的终结包

        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_10_chat_stream_empty_body_fails_to_yield_done_true_bug
        @throws AssertionError
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = []

        with patch("httpx.Client.stream") as mock_stream:
            mock_stream.return_value.__enter__.return_value = mock_resp
            chunks = list(self.svc.chat_stream(prompt="测试空body"))
            # 验证修复效果: 空 body 场景下兜底推送包含 done: True 的 completed 终结包
            has_done_true = any(c.get("done") is True for c in chunks)
            self.assertTrue(
                has_done_true,
                "修复验证: 空 body 场景下成功推送包含 done: True 的终结包"
            )
            self.assertEqual(len(chunks), 1)
            self.assertTrue(chunks[-1].get("done"))
            self.assertEqual(chunks[-1].get("type"), "completed")

    def test_11_chat_stream_done_marker_without_completed_event_bug(self):
        """压测 11: 验证流式传输仅收到 data: [DONE] 而未收到 conversation.chat.completed 时正常推送 done: True 终结包

        @param 无
        @returns 无
        @route tests/test_coze_adversarial_challenge.py/test_11_chat_stream_done_marker_without_completed_event_bug
        @throws AssertionError
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            "event: conversation.message.delta",
            'data: {"type": "answer", "content": "流式增量正文"}',
            "data: [DONE]"
        ]

        with patch("httpx.Client.stream") as mock_stream:
            mock_stream.return_value.__enter__.return_value = mock_resp
            chunks = list(self.svc.chat_stream(prompt="测试 [DONE] 提前截断"))
            # 验证修复效果: 仅有 [DONE] 标记而缺失 chat.completed 事件时，退出前兜底补发包含 done: True 的终结包
            has_done_true = any(c.get("done") is True for c in chunks)
            self.assertTrue(
                has_done_true,
                "修复验证: 仅有 [DONE] 标记而缺失 chat.completed 事件时，成功推送 done: True 终结包"
            )
            self.assertEqual(len(chunks), 2)
            self.assertFalse(chunks[0].get("done"))
            self.assertTrue(chunks[-1].get("done"))
            self.assertEqual(chunks[-1].get("type"), "completed")


if __name__ == "__main__":
    unittest.main()
