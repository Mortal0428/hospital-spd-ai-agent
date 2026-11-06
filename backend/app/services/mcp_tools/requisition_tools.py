"""
@file requisition_tools.py
@description 临床二级库自然语言申领、主库可用性核验与手术定数包规范查验 MCP 工具集
对应 Agent 03 (secondary_apply_qa_agent) 职责契约，
严格遵循 Pydantic V2 校验，真实落盘申领单据并联动 6W 审计日志 (6_SEC_APPLY)。

@param 各类申领前置核查、申领建单与手术定数包查验入参
@returns ToolResult 统一封装结果
@route internal://backend/app/services/mcp_tools/requisition_tools.py
@throws 字典未建档、非正整数数量与数据库异常
"""

import random
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.spd_models import (
    SpdMainInventory,
    SpdProductDict,
    SpdRequisitionOrder
)
from app.services.mcp_tools.schema import BaseToolInput, ToolResult
from app.services.trace_service import record_workflow_6w_log


class CheckMainAvailableInput(BaseToolInput):
    """主库可用性核查入参模型"""
    product_name: Optional[str] = Field(default=None, description="申领物资通用名称或关键字")
    product_code: Optional[str] = Field(default=None, description="物资标准编码")
    required_qty: int = Field(default=1, gt=0, description="申领或定数包基准需求数量")
    target_main_dept: Optional[str] = Field(default="CONSUMABLE_DEPT", description="定向主库科室: CONSUMABLE_DEPT / EQUIP_DEPT")


class MainAvailableOutput(BaseModel):
    """主库可用性核查输出模型"""
    product_found: bool
    product_id: Optional[int]
    product_code: Optional[str]
    product_name: Optional[str]
    total_available_qty: int = Field(..., description="主库当前所有正常可用批次总余量")
    is_sufficient: bool = Field(..., description="主库总余量是否充足满足需求")
    suggested_batch_no: Optional[str] = Field(default=None, description="按FEFO推荐的优先出库批次")
    unit_price: float = Field(default=0.0, description="基准参考单价(元)")


class SubmitRequisitionInput(BaseToolInput):
    """提交临床请领单入参模型"""
    product_name: str = Field(..., min_length=1, description="申领物资名称(必填，支持模糊自动匹配产品字典)")
    apply_dept_id: Optional[int] = Field(default=1, description="申领临床科室ID(关联sys_department.id)")
    apply_dept_name: str = Field(default="骨科病区二级库", min_length=2, description="申领临床科室名称(如: 心内科二级库)")
    product_id: Optional[int] = Field(default=None, description="关联产品字典主键ID")
    product_code: Optional[str] = Field(default=None, description="物资标准编码")
    apply_qty: int = Field(default=20, gt=0, description="申请领用数量(必须为大于0的正整数)")
    urgency_level: str = Field(default="ROUTINE", description="紧急程度: ROUTINE-日常定数包补货, URGENT-手术急用加急")
    applicant_id: int = Field(default=1, description="申领人用户ID")
    applicant_name: str = Field(default="临床二级库护士", min_length=2, description="申领人真实姓名")
    apply_reason: Optional[str] = Field(default="自然语言智能体申领自动建单", description="申领事由说明")
    reason: Optional[str] = Field(default=None, description="申领事由别名兼容")
    target_main_dept: Optional[str] = Field(default="CONSUMABLE_DEPT", description="接收审批的主库科室")


class RequisitionOrderOutput(BaseModel):
    """临床请领单创建输出模型"""
    order_id: int
    req_order_no: str
    apply_dept_name: str
    product_name: str
    product_code: str
    apply_qty: int
    req_status: str
    urgency_level: str
    trace_no: str


class QuerySurgeryPackSpecsInput(BaseToolInput):
    """手术定数包规范查验入参模型"""
    pack_name: Optional[str] = Field(default=None, description="定数包名称关键字(如: 骨科接骨定数包, 介入穿刺定数包)")
    dept_name: Optional[str] = Field(default=None, description="临床科室名称")


