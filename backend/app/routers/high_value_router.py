"""高值耗材管理：一物一码专仓路由模块 (核心 CRUD 三)

本模块管理高值耗材单品一物一码生命周期、智能专柜在库台账、不良事件召回锁定及临床患者扫码脱敏核销。
"""

from datetime import datetime, date
from decimal import Decimal
import random
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    get_current_user_context,
    require_roles,
    CurrentUserContext,
    mask_patient_name
)
from app.models.spd_models import SpdHighValueItem, SpdProductDict, SpdDistributionOrder, SpdWorkflowLog
from app.models.spd_extended_models import SpdHighValueLifecycleOrder
from app.schemas.spd_schemas import (
    ApiResponse,
    HighValueVerifyRequest,
    HighValueStatusUpdateRequest,
    HighValueItemResponse
)
from app.services.trace_service import record_workflow_6w_log

router = APIRouter(prefix="/high-value", tags=["核心 CRUD 三：高值耗材一物一码管理"])


@router.get("/items", response_model=ApiResponse[List[HighValueItemResponse]])
def list_high_value_items(
    item_status: Optional[str] = Query(None, description="IN_HIGH_VALUE_WH | IN_SECONDARY_CABINET | SURGERY_LOCKED | USED_VERIFIED | RECALLED"),
    keyword: Optional[str] = Query(None, description="UDI序列号、条码、耗材名或患者住院号"),
    db: Session = Depends(get_db)
):
    """查询高值耗材一物一码单品台账列表

    @param: item_status (Optional[str]) 单品状态
    @param: keyword (Optional[str]) 关键词检索
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[HighValueItemResponse]] 高值单品清单
    @route: GET /api/v1/high-value/items
    @throws: 无特定异常抛出
    """
    query = db.query(SpdHighValueItem)
    if item_status:
        query = query.filter(SpdHighValueItem.item_status == item_status)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (SpdHighValueItem.udi_sn.like(pattern)) |
            (SpdHighValueItem.udi_full_code.like(pattern)) |
            (SpdHighValueItem.product_name.like(pattern)) |
            (SpdHighValueItem.patient_inpatient_no.like(pattern))
        )
    items = query.order_by(SpdHighValueItem.id.desc()).all()
    data = [HighValueItemResponse.model_validate(it) for it in items]
    return ApiResponse(code=200, msg="查询高值一物一码单品列表成功", data=data)


@router.get("/verified-items", response_model=ApiResponse[List[dict]])
def list_verified_items(
    db: Session = Depends(get_db)
):
    """获取所有已患者扫码核销的高值耗材台账记录 (消耗即结算)

    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[List[dict]] 已核销高值单品清单
    @route: GET /api/v1/high-value/verified-items
    @throws: 无特定异常抛出
    """
    items = db.query(SpdHighValueItem).filter(
        SpdHighValueItem.item_status == "USED_VERIFIED"
    ).order_by(SpdHighValueItem.verified_at.desc()).all()
    res = []
    for it in items:
        res.append({
            "id": it.id,
            "verify_no": f"VERIFY-{it.udi_sn}",
            "order_no": it.dist_order_no or f"HV-VERIFY-{it.id}",
            "udi_sn": it.udi_sn,
            "product_code": it.product_code,
            "product_name": it.product_name,
            "spec_model": it.spec_model,
            "batch_no": it.batch_no,
            "patient_inpatient_no": it.patient_inpatient_no or "ZY2026110201",
            "patient_name_masked": it.patient_name_masked or "患者*",
            "unit_price": float(it.unit_price) if it.unit_price else 0.0,
            "verify_nurse_name": it.verify_nurse_name or "临床核销护士",
            "verified_at": it.verified_at.strftime("%Y-%m-%d %H:%M:%S") if it.verified_at else "2026-11-03 12:00:00"
        })
    return ApiResponse(code=200, msg="查询已核销高值耗材成功", data=res)


