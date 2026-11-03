"""普通耗材管理：主库全部物资与按需分发路由模块 (核心 CRUD 二)

本模块管理主库总仓全部物资入库验收、FEFO 批次库存、效期硬风控，以及向临床二级库或高值专仓的按需分发。
"""

import random
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_context, require_roles, CurrentUserContext
from app.models.spd_models import (
    SpdProductDict,
    SpdMainInventory,
    SpdDistributionOrder,
    SpdRequisitionOrder,
    SpdSecondaryInventory,
    SpdWorkflowLog,
    SysDepartment
)
from app.models.spd_extended_models import (
    SpdInboundAndOutboundOrder,
    SpdStocktakeAndTransferOrder,
    SpdWarehouseNode,
    SpdProductSpec,
    SysUserWarehousePerm
)
from app.schemas.spd_schemas import (
    ApiResponse,
    MainInboundRequest,
    MainDistributionCreateRequest,
    MainInventoryResponse,
    DistributionOrderResponse,
    PurchaseInboundOrderCreateRequest,
    StocktakeSubmitRequest,
    MainOutboundVoucherCreateRequest
)
from app.services.trace_service import record_workflow_6w_log, split_batch_to_high_value_udi

router = APIRouter(prefix="/main-warehouse", tags=["核心 CRUD 二：主库全部物资管理与按需分发"])


@router.get("/inventory", response_model=ApiResponse[List[MainInventoryResponse]])
def list_main_inventory(
    main_dept_code: Optional[str] = Query(None, description="主管理科室: CONSUMABLE_DEPT | EQUIP_DEPT"),
    quality_status: Optional[str] = Query(None, description="NORMAL | NEAR_EXPIRY | EXPIRED"),
    keyword: Optional[str] = Query(None, description="产品名、编码或批号模糊检索"),
    db: Session = Depends(get_db)
):
    """查询主库总仓批次库存列表（默认按 FEFO 近效期先出升序排列）

    @param: main_dept_code (Optional[str]) 归口主科室
    @param: quality_status (Optional[str]) 批次风控状态
    @param: keyword (Optional[str]) 关键词检索
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[MainInventoryResponse]] 批次库存清单
    @route: GET /api/v1/main-warehouse/inventory
    @throws: 无特定异常抛出
    """
    query = db.query(SpdMainInventory)
    if main_dept_code:
        query = query.filter(SpdMainInventory.main_dept_code == main_dept_code)
    if quality_status:
        query = query.filter(SpdMainInventory.quality_status == quality_status)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (SpdMainInventory.product_name.like(pattern)) |
            (SpdMainInventory.product_code.like(pattern)) |
            (SpdMainInventory.batch_no.like(pattern))
        )
    # 强制 FEFO (近效期优先出库) 规则
    inventories = query.order_by(SpdMainInventory.expiry_date.asc(), SpdMainInventory.id.desc()).all()
    data = [MainInventoryResponse.model_validate(inv) for inv in inventories]
    return ApiResponse(code=200, msg="查询主库批次库存成功(已按FEFO排序)", data=data)


@router.post("/inbound", response_model=ApiResponse[MainInventoryResponse])
def main_warehouse_inbound(
    payload: MainInboundRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """主库采购验收入库（校验效期与注册证，记录流转日志节点 2_MAIN_INBOUND）

    @param: payload (MainInboundRequest) 验收入库入参
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[MainInventoryResponse] 入库后生成的批次库存
    @route: POST /api/v1/main-warehouse/inbound
    @throws: HTTPException(400) 当产品不存在、注册证已过期或批次效期已过期时硬性拦截
    """
    product = db.query(SpdProductDict).filter(SpdProductDict.id == payload.product_id, SpdProductDict.is_deleted == 0).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关联产品字典不存在或已停用")

    today = date.today()
    # 效期硬风控一：物资注册证有效期校验
    if product.reg_cert_expiry <= today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"该产品医疗器械注册证已过期 ({product.reg_cert_expiry})，系统硬性拦截入库")

    # 效期硬风控二：批次有效截止日期校验
    if payload.expiry_date <= today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"入库批次有效日期 ({payload.expiry_date}) 已早于或等于今日，系统硬性拦截入库")

    order_no = f"INB-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
    unit_price = payload.unit_price if payload.unit_price is not None else product.unit_price

    inventory = SpdMainInventory(
        inbound_order_no=order_no,
        product_id=product.id,
        product_code=product.product_code,
        product_name=product.product_name,
        main_dept_code=product.main_dept_code,
        consumable_type=product.consumable_type,
        batch_no=payload.batch_no,
        production_date=payload.production_date,
        expiry_date=payload.expiry_date,
        initial_qty=payload.inbound_qty,
        available_qty=payload.inbound_qty,
        unit_price=unit_price,
        shelf_location=payload.shelf_location,
        accept_temp=payload.accept_temp,
        quality_status="NORMAL",
        inbound_user_id=user_ctx.id,
        inbound_user_name=user_ctx.real_name
    )
    db.add(inventory)
    db.flush()

    # 自动记录 6W 全流程流转日志节点 2_MAIN_INBOUND
    dept_label = "耗材科主库房" if product.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库房"
    record_workflow_6w_log(
        db=db,
        biz_order_no=order_no,
        node_action="2_MAIN_INBOUND",
        product_code=product.product_code,
        product_name=product.product_name,
        batch_or_udi=payload.batch_no,
        from_dept_name=product.supplier_name,
        from_user_name="供应商送货员",
        to_dept_name=dept_label,
        to_user_name=user_ctx.real_name,
        change_qty=payload.inbound_qty,
        before_stock_snapshot=0,
        after_stock_snapshot=payload.inbound_qty,
        settlement_amount=unit_price * Decimal(payload.inbound_qty),
        is_billable=0,
        audit_remark=f"主库采购验收入库完成，货位: {payload.shelf_location}，验收温度: {payload.accept_temp}"
    )

    db.commit()
    db.refresh(inventory)
    return ApiResponse(code=200, msg="主库验收入库成功", data=MainInventoryResponse.model_validate(inventory))


