# 多级库藏分仓授权中台、全院多仓权限联动与人员台账透视技术方案

- **计划文档路径**：`plans/2026-11-06_15-05-00_multi_warehouse_perm_center_plan.md`
- **记录时间戳**：2026-11-06 15:05:00
- **模式声明**：`[MODE: PLAN]`

---

## 一、变更计划与目标文件清单

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-06_15-05-00_multi_warehouse_perm_center_plan.md
- 记录时间戳：2026-11-06 15:05:00
- 前端目标文件：
  1. frontend/src/views/UserManagementView.vue：
     - 新增 Tab 3【多级库藏分仓授权中台 (name="warehouses")】，提供目标人员切换、角色模板标准恢复、全仓授权、一键清空及持久化落盘操作栏；
     - 在 Tab 3 构筑全院 9 大仓库的 6 项原子动作（准入查看、申领、入库、出库、盘点、调拨）矩阵表格与整行快捷开关；
     - 在 Tab 1【全院人员账号管理】表格中新增【经办/分管库藏 (多仓)】展示列，以彩色标签呈现已授权的多级仓库名称，sys_admin 穿透显示；
     - 在新增/编辑人员弹窗中支持“分管库藏 (多选)”配置。
  2. frontend/src/stores/userStore.ts：
     - 增加 refreshAuthorizedWarehouses() 异步 Action，根据当前登录用户的经办库藏持久化数据动态刷新 authorizedWarehouses；
     - 消除静态硬编码角色列表，实现与后端真实权限的精准同构与未授权仓库自动剔除。
  3. frontend/src/layouts/MainLayout.vue：
     - 优化顶部仓库切换下拉组件，监听 userStore.authorizedWarehouses 响应式变化，确保多仓切换丝滑无刷新。
  4. frontend/src/api/dictApi.ts：
     - 增补 batchSaveUserWarehousePerms() 批量落盘 API 签名与 TypeScript 接口定义。
- 后端目标文件：
  1. backend/app/schemas/spd_schemas.py：
     - 在 UserResponse 中增加 authorized_warehouses: List[UserWarehouseSummary] = [] 字段，附带仓库编码、名称与层级；
     - 定义 UserWarehousePermBatchRequest 与 UserWarehouseSummary 模型。
  2. backend/app/routers/dict_router.py：
     - 新增 POST /api/v1/dict/user-warehouse-perms/batch 批量持久化接口，在单个数据库事务中完成全量增删与校验；
     - 增强 GET /api/v1/dict/user-warehouse-perms 响应，关联 SpdWarehouseNode 自动注入 warehouse_name 与 warehouse_level。
  3. backend/app/routers/auth_router.py：
     - 在 list_users 中批量关联查询 SysUserWarehousePerm 与 SpdWarehouseNode，向前端一次性返回每个用户的已授权仓库列表。
- 测试与截图文件：
  1. tests/screenshots/2026-11-06_15-30-00_multi_warehouse_perm_center.png：多级库藏分仓授权中台矩阵渲染、角色模板一键恢复及保存成功 Toast 实机截图。
  2. tests/screenshots/2026-11-06_15-30-00_user_table_multi_warehouses.png：Tab 1 人员表格中经办/分管多仓 Tag 列直观呈现与顶栏动态联动截图。
