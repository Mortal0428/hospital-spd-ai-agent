"""Pydantic V2 统一数据契约、请求验证与响应 Schema 模型定义

本模块承载全局统一响应封装 ApiResponse[T] 及 5 大核心业务模块的 DTO 契约。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """全局统一 RESTful 响应封包结构"""
    code: int = Field(default=200, description="业务状态码: 200-成功, 400-业务规则拦截, 401-未登录, 403-无权操作, 500-系统异常")
    msg: str = Field(default="操作成功", description="业务提示信息")
    data: Optional[T] = Field(default=None, description="响应业务数据载荷")


# =========================================================================
# 1. 认证、人员与科室架构 Schema
# =========================================================================

class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="登录账号/工号")
    password: str = Field(..., description="登录密码")


class SwitchTokenRequest(BaseModel):
    """快速切换账号换取真实 JWT 访问令牌请求"""
    user_id: Optional[int] = Field(default=None, description="目标用户主键ID")
    username: Optional[str] = Field(default=None, description="目标用户工号/用户名")


class LoginResponse(BaseModel):
    """登录成功响应"""
    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user_id: int = Field(..., description="用户主键ID")
    username: str = Field(..., description="登录用户名")
    real_name: str = Field(..., description="用户真实姓名")
    role_code: str = Field(..., description="三级角色编码: sys_admin | dept_manager | secondary_user")
    dept_id: int = Field(..., description="所属科室ID")
    dept_code: str = Field(..., description="所属科室编码")
    dept_name: str = Field(..., description="所属科室名称")


class DepartmentResponse(BaseModel):
    """科室与库房信息"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    dept_code: str
    dept_name: str
    dept_type: str
    warehouse_zone: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    status: int
    created_at: datetime



class UserCreateRequest(BaseModel):
    """创建新用户"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    real_name: str = Field(..., description="真实姓名")
    role_code: str = Field(..., description="角色编码: sys_admin | dept_manager | secondary_user")
    dept_id: int = Field(..., description="科室ID")
    phone: Optional[str] = Field(None, description="联系手机号")


class UserWarehouseSummary(BaseModel):
    """人员已授权经办库藏摘要 (用于人员列表与顶栏联动)"""
    model_config = ConfigDict(from_attributes=True)
    warehouse_code: str = Field(..., description="仓库编码")
    warehouse_name: str = Field(..., description="仓库名称")
    warehouse_level: str = Field(default="MAIN_GROUP", description="仓库层级")
    can_view: int = Field(default=1, description="查看准入权限")
    can_apply: int = Field(default=0, description="申领权限")
    can_inbound: int = Field(default=0, description="验收入库权限")
    can_outbound: int = Field(default=0, description="发料出库权限")
    can_stocktake: int = Field(default=0, description="盘点权限")
    can_transfer: int = Field(default=0, description="调拨权限")


class UserResponse(BaseModel):
    """人员信息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    real_name: str
    role_code: str
    dept_id: int
    dept_code: str
    dept_name: Optional[str] = None
    phone_masked: Optional[str] = None
    status: int
    created_at: datetime
    authorized_warehouses: List[UserWarehouseSummary] = []



# =========================================================================
# 2. 核心 CRUD 一：产品分类与产品字典 Schema
# =========================================================================

class UserUpdateRequest(BaseModel):
    """修改人员信息请求载荷"""
    real_name: Optional[str] = Field(None, description="真实姓名")
    role_code: Optional[str] = Field(None, description="角色编码")
    dept_id: Optional[int] = Field(None, description="所属科室ID")
    phone: Optional[str] = Field(None, description="联系手机号")
    status: Optional[int] = Field(None, description="账号状态: 1-正常, 0-禁用")


class UserResetPasswordRequest(BaseModel):
    """重置密码请求载荷"""
    new_password: str = Field(..., min_length=6, description="新登录密码")


class UserBatchActionRequest(BaseModel):
    """批量人员操作请求载荷"""
    user_ids: List[int] = Field(..., description="选中的用户ID列表")
    action: str = Field(..., description="操作指令: ENABLE, DISABLE, DELETE, CHANGE_ROLE")
    target_role: Optional[str] = Field(None, description="目标角色")


class CategoryCreateRequest(BaseModel):
    """新增产品分类"""
    category_code: str = Field(..., description="分类编码")
    category_name: str = Field(..., description="分类名称")
    main_dept_code: str = Field(..., description="归口主管理科室: CONSUMABLE_DEPT | EQUIP_DEPT")
    consumable_level: str = Field(..., description="管控级别: GENERAL | HIGH_VALUE | EQUIP_PART")
    parent_id: int = Field(default=0, description="父级分类ID")
    storage_condition: str = Field(default="常温干燥", description="储运条件")
    sort_order: int = Field(default=0, description="排序权重")


