"""
@file feishu_tools.py
@description 飞书开放平台协同推送与卡片状态核查 MCP 工具定义
支持向飞书群机器人自定义 Webhook 或自建应用 OpenAPI 推送高颜值标准业务卡片，
严格实施 Pydantic V2 强类型契约校验，禁用 extra 字段，全程零 Emoji 并包含 100% 中文四要素注释。

@param 飞书交互式卡片推送与状态自检入参
@returns ToolResult 统一结构体封装
@route internal://backend/app/services/mcp_tools/feishu_tools.py
@throws Pydantic 参数校验失败与网络超时安全捕获
"""

import logging
import time
from typing import Any, Dict, Optional
from pydantic import Field
from sqlalchemy.orm import Session

from app.services.feishu_service import feishu_service
from app.services.mcp_tools.schema import BaseToolInput, ToolResult

logger = logging.getLogger("spd.mcp_tools.feishu")


class FeishuPushCardInput(BaseToolInput):
    """飞书卡片推送 MCP 工具入参契约"""
    card_type: str = Field(
        ...,
        description="业务卡片类型: dispatch_order (物资调拨) | hitl_approval (大额审批) | udi_freeze (UDI冻结) | dict_create (字典建仓)"
    )
    product_name: str = Field(
        default="经导管主动脉瓣膜系统",
        description="涉及的物资品名或规格"
    )
    receive_id: Optional[str] = Field(
        default=None,
        description="可选的接收人 open_id 或群聊 chat_id (OpenAPI 模式)"
    )
    webhook_url: Optional[str] = Field(
        default=None,
        description="可选的飞书群自定义机器人 Webhook 地址 (秒级直连群聊)"
    )


class FeishuCheckStatusInput(BaseToolInput):
    """飞书服务连通性自检 MCP 工具入参契约"""
    check_open_api: bool = Field(default=True, description="是否探测飞书开放平台 OpenAPI 连通性")
    check_webhook: bool = Field(default=False, description="是否探测当前默认 Webhook 连通性")


def mcp_feishu_push_card(args: Dict[str, Any], db: Session) -> ToolResult:
    """向飞书外发业务交互式卡片 MCP 原子工具实现
    @param args: Dict[str, Any] 包含 card_type, product_name, receive_id, webhook_url
    @param db: Session SQLAlchemy 数据库会话
    @returns ToolResult 包含 success, status_code, latency_ms, method, message
    @route internal://services/mcp_tools/feishu_tools/mcp_feishu_push_card
    @throws 参数校验异常时由 Pydantic 拦截
    """
    t0 = time.time()
    validated = FeishuPushCardInput(**args)
    ctype = validated.card_type.lower()
    p_name = validated.product_name
    r_id = validated.receive_id
    w_url = validated.webhook_url

    if ctype == "udi_freeze":
        res = feishu_service.send_udi_freeze_notification(
            batch_no="B20261105",
            udi_code="UDI-06972026110599",
            product_name=p_name,
            manufacturer="国药控股医疗科技(杭州)有限公司",
            freeze_reason="国家不良事件紧急召回，全院主库与二级库即刻行级物理冻结",
            operator_name="信息科系统管理员",
            receive_id=r_id,
            webhook_url=w_url
        )
    elif ctype == "hitl_approval":
        res = feishu_service.send_approval_suspend_notification(
            req_order_no="REQ-20261105-001",
            apply_dept_name="心血管介入科病区",
            applicant_name="李护士长",
            product_name=p_name,
            spec_model="医用专业型",
            apply_qty=50,
            total_amount=18500.0,
            suspend_reason="单笔请领金额超过一万元红线，触发人机协同 (HITL) 双人复核",
            receive_id=r_id,
            webhook_url=w_url
        )
    elif ctype == "dict_create":
        res = feishu_service.send_dict_create_notification(
            product_code="PRD-AUTO-FEISHU",
            product_name=p_name,
            spec_model="标准规格",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="HIGH_VALUE",
            supplier_name="普惠(杭州)医疗器械有限公司",
            reg_cert_no="国械注准20263139999",
            unit_price=350.0,
            udi_di="06978889998888",
            receive_id=r_id,
            webhook_url=w_url
        )
    else:
        res = feishu_service.send_dispatch_order_notification(
            dist_order_no="DIST-20261105-009",
            target_dept_name="骨科手术室二级库",
            product_name=p_name,
            batch_no="B20261105",
            expiry_date="2027-11-04",
            dist_qty=20,
            unit_price=288.0,
            dispatcher_name="张主管",
            receive_id=r_id,
            webhook_url=w_url
        )

    execution_time_ms = int((time.time() - t0) * 1000)
    is_success = res.get("success", True)
    msg = res.get("message", "飞书交互式卡片推送完成")

    return ToolResult(
        success=is_success,
        tool_name="mcp_feishu_push_card",
        input_args=validated.model_dump(),
        data=res,
        error=None if is_success else res.get("error", "推送失败"),
        message=msg,
        execution_time_ms=execution_time_ms
    )


def mcp_feishu_check_status(args: Dict[str, Any], db: Session) -> ToolResult:
    """探测飞书通信信道健康度 MCP 原子工具实现
    @param args: Dict[str, Any] 包含 check_open_api, check_webhook
    @param db: Session SQLAlchemy 数据库会话
    @returns ToolResult 包含 connected, latency_ms, token_prefix, message
    @route internal://services/mcp_tools/feishu_tools/mcp_feishu_check_status
    @throws 内部安全捕获网络异常
    """
    t0 = time.time()
    validated = FeishuCheckStatusInput(**args)
    res = feishu_service.test_connection()
    execution_time_ms = int((time.time() - t0) * 1000)

    return ToolResult(
        success=res.get("connected", False),
        tool_name="mcp_feishu_check_status",
        input_args=validated.model_dump(),
        data=res,
        error=None if res.get("connected") else res.get("error"),
        message=res.get("message", "飞书信道探测完成"),
        execution_time_ms=execution_time_ms
    )
