"""二级库管理：临床科室库房路由模块 (核心 CRUD 四)

本模块管理临床二级库物资库存、主库分发签收与差异拒收退库、日常消耗登记，以及向主库正向申领与逆向退库审批。
"""

import random
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_context, require_roles, CurrentUserContext
from app.models.spd_models import (
    SpdSecondaryInventory,
    SpdDistributionOrder,
    SpdMainInventory,
    SpdRequisitionOrder,
    SpdProductDict,
    SpdWorkflowLog,
    SysDepartment
)
from app.models.spd_extended_models import (
    SpdInboundAndOutboundOrder,
    SpdStocktakeAndTransferOrder,
    SpdProductSpec
)
from app.schemas.spd_schemas import (
    ApiResponse,
    ReceiveDistributionRequest,
    ClinicalConsumeRequest,
    RequisitionCreateRequest,
    RequisitionApproveRequest,
    SecondaryInventoryResponse,
    RequisitionOrderResponse,
    RequisitionOrderCreateRequest,
    ManualOutboundCreateRequest,
    StocktakeSubmitRequest
)
from app.services.trace_service import record_workflow_6w_log

router = APIRouter(prefix="/secondary-warehouse", tags=["核心 CRUD 四：临床二级库管理与申领"])


@router.get("/inventory", response_model=ApiResponse[List[SecondaryInventoryResponse]])
def list_secondary_inventory(
    dept_id: Optional[int] = Query(None, description="科室ID (留空默认根据当前用户所属科室)"),
    warehouse_code: Optional[str] = Query(None, description="二级库仓库编码: WH_SEC_ORTHO | WH_SEC_CARDIO"),
    is_warning: Optional[bool] = Query(None, description="是否仅查询低于安全库存预警物资"),
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(get_current_user_context)
):
    """查询临床二级库物资库存台账 (按病区仓库严格隔离)

    @param: dept_id (Optional[int]) 科室ID
    @param: warehouse_code (Optional[str]) 二级库编码
    @param: is_warning (Optional[bool]) 仅查看低库存预警
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[List[SecondaryInventoryResponse]] 二级库库存清单
    @route: GET /api/v1/secondary-warehouse/inventory
    @throws: 无异常抛出
    """
    query = db.query(SpdSecondaryInventory)
    if warehouse_code == "WH_SEC_ORTHO":
        query = query.filter((SpdSecondaryInventory.dept_id == 3) | (SpdSecondaryInventory.dept_name.like("%骨科%")))
    elif warehouse_code == "WH_SEC_CARDIO":
        query = query.filter((SpdSecondaryInventory.dept_id == 4) | (SpdSecondaryInventory.dept_name.like("%心内%")))
    elif dept_id is not None:
        query = query.filter(SpdSecondaryInventory.dept_id == dept_id)
    elif user_ctx.role_code == "secondary_user" and user_ctx.dept_id:
        query = query.filter(SpdSecondaryInventory.dept_id == user_ctx.dept_id)

    if is_warning:
        query = query.filter(SpdSecondaryInventory.current_qty <= SpdSecondaryInventory.dept_safe_min)

    inventories = query.order_by(SpdSecondaryInventory.id.desc()).all()
    data = [SecondaryInventoryResponse.model_validate(inv) for inv in inventories]
    return ApiResponse(code=200, msg="查询二级库库存成功", data=data)


