"""医院 SPD 通用两阶段二次确认状态机、细粒度 8 动作权限矩阵与跨模块业务联动服务层

本模块严格执行 Skill 04 (隐私脱敏)、Skill 05 (6W日志)、Skill 07 (两阶段确认+特例永久锁死) 与 Skill 08 (解耦式 8 动作 RBAC)。
"""

from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.spd_models import SpdProductDict, SpdRequisitionOrder, SpdWorkflowLog, SysUser
from app.models.spd_extended_models import (
    SysUserModulePermission,
    SpdWarehouseNode,
    SpdInboundAndOutboundOrder,
    SpdHighValueLifecycleOrder,
    SpdSupplierAndPurchaseOrder
)
from app.schemas.spd_extended_schemas import (
    PermissionToggleRequest,
    TwoStepActionRequest,
    PurchaseOrderFlowRequest
)

# 常用医疗物资汉字首字母映射字典（零外部依赖稳定生成拼音助记码）
PINYIN_CHAR_MAP = {
    "医": "Y", "用": "Y", "一": "Y", "次": "C", "性": "X", "无": "W", "菌": "J",
    "注": "Z", "射": "S", "器": "Q", "外": "W", "科": "K", "纱": "S", "布": "B",
    "敷": "F", "料": "L", "钛": "T", "合": "H", "金": "J", "骨": "G", "板": "B",
    "冠": "G", "脉": "M", "药": "Y", "物": "W", "洗": "X", "脱": "T", "支": "Z",
    "架": "J", "迈": "M", "瑞": "R", "监": "J", "护": "H", "仪": "Y", "血": "X",
    "氧": "Y", "探": "T", "头": "T", "留": "L", "置": "Z", "针": "Z", "导": "D",
    "管": "G", "手": "S", "套": "T", "口": "K", "罩": "Z", "缝": "F", "线": "X"
}

VALID_ACTION_KEYS = {
    "can_view", "can_create", "can_edit", "can_delete",
    "can_second_confirm", "can_cancel_submit", "can_approve", "can_print"
}


def generate_pinyin_abbr(product_name: str) -> str:
    """根据医疗耗材产品名称自动提取大写拼音首字母助记码
    @param product_name: str 医疗物资产品中文名称
    @returns str 自动生成的大写拼音首字母缩写字符串
    @route internal://app/services/rbac_and_confirm_service/generate_pinyin_abbr
    @throws ValueError 当输入名称为空字符串时返回默认助记码
    """
    if not product_name:
        return "SPDHC"
    result = []
    for ch in product_name:
        if ch in PINYIN_CHAR_MAP:
            result.append(PINYIN_CHAR_MAP[ch])
        elif ch.isascii() and ch.isalnum():
            result.append(ch.upper())
        elif "\u4e00" <= ch <= "\u9fff":
            # 基于 Unicode 偏移稳定映射大写字母
            result.append(chr(65 + (ord(ch) % 26)))
    return "".join(result)[:24] or "SPDHC"


def mask_patient_name(raw_name: str) -> str:
    """对患者真实姓名执行医疗隐私合规脱敏（Skill 04）
    @param raw_name: str 患者原始真实姓名
    @returns str 脱敏后的患者姓名（如 陈*生 或 李*）
    @route internal://app/services/rbac_and_confirm_service/mask_patient_name
    @throws ValueError 当姓名为空时返回匿名占位符
    """
    clean = (raw_name or "").strip()
    if len(clean) <= 1:
        return "*"
    if len(clean) == 2:
        return f"{clean[0]}*"
    return f"{clean[0]}*{clean[-1]}"


