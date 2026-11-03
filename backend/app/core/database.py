"""SQLAlchemy 2.0 数据库引擎、会话工厂与自动建库模块

本模块管理本地 MySQL 8.0 数据库连接池、会话生命周期以及数据表自动同步与 Redis 缓存连接。
"""

import logging
from typing import Generator
import pymysql
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("spd.database")


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 统一声明式基类

    所有业务 ORM 模型必须继承自此类，并强制为表和所有字段提供中文 comment 注释。
    """
    pass


def ensure_database_exists() -> None:
    """初始化前检查并自动创建 MySQL 目标数据库

    @param: 无入参
    @returns: None
    @route: 内部模块调用链路 backend.app.core.database.ensure_database_exists
    @throws: 当 MySQL 服务不可达或用户密码错误时捕获并抛出详细异常信息
    """
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset="utf8mb4",
            connect_timeout=5
        )
        with conn.cursor() as cursor:
            create_db_sql = (
                f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DATABASE}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            cursor.execute(create_db_sql)
        conn.commit()
        conn.close()
        logger.info(f"MySQL 数据库 `{settings.MYSQL_DATABASE}` 已就绪")
    except Exception as exc:
        logger.error(f"连接 MySQL 创建数据库失败: {exc}")
        raise exc


# 确保数据库存在
ensure_database_exists()

# 构建 MySQL SQLAlchemy 2.0 驱动连接串
DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@"
    f"{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    "?charset=utf8mb4"
)

# 创建连接池与会话工厂
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库会话实例并确保请求结束时安全关闭

    @param: 无入参
    @returns: Generator[Session, None, None] 数据库会话生成器
    @route: 内部模块调用链路 backend.app.core.database.get_db
    @throws: 遇到未捕获异常时自动回滚会话并向上抛出
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_redis_client():
    """获取 Redis 客户端连接实例，具备低版本 RESP 协议降级与兜底容错

    @param: 无入参
    @returns: redis.Redis 客户端对象或具备基础操作的降级字典容器
    @route: 内部模块调用链路 backend.app.core.database.get_redis_client
    @throws: 连接异常时记录日志并返回简易内存降级对象，绝不阻断业务执行
    """
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            db=settings.REDIS_DB,
            protocol=2,
            decode_responses=True,
            socket_timeout=3
        )
        r.ping()
        return r
    except Exception as exc:
        logger.warning(f"Redis 连接异常，已自动平滑降级为内存容器模式: {exc}")

        class FallbackMemoryRedis:
            def __init__(self):
                self._store = {}

            def get(self, key):
                return self._store.get(key)

            def set(self, key, value, ex=None):
                self._store[key] = str(value)
                return True

            def delete(self, key):
                return self._store.pop(key, None) is not None

            def ping(self):
                return True

        return FallbackMemoryRedis()


redis_client = get_redis_client()