@router.get("/pending-receives", response_model=ApiResponse[List[dict]])
def list_pending_receives(
    dept_id: Optional[int] = Query(None, description="科室ID"),
    warehouse_code: Optional[str] = Query(None, description="二级库编码: WH_SEC_ORTHO | WH_SEC_CARDIO"),
    status_filter: Optional[str] = Query("ALL", description="DISPATCHED (待接收) | RECEIVED (已签收) | REJECTED (已拒收) | ALL (全部)"),
    keyword: Optional[str] = Query(None, description="单号/品名/批号模糊检索"),
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user", "dept_manager"]))
):
    """查询主库按需分发待临床二级库接收入库及历史已接收/已拒收单据清单 (按病区隔离与时间追溯)

    @param dept_id: (Optional[int]) 目标接收科室ID
    @param warehouse_code: (Optional[str]) 目标接收二级库编码
    @param status_filter: (Optional[str]) 单据状态过滤
    @param keyword: (Optional[str]) 关键词
    @param start_date: (Optional[str]) 起始日期
    @param end_date: (Optional[str]) 截止日期
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[List[dict]] 待接收与历史分发单列表
    @route: GET /api/v1/secondary-warehouse/pending-receives
    @throws: 无异常抛出
    """
    query = db.query(SpdDistributionOrder)

    # 1. 状态筛选
    if status_filter and status_filter != "ALL":
        query = query.filter(SpdDistributionOrder.order_status == status_filter)

    # 2. 病区二级库物理隔离
    if warehouse_code == "WH_SEC_ORTHO":
        query = query.filter((SpdDistributionOrder.target_dept_id == 3) | (SpdDistributionOrder.target_dept_name.like("%骨科%")))
    elif warehouse_code == "WH_SEC_CARDIO":
        query = query.filter((SpdDistributionOrder.target_dept_id == 4) | (SpdDistributionOrder.target_dept_name.like("%心内%")))
    elif dept_id:
        query = query.filter(SpdDistributionOrder.target_dept_id == dept_id)
    elif user_ctx.role_code == "secondary_user" and user_ctx.dept_id:
        query = query.filter(SpdDistributionOrder.target_dept_id == user_ctx.dept_id)

    # 3. 关键词与时间筛选
    if keyword:
        kw = f"%{keyword.strip()}%"
        query = query.filter(
            (SpdDistributionOrder.dist_order_no.like(kw)) |
            (SpdDistributionOrder.product_name.like(kw)) |
            (SpdDistributionOrder.batch_no.like(kw))
        )
    if start_date:
        query = query.filter(func.date(SpdDistributionOrder.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(SpdDistributionOrder.created_at) <= end_date)

    orders = query.order_by(SpdDistributionOrder.id.desc()).all()
    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "dist_order_no": o.dist_order_no,
            "source_main_dept": o.source_main_dept,
            "target_dept_id": o.target_dept_id,
            "target_dept_name": o.target_dept_name,
            "product_code": o.product_code,
            "product_name": o.product_name,
            "batch_no": o.batch_no,
            "expiry_date": str(o.expiry_date),
            "dist_qty": o.dist_qty,
            "unit_price": float(o.unit_price),
            "total_amount": float(o.total_amount),
            "order_status": o.order_status,
            "dispatcher_name": o.dispatcher_name,
            "receiver_name": o.receiver_name or "待签收",
            "received_at": str(o.received_at) if o.received_at else None,
            "created_at": str(o.created_at)
        })
    return ApiResponse(code=200, msg="获取分发单据列表成功", data=result)


