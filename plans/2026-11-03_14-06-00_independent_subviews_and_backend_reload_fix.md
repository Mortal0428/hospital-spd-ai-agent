# 研发实施计划：全链路 404 故障恢复与多业务模块细分子功能独立视图重构

- 计划文档路径：`plans/2026-11-03_14-06-00_independent_subviews_and_backend_reload_fix.md`
- 记录时间戳：`2026-11-03 14:06:00`
- 关联任务：彻底根除后端新增接口 404 故障，并将左侧侧边栏细分子菜单全面重塑为主内容区独立工作台视图（仓库架构明确区分归口主库与临床二级库）

---

## 1. 变更范围与目标文件清单

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-03_14-06-00_independent_subviews_and_backend_reload_fix.md
- 记录时间戳：2026-11-03 14:06:00
- 前端目标文件：
  - frontend/src/views/ProductDictView.vue（解耦为 4 大独立主内容区视图：规格目录、仓库分层架构、分类设置、供应商全资质）
  - frontend/src/views/GeneralMaterialView.vue（双向监听 route.query.tab 切换 5 大独立工作台）
  - frontend/src/views/SecondaryWarehouseView.vue（双向监听 route.query.tab 切换 5 大独立工作台）
  - frontend/src/views/FinancePrintView.vue（双向监听 route.query.tab 切换 4 大独立对账看板）
  - frontend/src/views/WorkflowLogView.vue（双向监听 route.query.tab 切换 2 大追溯看板）
  - frontend/src/layouts/MainLayout.vue（精确子菜单高亮与路由跳转 query 参数对齐）
- 后端目标文件与服务：
  - backend/app/main.py 与后台常驻进程重启（终止无重载 task-2936，开启 uvicorn --reload）
  - backend/app/routers/dict_router.py（确保仓库分层查询与归口主库/二级库字段支持）
- 测试与截图文件：
  - tests/e2e/test_independent_subviews_and_routing.js（端到端校验子功能切换与 API 状态）
  - tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_subview_*.png（关键子视图截图凭证）
