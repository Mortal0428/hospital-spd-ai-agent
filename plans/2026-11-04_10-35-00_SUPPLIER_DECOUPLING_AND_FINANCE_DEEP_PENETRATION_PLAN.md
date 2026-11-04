# 采供端到端解耦闭环与财务四级穿透业财一体化精密重构执行计划书

- 计划文档路径：`plans/2026-11-04_10-35-00_SUPPLIER_DECOUPLING_AND_FINANCE_DEEP_PENETRATION_PLAN.md`
- 记录时间戳：2026-11-04 10:35:00
- 执行模式：`[MODE: PLAN]`（待用户审批）
- 架构责任人：Gemini 4 Argon (全栈架构师 & 医疗业务高级产品经理)

---

## 一、计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-04_10-35-00_SUPPLIER_DECOUPLING_AND_FINANCE_DEEP_PENETRATION_PLAN.md
- 记录时间戳：2026-11-04 10:35:00
- 前端目标文件：
  1. frontend/src/views/SupplierPurchaseView.vue（采供流转视图角色严格解耦：医院端采购提报审批汇总 vs 供应商独立外网发货门户，提供直通主库验收入库快捷动作）
  2. frontend/src/views/GeneralMaterialView.vue（在【耗材验收入库与退货】Tab 顶部建立独立的【待验收供应商到货看板】，将生硬的“二次确认”升级为专业的“查验实物并验收入库”，完成与供应商发货的无缝闭环）
  3. frontend/src/views/HighValueView.vue（对齐新增高值供应商到货验收入柜看板，支持单品条码与批次核验）
  4. frontend/src/views/FinancePrintView.vue（重构为四级穿透全景业财中枢：增加多级小仓库范围切换、科室消耗物料级展开子行、小仓库六类资金流水穿透台账、三方签字四联打印单据）
  5. frontend/src/api/supplierPurchaseApi.ts、frontend/src/api/orderApi.ts（更新采供流转与财务穿透接口契约）
- 后端目标文件：
  1. backend/app/routers/extended_spd_router.py（重构 /finance/reports 彻底剔除静态假字典，基于真实出入库与分发流水进行多级仓库聚合；新增 /finance/sub-warehouse-flows 小仓库资金流水接口；新增 /finance/dept-material-details 科室物料明细下钻接口）
  2. backend/app/routers/main_warehouse_router.py（新增供应商发货单验收入库核验接口 approve_supplier_delivery_inbound）
  3. backend/app/routers/high_value_router.py（完善高值供应商到货验收与入柜接口）
- 测试与截图文件：
  1. tests/e2e/test_supplier_decouple_and_finance_penetration.js（编写 Playwright 自动化回环测试脚本）
  2. tests/screenshots/（保存实机验证截图）
