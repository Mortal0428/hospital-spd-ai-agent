# 404/500 报错彻底根除与全域单据化选品闭环规划

> 记录时间戳：2026-11-03 19:04:00  
> 任务标识：`404_500_ERROR_ELIMINATION_AND_VOUCHER_ALIGNMENT`  
> 责任 Agent：主调度统筹 Agent + 后端 FastAPI Agent + 前端 UI Agent + 质量护栏 Agent  

---

## 1. 变更计划与目标文件范围

[变更计划]
- 计划文档路径：`plans/2026-11-03_19-04-00_404_500_ERROR_ELIMINATION_AND_VOUCHER_ALIGNMENT_PLAN.md`
- 记录时间戳：`2026-11-03 19:04:00`
- 后端目标文件：
  - `backend/app/routers/main_warehouse_router.py`（修复采购入库、材料按需分发出库与盘点损益单在多明细批量持久化时的 `order_no` 唯一索引冲突）
  - `backend/app/routers/extended_spd_router.py`（修复 RBAC 批量赋权在插入新记录时 `username`、`role_code`、`module_name` 缺失导致的 MySQL 1048 非空约束异常）
  - `backend/app/routers/high_value_router.py`（补齐 `GET /lifecycle-orders` 端点，彻底消除高值专仓备货申请单查询 404，打通真实备货台账）
- 前端目标文件：
  - `frontend/src/components/StocktakePlanWorkbench.vue`（彻底剔除写死的 `/api/v1` 重复前缀，根除全院独立盘点加载与新建时的 404 气泡）
  - `frontend/src/views/HighValueView.vue`（优化备货申请单与退货单据状态流转，联动真实后端单据）
- 测试与截图目标文件：
  - `tests/e2e/test_error_elimination.js`（自动化校验采购入库 3 明细提交、RBAC 批量赋权、独立盘点新建、高值备货查询零 404/500 报错）
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_error_elimination_verified.png`（实机截图归档）

---

## 2. 核心评估指标

- **可行性与把握度评估**：`把握度：99%`。报错根因已通过真实 Uvicorn 运行时日志（`task-5138.log`）精准捕获堆栈并定位到具体代码行，技术方案清晰直接，零未知盲区。
- **存量功能与三方体验影响分析**：
  - **用户体验（UX）**：彻底消除页面加载与保存操作时频繁弹出的红色 `404 Not Found` 与 `500 Internal Server Error` 报错气泡；所有单据均支持自由添加多行明细并一键保存。
  - **开发者体验（DX）**：后端模型与路由约束严格契约对齐，遵循 Pydantic V2 与 SQLAlchemy 2.0 规范，提供 100% 中文四要素注释。
  - **AI 代理体验（AX）**：单据编号与明细行结构清晰，时间戳台账完备，杜绝上下文污染。
  - **存量保护与零回归底线**：不改动现有数据库表结构，单据凭证统一采用 `[主单号]-[分项序号]` 的成熟分单方案，向后兼容全部现有历史数据。
- **Playwright 自动化回环测试与截图验证方案**：
  - 启动持久化无锁测试浏览器，依次自动触发：
    1. 普通耗材主库 -> 填写入库单 -> 选品 3 项耗材并保存 -> 断言返回 HTTP 200 且入库台账新增对应记录；
    2. 主库独立盘点 -> 创建 2026年11月份盘点计划 -> 断言返回 HTTP 200 且底表正常拉取，无 404 弹窗；
    3. 系统管理员 -> RBAC 矩阵 -> 批量赋权 -> 断言批量设置成功，无 500 弹窗；
    4. 高值耗材专仓 -> 备货自动入仓 -> 断言成功拉取真实生命周期单据列表，无 404 弹窗；
  - 拦截浏览器 Console Error / PageError，捕获实机验证全景截图保存至 `tests/screenshots/`。

---

## 3. 技术与代码规范细节

### 3.1 后端采购入库多明细唯一键冲突修复规范 (`main_warehouse_router.py`)
```python
# 针对 SpdInboundAndOutboundOrder 表的 order_no unique 约束：
# 父级凭证号统一规范为：RK936...
# 各明细分项行 order_no 规范为：
# 当 items 数量为 1 时，直接使用 inbound_no；
# 当 items 数量 > 1 时，使用 f"{inbound_no}-{idx:02d}"；
# 同时统一将父级单据编号写入 source_ref_order_no 或 remark，确保整单追溯性与数据行唯一性并存。
```

### 3.2 后端 RBAC 批量赋权非空字段补全规范 (`extended_spd_router.py`)
```python
# 批量插入 SysUserModulePermission 记录前：
target_user = db.query(SysUser).filter(SysUser.id == req.user_id).first()
username = target_user.username if target_user else f"user_{req.user_id}"
role_code = target_user.role if target_user else "sys_admin"
module_name = MODULE_NAME_MAP.get(mod, mod)
# 确保 INSERT INTO sys_user_module_permission 时所有非空列均具备合法业务值。
```

### 3.3 后端高值全生命周期单据端点补齐规范 (`high_value_router.py`)
```python
@router.get("/lifecycle-orders", response_model=ApiResponse[List[dict]])
def list_high_value_lifecycle_orders(
    hv_biz_type: Optional[str] = Query(None, description="HV_STOCK_PREP | HV_DEPT_RETURN"),
    db: Session = Depends(get_db)
) -> ApiResponse[List[dict]]:
    """查询高值耗材备货申请单与科室退货单全生命周期单据列表"""
    # 按照 id 倒序拉取真实持久化数据，返回完整订单字典
```

### 3.4 前端独立盘点工作台 API 路径纠偏规范 (`StocktakePlanWorkbench.vue`)
```typescript
// 修正前：
await httpGet('/api/v1/ext/stocktake-plans', ...);
await httpPost('/api/v1/ext/stocktake-plans', ...);
await httpPost(`/api/v1/ext/stocktake-plans/${order_no}/settle`, ...);

// 修正后：
await httpGet('/ext/stocktake-plans', ...);
await httpPost('/ext/stocktake-plans', ...);
await httpPost(`/ext/stocktake-plans/${order_no}/settle`, ...);
```

---

## 4. 原子实施清单

实施清单：
1. [后端 `backend/app/routers/main_warehouse_router.py`]：修改 `create_purchase_inbound_order`、`create_dispatch_order` 与 `submit_main_stocktake`，实现多明细行索引化编号，彻底根治 MySQL 1062 唯一键重复冲突。
2. [后端 `backend/app/routers/extended_spd_router.py`]：完善 `post_rbac_batch_grant`，补全目标用户的 `username`、`role_code` 与 `module_name`，根除 MySQL 1048 非空约束错误。
3. [后端 `backend/app/routers/high_value_router.py`]：新增 `@router.get("/lifecycle-orders")` 路由端点，支持按业务类型查询真实高值备货与退货生命周期单据。
4. [前端 `frontend/src/components/StocktakePlanWorkbench.vue`]：修正 3 处写死 `/api/v1` 的请求路径为 `/ext/stocktake-plans`，彻底消除盘点模块 404 弹窗。
5. [前端编译构建 `frontend/`]：执行 `npm run build` 重新编译生成静态资源包，使本地预览服务同步最新代码。
6. [回环测试与截图交付 `tests/`]：编写并运行 `tests/e2e/test_error_elimination.js`，验证采购入库 3 明细、独立盘点、RBAC 批量赋权、高值备货全流程通畅，截图归档至 `tests/screenshots/`。
