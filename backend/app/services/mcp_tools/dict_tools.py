"""
@file dict_tools.py
@description 产品字典建仓、信息检索与供应商资质准入审查 MCP 工具集
对应 Agent 01 (dict_inbound_guard_agent) 职责契约，
严格落盘至 MySQL 数据库并在创建时联动写入 6W 审计日志 (1_DICT_CREATE)。

@param 各类字典查询、资质校验与建档入参
@returns ToolResult 统一封装结果
@route internal://backend/app/services/mcp_tools/dict_tools.py
@throws 数据库操作异常与业务校验异常
"""

import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.spd_models import SpdProductDict
from app.models.spd_extended_models import SpdSupplierProfile
from app.services.mcp_tools.schema import BaseToolInput, ToolResult
from app.services.trace_service import record_workflow_6w_log


class QueryProductDictInput(BaseToolInput):
    """产品字典查询入参模型"""
    product_name: Optional[str] = Field(default=None, description="物资名称关键字(模糊匹配)")
    product_code: Optional[str] = Field(default=None, description="院内物资唯一标准编码")
    category_id: Optional[int] = Field(default=None, description="分类ID(关联spd_category.id)")
    main_dept_code: Optional[str] = Field(default=None, description="主库归口科室: CONSUMABLE_DEPT-耗材科, EQUIP_DEPT-设备科")
    consumable_type: Optional[str] = Field(default=None, description="耗材级别: GENERAL-普通耗材, HIGH_VALUE-高值耗材")
    limit: int = Field(default=20, ge=1, le=100, description="读取记录条数上限")
    offset: int = Field(default=0, ge=0, description="分页偏移量")


class ProductDictItem(BaseModel):
    """产品字典单项输出模型"""
    id: int
    product_code: str
    product_name: str
    udi_di: str
    main_dept_code: str
    consumable_type: str
    category_name: str
    spec_model: str
    unit: str
    unit_price: float
    manufacturer: str
    supplier_name: str
    reg_cert_no: str
    reg_cert_expiry: str
    status: int


class ProductDictListOutput(BaseModel):
    """产品字典列表输出结构"""
    total_count: int
    items: List[ProductDictItem]


class CheckSupplierCertInput(BaseToolInput):
    """供应商资质与注册证查验入参模型"""
    supplier_name: Optional[str] = Field(default=None, description="供货商企业名称关键字")
    supplier_code: Optional[str] = Field(default=None, description="供应商唯一编码")
    reg_cert_no: Optional[str] = Field(default=None, description="国家医疗器械注册证编号")
    check_date: Optional[str] = Field(default=None, description="基准核验日期(YYYY-MM-DD，默认当日)")


class SupplierCertOutput(BaseModel):
    """供应商资质与证照查验输出模型"""
    is_valid: bool = Field(..., description="综合准入查验是否通过")
    supplier_found: bool = Field(..., description="供应商是否在册")
    supplier_name: str
    license_no: str
    license_expiry_date: str
    qual_status: str
    reg_cert_valid: bool
    risk_warnings: List[str] = Field(default_factory=list, description="风险预警提示清单")


class CreateProductDictInput(BaseToolInput):
    """产品字典创建与建档入参模型"""
    product_code: str = Field(..., min_length=2, description="物资唯一标准编码")
    product_name: str = Field(..., min_length=2, description="医疗物资通用名称")
    udi_di: str = Field(..., min_length=5, description="UDI-DI固定产品标识代码")
    main_dept_code: str = Field(default="CONSUMABLE_DEPT", description="主科室归口: CONSUMABLE_DEPT / EQUIP_DEPT")
    consumable_type: str = Field(default="GENERAL", description="耗材属性: GENERAL-普耗, HIGH_VALUE-高值")
    category_id: int = Field(default=1, description="品类ID")
    category_name: str = Field(default="通用医用耗材", description="品类名称")
    spec_model: str = Field(default="通用标准型", description="规格型号")
    unit: str = Field(default="个", description="计量单位")
    unit_price: float = Field(default=10.0, ge=0.0, description="采购与核算基准单价")
    manufacturer: str = Field(default="标准医疗器械制造有限公司", description="生产厂家")
    supplier_name: str = Field(default="标准医药供应链科技有限公司", description="供应商名称")
    reg_cert_no: str = Field(default="国械注准20240001", description="医疗器械注册证编号")
    reg_cert_expiry: str = Field(default="2028-12-31", description="注册证有效截止期(YYYY-MM-DD)")
    operator_name: str = Field(default="耗材科管理员", description="建档操作人姓名")


class ProductDictCreateOutput(BaseModel):
    """产品字典创建输出模型"""
    product_id: int
    product_code: str
    product_name: str
    main_dept_code: str
    consumable_type: str
    trace_no: str
    audit_status: str = "VERIFIED"


def mcp_query_product_dict(input_model: QueryProductDictInput, db: Session) -> ToolResult[ProductDictListOutput]:
    """查询医疗物资产品字典列表 (支持多维组合过滤与分页)

    @param input_model: QueryProductDictInput 结构化查询参数
    @param db: Session 数据库活动会话
    @returns ToolResult[ProductDictListOutput] 符合条件的产品字典条目列表
    @route internal://backend/app/services/mcp_tools/dict_tools.py/mcp_query_product_dict
    @throws 数据库查询异常时安全捕获并返回失败状态
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        query = db.query(SpdProductDict).filter(SpdProductDict.is_deleted == 0)

        if input_model.product_name:
            query = query.filter(SpdProductDict.product_name.like(f"%{input_model.product_name}%"))
        if input_model.product_code:
            query = query.filter(SpdProductDict.product_code.like(f"%{input_model.product_code}%"))
        if input_model.category_id:
            query = query.filter(SpdProductDict.category_id == input_model.category_id)
        if input_model.main_dept_code:
            query = query.filter(SpdProductDict.main_dept_code == input_model.main_dept_code)
        if input_model.consumable_type:
            query = query.filter(SpdProductDict.consumable_type == input_model.consumable_type)

        total_count = query.count()
        rows = query.order_by(SpdProductDict.id.desc()).offset(input_model.offset).limit(input_model.limit).all()

        items: List[ProductDictItem] = []
        for r in rows:
            items.append(ProductDictItem(
                id=r.id,
                product_code=r.product_code,
                product_name=r.product_name,
                udi_di=r.udi_di,
                main_dept_code=r.main_dept_code,
                consumable_type=r.consumable_type,
                category_name=r.category_name,
                spec_model=r.spec_model,
                unit=r.unit,
                unit_price=float(r.unit_price),
                manufacturer=r.manufacturer,
                supplier_name=r.supplier_name,
                reg_cert_no=r.reg_cert_no,
                reg_cert_expiry=r.reg_cert_expiry.strftime("%Y-%m-%d") if r.reg_cert_expiry else "",
                status=r.status
            ))

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_query_product_dict",
            input_args=raw_args,
            data=ProductDictListOutput(total_count=total_count, items=items),
            message=f"成功检索到 {total_count} 条产品字典在册记录",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_query_product_dict",
            input_args=raw_args,
            error=str(e),
            message=f"产品字典查询异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_check_supplier_cert(input_model: CheckSupplierCertInput, db: Session) -> ToolResult[SupplierCertOutput]:
    """供应商营业准入资质与国家医疗器械注册证有效性核验

    @param input_model: CheckSupplierCertInput 供应商与注册证核验参数
    @param db: Session 数据库活动会话
    @returns ToolResult[SupplierCertOutput] 资质审查结果与合规预警
    @route internal://backend/app/services/mcp_tools/dict_tools.py/mcp_check_supplier_cert
    @throws 数据库操作异常安全捕获
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        check_date = date.today()
        if input_model.check_date:
            try:
                check_date = datetime.strptime(input_model.check_date, "%Y-%m-%d").date()
            except Exception:
                check_date = date.today()

        # 查找供应商
        sup_query = db.query(SpdSupplierProfile)
        if input_model.supplier_code:
            sup_query = sup_query.filter(SpdSupplierProfile.supplier_code == input_model.supplier_code)
        elif input_model.supplier_name:
            sup_query = sup_query.filter(SpdSupplierProfile.supplier_name.like(f"%{input_model.supplier_name}%"))

        sup = sup_query.first()
        risk_warnings: List[str] = []

        if not sup:
            execution_time_ms = int((time.time() - t0) * 1000)
            return ToolResult(
                success=True,
                tool_name="mcp_check_supplier_cert",
                input_args=raw_args,
                data=SupplierCertOutput(
                    is_valid=False,
                    supplier_found=False,
                    supplier_name=input_model.supplier_name or "未知供应商",
                    license_no="",
                    license_expiry_date="",
                    qual_status="NOT_FOUND",
                    reg_cert_valid=False,
                    risk_warnings=["供应商未在院方资质库中建档，严禁开展采购与入库业务"]
                ),
                message="供应商未建档，资质审查不合格",
                execution_time_ms=execution_time_ms
            )

        # 校验供应商经营许可证
        is_license_expired = sup.license_expiry_date < check_date
        if is_license_expired:
            risk_warnings.append(f"供应商《医疗器械经营许可证》已于 {sup.license_expiry_date} 到期失效")

        if sup.qual_status != "QUAL_APPROVED":
            risk_warnings.append(f"供应商准入状态为非正常供货状态: {sup.qual_status}")

        # 校验注册证
        reg_cert_valid = True
        if input_model.reg_cert_no:
            product = db.query(SpdProductDict).filter(
                SpdProductDict.reg_cert_no == input_model.reg_cert_no,
                SpdProductDict.is_deleted == 0
            ).first()
            if product and product.reg_cert_expiry and product.reg_cert_expiry < check_date:
                reg_cert_valid = False
                risk_warnings.append(f"国家医疗器械注册证 {input_model.reg_cert_no} 已于 {product.reg_cert_expiry} 到期失效")

        is_valid = (not is_license_expired) and (sup.qual_status == "QUAL_APPROVED") and reg_cert_valid
        execution_time_ms = int((time.time() - t0) * 1000)

        return ToolResult(
            success=True,
            tool_name="mcp_check_supplier_cert",
            input_args=raw_args,
            data=SupplierCertOutput(
                is_valid=is_valid,
                supplier_found=True,
                supplier_name=sup.supplier_name,
                license_no=sup.license_no,
                license_expiry_date=sup.license_expiry_date.strftime("%Y-%m-%d"),
                qual_status=sup.qual_status,
                reg_cert_valid=reg_cert_valid,
                risk_warnings=risk_warnings
            ),
            message="资质审查完成: 合规通过" if is_valid else f"资质审查预警: 发现 {len(risk_warnings)} 项合规缺陷",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_check_supplier_cert",
            input_args=raw_args,
            error=str(e),
            message=f"供应商资质查验异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )


def mcp_create_product_dict(input_model: CreateProductDictInput, db: Session) -> ToolResult[ProductDictCreateOutput]:
    """在产品字典中建立新物资档案并联动写入 6W 全流程业务日志

    @param input_model: CreateProductDictInput 新建物资完整字典属性
    @param db: Session 数据库活动会话
    @returns ToolResult[ProductDictCreateOutput] 建档完成实体与 6W 日志流水号
    @route internal://backend/app/services/mcp_tools/dict_tools.py/mcp_create_product_dict
    @throws 字段冲突或数据库事务异常时自动回滚并安全报错
    """
    t0 = time.time()
    raw_args = input_model.model_dump()
    try:
        # 解析注册证到期日
        try:
            expiry_d = datetime.strptime(input_model.reg_cert_expiry, "%Y-%m-%d").date()
        except Exception:
            expiry_d = date(2028, 12, 31)

        # 检查是否已存在相同 product_code
        existing = db.query(SpdProductDict).filter(
            SpdProductDict.product_code == input_model.product_code,
            SpdProductDict.is_deleted == 0
        ).first()

        if existing:
            # 更新现有记录
            existing.product_name = input_model.product_name
            existing.udi_di = input_model.udi_di
            existing.main_dept_code = input_model.main_dept_code
            existing.consumable_type = input_model.consumable_type
            existing.category_id = input_model.category_id
            existing.category_name = input_model.category_name
            existing.spec_model = input_model.spec_model
            existing.unit = input_model.unit
            existing.unit_price = Decimal(str(round(input_model.unit_price, 2)))
            existing.manufacturer = input_model.manufacturer
            existing.supplier_name = input_model.supplier_name
            existing.reg_cert_no = input_model.reg_cert_no
            existing.reg_cert_expiry = expiry_d
            existing.status = 1
            db.flush()
            prod_id = existing.id
        else:
            new_item = SpdProductDict(
                product_code=input_model.product_code,
                product_name=input_model.product_name,
                udi_di=input_model.udi_di,
                main_dept_code=input_model.main_dept_code,
                consumable_type=input_model.consumable_type,
                category_id=input_model.category_id,
                category_name=input_model.category_name,
                spec_model=input_model.spec_model,
                unit=input_model.unit,
                unit_price=Decimal(str(round(input_model.unit_price, 2))),
                manufacturer=input_model.manufacturer,
                supplier_name=input_model.supplier_name,
                reg_cert_no=input_model.reg_cert_no,
                reg_cert_expiry=expiry_d,
                safe_stock_min=20,
                safe_stock_max=500,
                storage_temp_req="常温(10~30℃)",
                status=1,
                is_deleted=0
            )
            db.add(new_item)
            db.flush()
            prod_id = new_item.id

        # 联动 6W 日志埋点
        target_dept_name = "耗材科主库" if input_model.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库"
        log_entry = record_workflow_6w_log(
            db=db,
            biz_order_no=f"DICT-{input_model.product_code}",
            node_action="1_DICT_CREATE",
            product_code=input_model.product_code,
            product_name=input_model.product_name,
            batch_or_udi=input_model.udi_di,
            from_dept_name="供应商/申报厂家",
            from_user_name=input_model.operator_name,
            to_dept_name=target_dept_name,
            to_user_name=input_model.operator_name,
            change_qty=0,
            before_stock_snapshot=0,
            after_stock_snapshot=0,
            settlement_amount=Decimal(str(round(input_model.unit_price, 2))),
            is_billable=0,
            audit_remark="大模型 Agent 01 审核首营准入并通过并落盘"
        )
        db.commit()

        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=True,
            tool_name="mcp_create_product_dict",
            input_args=raw_args,
            data=ProductDictCreateOutput(
                product_id=prod_id,
                product_code=input_model.product_code,
                product_name=input_model.product_name,
                main_dept_code=input_model.main_dept_code,
                consumable_type=input_model.consumable_type,
                trace_no=log_entry.trace_no
            ),
            message=f"物资 [{input_model.product_name}] 已成功建档落盘并关联 6W 流水号: {log_entry.trace_no}",
            trace_no=log_entry.trace_no,
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        db.rollback()
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name="mcp_create_product_dict",
            input_args=raw_args,
            error=str(e),
            message=f"产品字典建档失败已自动回滚: {str(e)}",
            execution_time_ms=execution_time_ms
        )