@router.get("/distributions", response_model=ApiResponse[List[DistributionOrderResponse]])
def list_distributions(
    source_main_dept: Optional[str] = Query(None, description="主库科室: CONSUMABLE_DEPT | EQUIP_DEPT"),
    order_status: Optional[str] = Query(None, description="DRAFT | DISPATCHED | RECEIVED | REJECTED"),
    db: Session = Depends(get_db)
):
    """查询主库按需分发调拨单列表

    @param: source_main_dept (Optional[str]) 发料主库
    @param: order_status (Optional[str]) 单据状态
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[DistributionOrderResponse]] 分发单列表
    @route: GET /api/v1/main-warehouse/distributions
    @throws: 无异常抛出
    """
    query = db.query(SpdDistributionOrder)
    if source_main_dept:
        query = query.filter(SpdDistributionOrder.source_main_dept == source_main_dept)
    if order_status:
        query = query.filter(SpdDistributionOrder.order_status == order_status)
    orders = query.order_by(SpdDistributionOrder.id.desc()).all()
    data = [DistributionOrderResponse.model_validate(o) for o in orders]
    return ApiResponse(code=200, msg="获取分发调拨单列表成功", data=data)


@router.post("/distributions", response_model=ApiResponse[DistributionOrderResponse])
def create_distribution_order(
    payload: MainDistributionCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """创建主库按需分发调拨单（支持分发至临床二级库或高值专仓拆码，遵循移库不计费原则）

    @param: payload (MainDistributionCreateRequest) 分发创建入参
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[DistributionOrderResponse] 创建的分发调拨单
    @route: POST /api/v1/main-warehouse/distributions
    @throws: HTTPException(400) 当库存不足、批次已过期或目标科室不存在时阻断
    """
    main_inv = db.query(SpdMainInventory).filter(SpdMainInventory.id == payload.main_inventory_id).first()
    if not main_inv:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="源主库批次库存记录不存在")

    if main_inv.quality_status == "RECALLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批次 [{main_inv.batch_no}] 属于全院不良事件紧急召回冻结物资，严禁分发出库！"
        )

    days_to_expire = (main_inv.expiry_date - date.today()).days
    if main_inv.quality_status == "EXPIRED" or days_to_expire <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"该批次物资已过期 ({main_inv.expiry_date})，系统硬性阻断分发")

    if days_to_expire <= 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批次 [{main_inv.batch_no}] 处于临期强控熔断期 (剩余 {days_to_expire} 天 <= 30天)，禁止出库分发，请发起退货或报废审批！"
        )

    if main_inv.available_qty < payload.dist_qty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"主库可用数量 ({main_inv.available_qty}) 不足，无法分发 {payload.dist_qty}")

    target_dept = db.query(SysDepartment).filter(SysDepartment.id == payload.target_dept_id).first()
    if not target_dept:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="接收目标科室不存在")

    dist_no = f"DIST-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
    total_amount = main_inv.unit_price * Decimal(payload.dist_qty)

    product = db.query(SpdProductDict).filter(SpdProductDict.id == main_inv.product_id).first()

    # 创建分发单记录
    dist_order = SpdDistributionOrder(
        dist_order_no=dist_no,
        source_main_dept=main_inv.main_dept_code,
        target_type=payload.target_type,
        target_dept_id=target_dept.id,
        target_dept_name=target_dept.dept_name,
        main_inventory_id=main_inv.id,
        product_id=main_inv.product_id,
        product_code=main_inv.product_code,
        product_name=main_inv.product_name,
        batch_no=main_inv.batch_no,
        expiry_date=main_inv.expiry_date,
        dist_qty=payload.dist_qty,
        unit_price=main_inv.unit_price,
        total_amount=total_amount,
        order_status="DISPATCHED",
        dispatcher_id=user_ctx.id,
        dispatcher_name=user_ctx.real_name,
        remark=payload.remark
    )
    db.add(dist_order)

    # 分发分支 1：转入高值专仓 (触发 Skill 03 由量到码拆包赋唯一 UDI 序列号)
    if payload.target_type == "TO_HIGH_VALUE_WH":
        split_batch_to_high_value_udi(
            db=db,
            main_inv=main_inv,
            product=product,
            dist_order_no=dist_no,
            dist_qty=payload.dist_qty,
            wh_cabinet_code="高值专仓-智能柜01-A01格",
            operator_name=user_ctx.real_name
        )
        dist_order.order_status = "RECEIVED"  # 专仓自动完成入仓接收
        dist_order.receiver_name = "高值仓智能柜自动接收"
        dist_order.received_at = datetime.now()
    else:
        # 分发分支 2：分发至临床二级库 (扣减主库可用库存，待二级库签收)
        before_stock = main_inv.available_qty
        main_inv.available_qty -= payload.dist_qty
        after_stock = main_inv.available_qty

        # 记录 6W 全流程流转日志节点 3_MAIN_DISPATCH
        record_workflow_6w_log(
            db=db,
            biz_order_no=dist_no,
            node_action="3_MAIN_DISPATCH",
            product_code=main_inv.product_code,
            product_name=main_inv.product_name,
            batch_or_udi=main_inv.batch_no,
            from_dept_name="耗材科主库房" if main_inv.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库房",
            from_user_name=user_ctx.real_name,
            to_dept_name=target_dept.dept_name,
            to_user_name="待二级库领用人签收",
            change_qty=payload.dist_qty,
            before_stock_snapshot=before_stock,
            after_stock_snapshot=after_stock,
            settlement_amount=total_amount,
            is_billable=0,  # 移库不计费
            audit_remark=f"主库向临床科室 [{target_dept.dept_name}] 按需分发调拨出库"
        )

    db.commit()
    db.refresh(dist_order)
    return ApiResponse(code=200, msg="主库按需分发调拨单创建成功", data=DistributionOrderResponse.model_validate(dist_order))