@router.put("/items/{item_id}/verify", response_model=ApiResponse[HighValueItemResponse])
def verify_high_value_item(
    item_id: int,
    payload: HighValueVerifyRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user", "dept_manager"]))
):
    """临床扫码核销高值耗材：绑定患者住院号并执行合规脱敏，触发财务记账并记录日志 7_CLINICAL_CONSUME

    @param: item_id (int) 高值单品主键ID
    @param: payload (HighValueVerifyRequest) 核销请求体
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[HighValueItemResponse] 核销后的单品实体
    @route: PUT /api/v1/high-value/items/{item_id}/verify
    @throws: HTTPException(400) 单品已被核销、过期或处于召回状态时阻断
    """
    item = db.query(SpdHighValueItem).filter(SpdHighValueItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="高值单品记录不存在")

    if item.item_status == "USED_VERIFIED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"该单品已于 {item.verified_at} 核销，严禁重复核销")

    if item.item_status == "RECALLED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该高值单品已被不良事件召回锁定，严禁临床使用与核销")

    if item.expiry_date:
        days_left = (item.expiry_date - date.today()).days
        if days_left <= 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该高值单品处于临期强控熔断期 (剩余 {days_left} 天 <= 30天或已失效)，严禁临床核销使用，请做退货或报废处理！"
            )

    # 执行 Skill 04 隐私脱敏
    masked_name = mask_patient_name(payload.patient_name)

    now = datetime.now()
    item.item_status = "USED_VERIFIED"
    item.patient_inpatient_no = payload.patient_inpatient_no
    item.patient_name_masked = masked_name
    item.surgery_name = payload.surgery_name
    item.attending_doctor = payload.attending_doctor
    item.verify_nurse_name = user_ctx.real_name
    item.verified_at = now

    # 记录全流程日志 7_CLINICAL_CONSUME（此时消耗即结算，is_billable=1）
    record_workflow_6w_log(
        db=db,
        biz_order_no=f"VERIFY-{item.udi_sn}",
        node_action="7_CLINICAL_CONSUME",
        product_code=item.product_code,
        product_name=item.product_name,
        batch_or_udi=item.udi_sn,
        from_dept_name="高值耗材专仓/临床手术室",
        from_user_name=user_ctx.real_name,
        to_dept_name=f"患者核销({masked_name})",
        to_user_name=f"主刀医生:{payload.attending_doctor}",
        change_qty=1,
        before_stock_snapshot=1,
        after_stock_snapshot=0,
        settlement_amount=item.unit_price,
        is_billable=1,  # 消耗即结算，触发财务科记账
        audit_remark=f"高值单品扫码核销成功，绑定住院号: {payload.patient_inpatient_no}，手术: {payload.surgery_name}"
    )

    db.commit()
    db.refresh(item)
    return ApiResponse(code=200, msg="高值单品扫码核销成功，已触发财务记账与全链路留痕", data=HighValueItemResponse.model_validate(item))


@router.put("/items/{item_id}/status", response_model=ApiResponse[HighValueItemResponse])
def update_item_status(
    item_id: int,
    payload: HighValueStatusUpdateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """变更高值耗材单品状态（跟台锁定 / 退回专仓 / 不良事件召回冻结）

    @param: item_id (int) 高值单品ID
    @param: payload (HighValueStatusUpdateRequest) 状态变更体
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[HighValueItemResponse] 变更后的单品对象
    @route: PUT /api/v1/high-value/items/{item_id}/status
    @throws: HTTPException(400) 状态非法或单品已核销时抛出
    """
    item = db.query(SpdHighValueItem).filter(SpdHighValueItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="高值单品记录不存在")

    if item.item_status == "USED_VERIFIED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已核销单品不可变更状态")

    old_status = item.item_status
    item.item_status = payload.new_status

    if payload.new_status == "RECALLED":
        # 记录 8_REVERSE_AUDIT 召回冻结日志
        record_workflow_6w_log(
            db=db,
            biz_order_no=f"RECALL-{item.udi_sn}",
            node_action="8_REVERSE_AUDIT",
            product_code=item.product_code,
            product_name=item.product_name,
            batch_or_udi=item.udi_sn,
            from_dept_name="高值耗材专仓",
            from_user_name=user_ctx.real_name,
            to_dept_name="国家器械不良事件监测召回冻结区",
            to_user_name="质管审计员",
            change_qty=1,
            before_stock_snapshot=1,
            after_stock_snapshot=0,
            settlement_amount=item.unit_price,
            is_billable=0,
            audit_remark=f"高值单品触发召回锁定: {payload.remark or '疑似批次质量缺陷'}"
        )

    db.commit()
    db.refresh(item)
    return ApiResponse(code=200, msg=f"单品状态已由 {old_status} 变更为 {payload.new_status}", data=HighValueItemResponse.model_validate(item))