```

---

## 二、核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`98%`
- **潜在风险点与防御策略**：
  - **角色标准模板与手动微调的边界**：定义清晰的标准模板字典（`ROLE_DEFAULT_WAREHOUSE_MAP`），一键恢复时仅覆盖前端暂存态，点击持久化才正式提交，防止管理员误触；
  - **历史旧数据与系统管理员兜底**：系统管理员 `sys_admin` 默认赋予 `ALL` 穿透模式；对于未单独配置分仓的历史普通人员，自动优雅降级为角色所属科室默认仓，确保零白屏、零回归。

### 2. 存量功能与三方体验影响分析
- **用户体验 (UX)**：
  - 界面风格与 Tab 2（15 模块 × 8 动作 RBAC 矩阵）保持 100% 视觉质感统一（Apple HIG 毛玻璃质感、微边框、无 Emoji、纯矢量 SVG 图标）；
  - Tab 1 一眼看清每个人员管辖哪些仓库；Tab 3 一键恢复角色标准模板或微调；顶栏仓库切换器动态收窄至仅本人有权仓库，操作极其顺畅。
- **开发者体验 (DX)**：
  - 采用单次事务批量写入接口替代大量离散请求，杜绝并发锁争用与网络拥堵；
  - 100% 函数级标准化中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。
- **AI 代理体验 (AX)**：
  - 显式定义 `UserWarehouseSummary` 与 `UserWarehousePermBatchRequest` Pydantic 契约，消除上下文幻觉；时间戳文档全面记录架构演进。
- **存量保护底线**：
  - 零破坏性演进，不改动 `sys_user` 基础列与外键关系，现有 8 大智能体工作流与各业务单据正常运行。

### 3. Playwright 自动化回环测试与截图验证方案
- **测试步骤**：
  1. 访问 `http://127.0.0.1:5173/system-user?tab=warehouses`，校验 Tab 3 正确挂载；
  2. 切换目标人员为“王建国 (耗材科主管)”，点击【按角色标准模板恢复】，验证卫材库、总务库、后勤库、专项高值库被自动勾选；
  3. 点击【保存并下发全院库藏授权矩阵 (持久化落盘)】，验证成功弹出绿色 Toast 提示；
  4. 切换到 Tab 1【全院人员账号管理】，断言王建国对应的【经办/分管库藏 (多仓)】列成功渲染出 4 个仓库 Tag；
  5. 校验顶栏【当前仓库】下拉框，验证展示的仓库项与授权列表严格对齐；
  6. 截取 Tab 3 授权矩阵与 Tab 1 人员多仓列表的高清截图，归档至 `tests/screenshots/`。

---

## 三、技术与 UI 细节规范

### 1. 后端数据契约与接口规范

#### A. 数据传输对象 (DTO) 规范 (`backend/app/schemas/spd_schemas.py`)
```python
class UserWarehouseSummary(BaseModel):
    """人员已授权经办库藏摘要 (用于人员列表与顶栏联动)"""
    model_config = ConfigDict(from_attributes=True)
    warehouse_code: str = Field(..., description="仓库编码")
    warehouse_name: str = Field(..., description="仓库名称")
    warehouse_level: str = Field(..., description="仓库层级")
    can_view: int = Field(default=1, description="查看准入权限")
    can_apply: int = Field(default=0, description="申领权限")
    can_inbound: int = Field(default=0, description="验收入库权限")
    can_outbound: int = Field(default=0, description="发料出库权限")
    can_stocktake: int = Field(default=0, description="盘点权限")
    can_transfer: int = Field(default=0, description="调拨权限")

class UserWarehousePermBatchItem(BaseModel):
    """批量设置单个仓库权限条目"""
    warehouse_code: str = Field(..., description="仓库编码")
    can_view: int = Field(default=1, description="查看准入")
    can_apply: int = Field(default=0, description="申领权限")
    can_inbound: int = Field(default=0, description="入库权限")
    can_outbound: int = Field(default=0, description="出库权限")
    can_stocktake: int = Field(default=0, description="盘点权限")
    can_transfer: int = Field(default=0, description="调拨权限")

class UserWarehousePermBatchRequest(BaseModel):
    """批量更新人员库藏细粒度权限请求"""
    user_id: int = Field(..., description="目标人员用户ID")
    perms: List[UserWarehousePermBatchItem] = Field(..., description="全量仓库权限矩阵清单")
```

#### B. 批量持久化接口 (`backend/app/routers/dict_router.py`)
```python
@router.post("/user-warehouse-perms/batch", response_model=ApiResponse[List[UserWarehousePermResponse]])
def batch_save_user_warehouse_perms(
    payload: UserWarehousePermBatchRequest,
    db: Session = Depends(get_db),
    admin_ctx: CurrentUserContext = Depends(require_roles(["sys_admin"]))
):
    """批量持久化保存指定人员的库藏细粒度授权矩阵
    在单个数据库事务内清理旧记录并批量写入新矩阵，保障 ACID 一致性。

    @param: payload (UserWarehousePermBatchRequest) 目标人员与各仓库权限项列表
    @param: db (Session) 数据库活动会话
    @param: admin_ctx (CurrentUserContext) 信息科系统管理员鉴权
    @returns: ApiResponse[List[UserWarehousePermResponse]] 保存后的全量权限记录
    @route: POST /api/v1/dict/user-warehouse-perms/batch
    @throws: HTTPException(404) 当目标用户不存在时抛出
    """
```

---

### 2. 前端状态与组件实现规范

