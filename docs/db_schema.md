# docs/db_schema.md - 数据库 SQLAlchemy 2.0 ORM 映射设计与 `comment` 注释契约

> 本文件作为 **Harness 组件①（数据库设计渐进式披露源）** 与 **组件④（ORM 架构硬约束）**。
> **核心铁律**：本项目全部 MySQL 8.0 数据表统一采用 **SQLAlchemy 2.0 声明式 ORM 映射（`DeclarativeBase`、`Mapped`、`mapped_column`）** 创建与迁移；**所有表（`__table_args__`）与所有字段（`mapped_column`）必须 100% 显式声明中文 `comment="..."` 注释**，确保数据库自解释并直接赋能 MCP 智能体工具零幻觉查询。

---

## 一、 数据库全局连接与命名约定

- **数据库引擎**：MySQL 8.0 (`InnoDB`)，字符集 `utf8mb4`，排序规则 `utf8mb4_unicode_ci`
- **库名约定**：`medical_spd_system`
- **ORM 映射位置**：`backend/app/models/`
- **通用审计字段约定**：所有核心表统一包含主键 `id`、创建时间 `created_at`、更新时间 `updated_at` 及软删除标记 `is_deleted`（全部携带中文 `comment`）。

---

## 二、 核心业务表 SQLAlchemy 2.0 ORM 映射规范定义（共 9 张核心表）

### 1. 科室与库房架构表 (`sys_department`)
```python
class SysDepartment(Base):
    """全院科室与库房层级架构 ORM 映射模型"""
    __tablename__ = "sys_department"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "全院科室与库房架构表(区分信息科、主库房管理科室、财务科与临床二级库科室)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="科室主键ID")
    dept_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="科室唯一编码(如: INFO_DEPT, CONSUMABLE_DEPT, EQUIP_DEPT, FINANCE_DEPT, SEC_ORTHO)")
    dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="科室名称(如: 信息科, 耗材科主库, 设备科主库, 财务科, 骨科二级库)")
    dept_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="科室职能类型: SYS_ADMIN-信息科管理, MAIN_WAREHOUSE-主库房管理科室(耗材科/设备科), FINANCE-财务核算科室, SECONDARY_WAREHOUSE-临床二级库科室")
    warehouse_zone: Mapped[str] = mapped_column(String(64), nullable=True, comment="关联物理库区位置编码(如: 中心主库A区, 高值专仓B区, 住院部3楼骨科二级库)")
    contact_person: Mapped[str] = mapped_column(String(32), nullable=True, comment="科室库房负责人姓名")
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=True, comment="科室联系电话(脱敏展示)")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="启用状态: 1-正常启用, 0-停用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
```

### 2. 三级人员用户表 (`sys_user`)
```python
class SysUser(Base):
    """系统三级人员用户与权限 ORM 映射模型"""
    __tablename__ = "sys_user"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "系统用户表(含系统管理员-信息科、科室管理员-耗材/设备/财务科、临床科室二级库人员)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户主键ID")
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="登录账号/工号")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="BCrypt加密密码哈希值")
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="用户真实姓名(用于单据签字栏与流转日志记录)")
    role_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="三级角色编码: sys_admin-系统管理员(信息科最大权限), dept_manager-科室管理员(耗材科/设备科/财务科), secondary_user-临床科室人员(二级库)")
    dept_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="所属科室ID(关联sys_department.id)")
    dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="所属科室编码冗余(便于按主科室归口快速鉴权)")
    phone_masked: Mapped[str] = mapped_column(String(32), nullable=True, comment="脱敏手机号(如: 138****5678)")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="账号状态: 1-正常, 0-禁用冻结")
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="软删除标记: 0-未删除, 1-已删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="注册/添加时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
```

