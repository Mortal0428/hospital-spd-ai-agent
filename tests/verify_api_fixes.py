import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Headers with login token for sys_admin (id=1)
# Create a valid token using backend auth
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.core.security import create_access_token

token = create_access_token(data={"sub": "admin", "role": "sys_admin", "user_id": 1, "real_name": "赵振华"})
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"=== 1. 测试多明细采购入库 (验证 1062 唯一键冲突已彻底解决) ===")
inbound_payload = {
    "warehouse_code": "WH_WEICAI",
    "delivery_order_no": "PS202611039901",
    "invoice_no": "FP202611039901",
    "delivery_person": "张师傅",
    "supplier_name": "南昌远达医用器材有限公司",
    "auto_approve": True,
    "remark": "自动化多明细入库测试验证",
    "items": [
        {
            "spec_code": "936010100024055499",
            "product_name": "医用氧气123",
            "spec_name": "40L 剑涛特供型",
            "batch_no": "B20261103A",
            "expiry_date": "2029-12-31",
            "quantity": 10,
            "unit_price": 52.0,
            "total_amount": 520.0
        },
        {
            "spec_code": "936010100024055500",
            "product_name": "医用氧气123",
            "spec_name": "15L 医用级减压瓶",
            "batch_no": "B20261103B",
            "expiry_date": "2029-12-31",
            "quantity": 5,
            "unit_price": 55.0,
            "total_amount": 275.0
        },
        {
            "spec_code": "936010100024055517",
            "product_name": "医用氧气123",
            "spec_name": "40L 纯度≥99.5%",
            "batch_no": "B20261103C",
            "expiry_date": "2029-12-31",
            "quantity": 8,
            "unit_price": 45.0,
            "total_amount": 360.0
        }
    ]
}
r1 = requests.post(f"{BASE_URL}/main-warehouse/purchase-inbound", json=inbound_payload, headers=headers)
print(f"Status Code: {r1.status_code}")
print(f"Response: {r1.json()}")
assert r1.status_code == 200, f"Purchase inbound failed: {r1.text}"
print("=> 采购入库 3 行明细插入测试 PASSED!\n")

print(f"=== 2. 测试 RBAC 细粒度批量赋权 (验证 1048 列非空错误已彻底解决) ===")
rbac_payload = {
    "user_id": 1,
    "modules": ["GEN_DISPATCH", "GEN_STOCKTAKE", "HV_UDI_CODE"],
    "action_keys": ["can_view", "can_create", "can_edit", "can_delete", "can_second_confirm", "can_approve", "can_print"],
    "action_value": 1,
    "operator_name": "赵振华"
}
r2 = requests.post(f"{BASE_URL}/ext/rbac/batch-grant", json=rbac_payload, headers=headers)
print(f"Status Code: {r2.status_code}")
print(f"Response: {r2.json()}")
assert r2.status_code == 200, f"RBAC batch grant failed: {r2.text}"
print("=> RBAC 批量赋权测试 PASSED!\n")

print(f"=== 3. 测试高值全生命周期单据检索 (验证 404 已彻底消除) ===")
r3 = requests.get(f"{BASE_URL}/high-value/lifecycle-orders", headers=headers)
print(f"Status Code: {r3.status_code}")
print(f"Total Lifecycle Orders: {len(r3.json().get('data', []))}")
assert r3.status_code == 200, f"Lifecycle orders failed: {r3.text}"
print("=> 高值全生命周期单据查询测试 PASSED!\n")

print(f"=== 4. 测试独立盘点计划 GET 与 POST (验证 404 已彻底消除) ===")
r4_get = requests.get(f"{BASE_URL}/ext/stocktake-plans?scope=MAIN&warehouse_code=WH_WEICAI", headers=headers)
print(f"GET Status Code: {r4_get.status_code}")
print(f"Existing Plans: {len(r4_get.json().get('data', []))}")
assert r4_get.status_code == 200, f"Stocktake plans GET failed: {r4_get.text}"

plan_create_payload = {
    "warehouse_code": "WH_WEICAI",
    "warehouse_name": "卫材库房",
    "plan_name": "2026年11月份自动化测试盘点计划",
    "plan_date": "2026-11-03",
    "month_period": "2026-11",
    "operator_name": "赵振华",
    "remark": "自动化测试平账底表拉取"
}
r4_post = requests.post(f"{BASE_URL}/ext/stocktake-plans", json=plan_create_payload, headers=headers)
print(f"POST Status Code: {r4_post.status_code}")
print(f"POST Response: {r4_post.json()}")
assert r4_post.status_code == 200, f"Stocktake plans POST failed: {r4_post.text}"
print("=> 独立盘点计划创建与底表拉取测试 PASSED!\n")

print("ALL 4 BACKEND BUG FIXES VERIFIED SUCCESSFULLY!")
