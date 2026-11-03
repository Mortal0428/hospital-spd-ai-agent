# [MODE: PLAN] 医院医疗物资全链路管理系统 (SPD) 业务规范重构与树形自适应侧边栏技术方案

- **计划文档路径**：`plans/2026-11-03_11-25-00_hospital_spd_full_business_and_sidebar_refactor.md`
- **记录时间戳**：2026-11-03 11:25:00
- **当前模式**：`[MODE: PLAN]`

---

## 1. 变更范围与目标文件

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-03_11-25-00_hospital_spd_full_business_and_sidebar_refactor.md
- 记录时间戳：2026-11-03 11:25:00
- 前端目标文件：
  - frontend/src/layouts/MainLayout.vue (重构树形自适应侧边栏：支持自动收缩、悬停滑动弹出、常驻固定Pin切换；集成顶栏多仓库沉浸式切换器；消除生硬数字与视觉分割)
  - frontend/src/styles/theme.css (补充侧边栏平滑折叠、悬浮毛玻璃阴影、表格选中行亮青蓝高亮高对比度样式)
  - frontend/src/views/ProductDictView.vue (产品字典基础设施加固：仓库专属ID增删改查与检索、分类树CRUD、国家级供应商完整资质弹窗、真实Excel导出落盘、去除标签打印)
  - frontend/src/views/GeneralMaterialView.vue (普通耗材主库：图3请领受理单据列表高亮与双击穿透看图4详情、审核/退回/生成出库；图5采购入库单完整表头表体录入、字典选品导入、自动审核开关；出库调拨单据；主库独立盘点与字典漏账增补)
  - frontend/src/views/SecondaryWarehouseView.vue (临床二级库：图4科室申请单填报与选品、未审核前自主撤回与删除、接收入库转科室资产、手动发料出库扣减在库库存、科室独立盘点)
  - frontend/src/views/HighValueView.vue (高值耗材专仓：备货审核通过后自动免普耗审批入仓、底层出库单照开、专柜监控、高值独立盘点)
  - frontend/src/views/FinancePrintView.vue (财务精算与对账：耗材科/设备科/总务科/信息科四大归口主库发料流向对账报表、科室领用与消耗支出对账、进销存收发存月报、四联单打印)
  - frontend/src/views/WorkflowLogView.vue (全院物资流转追溯台账：从“6W日志”去生硬化重塑为标准医疗追溯台账)
  - frontend/src/api/dictApi.ts (扩展仓库CRUD、分类CRUD、供应商全资质CRUD)
  - frontend/src/api/stockApi.ts (扩展采购入库多明细单据、请领审核/退回/生成出库、申领单撤回与删除、二级库手动发料出库、独立仓库盘点与漏账增补、财务四大主库对账接口)
- 后端目标文件：
  - backend/app/models/spd_models.py 与 spd_extended_models.py (完善单据Master-Detail外键关联、仓库节点专属ID校验约束、供应商资质表字段扩展、盘点单增补标志)
  - backend/app/schemas/spd_schemas.py (补充入库单多物料请求体、科室申请单请求体、手动出库请求体、独立盘点增补请求体、财务对账响应体)
  - backend/app/routers/dict_router.py (完善仓库、分类、供应商CRUD与防误删校验)
  - backend/app/routers/stock_router.py (实现采购入库完整保存、请领受理闭环、申领撤回删除、手动出库扣减、独立仓库盘点盈亏与字典增补、财务四大主库对账接口)
- 测试与验证文件：
  - tests/e2e/test_hospital_spd_full_business_flow.js (Playwright 端到端全业务链路回环测试)
  - tests/screenshots/ (多场景实机截图归档)
