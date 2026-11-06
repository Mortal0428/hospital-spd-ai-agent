import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        for col, col_def in [
            ("enable_faithfulness_check", "TINYINT(1) DEFAULT 1"),
            ("enable_system_grounding", "TINYINT(1) DEFAULT 1"),
            ("default_chunking_mode", "VARCHAR(32) DEFAULT 'AGENT_AUTO'")
        ]:
            try:
                conn.execute(text(f"ALTER TABLE spd_modular_rag_config ADD COLUMN {col} {col_def}"))
                conn.commit()
                print(f"Added column {col}")
            except Exception as e:
                print(f"Notice {col}: {e}")

if __name__ == "__main__":
    migrate()
