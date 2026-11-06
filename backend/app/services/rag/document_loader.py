"""
@file document_loader.py
@description 医疗多源异构规范文档高精度加载与纯文本解析引擎
支持多栏医疗法规 PDF (PyMuPDF/Fitz)、Word 临床路径 (.docx) 以及 Markdown / TXT。

@param content_bytes: bytes 文件字节流
@param filename: str 文件名
@returns str 抽取的规范化纯文本内容
@route internal://services/rag/document_loader
@throws 格式不支持或解析损坏时安全兜底
"""

import logging
import io
import pymupdf
import docx

logger = logging.getLogger("spd.rag.document_loader")


def extract_text_from_file_bytes(content_bytes: bytes, filename: str) -> str:
    """从上传文件二进制流中解析提取高纯度文本内容
    @param content_bytes: bytes 上传的文件字节流数据
    @param filename: str 原始文件名(用于推断文件类型扩展名)
    @returns str 提取后的纯文本正文内容
    @route internal://services/rag/document_loader/extract_text_from_file_bytes
    @throws 异常捕获并以安全降级 UTF-8 文本返回
    """
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    raw_text = ""

    if ext == "pdf":
        try:
            doc = pymupdf.open(stream=content_bytes, filetype="pdf")
            pages_text = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    pages_text.append(text.strip())
            doc.close()
            raw_text = "\n\n".join(pages_text).strip()
        except Exception as e:
            logger.warning(f"PyMuPDF 解析 PDF [{filename}] 失败: {e}，尝试字节流直接解码")
            raw_text = content_bytes.decode("utf-8", errors="ignore")

    elif ext in ["docx", "doc"]:
        try:
            doc = docx.Document(io.BytesIO(content_bytes))
            paras = []
            for p in doc.paragraphs:
                if p.text.strip():
                    paras.append(p.text.strip())
            # 表格单元格抽取
            for tbl in doc.tables:
                for row in tbl.rows:
                    row_txt = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                    if row_txt:
                        paras.append(f"| {row_txt} |")
            raw_text = "\n".join(paras).strip()
        except Exception as e:
            logger.warning(f"python-docx 解析 Word [{filename}] 失败: {e}")
            raw_text = content_bytes.decode("utf-8", errors="ignore")

    else:
        # Markdown / TXT / CSV / JSON
        raw_text = content_bytes.decode("utf-8", errors="ignore").strip()

    if not raw_text:
        raw_text = f"【文档解析兜底】文件 {filename} 为空或无有效可读文本内容。"

    return raw_text
