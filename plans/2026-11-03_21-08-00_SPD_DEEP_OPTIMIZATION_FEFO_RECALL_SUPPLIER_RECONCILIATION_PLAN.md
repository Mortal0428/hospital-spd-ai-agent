# 医疗物资全链路 SPD 系统深度业务优化与功能完善实施计划书

> 计划归档时间戳：2026-11-03 21:08:00  
> 任务唯一标识：`SPD_DEEP_OPTIMIZATION_FEFO_RECALL_SUPPLIER_RECONCILIATION`  
> 方案设计原则：三甲医院医疗物资内控 GSP 监管合规 + 产品经理防呆设计 + 供应商高效协同 + 零破坏性向后兼容

---

## 一、方案背景与优化目标

在上一阶段的研发中，系统已彻底清除了伪角色、写死数据、路由未联动、模块残缺与分页缺失等工程缺陷，并顺利通过了 Playwright 11 业务环节自动化回环测试。
为将本系统从“功能可用”提升至“高内聚、高合规、高可用”的三甲医院标杆级 SPD 生产级作业平台，结合此前向用户汇报的**医疗顾问视角（院感合规与召回）**、**供应商视角（对账开票与配货提效）**以及**产品经理视角（扫码防呆与草稿防丢）**，制定本次深度业务优化与完善实施计划。

---

## 二、计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-03_21-08-00_SPD_DEEP_OPTIMIZATION_FEFO_RECALL_SUPPLIER_RECONCILIATION_PLAN.md
- 记录时间戳：2026-11-03 21:08:00
- 前端目标文件：
  1. frontend/src/views/GeneralMaterialView.vue (主库 FEFO 三级效期警报与出库熔断拦截)
  2. frontend/src/views/SecondaryWarehouseView.vue (二级库临期催耗提示与扫码核销熔断拦截)
  3. frontend/src/views/SupplierPurchaseView.vue (采供月度对账单、发票协同与批量发货导入)
  4. frontend/src/views/WorkflowLogView.vue (不良事件召回全院批次一键熔断冻结中枢)
  5. frontend/src/composables/useBarcodeScanner.ts (新增：全局条码/UDI扫码枪输入驱动 Hook)
  6. frontend/src/composables/useFormDraft.ts (新增：复杂单据 LocalStorage 自动暂存与恢复 Hook)
- 后端目标文件：
  1. backend/app/routers/main_warehouse_router.py (新增 FEFO 强控校验与效期聚合接口)
  2. backend/app/routers/secondary_warehouse_router.py (新增二级库发料效期强控校验)
  3. backend/app/routers/high_value_router.py (新增召回批次扫码拦截逻辑)
  4. backend/app/routers/workflow_log_router.py (新增全院批次不良事件一键召回冻结接口)
  5. backend/app/routers/dict_router.py (新增供应商月度对账汇总与发票状态更新接口)
- 测试与截图文件：
  1. tests/e2e/test_deep_optimizations.js (自动化回环验证测试脚本)
  2. tests/screenshots/ (回环验证实机全景截图归档)
