"""
@file pressure_test_agent_6.py
@description 智能体 6 (Agentic RAG 与离线知识工程) 全方位架构能力与极限压力测试套件
全面压测：
1. Sub-Agent 6A 特征雷达与策略决策准确度与耗时
2. 7 大物理分块算子极限吞吐与内存稳定性 (10万字超长医疗文档、极值表格)
3. 在线自省重写循环 (Sub-Agent 6B & 6C) 达标率与收敛测试
4. 真实大模型协同推理延迟与熔断防御压测
5. 离线文档巡检、异常切片识别与重新切片 (Re-chunking) 架构成熟度审查
"""

import time
import math
import sys
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal
from app.models.rag_agent_models import SpdRagDocument, SpdRagChunk, SpdModularRagConfig
from app.services.rag_modular_engine import (
    CHUNKER_REGISTRY,
    ChunkingStrategistSubAgent,
    QueryRewriterSubAgent,
    PreRetrievalJudgeSubAgent,
    ModularRagPipeline
)
from app.services.agents.agent_6_supervisor import AgenticRagSupervisorAgent
from app.services.agents.llm_client import RealLlmClient


def test_subagent_6a_decision_stress():
    print("=" * 60)
    print("【压测 1】Sub-Agent 6A 分块策略智能决策引擎准确率与吞吐压测")
    print("=" * 60)

    test_cases = [
        ("高密度表格耗材目录", "| 编号 | 耗材品名 | 规格型号 | 挂网价格 | 厂商 |\n" + "| 01 | 冠脉支架 | 3.0*18mm | 680.00 | 微创医疗 |\n" * 20, "TABLE_AWARE"),
        ("临床手术定数包指南", "【临床手术定数包配发指南】\n手术室护士应依据骨科四肢骨折固定术式定数包配置规范进行配领。", "PARENT_CHILD"),
        ("国家法规监督管理条例", "第一条 为了保证医疗器械的安全、有效，保障人体健康和生命安全，制定本条例。\n第二条 在中华人民共和国境内从事医疗器械的研制、生产、经营、使用活动，应当遵守本条例。\n第三条 医疗器械监督管理制度遵循风险分级原则。", "RECURSIVE_CHAR"),
        ("不良事件召回通报", "【医疗器械不良事件召回通报】某批次一次性使用无菌导尿管存在包装密封不全，现启动二级紧急召回程序。", "SEMANTIC_CLUSTER"),
        ("章节层级分明规范", "# 第一章 总则\n本院耗材管理原则。\n## 第二章 准入评审\n供应商资质查验。\n### 第三节 现场核验\n仓库温湿度监测与双人验收记录。\n# 第三章 附则", "MARKDOWN_HEADER"),
        ("应急绿色通道单句", "急诊绿色通道领用高值耗材可先执行抢救术式，术后24小时内补录电子流转单。", "SENTENCE_WINDOW")
    ]

    t0 = time.time()
    correct = 0
    total = len(test_cases) * 50  # 循环 50 轮压测高频吞吐
    for _ in range(50):
        for title, text, expected_strategy in test_cases:
            chosen, reason = ChunkingStrategistSubAgent.analyze_and_decide(text, "md", title)
            if chosen == expected_strategy:
                correct += 1

    elapsed_ms = (time.time() - t0) * 1000
    qps = int(total / (elapsed_ms / 1000.0))
    acc = (correct / total) * 100
    print(f"-> 样本规模: {total} 次决策调用")
    print(f"-> 耗时: {elapsed_ms:.2f} ms (单次平均: {elapsed_ms/total:.3f} ms, QPS: {qps})")
    print(f"-> 策略决策准确率: {acc:.1f}%")
    return {"qps": qps, "accuracy": acc}