class CategoryResponse(BaseModel):
    """产品分类响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_code: str
    category_name: str
    main_dept_code: str
    consumable_level: str
    parent_id: int
    storage_condition: str
    sort_order: int
    created_at: datetime


class ProductDictCreateRequest(BaseModel):
    """创建产品字典档案"""
    product_code: str = Field(..., description="院内产品编码(唯一)")
    product_name: str = Field(..., description="物资通用名")
    udi_di: str = Field(..., description="14位GS1-UDI-DI固定编码")
    main_dept_code: str = Field(..., description="归口主管理科室: CONSUMABLE_DEPT | EQUIP_DEPT")
    consumable_type: str = Field(..., description="耗材分类: GENERAL | HIGH_VALUE | EQUIP_PART")
    category_id: int = Field(..., description="细分品类ID")
    spec_model: str = Field(..., description="规格型号")
    unit: str = Field(..., description="单位")
    manufacturer: str = Field(..., description="生产厂家")
    supplier_name: str = Field(..., description="供应商")
    reg_cert_no: str = Field(..., description="医疗器械注册证号")
    reg_cert_expiry: date = Field(..., description="注册证有效期至")
    unit_price: Decimal = Field(..., description="单价(元)")
    safe_stock_min: int = Field(default=20, description="主库安全下限")
    safe_stock_max: int = Field(default=500, description="主库安全上限")
    storage_temp_req: str = Field(default="常温(10~30℃)", description="储运温度")


class ProductDictUpdateRequest(BaseModel):
    """更新产品字典"""
    product_name: Optional[str] = None
    spec_model: Optional[str] = None
    unit: Optional[str] = None
    manufacturer: Optional[str] = None
    supplier_name: Optional[str] = None
    reg_cert_no: Optional[str] = None
    reg_cert_expiry: Optional[date] = None
    unit_price: Optional[Decimal] = None
    safe_stock_min: Optional[int] = None
    safe_stock_max: Optional[int] = None
    storage_temp_req: Optional[str] = None
    status: Optional[int] = None


class ProductDictResponse(BaseModel):
    """产品字典档案响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_code: str
    product_name: str
    udi_di: str
    main_dept_code: str
    consumable_type: str
    category_id: int
    category_name: str
    spec_model: str
    unit: str
    manufacturer: str
    supplier_name: str
    reg_cert_no: str
    reg_cert_expiry: date
    unit_price: Decimal
    safe_stock_min: int
    safe_stock_max: int
    storage_temp_req: str
    status: int
    created_at: datetime

    updated_at: datetime


# =========================================================================
# 3. 核心 CRUD 二：主库全部物资管理与按需分发 Schema
# =========================================================================

class MainInboundRequest(BaseModel):
    """主库验收入库请求"""
    product_id: int = Field(..., description="产品字典ID")
    batch_no: str = Field(..., description="生产批号")
    production_date: date = Field(..., description="生产日期")
    expiry_date: date = Field(..., description="有效期至(必须大于今日)")
    inbound_qty: int = Field(..., gt=0, description="验收入库数量")
    unit_price: Optional[Decimal] = Field(None, description="入库单价(留空取字典价)")
    shelf_location: str = Field(default="耗材主库-A区-01架-01层", description="主库货位")
    accept_temp: str = Field(default="22.5℃(合规)", description="验收温度")


class MainDistributionCreateRequest(BaseModel):
    """创建主库按需分发调拨单"""
    main_inventory_id: int = Field(..., description="源主库批次库存ID")
    target_type: str = Field(..., description="分发目标: TO_SECONDARY_DEPT (二级库) | TO_HIGH_VALUE_WH (高值专仓)")
    target_dept_id: int = Field(..., description="接收目标科室ID")
    dist_qty: int = Field(..., gt=0, description="本次按需分发数量")
    remark: Optional[str] = Field(None, description="分发备注说明")


class MainInventoryResponse(BaseModel):
    """主库批次库存响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    inbound_order_no: str
    product_id: int
    product_code: str
    product_name: str
    main_dept_code: str
    consumable_type: str
    batch_no: str
    production_date: date
    expiry_date: date
    initial_qty: int
    available_qty: int
    unit_price: Decimal
    shelf_location: str
    accept_temp: str
    quality_status: str
    inbound_user_name: str
    created_at: datetime


class DistributionOrderResponse(BaseModel):
    """按需分发调拨单响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    dist_order_no: str
    source_main_dept: str
    target_type: str
    target_dept_id: int
    target_dept_name: str
    main_inventory_id: int
    product_id: int
    product_code: str
    product_name: str
    batch_no: str
    expiry_date: date
    dist_qty: int
    unit_price: Decimal
    total_amount: Decimal
    order_status: str
    dispatcher_name: str
    receiver_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    received_at: Optional[datetime] = None


# =========================================================================
# 4. 核心 CRUD 三：高值耗材专仓一物一码 Schema
# =========================================================================

class HighValueActivateRequest(BaseModel):
    """由量到码：分拨入专仓拆包赋码请求 (Skill 03)"""
    main_inventory_id: int = Field(..., description="主库批次库存ID")
    dist_qty: int = Field(..., gt=0, description="拆包赋码数量")
    wh_cabinet_code: str = Field(default="高值专仓-智能柜01-A01格", description="专仓货柜编码")