### 3. 产品字典分类配置表 (`spd_category`)
```python
class SpdCategory(Base):
    """产品字典多维分类配置 ORM 映射模型"""
    __tablename__ = "spd_category"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "产品字典分类体系表(维护主库房下主科室归属与耗材多级分类树)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="分类主键ID")
    category_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="分类标准编码")
    category_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="分类名称(如: 注射穿刺类, 医用敷料类, 骨科植入物, 心血管介入物, 医疗设备配件)")
    main_dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="主库房下的归口主科室编码: CONSUMABLE_DEPT-耗材科主库, EQUIP_DEPT-设备科主库")
    consumable_level: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="耗材管控级别分类: GENERAL-普通耗材, HIGH_VALUE-高值耗材, EQUIP_PART-设备维保配件")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, comment="父级分类ID(0表示一级分类)")
    storage_condition: Mapped[str] = mapped_column(String(64), default="常温干燥", nullable=False, comment="法定储运温湿度条件(如: 常温干燥, 冷链2~8℃, 避光阴凉)")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="同级显示排序权重")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
```

### 4. 医疗物资产品字典表 (`spd_product_dict` —— 核心 CRUD 一)
```python
class SpdProductDict(Base):
    """医疗物资产品字典 ORM 映射模型"""
    __tablename__ = "spd_product_dict"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "医疗物资产品字典表(存放各类产品标准信息、归属主库房主科室与耗材分类)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="产品字典主键ID")
    product_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="院内产品标准编码(全局唯一)")
    product_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False, comment="医疗物资产品通用名称")
    udi_di: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="国家药监局UDI-DI产品固定标识(14位GS1基准码)")
    main_dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="主库房归口管理主科室: CONSUMABLE_DEPT-耗材科主库, EQUIP_DEPT-设备科主库")
    consumable_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="耗材一级分类: GENERAL-普通耗材(按批次数量管理), HIGH_VALUE-高值耗材(分拨入高值仓一物一码管理), EQUIP_PART-设备配件")
    category_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="所属细分品类ID(关联spd_category.id)")
    category_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="所属细分品类名称冗余(便于大模型MCP直接读取)")
    spec_model: Mapped[str] = mapped_column(String(128), nullable=False, comment="规格型号说明(如: 5ml带针, Φ4.0*120mm钛合金)")
    unit: Mapped[str] = mapped_column(String(16), nullable=False, comment="计量单位(支/盒/套/件/包)")
    manufacturer: Mapped[str] = mapped_column(String(128), nullable=False, comment="生产厂家全称")
    supplier_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="供货商企业名称")
    reg_cert_no: Mapped[str] = mapped_column(String(64), nullable=False, comment="国家医疗器械注册证号/备案凭证号(如: 国械注准20243130001)")
    reg_cert_expiry: Mapped[date] = mapped_column(Date, nullable=False, comment="医疗器械注册证到期日期(过期触发入库硬拦截)")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"), comment="采购与核算基准单价(人民币元)")
    safe_stock_min: Mapped[int] = mapped_column(Integer, default=20, nullable=False, comment="主库安全库存下限阈值(低于此值触发智能体补货预警)")
    safe_stock_max: Mapped[int] = mapped_column(Integer, default=500, nullable=False, comment="主库安全库存上限阈值(防止积压呆滞)")
    storage_temp_req: Mapped[str] = mapped_column(String(32), default="常温(10~30℃)", nullable=False, comment="储运温度要求说明")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="字典状态: 1-在用, 0-停用归档")
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="软删除标记: 0-正常, 1-已删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="建档时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
```

### 5. 普通耗材管理：主库全部物资批次库存表 (`spd_main_inventory` —— 核心 CRUD 二)
```python
class SpdMainInventory(Base):
    """主库总仓(耗材科/设备科)全部物资批次库存 ORM 映射模型"""
    __tablename__ = "spd_main_inventory"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "主库房总仓批次库存表(管理全部入库物资，支持按需分发至临床二级库或转入高值耗材仓库)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主库批次库存主键ID")
    inbound_order_no: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="关联主库验收入库单号(用于单据打印与溯源)")
    product_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联产品字典ID(spd_product_dict.id)")
    product_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="产品标准编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="产品名称冗余")
    main_dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="所属主库房管理科室: CONSUMABLE_DEPT-耗材科主库, EQUIP_DEPT-设备科主库")
    consumable_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="物资分类: GENERAL-普通耗材, HIGH_VALUE-高值耗材, EQUIP_PART-设备配件")
    batch_no: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="生产批号(UDI-PI应用标识符10)")
    production_date: Mapped[date] = mapped_column(Date, nullable=False, comment="生产日期(UDI-PI应用标识符11)")
    expiry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False, comment="有效期至(UDI-PI应用标识符17，用于FEFO排序与效期硬拦截)")
    initial_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="本批次初始验收入库数量")
    available_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="当前主库剩余可用数量(分发后扣减，退库后增加)")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, comment="本批次入库单价(元)")
    shelf_location: Mapped[str] = mapped_column(String(64), nullable=False, comment="主库三维货位编码(如: 耗材主库-A区-01架-02层)")
    accept_temp: Mapped[str] = mapped_column(String(32), default="22.5℃(合规)", nullable=False, comment="入库验收实测温度记录")
    quality_status: Mapped[str] = mapped_column(String(32), index=True, default="NORMAL", nullable=False, comment="批次风控状态: NORMAL-正常可用, NEAR_EXPIRY-近效期预警, EXPIRED-过期冻结(禁止分发), RECALLED-不良事件召回锁定, DAMAGED-报损核销")
    inbound_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="验收入库操作员ID")
    inbound_user_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="验收入库操作员姓名(主库管理员)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="入库时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="库存最后更新时间")
```