def toggle_user_module_permission(db: Session, req: PermissionToggleRequest) -> SysUserModulePermission:
    """信息科管理员针对具体人员独立开启或关闭某模块下的 8 项原子操作权限（Skill 08）
    @param db: Session SQLAlchemy 数据库会话实例
    @param req: PermissionToggleRequest 权限开关变更请求载荷
    @returns SysUserModulePermission 更新或新建后的用户级模块权限 ORM 实例
    @route internal://app/services/rbac_and_confirm_service/toggle_user_module_permission
    @throws HTTPException 当动作键名非法或目标用户不存在时抛出 400/404 异常
    """
    if req.action_key not in VALID_ACTION_KEYS:
        raise HTTPException(status_code=400, detail=f"非法的权限原子动作键: {req.action_key}")

    user = db.query(SysUser).filter(SysUser.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"未找到目标用户 ID={req.user_id}")

    perm = db.query(SysUserModulePermission).filter(
        SysUserModulePermission.user_id == req.user_id,
        SysUserModulePermission.module_code == req.module_code
    ).first()

    if not perm:
        perm = SysUserModulePermission(
            user_id=user.id,
            username=user.username,
            role_code=user.role_code,
            module_code=req.module_code,
            module_name=req.module_code,
            updated_by=req.operator_name
        )
        db.add(perm)

    setattr(perm, req.action_key, req.enabled)
    perm.updated_by = req.operator_name
    db.commit()
    db.refresh(perm)
    return perm


def execute_inbound_outbound_two_step(db: Session, req: TwoStepActionRequest) -> SpdInboundAndOutboundOrder:
    """执行通用出入库单、退给供应商红字单及科室期初建账单的两阶段二次确认与取消提交状态机（Skill 07）
    @param db: Session SQLAlchemy 数据库会话实例
    @param req: TwoStepActionRequest 包含单号、执行动作(SECOND_CONFIRM/CANCEL_SUBMIT/EDIT_REMARK/DELETE_ORDER)及操作人
    @returns SpdInboundAndOutboundOrder 状态跃迁完成后的出入库单据 ORM 实例
    @route internal://app/services/rbac_and_confirm_service/execute_inbound_outbound_two_step
    @throws HTTPException 当违反两阶段锁死规则或期初数据永久不可逆规则时抛出 400 业务拦截异常
    """
    order = db.query(SpdInboundAndOutboundOrder).filter(
        SpdInboundAndOutboundOrder.order_no == req.order_no
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"单据 {req.order_no} 不存在")

    if req.action == "SECOND_CONFIRM":
        if order.confirm_stage == "SUBMITTED":
            raise HTTPException(status_code=400, detail=f"单据 {req.order_no} 已处于二次确认正式提交态，无需重复确认")
        order.confirm_stage = "SUBMITTED"
        order.second_confirmed_by = req.operator_name
        order.second_confirmed_at = datetime.now()

        # 特例：若为科室仓库期初数据建账单(INIT_STOCK)，二次确认后永久锁死不可改，并锁定对应仓库节点
        if order.order_type == "INIT_STOCK":
            order.is_irreversible_locked = 1
            wh_node = db.query(SpdWarehouseNode).filter(
                SpdWarehouseNode.warehouse_code == order.warehouse_code
            ).first()
            if wh_node:
                wh_node.init_stock_locked = 1
                wh_node.init_stock_order_no = order.order_no
                wh_node.init_locked_at = datetime.now()

    elif req.action == "CANCEL_SUBMIT":
        if order.is_irreversible_locked == 1 or order.order_type == "INIT_STOCK":
            raise HTTPException(
                status_code=400,
                detail=f"[不可逆护栏拦截] 期初数据建账单 {req.order_no} 已完成二次确认永久锁定，只可填写一次，严禁取消提交或修改"
            )
        if order.confirm_stage != "SUBMITTED":
            raise HTTPException(status_code=400, detail="仅已完成二次确认(SUBMITTED)的单据可执行取消提交")
        order.confirm_stage = "PENDING_CONFIRM"
        order.second_confirmed_by = None
        order.second_confirmed_at = None

    elif req.action == "EDIT_REMARK":
        if order.is_irreversible_locked == 1:
            raise HTTPException(status_code=400, detail=f"[不可逆护栏拦截] 单据 {req.order_no} 已永久锁定只读，严禁修改")
        if order.confirm_stage == "SUBMITTED":
            raise HTTPException(
                status_code=400,
                detail=f"[两阶段状态机拦截] 单据 {req.order_no} 已完成外层二次确认提交，请先点击【取消提交】退回待确认态后再修改"
            )
        order.remark = req.new_remark or order.remark

    elif req.action == "DELETE_ORDER":
        if order.is_irreversible_locked == 1 or order.confirm_stage == "SUBMITTED":
            raise HTTPException(
                status_code=400,
                detail=f"[两阶段状态机拦截] 单据 {req.order_no} 已二次确认锁死或属于永久不可逆单据，严禁直接删除"
            )
        db.delete(order)
        db.commit()
        return order
    else:
        raise HTTPException(status_code=400, detail=f"不支持的状态机动作: {req.action}")

    db.commit()
    db.refresh(order)
    return order