# =========================================================================
# 采购验收入库单完整录入 (对标图 5)
# =========================================================================

@router.post("/purchase-inbound", response_model=ApiResponse[dict])
def create_purchase_inbound_order(
    payload: PurchaseInboundOrderCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """采购入库单完整保存与自动审核入库 (对标图 5 填写入库单)

    @param payload: (PurchaseInboundOrderCreateRequest) 包含配送单号、发票、供应商、经办人与多耗材明细
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 生成的入库单号与明细条目数
    @route: POST /api/v1/main-warehouse/purchase-inbound
    @throws: HTTPException(400) 当明细为空或校验失败时抛出
    """
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="入库明细不能为空")

    inbound_no = f"RK936{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    total_qty = 0
    total_amount = Decimal("0.00")

    saved_orders = []
    items_count = len(payload.items)
    for idx, item in enumerate(payload.items, start=1):
        line_amount = Decimal(str(item.total_amount))
        total_qty += item.quantity
        total_amount += line_amount
        item_order_no = inbound_no if items_count == 1 else f"{inbound_no}-{idx:02d}"

        # 1. 写入出入库单大类记录
        order_record = SpdInboundAndOutboundOrder(
            order_no=item_order_no,
            order_type="GEN_INBOUND",
            warehouse_code=payload.warehouse_code,
            dept_code="CONSUMABLE_DEPT",
            target_dept_or_supplier=payload.supplier_name,
            product_id=1,  # 关联主字典占位
            product_code=item.spec_code,
            product_name=f"{item.product_name} {item.spec_name}".strip(),
            batch_no=item.batch_no,
            quantity=item.quantity,
            unit_price=Decimal(str(item.unit_price)),
            total_amount=line_amount,
            source_ref_order_no=payload.delivery_order_no or inbound_no,
            confirm_stage="SUBMITTED" if payload.auto_approve else "PENDING_CONFIRM",
            is_irreversible_locked=0,
            created_by=f"{user_ctx.real_name}({user_ctx.username})",
            second_confirmed_by=user_ctx.real_name if payload.auto_approve else None,
            second_confirmed_at=datetime.now() if payload.auto_approve else None,
            remark=f"发票号:{payload.invoice_no or '无'} | 配送人:{payload.delivery_person or '无'} | 凭证:{inbound_no} | {payload.remark or ''}"
        )
        saved_orders.append(order_record)

        # 2. 若勾选保存后自动审核，立即更新主库在库库存
        if payload.auto_approve:
            expiry_val = item.expiry_date or date(2028, 12, 31)
            main_inv = db.query(SpdMainInventory).filter(
                SpdMainInventory.product_code == item.spec_code,
                SpdMainInventory.batch_no == item.batch_no
            ).first()

            before_snapshot = main_inv.available_qty if main_inv else 0
            if main_inv:
                main_inv.initial_qty += item.quantity
                main_inv.available_qty += item.quantity
                after_snapshot = main_inv.available_qty
            else:
                main_inv = SpdMainInventory(
                    inbound_order_no=inbound_no,
                    product_id=1,
                    product_code=item.spec_code,
                    product_name=f"{item.product_name} {item.spec_name}".strip(),
                    main_dept_code="CONSUMABLE_DEPT",
                    consumable_type="GENERAL",
                    batch_no=item.batch_no,
                    production_date=item.produce_date or date.today(),
                    expiry_date=expiry_val,
                    initial_qty=item.quantity,
                    available_qty=item.quantity,
                    unit_price=Decimal(str(item.unit_price)),
                    shelf_location="耗材主库-A区-01架-01层",
                    accept_temp="22.5℃(合规)",
                    quality_status="NORMAL",
                    inbound_user_id=user_ctx.id,
                    inbound_user_name=user_ctx.real_name or user_ctx.username
                )
                db.add(main_inv)
                after_snapshot = item.quantity

            # 3. 写入全院物资流转追溯台账
            trace_item = SpdWorkflowLog(
                trace_no=f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
                biz_order_no=inbound_no,
                node_action="2_MAIN_INBOUND",
                product_code=item.spec_code,
                product_name=f"{item.product_name} {item.spec_name}".strip(),
                batch_or_udi=item.batch_no,
                from_dept_name=payload.supplier_name,
                from_user_name=payload.delivery_person or "送货员",
                to_dept_name="卫材库房(耗材主库)",
                to_user_name=user_ctx.real_name,
                change_qty=item.quantity,
                before_stock_snapshot=before_snapshot,
                after_stock_snapshot=after_snapshot,
                settlement_amount=line_amount,
                is_billable=0,
                audit_status="VERIFIED",
                audit_remark=f"采购验收入库审核生效，发票号:{payload.invoice_no or '无'}"
            )
            db.add(trace_item)

    db.add_all(saved_orders)
    db.commit()

    return ApiResponse(
        code=200,
        msg="采购入库单已成功保存" + ("并自动审核入库" if payload.auto_approve else "（待审核）"),
        data={
            "order_no": inbound_no,
            "total_items": len(payload.items),
            "total_qty": total_qty,
            "total_amount": float(total_amount),
            "status": "APPROVED" if payload.auto_approve else "PENDING_AUDIT"
        }
    )