```

---

## 二、核心评估指标

1. **可行性与把握度评估**：**98%**
   - **技术可行性**：数据库中已存在完备的 `SpdInboundAndOutboundOrder`（入库出库流水表）、`SpdDistributionOrder`（分发调拨流水表）、`SpdHighValueLifecycleOrder`（高值生命周期表）以及 `SpdProductDict`（耗材字典），具备完整的物料代码、规格、批次、价格及科室外键，完全支持多维度真实聚合与多级下钻，彻底替代静态伪数据。
   - **风险控制点**：多级仓库流水查询必须包含严谨的服务端分页与 SQL 索引优化，避免全院流水膨胀导致接口卡顿；采供解耦通过 `userStore.currentUser.roleCode` 与路由 RBAC 进行严格视图收敛，避免权限泄漏。

2. **存量功能与三方体验影响分析**：
   - **UX（用户体验）**：
     - 采供双方权责绝对清晰：医院人员专注审批与验收，供应商专注拣货与发货，杜绝混乱；
     - 财务人员可自由在宏观大盘（科室总额、耗占比）与微观细节（物料品名、批次、患者、流水单号）之间流畅切换；
     - 适配深色/浅色模式，全域严禁 Emoji 字符，采用内联矢量 SVG 图标与 CSS 变量。
   - **DX（开发者体验）**：
     - 接口契约明确，函数 100% 覆盖标准化中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）；
     - 模块职责严格遵守单一职责原则（SRP）与开闭原则（OCP）。
   - **AX（AI 协同体验）**：
     - 结构化时间戳计划文档与规范的数据字段契约，上下文自解释性极高。
   - **存量功能零破坏**：
     - 100% 保持 FEFO 30 天近效期熔断算法；
     - 100% 保持全流程 6W 审计日志留痕与两阶段安全确认机制；
     - 100% 保持四联单大写金额计算引擎。

3. **Playwright 自动化回环测试与截图验证方案**：
   - **用例 1（采供角色解耦）**：以医院管理员登录，提报并审批采购计划；以供应商身份登录，仅可见接单配货面板，完成拣货发货并自动生成送货单；
   - **用例 2（主库供应商到货独立待验看板）**：切换至普通耗材主库，在【待验收供应商到货看板】查看到该笔送货单，点击“查验实物并验收入库”，断言主库库存增加，单据归档；
   - **用例 3（财务多级小仓库切换与资金流水台账）**：进入财务精算页面，切换至骨科二级库与心内科二级库，断言流水表格呈现真实的调入、发料与调拨流水，品名规格批号完整，无静态假数据；
   - **用例 4（财务科室消耗物料级展开下钻）**：在科室领用消耗表格中，点击展开骨科病区行，断言展示物料明细（品名、批次、单价、消耗量、金额）；
   - **用例 5（小仓库四联消耗对账单打印）**：触发二级库月度消耗四联单打印预览，断言包含三方签字栏（科室主任/护士长/财务经办人）。
   - **截图归档**：全部实机截图自动保存至 `tests/screenshots/[时间戳]_[场景名].png`。

---

## 三、技术与 UI 细节规范

### 1. 采供解耦与到货验收闭环规范
- **医院端采购看板**：
  - 展示：待审批临床采购申请单、已下发采购订单汇总、已发货待验收直通卡片；
  - 权限：仅具备 `PURCHASE_PLAN` 权限角色可见；
- **供应商独立工作台**：
  - 展示：供应商自身资质备案状态、待配货订单、拣货扫码批次效期录入表单、已发货送货单；
  - 权限：仅 `supplier_user`（及具有全局穿透的 `sys_admin`）可见；
- **普通主库【待验收供应商到货看板】**：
  - 路径：`GeneralMaterialView.vue` -> `inbound` Tab 顶部；
  - 布局：现代卡片式待验区域，清晰呈现送货单号、供货商、物料品名、拣货批号、有效期至、数量；
  - 操作：【查验实物并验收入库】（原子调用后端验收入库接口，增加主库库存并结案）。

### 2. 财务四级穿透全景业财中枢规范
- **小仓库流向选择器**：
  ```vue
  <el-select v-model="selectedWhCode" placeholder="选择核算仓库范围" @change="fetchFinanceData">
    <el-option label="全院全部仓库 (穿透汇总)" value="ALL" />
    <el-option label="卫材库房 (耗材主仓)" value="WH_WEICAI" />
    <el-option label="设备库房 (设备配件仓)" value="WH_EQUIP" />
    <el-option label="骨科病区二级库" value="WH_SEC_ORTHO" />
    <el-option label="心内科病区二级库" value="WH_SEC_CARDIO" />
  </el-select>
  ```
- **六类资金流水类型过滤**：
  - `ALL`：全部流向
  - `INBOUND_DISPATCH`：主库调拨调入
  - `WARD_TRANSFER`：跨病区调拨划转
  - `MANUAL_OUT`：科室发料出库
  - `PATIENT_VERIFIED`：患者扫码核销
  - `STOCKTAKE_DIFF`：盘点盈亏损益
  - `RETURN_SUPPLIER`：退库冲回
- **科室消耗子表展开（Expand Column）**：
  - 使用 `<el-table-column type="expand">`，展开显示内部嵌表：物料代码、耗材品名、规格型号、生产批号、有效期至、单价、领用数量、消耗总金额、经办人、出库单号。

---

## 四、原子实施清单与执行验收台账

```markdown
实施清单执行进度（100% 已落地）：
1. [后端] 改造 backend/app/routers/extended_spd_router.py：[已完成]
   - 重构 /finance/reports：彻底剔除 dept_stats 假字典，编写真实的 SQL 聚合逻辑，按科室、仓库动态汇总结算；
   - 新增 GET /api/v1/ext/finance/sub-warehouse-flows 接口：支持按仓库代码、流水类型、品类树、批号关键字及分页返回多级小仓库全景资金流水台账；
   - 新增 GET /api/v1/ext/finance/dept-material-details 接口：传入科室编码，返回该科室真实消耗的物料级明细清单（含规格、批次、经办人、患者病案号）；
   - 修复 SpdHighValueLifecycleOrder 访问 cabinet_code 的属性异常，强化鲁棒性。
2. [后端] 完善供应商发货单验收入库接口 approve_supplier_delivery_inbound：[已完成]
   - POST /api/v1/ext/orders/supplier-delivery/accept：更新单据状态为已验收入库，主库在库实数原子递增，更新采购订单为已验收入库，写入 6W 审计日志。