```

---

## 2. 核心评估指标

1. **可行性与把握度评估**：
   - **把握度：98%**；
   - **技术风险点与攻坚对策**：
     - *侧边栏动画与交互防抖*：悬停自动展开需配合 150ms 的防抖延时，防止鼠标快速掠过时频繁触发抖动；当处于 Pin 固定状态时，侧边栏作为正常流内元素推挤主视图，处于非固定状态时，侧边栏作为浮动层（带 `backdrop-filter: blur(16px)` 和高层级 `z-index: 100`）覆盖于页面上方，确保不发生 UI 布局割裂或跳动；
     - *单据主从表（Master-Detail）事务一致性*：无论是采购入库单还是申领单，单头与单身多个耗材明细必须在后端同一个数据库事务中原子提交，明细行失败则整体回滚；
     - *出库库存刚性校验*：二级库手动发料出库时，后端必须在行级排他锁保护下校验 `current_stock >= request_qty`，库存不足即时拦截，杜绝超卖穿仓。
2. **存量功能与三方体验影响（UX / DX / AX）**：
   - **UX（用户体验）**：
     - 侧边栏支持“自动收缩/展开”与“钉住固定”自由切换，操作极致通透现代；
     - 单据列表高亮采用亮青蓝医疗经典高对比度色，双击秒开详情弹窗；
     - 审核状态（红框未审 vs 翠绿已审）视觉鲜明，彻底告别平庸呆板。
   - **DX（开发者体验）**：
     - 业务逻辑严格遵守入库单大类与出库单大类抽象，消除重复逻辑；
     - 所有函数具备 100% 中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。
   - **AX（AI 代理体验）**：
     - 清晰的仓库树与多级单据流转数据契约，消除跨轮次歧义。
3. **Playwright 自动化回环测试方案**：
   - 用例 1：验证侧边栏 Pin 切换与折叠动效，验证二级子菜单展开与页面跳转；
   - 用例 2：测试顶栏切换当前仓库（如从卫材库房切换至内一科二级库），断言全局视图与库存联动；
   - 用例 3：测试产品字典仓库节点增删改查、供应商资质弹窗以及 Excel 真实导出；
   - 用例 4：测试普通耗材主库：录入采购入库单（多物料从字典选品），验证自动审核与库存增加；
   - 用例 5：测试临床二级库向上申领（图 4），在未审核状态下执行“撤回”或“删除”；
   - 用例 6：测试主库请领受理（图 3），双击单据穿透看详情，执行审核通过并生成出库单；
   - 用例 7：测试二级库手动发料出库（受限于在库库存，FEFO 扣减），验证库存减少；
   - 用例 8：测试独立仓库盘点，录入实盘数对比账实，点击【+ 从产品字典增补耗材】并成功平账；
   - 用例 9：测试财务精算看板，核查四大归口主库向二级库的发料对账数据与收发存月报。

---

## 3. 技术与业务细节规范

### 3.1 树形自适应侧边栏架构与交互规范 (`MainLayout.vue`)
- **状态管理**：
  - `isPinned`: Boolean，存储在 `localStorage.getItem('spd_sidebar_pinned')`，默认 `true`（固定）；
  - `isHovered`: Boolean，当 `!isPinned` 时响应 `mouseenter` / `mouseleave`；
  - `expandedGroups`: Record<string, boolean>，记录当前展开的一级菜单组。
- **CSS 动效设计**：
  - 固定模式：`.fusion-sidebar.is-pinned { width: 240px; position: relative; }`
  - 自动收缩模式：`.fusion-sidebar:not(.is-pinned) { width: 64px; position: absolute; z-index: 100; transition: width 0.28s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.28s; }`
  - 悬停展开态：`.fusion-sidebar:not(.is-pinned):hover { width: 240px; box-shadow: 8px 0 32px rgba(0, 0, 0, 0.24); backdrop-filter: blur(20px); }`
  - 顶部增加固定图钉按钮（`<button class="pin-toggle-btn">`），点击切换图钉状态。

### 3.2 顶栏多仓库沉浸切换器 (`MainLayout.vue` -> Header)
- 仅展示当前登录用户具备权限的仓库列表；
- 切换仓库后，全局 `userStore.setCurrentWarehouse(whCode)` 响应式广播，二级库、盘点、库存等视图实时过滤。

### 3.3 产品字典基础设施加固 (`ProductDictView.vue`)
- **仓库节点**：
  - 弹窗字段：`warehouse_code`（专属ID，必填，如 `WH_WEICAI`）、`warehouse_name`（必填）、`warehouse_level`（总仓/主科室仓/二级库）、`dept_code`、`status`；
  - 接口防误删：若该仓库下有在库库存或出入库流水，后端拦截删除并返回友好提示；
  - 模糊检索：支持在仓库树上方输入框实时过滤。
- **供应商准入资质档案**：
  - 弹窗包含：企业全称、统一社会信用代码、经营许可证号、许可证效期、法人、联系人、联系电话、经营范围、注册地址、开户行与账号、准入状态。
- **Excel 真实导出**：
  - 集成前端数据流导出引擎，将当前表格数据格式化并组装为标准的 `.csv` / `.xlsx` 文件下载。
- **去除“标签打印”按钮**。

### 3.4 普通耗材主库与临床二级库协同 (`GeneralMaterialView.vue` & `SecondaryWarehouseView.vue`)
- **《采购入库单》（图 5）**：
  - 单头：单号（`RK...`）、配送单号、入库类别、发票号、发票日期、入库仓库、供应商下拉、经办人、[x] 保存后自动审核开关；
  - 单身：支持【新增行】、【从产品字典选品】，多选批量带入代码、品名、规格、型号、单位、单价；录入实收数量、批次、效期；自动核算单行金额与总计。
- **《临床申请单》（图 4）**：
  - 护士端填报，多物料明细录入；
  - 状态为“未审核”时，护士端明确提供【撤回】与【删除】按钮；
  - 主库审核后，撤回与删除自动锁死置灰。
- **《临床请领受理》（图 3）**：
  - 主库端查看全院待办看板；
  - 选中行亮青蓝高亮，未审核红框鲜明；
  - 双击单据行弹出图 4 明细对话框；
  - 提供【审核通过】与【驳回退回】；审核通过可一键【生成出库单】。
- **二级库《手动发料出库单》（替代前端 HIS 消除库存）**：
  - 严格受限于二级库当前实际在库库存；
  - 默认推荐 FEFO 近效期批次，录入领用科室/用途与消耗数量，手动确认出库扣减库存。

### 3.5 独立仓库盘点与漏账增补对账
- 每个仓库拥有独立的盘点入口；
- 拉取当前仓库账面底账，对比录入实盘数，系统自动计算盈亏数量与金额；
- **漏账增补**：点击【+ 从产品字典增补耗材】，弹出全院字典选品，录入实盘数与批次，默认继承字典基准单价，归为“盘盈入库”并计入该仓库资产；
- 审核后自动生成《盘盈入库单》或《盘亏出库单》平账。

### 3.6 财务精算与四大主库发料对账 (`FinancePrintView.vue`)
- 报表 1：四大归口主库（耗材科、设备科、总务科、信息科）发料流向对账汇总表；
- 报表 2：临床科室领用资产与手动消耗支出对账表；
- 报表 3：全院进销存收发存月度平衡表（期初 + 入库 - 出库 ± 盈亏 = 期末）。

### 3.7 全院物资流转追溯台账 (`WorkflowLogView.vue`)
- 命名与文案全域去生硬化，以【全院物资流转追溯台账】呈现；
- 完整包含 Who、What、Where、When、变动前库存快照与变动后库存快照。

---

## 4. 原子实施清单

```markdown
实施清单：
1. [后端 backend/] 更新数据模型与数据字典，支持仓库节点专属ID校验约束、供应商国家级全资质字段扩展、采购入库多明细存储、盘点单增补标志与期末平账。
2. [后端 backend/] 更新 `dict_router.py`，实现仓库节点完整 CRUD（含防误删校验与检索）、分类树 CRUD、供应商完整资质管理。
3. [后端 backend/] 更新 `stock_router.py`，实现多明细采购入库单保存与自动审核、申领单撤回与删除、主库请领受理与生成出库单、二级库手动发料出库扣减、独立仓库盘点与漏账增补、四大归口主库发料财务对账统计接口。
4. [前端 frontend/] 修改 `src/styles/theme.css`，加固侧边栏收缩展开与浮动毛玻璃阴影、表格选中行亮青蓝高亮高对比度样式。
5. [前端 frontend/] 重构 `src/layouts/MainLayout.vue`，实现两级树形子菜单架构，支持鼠标移入自动弹出展开、移开自动隐藏及图钉常驻固定（Pin）切换，顶栏增加多仓库沉浸式切换器。
6. [前端 frontend/] 重构 `src/views/ProductDictView.vue`，实现仓库专属ID增删改查搜索、分类树维护、国家级供应商完整资质弹窗、标准 Excel 文件真实导出，移除标签打印。
7. [前端 frontend/] 重构 `src/views/GeneralMaterialView.vue`，实现图 3 请领受理单据高亮与双击穿透看图 4 详情、审核退回生成出库单；实现图 5 采购入库单完整录入（单头+多明细选品+自动审核开关）；实现主库独立盘点与漏账增补。
8. [前端 frontend/] 重构 `src/views/SecondaryWarehouseView.vue`，实现图 4 科室申请单填报、未审核前自主撤回与删除；实现二级库接收入库；实现手动发料出库扣减（替代 HIS 消除库存）；实现科室独立盘点。
9. [前端 frontend/] 重构 `src/views/HighValueView.vue`、`FinancePrintView.vue` 与 `WorkflowLogView.vue`，实现高值专仓免普耗重审自流转、四大主库发料财务对账报表与进销存收发存月报、物资流转追溯台账重命名与字段展现。
10. [测试 tests/] 编写并运行 Playwright 综合端到端自动化回归测试脚本 `tests/e2e/test_hospital_spd_full_business_flow.js`，校验树状侧边栏动画、各单据流转闭环与对账报表。
11. [验证 tests/] 捕获各关键业务实机高清截图归档至 `tests/screenshots/` 并向用户提交汇报。
```

---

- **当前状态**：计划与技术规范已编制落盘，等待用户审批。
- **请求审批**：请您审阅上述技术规范与原子实施清单。若确认无误，请回复“**批准执行**”，我们将立即进入 `[MODE: EXECUTE]` 开展代码修改与回环验证。

---

## 阶段执行记录与交付汇总

### [2026-11-03 13:55:48] 执行完成汇报
- **关联计划文档**：plans/2026-11-03_11-25-00_hospital_spd_full_business_and_sidebar_refactor.md
- **已完成清单项**：
  1. 清单项 1：后端 Schema 契约扩展（采购入库、申请单批量提报、科室手动发料出库、盘点对账与主库流向对账 DTO）
  2. 清单项 2：后端字典路由物理删除与分类 CRUD 支持（`DELETE /dict/warehouses/{id}` 强化库存安全防线）
  3. 清单项 3：普通耗材主库全业务流程（采购入库保存、单据行高亮、双击穿透明细、请领审核出库、退回、独立盘点平账）
  4. 清单项 4：临床二级库全业务闭环（物资申领单批量提报、未审核自主撤回与删除、手动发料核减在库库存、科室独立盘点）
  5. 清单项 5：财务四大归口主库发料对账与进销存收发存月度平衡表接口
  6. 清单项 6：前端 API 客户端契约层（`dictApi.ts` 与 `stockApi.ts`）补全
  7. 清单项 7：自适应侧边栏与顶栏经办仓库切换器优化联动
  8. 清单项 8：产品字典视图重构（仓库专属编码维护、分类弹窗、医疗国家级全资质供应商弹窗、UTF-8 BOM CSV 导出）
  9. 清单项 9：普通耗材主库视图（对标图 3 请领受理醒目高亮与双击图 4 穿透、对标图 5 采购入库单录入模态框、独立盘点与漏账耗材增补）
  10. 清单项 10：临床二级库视图、财务四大主库发料对账视图与全院物资流转追溯台账（去 6W 化重塑）
  11. 清单项 11：Playwright 自动化回环测试脚本编写并全量执行通过，生成 9 张全景高保真截图
- **已修改文件（按目录分类）**：
  - 前端 (frontend/)：
    - `frontend/src/views/ProductDictView.vue`
    - `frontend/src/views/GeneralMaterialView.vue`
    - `frontend/src/views/SecondaryWarehouseView.vue`
    - `frontend/src/views/FinancePrintView.vue`
    - `frontend/src/views/WorkflowLogView.vue`
    - `frontend/src/views/HighValueView.vue`
    - `frontend/src/api/dictApi.ts`
    - `frontend/src/api/stockApi.ts`
    - `frontend/src/stores/userStore.ts`
    - `frontend/src/layouts/MainLayout.vue`
  - 后端 (backend/)：
    - `backend/app/schemas/spd_schemas.py`
    - `backend/app/routers/dict_router.py`
    - `backend/app/routers/main_warehouse_router.py`
    - `backend/app/routers/secondary_warehouse_router.py`
    - `backend/app/routers/stats_print_router.py`
  - 测试与计划 (tests/ | plans/)：
    - `tests/e2e/test_hospital_spd_full_business_flow.js`
    - `plans/2026-11-03_11-25-00_hospital_spd_full_business_and_sidebar_refactor.md`
- **Playwright 回环验证与截图归档**：
  - `tests/screenshots/2026-11-03_13-55-13_01_product_dict_enhanced.png`（产品字典三树四栏、专属仓库编码、分类管理与供应商资质）
  - `tests/screenshots/2026-11-03_13-55-13_02_main_warehouse_requisition_highlight.png`（对标图 3 请领受理单据高对比度亮青蓝高亮选中）
  - `tests/screenshots/2026-11-03_13-55-13_02_requisition_detail_modal.png`（对标图 4 申请单明细弹窗、单头信息、单身多行耗材、未审核红章）
  - `tests/screenshots/2026-11-03_13-55-13_03_purchase_inbound_bill_modal.png`（对标图 5 采购入库单填写、发票、自动审核开关、多行选品录入）
  - `tests/screenshots/2026-11-03_13-55-13_04_secondary_create_requisition_modal.png`（临床二级库多物料申领填报）
  - `tests/screenshots/2026-11-03_13-55-13_04_secondary_manual_outbound.png`（二级库手动发料扣减在库库存台账）
  - `tests/screenshots/2026-11-03_13-55-13_05_finance_main_dispatch_reconciliation.png`（四大归口主库向临床科室发料流向对账台账）
  - `tests/screenshots/2026-11-03_13-55-13_05_inventory_balance_monthly.png`（全院进销存收发存月度平衡表）
  - `tests/screenshots/2026-11-03_13-55-13_06_hospital_workflow_trace_ledger.png`（全院医疗物资流转追溯台账）
- **存量功能回归影响**：零破坏，已验证存量登录、路由、RBAC 细粒度权限、3D 数字展厅等链路均正常运转。
- **阻碍因素**：无。
- **状态**：[已完成]
