# 采供双端物理彻底解耦与多供应商经营资质准入审查工程实施计划书

- **计划文档路径**：`plans/2026-11-04_11-15-00_SUPPLIER_PHYSICAL_DECOUPLING_AND_MULTI_VENDOR_AUDIT_PLAN.md`
- **记录时间戳**：`2026-11-04 11:15:00`
- **前端目标文件**：
  - `frontend/src/views/HospitalProcurementView.vue`（新建：医院采购管理与准入审核中枢）
  - `frontend/src/views/ExternalSupplierPortalView.vue`（新建：外部供应商专属协同门户）
  - `frontend/src/router/index.ts`（更新：拆分 `/procurement` 与 `/supplier-portal` 路由）
  - `frontend/src/layouts/MainLayout.vue`（更新：导航菜单解耦与角色跳转）
  - `frontend/src/api/supplierPurchaseApi.ts`（更新：增加多供应商资质列表与企业数据隔离接口）
- **后端目标文件**：
  - `backend/app/routers/extended_spd_router.py`（更新：新增资质列表查询、多企业资质审核与供应商企业数据隔离过滤）
  - `backend/app/services/rbac_and_confirm_service.py`（复查：保障 403 资质硬拦截边界）
- **测试与截图文件**：
  - `tests/e2e/test_supplier_physical_decoupling_and_multi_audit.js`（新建）
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_01_hospital_procurement_no_ship_btn.png`
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_02_multi_vendor_qualification_audit.png`
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_03_supplier_portal_ship_success.png`
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_04_main_warehouse_acceptance_closed_loop.png`

---

## 一、核心评估指标

1. **可行性与把握度评估**：
   - **把握度：98%**。
   - 系统中已有完整的 `SpdSupplierProfile` 供应商档案表、`SpdSupplierAndPurchaseOrder` 订单流转表以及 `accept_supplier_delivery_inbound` 验收入库闭环。本次改造主要是对混杂的前端视图进行彻底物理拆解，剥离越权操作，补齐多供应商审查台账，技术路径清晰无阻碍。
2. **存量功能与三方体验影响分析**：
   - **用户体验（UX）**：医院内控端与外部供应商端彻底物理隔离；医院管理员再也不会看到“替供应商发货”的假按钮，供应商端清晰展示本企业资质状态；彻底消除假业务幻觉。
   - **开发者体验（DX）**：遵循单一职责原则（SRP），将 1300 行杂糅单组件拆解为职责明确的两个标准页面，函数 100% 具备标准化中文四要素注释。
   - **AI 代理友好度（AX）**：显式路由契约与明确的入参出参，消除跨轮次推理的业务概念交叠。
   - **存量功能零破坏**：采购计划提报、主科审批、供应商配货发货生成待验单、主库验收入库、四联单打印等底层业务状态机保持向后兼容。
3. **Playwright 自动化回环测试与截图验证方案**：
   - 自测用例 1：以管理员进入 `/procurement`，断言顶栏为医院内控指标，采购订单列表无“配货发货”按钮；
   - 自测用例 2：在【供应商准入资质审查工作台】中选中 `某新注册未审资质医疗器械商贸公司 (SUP_UNVERIFIED_99)`，点击【审核通过】，校验后端返回 200，状态变为 `QUAL_APPROVED`；
   - 自测用例 3：以供应商视角进入 `/supplier-portal`，查看属于该公司的采购订单，点击【配货发货】录入批号效期，提交发货成功（0 个 403 拦截）；
   - 自测用例 4：进入普通主库 `/general?tab=inbound`，顶部待验收看板出现该发货单，点击【查验实物并验收入库】成功增库结案；
   - 捕获 4 张实机全屏截图归档至 `tests/screenshots/`。

---

## 二、技术与 UI 细节规范

### 1. 医院内控端：`HospitalProcurementView.vue`
- **页面定位**：公立医院采购计划管理、供应商准入监管与履约追踪中枢。
- **核心结构**：
  - 顶部 KPI 大盘：全院待批采购计划、待审供应商经营资质、在途待到货订单、本月采购发生总额；
  - **Tab 1: 临床采购计划提报与主科审批**：
    - 临床护士长/采购员提报采购需求（耗材品名、规格、需求数量、紧急程度）；
    - 耗材科/设备科主库审批，并指定合格准入供应商生成正式 PO 订单；
    - **操作列仅包含【查看详情】与【审批计划】，坚决移除【配货发货】按钮**；
  - **Tab 2: 供应商准入资质审查工作台（新增）**：
    - 表格列：供应商编码、企业全称、统一社会信用代码、经营许可证号、药监效期、准入状态、经办审核人、操作；
    - 操作列：针对未审供应商（如 `SUP_UNVERIFIED_99`）提供【审核通过】与【合规驳回】按钮，点击后向后端发送动态 `supplier_code`；
  - **Tab 3: 全院采供履约与验收入库看板**：
    - 展示全院各供应商订单履约状态（待接单/已发货/已入库）；
    - 状态为已发货时，提供【前往主库验收入库】快捷动作，点击直接带单号路由跳转至普通主库。

### 2. 外部供应商端：`ExternalSupplierPortalView.vue`
- **页面定位**：外部医疗器械商业公司专用数字化协同平台。
- **核心结构**：
  - 顶部资质横幅：动态绑定当前供应商企业名、许可证号与国家药监局有效期；
  - **硬拦截守门机制**：
    - 当资质状态为 `QUAL_PENDING` 或 `QUAL_REJECTED` 时，显示大号红色警示卡片：“企业经营资质处于待审/驳回状态，未经医院耗材科/设备科审核批准，严禁查看采购订单与接单发货！”，并提供【上传/更新证照】入口；
    - 下方接单发货功能强制锁定；
  - **企业数据物理隔离**：
    - 资质过审后，仅展示 `supplier_code` 与本企业相匹配的采购订单；
    - 针对本企业的“主科已审批待发货”订单，支持【配货发货】，填报批号效期并提交。