### 6. 主库按需分发调拨单表 (`spd_distribution_order` —— 核心 CRUD 二关联单据)
```python
class SpdDistributionOrder(Base):
    """主库向临床二级库或高值耗材仓库按需分发调拨单 ORM 映射模型"""
    __tablename__ = "spd_distribution_order"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "主库按需分发调拨单表(记录主库将物资按需分发给临床二级库或转入高值耗材仓库的单据)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="分发调拨单主键ID")
    dist_order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="按需分发调拨单唯一编号(如: DIST-20261102-001)")
    source_main_dept: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="发料主库房科室编码: CONSUMABLE_DEPT-耗材科主库, EQUIP_DEPT-设备科主库")
    target_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="按需分发目标类型: TO_SECONDARY_DEPT-分发至临床二级库, TO_HIGH_VALUE_WH-转入高值耗材专仓(触发一物一码拆包赋码)")
    target_dept_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="接收目标科室/库房ID(关联sys_department.id)")
    target_dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="接收目标科室/库房名称")
    main_inventory_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="源主库批次库存ID(关联spd_main_inventory.id)")
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="产品字典ID")
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="产品标准编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="产品名称")
    batch_no: Mapped[str] = mapped_column(String(64), nullable=False, comment="分发物资生产批号")
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, comment="分发物资有效期至")
    dist_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="本次按需分发数量")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, comment="单价(元)")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, comment="分发单总金额(元，遵循移库不计费原则，仅作调拨台账凭证)")
    order_status: Mapped[str] = mapped_column(String(32), index=True, default="DISPATCHED", nullable=False, comment="分发单状态: DRAFT-草稿, DISPATCHED-主库已发料待签收, RECEIVED-二级库/高值仓已签收, REJECTED-差异拒收退回主库")
    dispatcher_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="主库发料管理员ID")
    dispatcher_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="主库发料管理员姓名(用于打印签字栏)")
    receiver_id: Mapped[int] = mapped_column(BigInteger, nullable=True, comment="接收科室/高值仓签收人ID")
    receiver_name: Mapped[str] = mapped_column(String(64), nullable=True, comment="接收科室/高值仓签收人姓名(用于打印签字栏)")
    remark: Mapped[str] = mapped_column(String(255), nullable=True, comment="分发备注或AI智能体调拨依据说明")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="制单分发时间")
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="实际签收时间")
```

