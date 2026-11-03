const fs = require('fs');
const filePath = 'backend/app/routers/main_warehouse_router.py';
let content = fs.readFileSync(filePath, 'utf8');

const target = `    # 2. 检索主库总仓批次库存
    main_wh_codes = {"WH_WEICAI", "WH_EQUIP", "WH_ZONGWU", "WH_XINXI", "WH_ZHUANXIANG", "WH_HOUQIN", "WH_CESHI"} & filter_wh_codes
    if main_wh_codes:
        main_invs = db.query(SpdMainInventory).filter(SpdMainInventory.current_stock > 0).all()
        for inv in main_invs:
            wh_code = "WH_WEICAI" if inv.main_dept_code == "CONSUMABLE_DEPT" else "WH_EQUIP"
            if wh_code in filter_wh_codes:
                days_left = (inv.expiry_date - today).days if inv.expiry_date else 999
                is_near = 1 if days_left <= 180 else 0
                results.append({
                    "id": f"MAIN-{inv.id}",
                    "warehouse_code": wh_code,
                    "warehouse_name": all_wh_nodes.get(wh_code, None).warehouse_name if all_wh_nodes.get(wh_code) else ("卫材主库" if wh_code == "WH_WEICAI" else "设备库房"),
                    "warehouse_type": "院级归口主仓",
                    "product_code": inv.product_code,
                    "product_name": inv.product_name,
                    "spec_name": "标准包装规格",
                    "unit_name": "件",
                    "batch_no": inv.batch_no,
                    "expiry_date": str(inv.expiry_date),
                    "days_left": days_left,
                    "is_near_expiry": is_near,
                    "current_qty": inv.current_stock,
                    "available_qty": inv.available_qty,
                    "locked_qty": inv.locked_stock,
                    "unit_price": float(inv.unit_price),
                    "total_amount": float(inv.unit_price * Decimal(str(inv.current_stock))),
                    "shelf_location": inv.shelf_location or "主仓A区01架",
                    "source_dept": "耗材科主库" if inv.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库"
                })`;

const replacement = `    # 2. 检索主库总仓批次库存
    main_wh_codes = {"WH_WEICAI", "WH_EQUIP", "WH_ZONGWU", "WH_XINXI", "WH_ZHUANXIANG", "WH_HOUQIN", "WH_CESHI"} & filter_wh_codes
    if main_wh_codes:
        main_invs = db.query(SpdMainInventory).filter(SpdMainInventory.available_qty > 0).all()
        for inv in main_invs:
            wh_code = "WH_WEICAI" if inv.main_dept_code == "CONSUMABLE_DEPT" else "WH_EQUIP"
            if wh_code in filter_wh_codes:
                days_left = (inv.expiry_date - today).days if inv.expiry_date else 999
                is_near = 1 if days_left <= 180 else 0
                results.append({
                    "id": f"MAIN-{inv.id}",
                    "warehouse_code": wh_code,
                    "warehouse_name": all_wh_nodes.get(wh_code, None).warehouse_name if all_wh_nodes.get(wh_code) else ("卫材主库" if wh_code == "WH_WEICAI" else "设备库房"),
                    "warehouse_type": "院级归口主仓",
                    "product_code": inv.product_code,
                    "product_name": inv.product_name,
                    "spec_name": "标准包装规格",
                    "unit_name": "件",
                    "batch_no": inv.batch_no,
                    "expiry_date": str(inv.expiry_date),
                    "days_left": days_left,
                    "is_near_expiry": is_near,
                    "current_qty": inv.available_qty,
                    "available_qty": inv.available_qty,
                    "locked_qty": 0,
                    "unit_price": float(inv.unit_price),
                    "total_amount": float(inv.unit_price * Decimal(str(inv.available_qty))),
                    "shelf_location": inv.shelf_location or "主仓A区01架",
                    "source_dept": "耗材科主库" if inv.main_dept_code == "CONSUMABLE_DEPT" else "设备科主库"
                })`;

if (content.includes(target)) {
  content = content.replace(target, replacement);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Successfully fixed SpdMainInventory fields in main_warehouse_router.py');
} else {
  console.error('Target not found in main_warehouse_router.py');
}
