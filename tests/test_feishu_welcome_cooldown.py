"""
=============================================================================
测试用例: 飞书单聊欢迎卡片频控与全局开关逻辑自动化测试
对应需求: 用户进入飞书单聊时，每天仅弹窗一次卡片或根据配置冷却时间防打扰
=============================================================================
"""

import time
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# 将 backend 路径加入 sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from types import SimpleNamespace
from app.services.feishu_ws_service import FeishuWebSocketService


class TestFeishuWelcomeCooldown(unittest.TestCase):
    """
    飞书欢迎卡片频控防打扰与全局开关测试用例
    """

    def setUp(self):
        self.service = FeishuWebSocketService()
        # 清空频控缓存字典
        self.service._user_welcome_timestamp = {}

    def _create_mock_event(self, open_id: str, chat_id: str):
        event_obj = SimpleNamespace(
            chat_id=chat_id,
            operator_id=SimpleNamespace(open_id=open_id)
        )
        return SimpleNamespace(event=event_obj)

    def test_first_visit_should_send_card(self):
        """
        测试用户首次进入单聊：应正常发送欢迎卡片并更新时间戳
        """
        user_open_id = "ou_test_user_001"
        chat_id = "oc_test_chat_001"

        with patch('app.services.feishu_ws_service.feishu_service.send_interactive_card') as mock_send, \
             patch('app.core.database.SessionLocal') as mock_session_cls:
            
            # 模拟数据库配置：开关开启(1)，冷却时间24小时
            mock_db = MagicMock()
            mock_config = MagicMock()
            mock_config.enable_feishu_welcome_card = 1
            mock_config.feishu_welcome_cooldown_hours = 24.0
            mock_db.query.return_value.filter.return_value.first.return_value = mock_config
            mock_session_cls.return_value.__enter__.return_value = mock_db

            data = self._create_mock_event(user_open_id, chat_id)
            self.service._on_chat_entered(data)

            # 断言：首次必须触发卡片发送
            self.assertTrue(mock_send.called)
            # 断言：已记录时间戳
            self.assertIn(user_open_id, self.service._user_welcome_timestamp)

    def test_cooldown_within_period_should_block(self):
        """
        测试用户在冷却期内重复进入单聊：必须拦截，严禁重复推送卡片
        """
        user_open_id = "ou_test_user_002"
        chat_id = "oc_test_chat_002"

        # 模拟 10 秒前已发送过
        self.service._user_welcome_timestamp[user_open_id] = time.time() - 10

        with patch('app.services.feishu_ws_service.feishu_service.send_interactive_card') as mock_send, \
             patch('app.core.database.SessionLocal') as mock_session_cls:
            
            mock_db = MagicMock()
            mock_config = MagicMock()
            mock_config.enable_feishu_welcome_card = 1
            mock_config.feishu_welcome_cooldown_hours = 24.0  # 24小时冷却
            mock_db.query.return_value.filter.return_value.first.return_value = mock_config
            mock_session_cls.return_value.__enter__.return_value = mock_db

            data = self._create_mock_event(user_open_id, chat_id)
            self.service._on_chat_entered(data)

            # 断言：处于 24h 冷却期内，mock_send 不应被调用
            mock_send.assert_not_called()

    def test_switch_disabled_should_block_completely(self):
        """
        测试全局开关关闭 (enable_feishu_welcome_card = 0)：即使首访也严禁发送
        """
        user_open_id = "ou_test_user_003"
        chat_id = "oc_test_chat_003"

        with patch('app.services.feishu_ws_service.feishu_service.send_interactive_card') as mock_send, \
             patch('app.core.database.SessionLocal') as mock_session_cls:
            
            mock_db = MagicMock()
            mock_config = MagicMock()
            mock_config.enable_feishu_welcome_card = 0  # 开关已关闭
            mock_config.feishu_welcome_cooldown_hours = 24.0
            mock_db.query.return_value.filter.return_value.first.return_value = mock_config
            mock_session_cls.return_value.__enter__.return_value = mock_db

            data = self._create_mock_event(user_open_id, chat_id)
            self.service._on_chat_entered(data)

            # 断言：开关关闭时不触发发送
            mock_send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