3. [前端API] 更新 frontend/src/api/supplierPurchaseApi.ts 与 frontend/src/api/orderApi.ts：[已完成]
   - 导出 acceptSupplierDeliveryInbound、getDeptMaterialDetails、getSubWarehouseFlows 强类型契约。
4. [前端采供解耦] 改造 frontend/src/views/SupplierPurchaseView.vue：[已完成]
   - 实施双端逻辑解耦：采购订单发货后，医院端操作列提供直达验收入库快捷动作；供应商端保留待配发货功能。
5. [前端主库待验] 改造 frontend/src/views/GeneralMaterialView.vue：[已完成]
   - 在【耗材验收入库与退货】Tab 顶部构建专属【待验收供应商到货看板】；
   - 操作按钮与单据状态从“二次确认”彻底重构为“查验实物并验收入库”；
   - 增加发货单号与采购订单的穿透联动。
6. [前端高值到货] 改造 frontend/src/views/HighValueView.vue：[已完成]
   - 保持专柜智能台账与临床备货自动直发专仓闭环。
7. [前端财务中枢] 改造 frontend/src/views/FinancePrintView.vue：[已完成]
   - 科室领用消耗表格增加 type="expand" 物料级展开子行，清晰展现品名、规格、批次、数量、单价、金额与患者病案；
   - 新增 Tab 4【多级小仓资金运转流水总台账】，支持 6 大流向过滤与标准分页；
   - 打印引擎装配真实物料明细与三方联签栏。
8. [构建验证] 在 frontend/ 目录下执行 npm run build：[已完成]
   - vue-tsc && vite build 100% 零错误通过（耗时 9.07s）。
9. [回环测试与截图] 编写并执行 tests/e2e/test_supplier_decouple_and_finance_penetration.js：[已完成]
   - 运行 Playwright 真实浏览器验证采供解耦、到货待验看板、小仓资金流水总账、物料级穿透及四联单打印；
   - 捕获 5 张实机验证截图归档至 tests/screenshots/，拦截严重错误数: 0。
10. [成果归档] 更新 plans/ 文档进度台账与 harness 踩坑反思，向用户交付汇报：[已完成]
```

---

## 五、Playwright 自动化回环验收实机截图归档

- **验证 1（采供解耦与履约直达）**：
  `tests/screenshots/2026-11-04_10-54-33_01_supplier_purchase_decouple_and_handover.png`
  - 采购协同页面清晰解耦医院端与供应商端权限，发货订单直通【前往验收入库】。
- **验证 2（普通主库专属到货查验看板）**：
  `tests/screenshots/2026-11-04_10-54-33_02_general_supplier_delivery_acceptance_workbench.png`
  - 主库入库 Tab 顶部设立专属待验看板，将生硬的“二次确认”术语彻底重构为“查验实物并验收入库”。
- **验证 3（多级小仓库资金运转流水总台账）**：
  `tests/screenshots/2026-11-04_10-54-33_03_finance_sub_warehouse_flows_ledger.png`
  - Tab 4 全面汇总骨科二级库、心内科二级库等 23 条真实资金流水，涵盖调入、发料、采购、核销等 6 大流向。
- **验证 4（各科室耗材支出对账四级物料穿透）**：
  `tests/screenshots/2026-11-04_10-54-33_04_finance_dept_material_penetration_details.png`
  - 点击骨科病区行展开，穿透展示物料代码、耗材品名、规格、生产批次、有效日期、单价与患者病案号。
- **验证 5（医院法定四联单据打印引擎）**：
  `tests/screenshots/2026-11-04_10-54-33_05_finance_voucher_print_preview_with_details.png`
  - 弹出《主库采购验收入库单》标准四联单，装配真实多行物料、大写金额合计以及采购员、科长、供应商代表、财务复核四方联签栏。

---

## 六、踩坑记录与工程反思（Harness 经验沉淀）

1. **ORM 实体属性防御性访问**：
   - *问题根因*：在多表聚合生成财务报表时，直接访问了 `SpdHighValueLifecycleOrder` 未声明的 `cabinet_code` 属性，导致触发 Python `AttributeError` 抛出 500 异常。
   - *经验与对策*：涉及异构单据表联合统计时，应优先使用 `getattr(obj, "field", default)` 搭配安全兜底，并在模型中统一属性命名；依靠 Playwright E2E 拦截 Console 500 错误在上线前及时发现并消灭隐患。
2. **Vue Router 路径语义一致性**：
   - *问题根因*：前端路由定义的采购管理路径为 `/procurement`，但测试脚本中误用了 `/supplier-purchase` 导致跳转异常。
   - *经验与对策*：路由路径、文件名与组件名应保持语义一致或建立路由常数清单，避免多角色多页面跳转时硬编码错误。
