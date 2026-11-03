"""医院真实业务场景种子数据幂等初始化服务模块

本模块负责在系统首次启动或数据库重置时注入完备的基础科室、三级角色账号、双维产品分类与字典、主库批次库存及初始 6W 流转日志。
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, mask_phone
from app.models.spd_models import (
    SysDepartment,
    SysUser,
    SpdCategory,
    SpdProductDict,
    SpdMainInventory,
    SpdHighValueItem,
    SpdSecondaryInventory,
    SpdRequisitionOrder,
    SpdWorkflowLog
)
from app.models.spd_extended_models import (
    SysUserModulePermission,
    SpdWarehouseNode,
    SpdProductDictExt,
    SpdInboundAndOutboundOrder,
    SpdStocktakeAndTransferOrder,
    SpdHighValueLifecycleOrder,
    SpdSupplierAndPurchaseOrder,
    SpdProductSpn,
    SpdProductSpec,
    SpdSupplierProfile,
    SysUserWarehousePerm,
    SpdPriceAdjustLog
)
from app.services.rbac_and_confirm_service import generate_pinyin_abbr

logger = logging.getLogger("spd.seed")


def init_seed_data(db: Session) -> bool:
    """幂等初始化医院真实业务场景全套种子数据

    @param: db (Session) 数据库活动会话
    @returns: (bool) True 表示注入了新种子数据，False 表示数据库已存在数据跳过注入
    @route: 内部服务链路 backend.app.services.seed_service.init_seed_data
    @throws: 写入发生冲突或异常时向外抛出并在上层回滚
    """
    # 检查是否已存在科室数据
    if db.query(SysDepartment).count() > 0:
        logger.info("数据库已存在基础10表数据，继续校验深度扩展7表种子数据...")
        init_extended_seed_data(db)
        init_spn_spec_and_rbac_seeds(db)
        return False

    logger.info("开始执行医院真实业务场景种子数据幂等初始化...")

    # 1. 初始化 6 大核心科室与库房
    depts = [
        SysDepartment(
            dept_code="INFO_DEPT",
            dept_name="信息科",
            dept_type="SYS_ADMIN",
            warehouse_zone="行政楼2层信息机房",
            contact_person="赵振华",
            contact_phone="13900000001",
            status=1
        ),
        SysDepartment(
            dept_code="CONSUMABLE_DEPT",
            dept_name="耗材科主库房",
            dept_type="MAIN_WAREHOUSE",
            warehouse_zone="中心库区地下1层耗材主库A区/高值专仓",
            contact_person="王建国",
            contact_phone="13900000002",
            status=1
        ),
        SysDepartment(
            dept_code="EQUIP_DEPT",
            dept_name="设备科主库房",
            dept_type="MAIN_WAREHOUSE",
            warehouse_zone="中心库区地下1层设备配件库B区",
            contact_person="周天海",
            contact_phone="13900000003",
            status=1
        ),
        SysDepartment(
            dept_code="FINANCE_DEPT",
            dept_name="财务科",
            dept_type="FINANCE",
            warehouse_zone="行政楼3层财务审计中心",
            contact_person="孙丽娟",
            contact_phone="13900000004",
            status=1
        ),
        SysDepartment(
            dept_code="SEC_ORTHO",
            dept_name="骨科病区二级库",
            dept_type="SECONDARY_WAREHOUSE",
            warehouse_zone="住院部外科大楼5楼骨科护理站库房",
            contact_person="李晓琳",
            contact_phone="13900000005",
            status=1
        ),
        SysDepartment(
            dept_code="SEC_CARDIO",
            dept_name="心内科病区二级库",
            dept_type="SECONDARY_WAREHOUSE",
            warehouse_zone="住院部内科大楼7楼心内科介入导管室库房",
            contact_person="陈雅文",
            contact_phone="13900000006",
            status=1
        )
    ]
    db.add_all(depts)
    db.flush()

    # 2. 初始化三级角色代表账号 (默认密码均为 123456)
    default_pwd_hash = get_password_hash("123456")
    users = [
        SysUser(
            username="admin",
            password_hash=default_pwd_hash,
            real_name="赵振华",
            role_code="sys_admin",
            dept_id=depts[0].id,
            dept_code=depts[0].dept_code,
            phone_masked=mask_phone("13900000001"),
            status=1
        ),
        SysUser(
            username="mgr_consumable",
            password_hash=default_pwd_hash,
            real_name="王建国",
            role_code="dept_manager",
            dept_id=depts[1].id,
            dept_code=depts[1].dept_code,
            phone_masked=mask_phone("13900000002"),
            status=1
        ),
        SysUser(
            username="mgr_equip",
            password_hash=default_pwd_hash,
            real_name="周天海",
            role_code="dept_manager",
            dept_id=depts[2].id,
            dept_code=depts[2].dept_code,
            phone_masked=mask_phone("13900000003"),
            status=1
        ),
        SysUser(
            username="mgr_finance",
            password_hash=default_pwd_hash,
            real_name="孙丽娟",
            role_code="dept_manager",
            dept_id=depts[3].id,
            dept_code=depts[3].dept_code,
            phone_masked=mask_phone("13900000004"),
            status=1
        ),
        SysUser(
            username="nurse_ortho",
            password_hash=default_pwd_hash,
            real_name="李晓琳",
            role_code="secondary_user",
            dept_id=depts[4].id,
            dept_code=depts[4].dept_code,
            phone_masked=mask_phone("13900000005"),
            status=1
        ),
        SysUser(
            username="nurse_cardio",
            password_hash=default_pwd_hash,
            real_name="陈雅文",
            role_code="secondary_user",
            dept_id=depts[5].id,
            dept_code=depts[5].dept_code,
            phone_masked=mask_phone("13900000006"),
            status=1
        )
    ]
    db.add_all(users)
    db.flush()

    # 3. 初始化双维产品分类体系
    categories = [
        SpdCategory(
            category_code="CAT-C-01",
            category_name="注射穿刺与输液器具",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_level="GENERAL",
            storage_condition="常温干燥",
            sort_order=1
        ),
        SpdCategory(
            category_code="CAT-C-02",
            category_name="医用无菌敷料与防护类",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_level="GENERAL",
            storage_condition="常温干燥",
            sort_order=2
        ),
        SpdCategory(
            category_code="CAT-C-03",
            category_name="骨科植入与固定高值耗材",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_level="HIGH_VALUE",
            storage_condition="避光常温干燥",
            sort_order=3
        ),
        SpdCategory(
            category_code="CAT-C-04",
            category_name="心血管介入高值耗材",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_level="HIGH_VALUE",
            storage_condition="避光阴凉",
            sort_order=4
        ),
        SpdCategory(
            category_code="CAT-E-01",
            category_name="多参数监护仪专用备件",
            main_dept_code="EQUIP_DEPT",
            consumable_level="EQUIP_PART",
            storage_condition="防静电常温干燥",
            sort_order=5
        )
    ]
    db.add_all(categories)
    db.flush()

    # 4. 初始化产品字典档案
    products = [
        SpdProductDict(
            product_code="PROD-GEN-001",
            product_name="一次性使用无菌注射器带针 5ml",
            udi_di="06971234560014",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="GENERAL",
            category_id=categories[0].id,
            category_name=categories[0].category_name,
            spec_model="5ml 带针 0.7*30mm TWLB",
            unit="支",
            manufacturer="山东威高集团医用高分子制品股份有限公司",
            supplier_name="国药控股浙江有限公司",
            reg_cert_no="国械注准20223140120",
            reg_cert_expiry=date(2028, 5, 20),
            unit_price=Decimal("0.45"),
            safe_stock_min=50,
            safe_stock_max=1000,
            storage_temp_req="常温(10~30℃)",
            status=1
        ),
        SpdProductDict(
            product_code="PROD-GEN-002",
            product_name="医用无菌敷贴 10cm*15cm",
            udi_di="06971234560021",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="GENERAL",
            category_id=categories[1].id,
            category_name=categories[1].category_name,
            spec_model="10cm*15cm 透气防水型",
            unit="片",
            manufacturer="稳健医疗用品股份有限公司",
            supplier_name="华润医药商业集团有限公司",
            reg_cert_no="粤械注准20212140889",
            reg_cert_expiry=date(2027, 8, 15),
            unit_price=Decimal("2.80"),
            safe_stock_min=40,
            safe_stock_max=800,
            storage_temp_req="常温(10~30℃)",
            status=1
        ),
        SpdProductDict(
            product_code="PROD-HV-001",
            product_name="钛合金锁定接骨板螺钉系统",
            udi_di="06971234560038",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="HIGH_VALUE",
            category_id=categories[2].id,
            category_name=categories[2].category_name,
            spec_model="股骨远端外侧锁定板 8孔 左侧",
            unit="套",
            manufacturer="强生(上海)医疗器材有限公司",
            supplier_name="上药控股医疗器械有限公司",
            reg_cert_no="国械注准20233130456",
            reg_cert_expiry=date(2029, 3, 10),
            unit_price=Decimal("4200.00"),
            safe_stock_min=5,
            safe_stock_max=30,
            storage_temp_req="常温避光干燥",
            status=1
        ),
        SpdProductDict(
            product_code="PROD-HV-002",
            product_name="药物洗脱冠脉支架系统",
            udi_di="06971234560045",
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="HIGH_VALUE",
            category_id=categories[3].id,
            category_name=categories[3].category_name,
            spec_model="Firebird2 3.0*18mm 雷帕霉素",
            unit="套",
            manufacturer="微创医疗器械(上海)有限公司",
            supplier_name="国药控股浙江有限公司",
            reg_cert_no="国械注准20223130987",
            reg_cert_expiry=date(2028, 11, 25),
            unit_price=Decimal("680.00"),
            safe_stock_min=10,
            safe_stock_max=50,
            storage_temp_req="避光阴凉(20℃以下)",
            status=1
        ),
        SpdProductDict(
            product_code="PROD-EQ-001",
            product_name="多参数监护仪心电导联线",
            udi_di="06971234560052",
            main_dept_code="EQUIP_DEPT",
            consumable_type="EQUIP_PART",
            category_id=categories[4].id,
            category_name=categories[4].category_name,
            spec_model="5导联 拔插式 兼容迈瑞/飞利浦",
            unit="条",
            manufacturer="深圳迈瑞生物医疗电子股份有限公司",
            supplier_name="杭州科健医疗设备工程有限公司",
            reg_cert_no="粤械注准20202070112",
            reg_cert_expiry=date(2027, 4, 30),
            unit_price=Decimal("185.00"),
            safe_stock_min=5,
            safe_stock_max=40,
            storage_temp_req="防静电常温干燥",
            status=1
        )
    ]
    db.add_all(products)
    db.flush()

    # 5. 初始化主库总仓批次库存
    main_inventories = [
        SpdMainInventory(
            inbound_order_no="INB-20261015-001",
            product_id=products[0].id,
            product_code=products[0].product_code,
            product_name=products[0].product_name,
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="GENERAL",
            batch_no="B20261001",
            production_date=date(2026, 10, 1),
            expiry_date=date(2029, 9, 30),
            initial_qty=1000,
            available_qty=800,
            unit_price=Decimal("0.45"),
            shelf_location="耗材主库-A区-01架-01层",
            accept_temp="22.5℃(合规)",
            quality_status="NORMAL",
            inbound_user_id=users[1].id,
            inbound_user_name=users[1].real_name
        ),
        SpdMainInventory(
            inbound_order_no="INB-20261015-002",
            product_id=products[1].id,
            product_code=products[1].product_code,
            product_name=products[1].product_name,
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="GENERAL",
            batch_no="B20260915",
            production_date=date(2026, 9, 15),
            expiry_date=date(2028, 9, 14),
            initial_qty=600,
            available_qty=450,
            unit_price=Decimal("2.80"),
            shelf_location="耗材主库-A区-02架-01层",
            accept_temp="22.0℃(合规)",
            quality_status="NORMAL",
            inbound_user_id=users[1].id,
            inbound_user_name=users[1].real_name
        ),
        SpdMainInventory(
            inbound_order_no="INB-20261020-001",
            product_id=products[2].id,
            product_code=products[2].product_code,
            product_name=products[2].product_name,
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="HIGH_VALUE",
            batch_no="B20261010",
            production_date=date(2026, 10, 10),
            expiry_date=date(2031, 10, 9),
            initial_qty=20,
            available_qty=15,
            unit_price=Decimal("4200.00"),
            shelf_location="耗材主库-高值暂存区-01架",
            accept_temp="21.5℃(合规)",
            quality_status="NORMAL",
            inbound_user_id=users[1].id,
            inbound_user_name=users[1].real_name
        ),
        SpdMainInventory(
            inbound_order_no="INB-20261020-002",
            product_id=products[3].id,
            product_code=products[3].product_code,
            product_name=products[3].product_name,
            main_dept_code="CONSUMABLE_DEPT",
            consumable_type="HIGH_VALUE",
            batch_no="B20261012",
            production_date=date(2026, 10, 12),
            expiry_date=date(2028, 10, 11),
            initial_qty=30,
            available_qty=22,
            unit_price=Decimal("680.00"),
            shelf_location="耗材主库-高值暂存区-02架",
            accept_temp="18.5℃(合规)",
            quality_status="NORMAL",
            inbound_user_id=users[1].id,
            inbound_user_name=users[1].real_name
        ),
        SpdMainInventory(
            inbound_order_no="INB-20261022-001",
            product_id=products[4].id,
            product_code=products[4].product_code,
            product_name=products[4].product_name,
            main_dept_code="EQUIP_DEPT",
            consumable_type="EQUIP_PART",
            batch_no="EQB20261005",
            production_date=date(2026, 10, 5),
            expiry_date=date(2029, 10, 4),
            initial_qty=25,
            available_qty=20,
            unit_price=Decimal("185.00"),
            shelf_location="设备主库-B区-01架-03层",
            accept_temp="23.0℃(合规)",
            quality_status="NORMAL",
            inbound_user_id=users[2].id,
            inbound_user_name=users[2].real_name
        )
    ]
    db.add_all(main_inventories)
    db.flush()

    # 6. 初始化高值专仓一物一码单品
    high_value_items = [
        SpdHighValueItem(
            udi_full_code="(01)06971234560038(10)B20261010(17)311009(21)SN202610100001",
            udi_sn="SN202610100001",
            dist_order_no="DIST-20261021-001",
            product_id=products[2].id,
            product_code=products[2].product_code,
            product_name=products[2].product_name,
            spec_model=products[2].spec_model,
            main_dept_code="CONSUMABLE_DEPT",
            batch_no="B20261010",
            expiry_date=date(2031, 10, 9),
            unit_price=Decimal("4200.00"),
            wh_cabinet_code="高值专仓-智能柜01-A01格",
            current_dept_id=depts[1].id,
            current_dept_name="高值耗材专仓",
            item_status="IN_HIGH_VALUE_WH"
        ),
        SpdHighValueItem(
            udi_full_code="(01)06971234560045(10)B20261012(17)281011(21)SN202610120002",
            udi_sn="SN202610120002",
            dist_order_no="DIST-20261021-002",
            product_id=products[3].id,
            product_code=products[3].product_code,
            product_name=products[3].product_name,
            spec_model=products[3].spec_model,
            main_dept_code="CONSUMABLE_DEPT",
            batch_no="B20261012",
            expiry_date=date(2028, 10, 11),
            unit_price=Decimal("680.00"),
            wh_cabinet_code="高值专仓-智能柜02-B01格",
            current_dept_id=depts[1].id,
            current_dept_name="高值耗材专仓",
            item_status="IN_HIGH_VALUE_WH"
        )
    ]
    db.add_all(high_value_items)
    db.flush()

    # 7. 初始化临床二级库库存
    sec_inventories = [
        SpdSecondaryInventory(
            dept_id=depts[4].id,
            dept_name=depts[4].dept_name,
            product_id=products[0].id,
            product_code=products[0].product_code,
            product_name=products[0].product_name,
            main_dept_code="CONSUMABLE_DEPT",
            batch_no="B20261001",
            expiry_date=date(2029, 9, 30),
            current_qty=150,
            consumed_qty=50,
            unit_price=Decimal("0.45"),
            sec_shelf_code="骨科二级库-货架01-层02",
            dept_safe_min=20,
            batch_status="NORMAL"
        ),
        SpdSecondaryInventory(
            dept_id=depts[5].id,
            dept_name=depts[5].dept_name,
            product_id=products[1].id,
            product_code=products[1].product_code,
            product_name=products[1].product_name,
            main_dept_code="CONSUMABLE_DEPT",
            batch_no="B20260915",
            expiry_date=date(2028, 9, 14),
            current_qty=100,
            consumed_qty=30,
            unit_price=Decimal("2.80"),
            sec_shelf_code="心内科二级库-货架02-层01",
            dept_safe_min=15,
            batch_status="NORMAL"
        )
    ]
    db.add_all(sec_inventories)
    db.flush()

    # 8. 初始化全流程 6W 初始流转基线日志
    init_logs = [
        SpdWorkflowLog(
            trace_no="TRACE-20261015100000-0001",
            biz_order_no="DICT-INIT-001",
            node_action="1_DICT_CREATE",
            product_code=products[0].product_code,
            product_name=products[0].product_name,
            batch_or_udi=products[0].udi_di,
            from_dept_name="国家药监局数据库",
            from_user_name="王建国(耗材科)",
            to_dept_name="耗材科主库房",
            to_user_name="王建国(耗材科)",
            change_qty=0,
            before_stock_snapshot=0,
            after_stock_snapshot=0,
            settlement_amount=Decimal("0.00"),
            is_billable=0,
            audit_status="VERIFIED",
            audit_remark="耗材科产品字典标准建档"
        ),
        SpdWorkflowLog(
            trace_no="TRACE-20261015110000-0002",
            biz_order_no="INB-20261015-001",
            node_action="2_MAIN_INBOUND",
            product_code=products[0].product_code,
            product_name=products[0].product_name,
            batch_or_udi="B20261001",
            from_dept_name="国药控股浙江有限公司",
            from_user_name="供应商送货员",
            to_dept_name="耗材科主库房",
            to_user_name="王建国(耗材科)",
            change_qty=1000,
            before_stock_snapshot=0,
            after_stock_snapshot=1000,
            settlement_amount=Decimal("450.00"),
            is_billable=0,
            audit_status="VERIFIED",
            audit_remark="主库采购验收入库合格"
        ),
        SpdWorkflowLog(
            trace_no="TRACE-20261021140000-0003",
            biz_order_no="DIST-20261021-001",
            node_action="3_MAIN_DISPATCH",
            product_code=products[0].product_code,
            product_name=products[0].product_name,
            batch_or_udi="B20261001",
            from_dept_name="耗材科主库房",
            from_user_name="王建国(耗材科)",
            to_dept_name="骨科病区二级库",
            to_user_name="李晓琳(骨科护士)",
            change_qty=200,
            before_stock_snapshot=1000,
            after_stock_snapshot=800,
            settlement_amount=Decimal("90.00"),
            is_billable=0,
            audit_status="VERIFIED",
            audit_remark="主库按需分发调拨至骨科二级库(移库不计费)"
        )
    ]
    db.add_all(init_logs)
    db.commit()

    # 9. 继续执行深度扩展 7 张表与五大角色 RBAC 种子数据初始化
    init_extended_seed_data(db)
    init_spn_spec_and_rbac_seeds(db)

    logger.info("医院真实业务场景种子数据初始化圆满完成")
    return True


def init_extended_seed_data(db: Session) -> bool:
    """幂等初始化深度扩展 7 张业务表、五大角色(含外部供应商)、15模块x8动作权限矩阵与两阶段确认样板单据
    @param db: Session SQLAlchemy 数据库活动会话
    @returns bool True 表示首次注入扩展种子数据，False 表示已存在并跳过
    @route internal://app/services/seed_service/init_extended_seed_data
    @throws Exception 当数据库事务提交失败时抛出异常
    """
    if db.query(SpdWarehouseNode).count() > 0:
        logger.info("深度扩展 7 张表已存在种子数据，跳过重复初始化")
        return False

    logger.info("开始注入深度扩展 7 张物理表与五大角色细粒度 RBAC 种子数据...")
    default_pwd_hash = get_password_hash("123456")

    # 1. 补充第 5 类角色：外部供应商协同端代表账号 (supplier_user)
    sup_user = db.query(SysUser).filter(SysUser.username == "supplier_wego").first()
    if not sup_user:
        sup_user = SysUser(
            username="supplier_wego",
            password_hash=default_pwd_hash,
            real_name="张明远(威高医药代表)",
            role_code="supplier_user",
            dept_id=2,
            dept_code="SUPPLIER_EXT",
            phone_masked=mask_phone("13800008899"),
            status=1
        )
        db.add(sup_user)
        db.flush()

    # 2. 初始化全院多级仓库树节点 (对齐图4：卫材库、总务仓库、信息仓库、专项库房、后勤仓库、测试仓库、设备库房 + 临床二级库)
    wh_nodes = [
        SpdWarehouseNode(warehouse_code="WH_WEICAI", warehouse_name="卫材库(耗材主库)", warehouse_level="DEPT_PRIMARY", parent_code="ROOT", dept_code="CONSUMABLE_DEPT", init_stock_locked=1, init_stock_order_no="INI20261101001", init_locked_at=datetime.now()),
        SpdWarehouseNode(warehouse_code="WH_ZONGWU", warehouse_name="总务仓库", warehouse_level="MAIN_GROUP", parent_code="ROOT", dept_code="CONSUMABLE_DEPT", init_stock_locked=0),
        SpdWarehouseNode(warehouse_code="WH_XINXI", warehouse_name="信息仓库", warehouse_level="MAIN_GROUP", parent_code="ROOT", dept_code="INFO_DEPT", init_stock_locked=0),
        SpdWarehouseNode(warehouse_code="WH_ZHUANXIANG", warehouse_name="专项库房(高值专仓)", warehouse_level="DEPT_PRIMARY", parent_code="ROOT", dept_code="CONSUMABLE_DEPT", init_stock_locked=1, init_stock_order_no="INI20261101002", init_locked_at=datetime.now()),
        SpdWarehouseNode(warehouse_code="WH_HOUQIN", warehouse_name="后勤仓库", warehouse_level="MAIN_GROUP", parent_code="ROOT", dept_code="CONSUMABLE_DEPT", init_stock_locked=0),
        SpdWarehouseNode(warehouse_code="WH_CESHI", warehouse_name="测试仓库", warehouse_level="MAIN_GROUP", parent_code="ROOT", dept_code="INFO_DEPT", init_stock_locked=0),
        SpdWarehouseNode(warehouse_code="WH_EQUIP", warehouse_name="设备库房(设备科主库)", warehouse_level="DEPT_PRIMARY", parent_code="ROOT", dept_code="EQUIP_DEPT", init_stock_locked=0),
        SpdWarehouseNode(warehouse_code="WH_SEC_ORTHO", warehouse_name="骨科病区二级库", warehouse_level="CLINICAL_SECONDARY", parent_code="WH_WEICAI", dept_code="SEC_ORTHO", init_stock_locked=0),
        SpdWarehouseNode(warehouse_code="WH_SEC_CARDIO", warehouse_name="心内科病区二级库", warehouse_level="CLINICAL_SECONDARY", parent_code="WH_ZHUANXIANG", dept_code="SEC_CARDIO", init_stock_locked=0)
    ]
    db.add_all(wh_nodes)
    db.flush()

    # 3. 初始化解耦式细粒度 8 动作权限矩阵
    all_users = db.query(SysUser).all()
    core_modules = [
        ("DICT_MANAGE", "产品字典深度管理"),
        ("GEN_INBOUND", "普通耗材验收入库与退货"),
        ("GEN_OUTBOUND", "普通耗材出库与请领审核"),
        ("GEN_INIT_STOCK", "各科室仓库期初数据建账"),
        ("HV_PREP_RECEIVE", "高值耗材备货与科室接收"),
        ("HV_RETURN", "高值耗材科室退货出库(不可逆)"),
        ("HV_QR_VERIFY", "高值一物一码二维码扫码核销"),
        ("SEC_WAREHOUSE", "临床二级库全模块管理"),
        ("PURCHASE_PLAN", "多级采购计划与主科审批"),
        ("SUPPLIER_SHIP", "外部供应商资质上传与拣货发货"),
        ("WORKFLOW_LOG", "全流程业务链路日志 (6W)"),
        ("FINANCE_AUDIT", "统计查询与单据打印中心")
    ]
    perm_rows = []
    for u in all_users:
        role = u.role_code
        is_admin = 1 if role == "sys_admin" else 0
        for m_code, m_name in core_modules:
            v, c, e, d, sc, cs, ap, pr = 0, 0, 0, 0, 0, 0, 0, 0
            if is_admin:
                v, c, e, d, sc, cs, ap, pr = 1, 1, 1, 1, 1, 1, 1, 1
            elif (role == "dept_manager" or u.dept_code in ["CONSUMABLE_DEPT", "EQUIP_DEPT"]) and u.username != "mgr_finance":
                if m_code in ["DICT_MANAGE", "GEN_INBOUND", "GEN_OUTBOUND", "GEN_INIT_STOCK", "HV_PREP_RECEIVE", "HV_RETURN", "PURCHASE_PLAN"]:
                    v, c, e, d, sc, cs, ap, pr = 1, 1, 1, 0, 1, 1, 1, 1
            elif role == "secondary_user":
                if m_code == "SEC_WAREHOUSE":
                    v, c, e, d, sc, cs, ap, pr = 1, 1, 1, 0, 1, 1, 0, 1
                elif m_code == "HV_QR_VERIFY":
                    v, c, e, d, sc, cs, ap, pr = 1, 1, 1, 0, 1, 0, 0, 1
                elif m_code == "HV_PREP_RECEIVE":
                    v, c, e, d, sc, cs, ap, pr = 1, 0, 0, 0, 1, 0, 0, 1
            elif u.username == "mgr_finance" or role == "finance_auditor" or u.dept_code == "FINANCE_DEPT":
                if m_code in ["WORKFLOW_LOG", "FINANCE_AUDIT"]:
                    v, c, e, d, sc, cs, ap, pr = 1, 0, 0, 0, 0, 0, 1, 1
            elif role == "supplier_user":
                if m_code == "SUPPLIER_SHIP":
                    v, c, e, d, sc, cs, ap, pr = 1, 1, 1, 0, 1, 0, 0, 1

            perm_rows.append(
                SysUserModulePermission(
                    user_id=u.id,
                    username=u.username,
                    role_code=u.role_code,
                    module_code=m_code,
                    module_name=m_name,
                    can_view=v,
                    can_create=c,
                    can_edit=e,
                    can_delete=d,
                    can_second_confirm=sc,
                    can_cancel_submit=cs,
                    can_approve=ap,
                    can_print=pr,
                    updated_by="赵振华(信息科管理员)"
                )
            )
    db.add_all(perm_rows)
    db.flush()

    # 4. 初始化产品字典深度扩展表 (自动生成拼音码、通用名、品牌、分配仓库列表、调价记录)
    products = db.query(SpdProductDict).all()
    ext_rows = []
    for idx, p in enumerate(products):
        wh_assign = "WH_WEICAI,WH_SEC_ORTHO" if p.main_dept_code == "CONSUMABLE_DEPT" else "WH_EQUIP,WH_SEC_CARDIO"
        if p.consumable_type == "HIGH_VALUE":
            wh_assign = "WH_ZHUANXIANG,WH_SEC_ORTHO,WH_SEC_CARDIO"
        ext_rows.append(
            SpdProductDictExt(
                product_id=p.id,
                product_code=p.product_code,
                common_name=p.product_name.split(" ")[0],
                pinyin_code=generate_pinyin_abbr(p.product_name),
                component_name="无菌主件+独立包装附件",
                brand_name="威高WEGO" if idx == 0 else ("强生DePuy" if idx == 2 else "迈瑞Mindray"),
                assigned_warehouses=wh_assign,
                supplier_code="SUP_WEGO_01" if idx % 2 == 0 else "SUP_SINOPHARM_02",
                previous_price=p.unit_price + Decimal("0.50"),
                current_price=p.unit_price,
                price_updated_reason="2026年省级医用耗材集中带量采购联动降价",
                is_disabled=0,
                extra_fields_json='{"medical_insurance_code":"C010101001","sterilization":"环氧乙烷灭菌"}'
            )
        )
    db.add_all(ext_rows)
    db.flush()

    # 5. 补充一条待审批的二级库请领单 (用于测试请领审核通过自动生成耗材出库单)
    if db.query(SpdRequisitionOrder).count() == 0 and len(products) > 0:
        req_seed = SpdRequisitionOrder(
            req_order_no="REQ-20261102-001",
            order_direction="APPLY_FROM_MAIN",
            apply_dept_id=5,
            apply_dept_name="骨科病区二级库",
            target_main_dept="CONSUMABLE_DEPT",
            product_id=products[0].id,
            product_code=products[0].product_code,
            product_name=products[0].product_name,
            apply_qty=100,
            approved_qty=100,
            urgency_level="ROUTINE",
            req_status="PENDING_APPROVAL",
            applicant_id=5,
            applicant_name="李晓琳(骨科护士)",
            apply_reason="骨科病房日常换药与注射定数包周常补货申请"
        )
        db.add(req_seed)
        db.flush()

    # 6. 初始化通用出入库单、退给供应商红字退货单与已二次确认永久锁死的科室期初建账单
    if len(products) >= 2:
        in_out_seeds = [
            SpdInboundAndOutboundOrder(
                order_no="INI20261101001",
                order_type="INIT_STOCK",
                warehouse_code="WH_WEICAI",
                dept_code="CONSUMABLE_DEPT",
                target_dept_or_supplier="耗材科期初建账",
                product_id=products[0].id,
                product_code=products[0].product_code,
                product_name=products[0].product_name,
                batch_no="B20261001",
                quantity=1000,
                unit_price=products[0].unit_price,
                total_amount=products[0].unit_price * Decimal("1000"),
                confirm_stage="SUBMITTED",
                is_irreversible_locked=1,
                created_by="王建国",
                second_confirmed_by="王建国",
                second_confirmed_at=datetime.now(),
                remark="卫材库期初数据建账汇总单(二次确认后永久只读不可修改)"
            ),
            SpdInboundAndOutboundOrder(
                order_no="RET20261102001",
                order_type="RETURN_TO_SUPPLIER",
                warehouse_code="WH_WEICAI",
                dept_code="CONSUMABLE_DEPT",
                target_dept_or_supplier="SUP_WEGO_01(国药控股)",
                product_id=products[1].id,
                product_code=products[1].product_code,
                product_name=products[1].product_name,
                batch_no="B20260915",
                quantity=-20,
                unit_price=products[1].unit_price,
                total_amount=products[1].unit_price * Decimal("-20"),
                confirm_stage="PENDING_CONFIRM",
                is_irreversible_locked=0,
                created_by="王建国",
                remark="外包装轻微受潮，在耗材入库模块开具退给供应商红字退货单(待外层二次确认)"
            )
        ]
        db.add_all(in_out_seeds)
        db.flush()

    # 7. 初始化各科室独立盘点单与跨院调拨单
    if len(products) >= 1:
        stk_seeds = [
            SpdStocktakeAndTransferOrder(
                order_no="STK20261102001",
                biz_category="GEN_STOCKTAKE",
                from_warehouse_code="WH_WEICAI",
                to_warehouse_code=None,
                product_id=products[0].id,
                product_code=products[0].product_code,
                product_name=products[0].product_name,
                book_qty=800,
                actual_or_transfer_qty=798,
                diff_qty=-2,
                confirm_stage="SUBMITTED",
                operator_name="王建国",
                confirmed_by="王建国",
                confirmed_at=datetime.now(),
                reason_note="耗材科月度例行盘点：实盘少2支(破损报耗已核减库存)"
            ),
            SpdStocktakeAndTransferOrder(
                order_no="TRF20261102001",
                biz_category="CROSS_HOSP_TRANSFER",
                from_warehouse_code="WH_SEC_ORTHO",
                to_warehouse_code="WH_SEC_CARDIO",
                product_id=products[1].id,
                product_code=products[1].product_code,
                product_name=products[1].product_name,
                book_qty=150,
                actual_or_transfer_qty=20,
                diff_qty=0,
                confirm_stage="SUBMITTED",
                operator_name="李晓琳",
                confirmed_by="陈雅文",
                confirmed_at=datetime.now(),
                reason_note="二级库跨病区应急调拨20片无菌敷贴"
            )
        ]
        db.add_all(stk_seeds)
        db.flush()

    # 8. 初始化高值耗材备货、科室接收、二次确认永久锁死的科室退货出库单及一物一码二维码记录
    if len(products) >= 4:
        hv_seeds = [
            SpdHighValueLifecycleOrder(
                order_no="HVR20261102001",
                hv_biz_type="HV_DEPT_RETURN",
                dept_code="SEC_ORTHO",
                product_id=products[2].id,
                product_code=products[2].product_code,
                product_name=products[2].product_name,
                udi_sn="SN202610100088",
                qr_code_payload="SPD-QR|UDI:SN202610100088|PROD:PROD-HV-001|DEPT:SEC_ORTHO",
                is_qr_verified=0,
                confirm_stage="SUBMITTED",
                is_irreversible_locked=1,
                operator_name="李晓琳(骨科护士)",
                confirmed_by="王建国(高值仓主管)",
                confirmed_at=datetime.now(),
                remark="骨科术前备货规格变更退回高值主仓(二次确认后永久锁死不可修改)"
            ),
            SpdHighValueLifecycleOrder(
                order_no="HVQ20261102002",
                hv_biz_type="HV_QR_VERIFY",
                dept_code="SEC_CARDIO",
                product_id=products[3].id,
                product_code=products[3].product_code,
                product_name=products[3].product_name,
                udi_sn="SN202610120002",
                qr_code_payload="SPD-QR|UDI:SN202610120002|PROD:PROD-HV-002|DEPT:SEC_CARDIO",
                is_qr_verified=1,
                patient_inpatient_no="ZY2026110288",
                patient_name_masked="张*峰",
                confirm_stage="SUBMITTED",
                is_irreversible_locked=1,
                operator_name="陈雅文(心内科护士)",
                confirmed_by="陈雅文(心内科护士)",
                confirmed_at=datetime.now(),
                remark="心内科导管室扫描高值一物一码专属二维码完成患者使用核销"
            ),
            SpdHighValueLifecycleOrder(
                order_no="HVP20261102003",
                hv_biz_type="HV_STOCK_PREP",
                dept_code="SEC_ORTHO",
                product_id=products[2].id,
                product_code=products[2].product_code,
                product_name=products[2].product_name,
                udi_sn="SN202610100001",
                qr_code_payload="SPD-QR|UDI:SN202610100001|PROD:PROD-HV-001|DEPT:SEC_ORTHO",
                is_qr_verified=0,
                confirm_stage="PENDING_CONFIRM",
                is_irreversible_locked=0,
                operator_name="李晓琳(骨科护士)",
                remark="明日3台股骨内固定手术高值备货申请(尚未扫码核销，不在核销查询显示)"
            )
        ]
        db.add_all(hv_seeds)
        db.flush()

    # 9. 初始化多级采购计划与供应商资质准入、拣货发货协同记录
    if len(products) >= 4:
        po_seeds = [
            SpdSupplierAndPurchaseOrder(
                order_no="PUR20261102001",
                supplier_code="SUP_WEGO_01",
                supplier_name="山东威高集团医用高分子制品股份有限公司",
                license_no="鲁械经营备20260088号",
                license_expiry_date=date(2029, 12, 31),
                qual_audit_status="QUAL_APPROVED",
                apply_dept_code="SEC_CARDIO",
                audit_main_dept_code="CONSUMABLE_DEPT",
                product_id=products[3].id,
                product_code=products[3].product_code,
                product_name=products[3].product_name,
                purchase_qty=20,
                picked_batch_no="BATCH-FIREBIRD-2611",
                picked_expiry_date=date(2028, 11, 30),
                confirm_stage="SUBMITTED",
                purchase_flow_status="DEPT_APPROVED",
                auto_inbound_order_no=None,
                created_by="陈雅文(心内科提交) -> 王建国(耗材科审批)"
            ),
            SpdSupplierAndPurchaseOrder(
                order_no="PUR20261102002",
                supplier_code="SUP_UNVERIFIED_99",
                supplier_name="某新注册未审资质医疗器械商贸公司",
                license_no="浙械经营待审20269999号",
                license_expiry_date=date(2027, 6, 30),
                qual_audit_status="QUAL_PENDING",
                apply_dept_code="SEC_ORTHO",
                audit_main_dept_code="EQUIP_DEPT",
                product_id=products[0].id,
                product_code=products[0].product_code,
                product_name=products[0].product_name,
                purchase_qty=500,
                confirm_stage="PENDING_CONFIRM",
                purchase_flow_status="PLAN_SUBMITTED",
                auto_inbound_order_no=None,
                created_by="张明远(待医院审核经营资质)"
            )
        ]
        db.add_all(po_seeds)
        db.commit()

    logger.info("深度扩展 7 张物理表种子数据注入完成")
    return True


def init_spn_spec_and_rbac_seeds(db: Session) -> bool:
    """幂等初始化真实医院 SPD 四级物料字典体系、供应商档案、批量调价历史与用户仓库细粒度权限矩阵

    @param db: (Session) 数据库活动会话
    @returns: (bool) 是否成功执行初始化
    @route: 内部服务链路 backend.app.services.seed_service.init_spn_spec_and_rbac_seeds
    @throws: 数据库写入异常时由外层捕获并回滚
    """
    # 1. 初始化独立供应商档案 (SpdSupplierProfile)
    if db.query(SpdSupplierProfile).count() == 0:
        suppliers = [
            SpdSupplierProfile(
                supplier_code="2764",
                supplier_name="普昂(杭州)医疗科技有限公司",
                social_credit_code="91330100799654123B",
                license_no="浙械经营备20260123号",
                license_expiry_date=date(2030, 5, 18),
                contact_person="周建业",
                contact_phone="13800571001",
                supply_categories="医用气体,普耗低值,呼吸耗材",
                qual_status="QUAL_APPROVED",
                status="ACTIVE"
            ),
            SpdSupplierProfile(
                supplier_code="2765",
                supplier_name="重庆剑涛科技有限公司",
                social_credit_code="91500000789123456D",
                license_no="渝械经营备20260789号",
                license_expiry_date=date(2028, 10, 20),
                contact_person="张剑涛",
                contact_phone="13900230002",
                supply_categories="医用气体,医用器械,高纯气体",
                qual_status="QUAL_APPROVED",
                status="ACTIVE"
            ),
            SpdSupplierProfile(
                supplier_code="SUP_WEGO_01",
                supplier_name="山东威高集团医用高分子制品股份有限公司",
                social_credit_code="91371000163048999A",
                license_no="鲁械经营备20260088号",
                license_expiry_date=date(2029, 12, 31),
                contact_person="张明远",
                contact_phone="13800008899",
                supply_categories="普耗,高值,骨科,穿刺类",
                qual_status="QUAL_APPROVED",
                status="ACTIVE"
            ),
            SpdSupplierProfile(
                supplier_code="2803",
                supplier_name="江西健宝医药科技有限公司",
                social_credit_code="91360100781234567E",
                license_no="赣械经营备20260456号",
                license_expiry_date=date(2029, 3, 15),
                contact_person="黄健康",
                contact_phone="13700791003",
                supply_categories="医用敷料,消毒灭菌",
                qual_status="QUAL_APPROVED",
                status="ACTIVE"
            ),
            SpdSupplierProfile(
                supplier_code="2949",
                supplier_name="南昌远达医用器材有限公司",
                social_credit_code="91360100789876543F",
                license_no="赣械经营备20260678号",
                license_expiry_date=date(2028, 11, 28),
                contact_person="李远达",
                contact_phone="13600791004",
                supply_categories="骨科内固定,外科耗材",
                qual_status="QUAL_APPROVED",
                status="ACTIVE"
            ),
            SpdSupplierProfile(
                supplier_code="SUP_DEP_01",
                supplier_name="强生(上海)医疗器材有限公司",
                social_credit_code="91310000607212456C",
                license_no="沪械经营备20260456号",
                license_expiry_date=date(2029, 8, 15),
                contact_person="陈强生",
                contact_phone="13900210005",
                supply_categories="骨科高值,钛合金锁定接骨板,缝合器",
                qual_status="QUAL_APPROVED",
                status="ACTIVE"
            )
        ]
        db.add_all(suppliers)
        db.flush()

    # 2. 初始化大品名表 (SpdProductSpn - 对应图 4 中栏列表与图 3 新增品名)
    if db.query(SpdProductSpn).count() == 0:
        spns = [
            SpdProductSpn(
                spn_code="936010100024",
                spn_name="医用氧气123",
                category_code="0101",
                common_name="医用氧气",
                pinyin_code="YYQ123",
                finance_category="西药/气体核算",
                performance_category="临床基础耗材",
                inpatient_charge_category="按量计费",
                outpatient_charge_category="按量计费",
                medical_record_category="支持疗法物资",
                medicare_category="甲类医保",
                is_chargeable=1,
                is_high_value=0,
                is_central_proc=0,
                central_proc_project="",
                contract_no="HT-2026-O2-001",
                contract_signed_date=date(2026, 1, 1),
                contract_start_date=date(2026, 1, 1),
                contract_end_date=date(2028, 12, 31),
                status="ACTIVE"
            ),
            SpdProductSpn(
                spn_code="936010100193",
                spn_name="医用氧气(跃达)",
                category_code="0101",
                common_name="医用氧气",
                pinyin_code="YYQYD",
                finance_category="西药/气体核算",
                performance_category="临床基础耗材",
                inpatient_charge_category="按量计费",
                outpatient_charge_category="按量计费",
                medical_record_category="支持疗法物资",
                medicare_category="甲类医保",
                is_chargeable=1,
                is_high_value=0,
                is_central_proc=0,
                status="ACTIVE"
            ),
            SpdProductSpn(
                spn_code="936010100324",
                spn_name="医用液氧",
                category_code="0101",
                common_name="医用液氧",
                pinyin_code="YYYY",
                finance_category="西药/气体核算",
                performance_category="临床基础耗材",
                inpatient_charge_category="按量计费",
                outpatient_charge_category="按量计费",
                medical_record_category="支持疗法物资",
                medicare_category="甲类医保",
                is_chargeable=1,
                is_high_value=0,
                is_central_proc=0,
                status="ACTIVE"
            ),
            SpdProductSpn(
                spn_code="936010100326",
                spn_name="*二氧化碳钢瓶",
                category_code="0101",
                common_name="二氧化碳钢瓶",
                pinyin_code="EYHTGP",
                finance_category="西药/气体核算",
                performance_category="临床基础耗材",
                inpatient_charge_category="按量计费",
                outpatient_charge_category="按量计费",
                medical_record_category="腹腔镜气体",
                medicare_category="乙类医保",
                is_chargeable=1,
                is_high_value=0,
                is_central_proc=0,
                status="ACTIVE"
            ),
            SpdProductSpn(
                spn_code="936010200090",
                spn_name="高纯氦气",
                category_code="0102",
                common_name="高纯氦气",
                pinyin_code="GCHQ",
                finance_category="特种耗材",
                performance_category="医技专用耗材",
                inpatient_charge_category="按次计费",
                outpatient_charge_category="按次计费",
                medical_record_category="检查类耗材",
                medicare_category="自费",
                is_chargeable=1,
                is_high_value=0,
                is_central_proc=0,
                status="ACTIVE"
            ),
            SpdProductSpn(
                spn_code="936010300018",
                spn_name="塑料镊",
                category_code="0103",
                common_name="塑料镊",
                pinyin_code="SLN",
                finance_category="低值普耗",
                performance_category="病房护理",
                inpatient_charge_category="不计费",
                outpatient_charge_category="不计费",
                medical_record_category="护理耗材",
                medicare_category="医保打包",
                is_chargeable=0,
                is_high_value=0,
                is_central_proc=0,
                status="ACTIVE"
            ),
            SpdProductSpn(
                spn_code="936011000001",
                spn_name="一次性使用无菌注射器带针",
                category_code="0110",
                common_name="无菌注射器",
                pinyin_code="YCXSYWJZSQ",
                finance_category="低值普耗",
                performance_category="护理耗材",
                inpatient_charge_category="计费耗材",
                outpatient_charge_category="计费耗材",
                medical_record_category="注射治疗",
                medicare_category="甲类医保",
                is_chargeable=1,
                is_high_value=0,
                is_central_proc=1,
                central_proc_project="国家集采第五批注射器类",
                status="ACTIVE"
            ),
            SpdProductSpn(
                spn_code="936011600001",
                spn_name="钛合金锁定接骨板螺钉系统",
                category_code="0116",
                common_name="钛合金接骨板系统",
                pinyin_code="THJSDJGB",
                finance_category="高值骨科植入物",
                performance_category="手术特异性高值",
                inpatient_charge_category="按件计费",
                outpatient_charge_category="按件计费",
                medical_record_category="骨科内固定",
                medicare_category="乙类医保",
                is_chargeable=1,
                is_high_value=1,
                is_central_proc=1,
                central_proc_project="国家人工关节与骨科创伤集采",
                status="ACTIVE"
            )
        ]
        db.add_all(spns)
        db.flush()

    # 3. 初始化型号规格单品 (SpdProductSpec - 对应图 4 右栏与图 5 新增规格)
    if db.query(SpdProductSpec).count() == 0:
        o2_spn = db.query(SpdProductSpn).filter(SpdProductSpn.spn_code == "936010100024").first()
        o2_id = o2_spn.id if o2_spn else 1

        syringe_spn = db.query(SpdProductSpn).filter(SpdProductSpn.spn_code == "936011000001").first()
        syr_id = syringe_spn.id if syringe_spn else 6

        plate_spn = db.query(SpdProductSpn).filter(SpdProductSpn.spn_code == "936011600001").first()
        plt_id = plate_spn.id if plate_spn else 7

        specs = [
            SpdProductSpec(
                spn_id=o2_id,
                spec_code="936010100024055517",
                product_name="医用氧气123",
                spec_name="40L 纯度≥99.5%",
                model_name="TWLB-40",
                common_name="医用氧气",
                pinyin_code="YYQ123",
                component_name="1",
                brand_name="普昂(杭州)",
                manufacturer="2764|普昂(杭州)医疗科技有限公司",
                description="高压钢瓶装医用氧气，纯度符合中国药典标准",
                pricing_unit="瓶",
                package_unit="瓶",
                conversion_ratio=Decimal("1.00"),
                unit_price=Decimal("45.0000"),
                register_card_no="国械注准20223140555",
                register_expiry_date=date(2028, 8, 30),
                medicare_code="C01010100024001",
                medicare_category_code="C0101",
                production_license_no="浙食药监械生产许20200012号",
                production_license_expiry=date(2029, 5, 20),
                default_supplier_id=1,
                default_supplier_name="普昂(杭州)医疗科技有限公司",
                original_code="PA-O2-40L",
                provincial_code="ZB2026-PA-055517",
                storage_condition="避光、干燥、远离火源与高温环境",
                is_central_proc=0,
                origin_place="国产",
                category_code="0101",
                status="ACTIVE",
                assigned_warehouses="WH_WEICAI,WH_ZONGWU,WH_SEC_CARDIO"
            ),
            SpdProductSpec(
                spn_id=o2_id,
                spec_code="936010100024057761",
                product_name="医用氧气123",
                spec_name="10L 便携型钢瓶",
                model_name="PA-PORTABLE-10",
                common_name="医用氧气",
                pinyin_code="YYQ123",
                component_name="1",
                brand_name="普昂(杭州)",
                manufacturer="2764|普昂(杭州)医疗科技有限公司",
                description="病区急救转运便携式医用氧气钢瓶",
                pricing_unit="瓶",
                package_unit="瓶",
                conversion_ratio=Decimal("1.00"),
                unit_price=Decimal("48.0000"),
                register_card_no="国械注准20223140555",
                register_expiry_date=date(2028, 8, 30),
                medicare_code="C01010100024002",
                medicare_category_code="C0101",
                default_supplier_id=1,
                default_supplier_name="普昂(杭州)医疗科技有限公司",
                storage_condition="常温干燥避光",
                category_code="0101",
                status="ACTIVE",
                assigned_warehouses="WH_WEICAI,WH_SEC_ORTHO"
            ),
            SpdProductSpec(
                spn_id=o2_id,
                spec_code="936010100024055499",
                product_name="医用氧气123",
                spec_name="40L 剑涛特供型",
                model_name="JT-O2-40A",
                common_name="医用氧气",
                pinyin_code="YYQ123",
                component_name="1",
                brand_name="重庆剑涛",
                manufacturer="2765|重庆剑涛科技有限公司",
                description="符合三甲医院中心供氧备用指标",
                pricing_unit="瓶",
                package_unit="瓶",
                conversion_ratio=Decimal("1.00"),
                unit_price=Decimal("52.0000"),
                register_card_no="国械注准20233140999",
                register_expiry_date=date(2028, 12, 10),
                medicare_code="C01010100024003",
                medicare_category_code="C0101",
                default_supplier_id=2,
                default_supplier_name="重庆剑涛科技有限公司",
                storage_condition="常温干燥避光",
                category_code="0101",
                status="ACTIVE",
                assigned_warehouses="WH_WEICAI"
            ),
            SpdProductSpec(
                spn_id=o2_id,
                spec_code="936010100024055500",
                product_name="医用氧气123",
                spec_name="15L 医用级减压瓶",
                model_name="JT-O2-15B",
                common_name="医用氧气",
                pinyin_code="YYQ123",
                component_name="1",
                brand_name="重庆剑涛",
                manufacturer="2765|重庆剑涛科技有限公司",
                description="重庆剑涛标准减压医用氧气瓶",
                pricing_unit="瓶",
                package_unit="瓶",
                conversion_ratio=Decimal("1.00"),
                unit_price=Decimal("55.0000"),
                register_card_no="国械注准20233140999",
                register_expiry_date=date(2028, 12, 10),
                medicare_code="C01010100024004",
                medicare_category_code="C0101",
                default_supplier_id=2,
                default_supplier_name="重庆剑涛科技有限公司",
                storage_condition="常温干燥避光",
                category_code="0101",
                status="ACTIVE",
                assigned_warehouses="WH_WEICAI,WH_ZONGWU"
            ),
            SpdProductSpec(
                spn_id=o2_id,
                spec_code="936010100024057514",
                product_name="医用氧气123",
                spec_name="50L 大容量储气瓶",
                model_name="JT-O2-50C",
                common_name="医用氧气",
                pinyin_code="YYQ123",
                component_name="",
                brand_name="重庆剑涛",
                manufacturer="2765|重庆剑涛科技有限公司",
                description="大容量备用供氧瓶",
                pricing_unit="瓶",
                package_unit="瓶",
                conversion_ratio=Decimal("1.00"),
                unit_price=Decimal("60.0000"),
                register_card_no="国械注准20233140999",
                register_expiry_date=date(2028, 12, 10),
                medicare_code="C01010100024005",
                medicare_category_code="C0101",
                default_supplier_id=2,
                default_supplier_name="重庆剑涛科技有限公司",
                storage_condition="常温干燥避光",
                category_code="0101",
                status="ACTIVE",
                assigned_warehouses="WH_WEICAI"
            ),
            # 规格 6: 注射器规格 (普耗带量采购)
            SpdProductSpec(
                spn_id=syr_id,
                spec_code="93601100000100001",
                product_name="一次性使用无菌注射器带针",
                spec_name="5ml 带针 0.7*30mm TWLB",
                model_name="TWLB-5ML",
                common_name="无菌注射器",
                pinyin_code="YCXSYWJZSQ",
                component_name="注射器+针头",
                brand_name="威高WEGO",
                manufacturer="山东威高集团医用高分子制品股份有限公司",
                description="国家集采带量中选规格，环氧乙烷灭菌",
                pricing_unit="支",
                package_unit="盒",
                conversion_ratio=Decimal("100.00"),
                unit_price=Decimal("0.4200"),
                register_card_no="国械注准20203140123",
                register_expiry_date=date(2030, 6, 30),
                medicare_code="C011001000001",
                medicare_category_code="C0110",
                default_supplier_id=3,
                default_supplier_name="山东威高集团医用高分子制品股份有限公司",
                storage_condition="常温避光干燥",
                is_central_proc=1,
                central_proc_code="JC-SYR-5ML",
                origin_place="国产",
                category_code="0110",
                status="ACTIVE",
                assigned_warehouses="WH_WEICAI,WH_SEC_ORTHO,WH_SEC_CARDIO"
            ),
            # 规格 7: 骨科高值耗材锁定接骨板
            SpdProductSpec(
                spn_id=plt_id,
                spec_code="93601160000100001",
                product_name="钛合金锁定接骨板螺钉系统",
                spec_name="股骨远端外侧锁定板 8孔 左侧",
                model_name="LCP-DIST-FEM-08L",
                common_name="钛合金接骨板系统",
                pinyin_code="THJSDJGB",
                component_name="锁定接骨板",
                brand_name="强生-DePuy",
                manufacturer="强生(上海)医疗器材有限公司",
                description="三类高值植入物，一物一码UDI全程追溯",
                pricing_unit="套",
                package_unit="盒",
                conversion_ratio=Decimal("1.00"),
                unit_price=Decimal("4200.0000"),
                register_card_no="国械注准20213130888",
                register_expiry_date=date(2029, 12, 31),
                medicare_code="C011601000001",
                medicare_category_code="C0116",
                default_supplier_id=6,
                default_supplier_name="强生(上海)医疗器材有限公司",
                storage_condition="常温密封无菌保存",
                is_central_proc=1,
                central_proc_code="JC-ORTHO-PLATE-08L",
                origin_place="合资",
                category_code="0116",
                status="ACTIVE",
                assigned_warehouses="WH_ZHUANXIANG,WH_SEC_ORTHO"
            )
        ]
        db.add_all(specs)
        db.flush()


    # 4. 初始化调价历史记录快照 (SpdPriceAdjustLog - 对应图 5 调价记录 Tab)
    if db.query(SpdPriceAdjustLog).count() == 0:
        spec_item = db.query(SpdProductSpec).filter(SpdProductSpec.spec_code == "936010100024055517").first()
        spec_id = spec_item.id if spec_item else 1
        price_logs = [
            SpdPriceAdjustLog(
                spec_id=spec_id,
                spec_code="936010100024055517",
                spec_name="医用氧气123 (40L 纯度≥99.5%)",
                old_price=Decimal("50.0000"),
                new_price=Decimal("45.0000"),
                adjust_diff=Decimal("-5.0000"),
                adjust_reason="省药械采购中心【2026】18号文集中带量采购动态调价",
                adjust_doc_no="浙药械采【2026】18号",
                operator_name="赵振华(信息科)",
                effective_time=datetime(2026, 10, 15, 9, 30, 0)
            ),
            SpdPriceAdjustLog(
                spec_id=spec_id,
                spec_code="936010100024055517",
                spec_name="医用氧气123 (40L 纯度≥99.5%)",
                old_price=Decimal("55.0000"),
                new_price=Decimal("50.0000"),
                adjust_diff=Decimal("-5.0000"),
                adjust_reason="2026年度公立医院公用耗材价格动态联动调整通知",
                adjust_doc_no="杭卫医发【2026】05号",
                operator_name="赵振华(信息科)",
                effective_time=datetime(2026, 6, 1, 14, 0, 0)
            )
        ]
        db.add_all(price_logs)
        db.flush()

    # 5. 初始化用户与仓库细粒度授权矩阵 (SysUserWarehousePerm)
    if db.query(SysUserWarehousePerm).count() == 0:
        all_wh_nodes = db.query(SpdWarehouseNode).all()
        all_wh_codes = [w.warehouse_code for w in all_wh_nodes] if all_wh_nodes else [
            "WH_WEICAI", "WH_ZONGWU", "WH_XINXI", "WH_ZHUANXIANG", "WH_HOUQIN", "WH_CESHI", "WH_EQUIP", "WH_SEC_ORTHO", "WH_SEC_CARDIO"
        ]

        users = {u.username: u for u in db.query(SysUser).all()}
        perms = []

        # 1) admin (sys_admin)
        admin_user = users.get("admin")
        if admin_user:
            for code in all_wh_codes:
                perms.append(SysUserWarehousePerm(
                    user_id=admin_user.id,
                    username=admin_user.username,
                    warehouse_code=code,
                    can_view=1,
                    can_apply=1,
                    can_inbound=1,
                    can_outbound=1,
                    can_stocktake=1,
                    can_transfer=1,
                    updated_by="system"
                ))

        # 2) haocai (dept_manager)
        haocai_user = users.get("haocai")
        if haocai_user:
            for code in ["WH_WEICAI", "WH_ZONGWU", "WH_ZHUANXIANG", "WH_HOUQIN"]:
                perms.append(SysUserWarehousePerm(
                    user_id=haocai_user.id,
                    username=haocai_user.username,
                    warehouse_code=code,
                    can_view=1,
                    can_apply=1,
                    can_inbound=1,
                    can_outbound=1,
                    can_stocktake=1,
                    can_transfer=1,
                    updated_by="admin"
                ))

        # 3) shebei (dept_manager)
        shebei_user = users.get("shebei")
        if shebei_user:
            for code in ["WH_EQUIP", "WH_CESHI"]:
                perms.append(SysUserWarehousePerm(
                    user_id=shebei_user.id,
                    username=shebei_user.username,
                    warehouse_code=code,
                    can_view=1,
                    can_apply=1,
                    can_inbound=1,
                    can_outbound=1,
                    can_stocktake=1,
                    can_transfer=1,
                    updated_by="admin"
                ))

        # 4) nurse (secondary_user) - 严格仅限本科室二级库查看与申领
        nurse_user = users.get("nurse")
        if nurse_user:
            perms.append(SysUserWarehousePerm(
                user_id=nurse_user.id,
                username=nurse_user.username,
                warehouse_code="WH_SEC_ORTHO",
                can_view=1,
                can_apply=1,
                can_inbound=0,
                can_outbound=0,
                can_stocktake=0,
                can_transfer=0,
                updated_by="admin"
            ))
            perms.append(SysUserWarehousePerm(
                user_id=nurse_user.id,
                username=nurse_user.username,
                warehouse_code="WH_SEC_CARDIO",
                can_view=1,
                can_apply=1,
                can_inbound=0,
                can_outbound=0,
                can_stocktake=0,
                can_transfer=0,
                updated_by="admin"
            ))

        # 5) caiwu (finance_auditor)
        caiwu_user = users.get("caiwu")
        if caiwu_user:
            for code in all_wh_codes:
                perms.append(SysUserWarehousePerm(
                    user_id=caiwu_user.id,
                    username=caiwu_user.username,
                    warehouse_code=code,
                    can_view=1,
                    can_apply=0,
                    can_inbound=0,
                    can_outbound=0,
                    can_stocktake=0,
                    can_transfer=0,
                    updated_by="admin"
                ))

        db.add_all(perms)
        db.commit()

    logger.info("真实医院 SPD 四级字典、规格体系、供应商档案与用户-仓库 RBAC 细粒度权限矩阵注入完成")
    return True

