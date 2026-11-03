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

    # Redis 缓存配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "12345678"
    REDIS_DB: int = 0

    # Chroma 向量数据库与本地 Ollama 配置
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_CHAT_MODEL: str = "qwen2.5:7b"

    # 云端小米 MiMo 配置
    LLM_PROVIDER: str = "ollama"
    XIAOMI_MIMO_API_KEY: str = "your_xiaomi_mimo_api_key"
    XIAOMI_MIMO_BASE_URL: str = "https://api.xiaomi.com/v1"
    XIAOMI_MIMO_MODEL: str = "mimo-v2.6flash"

    # 可选 Coze 智能体协同配置
    COZE_ENABLED: bool = False
    COZE_API_TOKEN: str = "your_coze_pat_token"
    COZE_BOT_ID: str = "your_coze_bot_id"

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
    """获取单例配置实例

    @param: 无入参
    @returns: Settings 系统配置对象
    @route: 内部模块调用链路 backend.app.core.config.get_settings
    @throws: 若环境配置值格式错误可能抛出 ValidationError
    """
    return Settings()


settings = get_settings()