class HighValueVerifyRequest(BaseModel):
    """临床患者扫码使用核销请求 (触发财务记账与脱敏)"""
    patient_inpatient_no: str = Field(..., description="患者住院号")
    patient_name: str = Field(..., description="患者原始姓名(系统将自动调用Skill 04脱敏)")
    surgery_name: str = Field(..., description="手术/诊疗名称")
    attending_doctor: str = Field(..., description="主刀/主治医生")


class HighValueStatusUpdateRequest(BaseModel):
    """变更状态 (跟台锁定/不良召回/退回专柜)"""
    new_status: str = Field(..., description="新状态: SURGERY_LOCKED | RETURNED | RECALLED")
    remark: Optional[str] = Field(None, description="变更说明")


class HighValueItemResponse(BaseModel):
    """高值单品信息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    udi_full_code: str
    udi_sn: str
    dist_order_no: str
    product_id: int
    product_code: str
    product_name: str
    spec_model: str
    main_dept_code: str
    batch_no: str
    expiry_date: date
    unit_price: Decimal
    wh_cabinet_code: str
    current_dept_id: int
    current_dept_name: str
    item_status: str
    patient_inpatient_no: Optional[str] = None
    patient_name_masked: Optional[str] = None
    surgery_name: Optional[str] = None
    attending_doctor: Optional[str] = None
    verify_nurse_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


# =========================================================================
# 5. 核心 CRUD 四：二级库管理与申领/退库 Schema
# =========================================================================

class RequisitionCreateRequest(BaseModel):
    """临床二级库新建申领单或退库单"""
    order_direction: str = Field(default="APPLY_FROM_MAIN", description="APPLY_FROM_MAIN (正向申领) | RETURN_TO_MAIN (逆向退库)")
    product_id: int = Field(..., description="产品字典ID")
    apply_qty: int = Field(..., gt=0, description="申领/退库数量")
    urgency_level: str = Field(default="ROUTINE", description="ROUTINE (日常) | URGENT (加急)")
    apply_reason: Optional[str] = Field(None, description="申领或退库原因")


class RequisitionApproveRequest(BaseModel):
    """主库管理员审批申领单或退库单"""
    approved_qty: int = Field(..., ge=0, description="实际批准数量(0表示驳回)")
    is_approved: bool = Field(default=True, description="是否同意批准")
    reject_reason: Optional[str] = Field(None, description="驳回原因")


class ReceiveDistributionRequest(BaseModel):
    """二级库签收主库分发调拨单"""
    is_accept: bool = Field(default=True, description="True-正常签收入库, False-差异拒收退回主库")
    reject_reason: Optional[str] = Field(None, description="拒收退料原因")


class ClinicalConsumeRequest(BaseModel):
    """二级库普通耗材临床消耗登记 (触发财务科成本核算)"""
    sec_inventory_id: int = Field(..., description="二级库批次库存ID")
    consume_qty: int = Field(..., gt=0, description="消耗数量")
    patient_inpatient_no: Optional[str] = Field(None, description="关联住院号")
    consume_reason: str = Field(default="病区日常护理消耗", description="消耗说明")


class SecondaryInventoryResponse(BaseModel):
    """二级库库存响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    dept_id: int
    dept_name: str
    product_id: int
    product_code: str
    product_name: str
    main_dept_code: str
    batch_no: str
    expiry_date: date
    current_qty: int
    consumed_qty: int
    unit_price: Decimal
    sec_shelf_code: str
    dept_safe_min: int
    batch_status: str
    updated_at: datetime


class RequisitionOrderResponse(BaseModel):
    """申领与退库单响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    req_order_no: str
    order_direction: str
    apply_dept_id: int
    apply_dept_name: str
    target_main_dept: str
    product_id: int
    product_code: str
    product_name: str
    apply_qty: int
    approved_qty: int
    urgency_level: str
    req_status: str
    applicant_name: str
    approver_name: Optional[str] = None
    apply_reason: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None


# =========================================================================
# 6. 核心 CRUD 五：全流程 6W 业务链路日志 Schema
# =========================================================================

class WorkflowLogCreateRequest(BaseModel):
    """信息科管理员手动补录流转日志"""
    biz_order_no: str = Field(..., description="业务单据号")
    node_action: str = Field(..., description="8大流转节点")
    product_code: str = Field(..., description="物资编码")
    product_name: str = Field(..., description="物资名称")
    batch_or_udi: str = Field(..., description="批号或UDI码")
    from_dept_name: str = Field(..., description="交出方科室")
    from_user_name: str = Field(..., description="交出人")
    to_dept_name: str = Field(..., description="接收方科室")
    to_user_name: str = Field(..., description="接收人")
    change_qty: int = Field(..., description="变动数量")
    before_stock_snapshot: int = Field(default=0, description="流转前库存")
    after_stock_snapshot: int = Field(default=0, description="流转后库存")
    settlement_amount: Decimal = Field(default=Decimal("0.00"), description="金额")
    is_billable: int = Field(default=0, description="是否计费")
    audit_remark: Optional[str] = Field(None, description="说明")


class WorkflowLogAuditRequest(BaseModel):
    """审计复核流转日志"""
    audit_status: str = Field(..., description="VERIFIED | FLAGGED | RECTIFIED")
    audit_remark: str = Field(..., description="审计复核批注")


class WorkflowLogResponse(BaseModel):
    """全流程 6W 日志响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    trace_no: str
    biz_order_no: str
    node_action: str
    product_code: str
    product_name: str
    batch_or_udi: str
    from_dept_name: str
    from_user_name: str
    to_dept_name: str
    to_user_name: str
    change_qty: int
    before_stock_snapshot: int
    after_stock_snapshot: int
    settlement_amount: Decimal
    is_billable: int
    audit_status: str
    audit_remark: Optional[str] = None
    created_at: datetime