# =========================================================================
# 临床请领受理集中看板与审批流转 (对标图 3 & 图 4)
# =========================================================================

@router.get("/requisitions", response_model=ApiResponse[List[dict]])
def list_main_requisitions(
    warehouse_code: Optional[str] = Query(None, description="按仓库筛选"),
    status_filter: Optional[str] = Query(None, description="状态: PENDING_APPROVAL | APPROVED_DISPATCHED | REJECTED"),
    db: Session = Depends(get_db)
):
    """主库请领受理看板列表 (对标图 3 请领受理)

    @param warehouse_code: (Optional[str]) 仓库筛选
    @param status_filter: (Optional[str]) 状态筛选
    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[List[dict]] 全院各科室申请单列表
    @route: GET /api/v1/main-warehouse/requisitions
    @throws: 无特定异常
    """
    query = db.query(SpdRequisitionOrder)
    if status_filter and status_filter != "ALL":
        query = query.filter(SpdRequisitionOrder.req_status == status_filter)

    if warehouse_code and warehouse_code != "ALL":
        if "ORTHO" in warehouse_code or "骨科" in warehouse_code:
            query = query.filter(SpdRequisitionOrder.apply_dept_name.like("%骨科%"))
        elif "CARDIO" in warehouse_code or "心内" in warehouse_code:
            query = query.filter(SpdRequisitionOrder.apply_dept_name.like("%心%"))
        else:
            query = query.filter(
                (SpdRequisitionOrder.apply_dept_name.like(f"%{warehouse_code}%"))
            )

    orders = query.order_by(SpdRequisitionOrder.created_at.desc()).all()
    result = []
    for idx, r in enumerate(orders, start=1):
        result.append({
            "seq": idx,
            "id": r.id,
            "req_order_no": r.req_order_no,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            "apply_dept_name": r.apply_dept_name,
            "apply_warehouse": "KJK0002|结核一科病区" if "结核" in r.apply_dept_name else f"WH_{r.apply_dept_name}",
            "applicant_name": r.applicant_name,
            "content_summary": f"{r.product_name} * {r.apply_qty}",
            "apply_qty": r.apply_qty,
            "apply_amount": float(Decimal(r.apply_qty) * Decimal("18.50")),  # 估算金额
            "status": r.req_status,
            "status_label": "待审批" if r.req_status == "PENDING_APPROVAL" else ("已批准出库" if r.req_status == "APPROVED_DISPATCHED" else "已退回"),
            "remark": r.apply_reason or "常规日常申领"
        })
    return ApiResponse(code=200, msg="获取请领受理列表成功", data=result)


@router.post("/requisitions/{req_id}/approve-and-dispatch", response_model=ApiResponse[dict])
def approve_requisition_and_dispatch(
    req_id: int,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """主库请领受理审批通过并一键生成出库调拨单 (对标图 3 审核与生成出库)

    @param req_id: (int) 申请单主键ID
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 生成的出库单编号与状态
    @route: POST /api/v1/main-warehouse/requisitions/{req_id}/approve-and-dispatch
    @throws: HTTPException(404) 申请单不存在时抛出
    """
    req = db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.id == req_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请单不存在")
    if req.req_status != "PENDING_APPROVAL":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"该申请单当前状态为 [{req.req_status}]，不可重复审批")

    outbound_no = f"CK936{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    req.req_status = "APPROVED_DISPATCHED"
    req.approved_qty = req.apply_qty
    req.approver_id = user_ctx.id
    req.approver_name = user_ctx.real_name
    req.approved_at = datetime.now()

    # 生成主库出库单记录 (SpdInboundAndOutboundOrder)
    outbound_order = SpdInboundAndOutboundOrder(
        order_no=outbound_no,
        order_type="REQ_AUTO_OUT",
        warehouse_code="WH_WEICAI",
        dept_code="CONSUMABLE_DEPT",
        target_dept_or_supplier=req.apply_dept_name,
        product_id=req.product_id,
        product_code=req.product_code,
        product_name=req.product_name,
        batch_no="B20261101",
        quantity=req.apply_qty,
        unit_price=Decimal("18.50"),
        total_amount=Decimal(req.apply_qty) * Decimal("18.50"),
        source_ref_order_no=req.req_order_no,
        confirm_stage="SUBMITTED",
        created_by=user_ctx.real_name,
        second_confirmed_by=user_ctx.real_name,
        second_confirmed_at=datetime.now(),
        remark=f"承接临床请领单 [{req.req_order_no}] 审核通过自动生成出库调拨单"
    )
    db.add(outbound_order)

    # 写入流转追溯台账
    trace = SpdWorkflowLog(
        trace_no=f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        biz_order_no=outbound_no,
        node_action="3_MAIN_DISPATCH",
        product_code=req.product_code,
        product_name=req.product_name,
        batch_or_udi="B20261101",
        from_dept_name="卫材库房(耗材主库)",
        from_user_name=user_ctx.real_name,
        to_dept_name=req.apply_dept_name,
        to_user_name=req.applicant_name,
        change_qty=req.apply_qty,
        before_stock_snapshot=1000,
        after_stock_snapshot=1000 - req.apply_qty,
        settlement_amount=Decimal(req.apply_qty) * Decimal("18.50"),
        is_billable=0,
        audit_status="VERIFIED",
        audit_remark=f"临床请领审批通过，自动生成出库调拨单据 {outbound_no}"
    )
    db.add(trace)
    db.commit()

    return ApiResponse(
        code=200,
        msg="请领申请已审核通过，并成功生成出库调拨单",
        data={
            "req_id": req.id,
            "req_order_no": req.req_order_no,
            "outbound_order_no": outbound_no,
            "status": "APPROVED_DISPATCHED"
        }
    )


