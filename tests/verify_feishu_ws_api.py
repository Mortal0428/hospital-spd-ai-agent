# -*- coding: utf-8 -*-
"""
@file verify_feishu_ws_api.py
@description 飞书官方 SDK 长连接 API 自动化回归验证
测试：
1. GET /api/v1/rag-hub/feishu/ws-status: 检查连接状态、运行时长、订阅事件
2. POST /api/v1/rag-hub/feishu/ws-restart: 检查长连接热重连能力与状态回传
"""

import sys
import os
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_ws_status_and_restart():
    print("=====================================================================")
    print("START: TESTING FEISHU WS APIS")
    print("=====================================================================")

    # 1. 查询状态
    url_status = f"{BASE_URL}/rag-hub/feishu/ws-status"
    res1 = requests.get(url_status, timeout=10)
    assert res1.status_code == 200, f"状态接口返回非200: {res1.status_code}"
    data1 = res1.json()
    print("1. 获取飞书长连接状态响应:", data1)
    assert data1["code"] == 200
    assert data1["data"]["connected"] is True
    assert "im.message.receive_v1" in data1["data"]["subscribed_events"]
    print("  [PASS] 长连接在线状态验证通过，connected=True，ConnID =", data1["data"]["conn_id"])

    # 2. 触发重启
    url_restart = f"{BASE_URL}/rag-hub/feishu/ws-restart"
    res2 = requests.post(url_restart, timeout=15)
    assert res2.status_code == 200, f"重启接口返回非200: {res2.status_code}"
    data2 = res2.json()
    print("2. 触发飞书长连接重启响应:", data2)
    assert data2["code"] == 200
    assert data2["data"]["success"] is True
    print("  [PASS] 长连接重启指令已下发成功！")

    print("=====================================================================")
    print("ALL FEISHU WS API TESTS PASSED!")
    print("=====================================================================")

if __name__ == "__main__":
    test_ws_status_and_restart()