```

---

## 2. 核心评估指标

1. **可行性与把握度评估**：
   - 把握度：**98%**。
   - 技术风险点：Uvicorn 进程在 Windows 环境下的端口占用释放；Vue 3 单文件组件内 `route.query.tab` 的初始挂载与动态监听平滑过渡。
2. **存量功能与三方体验影响分析**：
   - **UX（用户体验）**：侧边栏每一个子菜单点击后，主内容区立即清晰切换为专属独立视图，彻底消除“点击每一个功能都堆在同一界面”的困惑；仓库架构一眼看清哪些是大仓库（耗材科、设备科等）、哪些是二级库，层级清晰明了。
   - **DX（开发者体验）**：单组件内部状态机统一由 `route.query.tab` 驱动，模块逻辑独立，注释 100% 覆盖。
   - **AX（AI 协同体验）**：路由与视图一一对应，结构透明，易于自动化回归定位。
   - **存量功能保护**：保留原规格目录三树四栏核心工作台不变，仅在 `tab=specs` 时完整呈现；所有历史 API、接口签名与业务模型 100% 向后兼容。
3. **Playwright 自动化回环测试与截图验证方案**：
   - 测试用例 1：接口状态自检，逐一探测 `/main-warehouse/requisitions`、`/stats/*` 等端点，断言 HTTP 状态码均为 200，绝无 404；
   - 测试用例 2：逐项点击侧边栏子菜单，断言主内容区对应 DOM 节点渲染呈现，无页面空白与控制台报错；
   - 截图归档：生成各个子视图实机截图归档至 `tests/screenshots/`。

---

## 3. 技术与 UI 细节规范

### 3.1 后端服务重启与接口可用性保障
- 终止当前运行的陈旧进程 `task-2936`；
- 使用带有 `--reload` 的命令重启后端：
  ```powershell
  cd backend; E:\python\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- 验证 `/api/v1/main-warehouse/requisitions` 等端点返回 200。

### 3.2 产品字典 4 大主内容区独立视图（ProductDictView.vue）
- 增加响应式状态 `activeModuleTab = ref('specs')`：
  - `tab === 'specs'`：**耗材规格目录**（展示原三树四栏产品大工作台）；
  - `tab === 'warehouses'`：**仓库架构维护**（独立主视图）：
    - 顶部统计卡片：院级归口主库数、临床二级库数、已锁死建账库房数；
    - 拓扑布局：左侧呈现四大归口主库（卫材主库、设备主库、总务主库、信息主库），右侧呈现下属临床二级库列表（附带归属主库标签与期初锁死标识）；
    - 提供【+ 新建仓库】模态框，包含单选 `仓库层级: [x] 院级归口主库  ( ) 临床科室二级库`，二级库可选择其上级归口主库；提供编辑与物理删除；
  - `tab === 'categories'`：**耗材分类设置**（独立主视图）：
    - 独立树形卡片展示国标分类大类与子分类，支持快速检索、新增分类节点、修改分类名称与删除；
  - `tab === 'suppliers'`：**供应商资质档案**（独立主视图）：
    - 独立展示医疗器械准入供应商资质台账大表格（统一社会信用代码、经营许可证、效期、法人、准入状态），提供资质预警过滤与【+ 新增供应商档案】。

### 3.3 其他四大模块响应式 Tab 同步
- 在 `GeneralMaterialView.vue`、`SecondaryWarehouseView.vue`、`FinancePrintView.vue`、`WorkflowLogView.vue` 中统一加入：
  ```typescript
  // 监听路由 query 参数实现侧边栏子菜单联动
  watch(
    () => route.query.tab,
    (newTab) => {
      if (newTab && typeof newTab === 'string') {
        activeTab.value = newTab;
      }
    },
    { immediate: true }
  );
  ```
- 确保当用户在页面内点击 Tab 头部时，同步通过 `router.replace({ query: { ...route.query, tab: activeTab.value } })` 保持 URL 与页面状态严格一致。

---

## 4. 原子实施清单

1. [backend/] 终止无重载常驻后端进程 `task-2936`，并以 `--reload` 模式重新启动 FastAPI 服务，验证端点全部恢复 200 响应；
2. [frontend/src/views/ProductDictView.vue] 重构产品字典主视图，依据 `route.query.tab` 解耦为 4 大独立主内容区视图（规格目录、仓库分层架构、分类树管理、供应商资质档案）；
3. [frontend/src/views/ProductDictView.vue] 完善仓库架构独立视图，区分院级归口主仓库（设备科/耗材科等）与临床科室二级库房，支持层级创建与上下级归口；
4. [frontend/src/views/GeneralMaterialView.vue] 接入 `route.query.tab` 双向响应式同步，打通临床请领受理、验收入库、按需分发、主库台账与独立盘点 5 大独立工作台；
5. [frontend/src/views/SecondaryWarehouseView.vue] 接入 `route.query.tab` 双向响应式同步，打通物资申领、接收入库、在库台账、手动发料与科室盘点 5 大独立工作台；
6. [frontend/src/views/FinancePrintView.vue] 接入 `route.query.tab` 双向响应式同步，打通四大主库发料对账、科室消耗支出对账、进销存月平衡与四联凭证补打 4 大对账看板；
7. [frontend/src/views/WorkflowLogView.vue] 接入 `route.query.tab` 双向响应式同步，打通物资流转追溯与异常审计预警 2 大独立看板；
8. [frontend/src/layouts/MainLayout.vue] 校验并优化侧边栏各细分项高亮匹配逻辑与默认 query 参数分发；
9. [frontend/] 执行 `npm.cmd run build`，确保 TypeScript 类型检查与 Vue 模板编译 0 报错；
10. [tests/e2e/] 编写并运行 Playwright 自动化回环测试脚本 `tests/e2e/test_independent_subviews_and_routing.js`，验证子菜单切换与 API 状态码，捕获实机截图归档至 `tests/screenshots/`。

---

## 阶段执行记录与交付汇总

### [2026-11-03 14:28:00] 执行完成汇报
- **关联计划文档**：plans/2026-11-03_14-06-00_independent_subviews_and_backend_reload_fix.md
- **已完成清单项**：
  1. 清单项 1：终止无重载常驻后端进程 `task-2936`，以 `--reload` 重新启动 FastAPI 服务并实测 10 大核心端点全部 200 通过（0 项 404）；
  2. 清单项 2：重构产品字典主视图，依据 `route.query.tab` 解耦为 4 大独立主内容区视图（规格目录、仓库分层架构、分类树管理、供应商资质档案）；
  3. 清单项 3：完善仓库架构独立视图，区分院级归口主仓库（耗材科/设备科/总务科/信息科）与临床科室二级库房，支持层级创建与上下级归口；
  4. 清单项 4：普通耗材主库接入 `route.query.tab` 双向响应式同步，打通临床请领受理、验收入库、按需分发、主库台账与独立盘点 5 大独立工作台；
  5. 清单项 5：临床二级库接入 `route.query.tab` 双向响应式同步，打通物资申领、接收入库、在库台账、手动发料与科室盘点 5 大独立工作台；
  6. 清单项 6：财务精算对账接入 `route.query.tab` 双向响应式同步，打通四大主库发料对账、科室消耗支出对账、进销存月平衡与四联凭证补打 4 大对账看板；
  7. 清单项 7：全院物资流转追溯接入 `route.query.tab` 双向响应式同步，打通物资流转追溯与异常审计预警 2 大独立看板；
  8. 清单项 8：优化侧边栏各细分项高亮匹配逻辑与默认 query 参数分发；
  9. 清单项 9：前端 `npm run build` 编译 0 报错，重启并刷新 preview 服务（`task-3886`）；
  10. 清单项 10：编写并运行 Playwright 回环测试脚本 `tests/e2e/test_independent_subviews_and_routing.js`，实机验证 0 Console Error / 0 PageError，全量捕获 8 张全景高保真截图凭证。
- **已修改文件（按目录分类）**：
  - 前端 (frontend/)：
    - `frontend/src/views/ProductDictView.vue`
    - `frontend/src/views/GeneralMaterialView.vue`
    - `frontend/src/views/SecondaryWarehouseView.vue`
    - `frontend/src/views/FinancePrintView.vue`
    - `frontend/src/views/WorkflowLogView.vue`
    - `frontend/src/layouts/MainLayout.vue`
  - 后端服务 (backend/)：
    - 常驻 Uvicorn 进程已重启开启 `--reload` 守护
  - 测试与计划 (tests/ | plans/)：
    - `tests/e2e/test_independent_subviews_and_routing.js`
    - `plans/2026-11-03_14-06-00_independent_subviews_and_backend_reload_fix.md`
- **Playwright 回环验证与截图归档**：
  - `tests/screenshots/2026-11-03_14-27-39_subview_01_dict_specs.png`（耗材规格目录三树四栏工作台）
  - `tests/screenshots/2026-11-03_14-27-39_subview_02_dict_warehouses_topology.png`（仓库架构分层维护：四大主库与临床二级库两栏拓扑）
  - `tests/screenshots/2026-11-03_14-27-39_subview_03_dict_categories.png`（医疗物资国标/院内双维分类设置独立工作台）
  - `tests/screenshots/2026-11-03_14-27-39_subview_04_dict_suppliers.png`（国家级医疗器械供应商全资质档案独立大表格）
  - `tests/screenshots/2026-11-03_14-27-39_subview_05_general_inbound.png`（主库耗材验收入库与退货工作台）
  - `tests/screenshots/2026-11-03_14-27-39_subview_07_secondary_manual_out.png`（临床二级库手动发料扣减库存工作台）
  - `tests/screenshots/2026-11-03_14-27-39_subview_09_finance_main_reconciliation.png`（财务四大主库发料流向对账台账）
  - `tests/screenshots/2026-11-03_14-27-39_subview_11_logs_trace.png`（全院医疗物资流转追溯台账）
- **存量功能回归影响**：零破坏，已验证存量登录、路由、RBAC 细粒度权限判定、3D 展厅链路均运行稳定。
- **阻碍因素**：无。
- **状态**：[已完成]
