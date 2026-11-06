"""
数据库迁移脚本：为 spd_modular_rag_config 表增补流式、思考开关、超时与分块配置字段
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        columns = [
            ("enable_streaming", "TINYINT DEFAULT 1 COMMENT '是否启用SSE流式输出打字机模式: 1-开启, 0-关闭'"),
            ("enable_deep_thinking", "TINYINT DEFAULT 1 COMMENT '是否启用长思考推理链路: 1-开启, 0-关闭'"),
            ("llm_timeout_seconds", "INT DEFAULT 60 COMMENT '大模型调用兜底超时上限(秒)'"),
            ("default_chunk_size", "INT DEFAULT 500 COMMENT '知识库文档默认切片字符数'"),
            ("default_chunk_overlap", "INT DEFAULT 80 COMMENT '知识库文档默认重叠字符数'")
        ]
        for col_name, col_def in columns:
            try:
                conn.execute(text(f"ALTER TABLE spd_modular_rag_config ADD COLUMN {col_name} {col_def};"))
                conn.commit()
                print(f"[OK] Added column: {col_name}")
            except Exception as e:
                print(f"[INFO] Column {col_name} check/add: {e}")

        conn.execute(text("UPDATE spd_modular_rag_config SET mimo_base_url='https://api.xiaomimimo.com/v1' WHERE mimo_base_url LIKE '%api.xiaomi.com%';"))
        conn.execute(text("UPDATE spd_modular_rag_config SET active_llm_provider='mimo' WHERE active_llm_provider='ollama';"))
        conn.commit()
        print("[OK] Migrated existing rows to https://api.xiaomimimo.com/v1 and mimo provider.")

if __name__ == "__main__":
    migrate()
