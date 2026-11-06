"""
@file feature_radar.py
@description Sub-Agent 6A 文档特征探测与策略决策雷达
基于多维特征（表格密度、条款密度、标题层级深度、段落平均长度）自主判定推荐 7 大分块策略。

@param raw_text: str, filename: str
@returns Dict[str, Any] 包含雷达数据、推荐策略、置信度与决策理由
@route internal://services/rag/feature_radar
@throws 无
"""

import re
from typing import Any, Dict


def analyze_features_and_radar(raw_text: str, filename: str) -> Dict[str, Any]:
    """探测文档结构特征并生成特征雷达及 Agent 推荐决策
    @param raw_text: str 原始纯文本
    @param filename: str 文件名称
    @returns Dict[str, Any] 特征雷达字典
    @route internal://services/rag/feature_radar/analyze_features_and_radar
    @throws 无
    """
    char_count = len(raw_text)
    table_pipe_count = raw_text.count("|")
    table_ratio = round(min(1.0, (table_pipe_count * 8) / max(1, char_count)), 2)
    markdown_header_count = len([line for line in raw_text.splitlines() if line.strip().startswith("#")])
    clause_count = len(re.findall(r"(第[零一二三四五六七八九十百0-9]+条|监督管理条例|细则|管理制度)", raw_text))
    paras = [p for p in raw_text.split("\n\n") if p.strip()]
    avg_len = int(char_count / max(1, len(paras)))

    radar_report = {
        "char_count": char_count,
        "table_pipe_count": table_pipe_count,
        "table_density": table_ratio,
        "header_count": markdown_header_count,
        "regulation_clauses": clause_count,
        "avg_paragraph_len": avg_len
    }

    # Agent 6A 自主特征决策
    chosen_strategy = "RECURSIVE_CHAR"
    decision_reason = "通用长文本规范，采用递归字符分块保持自然段落完整性。"
    confidence = 0.90

    if table_pipe_count >= 10 or table_ratio >= 0.15:
        chosen_strategy = "TABLE_AWARE"
        decision_reason = f"检测到表格密度较高(管线符 {table_pipe_count} 处)，推荐医疗表格感知分块以保留表头。"
        confidence = 0.95
    elif markdown_header_count >= 3:
        chosen_strategy = "MARKDOWN_HEADER"
        decision_reason = f"检测到具备清晰的 Markdown 标题结构({markdown_header_count} 处标题)，推荐层级分块以继承路径元数据。"
        confidence = 0.94
    elif clause_count >= 4:
        chosen_strategy = "RECURSIVE_CHAR"
        decision_reason = f"检测到法规与内控制度条款模式({clause_count} 处)，推荐按条款递归分块切断。"
        confidence = 0.92
    elif "手术定数包" in filename or "说明书" in filename or "指南" in filename:
        chosen_strategy = "PARENT_CHILD"
        decision_reason = "医疗手术包或耗材使用指南，推荐父子分块(Small-to-Big)兼顾召回灵敏度与大上下文。"
        confidence = 0.93
    elif "不良事件" in filename or "召回" in filename:
        chosen_strategy = "SEMANTIC_CLUSTER"
        decision_reason = "通报与案例类文档，推荐语义聚类分块确保案例前因后果内聚。"
        confidence = 0.91
    elif char_count < 800:
        chosen_strategy = "SENTENCE_WINDOW"
        decision_reason = "文档篇幅精简，推荐句子滑动窗口分块丰富单句上下文。"
        confidence = 0.90

    return {
        "chosen_strategy": chosen_strategy,
        "decision_reason": decision_reason,
        "confidence": confidence,
        "radar": radar_report
    }