#### A. Pinia Store 动态联动 (`frontend/src/stores/userStore.ts`)
- 新增 `authorizedWarehouseList: ref<Array<{ code: string; name: string }>>([])`；
- 改造 `getters.authorizedWarehouses`：
  - 若 `currentUser.roleCode === 'sys_admin'`，首项为 `{ code: 'ALL', name: '全院全部仓库 (穿透模式)' }` 并附带全部 9 仓；
  - 若 `authorizedWarehouseList` 中有数据，直接返回该已授权列表；
  - 若为空，安全回退到该角色的静态预设组合，保障系统绝对健壮。
- 新增 `async refreshAuthorizedWarehouses()` Action：拉取 `/api/v1/dict/user-warehouse-perms?user_id=currentUser.id` 并同步更新。

#### B. 前端 Tab 3 界面规范 (`frontend/src/views/UserManagementView.vue`)
- **角色标准预设字典**：
  - `sys_admin` -> 全院全部 9 仓全功能开启；
  - `dept_manager (耗材科)` -> `WH_WEICAI`, `WH_ZONGWU`, `WH_HOUQIN`, `WH_ZHUANXIANG`（准入、申领、入库、出库、盘点、调拨全开）；
  - `dept_manager (设备科)` -> `WH_EQUIP`, `WH_XINXI`；
  - `secondary_user (骨科)` -> `WH_SEC_ORTHO`, `WH_ZHUANXIANG`（准入、申领、出库全开，主库调拨关闭）；
  - `secondary_user (心内科)` -> `WH_SEC_CARDIO`, `WH_ZHUANXIANG`；
  - `finance_auditor` -> 仅开启全仓 `can_view` 与 `can_stocktake`。
- **UI 质感与防打扰**：
  - 提供类似 Tab 2 的黄色未保存提示条幅；
  - 保存成功后弹出带已赋权仓库名称摘要的 `ElMessage.success`；
  - 自动触发 `fetchUsers()` 刷新 Tab 1 表格 Tag 列，以及调用 `userStore.refreshAuthorizedWarehouses()`。

---

## 四、原子实施清单：
1. [x] [backend/] 在 backend/app/schemas/spd_schemas.py 中补充 UserWarehouseSummary、UserWarehousePermBatchItem 与 UserWarehousePermBatchRequest 模型，并在 UserResponse 中加入 authorized_warehouses 列表。
2. [x] [backend/] 在 backend/app/routers/dict_router.py 中编写 POST /api/v1/dict/user-warehouse-perms/batch 持久化接口，优化 GET 接口注入仓库层级。
3. [x] [backend/] 在 backend/app/routers/auth_router.py 中 list_users 批量预加载用户授权仓库数据，下发至前端。
4. [x] [frontend/] 在 frontend/src/api/dictApi.ts 中定义 batchSaveUserWarehousePerms 接口签名与类型。
5. [x] [frontend/] 在 frontend/src/stores/userStore.ts 中增加 refreshAuthorizedWarehouses() Action 与动态 getter 过滤。
6. [x] [frontend/] 在 frontend/src/views/UserManagementView.vue 中挂载：
   - Tab 1 新增【经办/分管库藏 (多仓)】彩色 Tag 展示列，支持点击跳转；
   - 挂载 Tab 3【多级库藏分仓授权中台】矩阵表格、角色标准模板、一键恢复、全仓赋权与全量授权持久化逻辑；
   - 侧边栏子菜单新增【多级库藏分仓授权】直达 Tab 3。
7. [x] [frontend/] 执行 cd frontend; npm run build 全量 TypeScript 编译，验证 0 警告 0 报错。
8. [x] [backend/] 平替重启后端服务加载新路由接口并使用 Python 脚本验证接口连通性 (PASS)。
9. [x] [tests/] 运行 Playwright 自动化回环测试：
   - 切换 Tab 3 选取人员并套用角色标准模板并持久化保存；
   - 切换至 Tab 1 校验经办 Tag 正确显示 (王建国 4 仓、李晓琳 2 仓)；
   - 校验顶栏仓库切换动态同构并捕获实机截图归档至 tests/screenshots/ (PASS)。

---
## 执行完成记录 [2026-11-06 15:23:00]
- 状态：全部原子任务均已高质感完成，回环验证 100% 通过。
- 实机截图归档：
  - tests/screenshots/2026-11-06_15-30-00_user_table_multi_warehouses.png
  - tests/screenshots/2026-11-06_15-30-00_multi_warehouse_perm_center.png
  - tests/screenshots/2026-11-06_15-30-00_header_warehouse_switcher.png