def test_chunkers_extreme_stress():
    print("\n" + "=" * 60)
    print("【压测 2】7 大物理切片算子超长文本极限吞吐与稳定性压测")
    print("=" * 60)

    # 构造 10 万字恶劣极限医疗文本 (混合表格、长条款、无标点超长段落)
    base_text = (
        "【医疗物资SPD系统运行规范第" + str(1) + "条】\n"
        "各临床科室与二级库房在接收普通医用耗材与高值植入性耗材时，必须严格执行三查七对制度。\n"
        "| 序号 | 批号 | 效期 | 灭菌批次 | 注册证编号 | 灭菌状态 |\n"
        "| 001 | B20261101 | 2028-10-31 | ST2026-X | 国械注准20223130001 | 合格 |\n"
        "这是一段极其漫长的无停顿技术说明文字包含多科室专科耗材编码与UDI条形码载体数据要求在极端情况下不可发生栈溢出或内存崩溃。\n\n"
    ) * 300  # 约 10 万字

    print(f"-> 构造极限超长测试文本：{len(base_text)} 字符 (~{len(base_text.encode('utf-8'))//1024} KB)")

    results = {}
    for name, chunker in CHUNKER_REGISTRY.items():
        t0 = time.time()
        chunks = chunker.chunk(base_text, "DOC-STRESS-001", chunk_size=500, overlap=80)
        dur_ms = (time.time() - t0) * 1000
        count = len(chunks)
        results[name] = {"chunks": count, "time_ms": round(dur_ms, 2)}
        print(f"   [{name:16s}] -> 切片数: {count:4d} 个 | 耗时: {dur_ms:6.2f} ms")

    return results


def test_query_rewrite_convergence():
    print("\n" + "=" * 60)
    print("【压测 3】Sub-Agent 6B & 6C 自省重写评估循环收敛测试")
    print("=" * 60)

    queries = [
        "骨科那个钉子怎么领",
        "心内科支架坏了怎么退",
        "查一下上个月各科室亏了多少钱",
        "字典里耗材重名怎么办",
        "测试"
    ]

    for q in queries:
        curr_q = q
        history = []
        print(f"\n[原始查询]: '{q}'")
        for loop in range(1, 4):
            rewritten = QueryRewriterSubAgent.rewrite(curr_q, history)
            score, feedback = PreRetrievalJudgeSubAgent.evaluate(rewritten, q)
            print(f"   第 {loop} 轮自省 -> 得分: {score:.2f} | 改写式: {rewritten[:40]}... ({feedback})")
            history.append(feedback)
            curr_q = rewritten
            if score >= 0.85:
                print(f"   [收敛达标] 在第 {loop} 轮达到质量阈值 (>=0.85)，提前终止自省！")
                break


def test_agent_6_supervisor_live():
    print("\n" + "=" * 60)
    print("【压测 4】智能体 6 主控调度器真实端到端推理性能压测")
    print("=" * 60)

    with SessionLocal() as db:
        agent = AgenticRagSupervisorAgent(db)
        print("-> 触发智能体 6 端到端调度 (涉及自省重写 + 混合检索 + 交叉重排 + 云端大模型)...")
        t0 = time.time()
        res = agent.dispatch("骨科手术定数包与UDI追溯管理条例如何落地执行？", "sys_admin")
        total_time = (time.time() - t0) * 1000

        print(f"-> 执行总耗时: {total_time:.2f} ms")
        print(f"-> 智能体名称: {res.get('agent_name')}")
        print(f"-> 生效算子拓扑: {res.get('active_operators')}")
        print(f"-> 调用的真实工具: {res.get('tools_called')}")
        print(f"-> 自省重写轮数: {len(res.get('rewrite_steps', []))}")
        print(f"-> 匹配参考切片数: {len(res.get('citations', []))}")
        print(f"-> 模型回答前 100 字: {res.get('final_answer', '')[:100]}...")


def audit_document_inspection_and_rechunking():
    print("\n" + "=" * 60)
    print("【审查 5】系统中未切分文档巡检与自动重新切片 (Re-chunking) 架构现状审查")
    print("=" * 60)

    with SessionLocal() as db:
        total_docs = db.query(SpdRagDocument).count()
        total_chunks = db.query(SpdRagChunk).count()

        # 检查是否存在没有切片的孤儿文档
        docs = db.query(SpdRagDocument).all()
        orphan_docs = []
        for d in docs:
            c_count = db.query(SpdRagChunk).filter(SpdRagChunk.doc_id == d.id).count()
            if c_count == 0 or d.chunk_count == 0:
                orphan_docs.append(d)

        print(f"-> 知识库文档总数: {total_docs} 篇")
        print(f"-> 知识库切片总数: {total_chunks} 个")
        print(f"-> 零切片/未分块异常文档数: {len(orphan_docs)} 篇")

        if orphan_docs:
            print("   发现未切分异常文档:")
            for od in orphan_docs:
                print(f"   - ID: {od.id}, 标题: {od.doc_title}, 状态: {od.doc_status}")
        else:
            print("   [现状] 当前知识库中的存量文档均包含切片记录。")


if __name__ == "__main__":
    test_subagent_6a_decision_stress()
    test_chunkers_extreme_stress()
    test_query_rewrite_convergence()
    test_agent_6_supervisor_live()
    audit_document_inspection_and_rechunking()