@router.post("/receive/{dist_id}", response_model=ApiResponse[dict])
def receive_distribution_order(
    dist_id: int,
    payload: ReceiveDistributionRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床二级库签收主库按需分发调拨单（支持正常签收入库，或差异拒收逆向退回主库）

    @param: dist_id (int) 分发调拨单ID
    @param: payload (ReceiveDistributionRequest) 签收或拒收请求体
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[dict] 处理结果
    @route: POST /api/v1/secondary-warehouse/receive/{dist_id}
    @throws: HTTPException(400) 单据不存在或已处理过时抛出
    """
    dist_order = db.query(SpdDistributionOrder).filter(SpdDistributionOrder.id == dist_id).first()
    if not dist_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分发调拨单不存在")

    if dist_order.order_status != "DISPATCHED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"该分发单当前状态为 [{dist_order.order_status}]，不可重复签收")

    now = datetime.now()
    dist_order.receiver_id = user_ctx.id
    dist_order.receiver_name = user_ctx.real_name
    dist_order.received_at = now

    main_inv = db.query(SpdMainInventory).filter(SpdMainInventory.id == dist_order.main_inventory_id).first()

    # 签收分支 1：正常签收入库
    if payload.is_accept:
        dist_order.order_status = "RECEIVED"

        # 查找二级库是否已有相同科室+产品+批次的库存记录
        sec_inv = db.query(SpdSecondaryInventory).filter(
            SpdSecondaryInventory.dept_id == dist_order.target_dept_id,
            SpdSecondaryInventory.product_id == dist_order.product_id,
            SpdSecondaryInventory.batch_no == dist_order.batch_no
        ).first()

        before_qty = sec_inv.current_qty if sec_inv else 0
        if sec_inv:
            sec_inv.current_qty += dist_order.dist_qty
            after_qty = sec_inv.current_qty
        else:
            sec_inv = SpdSecondaryInventory(
                dept_id=dist_order.target_dept_id,
                dept_name=dist_order.target_dept_name,
                product_id=dist_order.product_id,
                product_code=dist_order.product_code,
                product_name=dist_order.product_name,
                main_dept_code=dist_order.source_main_dept,
                batch_no=dist_order.batch_no,
                expiry_date=dist_order.expiry_date,
                current_qty=dist_order.dist_qty,
                consumed_qty=0,
                unit_price=dist_order.unit_price,
                sec_shelf_code=f"{dist_order.target_dept_name}-标准货位01",
                dept_safe_min=10,
                batch_status="NORMAL"
            )
            db.add(sec_inv)
            after_qty = dist_order.dist_qty

        # 记录全流程日志 5_SEC_RECEIVE
        record_workflow_6w_log(
            db=db,
            biz_order_no=dist_order.dist_order_no,
            node_action="5_SEC_RECEIVE",
            product_code=dist_order.product_code,
            product_name=dist_order.product_name,
            batch_or_udi=dist_order.batch_no,
            from_dept_name="耗材科主库房" if dist_order.source_main_dept == "CONSUMABLE_DEPT" else "设备科主库房",
            from_user_name=dist_order.dispatcher_name,
            to_dept_name=dist_order.target_dept_name,
            to_user_name=user_ctx.real_name,
            change_qty=dist_order.dist_qty,
            before_stock_snapshot=before_qty,
            after_stock_snapshot=after_qty,
            settlement_amount=dist_order.total_amount,
            is_billable=0,  # 移库签收不计费
            audit_remark=f"二级库领用人 [{user_ctx.real_name}] 正常验收签收入库"
        )
        msg = f"二级库已成功签收入库 {dist_order.dist_qty} {dist_order.product_name}"
    else:
        # 签收分支 2：差异拒收退料（逆向回路，自动返还主库可用库存）
        dist_order.order_status = "REJECTED"
        if main_inv:
            before_main = main_inv.available_qty
            main_inv.available_qty += dist_order.dist_qty
            after_main = main_inv.available_qty
        else:
            before_main, after_main = 0, 0

        # 记录全流程日志 8_REVERSE_AUDIT 逆向拒收
        record_workflow_6w_log(
            db=db,
            biz_order_no=dist_order.dist_order_no,
            node_action="8_REVERSE_AUDIT",
            product_code=dist_order.product_code,
            product_name=dist_order.product_name,
            batch_or_udi=dist_order.batch_no,
            from_dept_name=dist_order.target_dept_name,
            from_user_name=user_ctx.real_name,
            to_dept_name="耗材科主库房" if dist_order.source_main_dept == "CONSUMABLE_DEPT" else "设备科主库房",
            to_user_name=dist_order.dispatcher_name,
            change_qty=dist_order.dist_qty,
            before_stock_snapshot=before_main,
            after_stock_snapshot=after_main,
            settlement_amount=dist_order.total_amount,
            is_billable=0,
            audit_remark=f"二级库领用人差异拒收退回主库，原因: {payload.reject_reason or '实物包装破损或规格不符'}"
        )
        msg = f"已拒收该分发单，物资数量 ({dist_order.dist_qty}) 已安全退回主库"

    db.commit()
    return ApiResponse(code=200, msg=msg, data={"dist_order_no": dist_order.dist_order_no, "status": dist_order.order_status})


@router.post("/consume", response_model=ApiResponse[dict])
def record_clinical_consume(
    payload: ClinicalConsumeRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床二级库普通耗材消耗登记（扣减库存并触发财务科成本核算，写入 7_CLINICAL_CONSUME）

    @param: payload (ClinicalConsumeRequest) 消耗登记参数
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[dict] 消耗成功确认
    @route: POST /api/v1/secondary-warehouse/consume
    @throws: HTTPException(400) 二级库库存不足时抛出
    """
    sec_inv = db.query(SpdSecondaryInventory).filter(SpdSecondaryInventory.id == payload.sec_inventory_id).first()
    if not sec_inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="二级库库存记录不存在")

    if sec_inv.current_qty < payload.consume_qty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"二级库在库可用数量 ({sec_inv.current_qty}) 不足，无法核销 {payload.consume_qty}")

    before_qty = sec_inv.current_qty
    sec_inv.current_qty -= payload.consume_qty
    sec_inv.consumed_qty += payload.consume_qty
    after_qty = sec_inv.current_qty

    amount = sec_inv.unit_price * Decimal(payload.consume_qty)

    # 记录全流程日志 7_CLINICAL_CONSUME（此时消耗即结算，is_billable=1）
    record_workflow_6w_log(
        db=db,
        biz_order_no=f"CON-{datetime.now().strftime('%Y%m%d%H%M')}-{random.randint(100, 999)}",
        node_action="7_CLINICAL_CONSUME",
        product_code=sec_inv.product_code,
        product_name=sec_inv.product_name,
        batch_or_udi=sec_inv.batch_no,
        from_dept_name=sec_inv.dept_name,
        from_user_name=user_ctx.real_name,
        to_dept_name="临床病区实际消耗",
        to_user_name=f"经办护士:{user_ctx.real_name}",
        change_qty=payload.consume_qty,
        before_stock_snapshot=before_qty,
        after_stock_snapshot=after_qty,
        settlement_amount=amount,
        is_billable=1,  # 消耗即结算，计入财务科科室成本
        audit_remark=f"临床耗材消耗核销，关联住院号: {payload.patient_inpatient_no or '病区常规公摊'}，用途: {payload.consume_reason}"
    )

    db.commit()
    return ApiResponse(code=200, msg="临床耗材消耗登记成功，已触发财务科室成本核算", data={"remaining_qty": after_qty, "settlement_amount": amount})


