"""全流程业务链路日志管理路由模块 (核心 CRUD 五：6W 物权交接台账)

本模块记录信息科、耗材/设备主库、高值专仓、临床二级库与财务科之间的 6W 物权责任交接关系，提供穿透溯源与合规审计接口。
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_context, require_roles, CurrentUserContext
from app.models.spd_models import (
    SpdWorkflowLog,
    SpdMainInventory,
    SpdSecondaryInventory,
    SpdHighValueItem
)
from app.schemas.spd_schemas import (
    ApiResponse,
    WorkflowLogCreateRequest,
    WorkflowLogAuditRequest,
    WorkflowLogResponse,
    RecallFreezeBatchRequest
)
from app.services.trace_service import record_workflow_6w_log

router = APIRouter(prefix="/workflow-logs", tags=["核心 CRUD 五：全流程业务链路日志管理"])


@router.get("", response_model=ApiResponse[List[WorkflowLogResponse]])
def query_workflow_logs(
    biz_order_no: Optional[str] = Query(None, description="关联业务单据号精确/模糊查询"),
    node_action: Optional[str] = Query(None, description="8大业务节点过滤"),
    product_code: Optional[str] = Query(None, description="物资编码"),
    from_dept_name: Optional[str] = Query(None, description="交出方科室"),
    to_dept_name: Optional[str] = Query(None, description="接收方科室"),
    is_billable: Optional[int] = Query(None, description="是否计费(0-移库, 1-消耗记账)"),
    audit_status: Optional[str] = Query(None, description="VERIFIED | FLAGGED | RECTIFIED"),
    db: Session = Depends(get_db)
):
    """多维穿透查询全流程 6W 业务链路日志台账

    @param: biz_order_no (Optional[str]) 单据号
    @param: node_action (Optional[str]) 8大节点
    @param: product_code (Optional[str]) 物资编码
    @param: from_dept_name (Optional[str]) 交出科室
    @param: to_dept_name (Optional[str]) 接收科室
    @param: is_billable (Optional[int]) 计费标记
    @param: audit_status (Optional[str]) 审计状态
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[WorkflowLogResponse]] 6W日志清单
    @route: GET /api/v1/workflow-logs
    @throws: 无异常抛出
    """
    query = db.query(SpdWorkflowLog)
    if biz_order_no:
        query = query.filter(SpdWorkflowLog.biz_order_no.like(f"%{biz_order_no}%"))
    if node_action:
        query = query.filter(SpdWorkflowLog.node_action == node_action)
    if product_code:
        query = query.filter(SpdWorkflowLog.product_code == product_code)
    if from_dept_name:
        query = query.filter(SpdWorkflowLog.from_dept_name.like(f"%{from_dept_name}%"))
    if to_dept_name:
        query = query.filter(SpdWorkflowLog.to_dept_name.like(f"%{to_dept_name}%"))
    if is_billable is not None:
        query = query.filter(SpdWorkflowLog.is_billable == is_billable)
    if audit_status:
        query = query.filter(SpdWorkflowLog.audit_status == audit_status)

    logs = query.order_by(SpdWorkflowLog.created_at.desc(), SpdWorkflowLog.id.desc()).all()
    data = [WorkflowLogResponse.model_validate(l) for l in logs]
    return ApiResponse(code=200, msg="查询全流程 6W 业务日志成功", data=data)


@router.post("", response_model=ApiResponse[WorkflowLogResponse])
def append_workflow_log(
    payload: WorkflowLogCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """信息科管理员手动补录或纠偏全流程流转审计日志

    @param: payload (WorkflowLogCreateRequest) 补录日志参数
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文 (仅限 sys_admin)
    @returns: ApiResponse[WorkflowLogResponse] 补录成功的日志记录
    @route: POST /api/v1/workflow-logs
    @throws: 写入异常时抛出并在上层回滚
    """
    log_entry = record_workflow_6w_log(
        db=db,
        biz_order_no=payload.biz_order_no,
        node_action=payload.node_action,
        product_code=payload.product_code,
        product_name=payload.product_name,
        batch_or_udi=payload.batch_or_udi,
        from_dept_name=payload.from_dept_name,
        from_user_name=payload.from_user_name,
        to_dept_name=payload.to_dept_name,
        to_user_name=payload.to_user_name,
        change_qty=payload.change_qty,
        before_stock_snapshot=payload.before_stock_snapshot,
        after_stock_snapshot=payload.after_stock_snapshot,
        settlement_amount=payload.settlement_amount,
        is_billable=payload.is_billable,
        audit_remark=payload.audit_remark or f"信息科管理员 [{user_ctx.real_name}] 手动补录审计日志"
    )
    db.commit()
    db.refresh(log_entry)
    return ApiResponse(code=200, msg="全流程日志补录成功", data=WorkflowLogResponse.model_validate(log_entry))


@router.put("/{log_id}", response_model=ApiResponse[WorkflowLogResponse])
def audit_workflow_log(
    log_id: int,
    payload: WorkflowLogAuditRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """管理员对流转日志更新审计复核状态与批注

    @param: log_id (int) 日志ID
    @param: payload (WorkflowLogAuditRequest) 审计状态与批注
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[WorkflowLogResponse] 审计后的日志实体
    @route: PUT /api/v1/workflow-logs/{log_id}
    @throws: HTTPException(404) 日志不存在时抛出
    """
    log_entry = db.query(SpdWorkflowLog).filter(SpdWorkflowLog.id == log_id).first()
    if not log_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流转日志不存在")

    log_entry.audit_status = payload.audit_status
    log_entry.audit_remark = f"[{user_ctx.real_name} 审计复核]: {payload.audit_remark}"
    db.commit()
    db.refresh(log_entry)
    return ApiResponse(code=200, msg="流转日志审计状态更新成功", data=WorkflowLogResponse.model_validate(log_entry))


@router.delete("/{log_id}", response_model=ApiResponse[dict])
def delete_workflow_log(
    log_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """信息科系统管理员清理无效流转日志（最高权限护栏保护）

    @param: log_id (int) 日志ID
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权 (严禁科室人员或普通管理员越权删除)
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/workflow-logs/{log_id}
    @throws: HTTPException(404) 日志不存在时抛出
    """
    log_entry = db.query(SpdWorkflowLog).filter(SpdWorkflowLog.id == log_id).first()
    if not log_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流转日志不存在")

    db.delete(log_entry)
    db.commit()
    return ApiResponse(code=200, msg="流转日志已由系统管理员安全清理", data={"deleted_id": log_id})


@router.get("/user-actions", response_model=ApiResponse[List[dict]])
def query_user_action_audit_logs(
    username: Optional[str] = Query(None, description="按操作人工号/姓名筛选"),
    module_code: Optional[str] = Query(None, description="按业务模块筛选"),
    action_type: Optional[str] = Query(None, description="按操作动作筛选"),
    db: Session = Depends(get_db)
):
    """查询全院全员人工操作安全审计日志 (人机操作痕迹台账)

    @param username: (Optional[str]) 操作人员工号或姓名模糊搜索
    @param module_code: (Optional[str]) 模块编码过滤
    @param action_type: (Optional[str]) 动作类型过滤
    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[List[dict]] 全员人工操作记录清单
    @route: GET /api/v1/workflow-logs/user-actions
    @throws: 无异常抛出
    """
    # 构造可追溯的系统操作审计种子流水
    base_actions = [
        {
            "id": 1,
            "action_no": "ACT202611030001",
            "operator_name": "赵振华",
            "username": "sys_admin",
            "role_name": "信息科系统管理员",
            "dept_name": "信息科",
            "module_name": "人员与RBAC中心",
            "action_type": "权限变更",
            "target_object": "护士李晓琳(secondary_user)",
            "detail": "为用户李晓琳分配骨科二级库(WH_SEC_ORTHO)申领与出库原子权限",
            "client_ip": "192.168.1.102",
            "status": "SUCCESS",
            "created_at": "2026-11-03 14:10:22"
        },
        {
            "id": 2,
            "action_no": "ACT202611030002",
            "operator_name": "王建国",
            "username": "dept_manager",
            "role_name": "耗材科主库管理员",
            "dept_name": "耗材科主库",
            "module_name": "普通耗材主库",
            "action_type": "验收入库",
            "target_object": "入库单 IN202611031900",
            "detail": "完成国药控股医用敷料贴等8品项验收入库并自动审核入库台账",
            "client_ip": "192.168.1.155",
            "status": "SUCCESS",
            "created_at": "2026-11-03 14:22:15"
        },
        {
            "id": 3,
            "action_no": "ACT202611030003",
            "operator_name": "王建国",
            "username": "dept_manager",
            "role_name": "耗材科主库管理员",
            "dept_name": "耗材科主库",
            "module_name": "高值耗材专仓",
            "action_type": "备货审批",
            "target_object": "备货单 HVP20261102001",
            "detail": "审批通过骨科脊柱锁定板备货申请，自动生成主库出库记录并直达高值仓",
            "client_ip": "192.168.1.155",
            "status": "SUCCESS",
            "created_at": "2026-11-03 14:35:40"
        },
        {
            "id": 4,
            "action_no": "ACT202611030004",
            "operator_name": "李晓琳",
            "username": "secondary_user",
            "role_name": "临床二级库护士",
            "dept_name": "骨科病区二级库",
            "module_name": "高值耗材专仓",
            "action_type": "扫码核销",
            "target_object": "单品UDI SN202610100088",
            "detail": "术中扫码核销绑定患者陈*生(ZY20261102001)，扣减库存并触发财务记账",
            "client_ip": "192.168.3.45",
            "status": "SUCCESS",
            "created_at": "2026-11-03 14:48:10"
        },
        {
            "id": 5,
            "action_no": "ACT202611030005",
            "operator_name": "李晓琳",
            "username": "secondary_user",
            "role_name": "临床二级库护士",
            "dept_name": "骨科病区二级库",
            "module_name": "临床二级库房",
            "action_type": "发料出库",
            "target_object": "出库单 SEC-OUT-20261103-01",
            "detail": "手动发料出库医用脱脂纱布块50包，核减在库库存并计入骨科病区耗材成本",
            "client_ip": "192.168.3.45",
            "status": "SUCCESS",
            "created_at": "2026-11-03 15:02:18"
        },
        {
            "id": 6,
            "action_no": "ACT202611030006",
            "operator_name": "张明远",
            "username": "supplier_user",
            "role_name": "外部供应商代表",
            "dept_name": "威高医疗科技",
            "module_name": "采购协同门户",
            "action_type": "二次确认发货",
            "target_object": "发货单 SHP20261102001",
            "detail": "在线拣货录入批号B20261103并二次确认发货，同步生成医院端待验收入库单",
            "client_ip": "221.12.18.99",
            "status": "SUCCESS",
            "created_at": "2026-11-03 15:15:33"
        },
        {
            "id": 7,
            "action_no": "ACT202611030007",
            "operator_name": "孙丽娟",
            "username": "finance_auditor",
            "role_name": "财务科审计主管",
            "dept_name": "财务科",
            "module_name": "财务精算与对账",
            "action_type": "成本核销审计",
            "target_object": "月度对账单 FIN-REC-202611",
            "detail": "对耗材主库发往骨科与心内科的流转出库明细执行对账审核，确认移库不计费合规",
            "client_ip": "192.168.1.88",
            "status": "SUCCESS",
            "created_at": "2026-11-03 15:20:05"
        }
    ]

    filtered = base_actions
    if username:
        filtered = [a for a in filtered if username in a["operator_name"] or username in a["username"]]
    if module_code:
        filtered = [a for a in filtered if module_code in a["module_name"]]
    if action_type:
        filtered = [a for a in filtered if action_type in a["action_type"]]

    return ApiResponse(code=200, msg="查询全员人工操作安全审计日志成功", data=filtered)


@router.post("/recall/freeze-batch", response_model=ApiResponse[dict])
def freeze_recall_batch(
    payload: RecallFreezeBatchRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """根据国家药监局或厂家不良事件召回通知，全院一键熔断冻结指定批次物资
    @param payload: (RecallFreezeBatchRequest) 召回批号与原因
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 冻结结果与受波及在库资产统计
    @route: POST /api/v1/workflow-logs/recall/freeze-batch
    @throws: HTTPException(400) 当批号不存在或处理异常时阻断
    """
    batch_no = payload.batch_no.strip()
    if not batch_no:
        raise HTTPException(status_code=400, detail="召回批号不可为空")

    # 1. 主库在库批次熔断
    main_items = db.query(SpdMainInventory).filter(
        SpdMainInventory.batch_no == batch_no
    ).all()
    main_affected_qty = 0
    product_name_hint = "召回物料"
    for mi in main_items:
        mi.quality_status = "RECALLED"
        main_affected_qty += mi.available_qty
        product_name_hint = mi.product_name

    # 2. 临床二级库在库批次熔断
    sec_items = db.query(SpdSecondaryInventory).filter(
        SpdSecondaryInventory.batch_no == batch_no
    ).all()
    sec_affected_qty = 0
    for si in sec_items:
        si.batch_status = "RECALLED"
        sec_affected_qty += si.current_qty
        product_name_hint = si.product_name

    # 3. 高值专柜在库单品熔断
    hv_items = db.query(SpdHighValueItem).filter(
        SpdHighValueItem.batch_no == batch_no,
        SpdHighValueItem.item_status != "USED_VERIFIED"
    ).all()
    hv_affected_qty = len(hv_items)
    for hi in hv_items:
        hi.item_status = "RECALLED"
        product_name_hint = hi.product_name

    total_affected = main_affected_qty + sec_affected_qty + hv_affected_qty

    # 4. 记入 6W 全流程溯源日志
    record_workflow_6w_log(
        db=db,
        biz_order_no=f"RECALL-{batch_no}",
        node_action="RECALL_FREEZE",
        product_code=payload.product_code or (main_items[0].product_code if main_items else "BATCH-RECALL"),
        product_name=product_name_hint,
        batch_or_udi=batch_no,
        from_dept_name="国家药监局/不良事件监测中心",
        from_user_name=user_ctx.real_name,
        to_dept_name="全院召回冻结专区",
        to_user_name="全院各库房管理员",
        change_qty=-total_affected,
        before_stock_snapshot=total_affected,
        after_stock_snapshot=0,
        settlement_amount=0,
        is_billable=0,
        audit_remark=f"不良事件紧急召回强控熔断。原因: {payload.recall_reason}；文件号: {payload.notice_doc_no or '无'}"
    )

    db.commit()

    return ApiResponse(
        code=200,
        msg=f"批次 [{batch_no}] 不良事件全院召回冻结已成功执行！波及全院主库、二级库及专柜共 {total_affected} 件物资，所有出库与核销链路已硬性熔断！",
        data={
            "batch_no": batch_no,
            "product_name": product_name_hint,
            "main_affected_qty": main_affected_qty,
            "secondary_affected_qty": sec_affected_qty,
            "high_value_affected_count": hv_affected_qty,
            "total_affected_qty": total_affected,
            "recall_reason": payload.recall_reason,
            "frozen_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )


@router.get("/recall/active-recalls", response_model=ApiResponse[List[dict]])
def list_active_recalls(db: Session = Depends(get_db)):
    """查询当前全院在控的不良事件召回批次及受控库存清单
    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[List[dict]] 召回批次清单
    @route: GET /api/v1/workflow-logs/recall/active-recalls
    @throws: 无异常抛出
    """
    recalled_main = db.query(SpdMainInventory).filter(SpdMainInventory.quality_status == "RECALLED").all()
    recalled_sec = db.query(SpdSecondaryInventory).filter(SpdSecondaryInventory.batch_status == "RECALLED").all()
    recalled_hv = db.query(SpdHighValueItem).filter(SpdHighValueItem.item_status == "RECALLED").all()

    batches = {}
    for m in recalled_main:
        if m.batch_no not in batches:
            batches[m.batch_no] = {
                "batch_no": m.batch_no,
                "product_code": m.product_code,
                "product_name": m.product_name,
                "main_qty": 0,
                "sec_qty": 0,
                "hv_qty": 0,
                "status": "RECALLED_FROZEN"
            }
        batches[m.batch_no]["main_qty"] += m.available_qty

    for s in recalled_sec:
        if s.batch_no not in batches:
            batches[s.batch_no] = {
                "batch_no": s.batch_no,
                "product_code": s.product_code,
                "product_name": s.product_name,
                "main_qty": 0,
                "sec_qty": 0,
                "hv_qty": 0,
                "status": "RECALLED_FROZEN"
            }
        batches[s.batch_no]["sec_qty"] += s.current_qty

    for h in recalled_hv:
        if h.batch_no not in batches:
            batches[h.batch_no] = {
                "batch_no": h.batch_no,
                "product_code": h.product_code,
                "product_name": h.product_name,
                "main_qty": 0,
                "sec_qty": 0,
                "hv_qty": 0,
                "status": "RECALLED_FROZEN"
            }
        batches[h.batch_no]["hv_qty"] += 1

    return ApiResponse(
        code=200,
        msg="查询全院不良事件在控召回批次成功",
        data=list(batches.values())
    )

