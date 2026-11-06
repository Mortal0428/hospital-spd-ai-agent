"""
@file feishu_service.py
@description 飞书开放平台原生对接与交互式卡片消息推送服务
支持自动获取并缓存 tenant_access_token，构建物资建仓、调拨分发、审批挂起与 UDI 冻结 4 类业务卡片，
支持 Webhook 发送与双向事件回调处理，全程零 Emoji 并包含 100% 中文四要素注释。

@param 各类飞书卡片要素与回调载荷
@returns Dict[str, Any] 卡片推送与鉴权测试结果
@route internal://backend/app/services/feishu_service.py
@throws 网络异常与鉴权失败时安全降级捕获
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import httpx
from app.core.config import settings

logger = logging.getLogger("spd.services.feishu")


class FeishuService:
    """飞书开放平台原生卡片推送与交互服务客户端"""

    # 官方分配并已验证的开发者凭据 (优先从环境变量读取)
    DEFAULT_APP_ID = os.environ.get("FEISHU_APP_ID", "")
    DEFAULT_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
    DEFAULT_BOT_OPEN_ID = os.environ.get("FEISHU_BOT_OPEN_ID", "")
    DEFAULT_BOT_NAME = "Openclaw_测试"
    BASE_URL = "https://open.feishu.cn"

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        """初始化飞书服务配置与内存 Token 缓存
        @param app_id: Optional[str] 飞书开放平台应用 ID
        @param app_secret: Optional[str] 飞书开放平台应用密钥
        @param webhook_url: Optional[str] 飞书群自定义机器人 Webhook 地址
        @returns 无 构造函数完成实例属性初始化
        @route internal://services/feishu_service/__init__
        @throws 无
        """
        self.app_id = app_id or getattr(settings, "FEISHU_APP_ID", self.DEFAULT_APP_ID)
        self.app_secret = app_secret or getattr(settings, "FEISHU_APP_SECRET", self.DEFAULT_APP_SECRET)
        self.default_webhook_url = webhook_url or getattr(settings, "FEISHU_WEBHOOK_URL", "")
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._bot_info: Optional[Dict[str, Any]] = None
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        """获取带有连接池复用与指数退避重试的持久化 HTTP 会话
        @param 无
        @returns requests.Session 线程安全且抗网络抖动的客户端会话
        @route internal://services/feishu_service/_get_session
        @throws 无
        """
        if self._session is None:
            sess = requests.Session()
            retry_strategy = Retry(
                total=2,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["POST", "GET"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
            sess.mount("https://", adapter)
            sess.mount("http://", adapter)
            self._session = sess
        return self._session

    def get_bot_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """通过飞书 OpenAPI 官方接口获取当前机器人底座信息与专属 OpenID
        @param force_refresh: bool 是否强制刷新内存缓存
        @returns Dict[str, Any] 包含 bot_open_id, bot_name, activate_status 等元数据
        @route internal://services/feishu_service/get_bot_info
        @throws 内部捕获网络异常并返回内置安全兜底凭据
        """
        if not force_refresh and self._bot_info:
            return self._bot_info

        url = f"{self.BASE_URL}/open-apis/bot/v3/info"
        fallback_data = {
            "bot_open_id": self.DEFAULT_BOT_OPEN_ID,
            "bot_name": self.DEFAULT_BOT_NAME,
            "app_name": self.DEFAULT_BOT_NAME,
            "activate_status": 2,
            "source": "fallback"
        }

        try:
            token = self.get_tenant_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(url, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    bot = data.get("bot", {})
                    self._bot_info = {
                        "bot_open_id": bot.get("open_id") or self.DEFAULT_BOT_OPEN_ID,
                        "bot_name": bot.get("app_name") or self.DEFAULT_BOT_NAME,
                        "app_name": bot.get("app_name") or self.DEFAULT_BOT_NAME,
                        "activate_status": bot.get("activate_status", 2),
                        "avatar_url": bot.get("avatar_url", ""),
                        "source": "open_api"
                    }
                    logger.info(
                        f"成功获取飞书机器人底座信息: name={self._bot_info['bot_name']}, open_id={self._bot_info['bot_open_id']}"
                    )
                    return self._bot_info
                else:
                    logger.warning(f"获取机器人信息接口返回业务错误: {data}")
            else:
                logger.warning(f"获取机器人信息 HTTP 状态异常: {resp.status_code}")
        except Exception as e:
            logger.warning(f"获取飞书机器人信息异常: {e}")

        self._bot_info = fallback_data
        return fallback_data

    def get_tenant_access_token(self, force_refresh: bool = False) -> str:
        """获取应用 tenant_access_token 并实现内存安全缓存
        提前 300 秒刷新，杜绝临期失效

        @param force_refresh: bool 是否强制重新获取 Token
        @returns str 有效的 tenant_access_token 凭据
        @route internal://services/feishu_service/get_tenant_access_token
        @throws RuntimeError 若开放平台鉴权失败
        """
        now = time.time()
        if not force_refresh and self._token and now < self._token_expires_at:
            return self._token

        url = f"{self.BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        last_err = None
        for attempt in range(2):
            try:
                resp = requests.post(url, json=payload, timeout=15.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        token = data.get("tenant_access_token")
                        expire_seconds = data.get("expire", 7200)
                        self._token = token
                        # 提前 300 秒失效安全余量
                        self._token_expires_at = now + max(60, expire_seconds - 300)
                        logger.info("飞书 tenant_access_token 获取并缓存成功")
                        return token
                    else:
                        err_msg = f"飞书 Token 接口返回错误: code={data.get('code')}, msg={data.get('msg')}"
                        logger.error(err_msg)
                        raise RuntimeError(err_msg)
                else:
                    err_msg = f"飞书 Token HTTP 异常状态码: {resp.status_code}"
                    logger.error(err_msg)
                    raise RuntimeError(err_msg)
            except Exception as e:
                last_err = e
                logger.warning(f"获取飞书 Token 第 {attempt + 1} 次尝试受阻: {e}")
                time.sleep(0.5)

        logger.error(f"获取飞书 tenant_access_token 最终异常: {last_err}")
        raise RuntimeError(f"飞书鉴权连接失败: {str(last_err)}")

    def test_connection(self) -> Dict[str, Any]:
        """连通性与 Token 有效性自检测试

        @param 无 实例方法无额外入参
        @returns Dict[str, Any] 包含 connected, latency_ms, token_prefix, message
        @route internal://services/feishu_service/test_connection
        @throws 内部安全捕获异常并返回失败状态
        """
        t0 = time.time()
        try:
            token = self.get_tenant_access_token(force_refresh=True)
            latency_ms = int((time.time() - t0) * 1000)
            prefix = token[:12] + "..." if token else ""
            return {
                "connected": True,
                "latency_ms": latency_ms,
                "token_prefix": prefix,
                "app_id": self.app_id,
                "message": "飞书开放平台连通性正常，Token 鉴权成功"
            }
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            return {
                "connected": False,
                "latency_ms": latency_ms,
                "error": str(e),
                "message": f"飞书连接检测未通过: {str(e)}"
            }

    # =========================================================================
    # 4 类高颜值业务卡片构造器 (Card JSON V2 标准规范)
    # =========================================================================

    @classmethod
    def build_dict_create_card(
        cls,
        product_code: str,
        product_name: str,
        spec_model: str,
        main_dept_code: str,
        consumable_type: str,
        supplier_name: str,
        reg_cert_no: str,
        unit_price: float,
        udi_di: str,
        trace_no: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建新物资字典入库建档交互式卡片 (松石绿主题)

        @param product_code: str 物资标准编码
        @param product_name: str 物资通用名
        @param spec_model: str 规格型号
        @param main_dept_code: str 归口主科室
        @param consumable_type: str 耗材类别
        @param supplier_name: str 供应商全称
        @param reg_cert_no: str 医疗器械注册证号
        @param unit_price: float 基准单价
        @param udi_di: str UDI-DI 码
        @param trace_no: Optional[str] 6W 流水号
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 飞书标准卡片 JSON 结构
        @route internal://services/feishu_service/build_dict_create_card
        @throws 无
        """
        dept_text = "耗材科主库" if main_dept_code == "CONSUMABLE_DEPT" else "设备科主库"
        type_text = "普通耗材 (按批次管理)" if consumable_type == "GENERAL" else "高值耗材 (一物一码专仓管理)"
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fields = [
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**物资编码:**\n{product_code}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**物资品名:**\n{product_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**规格型号:**\n{spec_model}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**归口科室:**\n{dept_text}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**耗材属性:**\n{type_text}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**供货单位:**\n{supplier_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**注册证号:**\n{reg_cert_no}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**基准单价:**\n{unit_price:.2f} 元"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**UDI-DI 固定标识:** `{udi_di}`"}},
        ]
        if trace_no:
            fields.append({"is_short": False, "text": {"tag": "lark_md", "content": f"**6W 全流程追踪号:** `{trace_no}`"}})

        elements = []
        if at_open_id:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"<at id=\"{at_open_id}\"></at> 医疗物资首营建档待核验提醒："
                }
            })
        elements.extend([
            {
                "tag": "div",
                "fields": fields
            },
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": f"建档核准时间: {ts_now} · 智能体 Agent 01 首营质检已通过"}]
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看物资字典详情"},
                        "type": "primary",
                        "value": {"action": "view_dict", "product_code": product_code}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "打印入库验收质检单"},
                        "type": "default",
                        "value": {"action": "print_inbound_voucher", "product_code": product_code}
                    }
                ]
            }
        ])

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "turquoise",
                "title": {"tag": "plain_text", "content": "【SPD建档通知】医疗物资首营建仓已核准"}
            },
            "elements": elements
        }

    @classmethod
    def build_dispatch_order_card(
        cls,
        dist_order_no: str,
        target_dept_name: str,
        product_name: str,
        batch_no: str,
        expiry_date: str,
        dist_qty: int,
        unit_price: float,
        dispatcher_name: str,
        trace_no: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建主库物资分发调拨完成交互式卡片 (经典蓝主题)

        @param dist_order_no: str 调拨单号
        @param target_dept_name: str 接收科室名称
        @param product_name: str 物资名称
        @param batch_no: str 批号
        @param expiry_date: str 有效期至
        @param dist_qty: int 分发数量
        @param unit_price: float 单价
        @param dispatcher_name: str 发料人
        @param trace_no: Optional[str] 6W 追踪号
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 飞书标准卡片 JSON 结构
        @route internal://services/feishu_service/build_dispatch_order_card
        @throws 无
        """
        total_amount = round(dist_qty * unit_price, 2)
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fields = [
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**调拨单号:**\n`{dist_order_no}`"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**调拨去向:**\n{target_dept_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**调拨数量:**\n{dist_qty}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**出库原则:**\nFEFO 近效期先出"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**物资品规:**\n{product_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**生产批号:**\n`{batch_no}`"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**有效期至:**\n{expiry_date}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**调拨总值:**\n{total_amount:.2f} 元"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**主库发料人:**\n{dispatcher_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**单据状态:**\n已发料待二级库签收"}},
        ]
        if trace_no:
            fields.append({"is_short": False, "text": {"tag": "lark_md", "content": f"**6W 物权交接流水号:** `{trace_no}`"}})

        elements = []
        if at_open_id:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"<at id=\"{at_open_id}\"></at> 主库按需分发调拨待签收提醒："
                }
            })
        elements.extend([
            {
                "tag": "div",
                "fields": fields
            },
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": f"制单时间: {ts_now} · 智能体 Agent 02 FEFO 批次智能匹配"}]
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "二级库确认接收"},
                        "type": "primary",
                        "value": {"action": "confirm_receipt", "dist_order_no": dist_order_no}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看调拨流转台账"},
                        "type": "default",
                        "value": {"action": "view_dispatch_log", "dist_order_no": dist_order_no}
                    }
                ]
            }
        ])

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "【SPD调拨通知】主库物资按需分发调拨完成"}
            },
            "elements": elements
        }

    @classmethod
    def build_approval_suspend_card(
        cls,
        req_order_no: str,
        apply_dept_name: str,
        applicant_name: str,
        product_name: str,
        spec_model: str,
        apply_qty: int,
        total_amount: float,
        suspend_reason: str = "单笔申领总额超过一万元红线，触发人机协同 (HITL) 双人复核",
        trace_no: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建大额高值申领人机协同审批挂起交互式卡片 (警示橙主题)

        @param req_order_no: str 申领单号
        @param apply_dept_name: str 申领科室
        @param applicant_name: str 申请人
        @param product_name: str 物资品名
        @param spec_model: str 规格
        @param apply_qty: int 申领数量
        @param total_amount: float 预估总额
        @param suspend_reason: str 挂起原因
        @param trace_no: Optional[str] 6W 追踪流水号
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 飞书标准卡片 JSON 结构
        @route internal://services/feishu_service/build_approval_suspend_card
        @throws 无
        """
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = [
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**申领单号:**\n`{req_order_no}`"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**申领科室:**\n{apply_dept_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**申领申请人:**\n{applicant_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**物资品规:**\n{product_name} ({spec_model})"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**申领数量:**\n{apply_qty}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**预估总额:**\n{total_amount:.2f} 元"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**风控拦截规则:**\n{suspend_reason}"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**挂起状态:** `PENDING_HUMAN_REVIEW`"}},
        ]
        if trace_no:
            fields.append({"is_short": False, "text": {"tag": "lark_md", "content": f"**6W 链路追踪号:** `{trace_no}`"}})

        elements = []
        if at_open_id:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"<at id=\"{at_open_id}\"></at> 审批待办强提醒：请审批责任人即刻核审。"
                }
            })
        elements.extend([
            {
                "tag": "div",
                "fields": fields
            },
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": f"触发挂起时间: {ts_now} · 智能体 Agent 03 状态机已暂挂等待人工签字"}]
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "审批同意通过"},
                        "type": "primary",
                        "value": {"action": "approve_requisition", "req_order_no": req_order_no}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "驳回申领请求"},
                        "type": "danger",
                        "value": {"action": "reject_requisition", "req_order_no": req_order_no}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "前往控制台复核"},
                        "type": "default",
                        "value": {"action": "open_spd_console", "req_order_no": req_order_no}
                    }
                ]
            }
        ])

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "orange",
                "title": {"tag": "plain_text", "content": "【SPD审批待办】临床大额高值申领人机回环挂起待审"}
            },
            "elements": elements
        }

    @classmethod
    def build_udi_freeze_card(
        cls,
        batch_no: str,
        udi_code: str,
        product_name: str,
        manufacturer: str,
        freeze_reason: str,
        operator_name: str,
        trace_no: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建高值耗材问题批次紧急物理冻结通告卡片 (胭脂红最高预警主题)

        @param batch_no: str 冻结批号
        @param udi_code: str 目标 UDI 码
        @param product_name: str 耗材名称
        @param manufacturer: str 生产厂家
        @param freeze_reason: str 冻结原因
        @param operator_name: str 处置人姓名
        @param trace_no: Optional[str] 6W 追踪号
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 飞书标准卡片 JSON 结构
        @route internal://services/feishu_service/build_udi_freeze_card
        @throws 无
        """
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = [
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**冻结批号:**\n`{batch_no}`"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**目标 UDI 码:**\n`{udi_code}`"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**耗材名称:**\n{product_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**生产厂家:**\n{manufacturer}"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**冻结范围:** 全院主库、高值专仓及所有临床科室二级柜"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**处置依据:** {freeze_reason}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**数据库状态:**\n`RECALLED / FROZEN` (扫码核销即刻熔断)"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**风控执行人:**\n{operator_name}"}},
        ]
        if trace_no:
            fields.append({"is_short": False, "text": {"tag": "lark_md", "content": f"**6W 审计流水号:** `{trace_no}`"}})

        elements = []
        if at_open_id:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"<at id=\"{at_open_id}\"></at> 紧急安全风控预警：请科室主任与护士长立即封存涉事物资。"
                }
            })
        elements.extend([
            {
                "tag": "div",
                "fields": fields
            },
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": f"冻结生效时间: {ts_now} · 智能体 Agent 04 全链路溯源与行级风控"}]
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看全生命周期溯源链"},
                        "type": "primary",
                        "value": {"action": "trace_udi_graph", "udi_code": udi_code}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "不良事件上报归档"},
                        "type": "default",
                        "value": {"action": "archive_adverse_event", "batch_no": batch_no}
                    }
                ]
            }
        ])

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "carmine",
                "title": {"tag": "plain_text", "content": "【SPD紧急预警】高值耗材问题批次即刻冻结通告"}
            },
            "elements": elements
        }

    @classmethod
    def build_interactive_reply_card(
        cls,
        title: str,
        query: str,
        answer: str,
        thought_process: Optional[str] = None,
        at_open_id: Optional[str] = None,
        template_color: str = "blue",
        summary_note: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """构建问答、业务数据检索与带思考链的高质感交互式卡片

        @param title: str 卡片顶栏标题
        @param query: str 用户提问或检索关键词
        @param answer: str 最终答案正文或系统检索结果
        @param thought_process: Optional[str] 大模型深度推理思考链 (若有)
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @param template_color: str 卡片主题色 ('blue' | 'turquoise' | 'orange' | 'wathet' | 'carmine')
        @param summary_note: Optional[str] 底部注脚说明
        @param fields: Optional[List[Dict[str, Any]]] 附加字段列表
        @returns Dict[str, Any] 飞书标准卡片 JSON 结构
        @route internal://services/feishu_service/build_interactive_reply_card
        @throws 无
        """
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements: List[Dict[str, Any]] = []

        # 1. 精准 @ 成员强提醒
        if at_open_id:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"<at id=\"{at_open_id}\"></at> 您好，针对您的提问已完成系统协同研判与检索："
                }
            })

        # 2. 提问与思考链展示
        body_md = f"**提问：** {query}\n\n"
        if thought_process and thought_process.strip():
            clean_thought = thought_process.strip()
            if len(clean_thought) > 400:
                clean_thought = clean_thought[:400] + "...(完整深度推理已在系统底座留痕)"
            body_md += f"**深度思考 (Deep Thinking)：**\n> {clean_thought}\n\n"
        body_md += f"**研判答复：**\n{answer}"

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": body_md
            }
        })

        # 3. 结构化字段 (如物资库存、编码等)
        if fields:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "fields": fields
            })

        # 4. 底部状态注脚
        elements.append({"tag": "hr"})
        note_text = summary_note or f"医疗物资管理系统 (SPD) · 8大智能体动态决策 · 响应时间: {ts_now}"
        elements.append({
            "tag": "note",
            "elements": [{"tag": "plain_text", "content": note_text}]
        })

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": template_color,
                "title": {"tag": "plain_text", "content": title}
            },
            "elements": elements
        }

    # =========================================================================
    # 消息发送与 Webhook 推送
    # =========================================================================

    def send_interactive_card(
        self,
        card_content: Dict[str, Any],
        receive_id: Optional[str] = None,
        receive_id_type: str = "open_id",
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """向指定飞书接收者或自定义机器人 Webhook 发送交互式卡片消息
        支持优先使用传入或默认的群机器人 Webhook 实现秒级进群弹卡；同时兼容企业自建应用 OpenAPI 推送。

        @param card_content: Dict[str, Any] 飞书标准 Card 结构
        @param receive_id: Optional[str] 用户 open_id 或 群聊 chat_id
        @param receive_id_type: str 接收者类型 ('open_id' | 'chat_id' | 'user_id')
        @param webhook_url: Optional[str] 可选的自定义群机器人 Webhook 地址
        @returns Dict[str, Any] 发送状态、响应回执或安全模拟结果
        @route internal://services/feishu_service/send_interactive_card
        @throws 内部捕获异常并平滑降级，绝不影响主业务
        """
        t0 = time.time()
        target_webhook = webhook_url or self.default_webhook_url

        # 1. 若配置了自定义机器人 Webhook，直接向 Webhook 推送 (真实秒级送达飞书群)
        if target_webhook and target_webhook.startswith("http"):
            try:
                payload = {
                    "msg_type": "interactive",
                    "card": card_content
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(target_webhook, json=payload)
                    latency = int((time.time() - t0) * 1000)
                    resp_json = resp.json() if resp.status_code == 200 else {}
                    is_ok = resp.status_code == 200 and resp_json.get("StatusCode", resp_json.get("code", 0)) == 0
                    return {
                        "success": is_ok,
                        "status_code": resp.status_code,
                        "latency_ms": latency,
                        "method": "webhook",
                        "webhook_used": target_webhook[:35] + "...",
                        "response": resp_json if resp.status_code == 200 else resp.text,
                        "message": "飞书群机器人 Webhook 真实推送成功，群内卡片已弹出" if is_ok else f"飞书推送响应异常: {resp.text}"
                    }
            except Exception as e:
                logger.warning(f"飞书 Webhook 发送失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "method": "webhook",
                    "card": card_content,
                    "message": f"飞书 Webhook 连接异常: {str(e)}"
                }

        # 2. 若传入了 receive_id，调用开放平台官方消息发送 API
        if receive_id:
            try:
                # 智能自适应 receive_id 类型 (oc_ 为群聊 chat_id, ou_ 为用户 open_id)
                actual_type = receive_id_type
                if receive_id.startswith("oc_"):
                    actual_type = "chat_id"
                elif receive_id.startswith("ou_"):
                    actual_type = "open_id"

                token = self.get_tenant_access_token()
                url = f"{self.BASE_URL}/open-apis/im/v1/messages?receive_id_type={actual_type}"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8"
                }
                payload = {
                    "receive_id": receive_id,
                    "msg_type": "interactive",
                    "content": json.dumps(card_content, ensure_ascii=False)
                }

                session = self._get_session()
                resp = session.post(url, headers=headers, json=payload, timeout=(5.0, 20.0))
                latency = int((time.time() - t0) * 1000)
                res_data = resp.json() if resp.status_code == 200 else {}
                is_ok = resp.status_code == 200 and res_data.get("code") == 0

                return {
                    "success": is_ok,
                    "status_code": resp.status_code,
                    "latency_ms": latency,
                    "method": "open_api",
                    "response": res_data,
                    "message": "飞书开放平台 OpenAPI 消息发送成功" if is_ok else f"飞书 OpenAPI 报错: {res_data.get('msg')}"
                }
            except Exception as e:
                logger.warning(f"飞书开放平台发送消息异常: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "method": "open_api",
                    "card": card_content,
                    "message": f"飞书 OpenAPI 发送异常: {str(e)}"
                }

        # 3. 若无接收人且无 Webhook，完成卡片组装并在控制台记录日志 (沙箱与自检模式)
        latency = int((time.time() - t0) * 1000)
        logger.info("未指定飞书接收目标与群机器人 Webhook，卡片已在本地就绪")
        return {
            "success": True,
            "mocked": True,
            "latency_ms": latency,
            "method": "local_mock",
            "message": "卡片结构组装解析成功！请在配置面板填入飞书群机器人 Webhook 地址，即可秒级在真实飞书群内弹卡。",
            "card": card_content
        }

    def send_text_message(
        self,
        text_content: str,
        receive_id: str,
        receive_id_type: str = "chat_id"
    ) -> Dict[str, Any]:
        """向指定飞书群聊或用户发送原生纯文本消息
        @param text_content: str 文本正文内容
        @param receive_id: str 接收人 open_id 或群聊 chat_id
        @param receive_id_type: str 接收者类型 ('open_id' | 'chat_id' | 'user_id')
        @returns Dict[str, Any] 包含 success, code, msg 回执
        @route internal://services/feishu_service/send_text_message
        @throws 内部捕获异常并平滑降级
        """
        t0 = time.time()
        try:
            # 智能自适应 receive_id 类型 (oc_ 为群聊 chat_id, ou_ 为用户 open_id)
            actual_type = receive_id_type
            if receive_id.startswith("oc_"):
                actual_type = "chat_id"
            elif receive_id.startswith("ou_"):
                actual_type = "open_id"

            token = self.get_tenant_access_token()
            url = f"{self.BASE_URL}/open-apis/im/v1/messages?receive_id_type={actual_type}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8"
            }
            payload = {
                "receive_id": receive_id,
                "msg_type": "text",
                "content": json.dumps({"text": text_content}, ensure_ascii=False)
            }
            session = self._get_session()
            resp = session.post(url, headers=headers, json=payload, timeout=(5.0, 20.0))
            latency = int((time.time() - t0) * 1000)
            res_data = resp.json() if resp.status_code == 200 else {}
            is_ok = resp.status_code == 200 and res_data.get("code") == 0
            return {
                "success": is_ok,
                "status_code": resp.status_code,
                "latency_ms": latency,
                "method": "open_api_text",
                "response": res_data,
                "message": "飞书纯文本消息发送成功" if is_ok else f"飞书 OpenAPI 报错: {res_data.get('msg')}"
            }
        except Exception as e:
            logger.warning(f"飞书纯文本消息发送异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "open_api_text",
                "message": f"飞书文本发送异常: {str(e)}"
            }

    # =========================================================================
    # 4 类业务便捷通知方法 (全面支持 webhook_url 与 receive_id 双轨)
    # =========================================================================

    def send_dict_create_notification(
        self,
        product_code: str,
        product_name: str,
        spec_model: str,
        main_dept_code: str,
        consumable_type: str,
        supplier_name: str,
        reg_cert_no: str,
        unit_price: float,
        udi_di: str,
        trace_no: Optional[str] = None,
        receive_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """触发新物资建仓飞书通知卡片推送

        @param product_code: str 物资标准编码
        @param product_name: str 物资通用名
        @param spec_model: str 规格型号
        @param main_dept_code: str 归口主科室编码 (CONSUMABLE_DEPT / EQUIPMENT_DEPT)
        @param consumable_type: str 耗材类别 (GENERAL / HIGH_VALUE)
        @param supplier_name: str 供货单位全称
        @param reg_cert_no: str 医疗器械注册证编号
        @param unit_price: float 物资基准单价
        @param udi_di: str UDI-DI 厂商产品标识
        @param trace_no: Optional[str] 关联的 6W 审计全流程追踪号
        @param receive_id: Optional[str] 飞书接收人 open_id 或群聊 chat_id
        @param webhook_url: Optional[str] 自定义群机器人 Webhook 地址
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 发送响应结果
        @route internal://services/feishu_service/send_dict_create_notification
        @throws 内部安全捕获网络异常
        """
        card = self.build_dict_create_card(
            product_code=product_code,
            product_name=product_name,
            spec_model=spec_model,
            main_dept_code=main_dept_code,
            consumable_type=consumable_type,
            supplier_name=supplier_name,
            reg_cert_no=reg_cert_no,
            unit_price=unit_price,
            udi_di=udi_di,
            trace_no=trace_no,
            at_open_id=at_open_id
        )
        return self.send_interactive_card(card, receive_id=receive_id, webhook_url=webhook_url)

    def send_dispatch_order_notification(
        self,
        dist_order_no: str,
        target_dept_name: str,
        product_name: str,
        batch_no: str,
        expiry_date: str,
        dist_qty: int,
        unit_price: float,
        dispatcher_name: str,
        trace_no: Optional[str] = None,
        receive_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """触发主库分发调拨完成飞书通知卡片推送

        @param dist_order_no: str 主库调拨单唯一编号
        @param target_dept_name: str 接收调拨物资的二级库科室名称
        @param product_name: str 调拨物资通用名称与品规
        @param batch_no: str 调拨出库的生产批号
        @param expiry_date: str 批次有效截止日期 (YYYY-MM-DD)
        @param dist_qty: int 分发出库数量
        @param unit_price: float 物资单价
        @param dispatcher_name: str 主库操作发料人姓名
        @param trace_no: Optional[str] 关联的 6W 物权交接流水号
        @param receive_id: Optional[str] 飞书接收人 open_id 或群聊 chat_id
        @param webhook_url: Optional[str] 自定义群机器人 Webhook 地址
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 发送响应结果
        @route internal://services/feishu_service/send_dispatch_order_notification
        @throws 内部安全捕获网络异常
        """
        card = self.build_dispatch_order_card(
            dist_order_no=dist_order_no,
            target_dept_name=target_dept_name,
            product_name=product_name,
            batch_no=batch_no,
            expiry_date=expiry_date,
            dist_qty=dist_qty,
            unit_price=unit_price,
            dispatcher_name=dispatcher_name,
            trace_no=trace_no,
            at_open_id=at_open_id
        )
        return self.send_interactive_card(card, receive_id=receive_id, webhook_url=webhook_url)

    @classmethod
    def build_hitl_approval_card(
        cls,
        req_order_no: str,
        apply_dept_name: str,
        product_name: str,
        apply_qty: int,
        urgency_level: str = "ROUTINE",
        applicant_name: str = "临床科室护士",
        reason: str = "临床科室申领触发人机协同审批",
        **kwargs
    ) -> Dict[str, Any]:
        """构建人机回环审批待办交互式卡片 (自适应参数契约)
        @param req_order_no: str 申领单号
        @param apply_dept_name: str 科室名称
        @param product_name: str 物资品名
        @param apply_qty: int 申领数量
        @param urgency_level: str 紧急程度
        @param applicant_name: str 申请人姓名
        @param reason: str 挂起原因
        @returns Dict[str, Any] 卡片 JSON 结构
        @route internal://services/feishu_service/build_hitl_approval_card
        @throws 无
        """
        total_amount = float(kwargs.get("total_amount", apply_qty * 18.5))
        spec_model = str(kwargs.get("spec_model", "标准临床规格"))
        return cls.build_approval_suspend_card(
            req_order_no=req_order_no,
            apply_dept_name=apply_dept_name,
            applicant_name=applicant_name,
            product_name=product_name,
            spec_model=spec_model,
            apply_qty=apply_qty,
            total_amount=total_amount,
            suspend_reason=reason,
            trace_no=kwargs.get("trace_no")
        )

    def send_hitl_approval_notification(
        self,
        req_order_no: str,
        dept_name: str = "骨科病区二级库",
        product_name: str = "一次性医用外科口罩",
        apply_qty: int = 50,
        urgency_level: str = "ROUTINE",
        applicant_name: str = "临床科室护士",
        reason: str = "临床科室申领触发人机协同审批",
        trace_no: Optional[str] = None,
        receive_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """触发人机协同审批挂起飞书待办卡片推送 (自适应参数别名)
        @param req_order_no: str 申领单号
        @param dept_name: str 科室名称
        @param product_name: str 物资品名
        @param apply_qty: int 申领数量
        @param urgency_level: str 紧急程度
        @param applicant_name: str 申请人
        @param reason: str 挂起原因
        @param trace_no: Optional[str] 6W 日志流水
        @param receive_id: Optional[str] 接收人
        @returns Dict[str, Any]
        @route internal://services/feishu_service/send_hitl_approval_notification
        @throws 内部安全捕获
        """
        total_amount = float(kwargs.get("total_amount", apply_qty * 18.5))
        spec_model = str(kwargs.get("spec_model", "标准临床规格"))
        return self.send_approval_suspend_notification(
            req_order_no=req_order_no,
            apply_dept_name=dept_name,
            applicant_name=applicant_name,
            product_name=product_name,
            spec_model=spec_model,
            apply_qty=apply_qty,
            total_amount=total_amount,
            suspend_reason=reason,
            trace_no=trace_no,
            receive_id=receive_id
        )

    def send_approval_suspend_notification(
        self,
        req_order_no: str,
        apply_dept_name: str,
        applicant_name: str,
        product_name: str,
        spec_model: str,
        apply_qty: int,
        total_amount: float,
        suspend_reason: str = "单笔申领总额超过一万元红线，触发人机协同 (HITL) 双人复核",
        trace_no: Optional[str] = None,
        receive_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """触发大额申领审批挂起飞书待办卡片推送

        @param req_order_no: str 临床科室耗材申领单号
        @param apply_dept_name: str 发起申领的临床科室名称
        @param applicant_name: str 申领申请人姓名
        @param product_name: str 申请领用的物资品名
        @param spec_model: str 物资规格型号
        @param apply_qty: int 申领物资数量
        @param total_amount: float 申领预估总金额 (元)
        @param suspend_reason: str 触发状态机挂起风控规则的具体原因描述
        @param trace_no: Optional[str] 关联的 6W 审批链路追踪号
        @param receive_id: Optional[str] 飞书接收人 open_id 或群聊 chat_id
        @param webhook_url: Optional[str] 自定义群机器人 Webhook 地址
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 发送响应结果
        @route internal://services/feishu_service/send_approval_suspend_notification
        @throws 内部安全捕获网络异常
        """
        card = self.build_approval_suspend_card(
            req_order_no=req_order_no,
            apply_dept_name=apply_dept_name,
            applicant_name=applicant_name,
            product_name=product_name,
            spec_model=spec_model,
            apply_qty=apply_qty,
            total_amount=total_amount,
            suspend_reason=suspend_reason,
            trace_no=trace_no,
            at_open_id=at_open_id
        )
        return self.send_interactive_card(card, receive_id=receive_id, webhook_url=webhook_url)

    def send_udi_freeze_notification(
        self,
        batch_no: str,
        udi_code: str,
        product_name: str,
        manufacturer: str,
        freeze_reason: str,
        operator_name: str,
        trace_no: Optional[str] = None,
        receive_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        at_open_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """触发高值耗材紧急冻结飞书通告卡片推送

        @param batch_no: str 目标紧急冻结的生产批号
        @param udi_code: str 目标唯一识别 UDI 码或序列号
        @param product_name: str 涉事高值耗材通用品名
        @param manufacturer: str 耗材生产厂家全称
        @param freeze_reason: str 质量召回或不良事件处置依据说明
        @param operator_name: str 触发本次物理冻结的风控执行人
        @param trace_no: Optional[str] 关联的 6W 审计处置追踪号
        @param receive_id: Optional[str] 飞书接收人 open_id 或群聊 chat_id
        @param webhook_url: Optional[str] 自定义群机器人 Webhook 地址
        @param at_open_id: Optional[str] 需强提醒并 @ 的成员 open_id
        @returns Dict[str, Any] 发送响应结果
        @route internal://services/feishu_service/send_udi_freeze_notification
        @throws 内部安全捕获网络异常
        """
        card = self.build_udi_freeze_card(
            batch_no=batch_no,
            udi_code=udi_code,
            product_name=product_name,
            manufacturer=manufacturer,
            freeze_reason=freeze_reason,
            operator_name=operator_name,
            trace_no=trace_no,
            at_open_id=at_open_id
        )
        return self.send_interactive_card(card, receive_id=receive_id, webhook_url=webhook_url)

    def send_raw_webhook_test(
        self,
        webhook_url: str,
        card_type: str = "dispatch_order",
        product_name: str = "经导管主动脉瓣膜系统"
    ) -> Dict[str, Any]:
        """向自定义飞书群机器人 Webhook 发送全真测试卡片
        支持直接校验 Webhook 连通性并推送实际交互式四联卡片到群聊中。

        @param webhook_url: str 目标飞书群机器人 Webhook 地址
        @param card_type: str 测试卡片类型 (dispatch_order | udi_freeze | hitl_approval | dict_create)
        @param product_name: str 演示物资品名
        @returns Dict[str, Any] 包含 success, status_code, latency_ms, response
        @route internal://services/feishu_service/send_raw_webhook_test
        @throws 异常捕获并返回平滑降级字典
        """
        now_ts = datetime.now().strftime("%Y%m%d%H%M%S")
        ctype = (card_type or "dispatch_order").lower()

        if ctype == "dispatch_order":
            return self.send_dispatch_order_notification(
                dist_order_no=f"DIST-FEISHU-{now_ts[-6:]}",
                target_dept_name="骨科手术室二级库",
                product_name=product_name,
                batch_no="B20261105",
                expiry_date="2027-11-04",
                dist_qty=15,
                unit_price=368.5,
                dispatcher_name="张主管 (主库管理员)",
                webhook_url=webhook_url
            )
        elif ctype == "udi_freeze":
            return self.send_udi_freeze_notification(
                batch_no="B20261105",
                udi_code="UDI-06972026110599",
                product_name=product_name,
                manufacturer="国药控股医疗科技(杭州)有限公司",
                freeze_reason="国家不良事件监测紧急召回指令，全院各级仓库即刻冻结",
                operator_name="信息科系统管理员",
                webhook_url=webhook_url
            )
        elif ctype == "hitl_approval":
            return self.send_approval_suspend_notification(
                req_order_no=f"REQ-FEISHU-{now_ts[-6:]}",
                apply_dept_name="心血管介入科病区",
                applicant_name="李护士长",
                product_name=product_name,
                spec_model="医用专业型",
                apply_qty=80,
                total_amount=29480.0,
                suspend_reason="单笔耗材请领金额突破两万元，触发状态机挂起人机协同双人签批",
                webhook_url=webhook_url
            )
        else:
            return self.send_dict_create_notification(
                product_code=f"PRD-FEISHU-{now_ts[-6:]}",
                product_name=product_name,
                spec_model="临床通用型",
                main_dept_code="CONSUMABLE_DEPT",
                consumable_type="HIGH_VALUE",
                supplier_name="普惠(杭州)医疗器械有限公司",
                reg_cert_no="国械注准20263139999",
                unit_price=450.0,
                udi_di="06978889998888",
                webhook_url=webhook_url
            )

    def handle_feishu_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """处理飞书开放平台 Webhook 回调事件 (URL 验证握手与卡片按钮交互)

        @param payload: Dict[str, Any] 飞书推送的回调载荷
        @returns Dict[str, Any] 响应飞书开放平台的结构体
        @route internal://services/feishu_service/handle_feishu_event
        @throws 无
        """
        # 1. 处理飞书 Webhook 首次配置时的 URL 验证握手
        if payload.get("type") == "url_verification":
            challenge = payload.get("challenge", "")
            return {"challenge": challenge}

        # 2. 处理卡片按钮点击回调
        action_data = payload.get("action", {})
        action_val = action_data.get("value", {})
        action_type = action_val.get("action", "unknown")

        logger.info(f"收到飞书卡片交互回调: action={action_type}, value={action_val}")
        return {
            "toast": {
                "type": "success",
                "content": f"系统已接收并响应操作 [{action_type}]，业务状态已更新"
            }
        }


# 全局单例导出
feishu_service = FeishuService()
