"""全流程 6W 业务链路日志埋点与高值耗材拆包赋码服务模块

本模块严格执行 Skill 05 (workflow_6w_trace_logger) 与 Skill 03 (main_to_high_value_split_code)。
"""

import time
import random
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.spd_models import (
    SpdWorkflowLog,
    SpdHighValueItem,
    SpdMainInventory,
    SpdProductDict
)


def generate_trace_no() -> str:
    """生成全局唯一的 6W 流转日志流水号

    @param: 无入参
    @returns: (str) 流水号 (如: TRACE-20261102120000-8848)
    @route: 内部工具链路 backend.app.services.trace_service.generate_trace_no
    @throws: 无异常抛出
    """
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand_suffix = random.randint(1000, 9999)
    return f"TRACE-{ts}-{rand_suffix}"


def record_workflow_6w_log(
    db: Session,
    biz_order_no: str,
    node_action: str,
    product_code: str,
    product_name: str,
    batch_or_udi: str,
    from_dept_name: str,
    from_user_name: str,
    to_dept_name: str,
    to_user_name: str,
    change_qty: int,
    before_stock_snapshot: int = 0,
    after_stock_snapshot: int = 0,
    settlement_amount: Decimal = Decimal("0.00"),
    is_billable: int = 0,
    audit_remark: Optional[str] = None
) -> SpdWorkflowLog:
    """全流程业务链路 6W 物权交接日志统一埋点写入服务 (Skill 05)

    @param: db (Session) 数据库活动会话
    @param: biz_order_no (str) 关联业务单号
    @param: node_action (str) 8大流转节点标识
    @param: product_code (str) 物资编码
    @param: product_name (str) 物资名称
    @param: batch_or_udi (str) 批号或UDI码
    @param: from_dept_name (str) 交出方科室
    @param: from_user_name (str) 交出人姓名
    @param: to_dept_name (str) 接收方科室
    @param: to_user_name (str) 接收人姓名
    @param: change_qty (int) 变动数量
    @param: before_stock_snapshot (int) 变动前库存
    @param: after_stock_snapshot (int) 变动后库存
    @param: settlement_amount (Decimal) 涉及金额
    @param: is_billable (int) 是否触发财务记账 (0-移库不计费, 1-消耗即结算)
    @param: audit_remark (Optional[str]) 批注说明
    @returns: SpdWorkflowLog 持久化保存的日志实体
    @route: 内部服务链路 backend.app.services.trace_service.record_workflow_6w_log
    @throws: 数据库写入异常时由外层事务捕获回滚
    """
    log_entry = SpdWorkflowLog(
        trace_no=generate_trace_no(),
        biz_order_no=biz_order_no,
        node_action=node_action,
        product_code=product_code,
        product_name=product_name,
        batch_or_udi=batch_or_udi,
        from_dept_name=from_dept_name,
        from_user_name=from_user_name,
        to_dept_name=to_dept_name,
        to_user_name=to_user_name,
        change_qty=change_qty,
        before_stock_snapshot=before_stock_snapshot,
        after_stock_snapshot=after_stock_snapshot,
        settlement_amount=settlement_amount,
        is_billable=is_billable,
        audit_status="VERIFIED",
        audit_remark=audit_remark or f"执行业务节点 {node_action} 自动留痕"
    )
    db.add(log_entry)
    db.flush()
    return log_entry


def split_batch_to_high_value_udi(
    db: Session,
    main_inv: SpdMainInventory,
    product: SpdProductDict,
    dist_order_no: str,
    dist_qty: int,
    wh_cabinet_code: str = "高值专仓-智能柜01-A01格",
    operator_name: str = "耗材科管理员"
) -> List[SpdHighValueItem]:
    """主库向高值耗材专仓按需分发时“由量到码”拆包赋码服务 (Skill 03)

    @param: db (Session) 数据库活动会话
    @param: main_inv (SpdMainInventory) 主库批次库存记录
    @param: product (SpdProductDict) 产品字典档案
    @param: dist_order_no (str) 关联按需分发单号
    @param: dist_qty (int) 拆包数量
    @param: wh_cabinet_code (str) 专仓存放柜号
    @param: operator_name (str) 操作人姓名
    @returns: List[SpdHighValueItem] 生成的单品一物一码列表
    @route: 内部服务链路 backend.app.services.trace_service.split_batch_to_high_value_udi
    @throws: 当主库可用库存不足时抛出 ValueError
    """
    if main_inv.available_qty < dist_qty:
        raise ValueError(f"主库可用数量 ({main_inv.available_qty}) 不足，无法拆包分发 {dist_qty}")

    items = []
    base_ts = datetime.now().strftime("%Y%m%d%H%M")
    clean_batch = main_inv.batch_no.replace("-", "")

    for i in range(dist_qty):
        seq = f"{i+1:04d}"
        udi_sn = f"SN{clean_batch}{seq}{random.randint(10, 99)}"
        # 构建 GS1-128 格式 UDI 字符串: (01)DI (10)批号 (17)效期 (21)序列号
        exp_str = main_inv.expiry_date.strftime("%y%m%d")
        udi_full = f"(01){product.udi_di}(10){main_inv.batch_no}(17){exp_str}(21){udi_sn}"

        item = SpdHighValueItem(
            udi_full_code=udi_full,
            udi_sn=udi_sn,
            dist_order_no=dist_order_no,
            product_id=product.id,
            product_code=product.product_code,
            product_name=product.product_name,
            spec_model=product.spec_model,
            main_dept_code=product.main_dept_code,
            batch_no=main_inv.batch_no,
            expiry_date=main_inv.expiry_date,
            unit_price=main_inv.unit_price,
            wh_cabinet_code=wh_cabinet_code,
            current_dept_id=2,  # 默认为耗材科下属高值专仓
            current_dept_name="高值耗材专仓",
            item_status="IN_HIGH_VALUE_WH"
        )
        db.add(item)
        items.append(item)

    # 扣减主库库存
    before_qty = main_inv.available_qty
    main_inv.available_qty -= dist_qty
    after_qty = main_inv.available_qty

    # 记录全流程日志 4_HIGH_VALUE_CODE
    record_workflow_6w_log(
        db=db,
        biz_order_no=dist_order_no,
        node_action="4_HIGH_VALUE_CODE",
        product_code=product.product_code,
        product_name=product.product_name,
        batch_or_udi=f"批量拆包生成 {dist_qty} 个唯一 UDI 序列号",
        from_dept_name="耗材科主库房",
        from_user_name=operator_name,
        to_dept_name="高值耗材专仓",
        to_user_name="高值仓管理员",
        change_qty=dist_qty,
        before_stock_snapshot=before_qty,
        after_stock_snapshot=after_qty,
        settlement_amount=main_inv.unit_price * Decimal(dist_qty),
        is_billable=0,  # 移库不计费
        audit_remark=f"主库向高值专仓调拨拆包，已生成 {dist_qty} 条独立一物一码单品"
    )

    db.flush()
    return items
