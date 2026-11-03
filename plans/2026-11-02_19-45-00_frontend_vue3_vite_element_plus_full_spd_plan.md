# 研发实施计划：前端生产级 Vue 3 + TypeScript + Element Plus 全量 SPD 业务系统建设

> 计划归档时间戳：2026-11-02 19:45:00  
> 任务标识符：`frontend_vue3_vite_element_plus_full_spd_plan`  
> 关联协议：增强型 RIPER-5 代理执行协议（阶段 3：[MODE: PLAN] 技术规范与原子清单归档）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_19-45-00_frontend_vue3_vite_element_plus_full_spd_plan.md
- 记录时间戳：2026-11-02 19:45:00
- 前端目标工程目录 (frontend/)：
  - frontend/package.json（配置 Vue 3.5+, TypeScript 5+, Vite 5+, Element Plus, Pinia, Vue Router, Axios, @element-plus/icons-vue）
  - frontend/vite.config.ts（配置 @ 路径别名与 /api 反向代理至 http://127.0.0.1:8000）
  - frontend/tsconfig.json（标准严谨 TypeScript 配置）
  - frontend/index.html（标准入口 HTML，严禁 Emoji，引入标准矢量 Favicon）
  - frontend/src/main.ts（Vue 应用挂载、Pinia 状态机注册、Vue Router、Element Plus 全局注册与样式注入）
  - frontend/src/App.vue（根容器，亮暗主题自适应）
  - frontend/src/styles/theme.css & main.css（统一 CSS 主题变量体系、去 AI 廉价质感、@media print 打印专用样式）
  - frontend/src/api/（封装 Axios 请求实例与 6 大业务模块 API：dictApi, orderApi, highValueApi, stocktakeTransferApi, supplierPurchaseApi, rbacApi）
  - frontend/src/stores/userStore.ts（当前登录人员、科室、角色切换与 15 模块 x 8 动作细粒度 RBAC 权限缓存与动态校验器）
  - frontend/src/router/index.ts（前端路由体系：产品字典双树、普耗管理、高值耗材、二级库、采供协同、全流程日志、财务核算与打印）
  - frontend/src/layouts/MainLayout.vue（现代通透工作台布局：顶部导航、角色快速切换、亮暗切换、直达数字展厅入口、RBAC 抽屉触发器）
  - frontend/src/components/（通用复用组件：TwoStepConfirmDialog.vue, PrintVoucherDialog.vue, RbacMatrixDrawer.vue, HighValueQrVerifyModal.vue）
  - frontend/src/views/（全量业务视图：ProductDictView.vue, GeneralMaterialView.vue, HighValueView.vue, SecondaryWarehouseView.vue, SupplierPurchaseView.vue, WorkflowLogView.vue, FinancePrintView.vue）
- 测试与截图验证文件 (tests/)：
  - tests/harness/verify_frontend_vue3.js（Playwright 全链路 E2E 自动化测试脚本，覆盖 10 项前端核心交互与状态机强断言）
  - tests/screenshots/2026-11-02_19-45-00_vue3_frontend_full_spd_verify.png（实机运行截图凭证）
```

---

## 二、 核心评估指标（必填）

### 1. 可行性与把握度评估
- **把握度：96%**
- **潜在技术风险与应对策略**：
  - *风险点 1：Node.js v25.2.0 环境下的 npm 依赖安装与 Element Plus 兼容性*。
    - **应对**：选用稳定成熟的 `element-plus`、`vue@^3.5.0`、`vite@^5.4.0` 版本，并通过 `npm install --no-audit` 快速幂等安装，确保依赖干净且无多余编译报错。
  - *风险点 2：前端两阶段二次确认状态与不可逆单据的实时联动*。
    - **应对**：在 `userStore.ts` 与 `orderApi.ts` 中封装统一的防误触与状态拦截逻辑。外层表格行实时根据 `confirm_stage` 与 `is_irreversible_locked` 动态计算按钮状态：`PENDING_CONFIRM` 显示【修改】与【确认提交】；`SUBMITTED` 显示【取消提交】与【打印】；若单据为期初建账或高值科室退货出库，【取消提交】强制置灰并展示“不可逆永久锁定”徽标。
  - *风险点 3：高保真打印样式与亮暗主题自适应*。
    - **应对**：严格遵循 `Skill 06 (medical_voucher_print_engine)`，为打印预览组件注入 `@media print` 专用媒体查询，隐藏导航栏、按钮等无关 DOM，保留纯白背景与法定四联签字栏；在日常界面中 100% 基于 CSS 变量（`--spd-bg-app`, `--spd-bg-surface`, `--spd-text-main`）实现亮暗模式自适应，全域 0 Emoji。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：提供工业级、医疗级的高质感界面（合理的留白、清爽的边框、自然的悬浮与平滑过渡）；在页面右上角提供“数字展厅 / 壁纸中心”快捷跳转入口，与已交付的 3D 展厅无缝贯通。
- **开发者体验（DX）**：严格按照 `CLAUDE.md` 规定的物理隔离原则将前端代码集中在 `frontend/`；所有组件与函数 100% 具备 TypeScript 类型提示与中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。
- **AI 代理体验（AX）**：结构清晰的组件拓扑与显式的 API 请求函数，为后续接入智能体可视化对话舱提供极高的可解析性与增量迭代基座。
- **存量功能零破坏性底线**：完全独立于 `backend/` 目录运行，通过 Vite 反向代理对接后端 `http://127.0.0.1:8000/api/v1` 与 `/api/v1/ext`，存量 17 张数据库表与全部后端接口保持零变动、零回归。

