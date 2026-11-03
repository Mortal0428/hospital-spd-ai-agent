"""认证、全院人员管理与科室架构路由模块

本模块提供三级角色登录鉴权、Token 签发、全院用户管理及科室架构树查询接口。
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user_context,
    require_roles,
    CurrentUserContext,
    mask_phone
)
from app.models.spd_models import SysDepartment, SysUser
from app.schemas.spd_schemas import (
    ApiResponse,
    LoginRequest,
    LoginResponse,
    UserCreateRequest,
    UserUpdateRequest,
    UserResetPasswordRequest,
    UserBatchActionRequest,
    UserResponse,
    DepartmentResponse
)

router = APIRouter(tags=["认证与人员权限"])


@router.post("/auth/login", response_model=ApiResponse[LoginResponse])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """用户登录接口：验证账号密码并返回 JWT 访问令牌与三级角色信息

    @param: payload (LoginRequest) 登录请求体，包含 username 与 password
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[LoginResponse] 包含 JWT 令牌、三级角色编码与归口科室
    @route: POST /api/v1/auth/login
    @throws: HTTPException(400) 当账号不存在、密码错误或已被禁用时抛出
    """
    user = db.query(SysUser).filter(SysUser.username == payload.username, SysUser.is_deleted == 0).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码不正确")

    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该账号已被冻结停用，请联系信息科管理员")

    dept = db.query(SysDepartment).filter(SysDepartment.id == user.dept_id).first()
    dept_name = dept.dept_name if dept else "未知科室"

    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "real_name": user.real_name,
        "role_code": user.role_code,
        "dept_id": user.dept_id,
        "dept_code": user.dept_code,
        "dept_name": dept_name
    }
    access_token = create_access_token(token_data)

    resp_data = LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        real_name=user.real_name,
        role_code=user.role_code,
        dept_id=user.dept_id,
        dept_code=user.dept_code,
        dept_name=dept_name
    )
    return ApiResponse(code=200, msg="登录成功", data=resp_data)


@router.get("/users/me", response_model=ApiResponse[LoginResponse])
def get_current_user_profile(user_ctx: CurrentUserContext = Depends(get_current_user_context)):
    """获取当前登录操作人员的档案与所属科室信息

    @param: user_ctx (CurrentUserContext) 当前操作人上下文
    @returns: ApiResponse[LoginResponse] 当前用户信息
    @route: GET /api/v1/users/me
    @throws: 无特定异常抛出
    """
    resp_data = LoginResponse(
        access_token="",
        token_type="bearer",
        user_id=user_ctx.id,
        username=user_ctx.username,
        real_name=user_ctx.real_name,
        role_code=user_ctx.role_code,
        dept_id=user_ctx.dept_id,
        dept_code=user_ctx.dept_code,
        dept_name=user_ctx.dept_name
    )
    return ApiResponse(code=200, msg="获取当前人员档案成功", data=resp_data)


@router.get("/departments", response_model=ApiResponse[List[DepartmentResponse]])
def get_all_departments(
    dept_type: Optional[str] = Query(None, description="按科室类型过滤"),
    db: Session = Depends(get_db)
):
    """查询全院科室与库房架构列表

    @param: dept_type (Optional[str]) 科室职能类型过滤
    @param: db (Session) 数据库活动会话
    @returns: ApiResponse[List[DepartmentResponse]] 科室列表
    @route: GET /api/v1/departments
    @throws: 无异常抛出
    """
    query = db.query(SysDepartment).filter(SysDepartment.status == 1)
    if dept_type:
        query = query.filter(SysDepartment.dept_type == dept_type)
    depts = query.order_by(SysDepartment.id.asc()).all()
    data = [DepartmentResponse.model_validate(d) for d in depts]
    return ApiResponse(code=200, msg="获取科室列表成功", data=data)


@router.get("/users", response_model=ApiResponse[List[UserResponse]])
def list_users(
    role_code: Optional[str] = Query(None, description="按角色筛选"),
    dept_id: Optional[int] = Query(None, description="按科室筛选"),
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """分页与多条件查询全院人员列表

    @param: role_code (Optional[str]) 角色过滤
    @param: dept_id (Optional[int]) 所属科室过滤
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权 (限 sys_admin 与 dept_manager)
    @returns: ApiResponse[List[UserResponse]] 人员清单
    @route: GET /api/v1/users
    @throws: 越权时抛出 403
    """
    query = db.query(SysUser).filter(SysUser.is_deleted == 0)
    if role_code:
        query = query.filter(SysUser.role_code == role_code)
    if dept_id:
        query = query.filter(SysUser.dept_id == dept_id)
    users = query.order_by(SysUser.id.asc()).all()
    data = [UserResponse.model_validate(u) for u in users]
    return ApiResponse(code=200, msg="获取人员列表成功", data=data)


@router.post("/users", response_model=ApiResponse[UserResponse])
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """信息科管理员新增系统操作人员账号

    @param: payload (UserCreateRequest) 用户创建请求体
    @param: db (Session) 数据库活动会话
    @param: _ 当前操作人鉴权 (仅限 sys_admin)
    @returns: ApiResponse[UserResponse] 创建的新增人员记录
    @route: POST /api/v1/users
    @throws: HTTPException(400) 用户名已存在或科室不存在时抛出
    """
    exists = db.query(SysUser).filter(SysUser.username == payload.username, SysUser.is_deleted == 0).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"登录账号 [{payload.username}] 已存在")

    dept = db.query(SysDepartment).filter(SysDepartment.id == payload.dept_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"所属科室ID [{payload.dept_id}] 不存在")

    new_user = SysUser(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        real_name=payload.real_name,
        role_code=payload.role_code,
        dept_id=dept.id,
        dept_code=dept.dept_code,
        phone_masked=mask_phone(payload.phone),
        status=1
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return ApiResponse(code=200, msg="人员账号添加成功", data=UserResponse.model_validate(new_user))


@router.put("/users/{user_id}", response_model=ApiResponse[UserResponse])
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """修改系统操作人员账号信息 (仅限信息科管理员)

    @param user_id: (int) 目标操作人员主键ID
    @param payload: (UserUpdateRequest) 修改信息载荷
    @param db: (Session) 数据库活动会话
    @param _: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[UserResponse] 更新后的人员数据对象
    @route: PUT /api/v1/users/{user_id}
    @throws: HTTPException(404) 当人员不存在时抛出
    """
    user = db.query(SysUser).filter(SysUser.id == user_id, SysUser.is_deleted == 0).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户ID [{user_id}] 不存在或已删除")

    if payload.real_name is not None:
        user.real_name = payload.real_name
    if payload.role_code is not None:
        user.role_code = payload.role_code
    if payload.dept_id is not None:
        dept = db.query(SysDepartment).filter(SysDepartment.id == payload.dept_id).first()
        if dept:
            user.dept_id = dept.id
            user.dept_code = dept.dept_code
    if payload.phone is not None:
        user.phone_masked = mask_phone(payload.phone)
    if payload.status is not None:
        user.status = payload.status

    db.commit()
    db.refresh(user)
    return ApiResponse(code=200, msg="人员账号信息修改成功", data=UserResponse.model_validate(user))


@router.delete("/users/{user_id}", response_model=ApiResponse[dict])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """软删除系统操作人员账号 (置 is_deleted=1)

    @param user_id: (int) 待删除人员主键ID
    @param db: (Session) 数据库活动会话
    @param _: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 删除结果
    @route: DELETE /api/v1/users/{user_id}
    @throws: HTTPException(404) 当用户不存在时抛出
    """
    user = db.query(SysUser).filter(SysUser.id == user_id, SysUser.is_deleted == 0).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户ID [{user_id}] 不存在或已删除")

    user.is_deleted = 1
    user.status = 0
    db.commit()
    return ApiResponse(code=200, msg=f"人员账号 [{user.username}] 已成功注销删除", data={"user_id": user_id})


@router.post("/users/{user_id}/reset-password", response_model=ApiResponse[dict])
def reset_user_password(
    user_id: int,
    payload: UserResetPasswordRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """信息科管理员重置指定操作人员登录密码

    @param user_id: (int) 目标操作人员主键ID
    @param payload: (UserResetPasswordRequest) 新密码载荷
    @param db: (Session) 数据库活动会话
    @param _: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 重置结果
    @route: POST /api/v1/users/{user_id}/reset-password
    @throws: HTTPException(404) 当用户不存在时抛出
    """
    user = db.query(SysUser).filter(SysUser.id == user_id, SysUser.is_deleted == 0).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户ID [{user_id}] 不存在或已删除")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return ApiResponse(code=200, msg=f"用户 [{user.real_name}] 密码已成功重置", data={"user_id": user_id})


@router.post("/users/batch-action", response_model=ApiResponse[dict])
def batch_user_actions(
    payload: UserBatchActionRequest,
    db: Session = Depends(get_db),
    _: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """批量人员操作 (批量启停/修改角色/软删除)

    @param payload: (UserBatchActionRequest) 批量操作载荷
    @param db: (Session) 数据库活动会话
    @param _: (CurrentUserContext) 当前操作人鉴权
    @returns: ApiResponse[dict] 执行结果与受影响行数
    @route: POST /api/v1/users/batch-action
    @throws: HTTPException(400) 当指令未知时抛出
    """
    users = db.query(SysUser).filter(SysUser.id.in_(payload.user_ids), SysUser.is_deleted == 0).all()
    count = 0
    for u in users:
        if payload.action == "ENABLE":
            u.status = 1
            count += 1
        elif payload.action == "DISABLE":
            u.status = 0
            count += 1
        elif payload.action == "DELETE":
            u.is_deleted = 1
            u.status = 0
            count += 1
        elif payload.action == "CHANGE_ROLE" and payload.target_role:
            u.role_code = payload.target_role
            count += 1

    db.commit()
    return ApiResponse(code=200, msg=f"批量操作 [{payload.action}] 成功，已生效 {count} 人", data={"affected_count": count})


class ChangeOwnPasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6, description="当前原密码")
    new_password: str = Field(..., min_length=6, description="拟修改的新密码")


class UpdateOwnProfileRequest(BaseModel):
    real_name: Optional[str] = Field(None, max_length=64, description="真实姓名")
    phone: Optional[str] = Field(None, max_length=20, description="联系手机号")


@router.post("/users/me/change-password", response_model=ApiResponse[dict])
def change_own_password(
    payload: ChangeOwnPasswordRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(get_current_user_context)
):
    """当前登录操作人员自主修改本人登录密码

    @param payload: (ChangeOwnPasswordRequest) 原密码与新密码载荷
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权上下文
    @returns: ApiResponse[dict] 修改结果
    @route: POST /api/v1/users/me/change-password
    @throws: HTTPException(400) 当原密码验证不通过时抛出
    """
    user = db.query(SysUser).filter(SysUser.id == user_ctx.id, SysUser.is_deleted == 0).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="当前人员档案不存在")

    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码不正确，请重新输入")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return ApiResponse(code=200, msg="密码修改成功，请牢记新密码", data={"user_id": user.id})


@router.put("/users/me/profile", response_model=ApiResponse[dict])
def update_own_profile(
    payload: UpdateOwnProfileRequest,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(get_current_user_context)
):
    """当前登录操作人员自主更新本人联系电话等基本档案信息

    @param payload: (UpdateOwnProfileRequest) 拟修改的联系电话或姓名
    @param db: (Session) 数据库活动会话
    @param user_ctx: (CurrentUserContext) 当前操作人鉴权上下文
    @returns: ApiResponse[dict] 更新结果
    @route: PUT /api/v1/users/me/profile
    @throws: HTTPException(404) 当人员档案不存在时抛出
    """
    user = db.query(SysUser).filter(SysUser.id == user_ctx.id, SysUser.is_deleted == 0).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="当前人员档案不存在")

    if payload.real_name:
        user.real_name = payload.real_name
    if payload.phone:
        user.phone_masked = mask_phone(payload.phone)

    db.commit()
    return ApiResponse(
        code=200,
        msg="个人档案信息已成功更新",
        data={
            "user_id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "phone_masked": user.phone_masked
        }
    )

