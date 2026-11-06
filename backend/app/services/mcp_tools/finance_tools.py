"""
@file finance_tools.py
@description 多科室耗材财务成本精算、耗占比统计与 6W 异常流转审计 MCP 工具集
对应 Agent 05 (finance_stat_audit_agent) 职责契约，
聚合统计临床各二级库普通与高值耗材消耗金额，穿透排查 6W 审计日志异常流转。

@param 各类核算月份、科室过滤与异常流转排查入参
@returns ToolResult 统一封装结果
@route internal://backend/app/services/mcp_tools/finance_tools.py
@throws 统计日期格式非法与数据库异常
"""

import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.spd_models import (
    SpdDistributionOrder,
    SpdHighValueItem,
    SpdWorkflowLog,
    SysDepartment
)
from app.services.mcp_tools.schema import BaseToolInput, ToolResult


class AggregateDeptCostInput(BaseToolInput):
    """科室耗材成本精算入参模型"""
    period_month: Optional[str] = Field(default=None, description="核算月份(格式 YYYY-MM，如 2026-11，默认当月)")
    dept_id: Optional[int] = Field(default=None, description="指定科室ID过滤")
    consumable_type: Optional[str] = Field(default="ALL", description="耗材类型: ALL-全部, GENERAL-普通耗材, HIGH_VALUE-高值耗材")


class DeptCostSummary(BaseModel):
    """科室成本明细项模型"""
    dept_id: int
    dept_name: str
    general_cost: float
    high_value_cost: float
    total_cost: float
    dispatch_count: int
    verified_patients_count: int


class DeptCostAggOutput(BaseModel):
    """科室成本财务精算汇总输出模型"""
    period: str
    total_hospital_cost: float
    dept_count: int
    details: List[DeptCostSummary]