### 7. 高值耗材管理：高值耗材专仓一物一码表 (`spd_high_value_item` —— 核心 CRUD 三)
```python
class SpdHighValueItem(Base):
    """高值耗材仓库一物一码全生命周期管理 ORM 映射模型"""
    __tablename__ = "spd_high_value_item"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "高值耗材一物一码专仓表(主库分拨入仓时拆包赋唯一UDI序列号，追踪至临床患者核销)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="高值耗材单品主键ID")
    udi_full_code: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False, comment="完整GS1-128一物一码UDI条码字符串(DI+PI+SN)")
    udi_sn: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="高值耗材单品唯一序列号(UDI-PI应用标识符21，全局唯一)")
    dist_order_no: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="来源主库分发调拨单号(关联spd_distribution_order.dist_order_no)")
    product_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联产品字典ID")
    product_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="产品标准编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="高值耗材名称")
    spec_model: Mapped[str] = mapped_column(String(128), nullable=False, comment="规格型号")
    main_dept_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="归口主管理科室(CONSUMABLE_DEPT/EQUIP_DEPT)")
    batch_no: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="生产批号")
    expiry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False, comment="有效期至")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, comment="单品核算单价(元)")
    wh_cabinet_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="高值专仓或手术室智能柜位置编码(如: 高值专仓-智能柜01-A03格)")
    current_dept_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="当前所在科室/库房ID")
    current_dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="当前所在科室/库房名称")
    item_status: Mapped[str] = mapped_column(String(32), index=True, default="IN_HIGH_VALUE_WH", nullable=False, comment="高值单品状态: IN_HIGH_VALUE_WH-高值仓在库, IN_SECONDARY_CABINET-已下发二级库专柜, SURGERY_LOCKED-手术跟台锁定, USED_VERIFIED-已绑定患者使用核销(触发财务记账), RETURNED-未使用退回高值仓, RECALLED-不良事件召回冻结")
    patient_inpatient_no: Mapped[str] = mapped_column(String(64), index=True, nullable=True, comment="使用患者住院号/病案号(核销时必填)")
    patient_name_masked: Mapped[str] = mapped_column(String(64), nullable=True, comment="使用患者脱敏姓名(如: 张*丰)")
    surgery_name: Mapped[str] = mapped_column(String(128), nullable=True, comment="关联手术/诊疗名称(如: 经皮冠状动脉支架植入术)")
    attending_doctor: Mapped[str] = mapped_column(String(64), nullable=True, comment="主刀/执行医生姓名")
    verify_nurse_name: Mapped[str] = mapped_column(String(64), nullable=True, comment="扫码核销临床二级库护士姓名")
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="临床扫码使用核销时间(即财务结算记账时间)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="拆包赋码入高值仓时间")
```

### 8. 临床二级库管理：二级库库存与申领表 (`spd_secondary_inventory` & `spd_requisition_order` —— 核心 CRUD 四)
```python
class SpdSecondaryInventory(Base):
    """临床各科室二级库库存台账 ORM 映射模型"""
    __tablename__ = "spd_secondary_inventory"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "临床科室二级库库存表(管理主库分发至各临床科室二级库的物资库存、日常消耗与预警)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="二级库库存主键ID")
    dept_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="所属临床二级库科室ID(关联sys_department.id)")
    dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="所属临床二级库科室名称(如: 骨科二级库, 心内科二级库)")
    product_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="关联产品字典ID")
    product_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="产品标准编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="产品名称")
    main_dept_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="归口主库房科室(CONSUMABLE_DEPT-耗材科, EQUIP_DEPT-设备科)")
    batch_no: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="生产批号")
    expiry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False, comment="有效期至")
    current_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="本二级库当前可用库存数量")
    consumed_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="本批次在本科室累计已消耗数量(已触发财务记账数量)")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, comment="核算单价(元)")
    sec_shelf_code: Mapped[str] = mapped_column(String(64), default="二级库标准货架-01", nullable=False, comment="临床二级库内部存放货位/定数包编号")
    dept_safe_min: Mapped[int] = mapped_column(Integer, default=5, nullable=False, comment="本二级库安全库存下限(低于此值触发向主库自动申领预警)")
    batch_status: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False, comment="状态: NORMAL-正常, NEAR_EXPIRY-临期, EXPIRED-过期锁定, RETURN_PENDING-待退回主库")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后变动时间")


class SpdRequisitionOrder(Base):
    """临床二级库向主库(耗材科/设备科)物资申领与退库单 ORM 映射模型"""
    __tablename__ = "spd_requisition_order"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "临床二级库物资申领与退库单表(按归口主科室定向流转至耗材科或设备科审批)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="申领单主键ID")
    req_order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="二级库申领/退库单唯一编号(如: REQ-20261102-001)")
    order_direction: Mapped[str] = mapped_column(String(32), default="APPLY_FROM_MAIN", nullable=False, comment="单据流向类型: APPLY_FROM_MAIN-二级库向主库正向申领, RETURN_TO_MAIN-二级库向主库逆向退库")
    apply_dept_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="申领临床二级库科室ID")
    apply_dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="申领临床二级库科室名称")
    target_main_dept: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="定向审批主库房科室: CONSUMABLE_DEPT-耗材科主库, EQUIP_DEPT-设备科主库")
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="申领产品字典ID")
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="申领产品编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="申领产品名称")
    apply_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="申领/退库数量")
    approved_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="主库管理员实际批准分发数量")
    urgency_level: Mapped[str] = mapped_column(String(32), default="ROUTINE", nullable=False, comment="紧急程度: ROUTINE-日常定数包补货, URGENT-手术急用加急")
    req_status: Mapped[str] = mapped_column(String(32), index=True, default="PENDING_APPROVAL", nullable=False, comment="申领单状态: PENDING_APPROVAL-待主库审批, APPROVED_DISPATCHED-已批准并生成分发单, REJECTED-已驳回, COMPLETED-二级库已签收闭环, CANCELLED-申请人已撤回")
    applicant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="二级库申领人员ID")
    applicant_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="二级库申领人员姓名")
    approver_id: Mapped[int] = mapped_column(BigInteger, nullable=True, comment="主库审批管理员ID")
    approver_name: Mapped[str] = mapped_column(String(64), nullable=True, comment="主库审批管理员姓名(耗材科/设备科)")
    apply_reason: Mapped[str] = mapped_column(String(255), nullable=True, comment="申领用途说明或AI对话申领原始指令")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="发起申领时间")
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="审批完成时间")
```