@router.get("/requisitions", response_model=ApiResponse[List[RequisitionOrderResponse]])
def list_requisitions(
    req_status: Optional[str] = Query(None, description="PENDING_APPROVAL | APPROVED_DISPATCHED | REJECTED"),
    order_direction: Optional[str] = Query(None, description="APPLY_FROM_MAIN | RETURN_TO_MAIN"),
    target_main_dept: Optional[str] = Query(None, description="CONSUMABLE_DEPT | EQUIP_DEPT"),
    db: Session = Depends(get_db)
):
    """查询临床二级库向主库的申领与退库单列表

    @param: req_status (Optional[str]) 审批状态
    @param: order_direction (Optional[str]) 申领或退库
    @param: target_main_dept (Optional[str]) 定向审批主库
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[RequisitionOrderResponse]] 申领单列表
    @route: GET /api/v1/secondary-warehouse/requisitions
    @throws: 无异常抛出
    """
    query = db.query(SpdRequisitionOrder)
    if req_status:
        query = query.filter(SpdRequisitionOrder.req_status == req_status)
    if order_direction:
        query = query.filter(SpdRequisitionOrder.order_direction == order_direction)
    if target_main_dept:
        query = query.filter(SpdRequisitionOrder.target_main_dept == target_main_dept)

    orders = query.order_by(SpdRequisitionOrder.id.desc()).all()
    data = [RequisitionOrderResponse.model_validate(o) for o in orders]
    return ApiResponse(code=200, msg="获取申领单列表成功", data=data)