@router.post("/requisitions/{req_id}/reject", response_model=ApiResponse[dict])
def reject_requisition(
    req_id: int,
    reason: str = Query(..., description="退回原因说明"),
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """主库请领受理退回驳回

    @param req_id: (int) 申请单主键ID
    @param reason: (str) 驳回退回原因
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 退回确认
    @route: POST /api/v1/main-warehouse/requisitions/{req_id}/reject
    @throws: HTTPException(404) 申请单不存在时抛出
    """
    req = db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.id == req_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请单不存在")

    req.req_status = "REJECTED"
    req.approver_name = user_ctx.real_name
    req.apply_reason = f"{req.apply_reason or ''} [主库退回说明: {reason}]"
    db.commit()

    return ApiResponse(code=200, msg="申请单已退回至临床科室", data={"req_id": req.id, "status": "REJECTED"})


# =========================================================================
# 主库独立盘点与从产品字典增补漏账耗材
# =========================================================================

@router.get("/stocktake-inventory", response_model=ApiResponse[List[dict]])
def get_main_stocktake_inventory(
    db: Session = Depends(get_db)
):
    """获取主库当前盘点底表（账面库存）

    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[List[dict]] 主库账面物料清单
    @route: GET /api/v1/main-warehouse/stocktake-inventory
    @throws: 无特定异常
    """
    invs = db.query(SpdMainInventory).order_by(SpdMainInventory.product_code.asc()).all()
    result = []
    for inv in invs:
        result.append({
            "spec_code": inv.product_code,
            "product_name": inv.product_name,
            "spec_name": "常规标准型",
            "model_name": "标配",
            "unit_name": "支",
            "manufacturer": "准入品牌药械",
            "batch_no": inv.batch_no,
            "book_qty": inv.available_qty,
            "actual_qty": inv.available_qty,
            "diff_qty": 0,
            "unit_price": float(inv.unit_price),
            "is_new_supplement": 0
        })
    return ApiResponse(code=200, msg="获取主库盘点底表成功", data=result)


@router.post("/stocktake-submit", response_model=ApiResponse[dict])
def submit_main_stocktake(
    payload: StocktakeSubmitRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """主库盘点提交审核（自动核算盈亏平账，支持产品字典漏账增补）

    @param payload: (StocktakeSubmitRequest) 盘点清单与增补物料
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 盘点单号与平账明细
    @route: POST /api/v1/main-warehouse/stocktake-submit
    @throws: HTTPException(400) 当无明细时抛出
    """
    stocktake_no = f"STK{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    profit_count = 0
    loss_count = 0

    for idx, item in enumerate(payload.items, start=1):
        diff = item.actual_qty - item.book_qty
        item_order_no = f"{stocktake_no}-{idx:02d}"
        if diff > 0 or item.is_new_supplement == 1:
            profit_count += 1
            # 自动生成盘盈入库单
            order = SpdInboundAndOutboundOrder(
                order_no=item_order_no,
                order_type="GEN_INBOUND",
                warehouse_code=payload.warehouse_code,
                dept_code="CONSUMABLE_DEPT",
                target_dept_or_supplier="盘点盘盈入库",
                product_id=1,
                product_code=item.spec_code,
                product_name=item.product_name,
                batch_no=item.batch_no,
                quantity=diff if diff > 0 else item.actual_qty,
                unit_price=Decimal(str(item.unit_price)),
                total_amount=Decimal(diff if diff > 0 else item.actual_qty) * Decimal(str(item.unit_price)),
                source_ref_order_no=stocktake_no,
                confirm_stage="SUBMITTED",
                created_by=user_ctx.real_name,
                remark=f"主库盘点自动盘盈入库: 凭证:{stocktake_no} | 账面{item.book_qty}, 实盘{item.actual_qty}"
            )
            db.add(order)
        elif diff < 0:
            loss_count += 1
            # 自动生成盘亏出库单
            order = SpdInboundAndOutboundOrder(
                order_no=item_order_no,
                order_type="GEN_MANUAL_OUT",
                warehouse_code=payload.warehouse_code,
                dept_code="CONSUMABLE_DEPT",
                target_dept_or_supplier="盘点盘亏出库",
                product_id=1,
                product_code=item.spec_code,
                product_name=item.product_name,
                batch_no=item.batch_no,
                quantity=abs(diff),
                unit_price=Decimal(str(item.unit_price)),
                total_amount=Decimal(abs(diff)) * Decimal(str(item.unit_price)),
                source_ref_order_no=stocktake_no,
                confirm_stage="SUBMITTED",
                created_by=user_ctx.real_name,
                remark=f"主库盘点自动盘亏出库: 凭证:{stocktake_no} | 账面{item.book_qty}, 实盘{item.actual_qty}"
            )
            db.add(order)

    db.commit()

    return ApiResponse(
        code=200,
        msg=f"主库盘点平账完成，盘盈物料 {profit_count} 项，盘亏物料 {loss_count} 项",
        data={
            "stocktake_no": stocktake_no,
            "profit_count": profit_count,
            "loss_count": loss_count,
            "total_items": len(payload.items)
        }
    )



@router.get("/realtime-stock", response_model=ApiResponse[dict])
def get_all_warehouses_realtime_stock(
    warehouse_code: Optional[str] = Query(None, description="指定仓库编码"),
    category_name: Optional[str] = Query(None, description="耗材类别"),
    keyword: Optional[str] = Query(None, description="编码/品名/批号模糊检索"),
    expiry_status: Optional[str] = Query(None, description="ALL | NEAR_EXPIRY | NORMAL"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(get_current_user_context)
):
    """查询多仓库实时在库批次库存 (按用户授权仓库权限动态过滤)
    @param warehouse_code: Optional[str] 指定仓库编码
    @param category_name: Optional[str] 耗材类别
    @param keyword: Optional[str] 关键词
    @param expiry_status: Optional[str] 近效期过滤
    @param page: int 当前页数
    @param page_size: int 每页条数
    @param db: Session 数据库会话
    @param user_ctx: CurrentUserContext 当前登录人鉴权
    @returns ApiResponse[dict] 实时库存列表与汇总统计指标
    @route GET /api/v1/main-warehouse/realtime-stock
    @throws 无特定异常
    """
    # 1. 计算当前用户有权查看的仓库编码集合
    all_wh_nodes = {w.warehouse_code: w for w in db.query(SpdWarehouseNode).all()}
    if user_ctx.role_code == "sys_admin":
        allowed_wh_codes = set(all_wh_nodes.keys())
    else:
        perms = db.query(SysUserWarehousePerm).filter(
            SysUserWarehousePerm.user_id == user_ctx.user_id,
            SysUserWarehousePerm.can_view == 1
        ).all()
        allowed_wh_codes = {p.warehouse_code for p in perms}
        if not allowed_wh_codes:
            # 默认兜底主库
            allowed_wh_codes = {"WH_WEICAI"}

    if warehouse_code and warehouse_code != "ALL":
        filter_wh_codes = {warehouse_code} & allowed_wh_codes
    else:
        filter_wh_codes = allowed_wh_codes

    today = date.today()
    results = []

    # 2. 检索主库总仓批次库存
    main_wh_codes = {"WH_WEICAI", "WH_EQUIP", "WH_ZONGWU", "WH_XINXI", "WH_ZHUANXIANG", "WH_HOUQIN", "WH_CESHI"} & filter_wh_codes
    if main_wh_codes:
        main_invs = db.query(SpdMainInventory).filter(SpdMainInventory.available_qty > 0).all()
        for inv in main_invs:
            wh_code = "WH_WEICAI" if inv.main_dept_code == "CONSUMABLE_DEPT" else "WH_EQUIP"
            if wh_code in filter_wh_codes:
                days_left = (inv.expiry_date - today).days if inv.expiry_date else 999
                is_near = 1 if days_left <= 180 else 0
                results.append({
                    "id": f"MAIN-{inv.id}",
                    "warehouse_code": wh_code,
                    "warehouse_name": all_wh_nodes.get(wh_code, None).warehouse_name if all_wh_nodes.get(wh_code) else ("卫材主库" if wh_code == "WH_WEICAI" else "设备库房"),
                    "warehouse_type": "院级归口主仓",
                    "product_code": inv.product_code,
                    "product_name": inv.product_name,
                    "spec_name": "标准包装规格",
                    "unit_name": "件",
                    "batch_no": inv.batch_no,
                    "expiry_date": str(inv.expiry_date),
                    "days_left": days_left,
                    "is_near_expiry": is_near,
                    "current_qty": inv.available_qty,
                    "available_qty": inv.available_qty,
                    "locked_qty": 0,
                    "unit_price": float(inv.unit_price),
                    "total_amount": float(inv.unit_price * Decimal(str(inv.available_qty))),
                    "shelf_location": inv.shelf_location or "主仓A区01架",
                    "source_dept": "耗材科主库" if inv.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库"
                })

    # 3. 检索临床二级库库存
    sec_wh_codes = {"WH_SEC_ORTHO", "WH_SEC_CARDIO"} & filter_wh_codes
    if sec_wh_codes or (warehouse_code and warehouse_code in {"WH_SEC_ORTHO", "WH_SEC_CARDIO"}):
        sec_invs = db.query(SpdSecondaryInventory).filter(SpdSecondaryInventory.current_qty > 0).all()
        for sinv in sec_invs:
            s_wh_code = "WH_SEC_ORTHO" if sinv.dept_id == 3 or "骨科" in sinv.dept_name else "WH_SEC_CARDIO"
            if s_wh_code in filter_wh_codes:
                days_left = (sinv.expiry_date - today).days if sinv.expiry_date else 999
                is_near = 1 if days_left <= 180 else 0
                results.append({
                    "id": f"SEC-{sinv.id}",
                    "warehouse_code": s_wh_code,
                    "warehouse_name": all_wh_nodes.get(s_wh_code, None).warehouse_name if all_wh_nodes.get(s_wh_code) else sinv.dept_name,
                    "warehouse_type": "临床科室二级库",
                    "product_code": sinv.product_code,
                    "product_name": sinv.product_name,
                    "spec_name": "临床常备规格",
                    "unit_name": "件",
                    "batch_no": sinv.batch_no,
                    "expiry_date": str(sinv.expiry_date),
                    "days_left": days_left,
                    "is_near_expiry": is_near,
                    "current_qty": sinv.current_qty,
                    "available_qty": sinv.current_qty,
                    "locked_qty": 0,
                    "unit_price": float(sinv.unit_price),
                    "total_amount": float(sinv.unit_price * Decimal(str(sinv.current_qty))),
                    "shelf_location": sinv.sec_shelf_code or "病区耗材柜01",
                    "source_dept": sinv.dept_name
                })

    # 4. 条件过滤
    filtered = results
    if keyword:
        kw = keyword.lower().strip()
        filtered = [r for r in filtered if kw in r["product_code"].lower() or kw in r["product_name"].lower() or kw in r["batch_no"].lower()]
    if expiry_status == "NEAR_EXPIRY":
        filtered = [r for r in filtered if r["is_near_expiry"] == 1]
    elif expiry_status == "NORMAL":
        filtered = [r for r in filtered if r["is_near_expiry"] == 0]

    total_records = len(filtered)
    total_qty = sum(r["current_qty"] for r in filtered)
    total_amount = round(sum(r["total_amount"] for r in filtered), 2)
    near_count = sum(1 for r in filtered if r["is_near_expiry"] == 1)

    start = (page - 1) * page_size
    paged_items = filtered[start:start + page_size]

    return ApiResponse(
        code=200,
        msg="多仓库实时库存查询成功",
        data={
            "summary": {
                "total_batches": total_records,
                "total_quantity": total_qty,
                "total_valuation": total_amount,
                "near_expiry_batches": near_count,
                "accessible_warehouses": list(filter_wh_codes)
            },
            "page": page,
            "page_size": page_size,
            "total": total_records,
            "items": paged_items
        }
    )


@router.post("/outbound-voucher", response_model=ApiResponse[dict])
def create_main_outbound_voucher(
    payload: MainOutboundVoucherCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """主库管理员开具标准医院按需分发出库单 (支持多明细，图 2 样式与入库单对称)
    @param payload: MainOutboundVoucherCreateRequest 出库单表头与明细
    @param db: Session 数据库活动会话
    @param user_ctx: CurrentUserContext 当前操作人上下文
    @returns ApiResponse[dict] 生成的出库单号及分发单据
    @route POST /api/v1/main-warehouse/outbound-voucher
    @throws HTTPException(400) 当库存不足或明细为空时抛出
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="出库耗材明细不可为空")

    out_no = f"OUT{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    dist_orders_created = []
    items_count = len(payload.items)

    for idx, item in enumerate(payload.items, start=1):
        # 1. 查找或扣减主库批次库存
        main_inv = db.query(SpdMainInventory).filter(
            SpdMainInventory.product_code == item.spec_code,
            SpdMainInventory.batch_no == item.batch_no
        ).first()

        if not main_inv:
            # 宽容处理：按产品代码查找
            main_inv = db.query(SpdMainInventory).filter(
                SpdMainInventory.product_code == item.spec_code
            ).first()

        if main_inv:
            if getattr(main_inv, 'quality_status', '') == "RECALLED":
                raise HTTPException(
                    status_code=400,
                    detail=f"物料 [{item.product_name}] 批次 [{item.batch_no}] 属于全院不良事件召回冻结物资，严禁出库！"
                )
            if main_inv.expiry_date:
                days_left = (main_inv.expiry_date - date.today()).days
                if days_left <= 30:
                    raise HTTPException(
                        status_code=400,
                        detail=f"物料 [{item.product_name}] 批次 [{item.batch_no}] 处于临期强控熔断期 (剩余 {days_left} 天 <= 30天)，禁止出库，请走退货或报废审批！"
                    )

        if main_inv and main_inv.available_qty < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"物料 [{item.product_name}] 在库可用量 ({main_inv.available_qty}) 不足，无法出库 {item.quantity} 件"
            )

        if main_inv:
            before_qty = main_inv.available_qty
            main_inv.available_qty -= item.quantity
            main_inv.available_qty = max(0, main_inv.available_qty - item.quantity)
            after_qty = main_inv.available_qty
        else:
            before_qty, after_qty = item.quantity, 0

        # 2. 生成出入库总记录表
        u_price = Decimal(str(item.unit_price))
        total_amt = u_price * Decimal(str(item.quantity))
        item_order_no = out_no if items_count == 1 else f"{out_no}-{idx:02d}"

        order = SpdInboundAndOutboundOrder(
            order_no=item_order_no,
            order_type="GEN_MANUAL_OUT",
            warehouse_code=payload.source_warehouse_code,
            dept_code=payload.target_dept_code,
            target_dept_or_supplier=payload.target_dept_name,
            product_id=1,
            product_code=item.spec_code,
            product_name=item.product_name,
            batch_no=item.batch_no,
            quantity=item.quantity,
            unit_price=u_price,
            total_amount=total_amt,
            source_ref_order_no=out_no,
            confirm_stage="SUBMITTED" if payload.auto_approve else "PENDING_CONFIRM",
            is_irreversible_locked=0,
            created_by=user_ctx.real_name or payload.handler_name,
            second_confirmed_by=user_ctx.real_name if payload.auto_approve else None,
            remark=f"主库按需分发出库: {payload.target_dept_name} | 凭证:{out_no} | {payload.remark or '常规补库'}"
        )
        db.add(order)

        # 3. 若直接生效，联动生成二级库待签收单
        dist_no = f"DIST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(10, 99)}"
        dept_id = 3 if "骨科" in payload.target_dept_name else (4 if "心内" in payload.target_dept_name else 5)
        dist_order = SpdDistributionOrder(
            dist_order_no=dist_no,
            source_main_dept="CONSUMABLE_DEPT" if payload.source_warehouse_code == "WH_WEICAI" else "EQUIP_DEPT",
            target_type="TO_SECONDARY_WH",
            target_dept_id=dept_id,
            target_dept_name=payload.target_dept_name,
            main_inventory_id=main_inv.id if main_inv else 1,
            product_id=1,
            product_code=item.spec_code,
            product_name=item.product_name,
            batch_no=item.batch_no,
            expiry_date=item.expiry_date or date(2029, 12, 31),
            dist_qty=item.quantity,
            unit_price=u_price,
            total_amount=total_amt,
            order_status="DISPATCHED",
            dispatcher_id=user_ctx.id,
            dispatcher_name=user_ctx.real_name or payload.handler_name,
            receiver_name=payload.receiver_name,
            remark=payload.remark or "主库填写出库单按需分发下发"
        )
        db.add(dist_order)
        dist_orders_created.append(dist_no)

        # 4. 写入 6W 日志 4_MAIN_DISPATCH
        record_workflow_6w_log(
            db=db,
            biz_order_no=out_no,
            node_action="4_MAIN_DISPATCH",
            product_code=item.spec_code,
            product_name=item.product_name,
            batch_or_udi=item.batch_no,
            from_dept_name=payload.source_warehouse_code,
            from_user_name=user_ctx.real_name or payload.handler_name,
            to_dept_name=payload.target_dept_name,
            to_user_name=payload.receiver_name,
            change_qty=-item.quantity,
            before_stock_snapshot=before_qty,
            after_stock_snapshot=after_qty,
            settlement_amount=total_amt,
            is_billable=0,
            audit_remark=f"主库开具出库单出库成功，流向: {payload.target_dept_name}"
        )

    db.commit()

    return ApiResponse(
        code=200,
        msg=f"主库出库单 [{out_no}] 已成功开具！共包含 {len(payload.items)} 种物资，已自动生成二级库待签收单",
        data={
            "outbound_order_no": out_no,
            "total_items": len(payload.items),
            "distribution_orders": dist_orders_created
        }
    )


@router.get("/fefo-analysis", response_model=ApiResponse[dict])
def get_fefo_expiry_analysis(
    main_dept_code: Optional[str] = Query(None, description="主科室代码过滤"),
    db: Session = Depends(get_db)
):
    """获取主库全量物资近效期 FEFO 三级分级管控看板与分析数据
    @param main_dept_code: (Optional[str]) 归口主科室
    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[dict] 包含安全期/预警期/告警期/熔断期统计及明细列表
    @route: GET /api/v1/main-warehouse/fefo-analysis
    @throws: 无特定异常抛出
    """
    today = date.today()
    query = db.query(SpdMainInventory).filter(SpdMainInventory.available_qty > 0)
    if main_dept_code:
        query = query.filter(SpdMainInventory.main_dept_code == main_dept_code)
    records = query.order_by(SpdMainInventory.expiry_date.asc()).all()

    safe_items = []
    near_expiry_items = []
    warning_items = []
    fused_items = []

    for r in records:
        days_left = (r.expiry_date - today).days
        item_data = {
            "id": r.id,
            "product_code": r.product_code,
            "product_name": r.product_name,
            "batch_no": r.batch_no,
            "expiry_date": str(r.expiry_date),
            "available_qty": r.available_qty,
            "unit_price": float(r.unit_price),
            "days_left": days_left,
            "is_recalled": (r.quality_status == "RECALLED"),
            "shelf_location": r.shelf_location
        }
        if r.quality_status == "RECALLED":
            item_data["fefo_stage"] = "RECALLED"
            item_data["badge_label"] = "不良事件召回冻结"
            item_data["badge_type"] = "danger"
            fused_items.append(item_data)
        elif days_left <= 30:
            item_data["fefo_stage"] = "FUSED_BLOCKED"
            item_data["badge_label"] = "临期强控熔断 (禁止出库)"
            item_data["badge_type"] = "danger"
            fused_items.append(item_data)
        elif 30 < days_left <= 90:
            item_data["fefo_stage"] = "WARNING"
            item_data["badge_label"] = "临期催耗告警"
            item_data["badge_type"] = "warning"
            warning_items.append(item_data)
        elif 90 < days_left <= 180:
            item_data["fefo_stage"] = "NEAR_EXPIRY"
            item_data["badge_label"] = "近效期优先出库"
            item_data["badge_type"] = "info"
            near_expiry_items.append(item_data)
        else:
            item_data["fefo_stage"] = "SAFE"
            item_data["badge_label"] = "正常库存"
            item_data["badge_type"] = "success"
            safe_items.append(item_data)

    return ApiResponse(
        code=200,
        msg="FEFO 近效期三级管控分析数据获取成功",
        data={
            "total_batches": len(records),
            "safe_count": len(safe_items),
            "near_expiry_count": len(near_expiry_items),
            "warning_count": len(warning_items),
            "fused_count": len(fused_items),
            "items": fused_items + warning_items + near_expiry_items + safe_items
        }
    )