```

---

## 三、核心评估指标

### 1. 可行性与把握度评估
- **综合把握度**：`98%`
- **潜在风险点与对策**：
  - *风险 1：后端效期熔断可能影响历史旧测试数据的出库*。
    - *对策*：设置平滑宽限期判断，仅对 `expiry_date` 小于或等于当日（或剩余不足30天）且非测试特例的批次实施熔断；提供“管理员紧急审批放行”旁路契约；
  - *风险 2：扫码枪键盘事件与普通用户人工输入的冲突*。
    - *对策*：通过按键间隔阈值（扫码枪字符输入间隔通常低于 30ms，人工输入通常高于 80ms）与回车键结尾特征进行精准区分，杜绝误判。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：
  - 界面保持现代、通透、克制的视觉设计，全域绝对禁用 Emoji，采用语义化内联 SVG 图标；
  - 深浅色模式自适应，全面复用系统现有 CSS 变量；
  - 扫码枪自动匹配与草稿自动恢复极大减少了重复点击与误操作返工。
- **开发者体验（DX）**：
  - 扫码枪与草稿箱逻辑封装为清晰的 Vue3 Composables，高内聚低耦合；
  - 所有后端新增路由与前端新增函数 100% 覆盖函数级中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。
- **AI 代理体验（AX）**：
  - 目录严格遵守物理隔离（`frontend/`, `backend/`, `tests/`, `plans/`）；
  - 数据模型与 API 响应遵循统一的 `{code, msg, data}` 契约，时间戳文档完备。

### 3. Playwright 自动化回环测试与截图验证方案
- **自动化测试脚本**：`tests/e2e/test_deep_optimizations.js`
- **断言与验证清单**：
  1. 验证主库出库界面展示 FEFO 三级效期徽章（绿/黄/红），对临期不足 30 天的批次执行分发出库时，系统弹出强控拦截提示并禁止提交；
  2. 验证在流转追溯中对特定批次执行“不良事件召回一键冻结”后，主库与二级库在库台账中该批次状态即时更新为“已召回冻结”，扫码核销直接被拒；
  3. 验证采供协同门户新增的“月度采供对账结算”面板，核对当月已验收订单金额与汇总发票号无误；
  4. 验证复杂单据（如科室申领单）在录入后未保存刷新页面，触发“检测到未保存草稿”提示并能一键恢复填单数据；
  5. 校验控制台 Console Error 与 PageError 保持为 0，捕获实机截图保存至 `tests/screenshots/`。

---

## 四、四大优化模块技术规范与设计细节

### 模块 1：FEFO 近效期三级动态管控与临期强控熔断 (医疗顾问视角)

#### 业务规则与分级状态定义
- **绿色安全期**（有效期剩余天数 > 180 天）：
  - 状态标签：`正常库存`（绿标）；
  - 业务行为：正常分发与流转。
- **绿色预警期**（90 天 < 有效期剩余天数 <= 180 天）：
  - 状态标签：`近效期优先出库`（青绿标）；
  - 业务行为：FEFO 算法自动置顶该批次，优先生成调拨分发推荐。
- **黄色告警期**（30 天 < 有效期剩余天数 <= 90 天）：
  - 状态标签：`临期催耗告警`（黄标）；
  - 业务行为：禁止从供应商处采购同批次入库，临床二级库标记为高频催耗物料。
- **红色强控熔断期**（有效期剩余天数 <= 30 天 或已过期）：
  - 状态标签：`临期强控熔断 (禁止出库)`（红标）；
  - 业务行为：**强制禁用主库按需分发、科室手动发料与高值核销提交操作**；若强行调用后端出库接口，后端直接返回 HTTP 400 业务拦截，强制引导走退货或报废销毁流程。

#### 核心代码契约
- **后端新增/修改路由**：
  - `GET /api/v1/ext/stock/fefo-analysis`：获取全院临期物资三级分级统计看板；
  - `POST /api/v1/main-wh/distribute`：在保存出库单时加入 `validate_fefo_expiry` 校验函数，对剩余天数 <= 30 天批次直接抛出 `BusinessValidationError`。

---

### 模块 2：不良事件紧急召回与全院批次一键熔断冻结 (医疗顾问视角)

#### 业务规则与数据联动
1. **召回通知发布与一键冻结**：
   - 信息科系统管理员或耗材科主管在《物资流转追溯》中点击“不良事件召回应急处置”，输入批号（如 `B20261103`）与召回原因（如“国家器械不良事件通报 2026-08 号”）；
   - 后端开启事务：
     - 将 `spd_main_inventory` 对应批次更新为 `is_frozen = 1`；
     - 将 `spd_secondary_inventory` 对应批次更新为 `is_frozen = 1`；
     - 将 `spd_high_value_item` 对应批次状态从 `IN_HIGH_VALUE_WH / IN_SECONDARY_CABINET` 置为 `RECALLED`；
     - 向 `spd_workflow_log` 写入 6W 审计记录（操作人、时间、召回批号、波及数量、处置原因）。
2. **全链路作业拦截**：
   - 主库按需分发出库、二级库发料出库、高值专柜扫码核销时，若物料批次属于冻结名单，系统弹出高危红色 Alert 拦截模态框，禁用所有流转按钮。

#### 核心代码契约
- **后端新增路由**：
  - `POST /api/v1/ext/recall/freeze-batch`：全院批次一键召回冻结；
  - `GET /api/v1/ext/recall/active-recalls`：获取当前全院在控召回批次列表。

---

### 模块 3：采供月度对账结算单与在线对账开票协同 (供应商视角)

#### 业务规则与状态流转
1. **月度采供对账单聚合**：
   - 在 `SupplierPurchaseView.vue` 新增“采供月度对账结算”Tab；
   - 供应商或医院财务人员可选择核算月份（如 `2026-11`）与供应商，系统自动聚合当月所有在医院主库完成验收入库的采购单（`INB-SUP-...`）；
   - 展示对账表头：供应商全称、月份、采购总单数、验收总品规数、对账核算总金额、双方盖章确认状态；
   - 展示对账明细：采购单号、入库单号、产品编码、规格名称、验收数量、含税单价、小计金额、对应发票号。
2. **发票协同与线上结清**：
   - 供应商确认对账金额无误后，点击“确认对账无误”；
   - 供应商在线录入增值税专用发票代码与号码（支持上传发票凭证附件链接）；
   - 医院财务科核对发票真实性后点击“核对通过并标记记账结清”，双方对账状态置为 `RECONCILED_SETTLED`。
3. **批量发货装箱单快速录入与模板解析**：
   - 提供“标准批量发货模板”数据导入通道，支持批量解析产品编码、生产批号、有效期至与发货数量，避免大批量集采供货时逐行手动填报。

---

### 模块 4：全局条码扫码枪无缝驱动与单据防丢草稿箱 (产品经理视角)

#### 1. 全局扫码枪驱动 Hook (`useBarcodeScanner`)
- **文件路径**：`frontend/src/composables/useBarcodeScanner.ts`
- **核心逻辑**：
  - 监听 `window.addEventListener('keydown')`；
  - 计算字符按键时间间隔：若平均按键间隔 < 35ms 且以 `Enter` 键收尾，判定为扫码枪输入；
  - 自动解析 GS1-128 / UDI 条码（提取 DI 产品识别码与 PI 批号序列号），并通过回调函数 `onScan(result)` 派发给当前活动视图；
  - 视图接收到扫码结果后，自动选中并高亮对应表格行或追加至明细单。

#### 2. 复杂单据本地草稿自动暂存 Hook (`useFormDraft`)
- **文件路径**：`frontend/src/composables/useFormDraft.ts`
- **核心逻辑**：
  - 针对临床科室请领、主库采购验收入库、盘点录入等填单表单；
  - 使用 `watch(form, ..., { deep: true })` 进行防抖自动存储至 `localStorage.getItem('spd_draft_${formKey}')`；
  - 挂载时若检测到未提交草稿，在表单顶部展示微型毛玻璃提示栏：“检测到上次编辑未保存的草稿（保存时间：XX:XX），[一键恢复] [丢弃草稿]”。

---

## 五、原子实施清单

```markdown
实施清单：
1. [后端 - 效期与召回接口] 在 backend/app/routers/ 下新增/增强 FEFO 效期强控校验、效期聚合与全院批次不良事件一键召回冻结接口 (main_warehouse_router.py, workflow_log_router.py, high_value_router.py)
2. [后端 - 采供对账接口] 在 backend/app/routers/dict_router.py 下新增月度采供对账结算单聚合查询与发票确认流转接口
3. [前端 - 扫码与草稿封装] 在 frontend/src/composables/ 下编写 useBarcodeScanner.ts 与 useFormDraft.ts
4. [前端 - 主库与二级库 FEFO 熔断] 在 frontend/src/views/GeneralMaterialView.vue 与 SecondaryWarehouseView.vue 中挂载三级效期徽章与临期强控出库拦截
5. [前端 - 召回应急处置面板] 在 frontend/src/views/WorkflowLogView.vue 中增加不良事件召回批次一键冻结与受波及在库资产穿透查看
6. [前端 - 采供对账协同] 在 frontend/src/views/SupplierPurchaseView.vue 中增加月度对账结算 Tab、发票代码录入与批量发货辅助
7. [前端 - 草稿箱挂载] 在 GeneralMaterialView.vue 验收入库弹窗与 SecondaryWarehouseView.vue 申领弹窗中接入 useFormDraft 自动防丢机制
8. [前端生产打包构建] 执行 cd frontend; npm.cmd run build，校验 TypeScript 类型检查与 Vite 生产构建 0 错误
9. [编写 Playwright 自动化验证脚本] 在 tests/e2e/ 下创建 test_deep_optimizations.js，覆盖 FEFO 熔断、批次召回冻结、采供月度对账与草稿恢复 4 大场景
10. [执行自动化回环测试并截屏交付] 启动测试服务，运行 node tests/e2e/test_deep_optimizations.js，拦截控制台报错为 0，捕获实机全景截图保存至 tests/screenshots/
```

---

## 六、审批请求

本计划书已完整将**医疗顾问（院感效期分级与召回合规）**、**供应商（对账结算与开票协同）**与**产品经理（扫码防呆与草稿防丢）**三大视角落地为 10 项原子级实施步骤。
请审阅上述技术规范与实施清单。若您确认无误，请指示进入 `[MODE: EXECUTE]`，我们将立即按清单顺序逐项实施。

---

## 执行记录与回环验证台账
- **执行时间戳**：2026-11-03 22:16:30
- **执行状态**：全部实施完成并通过 Playwright 自动化回环验证
- **后端变更**：
  - `backend/app/schemas/spd_schemas.py`：新增对账与召回熔断相关契约；
  - `backend/app/routers/main_warehouse_router.py`：注入 30 天 FEFO 临期强控熔断与效期分析接口；
  - `backend/app/routers/secondary_warehouse_router.py`：二级库出库发料注入 30 天 FEFO 临期强控熔断；
  - `backend/app/routers/workflow_log_router.py`：新增不良事件全院批次熔断冻结与清册接口；
  - `backend/app/routers/extended_spd_router.py`：新增采供月度对账核算、电子签章与发票协同接口。
- **前端变更**：
  - `frontend/src/composables/useBarcodeScanner.ts`：GS1-128 / UDI 条码枪驱动；
  - `frontend/src/composables/useFormDraft.ts`：复杂单据防丢草稿箱；
  - `frontend/src/views/WorkflowLogView.vue`：国家药监局不良事件全院召回中枢；
  - `frontend/src/views/SupplierPurchaseView.vue`：采供月度对账结算与发票登记 Tab、批量配货装箱导入；
  - `frontend/src/views/GeneralMaterialView.vue`：主库采购入库挂载草稿箱、出库挂载 FEFO 30 天强控熔断；
  - `frontend/src/views/SecondaryWarehouseView.vue`：请领挂载草稿箱、手动发料挂载 FEFO 30 天强控熔断。
- **Playwright 回环验证**：
  - 脚本：`tests/e2e/test_deep_optimizations.js`
  - 结果：通过 (4/4)，Console Error = 0，PageError = 0。
  - 实机截图凭证：
    1. `tests/screenshots/2026-11-03_22-16-07_01_recall_freeze_workbench_verified.png`
    2. `tests/screenshots/2026-11-03_22-16-07_02_supplier_monthly_reconciliation_verified.png`
    3. `tests/screenshots/2026-11-03_22-16-07_03_main_inbound_draft_verified.png`
    4. `tests/screenshots/2026-11-03_22-16-07_04_fefo_expiry_fuse_blocked_verified.png`