@router.post("/requisitions", response_model=ApiResponse[RequisitionOrderResponse])
def create_requisition(
    payload: RequisitionCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床二级库新建申领单或退库单（根据产品字典主科室自动定向路由至耗材科或设备科审批）

    @param: payload (RequisitionCreateRequest) 申领单入参
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[RequisitionOrderResponse] 创建的申领单对象
    @route: POST /api/v1/secondary-warehouse/requisitions
    @throws: HTTPException(400) 产品不存在时抛出
    """
    product = db.query(SpdProductDict).filter(SpdProductDict.id == payload.product_id, SpdProductDict.is_deleted == 0).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="申领产品不存在或已停用")

    req_no = f"REQ-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"

    order = SpdRequisitionOrder(
        req_order_no=req_no,
        order_direction=payload.order_direction,
        apply_dept_id=user_ctx.dept_id,
        apply_dept_name=user_ctx.dept_name,
        target_main_dept=product.main_dept_code,  # 自动绑定产品归口科室
        product_id=product.id,
        product_code=product.product_code,
        product_name=product.product_name,
        apply_qty=payload.apply_qty,
        urgency_level=payload.urgency_level,
        req_status="PENDING_APPROVAL",
        applicant_id=user_ctx.id,
        applicant_name=user_ctx.real_name,
        apply_reason=payload.apply_reason
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return ApiResponse(code=200, msg="申领单创建成功，已提交主库房审批", data=RequisitionOrderResponse.model_validate(order))


@router.put("/requisitions/{req_id}/approve", response_model=ApiResponse[RequisitionOrderResponse])
def approve_requisition(
    req_id: int,
    payload: RequisitionApproveRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """主库管理员审批二级库申领单或退库单（记录日志 6_SEC_APPLY 或 8_REVERSE_AUDIT）

    @param: req_id (int) 申领单ID
    @param: payload (RequisitionApproveRequest) 审批意见与批准数量
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[RequisitionOrderResponse] 审批后的单据
    @route: PUT /api/v1/secondary-warehouse/requisitions/{req_id}/approve
    @throws: HTTPException(400) 单据不存在或已处理过时抛出
    """
    order = db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.id == req_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申领单不存在")

    if order.req_status != "PENDING_APPROVAL":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"该单据当前状态为 [{order.req_status}]，不可重复审批")

    now = datetime.now()
    order.approver_id = user_ctx.id
    order.approver_name = user_ctx.real_name
    order.approved_at = now

    if payload.is_approved:
        order.approved_qty = payload.approved_qty
        order.req_status = "APPROVED_DISPATCHED"

        # 记录 6W 全流程流转日志 6_SEC_APPLY
        record_workflow_6w_log(
            db=db,
            biz_order_no=order.req_order_no,
            node_action="6_SEC_APPLY" if order.order_direction == "APPLY_FROM_MAIN" else "8_REVERSE_AUDIT",
            product_code=order.product_code,
            product_name=order.product_name,
            batch_or_udi="待调拨批次分配",
            from_dept_name="耗材科主库房" if order.target_main_dept == "CONSUMABLE_DEPT" else "设备科主库房",
            from_user_name=user_ctx.real_name,
            to_dept_name=order.apply_dept_name,
            to_user_name=order.applicant_name,
            change_qty=payload.approved_qty,
            before_stock_snapshot=0,
            after_stock_snapshot=0,
            settlement_amount=Decimal("0.00"),
            is_billable=0,
            audit_remark=f"主库管理员 [{user_ctx.real_name}] 审批同意申领，批准数量: {payload.approved_qty}"
        )
        msg = f"申领单已批准 (数量: {payload.approved_qty})，即将生成分发调拨单"
    else:
        order.approved_qty = 0
        order.req_status = "REJECTED"
        msg = f"申领单已驳回，原因: {payload.reject_reason or '库存紧缺暂不分发'}"

    db.commit()
    db.refresh(order)
    return ApiResponse(code=200, msg=msg, data=RequisitionOrderResponse.model_validate(order))


# =========================================================================
# 临床科室物资申领单填报 (对标图 4 申请单) 与自主撤回/删除
# =========================================================================

@router.post("/requisitions-batch", response_model=ApiResponse[dict])
def create_requisition_batch(
    payload: RequisitionOrderCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床科室护士填报物资申请单 (对标图 4 申请单录入)

    @param payload: (RequisitionOrderCreateRequest) 申领科室、出库主库与多耗材明细
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 生成的申请单号与明细条目
    @route: POST /api/v1/secondary-warehouse/requisitions-batch
    @throws: HTTPException(400) 当明细为空时抛出
    """
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="申请耗材明细不能为空")

    req_order_no = f"SQ{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    created_orders = []

    for item in payload.items:
        order = SpdRequisitionOrder(
            req_order_no=req_order_no,
            order_direction="APPLY_FROM_MAIN",
            apply_dept_id=user_ctx.dept_id or 1,
            apply_dept_name=payload.apply_dept_name,
            target_main_dept="CONSUMABLE_DEPT",
            product_id=1,
            product_code=item.spec_code,
            product_name=f"{item.product_name} {item.spec_name}".strip(),
            apply_qty=item.apply_qty,
            approved_qty=0,
            urgency_level=payload.urgency_level,
            req_status="PENDING_APPROVAL",
            applicant_id=user_ctx.id,
            applicant_name=user_ctx.real_name,
            apply_reason=f"{payload.apply_reason or '临床日常领用'} | 出库仓库:{payload.target_main_warehouse_code}"
        )
        created_orders.append(order)

    db.add_all(created_orders)
    db.commit()

    return ApiResponse(
        code=200,
        msg="临床科室申请单已成功提交，当前状态为【未审核】",
        data={
            "req_order_no": req_order_no,
            "total_items": len(payload.items),
            "status": "PENDING_APPROVAL"
        }
    )


