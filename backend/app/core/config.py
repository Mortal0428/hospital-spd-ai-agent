"""系统全局配置中心与环境变量读取模块

本模块负责集中加载并验证系统运行所需的数据库连接、Redis 缓存、向量库、大模型接口及安全密钥。
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# 计算后端根目录路径 (定位到 backend/.env)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """全局系统配置参数定义"""

    # 关系型数据库配置 (MySQL 8.0)
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "Cyx.chen27"
    MYSQL_DATABASE: str = "medical_spd_system"

    # Redis 缓存配置 (兼容 RESP2 协议)
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "12345678"
    REDIS_DB: int = 0
    REDIS_PROTOCOL: int = 2

    # Chroma 向量数据库与本地 Ollama 配置 (已校准本机真实模型)
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_EMBED_MODEL: str = "bge-m3:latest"
    OLLAMA_CHAT_MODEL: str = "qwen3.5:2b"
    OLLAMA_REASONING_MODEL: str = "deepseek-r1:1.5b"
    OLLAMA_BACKUP_EMBED_MODEL: str = "qwen3-embedding:0.6b"

    # 本地 Neo4j 知识图谱配置
    NEO4J_URI: str = "bolt://127.0.0.1:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "12345678"

    # 云端小米 MiMo 配置 (默认读取环境变量，支持自定义覆盖)
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "mimo")
    XIAOMI_MIMO_API_KEY: str = os.environ.get("MIMO_API_KEY", "")
    XIAOMI_MIMO_BASE_URL: str = os.environ.get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    XIAOMI_MIMO_MODEL: str = os.environ.get("MIMO_MODEL", "mimo-v2.6-flash")

    # LangSmith 全流程链路可观测追踪配置 (支持环境变量注入)
    LANGCHAIN_TRACING_V2: str = os.environ.get("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_ENDPOINT: str = os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: str = os.environ.get("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.environ.get("LANGCHAIN_PROJECT", "Personal")

    # 可选 Coze 智能体协同配置 (支持环境变量注入)
    COZE_ENABLED: bool = os.environ.get("COZE_ENABLED", "false").lower() in ("true", "1")
    COZE_API_TOKEN: str = os.environ.get("COZE_API_TOKEN", "")
    COZE_BOT_ID: str = os.environ.get("COZE_BOT_ID", "")
    COZE_BASE_URL: str = os.environ.get("COZE_BASE_URL", "https://api.coze.cn")
    COZE_TIMEOUT: int = 60

    # 飞书开放平台与群机器人 Webhook 直连配置 (双轨制：开放平台自建应用 + 自定义群机器人 Webhook)
    FEISHU_APP_ID: str = os.environ.get("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET: str = os.environ.get("FEISHU_APP_SECRET", "")
    FEISHU_WEBHOOK_URL: str = os.environ.get("FEISHU_WEBHOOK_URL", "")

    # JWT 认证与安全配置
    JWT_SECRET_KEY: str = "spd_super_secret_jwt_key_2026_hospital"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    class Config:
        """Pydantic 读取环境文件元配置"""
        env_file = str(ENV_FILE) if ENV_FILE.exists() else None
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    """获取单例配置实例并将 LangSmith 追踪参数注入环境变量

    @param: 无入参
    @returns: Settings 系统配置对象
    @route: 内部模块调用链路 backend.app.core.config.get_settings
    @throws: 若环境配置值格式错误可能抛出 ValidationError
    """
    s = Settings()
    if s.LANGCHAIN_TRACING_V2.lower() == "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = s.LANGCHAIN_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = s.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = s.LANGCHAIN_PROJECT
    return s


settings = get_settings()
