# -*- coding: utf-8 -*-
import sys
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

r = requests.post(
    "http://127.0.0.1:8000/agent/execute",
    json={"agent_id": "agent_5", "query": "2026-11月份全院多科室耗材财务精算与合规审计"},
    timeout=30
)
res = r.json()
print("HTTP Status:", r.status_code)
if "data" in res:
    ans = res["data"]["final_answer"]
    matched = "主库向各临床二级库累计调拨出库" in ans
    print(f"Keyword '主库向各临床二级库累计调拨出库' matched: {matched}")
    print("Answer excerpt:\n", ans[:300])
else:
    print("Error response:", res)
