"""
@file __init__.py
@description RAG 物理分层解耦包初始化导出
"""

from app.services.rag.document_loader import extract_text_from_file_bytes
from app.services.rag.chunkers import CHUNKER_REGISTRY, BaseChunker
from app.services.rag.feature_radar import analyze_features_and_radar
from app.services.rag.hybrid_retriever import retrieve_chunks_hybrid

__all__ = [
    "extract_text_from_file_bytes",
    "CHUNKER_REGISTRY",
    "BaseChunker",
    "analyze_features_and_radar",
    "retrieve_chunks_hybrid"
]
