"""
@file high_value_tools.py
@description 高值耗材一物一码(UDI)全生命周期穿透溯源与问题批次紧急物理冻结 MCP 工具集
对应 Agent 04 (high_value_udi_trace_agent) 职责契约，
穿透查询 MySQL 在册条码与 6W 全流程交接日志时间轴，对患者信息实施强制脱敏，
在批次冻结时更新数据库状态并联动记录 6W 审计日志 (8_REVERSE_AUDIT)。

@param 各类 UDI 码溯源、批次冻结与脱敏查询入参
@returns ToolResult 统一封装结果
@route internal://backend/app/services/mcp_tools/high_value_tools.py
@throws 条码未检索到、联合条件空值拦截与数据库异常
"""

import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.spd_models import (
    SpdHighValueItem,
    SpdMainInventory,
    SpdWorkflowLog
)
from app.services.mcp_tools.schema import BaseToolInput, ToolResult
from app.services.trace_service import record_workflow_6w_log


class TraceUdiInput(BaseToolInput):
    """高值耗材 UDI 溯源入参模型"""
    udi_code: Optional[str] = Field(default=None, description="完整 UDI 条码或单品序列号 (SN)")
    batch_no: Optional[str] = Field(default=None, description="生产批号(辅助过滤)")
    operator_role: str = Field(default="secondary_user", description="当前操作人角色(非管理员患者隐私脱敏)")


class UdiItemDetail(BaseModel):
    """高值耗材单品明细模型"""
    id: int
    udi_full_code: str
    udi_sn: str
    product_name: str
    spec_model: str
    batch_no: str
    expiry_date: str
    unit_price: float
    wh_cabinet_code: str
    current_dept_name: str
    item_status: str
    patient_info_masked: str
    attending_doctor: Optional[str]
    verify_nurse_name: Optional[str]
    verified_at: Optional[str]


class HighValueTraceOutput(BaseModel):
    """高值耗材溯源全景输出模型"""
    item_found: bool
    item_detail: Optional[UdiItemDetail]
    workflow_timeline: List[Dict[str, Any]] = Field(default_factory=list, description="6W 全流程时间轴明细")
    is_frozen: bool


class FreezeProblemBatchInput(BaseToolInput):
    """问题批次与高值单品紧急物理冻结入参模型"""
    udi_code: Optional[str] = Field(default=None, description="待冻结的单个高值 UDI 码")
    batch_no: Optional[str] = Field(default=None, description="待批量冻结的生产批号")
    product_code: Optional[str] = Field(default=None, description="待冻结的物资标准编码")
    freeze_reason: str = Field(..., min_length=4, description="国家药监召回文号或不良事件调查原因")
    operator_name: str = Field(default="质量安全管理员", min_length=2, description="执行冻结的操作管理员姓名")
    operator_account: str = Field(default="sys_admin", description="操作人员账号工号")


class FreezeBatchOutput(BaseModel):
    """问题批次冻结完成输出模型"""
    frozen_items_count: int = Field(..., description="高值单品表中被置为 RECALLED 的条目总数")
    frozen_inventory_count: int = Field(..., description="主库库存表中被置为 RECALLED 的批次总数")
    target_identifier: str
    trace_no: str
    freeze_status: str = "FROZEN_CONFIRMED"


def _mask_patient_privacy(name: Optional[str], role: str) -> str:
    """患者姓名与隐私信息按角色安全脱敏函数
    符合 Skill 04 规范: 仅系统管理员查看，其他角色姓名中间脱敏为星号

    @param name: Optional[str] 患者原始真实姓名，若为空则显示未绑定患者
    @param role: str 当前访问用户的业务角色标识 (如 sys_admin, dept_manager, secondary_user 等)
    @returns str 符合隐私安全脱敏规范的姓名字符串 (管理员明文，其他脱敏为 张*三 或 李*)
    @route internal://backend/app/services/mcp_tools/high_value_tools.py/_mask_patient_privacy
    @throws 无 纯字符串脱敏处理，无异常抛出
    """
    if not name:
        return "未绑定患者"
    if role == "sys_admin":
        return name
    if len(name) <= 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]


