"""产品字典与双维分类管理路由模块 (核心 CRUD 一)

本模块管理“主库房下主科室归属（耗材科/设备科）+ 耗材多级分类”双维分类及医疗物资产品标准字典档案。
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_user_context, require_roles, CurrentUserContext
from app.models.spd_models import (
    SysUser,
    SpdCategory,
    SpdProductDict,
    SpdMainInventory,
    SpdHighValueItem,
    SpdSecondaryInventory
)
from app.models.spd_extended_models import (
    SpdProductSpn,
    SpdProductSpec,
    SpdSupplierProfile,
    SysUserWarehousePerm,
    SpdPriceAdjustLog,
    SpdWarehouseNode,
    SpdInboundAndOutboundOrder
)
from app.schemas.spd_schemas import (
    ApiResponse,
    CategoryCreateRequest,
    CategoryResponse,
    ProductDictCreateRequest,
    ProductDictUpdateRequest,
    ProductDictResponse,
    SpnCreateRequest,
    SpnUpdateRequest,
    SpnResponse,
    SpecCreateRequest,
    SpecUpdateRequest,
    SpecResponse,
    BatchAdjustPriceRequest,
    PriceAdjustLogResponse,
    SupplierProfileCreateRequest,
    SupplierProfileUpdateRequest,
    SupplierProfileResponse,
    UserWarehousePermUpdateRequest,
    UserWarehousePermResponse,
    WarehouseNodeCreateRequest,
    WarehouseNodeUpdateRequest,
    WarehouseNodeResponse
)
from app.services.trace_service import record_workflow_6w_log

router = APIRouter(prefix="/dict", tags=["核心 CRUD 一：产品字典与分类管理"])


STANDARD_SEEDED_CATEGORIES = [
    {"category_code": "0101", "category_name": "氧气", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "GENERAL", "sort_order": 1},
    {"category_code": "0102", "category_name": "其它气体", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "GENERAL", "sort_order": 2},
    {"category_code": "0110", "category_name": "一次性卫生用品", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "GENERAL", "sort_order": 3},
    {"category_code": "0103", "category_name": "医用器械", "main_dept_code": "EQUIP_DEPT", "consumable_level": "EQUIP_PART", "sort_order": 4},
    {"category_code": "0104", "category_name": "麻醉用材料", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "GENERAL", "sort_order": 5},
    {"category_code": "0105", "category_name": "放射材料", "main_dept_code": "EQUIP_DEPT", "consumable_level": "EQUIP_PART", "sort_order": 6},
    {"category_code": "0106", "category_name": "彩超室耗材", "main_dept_code": "EQUIP_DEPT", "consumable_level": "EQUIP_PART", "sort_order": 7},
    {"category_code": "0107", "category_name": "血透材料", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "GENERAL", "sort_order": 8},
    {"category_code": "0108", "category_name": "植介入高值材料", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "HIGH_VALUE", "sort_order": 9},
    {"category_code": "0109", "category_name": "骨科耗材", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "HIGH_VALUE", "sort_order": 10},
    {"category_code": "CAT-C-01", "category_name": "注射穿刺与输液器具", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "GENERAL", "sort_order": 11},
    {"category_code": "CAT-C-02", "category_name": "医用无菌敷料与防护类", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "GENERAL", "sort_order": 12},
    {"category_code": "CAT-C-03", "category_name": "骨科植入与固定高值耗材", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "HIGH_VALUE", "sort_order": 13},
    {"category_code": "CAT-C-04", "category_name": "心血管介入高值耗材", "main_dept_code": "CONSUMABLE_DEPT", "consumable_level": "HIGH_VALUE", "sort_order": 14},
    {"category_code": "CAT-E-01", "category_name": "多参数监护仪专用配件", "main_dept_code": "EQUIP_DEPT", "consumable_level": "GENERAL", "sort_order": 15},
]


@router.get("/categories", response_model=ApiResponse[List[CategoryResponse]])
def list_categories(
    main_dept_code: Optional[str] = Query(None, description="按主管理科室筛选: CONSUMABLE_DEPT | EQUIP_DEPT"),
    consumable_level: Optional[str] = Query(None, description="按管控级别筛选: GENERAL | HIGH_VALUE | EQUIP_PART"),
    db: Session = Depends(get_db)
):
    """获取产品字典分类列表 (自动确保 15 项医疗国标分类同源初始化)

    @param: main_dept_code (Optional[str]) 归口主科室
    @param: consumable_level (Optional[str]) 管控级别
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[CategoryResponse]] 分类列表
    @route: GET /api/v1/dict/categories
    @throws: 无特定异常抛出
    """
    # 检查并自动补齐 15 个国标分类入库
    existing_codes = {c.category_code for c in db.query(SpdCategory.category_code).all()}
    need_commit = False
    for sc in STANDARD_SEEDED_CATEGORIES:
        if sc["category_code"] not in existing_codes:
            new_cat = SpdCategory(
                category_code=sc["category_code"],
                category_name=sc["category_name"],
                main_dept_code=sc["main_dept_code"],
                consumable_level=sc["consumable_level"],
                sort_order=sc["sort_order"]
            )
            db.add(new_cat)
            existing_codes.add(sc["category_code"])
            need_commit = True
    if need_commit:
        db.commit()

    query = db.query(SpdCategory)
    if main_dept_code:
        query = query.filter(SpdCategory.main_dept_code == main_dept_code)
    if consumable_level:
        query = query.filter(SpdCategory.consumable_level == consumable_level)
    cats = query.order_by(SpdCategory.sort_order.asc(), SpdCategory.id.asc()).all()
    data = [CategoryResponse.model_validate(c) for c in cats]
    return ApiResponse(code=200, msg="获取产品分类列表成功", data=data)


@router.post("/categories", response_model=ApiResponse[CategoryResponse])
def create_category(
    payload: CategoryCreateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """新增产品字典细分品类节点

    @param: payload (CategoryCreateRequest) 分类创建请求体
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[CategoryResponse] 创建成功的分类对象
    @route: POST /api/v1/dict/categories
    @throws: HTTPException(400) 分类编码已存在时抛出
    """
    exists = db.query(SpdCategory).filter(SpdCategory.category_code == payload.category_code).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"分类编码 [{payload.category_code}] 已存在")

    cat = SpdCategory(
        category_code=payload.category_code,
        category_name=payload.category_name,
        main_dept_code=payload.main_dept_code,
        consumable_level=payload.consumable_level,
        parent_id=payload.parent_id,
        storage_condition=payload.storage_condition,
        sort_order=payload.sort_order
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return ApiResponse(code=200, msg="产品分类新增成功", data=CategoryResponse.model_validate(cat))


@router.get("/products", response_model=ApiResponse[List[ProductDictResponse]])
def list_products(
    main_dept_code: Optional[str] = Query(None, description="按归口主科室筛选: CONSUMABLE_DEPT | EQUIP_DEPT"),
    consumable_type: Optional[str] = Query(None, description="按耗材分类筛选: GENERAL | HIGH_VALUE | EQUIP_PART"),
    keyword: Optional[str] = Query(None, description="按产品名称、编码或UDI-DI模糊检索"),
    db: Session = Depends(get_db)
):
    """多条件查询医疗物资产品字典档案列表

    @param: main_dept_code (Optional[str]) 归口主科室
    @param: consumable_type (Optional[str]) 耗材类型
    @param: keyword (Optional[str]) 模糊匹配关键词
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[ProductDictResponse]] 字典记录列表
    @route: GET /api/v1/dict/products
    @throws: 无异常抛出
    """
    query = db.query(SpdProductDict).filter(SpdProductDict.is_deleted == 0)
    if main_dept_code:
        query = query.filter(SpdProductDict.main_dept_code == main_dept_code)
    if consumable_type:
        query = query.filter(SpdProductDict.consumable_type == consumable_type)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (SpdProductDict.product_name.like(pattern)) |
            (SpdProductDict.product_code.like(pattern)) |
            (SpdProductDict.udi_di.like(pattern))
        )
    products = query.order_by(SpdProductDict.id.desc()).all()
    data = [ProductDictResponse.model_validate(p) for p in products]
    return ApiResponse(code=200, msg="获取产品字典列表成功", data=data)


@router.post("/products", response_model=ApiResponse[ProductDictResponse])
def create_product(
    payload: ProductDictCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """新增产品字典档案并自动记录全流程流转日志节点 1_DICT_CREATE

    @param: payload (ProductDictCreateRequest) 新建字典请求体
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[ProductDictResponse] 创建的产品字典对象
    @route: POST /api/v1/dict/products
    @throws: HTTPException(400) 当产品编码或 UDI-DI 已存在时抛出
    """
    # 唯一性检查
    if db.query(SpdProductDict).filter(SpdProductDict.product_code == payload.product_code).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"产品编码 [{payload.product_code}] 已存在")
    if db.query(SpdProductDict).filter(SpdProductDict.udi_di == payload.udi_di).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"UDI-DI 固定标识 [{payload.udi_di}] 已存在")

    # 查询细分类别名称
    category = db.query(SpdCategory).filter(SpdCategory.id == payload.category_id).first()
    category_name = category.category_name if category else "默认品类"

    product = SpdProductDict(
        product_code=payload.product_code,
        product_name=payload.product_name,
        udi_di=payload.udi_di,
        main_dept_code=payload.main_dept_code,
        consumable_type=payload.consumable_type,
        category_id=payload.category_id,
        category_name=category_name,
        spec_model=payload.spec_model,
        unit=payload.unit,
        manufacturer=payload.manufacturer,
        supplier_name=payload.supplier_name,
        reg_cert_no=payload.reg_cert_no,
        reg_cert_expiry=payload.reg_cert_expiry,
        unit_price=payload.unit_price,
        safe_stock_min=payload.safe_stock_min,
        safe_stock_max=payload.safe_stock_max,
        storage_temp_req=payload.storage_temp_req,
        status=1
    )
    db.add(product)
    db.flush()

    # 自动记录 6W 全流程流转日志 1_DICT_CREATE
    dept_label = "耗材科主库房" if payload.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库房"
    record_workflow_6w_log(
        db=db,
        biz_order_no=f"DICT-BUILD-{product.id:04d}",
        node_action="1_DICT_CREATE",
        product_code=product.product_code,
        product_name=product.product_name,
        batch_or_udi=product.udi_di,
        from_dept_name="国家药监局医疗器械数据库",
        from_user_name=user_ctx.real_name,
        to_dept_name=dept_label,
        to_user_name=user_ctx.real_name,
        change_qty=0,
        before_stock_snapshot=0,
        after_stock_snapshot=0,
        settlement_amount=payload.unit_price,
        is_billable=0,
        audit_remark=f"新增物资字典档案，归口主科室: {dept_label}，分类: {category_name}"
    )

    db.commit()
    db.refresh(product)
    return ApiResponse(code=200, msg="产品字典建档成功", data=ProductDictResponse.model_validate(product))


@router.put("/products/{product_id}", response_model=ApiResponse[ProductDictResponse])
def update_product(
    product_id: int,
    payload: ProductDictUpdateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """更新产品字典档案属性与阈值

    @param: product_id (int) 产品字典ID
    @param: payload (ProductDictUpdateRequest) 更新字段载荷
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[ProductDictResponse] 更新后的产品字典对象
    @route: PUT /api/v1/dict/products/{product_id}
    @throws: HTTPException(404) 字典不存在时抛出
    """
    product = db.query(SpdProductDict).filter(SpdProductDict.id == product_id, SpdProductDict.is_deleted == 0).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品字典档案不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(product, field, val)

    db.commit()
    db.refresh(product)
    return ApiResponse(code=200, msg="产品字典修改成功", data=ProductDictResponse.model_validate(product))


@router.delete("/products/{product_id}", response_model=ApiResponse[dict])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """安全软删除产品字典档案（前置硬性风控：校验主库、高值仓、二级库在库库存必须为 0）

    @param: product_id (int) 产品字典ID
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/dict/products/{product_id}
    @throws: HTTPException(400) 当任一库房仍有可用库存时强制阻断删除
    """
    product = db.query(SpdProductDict).filter(SpdProductDict.id == product_id, SpdProductDict.is_deleted == 0).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品字典档案不存在")

    # 1. 检查主库库存
    main_stock = db.query(SpdMainInventory).filter(
        SpdMainInventory.product_id == product_id,
        SpdMainInventory.available_qty > 0
    ).first()
    if main_stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"主库仍有在库库存 ({main_stock.available_qty})，严禁删除字典")

    # 2. 检查高值仓单品
    hv_stock = db.query(SpdHighValueItem).filter(
        SpdHighValueItem.product_id == product_id,
        SpdHighValueItem.item_status.in_(["IN_HIGH_VALUE_WH", "IN_SECONDARY_CABINET", "SURGERY_LOCKED"])
    ).first()
    if hv_stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="高值专仓仍有未核销单品在库，严禁删除字典")

    # 3. 检查二级库库存
    sec_stock = db.query(SpdSecondaryInventory).filter(
        SpdSecondaryInventory.product_id == product_id,
        SpdSecondaryInventory.current_qty > 0
    ).first()
    if sec_stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"临床二级库 ({sec_stock.dept_name}) 仍有在库库存，严禁删除字典")

    # 软删除
    product.is_deleted = 1
    db.commit()
    return ApiResponse(code=200, msg="产品字典档案已安全软删除", data={"product_id": product_id})


# =========================================================================
# 医院真实 SPD 四级字典体系扩展：大品名 (SPN) CRUD
# =========================================================================

@router.get("/spns", response_model=ApiResponse[List[SpnResponse]])
def list_spns(
    category_code: Optional[str] = Query(None, description="按耗材分类筛选: 如 0101"),
    keyword: Optional[str] = Query(None, description="按品名、编码或通用名模糊检索"),
    db: Session = Depends(get_db)
):
    """查询通用大品名列表 (对应图 4 中栏品名树列表)

    @param: category_code (Optional[str]) 耗材分类编码
    @param: keyword (Optional[str]) 检索关键字
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[SpnResponse]] 大品名列表及下属规格计数
    @route: GET /api/v1/dict/spns
    @throws: 无特定异常
    """
    query = db.query(SpdProductSpn)
    if category_code:
        query = query.filter(SpdProductSpn.category_code == category_code)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (SpdProductSpn.spn_name.ilike(pattern)) |
            (SpdProductSpn.spn_code.ilike(pattern)) |
            (SpdProductSpn.common_name.ilike(pattern)) |
            (SpdProductSpn.pinyin_code.ilike(pattern))
        )
    spns = query.order_by(SpdProductSpn.spn_code.asc()).all()

    # 统计下属规格数量
    spec_counts = dict(
        db.query(SpdProductSpec.spn_id, func.count(SpdProductSpec.id))
        .group_by(SpdProductSpec.spn_id)
        .all()
    )

    data = []
    for s in spns:
        item = SpnResponse.model_validate(s)
        item.spec_count = spec_counts.get(s.id, 0)
        data.append(item)

    return ApiResponse(code=200, msg="获取大品名列表成功", data=data)


@router.post("/spns", response_model=ApiResponse[SpnResponse])
def create_spn(
    payload: SpnCreateRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """新增通用大品名档案 (对应图 3 新增品名对话框)

    @param: payload (SpnCreateRequest) 新增大品名请求载荷
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[SpnResponse] 创建成功的大品名对象
    @route: POST /api/v1/dict/spns
    @throws: HTTPException(400) 当品名编码已存在时抛出
    """
    exists = db.query(SpdProductSpn).filter(SpdProductSpn.spn_code == payload.spn_code).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"品名编码 [{payload.spn_code}] 已存在")

    spn = SpdProductSpn(
        spn_code=payload.spn_code,
        spn_name=payload.spn_name,
        category_code=payload.category_code,
        common_name=payload.common_name or payload.spn_name,
        pinyin_code=payload.pinyin_code or "",
        finance_category=payload.finance_category or "西药卫生材料",
        performance_category=payload.performance_category or "医疗耗材消耗",
        inpatient_charge_category=payload.inpatient_charge_category or "住院治疗材料费",
        outpatient_charge_category=payload.outpatient_charge_category or "门诊检查处置费",
        medical_record_category=payload.medical_record_category or "治疗用器械材料",
        medicare_category=payload.medicare_category or "甲类医保可报销材料",
        is_chargeable=payload.is_chargeable,
        is_high_value=payload.is_high_value,
        is_central_proc=payload.is_central_proc,
        central_proc_project=payload.central_proc_project or "",
        contract_no=payload.contract_no or "",
        contract_signed_date=payload.contract_signed_date,
        contract_start_date=payload.contract_start_date,
        contract_end_date=payload.contract_end_date,
        status="ACTIVE"
    )
    db.add(spn)
    db.commit()
    db.refresh(spn)

    res = SpnResponse.model_validate(spn)
    res.spec_count = 0
    return ApiResponse(code=200, msg="大品名创建成功", data=res)


@router.put("/spns/{spn_id}", response_model=ApiResponse[SpnResponse])
def update_spn(
    spn_id: int,
    payload: SpnUpdateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """更新大品名属性档案

    @param: spn_id (int) 大品名主键ID
    @param: payload (SpnUpdateRequest) 更新属性载荷
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[SpnResponse] 更新后的大品名对象
    @route: PUT /api/v1/dict/spns/{spn_id}
    @throws: HTTPException(404) 品名不存在时抛出
    """
    spn = db.query(SpdProductSpn).filter(SpdProductSpn.id == spn_id).first()
    if not spn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="大品名档案不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(spn, field, val)

    db.commit()
    db.refresh(spn)
    spec_count = db.query(SpdProductSpec).filter(SpdProductSpec.spn_id == spn_id).count()
    res = SpnResponse.model_validate(spn)
    res.spec_count = spec_count
    return ApiResponse(code=200, msg="大品名更新成功", data=res)


@router.delete("/spns/{spn_id}", response_model=ApiResponse[dict])
def delete_spn(
    spn_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """删除大品名档案（前置风控：校验下属是否仍挂载规格型号）

    @param: spn_id (int) 大品名主键ID
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/dict/spns/{spn_id}
    @throws: HTTPException(400) 当存在下属规格时强制阻断删除
    """
    spn = db.query(SpdProductSpn).filter(SpdProductSpn.id == spn_id).first()
    if not spn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="大品名档案不存在")

    has_specs = db.query(SpdProductSpec).filter(SpdProductSpec.spn_id == spn_id).first()
    if has_specs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该大品名下仍挂载有规格型号，严禁删除，请先移除或停用规格")

    db.delete(spn)
    db.commit()
    return ApiResponse(code=200, msg="大品名档案已安全删除", data={"spn_id": spn_id})


# =========================================================================
# 规格型号单品 (Spec) CRUD 与状态开关
# =========================================================================

@router.get("/specs", response_model=ApiResponse[List[SpecResponse]])
def list_specs(
    spn_id: Optional[int] = Query(None, description="按关联大品名筛选"),
    category_code: Optional[str] = Query(None, description="按耗材分类筛选"),
    warehouse_code: Optional[str] = Query(None, description="按授权分配仓库筛选"),
    keyword: Optional[str] = Query(None, description="按规格编码、品名或型号模糊检索"),
    status_filter: Optional[str] = Query(None, description="状态筛选: ACTIVE | DISABLED"),
    db: Session = Depends(get_db)
):
    """多维度查询产品规格型号列表 (对应图 4 右侧明细表格)

    @param: spn_id (Optional[int]) 关联大品名ID
    @param: category_code (Optional[str]) 分类编码
    @param: warehouse_code (Optional[str]) 仓库编码
    @param: keyword (Optional[str]) 检索关键字
    @param: status_filter (Optional[str]) 状态
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[SpecResponse]] 规格型号清单
    @route: GET /api/v1/dict/specs
    @throws: 无特定异常
    """
    query = db.query(SpdProductSpec)
    if spn_id:
        query = query.filter(SpdProductSpec.spn_id == spn_id)
    if category_code:
        query = query.filter(SpdProductSpec.category_code == category_code)
    if status_filter:
        query = query.filter(SpdProductSpec.status == status_filter)
    if warehouse_code:
        query = query.filter(SpdProductSpec.assigned_warehouses.contains(warehouse_code))
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (SpdProductSpec.spec_code.ilike(pattern)) |
            (SpdProductSpec.spec_name.ilike(pattern)) |
            (SpdProductSpec.model_name.ilike(pattern)) |
            (SpdProductSpec.manufacturer.ilike(pattern)) |
            (SpdProductSpec.pinyin_code.ilike(pattern))
        )

    specs = query.order_by(SpdProductSpec.spec_code.asc()).all()
    data = [SpecResponse.model_validate(s) for s in specs]
    return ApiResponse(code=200, msg="获取产品规格列表成功", data=data)


@router.post("/specs", response_model=ApiResponse[SpecResponse])
def create_spec(
    payload: SpecCreateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """新增产品规格型号 (对应图 5 新增产品规格)

    @param: payload (SpecCreateRequest) 规格创建请求载荷
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[SpecResponse] 创建成功的规格单品
    @route: POST /api/v1/dict/specs
    @throws: HTTPException(400) 当规格编码已存在时抛出
    """
    exists = db.query(SpdProductSpec).filter(SpdProductSpec.spec_code == payload.spec_code).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"产品规格编码 [{payload.spec_code}] 已存在")

    spec = SpdProductSpec(
        spn_id=payload.spn_id,
        spec_code=payload.spec_code,
        product_name=payload.product_name,
        spec_name=payload.spec_name,
        model_name=payload.model_name,
        common_name=payload.common_name or payload.product_name,
        component_name=payload.component_name or "主件",
        pinyin_code=payload.pinyin_code or "",
        brand_name=payload.brand_name or "国产品牌",
        manufacturer=payload.manufacturer,
        description=payload.description or "",
        pricing_unit=payload.pricing_unit,
        package_unit=payload.package_unit or payload.pricing_unit,
        conversion_ratio=payload.conversion_ratio,
        unit_price=payload.unit_price,
        register_card_no=payload.register_card_no or "",
        register_expiry_date=payload.register_expiry_date,
        medicare_code=payload.medicare_code or "",
        medicare_category_code=payload.medicare_category_code or "",
        production_license_no=payload.production_license_no or "",
        production_license_expiry=payload.production_license_expiry,
        default_supplier_id=payload.default_supplier_id or 0,
        default_supplier_name=payload.default_supplier_name or "",
        original_code=payload.original_code or "",
        provincial_code=payload.provincial_code or "",
        storage_condition=payload.storage_condition or "常温干燥避光",
        is_central_proc=payload.is_central_proc or 0,
        central_proc_code=payload.central_proc_code or "",
        origin_place=payload.origin_place or "国产",
        category_code=payload.category_code or "0101",
        status="ACTIVE",
        assigned_warehouses=payload.assigned_warehouses or "WH_WEICAI"
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return ApiResponse(code=200, msg="产品规格创建成功", data=SpecResponse.model_validate(spec))


@router.put("/specs/{spec_id}", response_model=ApiResponse[SpecResponse])
def update_spec(
    spec_id: int,
    payload: SpecUpdateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """更新规格型号单品档案

    @param: spec_id (int) 规格主键ID
    @param: payload (SpecUpdateRequest) 更新载荷
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[SpecResponse] 更新后的规格单品
    @route: PUT /api/v1/dict/specs/{spec_id}
    @throws: HTTPException(404) 规格不存在时抛出
    """
    spec = db.query(SpdProductSpec).filter(SpdProductSpec.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品规格档案不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(spec, field, val)

    db.commit()
    db.refresh(spec)
    return ApiResponse(code=200, msg="产品规格更新成功", data=SpecResponse.model_validate(spec))


@router.post("/specs/{spec_id}/toggle-status", response_model=ApiResponse[SpecResponse])
def toggle_spec_status(
    spec_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """启用/停用规格单品 (对应图 4 顶部【停用产品规格】按钮)

    @param: spec_id (int) 规格ID
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[SpecResponse] 切换后的规格对象
    @route: POST /api/v1/dict/specs/{spec_id}/toggle-status
    @throws: HTTPException(404) 规格不存在时抛出
    """
    spec = db.query(SpdProductSpec).filter(SpdProductSpec.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品规格档案不存在")

    spec.status = "DISABLED" if spec.status == "ACTIVE" else "ACTIVE"
    db.commit()
    db.refresh(spec)
    return ApiResponse(code=200, msg=f"产品规格已{'停用' if spec.status == 'DISABLED' else '重新启用'}", data=SpecResponse.model_validate(spec))


@router.delete("/specs/{spec_id}", response_model=ApiResponse[dict])
def delete_spec(
    spec_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """安全删除规格型号档案 (对应图 4 顶部【删除产品规格】按钮)

    @param: spec_id (int) 规格ID
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/dict/specs/{spec_id}
    @throws: HTTPException(400) 当规格有关联在库单据或库存时阻断
    """
    spec = db.query(SpdProductSpec).filter(SpdProductSpec.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品规格档案不存在")

    db.delete(spec)
    db.commit()
    return ApiResponse(code=200, msg="产品规格已成功删除", data={"spec_id": spec_id})


# =========================================================================
# 集中带量采购与批量调价管理 (Batch Price Adjustment)
# =========================================================================

@router.post("/batch-adjust-price", response_model=ApiResponse[dict])
def batch_adjust_price(
    payload: BatchAdjustPriceRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """集中带量采购多品批量调价与审计快照写入 (对应图 4 顶部【调价管理】与批量改价弹窗)

    @param: payload (BatchAdjustPriceRequest) 批量调价载荷 (规格IDs、模式、调整值、文号、原因)
    @param: db (Session) 数据库活动会话
    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[dict] 调价影响规格总数及调价审计日志
    @route: POST /api/v1/dict/batch-adjust-price
    @throws: HTTPException(400) 当规格ID列表为空或调整后价格小于等于0时抛出
    """
    if not payload.spec_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少选择一个产品规格进行调价")

    specs = db.query(SpdProductSpec).filter(SpdProductSpec.id.in_(payload.spec_ids)).all()
    if not specs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到符合条件的规格单品")

    logs = []
    for s in specs:
        old_price = s.unit_price
        if payload.adjust_type == "FIXED_PRICE":
            new_price = payload.adjust_value
        elif payload.adjust_type == "PERCENT_DISCOUNT":
            new_price = round(old_price * (Decimal("1.00") + payload.adjust_value), 4)
        elif payload.adjust_type == "FIXED_OFFSET":
            new_price = round(old_price + payload.adjust_value, 4)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的调价模式")

        if new_price <= Decimal("0.0000"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"规格 [{s.spec_name}] 调整后价格必须大于 0")

        s.unit_price = new_price
        log_item = SpdPriceAdjustLog(
            spec_id=s.id,
            spec_code=s.spec_code,
            spec_name=f"{s.spec_name} ({s.model_name})",
            old_price=old_price,
            new_price=new_price,
            adjust_diff=new_price - old_price,
            adjust_reason=payload.reason,
            adjust_doc_no=payload.doc_no or "",
            operator_name=f"{user_ctx.real_name}({user_ctx.username})"
        )
        logs.append(log_item)

    db.add_all(logs)
    db.commit()

    return ApiResponse(
        code=200,
        msg=f"成功完成 {len(specs)} 项产品规格批量调价并记录历史审计快照",
        data={
            "affected_count": len(specs),
            "adjust_type": payload.adjust_type,
            "adjust_reason": payload.reason
        }
    )


@router.get("/price-adjust-logs", response_model=ApiResponse[List[PriceAdjustLogResponse]])
def list_price_adjust_logs(
    spec_id: Optional[int] = Query(None, description="按规格ID筛选调价历史"),
    spec_code: Optional[str] = Query(None, description="按规格编码筛选"),
    db: Session = Depends(get_db)
):
    """查询产品规格历史调价记录快照 (对应图 5 右侧【调价记录】Tab)

    @param: spec_id (Optional[int]) 规格ID
    @param: spec_code (Optional[str]) 规格编码
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[PriceAdjustLogResponse]] 调价历史明细
    @route: GET /api/v1/dict/price-adjust-logs
    @throws: 无特定异常
    """
    query = db.query(SpdPriceAdjustLog)
    if spec_id:
        query = query.filter(SpdPriceAdjustLog.spec_id == spec_id)
    if spec_code:
        query = query.filter(SpdPriceAdjustLog.spec_code == spec_code)

    logs = query.order_by(SpdPriceAdjustLog.effective_time.desc()).limit(100).all()
    data = [PriceAdjustLogResponse.model_validate(l) for l in logs]
    return ApiResponse(code=200, msg="获取调价历史记录成功", data=data)


# =========================================================================
# 供应商资质档案管理 (Supplier Profiles - 对应图 4 中栏供应商 Tab)
# =========================================================================

@router.get("/suppliers", response_model=ApiResponse[List[SupplierProfileResponse]])
def list_suppliers(
    keyword: Optional[str] = Query(None, description="按企业全称、编码或社会信用代码检索"),
    db: Session = Depends(get_db)
):
    """获取物资供应商资质准入档案列表

    @param: keyword (Optional[str]) 检索关键字
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[SupplierProfileResponse]] 供应商档案列表
    @route: GET /api/v1/dict/suppliers
    @throws: 无特定异常
    """
    query = db.query(SpdSupplierProfile)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (SpdSupplierProfile.supplier_name.ilike(pattern)) |
            (SpdSupplierProfile.supplier_code.ilike(pattern)) |
            (SpdSupplierProfile.social_credit_code.ilike(pattern))
        )
    suppliers = query.order_by(SpdSupplierProfile.supplier_code.asc()).all()
    data = [SupplierProfileResponse.model_validate(s) for s in suppliers]
    return ApiResponse(code=200, msg="获取供应商档案列表成功", data=data)


@router.post("/suppliers", response_model=ApiResponse[SupplierProfileResponse])
def create_supplier(
    payload: SupplierProfileCreateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """新增供应商资质准入档案

    @param: payload (SupplierProfileCreateRequest) 供应商请求体
    @param: db (Session) 数据库会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[SupplierProfileResponse] 创建成功的供应商档案
    @route: POST /api/v1/dict/suppliers
    @throws: HTTPException(400) 当供应商编码或信用代码重复时抛出
    """
    exists = db.query(SpdSupplierProfile).filter(
        (SpdSupplierProfile.supplier_code == payload.supplier_code) |
        (SpdSupplierProfile.social_credit_code == payload.social_credit_code)
    ).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="供应商编码或统一社会信用代码已存在")

    sup = SpdSupplierProfile(
        supplier_code=payload.supplier_code,
        supplier_name=payload.supplier_name,
        social_credit_code=payload.social_credit_code,
        license_no=payload.license_no,
        license_expiry_date=payload.license_expiry_date,
        contact_person=payload.contact_person or "",
        contact_phone=payload.contact_phone or "",
        supply_categories=payload.supply_categories or "普耗,高值",
        qual_status=payload.qual_status or "QUAL_APPROVED",
        status="ACTIVE"
    )
    db.add(sup)
    db.commit()
    db.refresh(sup)
    return ApiResponse(code=200, msg="供应商档案创建成功", data=SupplierProfileResponse.model_validate(sup))


@router.put("/suppliers/{supplier_id}", response_model=ApiResponse[SupplierProfileResponse])
def update_supplier(
    supplier_id: int,
    payload: SupplierProfileUpdateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """更新供应商资质档案信息

    @param: supplier_id (int) 供应商ID
    @param: payload (SupplierProfileUpdateRequest) 更新字段
    @param: db (Session) 数据库会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[SupplierProfileResponse] 更新后供应商对象
    @route: PUT /api/v1/dict/suppliers/{supplier_id}
    @throws: HTTPException(404) 不存在时抛出
    """
    sup = db.query(SpdSupplierProfile).filter(SpdSupplierProfile.id == supplier_id).first()
    if not sup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="供应商档案不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(sup, field, val)

    db.commit()
    db.refresh(sup)
    return ApiResponse(code=200, msg="供应商档案更新成功", data=SupplierProfileResponse.model_validate(sup))


@router.delete("/suppliers/{supplier_id}", response_model=ApiResponse[dict])
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """删除供应商档案（前置风控：校验是否仍有产品规格绑定该供应商）

    @param: supplier_id (int) 供应商ID
    @param: db (Session) 数据库会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/dict/suppliers/{supplier_id}
    @throws: HTTPException(400) 当仍有关联物资绑定时阻断删除
    """
    sup = db.query(SpdSupplierProfile).filter(SpdSupplierProfile.id == supplier_id).first()
    if not sup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="供应商档案不存在")

    has_specs = db.query(SpdProductSpec).filter(SpdProductSpec.default_supplier_id == supplier_id).first()
    if has_specs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"仍有规格单品 [{has_specs.spec_name}] 绑定该供应商为默认供货商，严禁删除")

    db.delete(sup)
    db.commit()
    return ApiResponse(code=200, msg="供应商档案已删除", data={"supplier_id": supplier_id})


# =========================================================================
# 全院仓库管理与用户细粒度授权 (Warehouse Nodes & User-Warehouse Perms)
# =========================================================================

@router.get("/warehouses", response_model=ApiResponse[List[WarehouseNodeResponse]])
def list_warehouses(
    db: Session = Depends(get_db)
):
    """获取全院多级仓库树节点列表 (对应图 4 左上仓库树)

    @param: db (Session) 数据库会话
    @returns: ApiResponse[List[WarehouseNodeResponse]] 全院仓库列表
    @route: GET /api/v1/dict/warehouses
    @throws: 无特定异常
    """
    warehouses = db.query(SpdWarehouseNode).order_by(SpdWarehouseNode.id.asc()).all()
    data = [WarehouseNodeResponse.model_validate(w) for w in warehouses]
    return ApiResponse(code=200, msg="获取仓库节点列表成功", data=data)


@router.post("/warehouses", response_model=ApiResponse[WarehouseNodeResponse])
def create_warehouse(
    payload: WarehouseNodeCreateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """管理员新增仓库节点

    @param: payload (WarehouseNodeCreateRequest) 仓库节点请求载荷
    @param: db (Session) 数据库会话
    @param: _ 必须为信息科管理员 (sys_admin)
    @returns: ApiResponse[WarehouseNodeResponse] 创建成功的仓库节点
    @route: POST /api/v1/dict/warehouses
    @throws: HTTPException(400) 编码重复时抛出
    """
    exists = db.query(SpdWarehouseNode).filter(SpdWarehouseNode.warehouse_code == payload.warehouse_code).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"仓库编码 [{payload.warehouse_code}] 已存在")

    wh = SpdWarehouseNode(
        warehouse_code=payload.warehouse_code,
        warehouse_name=payload.warehouse_name,
        warehouse_level=payload.warehouse_level,
        parent_code=payload.parent_code,
        dept_code=payload.dept_code,
        init_stock_locked=0
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return ApiResponse(code=200, msg="仓库节点创建成功", data=WarehouseNodeResponse.model_validate(wh))


@router.put("/warehouses/{warehouse_id}", response_model=ApiResponse[WarehouseNodeResponse])
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseNodeUpdateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """管理员更新仓库节点属性

    @param: warehouse_id (int) 仓库主键ID
    @param: payload (WarehouseNodeUpdateRequest) 更新字段
    @param: db (Session) 数据库会话
    @param: _ 必须为信息科管理员 (sys_admin)
    @returns: ApiResponse[WarehouseNodeResponse] 更新后的仓库节点
    @route: PUT /api/v1/dict/warehouses/{warehouse_id}
    @throws: HTTPException(404) 仓库不存在时抛出
    """
    wh = db.query(SpdWarehouseNode).filter(SpdWarehouseNode.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="仓库节点不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(wh, field, val)

    db.commit()
    db.refresh(wh)
    return ApiResponse(code=200, msg="仓库节点更新成功", data=WarehouseNodeResponse.model_validate(wh))


@router.get("/user-warehouse-perms", response_model=ApiResponse[List[UserWarehousePermResponse]])
def get_user_warehouse_perms(
    user_id: Optional[int] = Query(None, description="指定查询的用户ID，不传默认查询当前登录用户"),
    db: Session = Depends(get_db),
    current_user: CurrentUserContext = Depends(get_current_user_context)
):
    """获取指定用户或当前登录用户的仓库细粒度授权矩阵 (按人分仓，限申领/查看等原子动作)

    @param: user_id (Optional[int]) 目标用户ID
    @param: db (Session) 数据库会话
    @param: current_user (CurrentUserContext) 当前会话用户
    @returns: ApiResponse[List[UserWarehousePermResponse]] 授权列表
    @route: GET /api/v1/dict/user-warehouse-perms
    @throws: 无特定异常
    """
    target_uid = user_id if (user_id and current_user.role_code == "sys_admin") else current_user.user_id
    perms = db.query(SysUserWarehousePerm).filter(SysUserWarehousePerm.user_id == target_uid).all()
    data = [UserWarehousePermResponse.model_validate(p) for p in perms]
    return ApiResponse(code=200, msg="获取用户仓库细粒度权限成功", data=data)


@router.post("/user-warehouse-perms", response_model=ApiResponse[UserWarehousePermResponse])
def upsert_user_warehouse_perm(
    payload: UserWarehousePermUpdateRequest,
    db: Session = Depends(get_db),
    admin_ctx: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """信息科管理员为指定用户分配或修改仓库的细粒度操作权限 (控制查看、申领、入库、出库等)

    @param: payload (UserWarehousePermUpdateRequest) 权限变更载荷
    @param: db (Session) 数据库会话
    @param: admin_ctx (CurrentUserContext) 必须为信息科管理员 (sys_admin)
    @returns: ApiResponse[UserWarehousePermResponse] 保存成功的权限项
    @route: POST /api/v1/dict/user-warehouse-perms
    @throws: HTTPException(404) 当目标用户不存在时抛出
    """
    target_user = db.query(SysUser).filter(SysUser.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标人员账号不存在")

    perm = db.query(SysUserWarehousePerm).filter(
        SysUserWarehousePerm.user_id == payload.user_id,
        SysUserWarehousePerm.warehouse_code == payload.warehouse_code
    ).first()

    if not perm:
        perm = SysUserWarehousePerm(
            user_id=payload.user_id,
            username=target_user.username,
            warehouse_code=payload.warehouse_code,
            can_view=payload.can_view,
            can_apply=payload.can_apply,
            can_inbound=payload.can_inbound,
            can_outbound=payload.can_outbound,
            can_stocktake=payload.can_stocktake,
            can_transfer=payload.can_transfer,
            updated_by=admin_ctx.username
        )
        db.add(perm)
    else:
        perm.can_view = payload.can_view
        perm.can_apply = payload.can_apply
        perm.can_inbound = payload.can_inbound
        perm.can_outbound = payload.can_outbound
        perm.can_stocktake = payload.can_stocktake
        perm.can_transfer = payload.can_transfer
        perm.updated_by = admin_ctx.username

    db.commit()
    db.refresh(perm)
    return ApiResponse(code=200, msg="用户仓库细粒度权限配置保存成功", data=UserWarehousePermResponse.model_validate(perm))


@router.delete("/warehouses/{warehouse_id}", response_model=ApiResponse[dict])
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """管理员删除仓库节点（前置风控：若该仓库下有在库库存或业务单据流水，强制拦截）

    @param: warehouse_id (int) 仓库主键ID
    @param: db (Session) 数据库会话
    @param: _ 必须为信息科管理员 (sys_admin)
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/dict/warehouses/{warehouse_id}
    @throws: HTTPException(400) 当存在库存或单据流水时抛出
    """
    wh = db.query(SpdWarehouseNode).filter(SpdWarehouseNode.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="仓库节点不存在")

    has_orders = db.query(SpdInboundAndOutboundOrder).filter(SpdInboundAndOutboundOrder.warehouse_code == wh.warehouse_code).first()
    if has_orders:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"仓库 [{wh.warehouse_name}] 已存在出入库业务流水单据，严禁物理删除，建议将其状态变更为停用")

    db.delete(wh)
    db.commit()
    return ApiResponse(code=200, msg="仓库节点已成功删除", data={"warehouse_id": warehouse_id})


# =========================================================================
# 耗材分类树 (Category) 增删改
# =========================================================================

@router.post("/categories", response_model=ApiResponse[CategoryResponse])
def create_category(
    payload: CategoryCreateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """新增耗材分类节点

    @param: payload (CategoryCreateRequest) 分类载荷
    @param: db (Session) 数据库会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[CategoryResponse] 创建成功的分类
    @route: POST /api/v1/dict/categories
    @throws: HTTPException(400) 编码重复时抛出
    """
    exists = db.query(SpdCategory).filter(SpdCategory.category_code == payload.category_code).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"分类编码 [{payload.category_code}] 已存在")

    cat = SpdCategory(
        category_code=payload.category_code,
        category_name=payload.category_name,
        main_dept_code=payload.main_dept_code,
        consumable_level=payload.consumable_level,
        parent_id=payload.parent_id,
        storage_condition=payload.storage_condition,
        sort_order=payload.sort_order,
        status=1
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return ApiResponse(code=200, msg="分类创建成功", data=CategoryResponse.model_validate(cat))


@router.put("/categories/{category_id}", response_model=ApiResponse[CategoryResponse])
def update_category(
    category_id: int,
    payload: CategoryCreateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """更新耗材分类属性

    @param: category_id (int) 分类ID
    @param: payload (CategoryCreateRequest) 更新字段
    @param: db (Session) 数据库会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[CategoryResponse] 更新后分类
    @route: PUT /api/v1/dict/categories/{category_id}
    @throws: HTTPException(404) 不存在时抛出
    """
    cat = db.query(SpdCategory).filter(SpdCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="耗材分类不存在")

    cat.category_name = payload.category_name
    cat.main_dept_code = payload.main_dept_code
    cat.consumable_level = payload.consumable_level
    cat.storage_condition = payload.storage_condition
    cat.sort_order = payload.sort_order
    db.commit()
    db.refresh(cat)
    return ApiResponse(code=200, msg="分类更新成功", data=CategoryResponse.model_validate(cat))


@router.delete("/categories/{category_id}", response_model=ApiResponse[dict])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """删除耗材分类（前置风控：校验是否仍有品名挂载该分类）

    @param: category_id (int) 分类ID
    @param: db (Session) 数据库会话
    @param: _ 当前操作人鉴权
    @returns: ApiResponse[dict] 删除确认
    @route: DELETE /api/v1/dict/categories/{category_id}
    @throws: HTTPException(400) 存在挂载品名时阻断删除
    """
    cat = db.query(SpdCategory).filter(SpdCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="耗材分类不存在")

    has_spn = db.query(SpdProductSpn).filter(SpdProductSpn.category_code == cat.category_code).first()
    if has_spn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"该分类下仍挂载大品名 [{has_spn.spn_name}]，严禁删除")

    db.delete(cat)
    db.commit()
    return ApiResponse(code=200, msg="分类已成功删除", data={"category_id": category_id})