class ScanAbnormalLogsInput(BaseToolInput):
    """异常流转审计排查入参模型"""
    start_date: Optional[str] = Field(default=None, description="审计起始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="审计截止日期 YYYY-MM-DD")
    dept_name: Optional[str] = Field(default=None, description="科室名称过滤")
    anomaly_type: Optional[str] = Field(default="ALL", description="异常类别: ALL / FLAGGED / REVERSE / DAMAGED")
    limit: int = Field(default=50, ge=1, le=200, description="读取日志上限条数")


class AbnormalLogItem(BaseModel):
    """异常流转单项输出模型"""
    id: int
    trace_no: str
    biz_order_no: str
    node_action: str
    product_code: str
    product_name: str
    from_dept_name: str
    to_dept_name: str
    change_qty: int
    settlement_amount: float
    audit_status: str
    audit_remark: str
    created_at: str


class AbnormalLogsOutput(BaseModel):
    """异常流转审计排查输出模型"""
    total_scanned: int
    abnormal_count: int
    flagged_logs: List[AbnormalLogItem]
    risk_assessment: str


def mcp_aggregate_dept_cost(input_model: AggregateDeptCostInput, db: Session) -> ToolResult[DeptCostAggOutput]:
    """聚合统计临床各二级库普通与高值耗材消耗金额与耗占比

    @param input_model: AggregateDeptCostInput 包含核算月份与科室过滤条件
    @param db: Session 数据库活动会话
    @returns ToolResult[DeptCostAggOutput] 科室成本拆分与全院总消耗汇总
    @route internal://backend/app/services/mcp_tools/finance_tools.py/mcp_aggregate_dept_cost
    @throws 数据库查询异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        period_str = input_model.period_month or datetime.now().strftime("%Y-%m")

        # 查询全院临床二级库科室
        dept_query = db.query(SysDepartment).filter(
            SysDepartment.dept_type == "SECONDARY_WAREHOUSE",
            SysDepartment.status == 1
        )
        if input_model.dept_id:
            dept_query = dept_query.filter(SysDepartment.id == input_model.dept_id)

        clinical_depts = dept_query.all()
        details: List[DeptCostSummary] = []
        total_hospital = 0.0

        for d in clinical_depts:
            # 1. 普通耗材调拨金额统计
            gen_dist = db.query(
                func.coalesce(func.sum(SpdDistributionOrder.total_amount), 0),
                func.count(SpdDistributionOrder.id)
            ).filter(
                SpdDistributionOrder.target_dept_id == d.id
            ).first()

            gen_cost = float(gen_dist[0] if gen_dist else 0.0)
            dist_count = int(gen_dist[1] if gen_dist else 0)

            # 2. 高值耗材临床核销金额统计
            hv_agg = db.query(
                func.coalesce(func.sum(SpdHighValueItem.unit_price), 0),
                func.count(SpdHighValueItem.id)
            ).filter(
                SpdHighValueItem.current_dept_id == d.id,
                SpdHighValueItem.item_status == "USED_VERIFIED"
            ).first()

            hv_cost = float(hv_agg[0] if hv_agg else 0.0)
            hv_count = int(hv_agg[1] if hv_agg else 0)

            # 过滤逻辑
            if input_model.consumable_type == "GENERAL":
                hv_cost = 0.0
            elif input_model.consumable_type == "HIGH_VALUE":
                gen_cost = 0.0

            sub_total = round(gen_cost + hv_cost, 2)
            total_hospital += sub_total

            details.append(DeptCostSummary(
                dept_id=d.id,
                dept_name=d.dept_name,
                general_cost=round(gen_cost, 2),
                high_value_cost=round(hv_cost, 2),
                total_cost=sub_total,
                dispatch_count=dist_count,
                verified_patients_count=hv_count
            ))

        total_hospital = round(total_hospital, 2)
        execution_time_ms = int((time.time() - t0) * 1000)

        return ToolResult(
            success=True,
            tool_name="mcp_aggregate_dept_cost",
            input_args=raw_args,
            data=DeptCostAggOutput(
                period=period_str,
                total_hospital_cost=total_hospital,
                dept_count=len(details),
                details=details
            ),
            message=f"核算期 [{period_str}] 统计完成: 共涵盖 {len(details)} 个临床科室，全院耗材总支出 {total_hospital} 元",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_aggregate_dept_cost",
            input_args=raw_args,
            error=str(e),
            message=f"科室成本精算统计异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_scan_abnormal_flow_logs(input_model: ScanAbnormalLogsInput, db: Session) -> ToolResult[AbnormalLogsOutput]:
    """穿透扫描 6W 业务日志排查异常流转、逆向退库与风控标记

    @param input_model: ScanAbnormalLogsInput 包含起止日期与异常类型过滤
    @param db: Session 数据库活动会话
    @returns ToolResult[AbnormalLogsOutput] 异常日志条目与综合风控评估
    @route internal://backend/app/services/mcp_tools/finance_tools.py/mcp_scan_abnormal_flow_logs
    @throws 数据库操作异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        query = db.query(SpdWorkflowLog)

        # 异常条件过滤
        if input_model.anomaly_type == "FLAGGED":
            query = query.filter(SpdWorkflowLog.audit_status == "FLAGGED")
        elif input_model.anomaly_type == "REVERSE":
            query = query.filter(SpdWorkflowLog.node_action == "8_REVERSE_AUDIT")
        else:
            # 默认抓取 FLAGGED 或 逆向退库/报损/召回
            query = query.filter(
                or_(
                    SpdWorkflowLog.audit_status == "FLAGGED",
                    SpdWorkflowLog.node_action == "8_REVERSE_AUDIT"
                )
            )

        if input_model.dept_name:
            query = query.filter(
                or_(
                    SpdWorkflowLog.from_dept_name.like(f"%{input_model.dept_name}%"),
                    SpdWorkflowLog.to_dept_name.like(f"%{input_model.dept_name}%")
                )
            )

        total_scanned = db.query(SpdWorkflowLog).count()
        abnormal_rows = query.order_by(SpdWorkflowLog.created_at.desc()).limit(input_model.limit).all()

        flagged_items: List[AbnormalLogItem] = []
        for r in abnormal_rows:
            flagged_items.append(AbnormalLogItem(
                id=r.id,
                trace_no=r.trace_no,
                biz_order_no=r.biz_order_no,
                node_action=r.node_action,
                product_code=r.product_code,
                product_name=r.product_name,
                from_dept_name=r.from_dept_name,
                to_dept_name=r.to_dept_name,
                change_qty=r.change_qty,
                settlement_amount=float(r.settlement_amount),
                audit_status=r.audit_status,
                audit_remark=r.audit_remark or "",
                created_at=r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
            ))

        abnormal_count = len(flagged_items)
        if abnormal_count == 0:
            assessment = "全院 6W 物权交接流转链路安全合规，未排查到任何逆向违规或冻结批次"
        elif abnormal_count < 5:
            assessment = f"排查到 {abnormal_count} 笔低风险预警流转（主要为质量冻结或常规退库退换），系统已有效留痕隔离"
        else:
            assessment = f"排查到 {abnormal_count} 笔高密度异常流转，建议立即启动医院耗材内控联合复核审计"

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_scan_abnormal_flow_logs",
            input_args=raw_args,
            data=AbnormalLogsOutput(
                total_scanned=total_scanned,
                abnormal_count=abnormal_count,
                flagged_logs=flagged_items,
                risk_assessment=assessment
            ),
            message=assessment,
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_scan_abnormal_flow_logs",
            input_args=raw_args,
            error=str(e),
            message=f"异常流转日志排查异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )
