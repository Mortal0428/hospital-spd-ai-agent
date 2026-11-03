const fs = require('fs');

// 1. 修复 extended_spd_router.py
let ext = fs.readFileSync('backend/app/routers/extended_spd_router.py', 'utf8');
ext = ext.replace(
  'main_items = db.query(SpdMainInventory).filter(SpdMainInventory.current_stock > 0).all()',
  'main_items = db.query(SpdMainInventory).filter(SpdMainInventory.available_qty > 0).all()'
);
ext = ext.replace(
  'items_to_add.append((it.product_code, it.product_name, it.batch_no, float(it.unit_price), it.current_stock))',
  'items_to_add.append((it.product_code, it.product_name, it.batch_no, float(it.unit_price), it.available_qty))'
);
ext = ext.replace(
  `            m_inv.current_stock = max(0, item.actual_qty)
            m_inv.available_qty = max(0, item.actual_qty - m_inv.locked_stock)`,
  `            m_inv.available_qty = max(0, item.actual_qty)`
);
fs.writeFileSync('backend/app/routers/extended_spd_router.py', ext, 'utf8');
console.log('extended_spd_router.py fixed.');

// 2. 修复 main_warehouse_router.py
let mwr = fs.readFileSync('backend/app/routers/main_warehouse_router.py', 'utf8');
mwr = mwr.replace(
  'main_inv.current_stock -= item.quantity',
  'main_inv.available_qty = max(0, main_inv.available_qty - item.quantity)'
);
fs.writeFileSync('backend/app/routers/main_warehouse_router.py', mwr, 'utf8');
console.log('main_warehouse_router.py fixed.');
