"""
@file tests/adversarial_rag_challenger.py
@description Challenger 1 独立对抗实测脚本：对 RAG 检索管线与环境连通性进行实机对抗性压测
包含：
1. 真实稠密余弦向量检索对抗验证 (对比不同专科查询、验证动态打分、验证非静态0.88、语义排名准确性)
2. 真实 BM25 稀疏分词打分对抗验证 (关键词覆盖、零频词、长短文本、非固定0.82)
3. 真实 RRF 倒数排名融合算法的数学精确性与逆序验证
4. 意图分类器在 6 大业务领域全样本覆盖验证
5. 复杂多跳复合子问题拆解（2路与3路复合语句切分、单句防误拆）
6. HTTP REST API 热配置持久化来回切换压测
7. HTTP REST API 四方连通性健康探测全字段真实性校验
8. 真实 HTTP agent_6 执行链路与动态引用溯源校验

@route tests/adversarial_rag_challenger.py
@throws AssertionError
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import numpy as np

# 将 backend 路径加入 sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.services.rag_modular_engine import (
    HybridRetriever,
    QueryRewriterSubAgent,
    PreRetrievalJudgeSubAgent,
    CrossEncoderReranker,
    ModularRagPipeline
)


def log_test_header(title: str):
    print("\n" + "=" * 70)
    print(f">> 对抗压测: {title}")
    print("=" * 70)


def challenge_1_dense_retrieval():
    log_test_header("1. 稠密余弦向量检索 (Ollama bge-m3:latest 动态打分对抗)")

    chunks_data = [
        {
            "chunk_uid": "CHUNK_CARDIO_001",
            "chunk_text": "心血管内科药物洗脱冠脉支架一物一码UDI核销全链路追溯规程，包含不良事件监测与批次硬冻结召回规范",
            "doc_code": "DOC-CARDIO-001",
            "strategy": "RECURSIVE_CHAR"
        },
        {
            "chunk_uid": "CHUNK_ORTHO_002",
            "chunk_text": "骨科病区高分子人工韧带耗材及膝关节锁定接骨板临床定数包请领与灭菌效期规范",
            "doc_code": "DOC-ORTHO-002",
            "strategy": "PARENT_CHILD"
        },
        {
            "chunk_uid": "CHUNK_FIN_003",
            "chunk_text": "全院多科室月度耗占比精算核算与高值耗材流转合规损耗审计内控制度",
            "doc_code": "DOC-FIN-003",
            "strategy": "TABLE_AWARE"
        },
        {
            "chunk_uid": "CHUNK_REG_004",
            "chunk_text": "国家药品监督管理局医疗器械监督管理条例，生产经营许可证查验与首营品种准入硬拦截",
            "doc_code": "DOC-REG-004",
            "strategy": "MARKDOWN_HEADER"
        }
    ]

    # 对抗查询 1：心内冠脉支架不良事件召回规范
    q1 = "心内冠脉支架不良事件召回规范"
    hits_q1 = HybridRetriever.search_dense(q1, chunks_data)
    scores_q1 = [h["dense_score"] for h in hits_q1]
    top_uid_q1 = hits_q1[0]["chunk_uid"]
    print(f"   [Query 1] '{q1}'")
    for h in hits_q1:
        print(f"      - {h['chunk_uid']}: score={h['dense_score']} | {h['chunk_text'][:35]}...")

    # 对抗查询 2：骨科高分子人工韧带耗材
    q2 = "骨科高分子人工韧带耗材"
    hits_q2 = HybridRetriever.search_dense(q2, chunks_data)
    scores_q2 = [h["dense_score"] for h in hits_q2]
    top_uid_q2 = hits_q2[0]["chunk_uid"]
    print(f"\n   [Query 2] '{q2}'")
    for h in hits_q2:
        print(f"      - {h['chunk_uid']}: score={h['dense_score']} | {h['chunk_text'][:35]}...")

    # 对抗查询 3：医院财务耗占比损耗审计
    q3 = "医院财务耗占比损耗审计"
    hits_q3 = HybridRetriever.search_dense(q3, chunks_data)
    scores_q3 = [h["dense_score"] for h in hits_q3]
    top_uid_q3 = hits_q3[0]["chunk_uid"]
    print(f"\n   [Query 3] '{q3}'")
    for h in hits_q3:
        print(f"      - {h['chunk_uid']}: score={h['dense_score']} | {h['chunk_text'][:35]}...")

    # 断言 1: 分数不是固定 0.88，且各切片间分数有显著差异
    assert all(s != 0.88 for s in scores_q1), f"Scores in Q1 must NOT be static 0.88: {scores_q1}"
    assert all(s != 0.88 for s in scores_q2), f"Scores in Q2 must NOT be static 0.88: {scores_q2}"
    assert len(set(scores_q1)) >= 3, f"Q1 scores must have distinct values: {scores_q1}"
    assert len(set(scores_q2)) >= 3, f"Q2 scores must have distinct values: {scores_q2}"

    # 断言 2: 两次不同查询的分数分布完全不同
    assert scores_q1 != scores_q2, "Different queries must yield different score vectors"

    # 断言 3: 语义排序正确 (Q1 -> 心内支架，Q2 -> 骨科韧带，Q3 -> 财务耗占比)
    assert top_uid_q1 == "CHUNK_CARDIO_001", f"Query 1 should rank CHUNK_CARDIO_001 first, got {top_uid_q1}"
    assert top_uid_q2 == "CHUNK_ORTHO_002", f"Query 2 should rank CHUNK_ORTHO_002 first, got {top_uid_q2}"
    assert top_uid_q3 == "CHUNK_FIN_003", f"Query 3 should rank CHUNK_FIN_003 first, got {top_uid_q3}"

    # 断言 4: 语义相关度最高项得分显著高于最不相关项 (差值 > 0.15)
    margin_q1 = hits_q1[0]["dense_score"] - hits_q1[-1]["dense_score"]
    margin_q2 = hits_q2[0]["dense_score"] - hits_q2[-1]["dense_score"]
    print(f"\n   Q1 区分度 (Top vs Bottom): {margin_q1:.4f}")
    print(f"   Q2 区分度 (Top vs Bottom): {margin_q2:.4f}")
    assert margin_q1 > 0.15, f"Dense score margin too low: {margin_q1}"
    assert margin_q2 > 0.15, f"Dense score margin too low: {margin_q2}"

    print("   [PASS] 稠密余弦向量打分具备真实动态性，语义排序准确无伪造！")


def challenge_2_sparse_bm25_retrieval():
    log_test_header("2. BM25 稀疏关键词打分 (真实分词与词频动态打分对抗)")

    chunks_data = [
        {
            "chunk_uid": "C_STENT",
            "chunk_text": "心血管内科药物洗脱冠脉支架一物一码UDI核销全链路追溯规程，支架植入全程记录，支架批次追踪",
            "doc_code": "DOC-STENT"
        },
        {
            "chunk_uid": "C_ORTHO",
            "chunk_text": "临床骨科膝关节手术定数包规范，包含锁定接骨板和钛合金骨水泥螺钉与人工韧带",
            "doc_code": "DOC-ORTHO"
        },
        {
            "chunk_uid": "C_FINANCE",
            "chunk_text": "全院多科室月度耗占比精算核算与高值耗材流转合规损耗审计内控制度",
            "doc_code": "DOC-FIN"
        }
    ]

    # 查询 A: 包含高频词 "支架"
    q_stent = "冠脉支架批次追踪"
    hits_a = HybridRetriever.search_sparse(q_stent, chunks_data)
    print(f"   [Query A] '{q_stent}'")
    for h in hits_a:
        print(f"      - {h['chunk_uid']}: sparse_score={h['sparse_score']}, raw_score={h['bm25_raw_score']}")

    # 查询 B: 包含骨科专有词
    q_ortho = "膝关节钛合金螺钉定数包"
    hits_b = HybridRetriever.search_sparse(q_ortho, chunks_data)
    print(f"\n   [Query B] '{q_ortho}'")
    for h in hits_b:
        print(f"      - {h['chunk_uid']}: sparse_score={h['sparse_score']}, raw_score={h['bm25_raw_score']}")

    # 查询 C: 完全无关词
    q_none = "火星飞船引力波推进器"
    hits_c = HybridRetriever.search_sparse(q_none, chunks_data)
    print(f"\n   [Query C] '{q_none}' (无关输入)")
    for h in hits_c:
        print(f"      - {h['chunk_uid']}: sparse_score={h['sparse_score']}, raw_score={h['bm25_raw_score']}")

    # 断言:
    # 1. 查询 A 命中 C_STENT 且得分 1.0 (归一化)，其他为 0 或极低
    assert hits_a[0]["chunk_uid"] == "C_STENT", "Query A should rank C_STENT top"
    assert hits_a[0]["sparse_score"] == 1.0, "Top hit normalized score should be 1.0"
    assert hits_a[-1]["sparse_score"] == 0.0, "Non-matching chunk score should be 0.0"

    # 2. 查询 B 命中 C_ORTHO 且得分 1.0
    assert hits_b[0]["chunk_uid"] == "C_ORTHO", "Query B should rank C_ORTHO top"
    assert hits_b[0]["sparse_score"] == 1.0

    # 3. 查询 C 所有得分为 0.0
    for h in hits_c:
        assert h["sparse_score"] == 0.0, f"Unrelated query must yield 0.0, got {h['sparse_score']}"

    # 4. 确认没有静态 0.82
    all_scores = [h["sparse_score"] for h in hits_a + hits_b]
    assert all(s != 0.82 for s in all_scores), f"BM25 must NOT return static 0.82: {all_scores}"

    print("   [PASS] BM25 稀疏检索打分具备真实关键词频率响应，零相关度正确归零！")


def challenge_3_rrf_fusion_correctness():
    log_test_header("3. RRF (Reciprocal Rank Fusion) 倒数排名融合精确度对抗")

    # 构建一个排名互斥的场景验证 RRF 数学精确度
    dense_hits = [
        {"chunk_uid": "DOC_A", "dense_score": 0.95},  # rank 0 -> score 1/(60+0+1) = 1/61
        {"chunk_uid": "DOC_B", "dense_score": 0.85},  # rank 1 -> score 1/(60+1+1) = 1/62
        {"chunk_uid": "DOC_C", "dense_score": 0.70},  # rank 2 -> score 1/(60+2+1) = 1/63
        {"chunk_uid": "DOC_D", "dense_score": 0.60},  # rank 3 -> score 1/(60+3+1) = 1/64
    ]

    sparse_hits = [
        {"chunk_uid": "DOC_B", "sparse_score": 1.00}, # rank 0 -> score 1/(60+0+1) = 1/61
        {"chunk_uid": "DOC_C", "sparse_score": 0.80}, # rank 1 -> score 1/(60+1+1) = 1/62
        {"chunk_uid": "DOC_D", "sparse_score": 0.60}, # rank 2 -> score 1/(60+2+1) = 1/63
        {"chunk_uid": "DOC_A", "sparse_score": 0.10}, # rank 3 -> score 1/(60+3+1) = 1/64
    ]

    fused = HybridRetriever.rrf_fuse(dense_hits, sparse_hits, k=60)
    print("   RRF 融合结果:")
    for item in fused:
        print(f"      - {item['chunk_uid']}: rrf_score={item['rrf_score']}")

    # 理论数学推导:
    # DOC_A: 1/61 + 1/64 = 0.0163934 + 0.0156250 = 0.0320184 -> round(0.0320)
    # DOC_B: 1/62 + 1/61 = 0.0161290 + 0.0163934 = 0.0325224 -> round(0.0325)
    # DOC_C: 1/63 + 1/62 = 0.0158730 + 0.0161290 = 0.0320020 -> round(0.0320)
    # DOC_D: 1/64 + 1/63 = 0.0156250 + 0.0158730 = 0.0314980 -> round(0.0315)
    # 因此 DOC_B (0.0325) 必须排名第 1！DOC_D (0.0315) 必须排名第 4！
    expected_top = "DOC_B"
    assert fused[0]["chunk_uid"] == expected_top, f"Expected {expected_top} to be top, got {fused[0]['chunk_uid']}"
    assert fused[0]["rrf_score"] == 0.0325, f"DOC_B score expected 0.0325, got {fused[0]['rrf_score']}"
    assert fused[-1]["chunk_uid"] == "DOC_D", f"DOC_D must be last, got {fused[-1]['chunk_uid']}"
    assert fused[-1]["rrf_score"] == 0.0315, f"DOC_D score expected 0.0315, got {fused[-1]['rrf_score']}"

    print("   [PASS] RRF 融合公式 1/(k+rank+1) 数学计算与排序完全精确吻合！")


def challenge_4_intent_and_subquery_operators():
    log_test_header("4. 意图分类器与复合子问题拆解算子对抗")
    db = SessionLocal()
    try:
        pipeline = ModularRagPipeline(db)
        pipeline.config.enable_intent_classify = 1
        pipeline.config.enable_subquery_decompose = 1
        pipeline.config.enable_query_rewrite = 0

        # 4.1 测试 6 大意图全覆盖
        intent_cases = [
            ("产品字典新耗材品规录入与分类建仓", "DICT_LOOKUP"),
            ("主库高值物资按需分发调拨与近效期FEFO出库", "DISPATCH_STOCK"),
            ("临床手术室二级库定数包申领与领料流程", "CLINICAL_REQUISITION"),
            ("心血管冠脉支架一物一码UDI全生命周期追溯与不良事件召回", "HIGH_VALUE_TRACE"),
            ("财务科多科室月度耗占比精算与流转合规损耗审计", "FINANCE_AUDIT"),
            ("国家药品监督管理政策宏观法规条例", "GENERAL_REGULATION"),
        ]

        print("   [意图分类 6 大业务领域全覆盖检验]:")
        for query_text, expected_cat in intent_cases:
            res = pipeline.run(query_text, operator_account="challenger_1")
            actual_cat = res.get("intent_classification", {}).get("intent_category")
            print(f"      - '{query_text[:20]}...' -> {actual_cat} (预期: {expected_cat})")
            assert actual_cat == expected_cat, f"Expected {expected_cat}, got {actual_cat} for query '{query_text}'"

        print("   [PASS] 6 大业务意图精准分类 100% 达成！")

        # 4.2 测试复合子问题多跳拆解
        compound_query_2 = "骨科定数包如何申领，并且高值支架一物一码如何全链路溯源"
        res_2 = pipeline.run(compound_query_2, operator_account="challenger_1")
        sub_2 = res_2.get("subqueries", [])
        print(f"\n   [双复合问题拆解]: '{compound_query_2}'")
        print(f"      拆解结果 ({len(sub_2)}个): {sub_2}")
        assert len(sub_2) == 2, f"Expected 2 subqueries, got {len(sub_2)}"

        compound_query_3 = "如何进行主库物资分发调拨；同时怎样进行月度耗占比财务审计；还有产品字典如何分类录入"
        res_3 = pipeline.run(compound_query_3, operator_account="challenger_1")
        sub_3 = res_3.get("subqueries", [])
        print(f"\n   [三复合问题拆解]: '{compound_query_3}'")
        print(f"      拆解结果 ({len(sub_3)}个): {sub_3}")
        assert len(sub_3) == 3, f"Expected 3 subqueries, got {len(sub_3)}"

        # 4.3 测试单句不应被误拆
        single_query = "骨科膝关节手术锁定接骨板定数包使用规范"
        res_single = pipeline.run(single_query, operator_account="challenger_1")
        sub_single = res_single.get("subqueries", [])
        print(f"\n   [单问题防误拆]: '{single_query}'")
        print(f"      拆解结果 ({len(sub_single)}个): {sub_single}")
        assert len(sub_single) == 1, f"Single query should not be split, got {sub_single}"

        print("   [PASS] 复合子问题拆解与防误拆算子逻辑严格准确！")

    finally:
        db.close()


def challenge_5_config_update_persistence_roundtrip():
    log_test_header("5. HTTP REST API: /config 与 /config/update 持久化来回切换热压测")

    url_update = "http://127.0.0.1:8000/api/v1/rag-hub/config/update"
    url_get = "http://127.0.0.1:8000/api/v1/rag-hub/config"

    # 轮次 1: 修改为非默认特征参数
    payload_1 = {
        "top_k_retrieval": 17,
        "enable_subquery_decompose": 0,
        "enable_intent_classify": 1,
        "enable_bm25_sparse": 0,
        "active_chat_model": "deepseek-r1:1.5b"
    }
    req_1 = urllib.request.Request(
        url_update,
        data=json.dumps(payload_1).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_1, timeout=8) as r:
        assert json.loads(r.read().decode())["code"] == 200

    # 立即 GET 验证
    with urllib.request.urlopen(url_get, timeout=8) as r:
        d1 = json.loads(r.read().decode())["data"]
        print(f"   [轮次 1 读取] top_k_retrieval={d1['top_k_retrieval']}, subquery={d1['enable_subquery_decompose']}, bm25={d1['enable_bm25_sparse']}, chat_model={d1['active_chat_model']}")
        assert d1["top_k_retrieval"] == 17, f"Expected 17, got {d1['top_k_retrieval']}"
        assert d1["enable_subquery_decompose"] == 0, f"Expected 0, got {d1['enable_subquery_decompose']}"
        assert d1["enable_bm25_sparse"] == 0, f"Expected 0, got {d1['enable_bm25_sparse']}"
        assert d1["active_chat_model"] == "deepseek-r1:1.5b", f"Expected deepseek-r1:1.5b, got {d1['active_chat_model']}"

    # 轮次 2: 恢复为生产级默认推荐配置
    payload_2 = {
        "top_k_retrieval": 20,
        "enable_subquery_decompose": 1,
        "enable_intent_classify": 1,
        "enable_bm25_sparse": 1,
        "active_chat_model": "qwen3.5:2b"
    }
    req_2 = urllib.request.Request(
        url_update,
        data=json.dumps(payload_2).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_2, timeout=8) as r:
        assert json.loads(r.read().decode())["code"] == 200

    with urllib.request.urlopen(url_get, timeout=8) as r:
        d2 = json.loads(r.read().decode())["data"]
        print(f"   [轮次 2 读取] top_k_retrieval={d2['top_k_retrieval']}, subquery={d2['enable_subquery_decompose']}, bm25={d2['enable_bm25_sparse']}, chat_model={d2['active_chat_model']}")
        assert d2["top_k_retrieval"] == 20
        assert d2["enable_subquery_decompose"] == 1
        assert d2["enable_bm25_sparse"] == 1
        assert d2["active_chat_model"] == "qwen3.5:2b"

    print("   [PASS] 配置热更新接口持久化双向来回切换验证 100% 通过！")


def challenge_6_connectivity_check_deep_inspection():
    log_test_header("6. HTTP REST API: /connectivity/check 全字段深度探测校验")

    url = "http://127.0.0.1:8000/api/v1/rag-hub/connectivity/check"
    with urllib.request.urlopen(url, timeout=8) as r:
        res = json.loads(r.read().decode())
        assert res["code"] == 200
        data = res["data"]

    # 校验 Ollama 状态
    ollama = data.get("ollama", {})
    print(f"   [Ollama] connected={ollama.get('connected')}, latency={ollama.get('latency_ms')}ms, models={ollama.get('models')}")
    assert ollama.get("connected") is True, "Ollama must be connected"
    assert "bge-m3:latest" in ollama.get("models", []), "bge-m3:latest must be in Ollama model list"
    assert ollama.get("latency_ms") >= 0, "Ollama latency must be non-negative"

    # 校验 Redis 状态
    redis_info = data.get("redis", {})
    print(f"   [Redis] connected={redis_info.get('connected')}, latency={redis_info.get('latency_ms')}ms, msg={redis_info.get('msg')}")
    assert redis_info.get("connected") is True, "Redis must be connected"
    assert redis_info.get("latency_ms") >= 0, "Redis latency must be non-negative"

    # 校验 Neo4j 状态与优雅降级提示
    neo4j_info = data.get("neo4j", {})
    print(f"   [Neo4j] connected={neo4j_info.get('connected')}, msg={neo4j_info.get('msg')}")
    # Neo4j 未独立启动时必须标明 connected=False 并提供降级信息
    assert isinstance(neo4j_info.get("connected"), bool)
    assert "内存医疗图谱" in neo4j_info.get("msg") or neo4j_info.get("connected") is True

    # 校验 MiMo 配置
    mimo_info = data.get("mimo", {})
    print(f"   [MiMo] configured={mimo_info.get('configured')}, model={mimo_info.get('model')}")
    assert mimo_info.get("configured") is True, "MiMo must be configured"
    assert mimo_info.get("model") == "mimo-v2.6-flash", f"MiMo model mismatch: {mimo_info.get('model')}"

    # 校验 LangSmith 配置
    ls_info = data.get("langsmith", {})
    print(f"   [LangSmith] enabled={ls_info.get('enabled')}, project={ls_info.get('project')}, has_key={ls_info.get('has_key')}")
    assert ls_info.get("enabled") is True
    assert ls_info.get("has_key") is True
    assert ls_info.get("project") == "Personal"

    print("   [PASS] 五方基础设施连通性与追踪状态全字段校验通过！")


def challenge_7_agent_6_execution_e2e():
    log_test_header("7. HTTP REST API: /agent/execute 智能体 6 端到端调用与动态引用")

    url = "http://127.0.0.1:8000/api/v1/rag-hub/agent/execute"
    payload = {
        "agent_id": "agent_6",
        "query": "心内科冠脉支架一物一码UDI核销规程，并且骨科人工韧带定数包如何领用"
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read().decode())
        assert res["code"] == 200, f"Agent execute failed: {res}"
        d = res["data"]

    print(f"   智能体名称: {d.get('agent_name')}")
    print(f"   架构标识: {d.get('architecture')}")
    print(f"   意图分类: {d.get('intent_classification')}")
    print(f"   子问题拆解 ({len(d.get('subqueries', []))}个): {d.get('subqueries')}")
    print(f"   引用溯源卡片 ({len(d.get('citations', []))}个):")
    citations = d.get("citations", [])
    assert len(citations) > 0, "Citations must not be empty"

    scores = []
    for c in citations:
        score_val = c.get("score")
        scores.append(score_val)
        print(f"      - ID={c['citation_id']}, chunk={c['chunk_uid']}, score={score_val}, snippet={c['snippet'][:35]}...")
        assert isinstance(score_val, (float, int))
        assert score_val > 0, "Score must be positive"

    # 验证引用分值不全是静态 0.88
    assert any(s != 0.88 for s in scores), f"Citations scores should be dynamic: {scores}"
    print("   [PASS] 智能体 6 端到端链路完整，意图、子问题与动态引用卡片齐备！")


def main():
    print("======================================================================")
    print("CHALLENGER 1: RAG 混合检索与环境连通性实机对抗压测开始")
    print("======================================================================")
    t_start = time.time()

    challenge_1_dense_retrieval()
    challenge_2_sparse_bm25_retrieval()
    challenge_3_rrf_fusion_correctness()
    challenge_4_intent_and_subquery_operators()
    challenge_5_config_update_persistence_roundtrip()
    challenge_6_connectivity_check_deep_inspection()
    challenge_7_agent_6_execution_e2e()

    total_time = time.time() - t_start
    print("\n" + "=" * 70)
    print(f"ALL 7 CHALLENGE ASSERTIONS PASSED! 总耗时: {total_time:.2f} 秒")
    print("VERDICT: CONFIRMED")
    print("======================================================================")


if __name__ == "__main__":
    main()
