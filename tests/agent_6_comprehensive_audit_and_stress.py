"""
@file agent_6_comprehensive_audit_and_stress.py
@description 智能体 6 号全功能架构审查与多维真实压力测试套件
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal
from app.models.rag_agent_models import SpdRagDocument, SpdRagChunk, SpdModularRagConfig
from app.services.rag_modular_engine import (
    CHUNKER_REGISTRY,
    ChunkingStrategistSubAgent,
    QueryRewriterSubAgent,
    PreRetrievalJudgeSubAgent
)
from app.services.agents.agent_6_supervisor import AgenticRagSupervisorAgent


def run_benchmark():
    print("=" * 80)
    print(" 智能体 6 号 (Agentic RAG 与离线知识工程) 全方位架构审查与性能压力测试")
    print("=" * 80)

    # -------------------------------------------------------------
    # 压测 1：Sub-Agent 6A 策略自适应特征探测与决策引擎压测
    # -------------------------------------------------------------
    print("\n>>> [压测 1] Sub-Agent 6A 文档特征雷达与 7 大策略决策引擎压测")
    test_samples = [
        ("高密度表格", "耗材集中采购价格目录表", "| 序号 | 品名 | 规格 | 价格 |\n| 1 | 骨水泥 | 40g | 450 |\n| 2 | 缝合线 | 3-0 | 35 |\n" * 10, "TABLE_AWARE"),
        ("临床定数包", "骨科四肢骨折临床手术定数包使用指南", "本规程指导临床定数包在手术室中的配发与使用标准。", "PARENT_CHILD"),
        ("法规与条例", "医疗器械监督管理条例与进货查验管理制度", "第一条 为了保证医疗器械安全制定本条例。\n第二条 医疗机构采购应查验供货者资质。\n第三条 建立健全进货查验记录制度。", "RECURSIVE_CHAR"),
        ("案例通报", "关于某批次输液器不良事件通报与紧急召回报告", "通报某批次一次性使用输液器存在漏液隐患，启动召回。", "SEMANTIC_CLUSTER"),
        ("章节层级规范", "三甲医院医用耗材全流程管理制度总则", "# 第一章 总则\n## 第一节 耗材分类\n### 1. 高值耗材\n# 第二章 准入", "MARKDOWN_HEADER"),
        ("简短应急规范", "急诊绿色通道领用要点", "急诊绿色通道高值耗材可术后24小时内补录电子流转单。", "SENTENCE_WINDOW")
    ]

    t0 = time.time()
    loops = 100
    correct = 0
    total = len(test_samples) * loops
    for _ in range(loops):
        for tag, title, content, expected in test_samples:
            st, reason = ChunkingStrategistSubAgent.analyze_and_decide(content, "md", title)
            if st == expected:
                correct += 1
    t1 = time.time()
    dur_ms = (t1 - t0) * 1000
    print(f"  - 样本规模: {total} 次特征探测调用")
    print(f"  - 总耗时: {dur_ms:.2f} ms | 单次均耗: {dur_ms/total:.3f} ms | QPS: {int(total/(dur_ms/1000))}")
    print(f"  - 策略自主推荐达标准确率: {(correct/total)*100:.1f}%")

    # -------------------------------------------------------------
    # 压测 2：7 大切片算子 2000 字真实医疗文本吞吐压测
    # -------------------------------------------------------------
    print("\n>>> [压测 2] 7 大物理切片策略算子吞吐与切分稳定性压测")
    sample_text = (
        "【医疗器械临床使用安全管理规范】\n"
        "第一条 各医疗机构必须建立健全医用耗材全生命周期追溯档案。\n"
        "| 耗材编码 | 规格型号 | 生产批号 | 灭菌批次 | 追溯码 |\n"
        "| MAT-001 | 3.0*18mm | B261101 | ST-998 | (01)06912345678901 |\n"
        "| MAT-002 | 4.0*20mm | B261102 | ST-999 | (01)06912345678902 |\n\n"
        "第二条 高值植入性耗材必须严格落实一物一码扫描登记，禁止手写单据替代。\n"
        "第三条 手术室二级库房应当设立专人专柜双人双锁管理高风险植入材料。\n\n"
        "第四条 发生不良事件时，应当在24小时内向不良事件监测系统直报并封存问题批次。\n"
    ) * 10  # 约 2500 字符

    for name, chunker in CHUNKER_REGISTRY.items():
        t_start = time.time()
        chunks = chunker.chunk(sample_text, "DOC-BENCH-001", chunk_size=300, overlap=50)
        t_end = time.time()
        c_time = (t_end - t_start) * 1000
        avg_len = sum(c["chunk_size"] for c in chunks) // max(1, len(chunks))
        print(f"  - 算子 [{name:16s}] -> 切片数: {len(chunks):3d} 个 | 平均长度: {avg_len:3d} 字 | 耗时: {c_time:5.2f} ms")

    # -------------------------------------------------------------
    # 压测 3：Sub-Agent 6B & 6C 自省重写评估循环收敛测试
    # -------------------------------------------------------------
    print("\n>>> [压测 3] Sub-Agent 6B (重写) 与 6C (质检) 自省循环收敛测试")
    test_queries = [
        "骨科那个钉子怎么领",
        "心内科支架坏了怎么退",
        "查一下上个月各科室亏了多少钱"
    ]
    for q in test_queries:
        curr_q = q
        history = []
        print(f"  - 原始口语提问: '{q}'")
        for loop in range(1, 4):
            rewritten = QueryRewriterSubAgent.rewrite(curr_q, history)
            score, feedback = PreRetrievalJudgeSubAgent.evaluate(rewritten, q)
            history.append(feedback)
            curr_q = rewritten
            status_tag = "[达标终止]" if score >= 0.85 else "[继续自省]"
            print(f"     第 {loop} 轮: 评分={score:.2f} {status_tag} -> 改写词: {rewritten[:35]}...")
            if score >= 0.85:
                break

    # -------------------------------------------------------------
    # 审查 4：数据库知识库资产现状审查 (是否存在未切分/孤儿文档)
    # -------------------------------------------------------------
    print("\n>>> [审查 4] 知识库物理资产现状与孤儿/未切分文档排查")
    with SessionLocal() as db:
        docs = db.query(SpdRagDocument).all()
        chunks_count = db.query(SpdRagChunk).count()
        print(f"  - 知识库登记文档总数: {len(docs)} 篇")
        print(f"  - 数据库切片总记录数: {chunks_count} 个")

        zero_chunk_docs = []
        for d in docs:
            c_cnt = db.query(SpdRagChunk).filter(SpdRagChunk.doc_id == d.id).count()
            if c_cnt == 0:
                zero_chunk_docs.append(d)

        if zero_chunk_docs:
            print(f"  - [发现未切分异常文档]: {len(zero_chunk_docs)} 篇")
            for zd in zero_chunk_docs:
                print(f"     ID {zd.id}: {zd.doc_title} (策略: {zd.selected_chunk_strategy}, 状态: {zd.doc_status})")
        else:
            print("  - [审查结论]: 当前所有已录入文档均已完成切片，无零切片孤儿文档！")

        print("  - 各文档采用的切分策略分布:")
        for d in docs[:6]:
            print(f"     * [{d.selected_chunk_strategy:15s}] (切片: {d.chunk_count:2d}个) {d.doc_title[:30]}")

    print("\n" + "=" * 80)
    print(" 压力测试与架构核验全部完成！")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