# =========================================================================
# 7. 统计看板与法定四联打印单据 Schema
# =========================================================================

class StatsOverviewResponse(BaseModel):
    """全院库存总盘概况"""
    main_warehouse_total_qty: int
    main_warehouse_total_amount: Decimal
    high_value_wh_total_items: int
    high_value_wh_total_amount: Decimal
    secondary_total_qty: int
    secondary_total_consumed_qty: int
    secondary_total_consumed_amount: Decimal
    near_expiry_warning_count: int
    low_stock_warning_count: int


class DeptConsumptionItem(BaseModel):
    """单个科室耗材消耗金额项"""
    dept_name: str
    general_amount: Decimal
    high_value_amount: Decimal
    total_amount: Decimal


class DeptConsumptionResponse(BaseModel):
    """财务科室消耗排行榜"""
    rankings: List[DeptConsumptionItem]
    total_hospital_consumed_amount: Decimal


class VoucherSignatures(BaseModel):
    """法定单据四联责任签字栏"""
    operator_signature: str = Field(default="", description="制单人签字")
    main_dept_leader: str = Field(default="", description="主库科室主管签字")
    secondary_receiver: str = Field(default="", description="二级库领用人签字")
    finance_auditor: str = Field(default="", description="财务科复核签字")


class VoucherPrintResponse(BaseModel):
    """法定标准单据打印结构化数据"""
    voucher_title: str = Field(..., description="单据标准法定抬头")
    voucher_type: str = Field(..., description="单据类型代码")
    order_no: str = Field(..., description="业务单据编号")
    print_time: str = Field(..., description="打印时间")
    source_dept: str = Field(..., description="交出科室")
    target_dept: str = Field(..., description="接收科室")
    items: List[dict] = Field(default_factory=list, description="批次或单品明细项清单")
    total_amount: Decimal = Field(default=Decimal("0.00"), description="合计金额")
    signatures: VoucherSignatures = Field(default_factory=VoucherSignatures, description="四联签字栏")
    watermark: str = Field(default="医院物资管理有效凭证", description="背景水印")


# =========================================================================
# 8. 医院真实 SPD 四级物料字典、多级规格、供应商与仓库细粒度授权 Schema
# =========================================================================

class SpnCreateRequest(BaseModel):
    """新增通用大品名请求载荷 (对应图 3 新增品名)"""
    spn_code: str = Field(..., description="品名编码，如 936010100024")
    spn_name: str = Field(..., description="品名名称，如 医用氧气123")
    category_code: str = Field(..., description="所属耗材分类编码，如 0101")
    common_name: Optional[str] = Field(default="", description="耗材通用名称")
    pinyin_code: Optional[str] = Field(default="", description="拼音助记码")
    finance_category: Optional[str] = Field(default="", description="财务核算分类")
    performance_category: Optional[str] = Field(default="", description="绩效核算分类")
    inpatient_charge_category: Optional[str] = Field(default="", description="住院收费分类")
    outpatient_charge_category: Optional[str] = Field(default="", description="门诊收费分类")
    medical_record_category: Optional[str] = Field(default="", description="病案分类")
    medicare_category: Optional[str] = Field(default="", description="医保分类")
    is_chargeable: int = Field(default=1, description="是否收费材料: 1-是, 0-否")
    is_high_value: int = Field(default=0, description="是否高值耗材: 1-是, 0-否")
    is_central_proc: int = Field(default=0, description="是否带量集采: 1-是, 0-否")
    central_proc_project: Optional[str] = Field(default="", description="集采项目说明")
    contract_no: Optional[str] = Field(default="", description="采购合同编号")
    contract_signed_date: Optional[date] = Field(default=None, description="合同签订日期")
    contract_start_date: Optional[date] = Field(default=None, description="合同开始日期")
    contract_end_date: Optional[date] = Field(default=None, description="合同结束日期")


class SpnUpdateRequest(BaseModel):
    """更新大品名属性"""
    spn_name: Optional[str] = None
    category_code: Optional[str] = None
    common_name: Optional[str] = None
    pinyin_code: Optional[str] = None
    finance_category: Optional[str] = None
    performance_category: Optional[str] = None
    inpatient_charge_category: Optional[str] = None
    outpatient_charge_category: Optional[str] = None
    medical_record_category: Optional[str] = None
    medicare_category: Optional[str] = None
    is_chargeable: Optional[int] = None
    is_high_value: Optional[int] = None
    is_central_proc: Optional[int] = None
    central_proc_project: Optional[str] = None
    contract_no: Optional[str] = None
    contract_signed_date: Optional[date] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None


class SpnResponse(BaseModel):
    """通用大品名响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    spn_code: str
    spn_name: str
    category_code: str
    common_name: str
    pinyin_code: str
    finance_category: str
    performance_category: str
    inpatient_charge_category: str
    outpatient_charge_category: str
    medical_record_category: str
    medicare_category: str
    is_chargeable: int
    is_high_value: int
    is_central_proc: int
    central_proc_project: str
    contract_no: str
    contract_signed_date: Optional[date] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    status: str
    created_at: datetime
    spec_count: Optional[int] = 0


class SpecCreateRequest(BaseModel):
    """新增产品规格型号请求载荷 (对应图 5 新增规格)"""
    spn_id: int = Field(..., description="关联大品名主键ID")
    spec_code: str = Field(..., description="唯一产品规格编码，如 936010100024055517")
    product_name: str = Field(..., description="产品名称")
    spec_name: str = Field(..., description="规格描述，如 40L 瓶装")
    model_name: str = Field(..., description="型号，如 TWLB")
    common_name: Optional[str] = Field(default="", description="通用名称")
    component_name: Optional[str] = Field(default="主件", description="组件名称")
    pinyin_code: Optional[str] = Field(default="", description="拼音码")
    brand_name: Optional[str] = Field(default="国产品牌", description="品牌名称")
    manufacturer: str = Field(..., description="生产厂商全称")
    description: Optional[str] = Field(default="", description="产品描述")
    pricing_unit: str = Field(..., description="计件单位，如 瓶/支/盒/套")
    package_unit: Optional[str] = Field(default="箱", description="包装单位，如 箱/件")
    conversion_ratio: Decimal = Field(default=Decimal("1.00"), description="大小包装转换比")
    unit_price: Decimal = Field(..., description="基准单价(元)")
    register_card_no: Optional[str] = Field(default="", description="医疗器械注册证号")
    register_expiry_date: Optional[date] = Field(default=None, description="注册证有效期")
    medicare_code: Optional[str] = Field(default="", description="国家医保耗材编码")
    medicare_category_code: Optional[str] = Field(default="", description="医保耗材分类编码")
    production_license_no: Optional[str] = Field(default="", description="生产许可证号")
    production_license_expiry: Optional[date] = Field(default=None, description="生产许可证有效期")
    default_supplier_id: Optional[int] = Field(default=0, description="默认供货供应商ID")
    default_supplier_name: Optional[str] = Field(default="", description="默认供应商企业名称")
    original_code: Optional[str] = Field(default="", description="原厂编码/原位码")
    provincial_code: Optional[str] = Field(default="", description="省标码/阳光采购平台编码")
    storage_condition: Optional[str] = Field(default="常温干燥避光", description="储存条件")
    is_central_proc: Optional[int] = Field(default=0, description="是否带量集采")
    central_proc_code: Optional[str] = Field(default="", description="集采中选规格物料编码")
    origin_place: Optional[str] = Field(default="国产", description="产地")
    category_code: Optional[str] = Field(default="0101", description="所属耗材分类编码")
    assigned_warehouses: Optional[str] = Field(default="WH_WEICAI", description="分配仓库逗号分隔列表")


class SpecUpdateRequest(BaseModel):
    """更新规格型号单品请求载荷"""
    product_name: Optional[str] = None
    spec_name: Optional[str] = None
    model_name: Optional[str] = None
    common_name: Optional[str] = None
    component_name: Optional[str] = None
    pinyin_code: Optional[str] = None
    brand_name: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    pricing_unit: Optional[str] = None
    package_unit: Optional[str] = None
    conversion_ratio: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    register_card_no: Optional[str] = None
    register_expiry_date: Optional[date] = None
    medicare_code: Optional[str] = None
    medicare_category_code: Optional[str] = None
    production_license_no: Optional[str] = None
    production_license_expiry: Optional[date] = None
    default_supplier_id: Optional[int] = None
    default_supplier_name: Optional[str] = None
    original_code: Optional[str] = None
    provincial_code: Optional[str] = None
    storage_condition: Optional[str] = None
    is_central_proc: Optional[int] = None
    central_proc_code: Optional[str] = None
    origin_place: Optional[str] = None
    category_code: Optional[str] = None
    assigned_warehouses: Optional[str] = None
    status: Optional[str] = None


class SpecResponse(BaseModel):
    """规格型号单品响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    spn_id: int
    spec_code: str
    product_name: str
    spec_name: str
    model_name: str
    common_name: str
    component_name: str
    pinyin_code: str
    brand_name: str
    manufacturer: str
    description: str
    pricing_unit: str
    package_unit: str
    conversion_ratio: Decimal
    unit_price: Decimal
    register_card_no: str
    register_expiry_date: Optional[date] = None
    medicare_code: str
    medicare_category_code: str
    production_license_no: str
    production_license_expiry: Optional[date] = None
    default_supplier_id: int
    default_supplier_name: str
    original_code: str
    provincial_code: str
    storage_condition: str
    is_central_proc: int
    central_proc_code: str
    origin_place: str
    category_code: str
    status: str
    assigned_warehouses: str
    created_at: datetime



class BatchAdjustPriceRequest(BaseModel):
    """集中带量采购与批量调价请求载荷"""
    spec_ids: List[int] = Field(..., description="待批量调价的规格ID列表")
    adjust_type: str = Field(..., description="调价模式: FIXED_PRICE-统一定价, PERCENT_DISCOUNT-按百分比调价(如-0.10为下浮10%), FIXED_OFFSET-按金额差额调整(如-5.00)")
    adjust_value: Decimal = Field(..., description="调价数值")
    reason: str = Field(..., description="调价原因/政策依据，如: 省集中带量采购联动调价")
    doc_no: Optional[str] = Field(default="", description="调价政策依据文件文号")


class PriceAdjustLogResponse(BaseModel):
    """调价历史快照响应 (对应图 5 调价记录 Tab)"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    spec_id: int
    spec_code: str
    spec_name: str
    old_price: Decimal
    new_price: Decimal
    adjust_diff: Decimal
    adjust_reason: str
    adjust_doc_no: str
    operator_name: str
    effective_time: datetime


class SupplierProfileCreateRequest(BaseModel):
    """新增供应商档案请求载荷 (对应图 4 中栏供应商维护)"""
    supplier_code: str = Field(..., description="供应商编码")
    supplier_name: str = Field(..., description="企业全称")
    social_credit_code: str = Field(..., description="统一社会信用代码(18位)")
    license_no: str = Field(..., description="《医疗器械经营许可证》编号")
    license_expiry_date: date = Field(..., description="经营许可证有效期截止日")
    contact_person: Optional[str] = Field(default="", description="业务联系人")
    contact_phone: Optional[str] = Field(default="", description="联系电话")
    supply_categories: Optional[str] = Field(default="普耗,高值", description="主营范围")
    qual_status: Optional[str] = Field(default="QUAL_APPROVED", description="资质状态")


class SupplierProfileUpdateRequest(BaseModel):
    """更新供应商档案"""
    supplier_name: Optional[str] = None
    social_credit_code: Optional[str] = None
    license_no: Optional[str] = None
    license_expiry_date: Optional[date] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    supply_categories: Optional[str] = None
    qual_status: Optional[str] = None
    status: Optional[str] = None


class SupplierProfileResponse(BaseModel):
    """供应商档案响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_code: str
    supplier_name: str
    social_credit_code: str
    license_no: str
    license_expiry_date: date
    contact_person: str
    contact_phone: str
    supply_categories: str
    qual_status: str
    status: str
    created_at: datetime


class UserWarehousePermUpdateRequest(BaseModel):
    """分配/修改用户仓库细粒度权限"""
    user_id: int = Field(..., description="目标用户ID")
    warehouse_code: str = Field(..., description="仓库编码")
    can_view: int = Field(default=1, description="查看物资: 1-允许, 0-禁止")
    can_apply: int = Field(default=0, description="申领物资: 1-允许, 0-禁止")
    can_inbound: int = Field(default=0, description="验收入库: 1-允许, 0-禁止")
    can_outbound: int = Field(default=0, description="发料出库: 1-允许, 0-禁止")
    can_stocktake: int = Field(default=0, description="盘点维护: 1-允许, 0-禁止")
    can_transfer: int = Field(default=0, description="调拨分发: 1-允许, 0-禁止")


class UserWarehousePermResponse(BaseModel):
    """用户仓库权限项响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    warehouse_code: str
    warehouse_name: Optional[str] = None
    warehouse_level: Optional[str] = None
    can_view: int
    can_apply: int
    can_inbound: int
    can_outbound: int
    can_stocktake: int
    can_transfer: int
    updated_by: str
    updated_at: datetime


class UserWarehousePermBatchItem(BaseModel):
    """批量设置单个仓库细粒度权限条目"""
    warehouse_code: str = Field(..., description="仓库编码")
    can_view: int = Field(default=1, description="查看准入权限")
    can_apply: int = Field(default=0, description="申领权限")
    can_inbound: int = Field(default=0, description="验收入库权限")
    can_outbound: int = Field(default=0, description="发料出库权限")
    can_stocktake: int = Field(default=0, description="盘点权限")
    can_transfer: int = Field(default=0, description="调拨权限")


class UserWarehousePermBatchRequest(BaseModel):
    """批量更新人员库藏细粒度权限矩阵请求载荷"""
    user_id: int = Field(..., description="目标人员用户ID")
    perms: List[UserWarehousePermBatchItem] = Field(..., description="全量仓库权限矩阵清单")


class WarehouseNodeCreateRequest(BaseModel):
    """新增仓库节点"""
    warehouse_code: str = Field(..., description="仓库编码")
    warehouse_name: str = Field(..., description="仓库名称")
    warehouse_level: str = Field(default="MAIN_GROUP", description="仓库层级: MAIN_GROUP | DEPT_PRIMARY | CLINICAL_SECONDARY")
    parent_code: str = Field(default="ROOT", description="父仓库编码")
    dept_code: str = Field(..., description="归属科室编码")


class WarehouseNodeUpdateRequest(BaseModel):
    """更新仓库节点"""
    warehouse_name: Optional[str] = None
    warehouse_level: Optional[str] = None
    parent_code: Optional[str] = None
    dept_code: Optional[str] = None
    status: Optional[int] = None


class WarehouseNodeResponse(BaseModel):
    """仓库节点响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    warehouse_code: str
    warehouse_name: str
    warehouse_level: str
    parent_code: str
    dept_code: str
    init_stock_locked: int
    init_stock_order_no: Optional[str] = None
    init_locked_at: Optional[datetime] = None
    status: int
    created_at: datetime

# =========================================================================
# 7. 采购入库、临床申请、手动出库、独立盘点与财务对账 Schema
# =========================================================================

class PurchaseInboundItem(BaseModel):
    """采购入库单身耗材明细行"""
    spec_code: str = Field(..., description="产品规格编码")
    product_name: str = Field(..., description="品名")
    spec_name: str = Field(default="", description="规格")
    model_name: str = Field(default="", description="型号")
    unit_name: str = Field(default="支", description="计量单位")
    manufacturer: str = Field(default="", description="生产厂家")
    unit_price: float = Field(..., description="单价(元)")
    quantity: int = Field(..., description="实收数量")
    total_amount: Optional[float] = Field(default=0.0, description="总金额")
    batch_no: str = Field(default="B20261101", description="生产批号")
    sterilization_batch: Optional[str] = Field(None, description="灭菌批号")
    produce_date: Optional[date] = Field(None, description="生产日期")
    expiry_date: Optional[date] = Field(None, description="有效截止日期")
    register_card_no: Optional[str] = Field(None, description="注册证号")


class PurchaseInboundOrderCreateRequest(BaseModel):
    """采购入库单完整录入请求 (图 5)"""
    delivery_order_no: Optional[str] = Field(None, description="配送单号")
    inbound_type: str = Field(default="采购入库", description="入库类别")
    invoice_no: Optional[str] = Field(None, description="发票号")
    invoice_date: Optional[date] = Field(None, description="发票日期")
    warehouse_code: str = Field(default="WH_WEICAI", description="入库仓库编码")
    supplier_id: Optional[int] = Field(default=1, description="供应商ID")
    supplier_name: str = Field(..., description="供应商名称")
    delivery_person: Optional[str] = Field(None, description="配送人姓名")
    delivery_phone: Optional[str] = Field(None, description="配送人联系方式")
    delivery_id_card: Optional[str] = Field(None, description="配送人身份证号")
    purchaser_name: Optional[str] = Field(None, description="采购人姓名")
    handler_name: str = Field(default="系统管理员", description="经办人姓名")
    auto_approve: bool = Field(default=True, description="保存后是否自动审核入账增加在库库存")
    remark: Optional[str] = Field(None, description="备注信息")
    items: List[PurchaseInboundItem] = Field(..., min_length=1, description="入库耗材明细清单")


class RequisitionOrderItem(BaseModel):
    """临床科室申请单明细行 (图 4)"""
    spec_code: str = Field(..., description="产品规格编码")
    product_name: str = Field(..., description="品名")
    spec_name: str = Field(default="", description="规格")
    model_name: str = Field(default="", description="型号")
    unit_name: str = Field(default="支", description="计量单位")
    manufacturer: str = Field(default="", description="生产厂家")
    unit_price: float = Field(..., description="单价(元)")
    apply_qty: int = Field(..., gt=0, description="申请数量")
    remark: Optional[str] = Field(None, description="明细备注")


class RequisitionOrderCreateRequest(BaseModel):
    """临床物资申请单填报请求 (图 4)"""
    apply_dept_code: str = Field(..., description="申领科室编码")
    apply_dept_name: str = Field(..., description="申领科室名称")
    apply_warehouse_code: str = Field(..., description="申领二级库编码")
    target_main_warehouse_code: str = Field(default="WH_WEICAI", description="供料主仓库编码")
    applicant_id: int = Field(..., description="申请人ID")
    applicant_name: str = Field(..., description="申请人姓名")
    urgency_level: str = Field(default="ROUTINE", description="紧急程度: ROUTINE | URGENT")
    apply_reason: Optional[str] = Field(None, description="申领事由说明")
    items: List[RequisitionOrderItem] = Field(..., min_length=1, description="申请耗材明细")


class ManualOutboundItem(BaseModel):
    """科室手动发料出库耗材明细"""
    spec_code: str = Field(..., description="产品规格编码")
    batch_no: str = Field(..., description="出库批号")
    quantity: int = Field(..., gt=0, description="出库数量")
    unit_price: float = Field(..., description="单价(元)")
    remark: Optional[str] = Field(None, description="消耗用途备注")


class ManualOutboundCreateRequest(BaseModel):
    """临床二级库手动发料出库请求 (替代前端 HIS 消除库存)"""
    warehouse_code: str = Field(..., description="出库二级库编码")
    dept_code: str = Field(..., description="所属科室编码")
    outbound_type: str = Field(default="CLINICAL_CONSUME", description="出库类型: CLINICAL_CONSUME-病区临床耗用, SURGERY_USE-手术耗用")
    receiver_name: str = Field(..., description="领用人/责任护士姓名")
    operator_name: str = Field(..., description="经办出库人姓名")
    use_purpose: str = Field(default="病区常规患者救治与耗用", description="领用用途")
    items: List[ManualOutboundItem] = Field(..., min_length=1, description="出库明细")


class StocktakeItem(BaseModel):
    """独立仓库盘点明细行"""
    spec_code: str = Field(..., description="规格编码")
    product_name: str = Field(..., description="品名")
    spec_name: str = Field(default="", description="规格")
    model_name: str = Field(default="", description="型号")
    unit_name: str = Field(default="支", description="单位")
    manufacturer: str = Field(default="", description="厂家")
    batch_no: str = Field(default="BATCH-INIT", description="批号")
    book_qty: int = Field(default=0, description="系统账面数量")
    actual_qty: int = Field(..., ge=0, description="实盘数量")
    diff_qty: int = Field(default=0, description="盈亏差额(实盘 - 账面)")
    unit_price: float = Field(default=0.0, description="单价(元)")
    is_new_supplement: int = Field(default=0, description="是否属于从字典增补的漏账耗材: 1-是, 0-否")


class StocktakeSubmitRequest(BaseModel):
    """独立仓库盘点提交平账请求"""
    warehouse_code: str = Field(..., description="盘点仓库编码")
    operator_name: str = Field(..., description="盘点操作人")
    reason_note: Optional[str] = Field(None, description="盘点说明或盈亏原因")
    items: List[StocktakeItem] = Field(..., min_length=1, description="盘点物料清册")



class MainOutboundItem(BaseModel):
    """主库出库单明细行 (对齐入库单规范)"""
    spec_code: str = Field(..., description="物料代码")
    product_name: str = Field(..., description="品名")
    spec_name: Optional[str] = Field(default="", description="规格")
    model_name: Optional[str] = Field(default="", description="型号")
    pricing_unit: Optional[str] = Field(default="件", description="单位")
    manufacturer: Optional[str] = Field(default="", description="生产厂家")
    quantity: int = Field(..., gt=0, description="出库数量")
    unit_price: float = Field(..., description="单价(元)")
    batch_no: str = Field(..., description="出库批号")
    expiry_date: Optional[date] = Field(default=None, description="有效期至")
    remark: Optional[str] = Field(default="", description="明细备注")


class MainOutboundVoucherCreateRequest(BaseModel):
    """主库耗材按需分发出库单 (对齐图 2 样式与入库单规范)"""
    outbound_type: str = Field(default="按需分发出库", description="出库类型: 按需分发出库 | 调拨出库 | 报损出库")
    source_warehouse_code: str = Field(default="WH_WEICAI", description="出库主库编码")
    target_dept_code: str = Field(..., description="领用目标二级库/科室编码")
    target_dept_name: str = Field(..., description="领用目标科室名称")
    receiver_name: str = Field(default="科室护士长", description="领用负责人/接收人")
    handler_name: str = Field(default="主库保管员", description="经办人姓名")
    auto_approve: bool = Field(default=True, description="保存后是否自动审核出账并生成二级库待签收单")
    remark: Optional[str] = Field(default="", description="出库说明备注")
    items: List[MainOutboundItem] = Field(..., min_length=1, description="出库耗材明细清单")


# =========================================================================
# 8. 深度优化：不良事件召回、FEFO 效期分析与采供月度对账 Schema
# =========================================================================

class RecallFreezeBatchRequest(BaseModel):
    """不良事件紧急召回全院批次冻结请求体"""
    batch_no: str = Field(..., description="待召回的生产批号")
    product_code: Optional[str] = Field(None, description="特定规格编码(可选)")
    recall_reason: str = Field(..., min_length=2, description="国家药监局或厂家召回公告与原因说明")
    notice_doc_no: Optional[str] = Field(None, description="召回通知文件编号")


class MonthlyReconciliationConfirmRequest(BaseModel):
    """采供月度对账单确认与发票记账流转请求体"""
    reconciliation_no: str = Field(..., description="对账单编号(如: REC-202611-SUP01)")
    supplier_code: str = Field(..., description="供应商统一编码")
    reconciliation_month: str = Field(..., description="结算月份(如: 2026-11)")
    invoice_code: Optional[str] = Field(None, description="增值税专用发票代码")
    invoice_no: Optional[str] = Field(None, description="增值税发票号码")
    invoice_amount: Optional[float] = Field(None, description="发票总金额(含税)")
    memo: Optional[str] = Field(None, description="对账与发票核对备注")


class SupplierBatchDispatchItem(BaseModel):
    """供应商批量发货导入明细项"""
    order_no: str = Field(..., description="采购计划单号")
    picked_batch_no: str = Field(..., description="配货生产批号")
    picked_expiry_date: date = Field(..., description="配货有效截止日期")
    picked_qty: int = Field(..., gt=0, description="实发配送数量")


class SupplierBatchDispatchRequest(BaseModel):
    """供应商批量装箱发货请求体"""
    supplier_code: str = Field(..., description="供应商统一编码")
    items: List[SupplierBatchDispatchItem] = Field(..., min_length=1, description="发货明细清册")

