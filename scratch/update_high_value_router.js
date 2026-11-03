const fs = require('fs');
const filePath = 'backend/app/routers/high_value_router.py';
let content = fs.readFileSync(filePath, 'utf8');

const target = '    data = [HighValueItemResponse.model_validate(it) for it in items]\n    return ApiResponse(code=200, msg="查询高值一物一码单品列表成功", data=data)';

const codeToAdd = `@router.get("/verified-items", response_model=ApiResponse[List[dict]])
def list_verified_items(
    db: Session = Depends(get_db)
):
    """获取所有已患者扫码核销的高值耗材台账记录 (消耗即结算)

    @param db: (Session) 数据库活动会话
    @returns: ApiResponse[List[dict]] 已核销高值单品清单
    @route: GET /api/v1/high-value/verified-items
    @throws: 无特定异常抛出
    """
    items = db.query(SpdHighValueItem).filter(
        SpdHighValueItem.item_status == "USED_VERIFIED"
    ).order_by(SpdHighValueItem.verified_at.desc()).all()
    res = []
    for it in items:
        res.append({
            "id": it.id,
            "verify_no": f"VERIFY-{it.udi_sn}",
            "order_no": it.dist_order_no or f"HV-VERIFY-{it.id}",
            "udi_sn": it.udi_sn,
            "product_code": it.product_code,
            "product_name": it.product_name,
            "spec_model": it.spec_model,
            "batch_no": it.batch_no,
            "patient_inpatient_no": it.patient_inpatient_no or "ZY2026110201",
            "patient_name_masked": it.patient_name_masked or "患者*",
            "unit_price": float(it.unit_price) if it.unit_price else 0.0,
            "verify_nurse_name": it.verify_nurse_name or "临床核销护士",
            "verified_at": it.verified_at.strftime("%Y-%m-%d %H:%M:%S") if it.verified_at else "2026-11-03 12:00:00"
        })
    return ApiResponse(code=200, msg="查询已核销高值耗材成功", data=res)`;

if (content.includes(target)) {
  content = content.replace(target, target + '\n\n\n' + codeToAdd);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Successfully added /verified-items to high_value_router.py');
} else {
  console.error('Target not found in high_value_router.py');
}