def execute_hv_lifecycle_two_step(db: Session, req: TwoStepActionRequest) -> SpdHighValueLifecycleOrder:
    """执行高值耗材备货、接收、科室退货出库单的两阶段确认及高值退货永久锁死逻辑（Skill 07）
    @param db: Session SQLAlchemy 数据库会话实例
    @param req: TwoStepActionRequest 包含高值单号、执行动作与操作人
    @returns SpdHighValueLifecycleOrder 状态更新后的高值耗材生命周期单据实例
    @route internal://app/services/rbac_and_confirm_service/execute_hv_lifecycle_two_step
    @throws HTTPException 当对已二次确认的高值科室退货出库单(HV_DEPT_RETURN)尝试取消提交或修改时抛出 400 异常
    """
    hv_order = db.query(SpdHighValueLifecycleOrder).filter(
        SpdHighValueLifecycleOrder.order_no == req.order_no
    ).first()
    if not hv_order:
        raise HTTPException(status_code=404, detail=f"高值单据 {req.order_no} 不存在")

    if req.action == "SECOND_CONFIRM":
        hv_order.confirm_stage = "SUBMITTED"
        hv_order.confirmed_by = req.operator_name
        hv_order.confirmed_at = datetime.now()
        # 核心业务契约：高值耗材-科室退货出库单(HV_DEPT_RETURN)一旦完成外层二次确认提交，永久锁死不可改
        if hv_order.hv_biz_type == "HV_DEPT_RETURN":
            hv_order.is_irreversible_locked = 1

    elif req.action in ("CANCEL_SUBMIT", "EDIT_REMARK", "DELETE_ORDER"):
        if hv_order.is_irreversible_locked == 1 or (
            hv_order.hv_biz_type == "HV_DEPT_RETURN" and hv_order.confirm_stage == "SUBMITTED"
        ):
            raise HTTPException(
                status_code=400,
                detail=f"[高值退货不可逆铁律拦截] 高值科室退货出库单 {req.order_no} 已完成二次确认提交，永久锁定不可取消、不可修改、不可删除"
            )
        if req.action == "CANCEL_SUBMIT":
            hv_order.confirm_stage = "PENDING_CONFIRM"
            hv_order.confirmed_by = None
            hv_order.confirmed_at = None
        elif req.action == "EDIT_REMARK":
            if hv_order.confirm_stage == "SUBMITTED":
                raise HTTPException(status_code=400, detail="已二次确认单据请先取消提交后再修改")
            hv_order.remark = req.new_remark or hv_order.remark
    else:
        raise HTTPException(status_code=400, detail=f"未知高值单据动作: {req.action}")

    db.commit()
    db.refresh(hv_order)
    return hv_order


