const fs = require('fs');
const filePath = 'backend/app/routers/main_warehouse_router.py';
let content = fs.readFileSync(filePath, 'utf8');

const target = `    query = db.query(SpdRequisitionOrder)
    if status_filter:
        query = query.filter(SpdRequisitionOrder.req_status == status_filter)

    orders = query.order_by(SpdRequisitionOrder.created_at.desc()).all()`;

const replacement = `    query = db.query(SpdRequisitionOrder)
    if status_filter and status_filter != "ALL":
        query = query.filter(SpdRequisitionOrder.req_status == status_filter)

    if warehouse_code and warehouse_code != "ALL":
        if "ORTHO" in warehouse_code or "骨科" in warehouse_code:
            query = query.filter(SpdRequisitionOrder.apply_dept_name.like("%骨科%"))
        elif "CARDIO" in warehouse_code or "心内" in warehouse_code:
            query = query.filter(SpdRequisitionOrder.apply_dept_name.like("%心%"))
        else:
            query = query.filter(
                (SpdRequisitionOrder.apply_dept_name.like(f"%{warehouse_code}%"))
            )

    orders = query.order_by(SpdRequisitionOrder.created_at.desc()).all()`;

if (content.includes(target)) {
  content = content.replace(target, replacement);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Successfully updated list_main_requisitions in main_warehouse_router.py');
} else {
  console.error('Target not found in main_warehouse_router.py');
}
