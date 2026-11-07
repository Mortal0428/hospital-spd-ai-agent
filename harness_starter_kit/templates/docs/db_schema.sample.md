# db_schema.sample.md - 数据库设计与 100% comment 注释契约模版

> 本文件承载 **Harness 组件①（数据库渐进式披露源）** 与 **组件④（ORM 架构硬护栏）**。复制至 `docs/db_schema.md` 作为项目的数据库设计基准。

---

## 1. 建模强制铁律 (Strict Database Guardrails)

1. **引擎与字符集**：所有数据表统一采用 `InnoDB` 存储引擎，默认字符集为 `utf8mb4`，排序规则为 `utf8mb4_unicode_ci`；
2. **表级注释强制 100%**：每个 ORM 类必须声明 `__table_args__ = {"comment": "表中文业务说明"}`；
3. **字段级注释强制 100%**：每个 `mapped_column(...)` 必须显式包含 `comment="字段中文名 + 业务含义与枚举说明"`；
4. **主键与通用审计字段**：
   - 主键必须为非空整数自增或 UUID；
   - 包含标准审计字段：`created_at` (创建时间)、`updated_at` (更新时间)、`is_deleted` (软删除标记)。

---

## 2. 核心数据模型 ORM 样例 (SQLAlchemy 2.0 规范)

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, SmallInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """全局声明式 ORM 基类"""
    pass


class SysUser(Base):
    """系统用户与账户实体模型"""
    __tablename__ = "sys_user"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "comment": "系统用户信息主表"
    }

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="用户主键ID"
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, comment="登录登录名(唯一)"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="加密后的密码散列"
    )
    real_name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="用户真实姓名"
    )
    role_code: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="角色编码(admin/operator/auditor)"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, default=1, nullable=False, comment="账号状态(0:停用, 1:正常)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False, comment="记录创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="最后更新时间"
    )
```