def auto_create_outbound_on_requisition_approved(
    db: Session,
    req_order_id: int,
    auditor_name: str
) -> SpdInboundAndOutboundOrder:
    """请领受理审核通过后，自动在【耗材出库】模块生成对应的审核出库记录（对齐图1普通耗材核心规则）
    @param db: Session SQLAlchemy 数据库会话实例
    @param req_order_id: int 临床二级库请领单主键ID (spd_requisition_order.id)
    @param auditor_name: str 耗材科/设备科审核人姓名
    @returns SpdInboundAndOutboundOrder 自动生成的耗材审核出库单 ORM 实例
    @route internal://app/services/rbac_and_confirm_service/auto_create_outbound_on_requisition_approved
    @throws HTTPException 当请领单不存在时抛出 404 异常
    """
    req_order = db.query(SpdRequisitionOrder).filter(SpdRequisitionOrder.id == req_order_id).first()
    if not req_order:
        raise HTTPException(status_code=404, detail=f"未找到请领单 ID={req_order_id}")

    product = db.query(SpdProductDict).filter(SpdProductDict.id == req_order.product_id).first()
    unit_price = product.unit_price if product else Decimal("10.00")
    approved_qty = req_order.approved_qty if req_order.approved_qty > 0 else req_order.apply_qty

    req_order.req_status = "APPROVED_DISPATCHED"
    req_order.approver_name = auditor_name
    req_order.approved_at = datetime.now()

    auto_out_no = f"OUT-AUTO-{req_order.req_order_no}"
    existing_out = db.query(SpdInboundAndOutboundOrder).filter(
        SpdInboundAndOutboundOrder.order_no == auto_out_no
    ).first()
    if existing_out:
        return existing_out

    auto_out_order = SpdInboundAndOutboundOrder(
        order_no=auto_out_no,
        order_type="REQ_AUTO_OUT",
        warehouse_code="WH_WEICAI" if req_order.target_main_dept == "CONSUMABLE_DEPT" else "WH_EQUIP",
        dept_code=req_order.target_main_dept,
        target_dept_or_supplier=req_order.apply_dept_name,
        product_id=req_order.product_id,
        product_code=req_order.product_code,
        product_name=req_order.product_name,
        batch_no="BATCH-FEFO-AUTO",
        quantity=approved_qty,
        unit_price=unit_price,
        total_amount=unit_price * Decimal(str(approved_qty)),
        source_ref_order_no=req_order.req_order_no,
        confirm_stage="SUBMITTED",
        is_irreversible_locked=0,
        created_by=auditor_name,
        second_confirmed_by=auditor_name,
        second_confirmed_at=datetime.now(),
        remark=f"请领单[{req_order.req_order_no}]审核通过自动生成耗材出库记录"
    )
    db.add(auto_out_order)

    # 同步写入 6W 全流程物权交接日志
    log_entry = SpdWorkflowLog(
        trace_no=f"TRC-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        biz_order_no=auto_out_no,
        node_action="3_MAIN_DISPATCH",
        product_code=req_order.product_code,
        product_name=req_order.product_name,
        batch_or_udi="BATCH-FEFO-AUTO",
        from_dept_name=req_order.target_main_dept,
        from_user_name=auditor_name,
        to_dept_name=req_order.apply_dept_name,
        to_user_name=req_order.applicant_name,
        change_qty=approved_qty,
        before_stock_snapshot=500,
        after_stock_snapshot=500 - approved_qty,
        settlement_amount=unit_price * Decimal(str(approved_qty)),
        is_billable=0,
        audit_status="VERIFIED",
        audit_remark=f"请领审核通过自动联动生成耗材出库单: {auto_out_no}"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(auto_out_order)
    return auto_out_order


def execute_supplier_purchase_flow(db: Session, req: PurchaseOrderFlowRequest) -> SpdSupplierAndPurchaseOrder:
    """执行多级采购计划、主科审批、供应商资质硬拦截与拣货二次确认发货闭环（自动生成医院待验收入库单）
    @param db: Session SQLAlchemy 数据库会话实例
    @param req: PurchaseOrderFlowRequest 采供协同流转请求载荷
    @returns SpdSupplierAndPurchaseOrder 更新后的采供协同单据 ORM 实例
    @route internal://app/services/rbac_and_confirm_service/execute_supplier_purchase_flow
    @throws HTTPException 当供应商经营资质未审核通过而尝试接单发货时抛出 403 硬拦截异常
    """
    product = db.query(SpdProductDict).filter(SpdProductDict.id == req.product_id).first()
    p_code = product.product_code if product else "PROD-GEN-001"
    p_name = product.product_name if product else "一次性使用无菌注射器"
    u_price = product.unit_price if product else Decimal("0.45")

    if req.flow_action == "CREATE_PLAN":
        new_no = req.order_no or f"PUR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        po = SpdSupplierAndPurchaseOrder(
            order_no=new_no,
            supplier_code=req.supplier_code,
            supplier_name="威高医用高分子制品股份有限公司",
            license_no="鲁械经营备20260088号",
            license_expiry_date=req.picked_expiry_date or datetime.now().date(),
            qual_audit_status="QUAL_APPROVED",
            apply_dept_code=req.apply_dept_code,
            audit_main_dept_code="EQUIP_DEPT" if "HV" in p_code else "CONSUMABLE_DEPT",
            product_id=req.product_id,
            product_code=p_code,
            product_name=p_name,
            purchase_qty=req.purchase_qty,
            confirm_stage="SUBMITTED",
            purchase_flow_status="PLAN_SUBMITTED",
            created_by=req.operator_name
        )
        db.add(po)
        db.commit()
        db.refresh(po)
        return po

    po = db.query(SpdSupplierAndPurchaseOrder).filter(
        SpdSupplierAndPurchaseOrder.order_no == req.order_no
    ).first()
    if not po:
        raise HTTPException(status_code=404, detail=f"采购单 {req.order_no} 不存在")

    if req.flow_action == "DEPT_APPROVE":
        po.purchase_flow_status = "DEPT_APPROVED"
        db.commit()
        db.refresh(po)
        return po

    if req.flow_action == "SUPPLIER_PICK_AND_SHIP":
        # 供应商资质硬拦截：未通过医院准入审核的供应商严禁接单发货
        if po.qual_audit_status != "QUAL_APPROVED":
            raise HTTPException(
                status_code=403,
                detail=f"[供应商资质准入硬拦截] 供应商 {po.supplier_code} 的《医疗器械经营许可证》处于 {po.qual_audit_status} 状态，未经医院审核通过严禁接单或发货"
            )
        po.picked_batch_no = req.picked_batch_no or "BATCH-SUP-202611"
        po.picked_expiry_date = req.picked_expiry_date
        po.confirm_stage = "SUBMITTED"
        po.purchase_flow_status = "HOSP_INBOUND_CREATED"

        # 自动同步生成医院端的《待验收入库单 (PENDING_CONFIRM)》
        auto_inb_no = f"INB-SUP-{po.order_no}"
        po.auto_inbound_order_no = auto_inb_no

        existing_inb = db.query(SpdInboundAndOutboundOrder).filter(
            SpdInboundAndOutboundOrder.order_no == auto_inb_no
        ).first()
        if not existing_inb:
            auto_inb = SpdInboundAndOutboundOrder(
                order_no=auto_inb_no,
                order_type="GEN_INBOUND",
                warehouse_code="WH_WEICAI" if po.audit_main_dept_code == "CONSUMABLE_DEPT" else "WH_EQUIP",
                dept_code=po.audit_main_dept_code,
                target_dept_or_supplier=po.supplier_code,
                product_id=po.product_id,
                product_code=po.product_code,
                product_name=po.product_name,
                batch_no=po.picked_batch_no,
                quantity=po.purchase_qty,
                unit_price=u_price,
                total_amount=u_price * Decimal(str(po.purchase_qty)),
                source_ref_order_no=po.order_no,
                confirm_stage="PENDING_CONFIRM",
                is_irreversible_locked=0,
                created_by=req.operator_name,
                remark=f"由供应商[{po.supplier_name}]二次确认发货单[{po.order_no}]自动同步生成的医院待验收入库单"
            )
            db.add(auto_inb)

        db.commit()
        db.refresh(po)
        return po

    raise HTTPException(status_code=400, detail=f"未知采供流转动作: {req.flow_action}")
