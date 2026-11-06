"""
@file dispatch_tools.py
@description 主库物资按需分发、全院库存水位穿透扫描与 FEFO 调拨下发 MCP 工具集
对应 Agent 02 (main_stock_dispatch_agent) 职责契约，
严格执行 FEFO (近效期先出) 原则，物理核减主库库存，并联动记录 6W 审计日志 (3_MAIN_DISPATCH)。

@param 各类库存扫描、调拨建单与待审批查询入参
@returns ToolResult 统一封装结果
@route internal://backend/app/services/mcp_tools/dispatch_tools.py
@throws 库存不足、批次过期拦截与数据库事务异常
"""

import random
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.spd_models import (
    SpdDistributionOrder,
    SpdMainInventory,
    SpdRequisitionOrder,
    SpdSecondaryInventory
)
from app.services.mcp_tools.schema import BaseToolInput, ToolResult
from app.services.trace_service import record_workflow_6w_log


class ScanStockInput(BaseToolInput):
    """主库与临床二级库库存水位扫描入参模型"""
    main_dept_code: Optional[str] = Field(default=None, description="主库科室编码: CONSUMABLE_DEPT / EQUIP_DEPT")
    target_dept_id: Optional[int] = Field(default=None, description="目标临床二级库ID")
    product_code: Optional[str] = Field(default=None, description="指定物资编码过滤")
    only_shortage: bool = Field(default=False, description="是否仅筛选低于安全水位的缺货记录")
    limit: int = Field(default=20, ge=1, le=100, description="读取批次条数上限")


class MainStockBatchItem(BaseModel):
    """主库批次库存明细项模型 (按 FEFO 效期升序)"""
    id: int
    product_id: int
    product_code: str
    product_name: str
    consumable_type: str
    batch_no: str
    expiry_date: str
    available_qty: int
    unit_price: float
    shelf_location: str
    quality_status: str


class SecStockItem(BaseModel):
    """临床二级库库存水位明细项模型"""
    id: int
    dept_id: int
    dept_name: str
    product_code: str
    product_name: str
    batch_no: str
    current_qty: int
    dept_safe_min: int
    shortage_qty: int


class ScanStockOutput(BaseModel):
    """全院库存扫描综合输出结构"""
    main_batches_count: int
    sec_stocks_count: int
    main_batches: List[MainStockBatchItem]
    sec_stocks: List[SecStockItem]


class CreateDispatchOrderInput(BaseToolInput):
    """创建主库分发调拨单入参模型"""
    main_inventory_id: int = Field(..., description="主库源批次库存ID(关联spd_main_inventory.id)")
    target_dept_id: Optional[int] = Field(default=1, description="接收目标科室ID(sys_department.id)")
    target_dept_name: str = Field(default="骨科病区二级库", min_length=2, description="接收目标科室名称(如: 骨科病区二级库)")
    target_type: str = Field(default="TO_SECONDARY_DEPT", description="TO_SECONDARY_DEPT / TO_HIGH_VALUE_WH")
    dist_qty: int = Field(..., gt=0, description="本次按需分发数量(必须为正整数)")
    dispatcher_id: int = Field(default=1, description="主库发料管理员ID")
    dispatcher_name: str = Field(default="主库发料员", min_length=2, description="主库发料人真实姓名")
    operator_name: Optional[str] = Field(default=None, description="操作人姓名别名兼容")
    remark: Optional[str] = Field(default="FEFO 近效期智能调拨下发", description="调拨原因说明")


class DispatchOrderOutput(BaseModel):
    """分发调拨单创建完成输出模型"""
    order_id: int
    dist_order_no: str
    product_code: str
    product_name: str
    batch_no: str
    expiry_date: str
    dist_qty: int
    unit_price: float
    total_amount: float
    remaining_main_qty: int
    trace_no: str
    order_status: str = "DISPATCHED"