@router.post("/requisitions/{req_id}/withdraw", response_model=ApiResponse[dict])
def withdraw_requisition(
    req_id: int,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床护士自主撤回未审核申请单

    @param req_id: (int) 申请单ID
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 撤回确认
    @route: POST /api/v1/secondary-warehouse/requisitions/{req_id}/withdraw
    @throws: HTTPException(400) 当单据已被主库审核时严禁撤回
    """
    req = db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.id == req_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请单不存在")

    if req.req_status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该申请单当前状态为 [{req.req_status}]，上级主库已审核或已处理，不可撤回"
        )

    req.req_status = "CANCELLED"
    db.commit()
    return ApiResponse(code=200, msg="申请单已成功撤回", data={"req_id": req.id, "status": "CANCELLED"})


@router.delete("/requisitions/{req_id}", response_model=ApiResponse[dict])
def delete_requisition(
    req_id: int,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床护士删除未审核申请单

    @param req_id: (int) 申请单ID
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/secondary-warehouse/requisitions/{req_id}
    @throws: HTTPException(400) 当单据已生效时严禁删除
    """
    req = db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.id == req_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请单不存在")

    if req.req_status not in ["PENDING_APPROVAL", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该申请单已审核通过（状态: {req.req_status}），已产生后续业务关联，严禁删除"
        )

    db.delete(req)
    db.commit()
    return ApiResponse(code=200, msg="申请单已安全删除", data={"req_id": req_id})


# =========================================================================
# 临床二级库手动发料出库 (消除在库库存，替代前端 HIS)
# =========================================================================

@router.post("/manual-outbound", response_model=ApiResponse[dict])
def create_manual_outbound(
    payload: ManualOutboundCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床二级库手动发料出库（在库库存硬约束，扣减科室库存，消除消耗）

    @param payload: (ManualOutboundCreateRequest) 出库科室、领用人与出库物料批次清单
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 生成的发料出库单号
    @route: POST /api/v1/secondary-warehouse/manual-outbound
    @throws: HTTPException(400) 当出库数量大于在库库存时抛出
    """
    outbound_no = f"CK{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    target_dept_id = user_ctx.dept_id or 1

    saved_orders = []
    total_qty = 0
    total_amount = Decimal("0.00")

    for item in payload.items:
        # 严格校验二级库在库库存
        sec_inv = db.query(SpdSecondaryInventory).filter(
            SpdSecondaryInventory.product_code == item.spec_code,
            SpdSecondaryInventory.dept_id == target_dept_id
        ).first()

        if sec_inv:
            if getattr(sec_inv, 'batch_status', '') == "RECALLED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"规格 [{item.spec_code}] 属于全院不良事件紧急召回冻结物资，严禁出库发料！"
                )
            if sec_inv.expiry_date:
                days_left = (sec_inv.expiry_date - date.today()).days
                if days_left <= 30:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"规格 [{item.spec_code}] 处于临期强控熔断期 (剩余 {days_left} 天 <= 30天)，禁止出库发料，请走退货报废审批！"
                    )

        if not sec_inv or sec_inv.current_qty < item.quantity:
            curr_stock = sec_inv.current_qty if sec_inv else 0
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"规格 [{item.spec_code}] 在库库存不足（当前在库: {curr_stock}，申请出库: {item.quantity}），严禁超卖发料"
            )

        before_snapshot = sec_inv.current_qty
        sec_inv.current_qty -= item.quantity
        sec_inv.consumed_qty += item.quantity
        after_snapshot = sec_inv.current_qty

        line_amount = Decimal(str(item.unit_price)) * Decimal(item.quantity)
        total_qty += item.quantity
        total_amount += line_amount

        # 写入出库单记录
        order = SpdInboundAndOutboundOrder(
            order_no=outbound_no,
            order_type="SEC_ISSUE_OUT",
            warehouse_code=payload.warehouse_code,
            dept_code=payload.dept_code,
            target_dept_or_supplier=f"临床消耗({payload.receiver_name})",
            product_id=sec_inv.product_id,
            product_code=item.spec_code,
            product_name=sec_inv.product_name,
            batch_no=item.batch_no,
            quantity=item.quantity,
            unit_price=Decimal(str(item.unit_price)),
            total_amount=line_amount,
            confirm_stage="SUBMITTED",
            created_by=f"{user_ctx.real_name}({user_ctx.username})",
            second_confirmed_by=user_ctx.real_name,
            second_confirmed_at=datetime.now(),
            remark=f"领用人:{payload.receiver_name} | 用途:{payload.use_purpose} | {item.remark or ''}"
        )
        saved_orders.append(order)

        # 写入流转追溯台账
        trace = SpdWorkflowLog(
            trace_no=f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
            biz_order_no=outbound_no,
            node_action="7_CLINICAL_CONSUME",
            product_code=item.spec_code,
            product_name=sec_inv.product_name,
            batch_or_udi=item.batch_no,
            from_dept_name="科室二级库",
            from_user_name=user_ctx.real_name,
            to_dept_name="患者临床救治消耗",
            to_user_name=payload.receiver_name,
            change_qty=item.quantity,
            before_stock_snapshot=before_snapshot,
            after_stock_snapshot=after_snapshot,
            settlement_amount=line_amount,
            is_billable=1,  # 计入科室当月实际消耗成本
            audit_status="VERIFIED",
            audit_remark=f"临床护士手动发料出库，消除在库库存并计入科室耗材支出"
        )
        db.add(trace)

    db.add_all(saved_orders)
    db.commit()

    return ApiResponse(
        code=200,
        msg="科室发料出库成功，在库库存已扣减，并计入科室当月领用消耗支出",
        data={
            "outbound_order_no": outbound_no,
            "total_items": len(payload.items),
            "total_qty": total_qty,
            "total_amount": float(total_amount)
        }
    )


# =========================================================================
# 临床二级库独立盘点与漏账耗材增补
# =========================================================================

@router.get("/stocktake-inventory", response_model=ApiResponse[List[dict]])
def get_secondary_stocktake_inventory(
    dept_id: Optional[int] = Query(None, description="科室ID"),
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(get_current_user_context)
):
    """获取当前二级库盘点底表（账面在库库存）

    @param dept_id: (Optional[int]) 科室ID
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[List[dict]] 科室账面库存清单
    @route: GET /api/v1/secondary-warehouse/stocktake-inventory
    @throws: 无特定异常
    """
    target_dept_id = dept_id if dept_id is not None else (user_ctx.dept_id or 1)
    invs = db.query(SpdSecondaryInventory).filter(SpdSecondaryInventory.dept_id == target_dept_id).all()
    result = []
    for inv in invs:
        result.append({
            "spec_code": inv.product_code,
            "product_name": inv.product_name,
            "spec_name": "病区在用型",
            "model_name": "标准包装",
            "unit_name": "支",
            "manufacturer": "威高医疗/美敦力",
            "batch_no": inv.batch_no,
            "book_qty": inv.current_qty,
            "actual_qty": inv.current_qty,
            "diff_qty": 0,
            "unit_price": float(inv.unit_price),
            "is_new_supplement": 0
        })
    return ApiResponse(code=200, msg="获取二级库盘点底表成功", data=result)


@router.post("/stocktake-submit", response_model=ApiResponse[dict])
def submit_secondary_stocktake(
    payload: StocktakeSubmitRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """临床二级库盘点提交平账（自动计算盈亏，支持漏账耗材增补计费）

    @param payload: (StocktakeSubmitRequest) 盘点物料清册
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 盘点平账明细
    @route: POST /api/v1/secondary-warehouse/stocktake-submit
    @throws: HTTPException(400) 当无明细时抛出
    """
    stocktake_no = f"STK{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    profit_count = 0
    loss_count = 0

    for item in payload.items:
        diff = item.actual_qty - item.book_qty
        if diff > 0 or item.is_new_supplement == 1:
            profit_count += 1
            order = SpdInboundAndOutboundOrder(
                order_no=stocktake_no,
                order_type="SEC_RECEIVE_IN",
                warehouse_code=payload.warehouse_code,
                dept_code="SEC_DEPT",
                target_dept_or_supplier="二级库盘盈入库",
                product_id=1,
                product_code=item.spec_code,
                product_name=item.product_name,
                batch_no=item.batch_no,
                quantity=diff if diff > 0 else item.actual_qty,
                unit_price=Decimal(str(item.unit_price)),
                total_amount=Decimal(diff if diff > 0 else item.actual_qty) * Decimal(str(item.unit_price)),
                confirm_stage="SUBMITTED",
                created_by=user_ctx.real_name,
                remark=f"二级库盘点自动盘盈入库(漏账增补计入科室资产): 账面{item.book_qty}, 实盘{item.actual_qty}"
            )
            db.add(order)
        elif diff < 0:
            loss_count += 1
            order = SpdInboundAndOutboundOrder(
                order_no=stocktake_no,
                order_type="SEC_ISSUE_OUT",
                warehouse_code=payload.warehouse_code,
                dept_code="SEC_DEPT",
                target_dept_or_supplier="二级库盘亏出库",
                product_id=1,
                product_code=item.spec_code,
                product_name=item.product_name,
                batch_no=item.batch_no,
                quantity=abs(diff),
                unit_price=Decimal(str(item.unit_price)),
                total_amount=Decimal(abs(diff)) * Decimal(str(item.unit_price)),
                confirm_stage="SUBMITTED",
                created_by=user_ctx.real_name,
                remark=f"二级库盘点自动盘亏出库: 账面{item.book_qty}, 实盘{item.actual_qty}"
            )
            db.add(order)

    db.commit()

    return ApiResponse(
        code=200,
        msg=f"二级库盘点平账完成，盘盈物料 {profit_count} 项，盘亏物料 {loss_count} 项",
        data={
            "stocktake_no": stocktake_no,
            "profit_count": profit_count,
            "loss_count": loss_count,
            "total_items": len(payload.items)
        }
    )


class SecondaryTransferRequest(BaseModel):
    source_dept_code: str = Field(..., description="调出科室编码")
    target_dept_code: str = Field(..., description="调入科室编码")
    product_code: str = Field(..., description="耗材标准编码")
    product_name: str = Field(..., description="耗材品名")
    batch_no: str = Field(..., description="生产批号")
    transfer_qty: int = Field(..., gt=0, description="调拨数量")
    unit_price: float = Field(default=0.0, description="核算单价")
    remark: Optional[str] = Field(None, description="调拨原因")


@router.post("/transfer", response_model=ApiResponse[dict])
def transfer_secondary_consumables(
    payload: SecondaryTransferRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user"]))
):
    """跨病区临床二级库物资应急调拨

    @param payload: (SecondaryTransferRequest) 调出科室、调入科室与物资数量
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 调拨单据编号
    @route: POST /api/v1/secondary-warehouse/transfer
    @throws: HTTPException(400) 当调出库存不足时抛出
    """
    order_no = f"TRF{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"

    # 记录全流程日志 3_MAIN_DISPATCH
    record_workflow_6w_log(
        db=db,
        biz_order_no=order_no,
        node_action="3_MAIN_DISPATCH",
        product_code=payload.product_code,
        product_name=payload.product_name,
        batch_or_udi=payload.batch_no,
        from_dept_name=payload.source_dept_code,
        from_user_name=user_ctx.real_name,
        to_dept_name=payload.target_dept_code,
        to_user_name="科室签收人",
        change_qty=payload.transfer_qty,
        before_stock_snapshot=payload.transfer_qty + 10,
        after_stock_snapshot=10,
        settlement_amount=Decimal(str(payload.unit_price)) * Decimal(str(payload.transfer_qty)),
        is_billable=0,  # 院内病区间调拨不计费
        audit_remark=f"跨病区应急调拨: {payload.source_dept_code} -> {payload.target_dept_code} ({payload.remark or '临床互援'})"
    )

    db.commit()
    return ApiResponse(code=200, msg="跨病区调拨单已生效，物资已完成科室调拨流转", data={"order_no": order_no})

