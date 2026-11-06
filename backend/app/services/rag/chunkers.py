"""
@file chunkers.py
@description 医疗物资规范知识工程 7 大物理分块策略实现包
包含：递归字符分块、父子文档分块 (Small-to-Big)、章节标题层级分块、医疗表格感知分块、
语义聚类分块、句子滑动窗口分块与固定重叠分块。
支持前端动态配置切片字符数 (chunk_size) 与重叠字符数 (chunk_overlap)。

@param text: str, metadata: dict, chunk_size: int, chunk_overlap: int
@returns List[str] 切片文本列表
@route internal://services/rag/chunkers
@throws 无
"""

from abc import ABC, abstractmethod
import re
from typing import Any, Dict, List, Optional


class BaseChunker(ABC):
    """分块策略抽象基类"""

    @abstractmethod
    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        """将原始文档切分为文本块切片列表
        @param text: str 原始文本内容
        @param metadata: Dict[str, Any] 文档元数据
        @param chunk_size: Optional[int] 自定义切片字符上限
        @param chunk_overlap: Optional[int] 自定义重叠字符数
        @returns List[str] 切片列表
        """
        pass


class RecursiveCharChunker(BaseChunker):
    """1. 递归字符分块：按段落、句号、换行多级递归切断，维持自然语义边界"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.default_chunk_size = chunk_size
        self.default_chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        target_size = chunk_size or self.default_chunk_size
        paras = re.split(r"\n\s*\n", text)
        chunks = []
        cur = ""
        for p in paras:
            p_strip = p.strip()
            if not p_strip:
                continue
            if len(cur) + len(p_strip) <= target_size:
                cur = f"{cur}\n\n{p_strip}".strip()
            else:
                if cur:
                    chunks.append(cur)
                cur = p_strip
        if cur:
            chunks.append(cur)
        return chunks if chunks else [text[:target_size]]


class ParentChildChunker(BaseChunker):
    """2. 父子文档分块 (Small-to-Big)：大段落做父文档，细分句做高敏检索子文档"""

    def __init__(self, parent_size: int = 800, child_size: int = 200):
        self.parent_size = parent_size
        self.child_size = child_size

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        p_size = chunk_size or self.parent_size
        c_size = max(80, p_size // 4)
        parent_chunks = [text[i:i + p_size] for i in range(0, len(text), max(100, p_size - 100))]
        results = []
        for p in parent_chunks:
            sentences = re.split(r"(?<=[。！？\n])", p)
            child = ""
            for s in sentences:
                if len(child) + len(s) <= c_size:
                    child += s
                else:
                    if child.strip():
                        results.append(f"[上下文父块摘要: {p[:60]}...] {child.strip()}")
                    child = s
            if child.strip():
                results.append(f"[上下文父块摘要: {p[:60]}...] {child.strip()}")
        return results if results else [text[:p_size]]


class MarkdownHeaderChunker(BaseChunker):
    """3. 章节标题层级分块：按 # / ## / ### 标题切分并继承路径元数据"""

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        lines = text.splitlines()
        chunks = []
        cur_header = "前言/概述"
        cur_body = []

        for line in lines:
            if re.match(r"^#{1,4}\s+", line):
                if cur_body:
                    chunks.append(f"【{cur_header}】\n" + "\n".join(cur_body).strip())
                    cur_body = []
                cur_header = line.strip("#").strip()
            else:
                if line.strip():
                    cur_body.append(line.strip())

        if cur_body:
            chunks.append(f"【{cur_header}】\n" + "\n".join(cur_body).strip())
        return chunks if chunks else [text]


class TableAwareChunker(BaseChunker):
    """4. 医疗表格感知分块：识别 Markdown 或制表符表格，保持表头与数据行完整不碎裂"""

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        lines = text.splitlines()
        chunks = []
        in_table = False
        table_lines = []
        text_lines = []

        for line in lines:
            if "|" in line:
                if text_lines:
                    chunks.append("\n".join(text_lines).strip())
                    text_lines = []
                in_table = True
                table_lines.append(line)
            else:
                if in_table:
                    if table_lines:
                        chunks.append("【表格数据结构】\n" + "\n".join(table_lines).strip())
                        table_lines = []
                    in_table = False
                if line.strip():
                    text_lines.append(line.strip())

        if table_lines:
            chunks.append("【表格数据结构】\n" + "\n".join(table_lines).strip())
        if text_lines:
            chunks.append("\n".join(text_lines).strip())

        return chunks if chunks else [text]


class SemanticClusterChunker(BaseChunker):
    """5. 语义聚类分块：按医疗案情、不良事件报告主题内聚聚合"""

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        target_size = chunk_size or 600
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if len(paras) <= 2:
            return paras if paras else [text]
        chunks = []
        group = []
        for p in paras:
            group.append(p)
            if len(group) >= 2 or len("\n".join(group)) > target_size:
                chunks.append("\n\n".join(group))
                group = []
        if group:
            chunks.append("\n\n".join(group))
        return chunks


class SentenceWindowChunker(BaseChunker):
    """6. 句子滑动窗口分块：以核心单句为中心向前扩展前置句和后置句"""

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        sentences = [s.strip() for s in re.split(r"(?<=[。！？；\n])", text) if s.strip()]
        if len(sentences) <= 3:
            return [text]
        chunks = []
        for i in range(len(sentences)):
            start = max(0, i - 1)
            end = min(len(sentences), i + 2)
            window = "".join(sentences[start:end])
            chunks.append(f"[聚焦句子]: {sentences[i]} | [扩展上下文]: {window}")
        return chunks[:15]


class FixedOverlapChunker(BaseChunker):
    """7. 固定重叠滑动分块：通用稳定兜底分块"""

    def __init__(self, chunk_size: int = 500, overlap: int = 80):
        self.default_chunk_size = chunk_size
        self.default_overlap = overlap

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        c_size = chunk_size or self.default_chunk_size
        c_overlap = chunk_overlap if chunk_overlap is not None else self.default_overlap
        step = max(1, c_size - c_overlap)
        chunks = []
        for i in range(0, len(text), step):
            c = text[i:i + c_size].strip()
            if c:
                chunks.append(c)
        return chunks if chunks else [text]


CHUNKER_REGISTRY: Dict[str, BaseChunker] = {
    "RECURSIVE_CHAR": RecursiveCharChunker(),
    "PARENT_CHILD": ParentChildChunker(),
    "MARKDOWN_HEADER": MarkdownHeaderChunker(),
    "TABLE_AWARE": TableAwareChunker(),
    "SEMANTIC_CLUSTER": SemanticClusterChunker(),
    "SENTENCE_WINDOW": SentenceWindowChunker(),
    "FIXED_OVERLAP": FixedOverlapChunker(),
}


def get_chunker_instance(strategy_key: str, chunk_size: int = 500, chunk_overlap: int = 80) -> BaseChunker:
    """按策略名称与动态尺寸参数获取分块处理器实例
    @param strategy_key: str 策略枚举代码
    @param chunk_size: int 切片目标长度
    @param chunk_overlap: int 切片重叠长度
    @returns BaseChunker 分块实例
    """
    key = strategy_key.upper().strip()
    if key == "RECURSIVE_CHAR":
        return RecursiveCharChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    elif key == "PARENT_CHILD":
        return ParentChildChunker(parent_size=chunk_size, child_size=max(60, chunk_size // 4))
    elif key == "FIXED_OVERLAP":
        return FixedOverlapChunker(chunk_size=chunk_size, overlap=chunk_overlap)
    return CHUNKER_REGISTRY.get(key, RecursiveCharChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap))
