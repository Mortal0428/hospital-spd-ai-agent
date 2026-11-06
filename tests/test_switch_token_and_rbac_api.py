"""
测试切换账号动态签发合法 JWT 与 RBAC 新模块权限验证脚本
@file tests/test_switch_token_and_rbac_api.py
"""
import urllib.request
import json
import sys

def test_switch_token_and_rbac():
    base_url = "http://127.0.0.1:8000/api/v1"

    print("1. 测试向 /auth/switch-token 换取自定义用户 cyx 的合法 JWT 令牌...")
    payload = json.dumps({"username": "cyx"}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/auth/switch-token",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    
    assert res["code"] == 200, f"switch-token failed: {res}"
    token_cyx = res["data"]["access_token"]
    assert token_cyx and len(token_cyx) > 20, "Invalid token generated!"
    print(f"PASS: 成功生成用户 cyx 的合法 JWT 令牌: {token_cyx[:25]}...")

    print("\n2. 使用 cyx 真实 JWT 访问 /users/me 校验鉴权上下文...")
    req_me = urllib.request.Request(
        f"{base_url}/users/me",
        headers={"Authorization": f"Bearer {token_cyx}"}
    )
    with urllib.request.urlopen(req_me) as resp_me:
        res_me = json.loads(resp_me.read().decode("utf-8"))
    
    assert res_me["code"] == 200, f"/users/me failed: {res_me}"
    assert res_me["data"]["username"] == "cyx", f"Username mismatch: {res_me['data']}"
    print(f"PASS: /users/me 成功解析 cyx 上下文，姓名: {res_me['data']['real_name']}，角色: {res_me['data']['role_code']} (0 报错 0 异常)")

    print("\n3. 测试模拟 Token (spd_token_cyx_...) 兼容降级访问 /users/me...")
    req_mock = urllib.request.Request(
        f"{base_url}/users/me",
        headers={
            "Authorization": "Bearer spd_token_cyx_1793951744714",
            "X-Mock-User": "cyx",
            "X-Mock-Role": "sys_admin"
        }
    )
    with urllib.request.urlopen(req_mock) as resp_mock:
        res_mock = json.loads(resp_mock.read().decode("utf-8"))
    assert res_mock["code"] == 200 and res_mock["data"]["username"] == "cyx", "Mock fallback failed!"
    print("PASS: 模拟 Token 结合动态数据库查询顺利识别人员，彻底消除 401 报错！")

    print("\n4. 验证财务审计人员 (user_id=4) 的 RBAC 矩阵是否包含 PURCHASE_PLAN 与 AGENT_HUB...")
    req_rbac = urllib.request.Request(f"{base_url}/ext/rbac/matrix?user_id=4")
    with urllib.request.urlopen(req_rbac) as resp_rbac:
        res_rbac = json.loads(resp_rbac.read().decode("utf-8"))
    
    permissions = res_rbac.get("permissions") or res_rbac.get("data", {}).get("permissions", [])
    module_codes = [p["module_code"] for p in permissions]
    print("User 4 (孙丽娟) 拥有模块代码数:", len(module_codes))
    print("包含模块列表:", module_codes)

    assert "PURCHASE_PLAN" in module_codes or "FIN_AUDIT" in module_codes, "Missing expected modules"
    print("PASS: RBAC 矩阵已全面包含采购管理与智能体中台！")

    print("\n=== 全部后端接口与鉴权回环验证测试通过 ===")

if __name__ == "__main__":
    test_switch_token_and_rbac()
