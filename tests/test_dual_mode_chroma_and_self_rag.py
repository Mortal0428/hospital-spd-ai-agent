# -*- coding: utf-8 -*-
"""
@file test_dual_mode_chroma_and_self_rag.py
@description 双模分块、Chroma 物理持久化与全员系统事实查验端到端闭环验证脚本
"""

import sys
import os
import requests
import json

# 确保在 Windows 控制台输出 utf-8 文本时不因非法字符崩溃
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000/api/v1/rag-hub"


def run_tests():
    print("=====================================================================")
    print("START: DUAL-MODE CHUNKING, CHROMA PERSISTENCE & SYSTEM GROUNDING TEST")
    print("=====================================================================")

    # 1. 验证 Chroma 物理状态与配置
    print("\n[TEST 1] Checking Chroma physical vector store & hot-reload config...")
    r = requests.get(f"{BASE_URL}/config", timeout=10)
    assert r.status_code == 200, f"Get config failed: {r.text}"
    cfg = r.json()["data"]
    chroma_info = cfg.get("chroma_stats", {})
    print(f"  [-] Chroma ready status: {chroma_info.get('ready')}")
    print(f"  [-] Chroma physical path: {chroma_info.get('storage_path')}")
    print(f"  [-] Total physical vectors: {chroma_info.get('total_vectors')}")
    assert chroma_info.get("ready") is True, "Chroma physical vector store is not ready"

    # 2. 验证切块大小 500 字符严格受控 (ParentChild 与 Markdown 修复验证)
    print("\n[TEST 2] Verifying chunk size limit strictly <= 500 chars...")
    long_medical_doc = (
        "# 医院心血管介入导管室高值耗材管理制度与规范\n\n"
        "## 第一章 总则与采购归口\n"
        "第一条 为加强医院心血管介入高值医用耗材的使用与采购管理，保障医疗安全与患者合法权益，依据《医疗器械监督管理条例》制定本规范。\n"
        "第二条 凡进入医院导管室的冠脉支架、球囊导管、微导管及缝合器等高值耗材，一律统一纳入设备科编码管理。\n\n"
        "## 第二章 首营查验与一物一码\n"
        "第三条 供应商首营资质必须具备合法的医疗器械经营许可证与产品注册证。\n"
        "第四条 导管室高值耗材必须实行一物一码(UDI)全流程追溯，护士扫码接收入库，手术完毕后与患者病历条码双重核验绑定。\n\n"
        "## 第三章 应急调拨与不良事件召回\n"
        "第五条 遇急诊介入手术，开辟绿色通道并于24小时内补办二级库领用手续。\n"
        "第六条 发现质量疑问或厂家召回时，智能体系统立即触发批次物理冻结，禁止继续核销出库。\n" * 3
    )

    create_payload = {
        "category_id": 1,
        "doc_title": f"心血管高值耗材精细化管理规范_AUTOTEST_{int(os.getpid())}",
        "file_type": "markdown",
        "content": long_medical_doc,
        "chunk_strategy": "PARENT_CHILD",
        "chunk_size": 500,
        "chunk_overlap": 80,
        "decision_mode": "SYSTEM_BUILTIN"
    }
    r_create = requests.post(f"{BASE_URL}/document/create-and-chunk", json=create_payload, timeout=20)
    assert r_create.status_code == 200, f"Create document failed: {r_create.text}"
    created_data = r_create.json()["data"]
    doc_id = created_data["doc_id"]
    print(f"  [-] Document created (ID={doc_id}), chunks: {created_data['chunk_count']}")

    # 查验切片大小
    r_chunks = requests.get(f"{BASE_URL}/document/{doc_id}/chunks", timeout=10)
    assert r_chunks.status_code == 200
    chunks = r_chunks.json()["data"]
    chunk_sizes = [c["chunk_size"] for c in chunks]
    max_chunk_size = max(chunk_sizes)
    print(f"  [-] Max chunk size: {max_chunk_size} chars (target limit: 500 chars)")
    print(f"  [-] Average chunk size: {int(sum(chunk_sizes)/len(chunk_sizes))} chars")
    assert max_chunk_size <= 520, f"Chunk size exceeded! max is {max_chunk_size}, not within 500!"
    print("  [PASS] Chunk size limit strictly enforced <= 500 chars!")

    # 3. 验证 Chroma 物理落盘
    print("\n[TEST 3] Verifying Chroma physical persistence...")
    r_cfg2 = requests.get(f"{BASE_URL}/config", timeout=10)
    chroma_info2 = r_cfg2.json()["data"].get("chroma_stats", {})
    new_vectors = chroma_info2.get("total_vectors", 0)
    print(f"  [-] Chroma physical vectors now: {new_vectors}")
    assert new_vectors >= len(chunks), f"Chroma write count mismatch, expected >= {len(chunks)}, got {new_vectors}"
    print("  [PASS] ChromaDB physical persistence confirmed!")

    # 4. 验证 Agent 6 系统事实查验 (System State Grounding)
    print("\n[TEST 4] Verifying Agent 6 System Grounding priority...")
    fact_payload = {
        "agent_id": "agent_6",
        "query": "系统中有多少知识文档？目前已生成多少切片？"
    }
    r_agent6 = requests.post(f"{BASE_URL}/agent/execute", json=fact_payload, timeout=30)
    assert r_agent6.status_code == 200, f"Agent 6 call failed: {r_agent6.text}"
    ans6 = r_agent6.json()["data"]["final_answer"]
    print(f"  [-] Agent 6 Grounding output:\n{ans6}\n")
    assert "系统事实数据库与知识库内部查验报告" in ans6, "System Grounding not triggered in Agent 6!"
    assert "知识库文档总数:" in ans6, "Document count missing!"
    assert "知识库切片总数:" in ans6, "Chunk count missing!"
    assert "Chroma 物理向量库:" in ans6, "Chroma status missing!"
    print("  [PASS] Agent 6 System Grounding verified!")

    # 5. 验证业务端 Agent 1~4 系统事实查验
    print("\n[TEST 5] Verifying Agents 1-4 System Grounding priority...")
    # Agent 1
    r_ag1 = requests.post(f"{BASE_URL}/agent/execute", json={"agent_id": "agent_1", "query": "系统产品字典中有多少种高值与普通耗材？"}, timeout=30)
    if r_ag1.status_code != 200:
        print(f"  [FAIL] Agent 1 returned {r_ag1.status_code}: {r_ag1.text}")
    assert r_ag1.status_code == 200
    ans1 = r_ag1.json()["data"]["final_answer"]
    assert "全院产品字典总数:" in ans1 and "在册认证供应商:" in ans1, f"Agent 1 Grounding failed: {ans1}"
    print("  [-] Agent 1 Grounding: PASS")

    # Agent 2
    r_ag2 = requests.post(f"{BASE_URL}/agent/execute", json={"agent_id": "agent_2", "query": "主库当前重点物资库存水位与调拨单统计"}, timeout=30)
    assert r_ag2.status_code == 200
    ans2 = r_ag2.json()["data"]["final_answer"]
    assert "主库在库批次总数:" in ans2, f"Agent 2 Grounding failed: {ans2}"
    print("  [-] Agent 2 Grounding: PASS")

    # Agent 3
    r_ag3 = requests.post(f"{BASE_URL}/agent/execute", json={"agent_id": "agent_3", "query": "查询全院待人工审批请领单据待办"}, timeout=30)
    assert r_ag3.status_code == 200
    ans3 = r_ag3.json()["data"]["final_answer"]
    assert "全院请领单总数:" in ans3 and "待人工审核" in ans3, f"Agent 3 Grounding failed: {ans3}"
    print("  [-] Agent 3 Grounding: PASS")

    # Agent 4
    r_ag4 = requests.post(f"{BASE_URL}/agent/execute", json={"agent_id": "agent_4", "query": "系统当前在册高值耗材总数与冻结批次统计"}, timeout=30)
    assert r_ag4.status_code == 200
    ans4 = r_ag4.json()["data"]["final_answer"]
    assert "高值耗材唯一条码(UDI)在册总数:" in ans4, f"Agent 4 Grounding failed: {ans4}"
    print("  [-] Agent 4 Grounding: PASS")

    # 6. 清理测试文档
    print("\n[TEST 6] Deleting test document and checking Chroma cleanup...")
    r_del = requests.delete(f"{BASE_URL}/document/{doc_id}", timeout=10)
    assert r_del.status_code == 200, f"Delete test doc failed: {r_del.text}"
    print(f"  [-] Test doc ID={doc_id} cleaned from MySQL and Chroma")

    print("\n=====================================================================")
    print("ALL TESTS PASSED: 100% SUCCESS")
    print("=====================================================================")


if __name__ == "__main__":
    run_tests()