class SurgeryPackComponent(BaseModel):
    """定数包内部标准组件项"""
    product_code: str
    product_name: str
    spec_model: str
    standard_qty: int
    unit: str
    main_stock_available: int
    is_in_stock: bool


class SurgeryPackItem(BaseModel):
    """手术定数包结构模型"""
    pack_id: str
    pack_name: str
    target_surgery: str
    target_dept: str
    total_components_count: int
    all_in_stock: bool
    components: List[SurgeryPackComponent]


class SurgeryPackSpecsOutput(BaseModel):
    """手术定数包查询输出结构"""
    packs_count: int
    packs: List[SurgeryPackItem]


def mcp_check_main_available(input_model: CheckMainAvailableInput, db: Session) -> ToolResult[MainAvailableOutput]:
    """申领前核验主库可用总余量与 FEFO 优先批次

    @param input_model: CheckMainAvailableInput 待申领物资与需求量
    @param db: Session 数据库活动会话
    @returns ToolResult[MainAvailableOutput] 主库可用量与是否充足判定
    @route internal://backend/app/services/mcp_tools/requisition_tools.py/mcp_check_main_available
    @throws 数据库查询异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        # 1. 查找产品字典
        dict_query = db.query(SpdProductDict).filter(SpdProductDict.is_deleted == 0)
        if input_model.product_code:
            dict_query = dict_query.filter(SpdProductDict.product_code == input_model.product_code)
        elif input_model.product_name:
            dict_query = dict_query.filter(SpdProductDict.product_name.like(f"%{input_model.product_name}%"))

        product = dict_query.first()
        if not product:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=True,
                tool_name="mcp_check_main_available",
                input_args=raw_args,
                data=MainAvailableOutput(
                    product_found=False,
                    product_id=None,
                    product_code=input_model.product_code,
                    product_name=input_model.product_name or "未检索到在册物资",
                    total_available_qty=0,
                    is_sufficient=False,
                    suggested_batch_no=None,
                    unit_price=0.0
                ),
                message="物资未在产品字典中建档",
                execution_time_ms=execution_time_ms
            )

        # 2. 查询主库可用库存批次
        batches = db.query(SpdMainInventory).filter(
            SpdMainInventory.product_id == product.id,
            SpdMainInventory.quality_status == "NORMAL",
            SpdMainInventory.available_qty > 0
        ).order_by(SpdMainInventory.expiry_date.asc()).all()

        total_avail = sum(b.available_qty for b in batches)
        suggested_batch = batches[0].batch_no if batches else None
        is_sufficient = total_avail >= input_model.required_qty

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_check_main_available",
            input_args=raw_args,
            data=MainAvailableOutput(
                product_found=True,
                product_id=product.id,
                product_code=product.product_code,
                product_name=product.product_name,
                total_available_qty=total_avail,
                is_sufficient=is_sufficient,
                suggested_batch_no=suggested_batch,
                unit_price=float(product.unit_price)
            ),
            message=f"物资 [{product.product_name}] 主库可用总量为 {total_avail}，{'库存充足满足需求' if is_sufficient else '库存不足预警'}",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_check_main_available",
            input_args=raw_args,
            error=str(e),
            message=f"主库可用性查验异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_submit_sec_requisition(input_model: SubmitRequisitionInput, db: Session) -> ToolResult[RequisitionOrderOutput]:
    """临床二级库发起自然语言申领单，持久化落盘并联动 6W 日志

    @param input_model: SubmitRequisitionInput 申领科室、物资ID与申领数量
    @param db: Session 数据库活动会话
    @returns ToolResult[RequisitionOrderOutput] 申领单生成结果与 6W 日志号
    @route internal://backend/app/services/mcp_tools/requisition_tools.py/mcp_submit_sec_requisition
    @throws 产品不存在或事务异常回滚
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        # 查找或自适应匹配产品字典
        product = None
        if input_model.product_id:
            product = db.query(SpdProductDict).filter(SpdProductDict.id == input_model.product_id, SpdProductDict.is_deleted == 0).first()
        elif input_model.product_code:
            product = db.query(SpdProductDict).filter(SpdProductDict.product_code == input_model.product_code, SpdProductDict.is_deleted == 0).first()
        elif input_model.product_name:
            product = db.query(SpdProductDict).filter(SpdProductDict.product_name.like(f"%{input_model.product_name}%"), SpdProductDict.is_deleted == 0).first()
            if not product and len(input_model.product_name) >= 3:
                product = db.query(SpdProductDict).filter(SpdProductDict.product_name.like(f"%{input_model.product_name[:3]}%"), SpdProductDict.is_deleted == 0).first()
            if not product and len(input_model.product_name) >= 2:
                product = db.query(SpdProductDict).filter(SpdProductDict.product_name.like(f"%{input_model.product_name[:2]}%"), SpdProductDict.is_deleted == 0).first()
        if not product:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=False,
                tool_name="mcp_submit_sec_requisition",
                input_args=raw_args,
                error="PRODUCT_NOT_FOUND",
                message=f"产品字典中未检索到指定物资: {input_model.product_name or input_model.product_code or input_model.product_id}",
                execution_time_ms=execution_time_ms
            )

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand_s = random.randint(100, 999)
        req_order_no = f"REQ-{ts}-{rand_s}"
        target_main = input_model.target_main_dept or product.main_dept_code
        final_reason = input_model.reason or input_model.apply_reason or "临床科室自然语言申领"

        new_req = SpdRequisitionOrder(
            req_order_no=req_order_no,
            order_direction="APPLY_FROM_MAIN",
            apply_dept_id=input_model.apply_dept_id,
            apply_dept_name=input_model.apply_dept_name,
            target_main_dept=target_main,
            product_id=product.id,
            product_code=product.product_code,
            product_name=product.product_name,
            apply_qty=input_model.apply_qty,
            approved_qty=0,
            urgency_level=input_model.urgency_level,
            req_status="PENDING_APPROVAL",
            applicant_id=input_model.applicant_id,
            applicant_name=input_model.applicant_name,
            apply_reason=final_reason
        )
        db.add(new_req)
        db.flush()

        # 联动 6W 业务流转日志 (6_SEC_APPLY)
        log_entry = record_workflow_6w_log(
            db=db,
            biz_order_no=req_order_no,
            node_action="6_SEC_APPLY",
            product_code=product.product_code,
            product_name=product.product_name,
            batch_or_udi=product.udi_di,
            from_dept_name=input_model.apply_dept_name,
            from_user_name=input_model.applicant_name,
            to_dept_name="耗材科主库审批台" if target_main == "CONSUMABLE_DEPT" else "设备科主库审批台",
            to_user_name="待主库审批管理员",
            change_qty=input_model.apply_qty,
            before_stock_snapshot=0,
            after_stock_snapshot=0,
            settlement_amount=Decimal(str(round(float(product.unit_price) * input_model.apply_qty, 2))),
            is_billable=0,
            audit_remark=input_model.apply_reason or "二级库发起申领待批"
        )
        db.commit()

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_submit_sec_requisition",
            input_args=raw_args,
            data=RequisitionOrderOutput(
                order_id=new_req.id,
                req_order_no=req_order_no,
                apply_dept_name=input_model.apply_dept_name,
                product_name=product.product_name,
                product_code=product.product_code,
                apply_qty=input_model.apply_qty,
                req_status="PENDING_APPROVAL",
                urgency_level=input_model.urgency_level,
                trace_no=log_entry.trace_no
            ),
            message=f"申领单 [{req_order_no}] 已提交至主库审批台，关联 6W 追踪流水号: {log_entry.trace_no}",
            trace_no=log_entry.trace_no,
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        db.rollback()
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_submit_sec_requisition",
            input_args=raw_args,
            error=str(e),
            message=f"提交临床申领单失败已回滚: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_query_surgery_pack_specs(input_model: QuerySurgeryPackSpecsInput, db: Session) -> ToolResult[SurgeryPackSpecsOutput]:
    """查询临床手术定数包标准规范与主库物资库存匹配度

    @param input_model: QuerySurgeryPackSpecsInput 定数包名称与科室过滤
    @param db: Session 数据库活动会话
    @returns ToolResult[SurgeryPackSpecsOutput] 标准定数包明细与库存匹配状态
    @route internal://backend/app/services/mcp_tools/requisition_tools.py/mcp_query_surgery_pack_specs
    @throws 数据库操作异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        # 标准预置手术定数包模板
        preset_packs = [
            {
                "pack_id": "PACK_ORTHO_01",
                "pack_name": "骨科创伤接骨标准手术定数包",
                "target_surgery": "四肢骨折切开复位内固定术",
                "target_dept": "骨科病区二级库",
                "items": [
                    {"code": "WZ001", "name": "钛合金接骨螺钉", "spec": "Φ3.5*30mm", "qty": 4, "unit": "枚"},
                    {"code": "WZ003", "name": "医用无菌敷料贴", "spec": "10cm*15cm", "qty": 10, "unit": "贴"},
                    {"code": "WZ005", "name": "骨水泥充填剂", "spec": "40g/包", "qty": 1, "unit": "包"}
                ]
            },
            {
                "pack_id": "PACK_CARDIO_01",
                "pack_name": "心内介入穿刺血管造影定数包",
                "target_surgery": "经皮冠状动脉造影及介入术",
                "target_dept": "心血管内科二级库",
                "items": [
                    {"code": "WZ002", "name": "冠脉球囊扩张导管", "spec": "2.5*15mm", "qty": 2, "unit": "根"},
                    {"code": "WZ004", "name": "一次性无菌穿刺针", "spec": "18G*70mm", "qty": 3, "unit": "支"},
                    {"code": "WZ003", "name": "医用无菌敷料贴", "spec": "10cm*15cm", "qty": 5, "unit": "贴"}
                ]
            }
        ]

        result_packs: List[SurgeryPackItem] = []
        for p in preset_packs:
            if input_model.pack_name and input_model.pack_name not in p["pack_name"]:
                continue
            if input_model.dept_name and input_model.dept_name not in p["target_dept"]:
                continue

            comps: List[SurgeryPackComponent] = []
            all_in_stock = True
            for item in p["items"]:
                # 动态查询主库可用量
                main_inv = db.query(func.coalesce(func.sum(SpdMainInventory.available_qty), 0)).filter(
                    SpdMainInventory.product_name.like(f"%{item['name']}%"),
                    SpdMainInventory.quality_status == "NORMAL"
                ).scalar()

                avail_qty = int(main_inv or 0)
                is_ok = avail_qty >= item["qty"]
                if not is_ok:
                    all_in_stock = False

                comps.append(SurgeryPackComponent(
                    product_code=item["code"],
                    product_name=item["name"],
                    spec_model=item["spec"],
                    standard_qty=item["qty"],
                    unit=item["unit"],
                    main_stock_available=avail_qty,
                    is_in_stock=is_ok
                ))

            result_packs.append(SurgeryPackItem(
                pack_id=p["pack_id"],
                pack_name=p["pack_name"],
                target_surgery=p["target_surgery"],
                target_dept=p["target_dept"],
                total_components_count=len(comps),
                all_in_stock=all_in_stock,
                components=comps
            ))

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_query_surgery_pack_specs",
            input_args=raw_args,
            data=SurgeryPackSpecsOutput(packs_count=len(result_packs), packs=result_packs),
            message=f"检索到 {len(result_packs)} 组标准临床手术定数包规范",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_query_surgery_pack_specs",
            input_args=raw_args,
            error=str(e),
            message=f"手术定数包规范查询异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )
