"""Pydantic V2 深度扩展业务模块请求校验与响应 Schema 模型定义

涵盖：
1. 信息科解耦式 15 模块 x 8 动作细粒度权限矩阵 Schema
2. 产品字典深度扩展管理(仓库树/拼音码/复制品名到其他仓库/变更供应商/调价/显示停用) Schema
3. 普通耗材与二级库出入库、退给供应商红字单、请领审核自动出库、科室期初数据(二次确认永久锁死) Schema
4. 全院各科室独立盘点与跨科/跨院调拨 Schema
5. 高值耗材备货、接收、科室退货(二次确认永久锁死)、报损与一物一码二维码扫码核销 Schema
6. 多级采购计划、供应商经营资质准入与拣货发货协同 Schema
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class PermissionToggleRequest(BaseModel):
    """信息科管理员针对具体人员独立开关模块 8 项原子权限请求"""
    user_id: int = Field(..., description="目标用户主键ID")
    module_code: str = Field(..., description="业务模块编码(如: DICT_MANAGE, GEN_INBOUND, GEN_INIT_STOCK, HV_RETURN, SUPPLIER_SHIP)")
    action_key: str = Field(..., description="原子动作字段名: can_view/can_create/can_edit/can_delete/can_second_confirm/can_cancel_submit/can_approve/can_print")
    enabled: int = Field(..., ge=0, le=1, description="开关值: 1-开启允许, 0-关闭禁止")
    operator_name: str = Field(default="陈工(信息科管理员)", description="执行授权变更的信息科管理员")


class ProductDictExtUpdateRequest(BaseModel):
    """产品字典深度扩展属性新增或修改请求"""
    product_id: int = Field(..., description="关联主产品字典ID")
    common_name: str = Field(..., description="耗材通用名")
    component_name: Optional[str] = Field(default=None, description="组件名称")
    brand_name: str = Field(default="国产品牌", description="品牌名称")
    supplier_code: str = Field(default="SUP_WEGO_01", description="绑定供应商编码")
    is_disabled: int = Field(default=0, ge=0, le=1, description="停用标记: 0-在用, 1-停用")
    extra_fields_json: Optional[str] = Field(default=None, description="自定义扩展属性JSON字符串") 


class CopyWarehouseRequest(BaseModel):
    """复制品名/规格到其他仓库请求"""
    product_id: int = Field(..., description="源产品ID")
    target_warehouse_code: str = Field(..., description="目标仓库编码(如: WH_ZONGWU, WH_EQUIP, WH_SEC_CARDIO)")


class PriceAdjustRequest(BaseModel):
    """产品字典调价管理请求"""
    product_id: int = Field(..., description="目标产品ID")
    new_price: Decimal = Field(..., gt=0, description="调整后新单价(元)")
    reason: str = Field(..., description="调价原因说明")


class InboundOutboundCreateRequest(BaseModel):
    """创建通用出入库单、退给供应商红字退货单或期初数据建账单请求(第1次填单提交)"""
    order_type: str = Field(..., description="单据类型: GEN_INBOUND/RETURN_TO_SUPPLIER/GEN_MANUAL_OUT/INIT_STOCK/SEC_RECEIVE_IN/SEC_ISSUE_OUT")
    warehouse_code: str = Field(..., description="所属仓库编码(如: WH_WEICAI, WH_SEC_ORTHO)")
    dept_code: str = Field(..., description="所属科室编码")
    target_dept_or_supplier: str = Field(..., description="往来单位(供应商编码或领用科室编码)")
    product_id: int = Field(..., description="关联产品ID")
    batch_no: str = Field(default="BATCH-202611", description="生产批号")
    quantity: int = Field(..., gt=0, description="业务数量(退给供应商时系统自动转为负向红冲)")
    created_by: str = Field(..., description="第1次填单提交人姓名")
    remark: Optional[str] = Field(default=None, description="备注或退货原因")


class TwoStepActionRequest(BaseModel):
    """通用业务单据外层列表两阶段二次确认或取消提交请求"""
    order_no: str = Field(..., description="目标单据号")
    action: str = Field(..., description="执行动作: SECOND_CONFIRM-外层二次确认正式提交, CANCEL_SUBMIT-外层取消提交退回可编辑态, EDIT_REMARK-修改备注, DELETE_ORDER-删除单据")
    operator_name: str = Field(..., description="操作人姓名")
    new_remark: Optional[str] = Field(default=None, description="修改单据时的更新备注")


class StocktakeTransferCreateRequest(BaseModel):
    """创建全院各科室仓库盘点单或跨科/跨院区调拨单请求"""
    biz_category: str = Field(..., description="业务大类: GEN_STOCKTAKE/HV_STOCKTAKE/SEC_STOCKTAKE/DEPT_TRANSFER/CROSS_HOSP_TRANSFER")
    from_warehouse_code: str = Field(..., description="盘点仓库或调出仓库编码")
    to_warehouse_code: Optional[str] = Field(default=None, description="调入仓库编码(调拨单必填)")
    product_id: int = Field(..., description="产品ID")
    book_qty: int = Field(..., ge=0, description="系统账面数量")
    actual_or_transfer_qty: int = Field(..., ge=0, description="实盘数量或调拨数量")
    operator_name: str = Field(..., description="发起人姓名")
    reason_note: Optional[str] = Field(default=None, description="盘盈盘亏原因或调拨事由")


class HighValueLifecycleCreateRequest(BaseModel):
    """创建高值耗材备货申请、科室接收、科室退货出库或报损单请求"""
    hv_biz_type: str = Field(..., description="高值业务类型: HV_STOCK_PREP/HV_DEPT_RECEIVE/HV_DEPT_RETURN/HV_DAMAGE_REPORT")
    dept_code: str = Field(..., description="临床科室编码")
    product_id: int = Field(..., description="高值产品ID")
    udi_sn: str = Field(..., description="高值单品UDI唯一码")
    operator_name: str = Field(..., description="操作护士/技师姓名")
    remark: Optional[str] = Field(default=None, description="退货出库原因或报损说明")


class HighValueQrVerifyRequest(BaseModel):
    """高值耗材一物一码专属二维码扫码核销绑定患者请求"""
    udi_sn: str = Field(..., description="扫码识别的高值单品UDI序列号")
    patient_inpatient_no: str = Field(..., description="患者住院号")
    patient_name: str = Field(..., description="患者真实姓名(系统自动脱敏存储)")
    operator_name: str = Field(..., description="手术室扫码核销护士")


class SupplierQualAuditRequest(BaseModel):
    """供应商经营资质上传绑定与医院主科室准入审核请求"""
    supplier_code: str = Field(..., description="供应商编码")
    supplier_name: str = Field(..., description="供应商企业全称")
    social_credit_code: Optional[str] = Field(default=None, description="统一社会信用代码(18位)")
    license_no: str = Field(..., description="《医疗器械经营许可证》编号")
    license_expiry_date: date = Field(..., description="许可证有效期至")
    contact_person: Optional[str] = Field(default=None, description="业务代表姓名")
    contact_phone: Optional[str] = Field(default=None, description="业务代表手机号")
    audit_action: str = Field(default="QUAL_APPROVED", description="准入状态: QUAL_PENDING-上传待审, QUAL_APPROVED-医院审核通过, QUAL_REJECTED-医院驳回")
    audit_remark: Optional[str] = Field(default=None, description="准入审核意见或合规驳回理由")


class PurchaseOrderFlowRequest(BaseModel):
    """多级采购计划提报、主科审批、供应商拣货与二次确认发货请求"""
    order_no: Optional[str] = Field(default=None, description="现有采购单号(新提报时为空)")
    flow_action: str = Field(..., description="流转动作: CREATE_PLAN-临床提报采购计划, DEPT_APPROVE-主科室审批通过下发供应商, SUPPLIER_PICK_AND_SHIP-供应商拣货并二次确认发货")
    supplier_code: str = Field(default="SUP_WEGO_01", description="目标供应商编码")
    apply_dept_code: str = Field(default="SEC_CARDIO", description="申请科室编码")
    product_id: int = Field(default=1, description="采购产品ID")
    purchase_qty: int = Field(default=100, gt=0, description="采购数量")
    picked_batch_no: Optional[str] = Field(default="BATCH-SUP-202611", description="供应商拣货填写的生产批号")
    picked_expiry_date: Optional[date] = Field(default=date(2028, 10, 31), description="供应商拣货填写的有效期")
    operator_name: str = Field(..., description="操作人姓名")