def mcp_trace_udi_full_logs(input_model: TraceUdiInput, db: Session) -> ToolResult[HighValueTraceOutput]:
    """输入 UDI 唯一码或批号，穿透还原高值耗材流转链与 6W 人物时间轴

    @param input_model: TraceUdiInput 溯源码、批号与当前操作人角色
    @param db: Session 数据库活动会话
    @returns ToolResult[HighValueTraceOutput] 高值单品信息与 6W 时间轴
    @route internal://backend/app/services/mcp_tools/high_value_tools.py/mcp_trace_udi_full_logs
    @throws 数据库操作异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        # 1. 查找高值单品记录
        query = db.query(SpdHighValueItem)
        if input_model.udi_code:
            query = query.filter(
                or_(
                    SpdHighValueItem.udi_full_code == input_model.udi_code,
                    SpdHighValueItem.udi_sn == input_model.udi_code
                )
            )
        elif input_model.batch_no:
            query = query.filter(SpdHighValueItem.batch_no == input_model.batch_no)
        else:
            # 若未传入具体唯一码或批号，默认检索第一条高值耗材作为基线溯源样本
            query = query.order_by(SpdHighValueItem.id.asc())

        item = query.first()
        if not item:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=True,
                tool_name="mcp_trace_udi_full_logs",
                input_args=raw_args,
                data=HighValueTraceOutput(
                    item_found=False,
                    item_detail=None,
                    workflow_timeline=[],
                    is_frozen=False
                ),
                message=f"未在在册高值专仓中检索到条码: {input_model.udi_code or input_model.batch_no}",
                execution_time_ms=execution_time_ms
            )

        # 患者隐私脱敏处理
        masked_patient = _mask_patient_privacy(item.patient_name_masked, input_model.operator_role)
        is_frozen = item.item_status in ["RECALLED", "FROZEN"]

        detail = UdiItemDetail(
            id=item.id,
            udi_full_code=item.udi_full_code,
            udi_sn=item.udi_sn,
            product_name=item.product_name,
            spec_model=item.spec_model,
            batch_no=item.batch_no,
            expiry_date=item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else "",
            unit_price=float(item.unit_price),
            wh_cabinet_code=item.wh_cabinet_code,
            current_dept_name=item.current_dept_name,
            item_status=item.item_status,
            patient_info_masked=masked_patient,
            attending_doctor=item.attending_doctor,
            verify_nurse_name=item.verify_nurse_name,
            verified_at=item.verified_at.strftime("%Y-%m-%d %H:%M:%S") if item.verified_at else None
        )

        # 2. 查询 6W 全流程时间轴日志
        log_query = db.query(SpdWorkflowLog).filter(
            or_(
                SpdWorkflowLog.batch_or_udi == item.udi_full_code,
                SpdWorkflowLog.batch_or_udi == item.udi_sn,
                SpdWorkflowLog.batch_or_udi == item.batch_no,
                SpdWorkflowLog.product_code == item.product_code
            )
        ).order_by(SpdWorkflowLog.created_at.asc()).all()

        timeline: List[Dict[str, Any]] = []
        for l in log_query:
            timeline.append({
                "trace_no": l.trace_no,
                "node_action": l.node_action,
                "biz_order_no": l.biz_order_no,
                "from_dept_name": l.from_dept_name,
                "from_user_name": l.from_user_name,
                "to_dept_name": l.to_dept_name,
                "to_user_name": l.to_user_name,
                "change_qty": l.change_qty,
                "settlement_amount": float(l.settlement_amount),
                "is_billable": l.is_billable,
                "audit_status": l.audit_status,
                "audit_remark": l.audit_remark,
                "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else ""
            })

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_trace_udi_full_logs",
            input_args=raw_args,
            data=HighValueTraceOutput(
                item_found=True,
                item_detail=detail,
                workflow_timeline=timeline,
                is_frozen=is_frozen
            ),
            message=f"成功还原高值条码 [{item.udi_sn}] 全生命周期时间轴，共检索到 {len(timeline)} 个 6W 物权交接节点",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_trace_udi_full_logs",
            input_args=raw_args,
            error=str(e),
            message=f"高值 UDI 溯源异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_freeze_problem_batch(input_model: FreezeProblemBatchInput, db: Session) -> ToolResult[FreezeBatchOutput]:
    """质量抽检不合格或不良事件时，对高值单品或批次库存执行行级锁定与物理冻结

    @param input_model: FreezeProblemBatchInput 冻结目标与原因参数
    @param db: Session 数据库活动会话
    @returns ToolResult[FreezeBatchOutput] 冻结行数与 6W 日志流水号
    @route internal://backend/app/services/mcp_tools/high_value_tools.py/mcp_freeze_problem_batch
    @throws 条件全空拦截与数据库事务异常
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        if not input_model.udi_code and not input_model.batch_no and not input_model.product_code:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=False,
                tool_name="mcp_freeze_problem_batch",
                input_args=raw_args,
                error="EMPTY_CRITERIA",
                message="必须至少指定 UDI 码、批号或物资编码之一，严禁全表误冻结",
                execution_time_ms=execution_time_ms
            )

        target_identifier = input_model.udi_code or input_model.batch_no or input_model.product_code or ""

        # 1. 冻结高值单品表 (spd_high_value_item)
        hv_query = db.query(SpdHighValueItem)
        if input_model.udi_code:
            hv_query = hv_query.filter(
                or_(
                    SpdHighValueItem.udi_full_code == input_model.udi_code,
                    SpdHighValueItem.udi_sn == input_model.udi_code
                )
            )
        elif input_model.batch_no:
            hv_query = hv_query.filter(SpdHighValueItem.batch_no == input_model.batch_no)
        elif input_model.product_code:
            hv_query = hv_query.filter(SpdHighValueItem.product_code == input_model.product_code)

        frozen_hv_items = hv_query.all()
        for item in frozen_hv_items:
            item.item_status = "RECALLED"
        db.flush()

        # 2. 冻结主库批次库存表 (spd_main_inventory)
        frozen_main_items = []
        if input_model.batch_no:
            frozen_main_items = db.query(SpdMainInventory).filter(SpdMainInventory.batch_no == input_model.batch_no).all()
        elif input_model.product_code:
            frozen_main_items = db.query(SpdMainInventory).filter(SpdMainInventory.product_code == input_model.product_code).all()
        elif frozen_hv_items:
            # 根据高值单品反查关联批号，仅冻结同批次主库库存
            associated_batches = list({item.batch_no for item in frozen_hv_items if item.batch_no})
            if associated_batches:
                frozen_main_items = db.query(SpdMainInventory).filter(SpdMainInventory.batch_no.in_(associated_batches)).all()

        for m in frozen_main_items:
            m.quality_status = "RECALLED"
        db.flush()

        total_frozen = len(frozen_hv_items) + len(frozen_main_items)

        # 3. 联动 6W 审计日志 (8_REVERSE_AUDIT)
        log_entry = record_workflow_6w_log(
            db=db,
            biz_order_no=f"FREEZE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            node_action="8_REVERSE_AUDIT",
            product_code=input_model.product_code or (frozen_hv_items[0].product_code if frozen_hv_items else "MULTI_PROD"),
            product_name="紧急召回冻结物资批次",
            batch_or_udi=target_identifier,
            from_dept_name="医院质量安全与风控中心",
            from_user_name=input_model.operator_name,
            to_dept_name="不良事件隔离封存仓",
            to_user_name="质量风控管理员",
            change_qty=total_frozen,
            before_stock_snapshot=0,
            after_stock_snapshot=0,
            settlement_amount=Decimal("0.00"),
            is_billable=0,
            audit_remark=f"紧急风控冻结: {input_model.freeze_reason}"
        )
        log_entry.audit_status = "FLAGGED"
        db.commit()

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_freeze_problem_batch",
            input_args=raw_args,
            data=FreezeBatchOutput(
                frozen_items_count=len(frozen_hv_items),
                frozen_inventory_count=len(frozen_main_items),
                target_identifier=target_identifier,
                trace_no=log_entry.trace_no,
                freeze_status="FROZEN_CONFIRMED"
            ),
            message=f"已紧急冻结高值单品 {len(frozen_hv_items)} 件、主库批次 {len(frozen_main_items)} 组，已登记 6W 审计流水号: {log_entry.trace_no}",
            trace_no=log_entry.trace_no,
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        db.rollback()
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_freeze_problem_batch",
            input_args=raw_args,
            error=str(e),
            message=f"问题批次冻结操作失败已回滚: {str(e)}",
            execution_time_ms=execution_time_ms
        )