class QueryPendingRequisitionsInput(BaseToolInput):
    """待审批二级库申领单查询入参模型"""
    main_dept_code: Optional[str] = Field(default=None, description="主库科室编码: CONSUMABLE_DEPT / EQUIP_DEPT")
    limit: int = Field(default=20, ge=1, le=100, description="单次查询上限")


class PendingRequisitionItem(BaseModel):
    """待审批申领单明细项"""
    id: int
    req_order_no: str
    apply_dept_name: str
    product_code: str
    product_name: str
    apply_qty: int
    urgency_level: str
    applicant_name: str
    apply_reason: Optional[str]
    created_at: str


class PendingRequisitionsOutput(BaseModel):
    """待审批申领单列表输出"""
    total_count: int
    items: List[PendingRequisitionItem]


def mcp_scan_main_and_sec_stock(input_model: ScanStockInput, db: Session) -> ToolResult[ScanStockOutput]:
    """穿透扫描主库总仓批次库存 (FEFO 排序) 与临床各二级库安全库存水位

    @param input_model: ScanStockInput 查询条件与缺货过滤参数
    @param db: Session 数据库活动会话
    @returns ToolResult[ScanStockOutput] 主库批次与临床二级库水位清单
    @route internal://backend/app/services/mcp_tools/dispatch_tools.py/mcp_scan_main_and_sec_stock
    @throws 数据库操作异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        # 1. 查询主库批次库存 (严格按 expiry_date 升序排列，落实 FEFO 原则)
        main_query = db.query(SpdMainInventory).filter(SpdMainInventory.available_qty > 0)
        if input_model.main_dept_code:
            main_query = main_query.filter(SpdMainInventory.main_dept_code == input_model.main_dept_code)
        if input_model.product_code:
            main_query = main_query.filter(SpdMainInventory.product_code.like(f"%{input_model.product_code}%"))

        main_rows = main_query.order_by(SpdMainInventory.expiry_date.asc()).limit(input_model.limit).all()
        main_batches: List[MainStockBatchItem] = []
        for m in main_rows:
            main_batches.append(MainStockBatchItem(
                id=m.id,
                product_id=m.product_id,
                product_code=m.product_code,
                product_name=m.product_name,
                consumable_type=m.consumable_type,
                batch_no=m.batch_no,
                expiry_date=m.expiry_date.strftime("%Y-%m-%d") if m.expiry_date else "",
                available_qty=m.available_qty,
                unit_price=float(m.unit_price),
                shelf_location=m.shelf_location,
                quality_status=m.quality_status
            ))

        # 2. 查询临床二级库库存水位
        sec_query = db.query(SpdSecondaryInventory)
        if input_model.target_dept_id:
            sec_query = sec_query.filter(SpdSecondaryInventory.dept_id == input_model.target_dept_id)
        if input_model.product_code:
            sec_query = sec_query.filter(SpdSecondaryInventory.product_code.like(f"%{input_model.product_code}%"))

        sec_rows = sec_query.order_by(SpdSecondaryInventory.id.desc()).limit(input_model.limit).all()
        sec_stocks: List[SecStockItem] = []
        for s in sec_rows:
            shortage = max(0, s.dept_safe_min - s.current_qty)
            if input_model.only_shortage and shortage <= 0:
                continue
            sec_stocks.append(SecStockItem(
                id=s.id,
                dept_id=s.dept_id,
                dept_name=s.dept_name,
                product_code=s.product_code,
                product_name=s.product_name,
                batch_no=s.batch_no,
                current_qty=s.current_qty,
                dept_safe_min=s.dept_safe_min,
                shortage_qty=shortage
            ))

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_scan_main_and_sec_stock",
            input_args=raw_args,
            data=ScanStockOutput(
                main_batches_count=len(main_batches),
                sec_stocks_count=len(sec_stocks),
                main_batches=main_batches,
                sec_stocks=sec_stocks
            ),
            message=f"扫描完成: 主库就绪批次 {len(main_batches)} 组，二级库监控位 {len(sec_stocks)} 组",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_scan_main_and_sec_stock",
            input_args=raw_args,
            error=str(e),
            message=f"库存扫描执行异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_create_dispatch_order(input_model: CreateDispatchOrderInput, db: Session) -> ToolResult[DispatchOrderOutput]:
    """主库按需创建分发调拨单，物理扣减主库库存并联动 6W 日志

    @param input_model: CreateDispatchOrderInput 调拨目标、批次与数量参数
    @param db: Session 数据库活动会话
    @returns ToolResult[DispatchOrderOutput] 调拨单生成实体与 6W 追踪凭据
    @route internal://backend/app/services/mcp_tools/dispatch_tools.py/mcp_create_dispatch_order
    @throws 库存不足或批次过期时硬拦截并回滚
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        main_inv = db.query(SpdMainInventory).filter(SpdMainInventory.id == input_model.main_inventory_id).first()
        if not main_inv:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=False,
                tool_name="mcp_create_dispatch_order",
                input_args=raw_args,
                error="MAIN_BATCH_NOT_FOUND",
                message=f"主库源批次不存在: ID={input_model.main_inventory_id}",
                execution_time_ms=execution_time_ms
            )

        # 批次风控状态校验
        if main_inv.quality_status in ["EXPIRED", "RECALLED", "DAMAGED"]:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=False,
                tool_name="mcp_create_dispatch_order",
                input_args=raw_args,
                error="BATCH_STATUS_LOCKED",
                message=f"该批次当前质量状态为 [{main_inv.quality_status}]，已触发质量硬拦截，严禁出库分发",
                execution_time_ms=execution_time_ms
            )

        # 可用库存扣减校验
        if main_inv.available_qty < input_model.dist_qty:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=False,
                tool_name="mcp_create_dispatch_order",
                input_args=raw_args,
                error="INSUFFICIENT_STOCK",
                message=f"主库可用数量不足: 当前仅余 {main_inv.available_qty}，申请调拨 {input_model.dist_qty}",
                execution_time_ms=execution_time_ms
            )

        # 1. 扣减主库可用库存
        before_stock = main_inv.available_qty
        main_inv.available_qty -= input_model.dist_qty
        after_stock = main_inv.available_qty

        # 2. 生成唯一调拨单号
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand_s = random.randint(100, 999)
        dist_order_no = f"DIST-{ts}-{rand_s}"
        total_amt = Decimal(str(round(float(main_inv.unit_price) * input_model.dist_qty, 2)))

        dist_order = SpdDistributionOrder(
            dist_order_no=dist_order_no,
            source_main_dept=main_inv.main_dept_code,
            target_type=input_model.target_type,
            target_dept_id=input_model.target_dept_id,
            target_dept_name=input_model.target_dept_name,
            main_inventory_id=main_inv.id,
            product_id=main_inv.product_id,
            product_code=main_inv.product_code,
            product_name=main_inv.product_name,
            batch_no=main_inv.batch_no,
            expiry_date=main_inv.expiry_date,
            dist_qty=input_model.dist_qty,
            unit_price=main_inv.unit_price,
            total_amount=total_amt,
            order_status="DISPATCHED",
            dispatcher_id=input_model.dispatcher_id,
            dispatcher_name=input_model.operator_name or input_model.dispatcher_name,
            remark=input_model.remark
        )
        db.add(dist_order)
        db.flush()

        # 3. 联动二级库台账增加或更新 (若目标为临床二级库)
        if input_model.target_type == "TO_SECONDARY_DEPT":
            sec_inv = db.query(SpdSecondaryInventory).filter(
                SpdSecondaryInventory.dept_id == input_model.target_dept_id,
                SpdSecondaryInventory.product_id == main_inv.product_id,
                SpdSecondaryInventory.batch_no == main_inv.batch_no
            ).first()

            if sec_inv:
                sec_inv.current_qty += input_model.dist_qty
            else:
                new_sec = SpdSecondaryInventory(
                    dept_id=input_model.target_dept_id,
                    dept_name=input_model.target_dept_name,
                    product_id=main_inv.product_id,
                    product_code=main_inv.product_code,
                    product_name=main_inv.product_name,
                    main_dept_code=main_inv.main_dept_code,
                    batch_no=main_inv.batch_no,
                    expiry_date=main_inv.expiry_date,
                    current_qty=input_model.dist_qty,
                    consumed_qty=0,
                    unit_price=main_inv.unit_price,
                    sec_shelf_code="二级库标准货架-01",
                    dept_safe_min=5,
                    batch_status="NORMAL"
                )
                db.add(new_sec)
            db.flush()

        # 4. 联动记录 6W 业务流转日志
        source_dept_name = "耗材科主库" if main_inv.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库"
        log_entry = record_workflow_6w_log(
            db=db,
            biz_order_no=dist_order_no,
            node_action="3_MAIN_DISPATCH",
            product_code=main_inv.product_code,
            product_name=main_inv.product_name,
            batch_or_udi=main_inv.batch_no,
            from_dept_name=source_dept_name,
            from_user_name=input_model.dispatcher_name,
            to_dept_name=input_model.target_dept_name,
            to_user_name="二级库待签收责任人",
            change_qty=input_model.dist_qty,
            before_stock_snapshot=before_stock,
            after_stock_snapshot=after_stock,
            settlement_amount=total_amt,
            is_billable=0,
            audit_remark=input_model.remark or "FEFO 近效期智能调拨下发"
        )
        db.commit()

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_create_dispatch_order",
            input_args=raw_args,
            data=DispatchOrderOutput(
                order_id=dist_order.id,
                dist_order_no=dist_order_no,
                product_code=main_inv.product_code,
                product_name=main_inv.product_name,
                batch_no=main_inv.batch_no,
                expiry_date=main_inv.expiry_date.strftime("%Y-%m-%d"),
                dist_qty=input_model.dist_qty,
                unit_price=float(main_inv.unit_price),
                total_amount=float(total_amt),
                remaining_main_qty=after_stock,
                trace_no=log_entry.trace_no
            ),
            message=f"调拨单 [{dist_order_no}] 创建成功，已扣减主库库存并生成 6W 追踪号: {log_entry.trace_no}",
            trace_no=log_entry.trace_no,
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        db.rollback()
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_create_dispatch_order",
            input_args=raw_args,
            error=str(e),
            message=f"创建分发调拨单失败已回滚: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_query_pending_requisitions(input_model: QueryPendingRequisitionsInput, db: Session) -> ToolResult[PendingRequisitionsOutput]:
    """查询临床二级库发起的待审批物资申领单清单

    @param input_model: QueryPendingRequisitionsInput 查询范围与条数限制
    @param db: Session 数据库活动会话
    @returns ToolResult[PendingRequisitionsOutput] 待审批申领单列表
    @route internal://backend/app/services/mcp_tools/dispatch_tools.py/mcp_query_pending_requisitions
    @throws 数据库操作异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        query = db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.req_status == "PENDING_APPROVAL")
        if input_model.main_dept_code:
            query = query.filter(SpdRequisitionOrder.target_main_dept == input_model.main_dept_code)

        total_count = query.count()
        rows = query.order_by(SpdRequisitionOrder.created_at.desc()).limit(input_model.limit).all()

        items: List[PendingRequisitionItem] = []
        for r in rows:
            items.append(PendingRequisitionItem(
                id=r.id,
                req_order_no=r.req_order_no,
                apply_dept_name=r.apply_dept_name,
                product_code=r.product_code,
                product_name=r.product_name,
                apply_qty=r.apply_qty,
                urgency_level=r.urgency_level,
                applicant_name=r.applicant_name,
                apply_reason=r.apply_reason,
                created_at=r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
            ))

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_query_pending_requisitions",
            input_args=raw_args,
            data=PendingRequisitionsOutput(total_count=total_count, items=items),
            message=f"检索到 {total_count} 笔待主库审批的临床申领单",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_query_pending_requisitions",
            input_args=raw_args,
            error=str(e),
            message=f"待审批申领单检索异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )
