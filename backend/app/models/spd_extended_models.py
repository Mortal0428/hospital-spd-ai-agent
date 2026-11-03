"""医院医疗物资全链路管理系统 (SPD) 深度扩展 SQLAlchemy 2.0 声明式 ORM 映射模型

本模块严格执行 Skill 01 (sqlalchemy_orm_with_comment)、Skill 07 (two_step_confirm_state_machine) 与 Skill 08 (decoupled_8_action_rbac)。
涵盖：
1. SysUserModulePermission - 信息科解耦式 15 模块 x 8 动作细粒度权限表
2. SpdWarehouseNode - 全院多级仓库树与科室期初数据一次性锁定状态表
3. SpdProductDictExt - 产品字典深度扩展表(通用名/拼音码/组件/品牌/分配仓库/停用/调价/JSON扩展)
4. SpdInboundAndOutboundOrder - 普耗/二级库出入库单、退供应商红字单、请领审核自动出库单与期初建账单表
5. SpdStocktakeAndTransferOrder - 全院各科室独立仓库盘点单(账实盈亏)与跨科/跨院调拨单表
6. SpdHighValueLifecycleOrder - 高值耗材备货、科室接收、科室退货(二次确认永久锁死)、报损与一物一码二维码扫码核销表
7. SpdSupplierAndPurchaseOrder - 供应商经营资质准入绑定、临床多级采购计划与供应商拣货发货协同表
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, SmallInteger, Numeric, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SysUserModulePermission(Base):
    """信息科解耦式人员细粒度模块权限矩阵 ORM 映射模型"""
    __tablename__ = "sys_user_module_permission"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "用户级模块与8项原子动作细粒度权限配置表(支持信息科针对任意具体人员独立开关权限)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="权限配置主键ID")
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联用户ID(sys_user.id)")
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="登录账号冗余")
    role_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="角色模板编码: sys_admin/dept_manager/secondary_user/finance_auditor/supplier_user")
    module_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="业务模块编码(如: DICT_MANAGE, GEN_INBOUND, GEN_OUTBOUND, GEN_INIT_STOCK, HV_RETURN, SUPPLIER_SHIP)")
    module_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="业务模块中文名称")
    can_view: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="查询权限: 1-允许, 0-禁止")
    can_create: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="新增/填单第一次提交权限: 1-允许, 0-禁止")
    can_edit: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="修改权限(仅限未二次确认锁死单据): 1-允许, 0-禁止")
    can_delete: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="删除权限(仅限未二次确认锁死单据): 1-允许, 0-禁止")
    can_second_confirm: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="外层列表二次确认提交权限: 1-允许, 0-禁止")
    can_cancel_submit: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="外层列表取消提交回退权限: 1-允许, 0-禁止")
    can_approve: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="科室/主库审核批准权限: 1-允许, 0-禁止")
    can_print: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="单据与条码/二维码打印权限: 1-允许, 0-禁止")
    updated_by: Mapped[str] = mapped_column(String(64), default="sys_admin", nullable=False, comment="权限最后修改人(信息科管理员)")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后更新时间")


class SpdWarehouseNode(Base):
    """全院多级仓库组织树与期初建账一次性锁定状态 ORM 映射模型"""
    __tablename__ = "spd_warehouse_node"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "全院多级仓库树节点与科室期初数据一次性锁定控制表(对齐图4仓库分类树)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="仓库节点主键ID")
    warehouse_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="仓库唯一编码(如: WH_WEICAI, WH_ZONGWU, WH_XINXI, WH_EQUIP, WH_SEC_CARDIO)")
    warehouse_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="仓库名称(如: 卫材库, 总务仓库, 信息仓库, 专项库房, 后勤仓库, 测试仓库, 设备库房, 心内科二级库)")
    warehouse_level: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="仓库层级: MAIN_GROUP-全院总仓群, DEPT_PRIMARY-主库科室仓, CLINICAL_SECONDARY-临床科室二级库")
    parent_code: Mapped[str] = mapped_column(String(32), default="ROOT", nullable=False, comment="父级仓库节点编码")
    dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="归属科室编码")
    init_stock_locked: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="科室期初数据是否已二次确认永久锁定: 0-未锁定可填报, 1-已二次确认永久只读(只可填写一次)")
    init_stock_order_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="已锁定的期初建账汇总单号")
    init_locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="期初数据永久锁定时间")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="启用状态: 1-启用, 0-停用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class SpdProductDictExt(Base):
    """产品字典深度管理扩展属性 ORM 映射模型 (对齐图4产品字典高级功能)"""
    __tablename__ = "spd_product_dict_ext"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "产品字典深度管理扩展表(维护通用名、拼音码、组件名、品牌、多仓库分配、停用状态、调价记录与JSON自定义列)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="扩展记录主键ID")
    product_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False, comment="关联主字典ID(spd_product_dict.id)")
    product_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="产品编码冗余")
    common_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False, comment="耗材通用名(如: 医用一次性无菌注射器)")
    pinyin_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="拼音助记码(根据产品名称自动生成首字母大写, 如: YYYCXWJZSQ)")
    component_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="组件名称(复合耗材包或植入物组件明细)")
    brand_name: Mapped[str] = mapped_column(String(64), default="国产品牌", nullable=False, comment="品牌名称(如: 威高WEGO, 迈瑞Mindray, 强生J&J)")
    assigned_warehouses: Mapped[str] = mapped_column(String(255), default="WH_WEICAI", nullable=False, comment="已分配/复制到的仓库编码逗号分隔列表(支持复制品名到其他仓库)")
    supplier_code: Mapped[str] = mapped_column(String(32), index=True, default="SUP_001", nullable=False, comment="当前绑定主供应商编码(支持变更供应商)")
    previous_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="调价前历史参考单价(元)")
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="当前生效单价(元)")
    price_updated_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="最近一次调价原因说明(如: 省级带量采购中标调价)")
    is_disabled: Mapped[int] = mapped_column(SmallInteger, default=0, index=True, nullable=False, comment="停用状态(支持勾选显示停用过滤): 0-在用, 1-已停用")
    extra_fields_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="动态扩展属性JSON字符串(如医保编码、阳光采购流水号、灭菌方式)")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后更新时间")


class SpdInboundAndOutboundOrder(Base):
    """普通耗材与二级库出入库单、退给供应商红字单、请领审核自动出库单及科室期初建账单 ORM 映射模型"""
    __tablename__ = "spd_inbound_outbound_order"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "通用出入库与期初建账业务单据表(含两阶段二次确认状态机、退给供应商红字单、请领审核自动出库联动)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="出入库单主键ID")
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="业务单据编号(如: INB20261102001, RET20261102001, OUT20261102001, INI20261102001)")
    order_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="单据类型: GEN_INBOUND-耗材验收入库单, RETURN_TO_SUPPLIER-退给供应商红字退货单, GEN_MANUAL_OUT-手动耗材出库单, REQ_AUTO_OUT-请领审核通过自动出库单, INIT_STOCK-科室仓库期初数据建账单, SEC_RECEIVE_IN-二级库接收入库单, SEC_ISSUE_OUT-二级库发料出库单")
    warehouse_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="所属仓库编码(关联spd_warehouse_node.warehouse_code)")
    dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="所属科室编码")
    target_dept_or_supplier: Mapped[str] = mapped_column(String(64), nullable=False, comment="往来对象编码或名称(供应商编码/领用临床科室编码/目标二级库)")
    product_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联产品ID(spd_product_dict.id)")
    product_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="产品编码冗余")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="产品名称冗余")
    batch_no: Mapped[str] = mapped_column(String(64), default="BATCH-INIT", nullable=False, comment="生产批号")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="单据变动数量(退给供应商红字单为负数或标记红冲)")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="单价(元)")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="总金额(元)")
    source_ref_order_no: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True, comment="上游触发源单号(如请领单号REQxxx或供应商发货单号SHPxxx)")
    confirm_stage: Mapped[str] = mapped_column(String(32), index=True, default="PENDING_CONFIRM", nullable=False, comment="两阶段确认状态机: DRAFT-草稿, PENDING_CONFIRM-填单已做第1次提交(待外层确认,可改可删), SUBMITTED-外层已完成第2次确认提交(正式生效锁死)")
    is_irreversible_locked: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否不可逆永久锁死: 0-普通单据可点取消提交回退, 1-永久锁死不可取消不可改(如INIT_STOCK期初建账单)")
    created_by: Mapped[str] = mapped_column(String(64), nullable=False, comment="第1次填单提交人姓名")
    second_confirmed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="第2次外层确认提交人姓名")
    second_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="第2次外层确认提交时间")
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="业务备注或退货原因")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="制单时间")


class SpdStocktakeAndTransferOrder(Base):
    """全院各科室独立仓库盘点单与跨科/跨院调拨单 ORM 映射模型"""
    __tablename__ = "spd_stocktake_transfer_order"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "全院各科室仓库盘点单(账实盈亏自动修正库存)与跨科/跨院区调拨单表"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="盘点或调拨单主键ID")
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="单据编号(如: STK20261102001, TRF20261102001)")
    biz_category: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="业务大类: GEN_STOCKTAKE-普耗盘点, HV_STOCKTAKE-高值盘点, SEC_STOCKTAKE-二级库盘点, DEPT_TRANSFER-院内跨科调拨, CROSS_HOSP_TRANSFER-跨院区调拨")
    from_warehouse_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="盘点仓库编码或调出方仓库编码")
    to_warehouse_code: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True, comment="调入方仓库编码(盘点单此项为空)")
    product_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联产品ID")
    product_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="产品编码冗余")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="产品名称冗余")
    book_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="盘点前系统账面数量(调拨单表示调出前库存)")
    actual_or_transfer_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="实盘数量(盘点单)或实际调拨数量(调拨单)")
    diff_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="盘盈盘亏差额(actual - book, 正数为盘盈, 负数为盘亏)")
    confirm_stage: Mapped[str] = mapped_column(String(32), index=True, default="PENDING_CONFIRM", nullable=False, comment="两阶段确认状态机: PENDING_CONFIRM-待外层二次确认, SUBMITTED-已二次确认生效并修正库存")
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="盘点人/调拨发起人")
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="外层二次确认审核人")
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="二次确认生效时间")
    reason_note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="盘盈盘亏原因说明或跨院调拨事由")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class SpdHighValueLifecycleOrder(Base):
    """高值耗材备货申请、科室接收、科室退货(二次确认永久锁死)、高值报损与一物一码二维码扫码核销表"""
    __tablename__ = "spd_high_value_lifecycle_order"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "高值耗材全生命周期扩展单据表(含备货管理、科室接收、二次确认后永久不可改的科室退货出库单、高值报损及专属二维码核销)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="高值生命周期单据主键ID")
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="高值单据编号(如: HVP20261102001, HVR20261102001, HVD20261102001)")
    hv_biz_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="高值业务类型: HV_STOCK_PREP-高值备货申请单, HV_DEPT_RECEIVE-科室接收入库确认单, HV_DEPT_RETURN-科室退货出库单(二次确认后永久不可改), HV_DAMAGE_REPORT-高值报损单, HV_QR_VERIFY-高值一物一码二维码扫码核销记录")
    dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="申请或操作临床科室编码(如: SEC_CARDIO, SEC_ORTHO)")
    product_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联高值产品ID")
    product_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="高值产品编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="高值产品名称")
    udi_sn: Mapped[str] = mapped_column(String(128), index=True, nullable=False, comment="高值单品UDI唯一序列号(一物一码)")
    qr_code_payload: Mapped[str] = mapped_column(String(255), nullable=False, comment="系统生成的专属高值二维码加密载荷(含UDI+批号+效期+产品编码)")
    is_qr_verified: Mapped[int] = mapped_column(SmallInteger, default=0, index=True, nullable=False, comment="是否已完成二维码扫码核销: 0-未扫码核销(核销查询不显示), 1-已扫码核销绑定患者(可在高值核销查询中检索)")
    patient_inpatient_no: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True, comment="扫码核销绑定的患者住院号(脱敏存储)")
    patient_name_masked: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="扫码核销绑定的患者脱敏姓名(如: 陈*生)")
    confirm_stage: Mapped[str] = mapped_column(String(32), index=True, default="PENDING_CONFIRM", nullable=False, comment="两阶段确认状态机: PENDING_CONFIRM-第1次提交待确认(可改可删), SUBMITTED-第2次确认已正式提交, APPROVED-设备科已审批")
    is_irreversible_locked: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否永久不可逆锁死: 1-当hv_biz_type为HV_DEPT_RETURN且进入SUBMITTED时强制置1(永久禁止取消提交/修改/删除)")
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="操作护士/技师姓名")
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="外层二次确认人或设备科审批人")
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="二次确认或扫码核销时间")
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="退回原因、报损原因或手术室核销备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class SpdSupplierAndPurchaseOrder(Base):
    """供应商经营资质准入绑定、临床多级采购计划单与供应商拣货发货协同表"""
    __tablename__ = "spd_supplier_purchase_order"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "多级采购计划与外部供应商资质准入、接单、拣货、发货闭环表(供应商二次确认发货后自动生成医院待验收入库单)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="采供协同单据主键ID")
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="采购或发货单号(如: PUR20261102001, SHP20261102001)")
    supplier_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="供应商唯一编码(如: SUP_WEGO_01)")
    supplier_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="供应商企业全称")
    license_no: Mapped[str] = mapped_column(String(128), nullable=False, comment="上传的《医疗器械经营许可证》编号")
    license_expiry_date: Mapped[date] = mapped_column(Date, nullable=False, comment="经营许可证有效截止日期")
    qual_audit_status: Mapped[str] = mapped_column(String(32), index=True, default="QUAL_APPROVED", nullable=False, comment="供应商资质准入与医院绑定状态: QUAL_PENDING-待医院耗材/设备科审核(硬拦截接单发货), QUAL_APPROVED-资质已审核绑定通过, QUAL_REJECTED-资质驳回")
    apply_dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="发起采购申请的临床科室或主库科室编码(如: SEC_CARDIO -> EQUIP_DEPT)")
    audit_main_dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="负责层层审批的主科室编码(CONSUMABLE_DEPT或EQUIP_DEPT)")
    product_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="采购产品ID")
    product_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="采购产品编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="采购产品名称")
    purchase_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="计划采购数量")
    picked_batch_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="供应商拣货填写的生产批号")
    picked_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="供应商拣货填写的有效期至")
    confirm_stage: Mapped[str] = mapped_column(String(32), index=True, default="PENDING_CONFIRM", nullable=False, comment="两阶段确认状态机: PENDING_CONFIRM-待外层二次确认, SUBMITTED-已二次确认正式提交")
    purchase_flow_status: Mapped[str] = mapped_column(String(32), index=True, default="PLAN_SUBMITTED", nullable=False, comment="采供全链路状态: PLAN_SUBMITTED-科室已提报待主科审批, DEPT_APPROVED-主科已批转供应商订单, SUPPLIER_ACCEPTED-供应商已接单拣货中, SUPPLIER_SHIPPED-供应商已二次确认发货, HOSP_INBOUND_CREATED-已自动生成医院待验收入库单")
    auto_inbound_order_no: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True, comment="供应商二次确认发货后自动生成的医院端《待验收入库单》单号")
    created_by: Mapped[str] = mapped_column(String(64), nullable=False, comment="采购申请人或供应商操作人")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后状态更新时间")


class SpdProductSpn(Base):
    """三级中枢：医疗物资大品名 ORM 映射模型 (对应图 3 品名管理)"""
    __tablename__ = "spd_product_spn"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "医疗物资产品大品名表(作为品类归口中枢，统领下属多种规格型号单品)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="大品名主键ID")
    spn_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="大品名唯一编码(如: 936010100024)")
    spn_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False, comment="耗材大品名名称(如: 医用氧气123)")
    category_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="所属耗材属性分类编码(如: 0101|氧气)")
    common_name: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="通用名称")
    pinyin_code: Mapped[str] = mapped_column(String(64), index=True, default="", nullable=False, comment="拼音首字母简码(如: YYYQ123)")
    finance_category: Mapped[str] = mapped_column(String(64), default="西药卫生材料", nullable=False, comment="财务核算分类")
    performance_category: Mapped[str] = mapped_column(String(64), default="医疗耗材消耗", nullable=False, comment="绩效核算分类")
    inpatient_charge_category: Mapped[str] = mapped_column(String(64), default="住院治疗材料费", nullable=False, comment="住院收费分类")
    outpatient_charge_category: Mapped[str] = mapped_column(String(64), default="门诊检查处置费", nullable=False, comment="门诊收费分类")
    medical_record_category: Mapped[str] = mapped_column(String(64), default="治疗用器械材料", nullable=False, comment="病案分类")
    medicare_category: Mapped[str] = mapped_column(String(64), default="甲类医保可报销材料", nullable=False, comment="医保分类")
    is_chargeable: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否收费材料: 1-是, 0-否")
    is_high_value: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否高值耗材: 1-是, 0-否")
    is_central_proc: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否国家/省带量集采项目: 1-是, 0-否")
    central_proc_project: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="集采项目名称及批次文号")
    contract_no: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="采购合同编号")
    contract_signed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="合同签订日期")
    contract_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="合同开始日期")
    contract_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="合同结束日期")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, comment="品名启用状态: ACTIVE-启用, DISABLED-停用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="建档时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")


class SpdProductSpec(Base):
    """四级终端：产品型号规格 ORM 映射模型 (对应图 4 右表 & 图 5 规格详情)"""
    __tablename__ = "spd_product_spec"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "产品型号规格单品表(同品名裂变为多个独立条码规格单品，承载单价、厂商、包装与资质)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="规格主键ID")
    spn_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联大品名主键(spd_product_spn.id)")
    spec_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="产品规格代码(唯一条码物料编码，如: 936010100024055517)")
    product_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False, comment="大品名名称冗余")
    component_name: Mapped[str] = mapped_column(String(128), default="主件", nullable=False, comment="组件名称(如: 瓶装氧气、5ml针筒组件)")
    pinyin_code: Mapped[str] = mapped_column(String(64), index=True, default="", nullable=False, comment="拼音首字母简码")
    common_name: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="通用名")
    brand_name: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="品牌名称")
    spec_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="规格描述(如: 40L 瓶装 / 5ml 带针 0.7*30mm)")
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="型号(如: TWLB / 8孔左侧)")
    manufacturer: Mapped[str] = mapped_column(String(128), nullable=False, comment="生产厂家企业全称(如: 普昂(杭州)医疗、威高Wego)")
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="产品详细说明与使用规范")
    pricing_unit: Mapped[str] = mapped_column(String(32), nullable=False, comment="最小计价单位(如: 支、瓶、盒、套、袋)")
    package_unit: Mapped[str] = mapped_column(String(32), default="箱", nullable=False, comment="大包装物流单位(如: 箱、大盒)")
    conversion_ratio: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.00"), nullable=False, comment="大小包装转换比(1箱折合多少最小计价单位)")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, comment="现行基准采购/记账单价(元)")
    register_card_no: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="医疗器械注册证号/备案号")
    register_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="注册证有效截止日期")
    medicare_code: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="国家医保医用耗材27位编码")
    medicare_category_code: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="医保耗材分类编码")
    production_license_no: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="医疗器械生产许可证号")
    production_license_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="生产许可证有效截止日期")
    default_supplier_id: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, comment="默认供货供应商ID")
    default_supplier_name: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="默认供货供应商企业名称")
    original_code: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="原厂物料编号/原位码")
    provincial_code: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="省级平台阳光挂网编码/省标码")
    storage_condition: Mapped[str] = mapped_column(String(64), default="常温干燥避光", nullable=False, comment="温湿度储存环境要求(常温/冷藏2-8℃/阴凉)")
    is_central_proc: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否属于带量集采规格: 1-是, 0-否")
    central_proc_code: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="集采中选规格物料编码")
    origin_place: Mapped[str] = mapped_column(String(64), default="国产", nullable=False, comment="产地属性(国产/进口/合资)")
    category_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="所属耗材分类编码")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, comment="规格状态: ACTIVE-正常在用, DISABLED-已停用")
    assigned_warehouses: Mapped[str] = mapped_column(String(255), default="WH_WEICAI,WH_SEC_ORTHO", nullable=False, comment="授权分配并支持在库的仓库编码列表(逗号分隔)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="规格创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后更新时间")


class SpdSupplierProfile(Base):
    """供应商资质与准入档案 ORM 映射模型 (对应图 4 中栏供应商 Tab)"""
    __tablename__ = "spd_supplier_profile"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "医疗物资供应商资质准入档案表(在产品字典中支持独立维护与资质预警)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="供应商主键ID")
    supplier_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="供应商唯一编码(如: SUP_WEGO_01)")
    supplier_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False, comment="供应商企业法定全称")
    social_credit_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="统一社会信用代码(18位)")
    license_no: Mapped[str] = mapped_column(String(128), nullable=False, comment="《医疗器械经营许可证》编号")
    license_expiry_date: Mapped[date] = mapped_column(Date, nullable=False, comment="经营许可证有效截止日期")
    contact_person: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="主要业务联系人")
    contact_phone: Mapped[str] = mapped_column(String(32), default="", nullable=False, comment="业务联系手机号")
    supply_categories: Mapped[str] = mapped_column(String(255), default="普耗,高值,骨科,心内", nullable=False, comment="主营供货物资品类范围")
    qual_status: Mapped[str] = mapped_column(String(32), default="QUAL_APPROVED", nullable=False, comment="资质状态: QUAL_APPROVED-审核通过正常供货, QUAL_PENDING-待审, QUAL_EXPIRED-资质已到期熔断")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, comment="档案启用状态: ACTIVE-启用, DISABLED-停用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="建档时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后更新时间")


class SysUserWarehousePerm(Base):
    """用户与仓库细粒度授权矩阵 ORM 映射模型 (按人分仓，限申领/查看等原子动作)"""
    __tablename__ = "sys_user_warehouse_perm"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "用户与仓库细粒度权限绑定表(普通人员仅见分配到的仓库，并按查看/申领/出库等细粒度控制)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="权限记录主键ID")
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联用户ID(sys_user.id)")
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="人员工号冗余")
    warehouse_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="被分配绑定的仓库编码(spd_warehouse_node.warehouse_code)")
    can_view: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="查看仓库物资权限: 1-允许, 0-禁止")
    can_apply: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="向该仓库发起申领物资权限: 1-允许, 0-禁止")
    can_inbound: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="验收入库权限: 1-允许, 0-禁止")
    can_outbound: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="出库与发料确认权限: 1-允许, 0-禁止")
    can_stocktake: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="盘点与库存核减权限: 1-允许, 0-禁止")
    can_transfer: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="跨仓调拨与分发确认权限: 1-允许, 0-禁止")
    updated_by: Mapped[str] = mapped_column(String(64), default="sys_admin", nullable=False, comment="最后授权分配人")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后更新时间")


class SpdPriceAdjustLog(Base):
    """集中带量采购与历史调价不可篡改审计日志 ORM 映射模型"""
    __tablename__ = "spd_price_adjust_log"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "产品规格历史调价不可篡改快照表(记录国家集采/医保谈判/厂家调价历史，供图5调价记录展示)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="调价记录主键ID")
    spec_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联产品规格ID(spd_product_spec.id)")
    spec_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="规格编码冗余")
    spec_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="规格型号描述")
    old_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, comment="调价前原基准单价(元)")
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, comment="调价后新基准单价(元)")
    adjust_diff: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, comment="调价金额差额(新价 - 原价)")
    adjust_reason: Mapped[str] = mapped_column(String(128), nullable=False, comment="调价业务原因(如: 国家集中带量采购中选降价)")
    adjust_doc_no: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="调价政策依据文件号/文号")
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="调价操作人员姓名与工号")
    effective_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="调价实际生效执行时间")

