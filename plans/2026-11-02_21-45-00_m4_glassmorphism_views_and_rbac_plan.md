# 变更计划：全域业务视图 Demo 风格高质感自然延展与 RBAC 动态过滤 (Milestone M4)

- 计划文档路径：`plans/2026-11-02_21-45-00_m4_glassmorphism_views_and_rbac_plan.md`
- 记录时间戳：2026-11-02 21:45:00
- 前端目标文件：
  - `frontend/src/layouts/MainLayout.vue`（重构为 Fusion 现代毛玻璃工作台骨架，动态 RBAC 侧边栏与沉浸式顶栏）
  - `frontend/src/stores/userStore.ts`（增强离线与演示环境下 5 大角色的默认 RBAC 细粒度权限矩阵与动态响应）
  - `frontend/src/views/ProductDictView.vue`（4-stat KPI 网格、双树分类面板、精密数据表、按钮级 RBAC 过滤）
  - `frontend/src/views/GeneralMaterialView.vue`（4-stat KPI 网格、FEFO 近效期高亮、按需分发两阶段确认、按钮级 RBAC）
  - `frontend/src/views/HighValueView.vue`（4-stat KPI 网格、智能柜一物一码单品、扫码核销脱敏绑定、按钮级 RBAC）
  - `frontend/src/views/SecondaryWarehouseView.vue`（4-stat KPI 网格、科室切换 Pills、安全水位预警、申领模态框、按钮级 RBAC）
  - `frontend/src/views/WorkflowLogView.vue`（8 节点物权流转图谱、6W 要素明细表格、穿透溯源、按钮级 RBAC）
  - `frontend/src/views/FinancePrintView.vue`（多科室成本精算指标、耗占比考核、5 类医院法定四联单据打印引擎）
  - `frontend/src/views/SupplierPurchaseView.vue`（供应商资质审查横幅、采购订单协同、配货发货验收）
- 测试与截图文件：
  - `tests/e2e/showcase_regression.spec.ts`

## 核心评估指标
- **可行性与把握度评估**：把握度 98%。已完成原型比对、Design Tokens 梳理、现有接口协议与类型检查基准构建，生产构建 0 error 0 warning 通过。
- **存量功能与三方体验影响分析**：
  - **UX**：彻底消除白底灰边普通后台的视觉割裂，完美延展 `spd_integrated_showcase_demo.html` 和 `spd_frontend_design_variants.html` 的毛玻璃微边框质感与流畅微动效；
  - **DX**：保持清晰的组件与视图职责划分，所有函数严格遵循四要素中文注释（`@param`, `@returns`, `@route`, `@throws`），TypeScript 强类型保证；
  - **AX**：统一的 Design Tokens、显式的数据接口模型、0 Emoji 约束；
  - **存量兼容**：完全保留后端真实接口与前端现有业务调用链路（包括产品字典、出入库、两阶段确认、高值扫码、调拨等）。
- **Playwright 自动化回环测试与截图验证方案**：
  - 覆盖各角色视角登录、侧边栏菜单显隐校验、核心业务视图渲染、按钮级权限管控断言；
  - 实机截图捕获保存至 `tests/screenshots/`。

## 原子实施清单
1. **[frontend/src/stores/userStore.ts]**：为 `userStore.ts` 补充预设角色 RBAC 细粒度权限模板（确保离线与网络降级时各角色的 `can_view` 与动作权限 100% 准确生效，且管理员在抽屉中动态修改后可立即响应刷新）。
2. **[frontend/src/layouts/MainLayout.vue]**：重构为 Fusion 现代毛玻璃工作台骨架（20px 高斯模糊卡片、微边框发光、顶部沉浸式导航栏、角色快捷切换下拉选单、细粒度 RBAC 抽屉入口、3D 展厅跳板按钮与纯矢量 SvgIcon，严格按角色 `can_view` 过滤侧边栏 7 大菜单）。
3. **[frontend/src/views/ProductDictView.vue]**：重构为 Demo 延展风格（4-stat KPI 网格、双树分类面板、精密数据表行悬浮微光、按钮级 RBAC 过滤）。
4. **[frontend/src/views/GeneralMaterialView.vue]**：重构为 Demo 延展风格（4-stat KPI 网格、通透毛玻璃 Tabs、FEFO 近效期高亮排版、按需分发两阶段确认弹窗、按钮级 RBAC 过滤）。
5. **[frontend/src/views/HighValueView.vue]**：重构为 Demo 延展风格（4-stat KPI 网格、智能柜一物一码单品管理、扫码核销脱敏绑定、按钮级 RBAC 过滤）。
6. **[frontend/src/views/SecondaryWarehouseView.vue]**：重构为 Demo 延展风格（4-stat KPI 网格、科室切换 Pills、安全水位预警状态条、按需申领模态框、按钮级 RBAC 过滤）。
7. **[frontend/src/views/WorkflowLogView.vue]**：重构为 Demo 延展风格（8 节点流转图谱、6W 要素明细表格、穿透溯源、按钮级 RBAC 过滤）。
8. **[frontend/src/views/FinancePrintView.vue]**：重构为 Demo 延展风格（多科室成本精算指标、耗占比考核、5 类医院法定四联单据打印引擎与 `@media print` 打印版式优化）。
9. **[frontend/src/views/SupplierPurchaseView.vue]**：重构为 Demo 延展风格（供应商资质审查横幅、采购订单流转卡、发货与验收入库弹窗、按钮级 RBAC 过滤）。
10. **[编译与测试验证]**：运行 `npm --prefix frontend run build` 确保 0 错误 0 警告，执行全域 Emoji 零容忍扫描，完成自检。
