# api_spec.sample.md - RESTful 接口与通信契约规范模版

> 本文件承载 **Harness 组件①（接口渐进式披露源）** 与 **组件④（前后端通信强类型契约）**。复制至 `docs/api_spec.md` 作为项目的 API 规范基准。

---

## 1. 通用 HTTP 协议与响应体封装规范

所有后端接口必须返回统一的 JSON 格式响应体，严禁返回裸类型或非结构化文本：

```json
{
  "code": 200,
  "msg": "操作执行成功",
  "data": {}
}
```

- **成功状态**：`code = 200`，`data` 承载实际业务负载对象或数组；
- **客户端错误**：`code = 400`（参数验证失败）、`code = 401`（未登录/Token 过期）、`code = 403`（权限不足已阻断）；
- **服务端错误**：`code = 500`，统一返回友好提示，并在内部服务端打印带有堆栈的日志。

---

## 2. 函数级中文四要素注释铁律 (Mandatory JSDoc / Docstring)

所有后端路由控制器方法必须 100% 具备中文四要素注释：

```python
@router.post("/items", response_model=ApiResponse[ItemResponse])
async def create_item(
    payload: ItemCreateSchema,
    current_user: SysUser = Depends(get_current_active_user)
) -> ApiResponse[ItemResponse]:
    """创建并保存业务实体记录
    
    @param payload: ItemCreateSchema 待创建实体的入参校验模型
    @param current_user: SysUser 当前通过 Token 认证的登录用户实例
    @returns ApiResponse[ItemResponse] 包含新创建实体主键与基本属性的统一响应体
    @route POST /api/v1/items
    @throws HTTPException(400) 当实体编码重复或参数非法时抛出
    @throws HTTPException(403) 当当前角色无权执行新增时阻断
    """
    # 业务实现逻辑...
    pass
```
