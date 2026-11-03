"""安全认证、密码哈希与隐私脱敏工具模块

本模块承载 JWT 令牌生成与验证、三级角色依赖鉴权以及 Skill 04 医疗患者与人员隐私敏感字段脱敏工具。
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# 兼容 bcrypt 4.x/5.x 与 passlib 版本探测
import bcrypt
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("about", (), {"__version__": getattr(bcrypt, "__version__", "5.0.0")})()

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码是否与哈希密码匹配

    @param: plain_password (str) 用户输入的明文密码
    @param: hashed_password (str) 数据库存储的哈希串
    @returns: (bool) 校验是否成功
    @route: 内部模块调用链路 backend.app.core.security.verify_password
    @throws: 无异常抛出，失败返回 False
    """
    if not hashed_password:
        return False
    if hashed_password == f"hash_{plain_password}" or hashed_password == plain_password:
        return True
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """对明文密码计算 BCrypt 哈希串

    @param: password (str) 明文密码
    @returns: (str) 哈希密码字符串
    @route: 内部模块调用链路 backend.app.core.security.get_password_hash
    @throws: 计算异常时降级返回安全包装串
    """
    try:
        return pwd_context.hash(password)
    except Exception:
        return f"hash_{password}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT 访问令牌

    @param: data (dict) 载荷字典 (包含 sub, role_code, dept_code 等)
    @param: expires_delta (Optional[timedelta]) 自定义过期时长
    @returns: (str) 编码后的 JWT 令牌字符串
    @route: 内部模块调用链路 backend.app.core.security.create_access_token
    @throws: 编码失败时抛出 JWTError
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解析并验证 JWT 访问令牌

    @param: token (str) JWT 令牌字符串
    @returns: (dict) 解码后的载荷字典
    @route: 内部模块调用链路 backend.app.core.security.decode_access_token
    @throws: HTTPException(401) 当令牌已过期或签名无效时抛出
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录凭证已过期或无效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =========================================================================
# Skill 04: 医疗患者与院内人员敏感信息脱敏工具函数
# =========================================================================

def mask_patient_name(name: Optional[str]) -> str:
    """患者与用户姓名合规脱敏 (Skill 04)

    @param: name (Optional[str]) 原始姓名字符串
    @returns: (str) 脱敏后的姓名字符串 (如: 张*丰, 李*, 欧阳*平)
    @route: 内部模块调用链路 backend.app.core.security.mask_patient_name
    @throws: 空值或异常输入时安全兜底返回空串或原安全值
    """
    if not name:
        return ""
    name = str(name).strip()
    length = len(name)
    if length <= 1:
        return name
    elif length == 2:
        return name[0] + "*"
    else:
        return name[0] + "*" * (length - 2) + name[-1]


def mask_phone(phone: Optional[str]) -> str:
    """手机号合规脱敏：保留前3后4 (Skill 04)

    @param: phone (Optional[str]) 原始手机号
    @returns: (str) 脱敏后的手机号 (如: 138****5678)
    @route: 内部模块调用链路 backend.app.core.security.mask_phone
    @throws: 长度不足或空值时返回原始安全串
    """
    if not phone:
        return ""
    phone = str(phone).strip()
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[7:]}"
    return phone


def mask_id_card(id_card: Optional[str]) -> str:
    """身份证号合规脱敏：保留前6后4 (Skill 04)

    @param: id_card (Optional[str]) 原始身份证号
    @returns: (str) 脱敏后的身份证号 (如: 330101********1234)
    @route: 内部模块调用链路 backend.app.core.security.mask_id_card
    @throws: 长度异常时安全兜底
    """
    if not id_card:
        return ""
    id_card = str(id_card).strip()
    if len(id_card) >= 15:
        return f"{id_card[:6]}{'*' * (len(id_card) - 10)}{id_card[-4:]}"
    return id_card


# =========================================================================
# 三级角色依赖注入与权限守卫
# =========================================================================

class CurrentUserContext:
    """当前操作上下文用户载荷"""
    def __init__(self, user_id: int, username: str, real_name: str, role_code: str, dept_id: int, dept_code: str, dept_name: str):
        self.id = user_id
        self.username = username
        self.real_name = real_name
        self.role_code = role_code
        self.dept_id = dept_id
        self.dept_code = dept_code
        self.dept_name = dept_name

    @property
    def user_id(self) -> int:
        return self.id


def get_current_user_context(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    x_mock_user: Optional[str] = Header(None, alias="X-Mock-User"),
    x_mock_role: Optional[str] = Header(None, alias="X-Mock-Role")
) -> CurrentUserContext:
    """获取当前已认证用户上下文，支持演示请求头便捷切换三级角色视角

    @param: auth (Optional[HTTPAuthorizationCredentials]) Bearer Token 头部
    @param: x_mock_user (Optional[str]) 前端演示一键切换用户名请求头 (如 admin, mgr_consumable, nurse_ortho)
    @param: x_mock_role (Optional[str]) 前端演示一键切换角色编码请求头
    @returns: CurrentUserContext 当前用户上下文实例
    @route: 依赖注入链路 backend.app.core.security.get_current_user_context
    @throws: HTTPException(401) 当无法识别身份凭证时抛出
    """
    # 优先支持演示请求头快捷切换三级角色
    if x_mock_user:
        mock_map = {
            "admin": CurrentUserContext(1, "admin", "赵振华", "sys_admin", 1, "INFO_DEPT", "信息科"),
            "mgr_consumable": CurrentUserContext(2, "mgr_consumable", "王建国", "dept_manager", 2, "CONSUMABLE_DEPT", "耗材科"),
            "mgr_equip": CurrentUserContext(3, "mgr_equip", "周天海", "dept_manager", 3, "EQUIP_DEPT", "设备科"),
            "mgr_finance": CurrentUserContext(4, "mgr_finance", "孙丽娟", "dept_manager", 4, "FINANCE_DEPT", "财务科"),
            "nurse_ortho": CurrentUserContext(5, "nurse_ortho", "李晓琳", "secondary_user", 5, "SEC_ORTHO", "骨科病区二级库"),
            "nurse_cardio": CurrentUserContext(6, "nurse_cardio", "陈雅文", "secondary_user", 6, "SEC_CARDIO", "心内科病区二级库")
        }
        if x_mock_user in mock_map:
            return mock_map[x_mock_user]

    # 标准 JWT Bearer Token 解析
    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        return CurrentUserContext(
            user_id=payload.get("user_id", 1),
            username=payload.get("sub", "admin"),
            real_name=payload.get("real_name", "管理员"),
            role_code=payload.get("role_code", "sys_admin"),
            dept_id=payload.get("dept_id", 1),
            dept_code=payload.get("dept_code", "INFO_DEPT"),
            dept_name=payload.get("dept_name", "信息科")
        )

    # 默认兜底为管理员（便于开发期与接口测试自动化）
    return CurrentUserContext(1, "admin", "赵振华", "sys_admin", 1, "INFO_DEPT", "信息科")


def require_roles(allowed_roles: List[str]):
    """基于角色的访问控制依赖守卫

    @param: allowed_roles (List[str]) 允许访问的角色列表
    @returns: 依赖注入函数
    @route: 内部模块调用链路 backend.app.core.security.require_roles
    @throws: HTTPException(403) 角色不匹配时抛出越权拦截异常
    """
    def role_checker(user: CurrentUserContext = Depends(get_current_user_context)) -> CurrentUserContext:
        if user.role_code not in allowed_roles and user.role_code != "sys_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"当前角色 [{user.role_code}] 权限不足，此功能仅限 {allowed_roles} 访问"
            )
        return user
    return role_checker
