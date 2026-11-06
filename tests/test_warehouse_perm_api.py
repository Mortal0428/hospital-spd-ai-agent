"""
全院多库藏分仓授权接口验证脚本
"""
import urllib.request
import json

def test_api():
    # 1. 查阅全量用户及其绑定的仓库
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/users")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        users = res.get("data", []) if isinstance(res, dict) else res
    
    print(f"Total users fetched: {len(users)}")
    for u in users:
        wh_names = [f"{w['warehouse_name']} ({w['warehouse_code']})" for w in u.get("authorized_warehouses", [])]
        print(f"User {u['id']} [{u['username']} - {u['real_name']} - {u['role_code']}]: {wh_names or '未分配'}")

    # 2. 为王建国 (id=2, 耗材科主管) 批量授权 4 大仓：卫材总仓、总务库、后勤库、高值专柜
    batch_payload = {
        "user_id": 2,
        "perms": [
            {
                "warehouse_code": "WH_WEICAI",
                "warehouse_name": "全院卫材耗材一级总仓",
                "warehouse_level": "MAIN_GROUP",
                "can_view": 1,
                "can_apply": 1,
                "can_inbound": 1,
                "can_outbound": 1,
                "can_stocktake": 1,
                "can_transfer": 1
            },
            {
                "warehouse_code": "WH_ZONGWU",
                "warehouse_name": "后勤总务库房",
                "warehouse_level": "MAIN_GROUP",
                "can_view": 1,
                "can_apply": 1,
                "can_inbound": 1,
                "can_outbound": 1,
                "can_stocktake": 1,
                "can_transfer": 1
            },
            {
                "warehouse_code": "WH_HOUQIN",
                "warehouse_name": "后勤物资保障库",
                "warehouse_level": "MAIN_GROUP",
                "can_view": 1,
                "can_apply": 1,
                "can_inbound": 1,
                "can_outbound": 1,
                "can_stocktake": 1,
                "can_transfer": 1
            },
            {
                "warehouse_code": "WH_ZHUANXIANG",
                "warehouse_name": "高值医用耗材智能专柜",
                "warehouse_level": "SPECIALTY_CABINET",
                "can_view": 1,
                "can_apply": 1,
                "can_inbound": 1,
                "can_outbound": 1,
                "can_stocktake": 1,
                "can_transfer": 1
            }
        ]
    }

    req_post = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/dict/user-warehouse-perms/batch",
        data=json.dumps(batch_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_post) as resp_post:
        post_res = json.loads(resp_post.read().decode("utf-8"))
    print("\nBatch save response count:", len(post_res))

    # 3. 再次查询用户列表，验证王建国是否携带这 4 个仓库
    with urllib.request.urlopen(req) as resp2:
        res2 = json.loads(resp2.read().decode("utf-8"))
        users2 = res2.get("data", []) if isinstance(res2, dict) else res2
    user2 = next((u for u in users2 if u["id"] == 2), None)
    if user2:
        wh2 = [w["warehouse_code"] for w in user2.get("authorized_warehouses", [])]
        print(f"\nUser 2 updated authorized_warehouses: {wh2}")
        assert set(wh2) == {"WH_WEICAI", "WH_ZONGWU", "WH_HOUQIN", "WH_ZHUANXIANG"}, "Warehouse mismatch!"
        print("PASS: User 2 successfully assigned 4 warehouses!")

if __name__ == "__main__":
    test_api()