### 9. 基础业务链路全流程日志表 (`spd_workflow_log` —— 核心 CRUD 五：6W 物权交接台账)
```python
class SpdWorkflowLog(Base):
    """全流程业务链路日志与跨用户流转关系 ORM 映射模型"""
    __tablename__ = "spd_workflow_log"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "全流程业务链路日志表(记录信息科、耗材/设备主库、高值仓、临床二级库与财务科各用户间的6W物权交接关系)"
    }

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="全流程日志主键ID")
    trace_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment="日志唯一追踪流水号(如: LOG-20261102112000-001)")
    biz_order_no: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="关联业务单据编号(入库单号/按需分发单号/申领单号/高值核销单号)")
    node_action: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="8大标准业务流转节点: 1_DICT_CREATE-字典建档, 2_MAIN_INBOUND-主库验收入库, 3_MAIN_DISPATCH-主库按需分发, 4_HIGH_VALUE_CODE-高值仓赋码入仓, 5_SEC_RECEIVE-二级库签收入库, 6_SEC_APPLY-二级库申领审批, 7_CLINICAL_CONSUME-临床消耗/患者核销(触发财务结算), 8_REVERSE_AUDIT-逆向退库/报损/财务审核")
    product_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="流转物资产品编码")
    product_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="流转物资产品名称")
    batch_or_udi: Mapped[str] = mapped_column(String(128), index=True, nullable=False, comment="关联生产批号或高值耗材UDI唯一序列号")
    from_dept_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="交出方(源)科室/库房名称(如: 供应商 / 耗材科主库 / 设备科主库)")
    from_user_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="交出方操作用户姓名与角色(如: 王建国[耗材科管理员])")
    to_dept_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="接收方(目标)科室/库房名称(如: 骨科二级库 / 高值耗材专仓 / 患者核销)")
    to_user_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="接收方责任用户姓名与角色(如: 李晓琳[骨科二级库护士])")
    change_qty: Mapped[int] = mapped_column(Integer, nullable=False, comment="本次流转变动数量")
    before_stock_snapshot: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="流转前库存快照数量")
    after_stock_snapshot: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="流转后库存快照数量")
    settlement_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False, comment="涉及金额(元)")
    is_billable: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否触发财务科科室成本记账: 0-移库不计费(院内调拨), 1-消耗即结算(计入临床科室成本)")
    audit_status: Mapped[str] = mapped_column(String(32), index=True, default="VERIFIED", nullable=False, comment="信息科/财务科审计状态: VERIFIED-正常合规流转, FLAGGED-疑似异常待复核, RECTIFIED-已核实整改")
    audit_remark: Mapped[str] = mapped_column(String(255), nullable=True, comment="流转详情说明或管理员审计复核批注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True, nullable=False, comment="流转发生精确时间戳")
```