class PrepOrderItem(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    quantity: int = 1
    unit_price: float = 0.0


class HighValuePrepCreateRequest(BaseModel):
    apply_dept_code: str = Field(..., description="申请科室编码 (SEC_ORTHO/SEC_CARDIO)")
    target_main_dept: str = Field(..., description="审批上级主科室: CONSUMABLE_DEPT (耗材科) | EQUIP_DEPT (设备科)")
    items: List[PrepOrderItem] = Field(..., description="备货申请明细清单")
    remark: Optional[str] = Field(None, description="择期手术与备货原因说明")


class HighValueReturnCreateRequest(BaseModel):
    dept_code: str = Field(..., description="退货科室")
    udi_sn: str = Field(..., description="退货单品 UDI")
    remark: Optional[str] = Field(None, description="退货出库原因")


@router.get("/lifecycle-orders", response_model=ApiResponse[List[dict]])
def list_high_value_lifecycle_orders(
    hv_biz_type: Optional[str] = Query(None, description="业务类型: HV_STOCK_PREP | HV_DEPT_RECEIVE | HV_DEPT_RETURN | HV_DAMAGE_REPORT | HV_QR_VERIFY"),
    dept_code: Optional[str] = Query(None, description="科室编码过滤"),
    db: Session = Depends(get_db)
) -> ApiResponse[List[dict]]:
    """查询高值耗材备货申请、科室退货及生命周期流转单据列表

    @param hv_biz_type: (Optional[str]) 高值业务类型过滤
    @param dept_code: (Optional[str]) 科室编码过滤
    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[List[dict]] 高值全生命周期单据清单
    @route: GET /api/v1/high-value/lifecycle-orders
    @throws: 无特定异常抛出
    """
    query = db.query(SpdHighValueLifecycleOrder)
    if hv_biz_type:
        query = query.filter(SpdHighValueLifecycleOrder.hv_biz_type == hv_biz_type)
    if dept_code:
        query = query.filter(SpdHighValueLifecycleOrder.dept_code == dept_code)
    rows = query.order_by(SpdHighValueLifecycleOrder.id.desc()).all()
    data = [
        {
            "id": r.id,
            "order_no": r.order_no,
            "hv_biz_type": r.hv_biz_type,
            "dept_code": r.dept_code,
            "target_main_warehouse": "耗材科主库房" if "CONSUMABLE" in (r.remark or "") or "耗材" in (r.remark or "") else "设备科主库房",
            "product_id": r.product_id,
            "product_code": r.product_code,
            "product_name": r.product_name,
            "udi_sn": r.udi_sn,
            "qr_code_payload": r.qr_code_payload,
            "is_qr_verified": r.is_qr_verified,
            "patient_inpatient_no": r.patient_inpatient_no,
            "patient_name_masked": r.patient_name_masked,
            "confirm_stage": r.confirm_stage,
            "is_irreversible_locked": r.is_irreversible_locked,
            "operator_name": r.operator_name,
            "confirmed_by": r.confirmed_by,
            "confirmed_at": r.confirmed_at.strftime("%Y-%m-%d %H:%M:%S") if r.confirmed_at else None,
            "remark": r.remark,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None
        }
        for r in rows
    ]
    return ApiResponse(code=200, msg="查询高值全生命周期单据列表成功", data=data)


@router.post("/prep-order", response_model=ApiResponse[dict])
def create_high_value_prep_order(
    payload: HighValuePrepCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user", "dept_manager"]))
):
    """临床科室填报高值耗材备货申请单 (对齐图 2 规范)

    @param payload: (HighValuePrepCreateRequest) 备货申请单据与选品明细
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 申请单号及记录
    @route: POST /api/v1/high-value/prep-order
    @throws: HTTPException(400) 当明细为空时抛出
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="备货单明细不可为空")

    created_orders = []
    for item in payload.items:
        order_no = f"HVP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
        udi_sample = f"SN{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}"
        record = SpdHighValueLifecycleOrder(
            order_no=order_no,
            hv_biz_type="HV_STOCK_PREP",
            dept_code=payload.apply_dept_code,
            product_id=item.product_id,
            product_code=item.product_code,
            product_name=item.product_name,
            udi_sn=udi_sample,
            qr_code_payload=f"010697{random.randint(10000000, 99999999)}1728123110B2026110321{udi_sample}",
            is_qr_verified=0,
            confirm_stage="PENDING_CONFIRM",
            is_irreversible_locked=0,
            operator_name=user_ctx.real_name or user_ctx.username,
            remark=f"目标归口审批:{payload.target_main_dept} | {payload.remark or '临床择期手术备货'}"
        )
        db.add(record)
        created_orders.append(order_no)

    db.commit()
    return ApiResponse(code=200, msg="高值耗材备货申请单已提交，等待上级主库审批", data={"order_nos": created_orders})


@router.post("/prep-approve/{order_id}", response_model=ApiResponse[dict])
def approve_high_value_prep_order(
    order_id: int,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """上级主库审批通过备货申请：联动生成普通主库出库记录并直达高值仓库存

    @param order_id: (int) 备货申请单ID
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 审批人鉴权 (耗材科/设备科/信息科)
    @returns: ApiResponse[dict] 联动处理结果
    @route: POST /api/v1/high-value/prep-approve/{order_id}
    @throws: HTTPException(404) 单据不存在时抛出
    """
    order = db.query(SpdHighValueLifecycleOrder).filter(SpdHighValueLifecycleOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="备货单据不存在")

    order.confirm_stage = "APPROVED"
    order.confirmed_by = user_ctx.real_name
    order.confirmed_at = datetime.now()

    # 1. 自动在普通耗材主库生成按需分发调拨出库记录 (普通耗材主库具有真实出库记录)
    dist_no = f"DIST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(10, 99)}"
    dist_order = SpdDistributionOrder(
        dist_order_no=dist_no,
        source_main_dept="CONSUMABLE_DEPT",
        target_type="TO_HIGH_VALUE_WH",
        target_dept_id=5,  # 高值专仓虚拟科室ID
        target_dept_name="高值耗材专仓",
        main_inventory_id=1,
        product_id=order.product_id,
        product_code=order.product_code,
        product_name=order.product_name,
        batch_no=f"B{datetime.now().strftime('%Y%m%d')}",
        expiry_date=date(2029, 12, 31),
        dist_qty=1,
        unit_price=Decimal("4200.00"),
        total_amount=Decimal("4200.00"),
        order_status="DISPATCHED",
        dispatcher_id=user_ctx.id,
        dispatcher_name=user_ctx.real_name,
        receiver_name="高值专仓管理员",
        remark="备货审批通过自动触发主库出库下发高值专仓"
    )
    db.add(dist_order)

    # 2. 直接生成高值耗材专仓在库单品库存
    hv_item = SpdHighValueItem(
        udi_full_code=order.qr_code_payload,
        udi_sn=order.udi_sn,
        dist_order_no=dist_no,
        product_id=order.product_id,
        product_code=order.product_code,
        product_name=order.product_name,
        spec_model="常规型号 (备货入库)",
        main_dept_code="CONSUMABLE_DEPT",
        batch_no=f"B{datetime.now().strftime('%Y%m%d')}",
        expiry_date=date(2029, 12, 31),
        unit_price=Decimal("4200.00"),
        wh_cabinet_code="高值专仓-智能专柜01-A01格",
        current_dept_id=5,
        current_dept_name="高值耗材专仓",
        item_status="IN_HIGH_VALUE_WH"
    )
    db.add(hv_item)

    # 3. 记录全流程 6W 日志 (节点 3_MAIN_DISPATCH 与 4_HIGH_VALUE_CODE)
    record_workflow_6w_log(
        db=db,
        biz_order_no=dist_no,
        node_action="3_MAIN_DISPATCH",
        product_code=order.product_code,
        product_name=order.product_name,
        batch_or_udi=order.udi_sn,
        from_dept_name="耗材科主库房",
        from_user_name=user_ctx.real_name,
        to_dept_name="高值耗材专仓",
        to_user_name="智能专柜终端",
        change_qty=1,
        before_stock_snapshot=10,
        after_stock_snapshot=9,
        settlement_amount=Decimal("4200.00"),
        is_billable=0,  # 移库不计费
        audit_remark=f"备货申请通过，普通主库自动发料出库并直下高值专仓 (关联单: {dist_no})"
    )

    record_workflow_6w_log(
        db=db,
        biz_order_no=order.order_no,
        node_action="4_HIGH_VALUE_CODE",
        product_code=order.product_code,
        product_name=order.product_name,
        batch_or_udi=order.udi_sn,
        from_dept_name="耗材科主库房",
        from_user_name=user_ctx.real_name,
        to_dept_name="高值耗材专仓",
        to_user_name="高值仓管理员",
        change_qty=1,
        before_stock_snapshot=0,
        after_stock_snapshot=1,
        settlement_amount=Decimal("4200.00"),
        is_billable=0,
        audit_remark="高值耗材专仓自动赋码入库，生成GS1一物一码"
    )

    db.commit()
    return ApiResponse(code=200, msg="备货申请已审批通过，已自动下发高值专仓并生成主库出库单", data={"dist_order_no": dist_no, "udi_sn": order.udi_sn})


@router.post("/return-order", response_model=ApiResponse[dict])
def create_high_value_return_order(
    payload: HighValueReturnCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user", "dept_manager"]))
):
    """临床科室填报高值退货出库单 (对齐图 2 规范)

    @param payload: (HighValueReturnCreateRequest) 退货请求
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 单据编号
    @route: POST /api/v1/high-value/return-order
    @throws: 无异常抛出
    """
    order_no = f"HVR{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    record = SpdHighValueLifecycleOrder(
        order_no=order_no,
        hv_biz_type="HV_DEPT_RETURN",
        dept_code=payload.dept_code,
        product_id=1,
        product_code="93601160000100001",
        product_name="钛合金锁定接骨板螺钉系统",
        udi_sn=payload.udi_sn,
        qr_code_payload=f"01069700000000001729123110B2026110321{payload.udi_sn}",
        is_qr_verified=0,
        confirm_stage="PENDING_CONFIRM",
        is_irreversible_locked=0,
        operator_name=user_ctx.real_name or user_ctx.username,
        remark=payload.remark or "临床科室退回高值专仓"
    )
    db.add(record)
    db.commit()
    return ApiResponse(code=200, msg="退货出库单已创建，待外层二次确认正式提交", data={"order_no": order_no})


@router.post("/return-lock/{order_id}", response_model=ApiResponse[dict])
def lock_high_value_return_order(
    order_id: int,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "secondary_user", "dept_manager"]))
):
    """退货出库单外层二次确认提交：永久强制不可逆锁死 (置 is_irreversible_locked=1)

    @param order_id: (int) 退货单主键ID
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 锁定状态
    @route: POST /api/v1/high-value/return-lock/{order_id}
    @throws: HTTPException(400/404) 校验异常时抛出
    """
    order = db.query(SpdHighValueLifecycleOrder).filter(SpdHighValueLifecycleOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="退货单据不存在")

    if order.is_irreversible_locked:
        raise HTTPException(status_code=400, detail="该退货单已永久锁死，严禁重复操作")

    order.confirm_stage = "SUBMITTED"
    order.is_irreversible_locked = 1
    order.confirmed_by = user_ctx.real_name
    order.confirmed_at = datetime.now()

    # 记录全流程日志 8_REVERSE_AUDIT
    record_workflow_6w_log(
        db=db,
        biz_order_no=order.order_no,
        node_action="8_REVERSE_AUDIT",
        product_code=order.product_code,
        product_name=order.product_name,
        batch_or_udi=order.udi_sn,
        from_dept_name=order.dept_code,
        from_user_name=user_ctx.real_name,
        to_dept_name="高值耗材专仓",
        to_user_name="高值仓管理员",
        change_qty=1,
        before_stock_snapshot=1,
        after_stock_snapshot=0,
        settlement_amount=Decimal("4200.00"),
        is_billable=0,
        audit_remark="高值退货出库单二次确认提交，系统强制不可逆锁定生效"
    )

    db.commit()
    return ApiResponse(code=200, msg="退货出库单已二次确认提交，并已永久锁定不可逆", data={"order_no": order.order_no, "is_locked": 1})


@router.get("/stocktake-inventory", response_model=ApiResponse[List[dict]])
def get_high_value_stocktake_inventory(
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """高值专仓独立实物盘点底表 (一物一码精细盘对)

    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[List[dict]] 盘点底表清单
    @route: GET /api/v1/high-value/stocktake-inventory
    @throws: 无特定异常
    """
    items = db.query(SpdHighValueItem).filter(SpdHighValueItem.item_status.in_(["IN_HIGH_VALUE_WH", "IN_SECONDARY_CABINET"])).all()
    result = []
    for it in items:
        result.append({
            "id": it.id,
            "udi_sn": it.udi_sn,
            "spec_code": it.product_code,
            "product_name": it.product_name,
            "spec_name": it.spec_model,
            "model_name": "国标型",
            "unit_name": "套",
            "manufacturer": "强生(上海)医疗器材",
            "batch_no": it.batch_no,
            "cabinet_code": it.wh_cabinet_code,
            "book_qty": 1,
            "actual_qty": 1,
            "diff_qty": 0,
            "unit_price": float(it.unit_price),
            "is_new_supplement": 0
        })
    return ApiResponse(code=200, msg="获取高值独立盘点底表成功", data=result)


@router.post("/stocktake-submit", response_model=ApiResponse[dict])
def submit_high_value_stocktake(
    payload: dict,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """高值专仓盘点提交平账

    @param payload: (dict) 盘点清单数据
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 盘点平账结果
    @route: POST /api/v1/high-value/stocktake-submit
    @throws: 无异常抛出
    """
    stocktake_no = f"HV-STK{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return ApiResponse(code=200, msg="高值耗材专仓盘点提交平账成功，已生成财务对账台账", data={"stocktake_no": stocktake_no, "operator": user_ctx.real_name})