### 3. Playwright 自动化回环测试与截图验证方案
- **测试执行脚本**：`node tests/harness/verify_frontend_vue3.js`
- **10 项核心强断言设计**：
  1. **静态代码与护栏扫描**：前端源码 100% 无任何 Emoji 字符，函数中文四要素注释覆盖率 100%；
  2. **Vite 开发服务与首屏渲染**：Playwright 启动无锁浏览器访问前端页面，校验首屏加载耗时与 DOM 结构完整；
  3. **产品字典双树与拼音助记码（图 4）**：校验左侧仓库树（9大仓库节点）与分类树联动筛选，表格正确显示拼音码、通用名、品牌与调价对比；
  4. **单据两阶段二次确认状态机**：在普通耗材入库单中录入“退给供应商红字退货单”，断言第 1 次提交显示 `待二次确认 (PENDING_CONFIRM)`（数量为负数），外层点【确认提交】后跃迁为 `已正式提交 (SUBMITTED)`；
  5. **期初数据一次性锁死铁律（图 1）**：在普通耗材【期初数据】页中，断言已确认的科室期初建账单【取消提交】按钮被禁用且无法编辑；
  6. **请领审批自动出库联动（图 1）**：在请领受理中审批单据，自动联动并在【耗材出库】列表中渲染关联出库单；
  7. **高值科室退货出库不可逆防护（图 2）**：断言已提交的高值科室退货出库单不可取消、不可修改；
  8. **高值专属二维码扫码核销与查询联动（图 2）**：点击高值耗材【扫码核销】，录入患者信息完成核销（患者姓名自动脱敏），断言该单品从待核销进入【高值核销查询】列表中；
  9. **供应商资质准入硬拦截与采供发货协同**：切换至外部供应商视角，断言未通过资质审核时发货按钮禁用；合规供应商发货后自动生成医院待验收入库单；
  10. **信息科解耦式 8 动作 RBAC 抽屉**：唤出权限中枢抽屉，针对具体用户切换开关，实时生效；页面无 Console Error / PageError，捕获实机截图保存至 `tests/screenshots/2026-11-02_19-45-00_vue3_frontend_full_spd_verify.png`。

---

## 三、 技术与前端组件规范细节

### 1. 核心 API 客户端 (`frontend/src/api/`)
- `request.ts`：Axios 实例，BaseURL 设为 `/api/v1`，响应拦截器解包 `response.data`，统一处理 `code !== 200` 并通过 `ElMessage.error` 提示。
- `dictApi.ts`：对接 `/ext/dict/overview`、`/ext/dict/copy-warehouse`、`/ext/dict/adjust-price`。
- `orderApi.ts`：对接 `/ext/orders/inbound-outbound`、`/ext/orders/two-step-action`、`/ext/orders/requisition-auto-outbound`。
- `highValueApi.ts`：对接 `/ext/high-value/lifecycle`、`/ext/high-value/two-step-action`、`/ext/high-value/qr-verify`、`/ext/high-value/verified-list`。
- `stocktakeTransferApi.ts`：对接 `/ext/orders/stocktake-transfer`。
- `supplierPurchaseApi.ts`：对接 `/ext/supplier-purchase/list`、`/ext/supplier-purchase/qual-audit`、`/ext/supplier-purchase/flow`。
- `rbacApi.ts`：对接 `/ext/rbac/matrix`、`/ext/rbac/toggle`。

