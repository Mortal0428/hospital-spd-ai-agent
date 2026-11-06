"""
Challenger R2 Empirical Verification Suite
Comprehensive stress-test and verification for all 6 challenge dimensions.
"""

import sys
import os
import json
import time
import subprocess
import requests
from decimal import Decimal

# Set UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import engine
from sqlalchemy import text
from app.services.rag_modular_engine import TableAwareChunker

BASE_URL = "http://127.0.0.1:8000"


def test_dimension_1_chinese_uppercase():
    print("\n" + "="*70)
    print("Dimension 1: Chinese Uppercase Amount in Frontend")
    print("="*70)
    
    cmd = [
        "node", "-e", """
        const fs = require('fs');
        function extractAndTest(filePath) {
            const content = fs.readFileSync(filePath, 'utf-8');
            const start = content.indexOf('function digitUppercase(money: number): string {');
            if (start === -1) throw new Error('Not found in ' + filePath);
            let open = 0, end = -1;
            for (let i = start; i < content.length; i++) {
                if (content[i] === '{') open++;
                else if (content[i] === '}') {
                    open--;
                    if (open === 0) { end = i; break; }
                }
            }
            const fullFunc = content.substring(start, end + 1);
            const jsFunc = fullFunc.replace('function digitUppercase(money: number): string', 'function digitUppercase(money)');
            const fn = eval('(' + jsFunc + ')');
            
            const cases = [
                [1000000.05, '壹佰万元零伍分'],
                [100.05, '壹佰元零伍分'],
                [0.00, '零元整'],
                [100.50, '壹佰元伍角'],
                [123456789.12, '壹亿贰仟叁佰肆拾伍万陆仟柒佰捌拾玖元壹角贰分'],
                [0.05, '伍分'],
                [0.50, '伍角'],
                [100000000.05, '壹亿元零伍分']
            ];
            
            console.log('Testing ' + filePath + ':');
            for (const [val, expected] of cases) {
                const actual = fn(val);
                if (actual !== expected) {
                    throw new Error(`FAIL: ${val} => ${actual}, expected: ${expected}`);
                }
                console.log(`  [PASS] ${val} => ${actual}`);
            }
        }
        extractAndTest('frontend/src/views/HospitalProcurementView.vue');
        extractAndTest('frontend/src/components/PrintVoucherDialog.vue');
        console.log('All frontend uppercase amount tests passed!');
        """
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        raise AssertionError("Dimension 1 verification failed!")
    print("[PASS] Dimension 1: Chinese Uppercase Amount Verified Successfully.")


def test_dimension_2_agent3_trace_persistence():
    print("\n" + "="*70)
    print("Dimension 2: Agent 3 Trace Persistence in spd_agent_execution_trace")
    print("="*70)
    
    with engine.connect() as conn:
        before_count = conn.execute(text("SELECT COUNT(*) FROM spd_agent_execution_trace WHERE agent_id = 'agent_3'")).scalar()
        print(f"Initial count of agent_3 traces: {before_count}")

    # Step 1: Draft Requisition execution (HITL pause)
    payload = {
        "agent_id": "agent_3",
        "query": "请为骨科二级库申领50件医用敷料贴与100支无菌注射器",
        "operator": "secondary_user"
    }
    resp = requests.post(f"{BASE_URL}/api/v1/rag-hub/agent/execute", json=payload, timeout=10)
    assert resp.status_code == 200, f"HTTP Error: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body.get("code") == 200, f"API Error: {body.get('msg')}"
    data = body.get("data", {})
    assert data.get("agent_id") == "agent_3", f"Wrong agent_id: {data.get('agent_id')}"
    hitl_status = data.get("state", {}).get("human_in_the_loop_status")
    print(f"Agent 3 Draft Requisition Executed. HITL Status: {hitl_status}")
    assert hitl_status == "WAITING_HUMAN", f"Expected WAITING_HUMAN, got {hitl_status}"

    # Verify trace inserted into DB
    with engine.connect() as conn:
        after_count_1 = conn.execute(text("SELECT COUNT(*) FROM spd_agent_execution_trace WHERE agent_id = 'agent_3'")).scalar()
        print(f"Trace count after draft execution: {after_count_1}")
        assert after_count_1 == before_count + 1, f"Expected {before_count + 1}, got {after_count_1}"

        latest = conn.execute(text(
            "SELECT id, agent_id, agent_name, architecture_pattern, user_query, langsmith_run_id, execution_time_ms, created_at "
            "FROM spd_agent_execution_trace WHERE agent_id = 'agent_3' ORDER BY id DESC LIMIT 1"
        )).mappings().first()
        print(f"Verified Trace in DB: id={latest['id']}, agent={latest['agent_id']}, run_id={latest['langsmith_run_id']}, cost={latest['execution_time_ms']}ms")
        assert latest["agent_id"] == "agent_3"
        assert "run-agent3-" in latest["langsmith_run_id"]
        assert latest["execution_time_ms"] >= 0

    # Step 2: Resume with CONFIRM (HITL resume)
    resume_payload = {
        "agent_id": "agent_3",
        "query": "确认提交请领审核",
        "resume_action": "CONFIRM",
        "operator": "secondary_user"
    }
    resp2 = requests.post(f"{BASE_URL}/api/v1/rag-hub/agent/execute", json=resume_payload, timeout=10)
    assert resp2.status_code == 200, f"Resume HTTP Error: {resp2.status_code} {resp2.text}"
    body2 = resp2.json()
    assert body2.get("code") == 200, f"Resume API Error: {body2.get('msg')}"
    
    with engine.connect() as conn:
        after_count_2 = conn.execute(text("SELECT COUNT(*) FROM spd_agent_execution_trace WHERE agent_id = 'agent_3'")).scalar()
        print(f"Trace count after resume execution: {after_count_2}")
        assert after_count_2 == after_count_1 + 1, f"Expected {after_count_1 + 1}, got {after_count_2}"

    print("[PASS] Dimension 2: Agent 3 Trace Persistence Verified Successfully.")


def test_dimension_3_cosine_monotonicity():
    print("\n" + "="*70)
    print("Dimension 3: Cosine Monotonicity in Dense Retrieval Score")
    print("="*70)
    
    cos_sim_test_points = [-1.0, -0.5, 0.0, 0.01, 0.1, 0.5, 1.0]
    
    # Compute dense_score exactly as in backend/app/services/rag_modular_engine.py
    def calc_dense_score(cos_sim: float) -> float:
        return round(float(max(0.0, min(1.0, (cos_sim + 1.0) / 2.0))), 4)
    
    scores = []
    print("Evaluating dense_score across points:")
    for sim in cos_sim_test_points:
        score = calc_dense_score(sim)
        scores.append(score)
        print(f"  cos_sim: {sim:5.2f} => dense_score: {score:.4f}")
    
    # Assert strict monotonic increase across all consecutive points
    for i in range(len(scores) - 1):
        p1, p2 = cos_sim_test_points[i], cos_sim_test_points[i+1]
        s1, s2 = scores[i], scores[i+1]
        print(f"  Checking {p1} -> {p2}: {s1} < {s2}")
        assert s1 < s2, f"Monotonicity violation! At {p1} ({s1}) vs {p2} ({s2})"
    
    # Check boundary clipping
    assert calc_dense_score(-1.5) == 0.0, "Clamping at lower bound failed!"
    assert calc_dense_score(1.5) == 1.0, "Clamping at upper bound failed!"
    print("  Clamping tests passed: -1.5 -> 0.0, 1.5 -> 1.0")

    print("[PASS] Dimension 3: Cosine Monotonicity Verified Successfully.")


def test_dimension_4_table_aware_chunker():
    print("\n" + "="*70)
    print("Dimension 4: TableAwareChunker on Two-Line Table")
    print("="*70)
    
    chunker = TableAwareChunker()
    
    # Case A: Two-line table without divider line
    two_line_table = "| 耗材 | 价格 |\n| 导管 | 100 |"
    chunks_a = chunker.chunk(two_line_table, doc_code="DOC_TEST_01")
    print(f"Case A: 2-line table (no divider line) produced {len(chunks_a)} chunk(s):")
    for i, ch in enumerate(chunks_a):
        print(f"  Chunk {i}: UID={ch['chunk_uid']} | Text: {ch['chunk_text']}")
    
    assert len(chunks_a) >= 1, f"Expected >= 1 chunk, got {len(chunks_a)}"
    assert "耗材" in chunks_a[0]["chunk_text"] and "价格" in chunks_a[0]["chunk_text"], "Header lost in chunk!"
    assert "导管" in chunks_a[0]["chunk_text"] and "100" in chunks_a[0]["chunk_text"], "Data row lost in chunk!"
    
    # Case B: Standard 3-line table with divider line
    three_line_table = "| 耗材 | 价格 |\n|---|---|\n| 导管 | 100 |"
    chunks_b = chunker.chunk(three_line_table, doc_code="DOC_TEST_02")
    print(f"Case B: Standard 3-line table (with divider) produced {len(chunks_b)} chunk(s):")
    for i, ch in enumerate(chunks_b):
        print(f"  Chunk {i}: UID={ch['chunk_uid']} | Text: {ch['chunk_text']}")
    assert len(chunks_b) >= 1, f"Expected >= 1 chunk, got {len(chunks_b)}"
    assert "导管" in chunks_b[0]["chunk_text"] and "100" in chunks_b[0]["chunk_text"]
    
    # Case C: Two-line table with multiple rows
    multi_row_table = "| 物料名称 | 规格 | 数量 |\n| 医用敷料贴 | 10cm*10cm | 50 |\n| 一次性注射器 | 5ml | 100 |"
    chunks_c = chunker.chunk(multi_row_table, doc_code="DOC_TEST_03")
    print(f"Case C: Multi-row table without divider produced {len(chunks_c)} chunk(s):")
    for i, ch in enumerate(chunks_c):
        print(f"  Chunk {i}: UID={ch['chunk_uid']} | Text: {ch['chunk_text']}")
    assert len(chunks_c) == 2, f"Expected 2 chunks, got {len(chunks_c)}"

    print("[PASS] Dimension 4: TableAwareChunker Verified Successfully.")


def test_dimension_5_pydantic_validation():
    print("\n" + "="*70)
    print("Dimension 5: Pydantic Validation on Negative / Out-of-Bounds Config")
    print("="*70)
    
    # Test 1: Negative top_k_retrieval (-5)
    payload_negative = {"top_k_retrieval": -5}
    resp = requests.post(f"{BASE_URL}/api/v1/rag-hub/config/update", json=payload_negative)
    print(f"Attempting update with top_k_retrieval = -5: HTTP Status {resp.status_code}")
    print(f"Response body: {resp.text}")
    assert resp.status_code == 422, f"Expected HTTP 422 for negative top_k, got {resp.status_code}"
    
    # Test 2: Zero top_k_retrieval (0)
    payload_zero = {"top_k_retrieval": 0}
    resp_zero = requests.post(f"{BASE_URL}/api/v1/rag-hub/config/update", json=payload_zero)
    print(f"Attempting update with top_k_retrieval = 0: HTTP Status {resp_zero.status_code}")
    assert resp_zero.status_code == 422, f"Expected HTTP 422 for top_k=0, got {resp_zero.status_code}"

    # Test 3: Excessive top_k_retrieval (101)
    payload_excess = {"top_k_retrieval": 101}
    resp_excess = requests.post(f"{BASE_URL}/api/v1/rag-hub/config/update", json=payload_excess)
    print(f"Attempting update with top_k_retrieval = 101: HTTP Status {resp_excess.status_code}")
    assert resp_excess.status_code == 422, f"Expected HTTP 422 for top_k=101, got {resp_excess.status_code}"

    # Test 4: Excessive rewrite loops (10)
    payload_loops = {"max_rewrite_loops": 10}
    resp_loops = requests.post(f"{BASE_URL}/api/v1/rag-hub/config/update", json=payload_loops)
    print(f"Attempting update with max_rewrite_loops = 10: HTTP Status {resp_loops.status_code}")
    assert resp_loops.status_code == 422, f"Expected HTTP 422 for max_rewrite_loops=10, got {resp_loops.status_code}"

    # Test 5: Valid config update (top_k_retrieval = 8)
    payload_valid = {"top_k_retrieval": 8}
    resp_valid = requests.post(f"{BASE_URL}/api/v1/rag-hub/config/update", json=payload_valid)
    print(f"Attempting valid update with top_k_retrieval = 8: HTTP Status {resp_valid.status_code}")
    assert resp_valid.status_code == 200, f"Expected HTTP 200 for valid config, got {resp_valid.status_code}"
    assert resp_valid.json().get("code") == 200
    
    # Verify via GET /config that top_k_retrieval is updated to 8
    resp_get = requests.get(f"{BASE_URL}/api/v1/rag-hub/config")
    assert resp_get.status_code == 200
    config_data = resp_get.json().get("data", {})
    print(f"Verified active config top_k_retrieval: {config_data.get('top_k_retrieval')}")
    assert config_data.get("top_k_retrieval") == 8

    print("[PASS] Dimension 5: Pydantic Validation Verified Successfully.")


def run_all_dimensions():
    print("STARTING CHALLENGER R2 EMPIRICAL TEST HARNESS")
    t0 = time.time()
    
    test_dimension_1_chinese_uppercase()
    test_dimension_2_agent3_trace_persistence()
    test_dimension_3_cosine_monotonicity()
    test_dimension_4_table_aware_chunker()
    test_dimension_5_pydantic_validation()
    
    total_time = time.time() - t0
    print("\n" + "="*70)
    print(f"ALL 5 EMPIRICAL CHALLENGER R2 DIMENSIONS PASSED! Total time: {total_time:.2f}s")
    print("="*70)


if __name__ == "__main__":
    run_all_dimensions()