### 3. 后端接口改造契约（`extended_spd_router.py`）
- `GET /api/v1/ext/supplier-purchase/qual-list`：
  - 返回全量供应商资质档案列表（含威高、SUP_UNVERIFIED_99 等），供医院端审查台账加载；
- `POST /api/v1/ext/supplier-purchase/qual-audit`：
  - 入参支持任意 `supplier_code`，原子更新 `SpdSupplierAndPurchaseOrder` 及 `SpdSupplierProfile` 的准入状态为 `QUAL_APPROVED` 或 `QUAL_REJECTED`；
- `GET /api/v1/ext/supplier-purchase/list`：
  - 接收可选参数 `supplier_code`。医院端传入 `ALL` 返回全院订单；供应商端传入自身 `supplier_code` 返回单企隔离订单。

---

## 三、原子实施清单与执行验收台账

```markdown
实施清单执行进度（100% 已落地）：
1. [后端] 改造 backend/app/routers/extended_spd_router.py：[已完成]
   - 新增 GET /api/v1/ext/supplier-purchase/qual-list 接口，聚合返回全量供应商资质申请及准入状态；
   - 优化 POST /api/v1/ext/supplier-purchase/qual-audit 接口，支持动态指定 supplier_code 进行精准审核并补齐 SpdSupplierProfile 必填字段；
   - 优化 GET /api/v1/ext/supplier-purchase/list 接口，增加 supplier_code 参数实现企业级数据隔离过滤。
2. [前端API] 改造 frontend/src/api/supplierPurchaseApi.ts：[已完成]
   - 新增 listSupplierQualifications 接口导出；
   - 优化 listSupplierPurchaseOrders 接口支持传入 supplier_code 过滤。
3. [前端医院端] 创建 frontend/src/views/HospitalProcurementView.vue：[已完成]
   - 搭建公立医院采购内控指标大盘；
   - 建设 Tab 1【采购计划提报与主科审批】，彻底移除配货发货越权按钮；
   - 建设 Tab 2【供应商准入资质审查工作台】，支持对 SUP_UNVERIFIED_99 等供应商逐一查验证照并审核通过/驳回；
   - 建设 Tab 3【采供履约与验收入库】，实现与普通主库/高值专仓的无缝直达。
4. [前端供应商端] 创建 frontend/src/views/ExternalSupplierPortalView.vue：[已完成]
   - 搭建外部供应商企业资质看板与待审硬拦截卡片；
   - 建设订单拣货配货与发货工作台，仅展示本企业订单并支持录入批号效期发货；
   - 建设采供月度对账与开票结算 Tab。
5. [前端路由与菜单] 改造 frontend/src/router/index.ts 与 frontend/src/layouts/MainLayout.vue：[已完成]
   - 路由解耦：/procurement 对应 HospitalProcurementView，/supplier-portal 对应 ExternalSupplierPortalView；
   - 左侧菜单拆分为【7. 采购管理与准入中心】与【8. 外部供应商协同门户】；
   - 导航守卫与切换账号角色自适应定向。
6. [构建校验] 在 frontend/ 目录下执行 npm run build：[已完成]
   - 验证 vue-tsc 类型检查与 Vite 打包 100% 零错误（耗时 10.27s）。
7. [回环测试与截图] 编写并执行 tests/e2e/test_supplier_physical_decoupling_and_multi_audit.js：[已完成]
   - 验证 1：医院管理员在 /procurement 无配货发货按钮（数量为 0）；
   - 验证 2：在资质审查台账对 SUP_UNVERIFIED_99 独立查验证照并审核通过；
   - 验证 3：在 /supplier-portal 切换至该企业成功配货发货，0 个 403 拦截；
   - 验证 4：普通主库到货看板完成实物查验并验收入库闭环；
   - 捕获 4 张实机全屏截图归档至 tests/screenshots/，页面严重错误数: 0。
8. [成果归档与交付] 更新 plans/ 记录并提交 Git：[已完成]
```

---

## 四、Playwright 自动化回环验收实机截图归档

- **验证 1（医院采购内控端彻底移除发货按钮）**：
  `tests/screenshots/2026-11-04_11-25-54_01_hospital_procurement_no_ship_btn.png`
  - 顶栏展示医院采购内控指标（待审批计划、待审供应商、在途待验送货单），表格操作列坚决无“配货发货”按钮。
- **验证 2（多供应商经营资质审查工作台）**：
  `tests/screenshots/2026-11-04_11-25-54_02_multi_vendor_qualification_audit.png`
  - 列表呈现全院 8 家供应商，对 `某新注册未审资质医疗器械商贸公司 (SUP_UNVERIFIED_99)` 独立查验证照并提交审核，状态实时变为 `已准入·允许供货`。
- **验证 3（外部供应商协同门户企业隔离与发货）**：
  `tests/screenshots/2026-11-04_11-25-54_03_supplier_portal_ship_success.png`
  - 独立协同门户，企业数据严格隔离，过审企业在线拣货配货录入生产批号并提交发货，0 个 403 拦截。
- **验证 4（普通主库查验送货实物验收入库闭环）**：
  `tests/screenshots/2026-11-04_11-25-54_04_main_warehouse_acceptance_closed_loop.png`
  - 普通主库入库看板查验实物并验收入库，在库实数原子递增，单据全流程闭环结案。