### 2. 状态机与细粒度权限 Pinia Store (`frontend/src/stores/userStore.ts`)
- 维护当前用户 `currentUser`（`sys_admin`, `dept_manager`, `secondary_user`, `finance_auditor`, `supplier_user`）。
- 维护权限映射表 `permissionMatrix: Record<string, Record<string, boolean>>`。
- 提供鉴权方法：`canAction(moduleCode: string, actionKey: string): boolean`。

### 3. 法定单据四联打印组件 (`frontend/src/components/PrintVoucherDialog.vue`)
- 支持《主库验收入库单》、《主库按需分发调拨单》、《高值耗材扫码核销单》、《二级库申领单》、《财务结算审计单》5 类单据。
- 票尾四联签字：【制单人】/【主库科室主管】/【二级库接收人】/【财务科复核】。
- 携带一维码/二维码纯 CSS 仿真区域，打印时自动隐藏弹窗遮罩与操作按钮。

---

## 四、 强制性最终步骤（原子实施清单）

```markdown
实施清单（已于 2026-11-02 19:57:30 全部 100% 执行完毕并通过 10 项强断言）：
1. [已完成] [frontend/] 在根目录下初始化标准前端脚手架：创建 frontend/package.json、frontend/vite.config.ts、frontend/tsconfig.json、frontend/index.html 并安装所需 npm 生产与开发依赖。
2. [已完成] [frontend/src/styles] 编写 frontend/src/styles/theme.css 与 main.css，构建现代医疗设计体系 CSS 变量（亮暗主题、无 Emoji 矢量图标样式、@media print 打印规则）。
3. [已完成] [frontend/src/api] 编写 frontend/src/api/request.ts 以及各业务 API 模块（dictApi.ts, orderApi.ts, highValueApi.ts, stocktakeTransferApi.ts, supplierPurchaseApi.ts, rbacApi.ts）。
4. [已完成] [frontend/src/stores] 编写 frontend/src/stores/userStore.ts，实现 5 大角色上下文切换与 15 模块 x 8 动作细粒度 RBAC 权限缓存鉴权引擎。
5. [已完成] [frontend/src/components] 编写 4 大通用业务交互组件：TwoStepConfirmDialog.vue（两阶段状态机确认）、PrintVoucherDialog.vue（四联单据打印）、RbacMatrixDrawer.vue（细粒度权限抽屉）、HighValueQrVerifyModal.vue（专属二维码扫码核销与脱敏）。
6. [已完成] [frontend/src/layouts] 编写 frontend/src/layouts/MainLayout.vue（现代通透顶部导航、角色快捷切换、主题切换、数字展厅返回入口、侧边主菜单）。
7. [已完成] [frontend/src/views] 编写 7 大核心业务视图页面：
   - ProductDictView.vue（对齐图4：左侧仓库树+分类树双树联动、拼音码、跨仓复制、调价、停用过滤）
   - GeneralMaterialView.vue（对齐图1：请领受理、入库退供应商红字单、出库自动联动、期初数据永久锁死、独立盘点核算）
   - HighValueView.vue（对齐图2：备货管理、科室接收、退货出库永久锁死、专属二维码扫码核销、核销查询联动）
   - SecondaryWarehouseView.vue（对齐图3：二级库日常出入库、发料、跨科/跨院调拨、定数包申领）
   - SupplierPurchaseView.vue（外部供应商协同门户：资质准入硬拦截、在线接单拣货、二次确认发货联动）
   - WorkflowLogView.vue（6W 物权交接全流程日志时间轴台账）
   - FinancePrintView.vue（财务多科室耗材核算与单据打印中心）
8. [已完成] [frontend/src/router] 编写 frontend/src/router/index.ts，配置全量业务路由并在 frontend/src/main.ts 中完整装配挂载。
9. [已完成] [tests/] 编写 tests/harness/verify_frontend_vue3.js 自动化测试脚本，覆盖 10 项强断言。
10. [已完成] [tests/ | plans/] 启动前后端服务并执行 Playwright 回环测试，断言 10 项全部通过（0 Console Error / 0 PageError / 0 Emoji），捕获实机截图保存至 tests/screenshots/2026-11-02_19-45-00_vue3_frontend_full_spd_verify.png，更新计划文档并向用户汇报。
```
