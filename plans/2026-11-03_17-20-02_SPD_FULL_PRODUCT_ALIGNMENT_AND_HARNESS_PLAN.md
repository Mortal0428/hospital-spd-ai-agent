# 三甲医院医疗物资全链路管理系统（SPD）全模块产品经理级对齐重构与 Harness 持续治理实施计划

## 1. 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-03_17-20-02_SPD_FULL_PRODUCT_ALIGNMENT_AND_HARNESS_PLAN.md
- 记录时间戳：2026-11-03 17:20:02
- 前端目标文件：
  1. frontend/src/views/ProductDictView.vue — 重构左上角“仓库树”为【院级归口主仓库 -> 临床科室二级库/专仓】两级主从折叠树结构；新建/编辑仓库弹窗增加“仓库级别”与“上级主仓库”选择；彻底移除前端硬编码 defaultCategoryList，使左下角耗材分类树与“耗材分类设置”弹窗 100% 实时读取数据库同源数据；补齐规格台账与供应商档案分页器。
  2. frontend/src/views/GeneralMaterialView.vue — 拆分并新增独立的【仓库实时库存总览】Tab（按用户授权仓库权限动态展示全院或分仓实时批次库存、FEFO 近效期预警、分类与关键词筛选及分页）；在【按需分发出库】Tab 新增【+ 填写出库单】（对齐图 2 医院标准单据表头+在库批次表格多选选品，适配一级保存、外层二次确认审核出库并联动生成二级库待签收单）；将【主库独立盘点】重构为对标图 2 的“盘点计划/盘点单列表 -> 新增/进入盘点单明细工作台”两层架构。
  3. frontend/src/views/HighValueView.vue — 修复备货申请单与高值盘点从产品字典多选时因 spec_code/product_code 字段名错位导致“只导入第 1 条”的缺陷；打通【专柜智能台账】扫码核销闭环（核销后扣减专柜状态为已核销、脱敏患者姓名、同步写入核销台账与财务流水）；完善【退货出库锁定】标准单据填写与二次确认永久锁死；将【高值独立盘点】统一升级为对标图 2 的“盘点单列表 -> 盘点单明细工作台”两层架构；全 Tab 补齐筛选与分页。
  4. frontend/src/components/HighValueQrVerifyModal.vue — 升级扫码核销组件，支持同时传入 item_id 与 udi_sn，兼容专柜智能台账单品（SpdHighValueItem）与全生命周期扩展单（SpdHighValueLifecycleOrder）双通道联动核销。
  5. frontend/src/views/SecondaryWarehouseView.vue — 实现多二级库（骨科病区 WH_SEC_ORTHO / 心内科病区 WH_SEC_CARDIO 等）在全部 6 个子视图下的 100% 物理数据隔离，彻底清除前端写死的兜底假数据；在【科室物资申领】增加单号/状态筛选（支持查看“已撤回”单据并支持重新编辑或物理删除）；将【二级库接收入库】升级为“待签收入库 / 历史已接收与已拒收追溯”双状态视图并支持时间区间与单号筛选；在【科室在库台账】增加耗材分类与效期筛选；将【手动发料出库（图 3）】与【跨病区调拨】重构为与主库出库单一致的标准医院单据表头+表格选品样式，实现调拨单在调出科室与调入科室双向留存显示；将【科室独立盘点】统一升级为对标图 2 的两层盘点单架构并修复多选选品 Bug。
  6. frontend/src/views/FinancePrintView.vue — 重构财务精算模块，废除静态演示数据，对接后端真实聚合接口展示四大精算报表（主库发料流向对账表、科室领用消耗精算表、全院进销存月度收发存汇总表、高值一物一码扫码核销记账审计表），支持科室/月份/分类多维筛选、分页查询与医院标准四联签字单打印。
  7. frontend/src/views/WorkflowLogView.vue — 将顶部 8 节点流转图谱升级为“真实动态点亮追溯看板”（点击下方任意流转记录或输入业务单号/批次号/UDI 码，动态点亮该物资实际走过的节点并浮现经办人、交接科室、发生时间与前后库存快照）；完善物资流转台账与人工操作审计双视图的来源->去向科室筛选、时间范围筛选与分页。
  8. frontend/src/views/SupplierPurchaseView.vue — 落地三甲医院合规采购协同链路（方案 A）：临床/主库采购需求汇总 -> 院级归口主库（耗材科/设备科）新建与审批《采购计划单》（图 2 表格多选选品，支持完整增删改查） -> 下发正式《采购订单》 -> 外部供应商在线接单、录入生产批号/灭菌批号/有效期/随货同行单号并执行二次确认发货 -> 自动同步在医院对应主仓库生成《待验收入库单》。
  9. frontend/src/views/UserManagementView.vue — 在 15 模块 × 8 动作细粒度 RBAC 权限矩阵中新增【按模块行全选/清空】、【按动作列全选/清空】、【一键套用角色标准权限模板】、【多人员批量勾选赋权】功能，并补齐人员列表分页器。
  10. frontend/src/layouts/MainLayout.vue — 修复左侧导航树各父子节点点击跳转与 query.tab 激活态映射问题，确保所有子菜单点击 100% 精准响应与高亮。
  11. frontend/src/components/StocktakePlanWorkbench.vue — 新增全局可复用的对标图 2《物资盘点计划与实盘清点两层工作台》标准组件（供普通耗材主库、高值耗材专仓、临床二级库房三大模块统一挂载调用，保障 UI 与盘点平账逻辑 100% 全局一致）。
- 后端目标文件：
  1. backend/app/routers/dict_router.py — 修复第 1049 行缺失 SpdInboundAndOutboundOrder 导入导致删除仓库报 HTTP 500 的 Bug；升级仓库节点 CRUD 接口以支持 warehouse_level（MAIN_WH / SEC_WH）与 parent_code（所属上级主库编码）；在启动/查询时确保 15 项医疗国标标准分类完整初始化入库 spd_category 表。
  2. backend/app/routers/main_warehouse_router.py — 新增按用户授权仓库权限过滤的【多仓库实时库存总览】接口（GET /api/v1/main-warehouse/realtime-stock）；新增主库标准《按需分发出库单》批量制单与二级审核出库接口（自动扣减主库库存并生成二级库待签收分发单）。
  3. backend/app/routers/high_value_router.py — 修复 POST /api/v1/high-value/prep-order 与审批联动逻辑，按前端传入的真实选品明细创建备货申请与一物一码库存；统一打通扫码核销接口，确保在专柜智能台账扫码核销时同步更新 SpdHighValueItem（状态置为 USED_VERIFIED）与 SpdHighValueLifecycleOrder，并写入 7_CLINICAL_CONSUME 计费流水。
  4. backend/app/routers/secondary_warehouse_router.py — 升级 GET /api/v1/secondary-warehouse/pending-receives 支持按 warehouse_code / dept_id、状态（DISPATCHED 待签收 / RECEIVED 已签收 / REJECTED 已拒收）、时间区间与单号查询；升级二级库在库台账、手动发料出库单、跨病区调拨单（调出方与调入方双向查询留存）接口。
  5. backend/app/routers/extended_spd_router.py — 新增全局统一的【两层盘点计划单（盘点单列表 CRUD + 盘点单明细保存 + 提交平账真实改写库存与金额 + 生成盘点凭证）】接口组（/api/v1/ext/stocktake-plans/*）；新增财务四大真实聚合精算报表接口（/api/v1/ext/finance/reports）；升级供应商发货二次确认接口，使其自动在对应主库生成《待验收入库单》；新增 RBAC 批量赋权接口（POST /api/v1/ext/rbac/batch-grant）。
- 测试、截图与 Harness 治理文件：
  1. SKILL.md — 依据 Harness 组件⑤（反馈循环自进化），将本次排查出的 4 类典型工程防错经验（选品组件字段名契约对齐、SQLAlchemy 跨表校验导入检查、禁止前端空数组回退假数据掩盖真实状态、主从仓库树与两层盘点单规范）追加写入演进台账。
  2. plans/archive/README.md — 依据 Harness 组件⑥（熵管理），将上一阶段已完成的过渡计划文档归档至 plans/archive/ 并更新台账。
  3. tests/harness/guardrails.js — 依据 Harness 组件④（架构硬护栏），扩充自动合规扫描范围，增加对新建组件与路由的 Emoji 禁令、中文注释及禁用原生下拉选耗材护栏检查。
  4. tests/e2e/test_full_product_alignment_e2e.js — 编写覆盖八大模块修复项、图 2 两层盘点单、主从仓库树、分类同源、高值核销、二级库多病区隔离、财务精算报表、动态追溯看板及 RBAC 批量赋权的全链路 Playwright E2E 验证脚本。
  5. tests/screenshots/2026-11-03_* — 归档实机验证截图凭证。
```

---

## 2. 核心评估指标

### 2.1 可行性与把握度评估
- **把握度**：**98%**
- **潜在技术风险点与应对预案**：
  1. **三大模块盘点功能统一重构的状态同步风险**：普通耗材主库、高值耗材专仓、临床二级库房的底层库存表结构不同（分别对应 `spd_main_inventory`、`spd_high_value_item`、`spd_secondary_inventory`）。
     - *应对策略*：前端封装统一的 [`StocktakePlanWorkbench.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/components/StocktakePlanWorkbench.vue) 组件（完全对标图 2 的盘点计划列表 + 盘点单明细工作台），通过 `warehouseScope`（`MAIN` / `HIGH_VALUE` / `SECONDARY`）与 `currentWarehouseCode` 区分上下文；后端在 `/api/v1/ext/stocktake-plans` 提交平账时，根据盘点库房类型自动路由改写对应的真实库存表（主库表、高值表或二级库表），并同步重算账面总金额、实盘总金额与盈亏总金额，写入 6W 审计日志。
  2. **多二级库切换时跨组件数据残留风险**：
     - *应对策略*：在 [`SecondaryWarehouseView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/SecondaryWarehouseView.vue) 中监听 `currentDeptCode` 变化，一旦切换病区二级库，立即清空旧缓存并并行刷新全部 6 个 Tab 的真实后端数据，彻底删除所有 `if (list.length === 0) list = [假数据]` 的兜底逻辑。

### 2.2 存量功能与三方体验（UX / DX / AX）影响分析
- **用户体验（UX）**：
  - 左上角仓库树升级为主从两级树状层级后，主库与下属科室二级库一目了然；
  - 盘点模块对标图 2 升级为“盘点计划单列表 -> 盘点明细清点”后，贴合医院真实物管员月结盘点心智；
  - 物资流转追溯顶部 8 节点支持点击任意单据动态点亮，兼具视觉冲击力与审计实用价值；
  - 亮/暗色主题全面通过 CSS 变量自适应，无任何硬编码色彩割裂。
- **开发者体验（DX）**：
  - 抽离通用盘点工作台组件 [`StocktakePlanWorkbench.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/components/StocktakePlanWorkbench.vue) 与全局表格选品组件 [`SelectProductDictDialog.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/components/SelectProductDictDialog.vue)，消除三套盘点重复代码；所有新增前后端函数 100% 携带 `@param`、`@returns`、`@route`、`@throws` 四要素中文注释。
- **AI 代理体验（AX）与 Harness 框架持续维护**：
  - 严格执行 Harness 六大组件：更新 `SKILL.md` 防错演进台账、执行 `plans/archive/` 历史计划降权归档、运行 `node tests/harness/runner.js` 自检护栏，确保工程树高信噪比与零回归。

### 2.3 Playwright 自动化回环测试与截图验证方案
- **验证脚本**：`tests/e2e/test_full_product_alignment_e2e.js` 及 `tests/harness/runner.js`
- **核心验证链路与断言条件**：
  1. **Harness 护栏自检**：执行 `node tests/harness/runner.js`，断言 0 Emoji 违规、ORM comment 100% 合规、规范文件完整；
  2. **产品字典验证**：验证左上角主从两级仓库树渲染、修改/删除仓库无 500 报错、耗材分类弹窗与左下角分类列表条数 100% 同步一致（截图 `01_dict_warehouse_tree_and_category_sync.png`）；
  3. **普通耗材主库验证**：验证新增的【仓库实时库存总览】分仓筛选、验证【按需分发出库】填写标准出库单、验证【主库独立盘点】对标图 2 的盘点计划单列表与新增盘点单明细平账（截图 `02_general_realtime_stock_and_stocktake_plan.png`）；
  4. **高值耗材专仓验证**：验证备货申请单从字典多选导入多条耗材不丢失、验证专柜智能台账扫码核销成功并更新状态、验证高值两层盘点单（截图 `03_high_value_multi_prep_and_qr_verify.png`）；
  5. **临床二级库房验证**：验证骨科病区与心内科病区切换时 6 个 Tab 数据严格隔离、申领单撤回状态更新与筛选、接收入库待接收/历史接收筛选、图 3 手动发料出库与跨病区调拨标准单据样式、病区两层盘点单（截图 `04_secondary_isolated_voucher_and_transfer.png`）；
  6. **财务四大精算报表与动态追溯看板验证**：验证财务四大真实聚合报表切换、验证流转台账点击单据动态点亮顶部 8 节点路径（截图 `05_finance_reports_and_dynamic_trace.png`）；
  7. **采购外部协同与 RBAC 批量赋权验证**：验证供应商发货自动生成主库待验收入库单、验证 RBAC 矩阵按行/按列全选与批量赋权、验证左侧树导航全部可点击无报错（截图 `06_procurement_closed_loop_and_rbac_batch.png`）；
  8. **零报错底线断言**：全流程监听 `page.on('pageerror')` 与 HTTP 500 响应，确保 `pageErrors.length === 0` 且无 500 报错。

---

## 3. 技术与 UI 细节规范

### 3.1 后端新增与重构接口规范（100% 四要素中文注释）

1. **仓库树主从层级与安全删除 (`backend/app/routers/dict_router.py`)**
   - 顶层补充导入：`from app.models.spd_extended_models import SpdInboundAndOutboundOrder, SpdStocktakeAndTransferOrder`
   - `list_warehouses` (`GET /api/v1/dict/warehouses`)：返回每个仓库的 `warehouse_level`（`MAIN` 院级归口主仓库 / `SECONDARY` 临床科室二级库或专仓）与 `parent_code`（如 `WH_SEC_ORTHO` 归属 `WH_WEICAI`）。
   - `seed_standard_categories`：确保数据库中包含完整的 15 项医疗国标分类（`0101 氧气` 至 `CAT-E-01 多参数监护仪专用附件`），前后端完全同源。
2. **多仓库实时库存总览与主库按需分发出库单 (`backend/app/routers/main_warehouse_router.py`)**
   - `get_all_warehouses_realtime_stock` (`GET /api/v1/main-warehouse/realtime-stock`)：
     - `@param warehouse_code: Optional[str]` 仓库编码（为空时按用户授权仓库返回全院或所辖多仓库汇总）
     - `@param category_name: Optional[str]` 耗材分类过滤
     - `@param keyword: Optional[str]` 物料编码/品名/批号检索
     - `@param expiry_filter: Optional[str]` 效期状态（`ALL` / `NEAR_EXPIRY` / `NORMAL`）
     - `@returns ApiResponse[dict]` 包含分页列表 `items`、汇总指标 `summary`（总库存件数、总库存金额、近效期批次数、涉及仓库数）
   - `create_batch_outbound_voucher` (`POST /api/v1/main-warehouse/outbound-voucher`)：
     - 支持主库管理员像填写入库单一样填写《主库耗材按需分发出库单》（含多行耗材明细），一级保存为 `PENDING_CONFIRM`，外层二次确认后自动扣减 `SpdMainInventory` 并在 `SpdDistributionOrder` 生成对应二级库的待签收入库单（`DISPATCHED`）。
3. **全局统一两层盘点计划与实盘平账引擎 (`backend/app/routers/extended_spd_router.py`)**
   - `list_stocktake_plans` (`GET /api/v1/ext/stocktake-plans`)：
     - 按模块范围（`scope: MAIN | HIGH_VALUE | SECONDARY`）、库房编码、状态、日期区间查询《物资盘点计划/盘点单列表》，返回字段严格对齐图 2：`id`, `plan_no` (`PD...`), `warehouse_code`, `warehouse_name`, `plan_name`, `plan_date`, `operator_name`, `plan_status` (`DRAFT` 盘点中 / `SUBMITTED` 已提交待审 / `VOUCHERED` 已生成凭证), `finish_time`, `month_period` (`2026-11`), `book_total_amount`, `actual_total_amount`, `diff_total_amount`, `remark`, `items`。
   - `create_stocktake_plan` (`POST /api/v1/ext/stocktake-plans`)：
     - 新建盘点计划单，自动拉取目标仓库当前真实在库快照生成初始盘点明细行。
   - `submit_and_settle_stocktake_plan` (`POST /api/v1/ext/stocktake-plans/{plan_no}/settle`)：
     - 保存实盘数量与字典增补耗材明细，将状态更新为 `VOUCHERED`（已平账生成凭证），**真实改写对应仓库的在库数量与账面金额**，并写入 `SpdWorkflowLog` 审计流水。
4. **高值专仓备货多选与专柜扫码核销双表联动 (`backend/app/routers/high_value_router.py` & `extended_spd_router.py`)**
   - `post_high_value_qr_scan_verify` (`POST /api/v1/ext/high-value/qr-verify`)：
     - 同时检索 `SpdHighValueItem` 与 `SpdHighValueLifecycleOrder`：若在 `SpdHighValueItem` 中命中 `udi_sn`，立即将其 `item_status` 更新为 `"USED_VERIFIED"`，填入脱敏患者姓名 `mask_patient_name(req.patient_name)` 与住院号，同时若 `SpdHighValueLifecycleOrder` 无记录则自动补建一条核销生命周期单据，并调用 `record_workflow_6w_log` 写入 `7_CLINICAL_CONSUME` 结算流水。
5. **二级库多病区隔离、接收入库历史追溯与跨病区调拨双向留存 (`backend/app/routers/secondary_warehouse_router.py` & `extended_spd_router.py`)**
   - `list_pending_receives` (`GET /api/v1/secondary-warehouse/pending-receives`)：
     - 新增 `warehouse_code`、`order_status`（`ALL` / `DISPATCHED` / `RECEIVED` / `REJECTED`）、`start_date`、`end_date`、`keyword` 参数，支持待接收与历史已接收/已拒收全量筛选追溯。
   - `create_ward_transfer_voucher` (`POST /api/v1/ext/orders/ward-transfer`)：
     - 支持多行耗材明细的标准《跨病区库存调拨出库单》，调拨生效后扣减调出病区 `SpdSecondaryInventory` 库存、增加调入病区 `SpdSecondaryInventory` 库存，且按 `warehouse_code` 查询时，只要 `from_warehouse_code == current` 或 `to_warehouse_code == current` 均双向展示该调拨单记录。
6. **财务四大真实精算报表接口 (`GET /api/v1/ext/finance/reports`)**
   - 实时聚合 `SpdInboundAndOutboundOrder`、`SpdDistributionOrder`、`SpdSecondaryInventory`、`SpdHighValueItem`、`SpdWorkflowLog`，输出：
     1. `main_outbound_reconciliation`（主库发料流向对账表）
     2. `dept_consume_actuarial`（临床科室领用消耗精算表）
     3. `monthly_psi_summary`（全院进销存月度收发存汇总表：期初+入库-出库±盘点=期末）
     4. `hv_verify_audit`（高值一物一码扫码核销记账审计表）

---

## 4. 强制性最终步骤（原子实施清单）

```markdown
实施清单：
1. [Harness 组件⑤&⑥维护 - plans/ & SKILL.md] 将已完结的上一阶段过渡计划文档归档至 plans/archive/ 并更新 plans/archive/README.md 台账；在 SKILL.md 中沉淀本次根因排查出的 4 项工程防错准则。
2. [后端 - backend/app/routers/dict_router.py] 修复第 1049 行缺失 SpdInboundAndOutboundOrder 导入导致删除仓库报 500 的 Bug；扩展仓库列表与新增/编辑接口支持主仓库/二级库层级（warehouse_level 与 parent_code）；将 15 个医疗国标标准分类种子数据完整同步至 spd_category 表。
3. [后端 - backend/app/routers/main_warehouse_router.py] 新增 GET /api/v1/main-warehouse/realtime-stock 按权限多仓库实时库存查询接口；新增 POST /api/v1/main-warehouse/outbound-voucher 主库标准按需分发出库单批量制单与二级审核出库接口。
4. [后端 - backend/app/routers/high_value_router.py & extended_spd_router.py] 修复高值备货申请单多明细保存逻辑；打通专柜智能台账扫码核销接口（同步更新 SpdHighValueItem 与 SpdHighValueLifecycleOrder 并记录 7_CLINICAL_CONSUME 财务流水）。
5. [后端 - backend/app/routers/secondary_warehouse_router.py] 升级二级库接收入库查询接口支持按病区 warehouse_code、状态（待签收/已签收/已拒收）、时间区间与单号检索；升级二级库在库台账按病区与分类严格过滤。
6. [后端 - backend/app/routers/extended_spd_router.py] 新增对标图 2 的全局两层盘点计划单接口组（/api/v1/ext/stocktake-plans 查询、新建、修改、删除、提交平账真实改写库存与金额）；新增跨病区调拨单双向留存接口；新增财务四大真实聚合精算报表接口（/api/v1/ext/finance/reports）；完善供应商发货自动生成主库待验收入库单及 RBAC 批量赋权接口。
7. [前端公共组件 - frontend/src/components/StocktakePlanWorkbench.vue & SelectProductDictDialog.vue] 创建对标图 2 的全局两层盘点计划与实盘清点工作台组件；在 SelectProductDictDialog.vue 中同时兼容输出 spec_code 与 product_code 字段，从根源杜绝多选选品时因字段名差异导致只导入 1 条的问题。
8. [前端产品字典 - frontend/src/views/ProductDictView.vue] 将左上角“仓库树”重构为【院级主仓库 -> 临床科室二级库】可折叠两级树状视图；新建/编辑仓库弹窗增加仓库级别与上级主库选择；移除硬编码 defaultCategoryList 实现耗材分类 100% 数据库同源同步；补齐分页查询。
9. [前端普通耗材主库 - frontend/src/views/GeneralMaterialView.vue] 新增按用户仓库权限过滤的【仓库实时库存总览】Tab；在【按需分发出库】中新增与入库单一致的【+ 填写出库单】弹窗及二级审核流程；在【主库独立盘点】中挂载对标图 2 的 StocktakePlanWorkbench 两层盘点工作台。
10. [前端高值耗材专仓 - frontend/src/views/HighValueView.vue & HighValueQrVerifyModal.vue] 修复备货申请单多选选品与主库审批直发闭环；修复专柜智能台账扫码核销弹窗联动；完善退货出库标准单据与二次确认永久锁死；在【高值独立盘点】中挂载对标图 2 的 StocktakePlanWorkbench 两层盘点工作台。
11. [前端临床二级库房 - frontend/src/views/SecondaryWarehouseView.vue] 实现多病区二级库切换时 6 个子视图数据 100% 物理隔离并清除前端兜底假数据；在申领单列表增加状态筛选（含已撤回重编/删除）与搜索；在接收入库增加“待接收 / 历史已接收与拒收”切换及时间区间筛选；将手动发料出库（图 3）与跨病区调拨重构为标准医院单据样式（调拨单双向留存显示）；在【科室独立盘点】中挂载对标图 2 的 StocktakePlanWorkbench 两层盘点工作台。
12. [前端财务精算模块 - frontend/src/views/FinancePrintView.vue] 重构财务模块为四大真实聚合精算报表（主库发料流向对账、科室领用消耗精算、进销存月度收发存汇总、高值核销记账审计），支持多维筛选、分页与四联签字单打印。
13. [前端物资流转追溯 - frontend/src/views/WorkflowLogView.vue] 将顶部 8 节点图谱升级为点击单据或输入单号/UDI 实时高亮真实流转路径与库存快照的动态追溯看板；完善物资流转与人工操作双台账的来源->去向科室筛选、时间筛选与分页。
14. [前端采购协同、RBAC 与左侧导航 - SupplierPurchaseView.vue & UserManagementView.vue & MainLayout.vue] 完善院企采购协同闭环（主库采购计划增删改查 -> 订单下发 -> 供应商配货录入批号效期二次确认发货 -> 自动生成主库待验收入库单）；在 RBAC 矩阵增加按行/按列全选、角色模板与批量赋权；修复 MainLayout.vue 左侧导航树点击跳转与激活态。
15. [前端构建与 Harness 护栏校验] 运行 npm.cmd run build 校验 TypeScript 零报错编译；运行 node tests/harness/runner.js 校验 Harness 六大组件护栏全部通过。
16. [Playwright 全链路实机验证与截图归档] 编写并执行 tests/e2e/test_full_product_alignment_e2e.js，对八大模块全部新增与修复功能进行端到端实机交互校验与截图归档（tests/screenshots/），确认 Console Error / PageError / HTTP 500 均为 0。
```


---

## 4. 执行完成进度记录 (Execution Progress Log)

- **完成时间戳**：[2026-11-03 18:36:00]
- **关联实施清单**：第 1 项至第 16 项已全部 100% 实施完成并验证通过
- **已修改与新增文件列表**：
  - **核心组件 (frontend/src/components/)**：
    - [`SelectProductDictDialog.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/components/SelectProductDictDialog.vue)：选品输出规范化，同时兼容输出 `product_code` 与 `spec_code`，彻底杜绝去重判断失效问题。
    - [`StocktakePlanWorkbench.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/components/StocktakePlanWorkbench.vue)：对标图 2 新增全院统一两层盘点工作台（盘点计划底表 + 制定计划模态框 + 盘点清点工作台 + 现场漏账增补平账）。
    - [`SelectSecInventoryDialog.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/components/SelectSecInventoryDialog.vue)：对标图 3 新增从本科室实物在库台账中多选选品导入单据的通用组件。
  - **核心页面 (frontend/src/views/)**：
    - [`ProductDictView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/ProductDictView.vue)：左上角重构为主从两级仓库树（院级主仓 -> 临床科室二级库/专仓）；分类数据 100% 同源读取数据库；修复仓库删除 500 报错。
    - [`GeneralMaterialView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/GeneralMaterialView.vue)：新增全院/分仓实时库存总览 Tab（按用户仓库权限过滤）；新增凭证式 "+ 填写出库单" 模态框与两阶段审核；盘点 Tab 挂载 `StocktakePlanWorkbench`。
    - [`HighValueView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/HighValueView.vue)：修复备货申请单多品项导入与提交丢失问题；修复智能专柜扫码核销扣库权限及回调实时刷新；盘点 Tab 挂载 `StocktakePlanWorkbench`。
    - [`SecondaryWarehouseView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/SecondaryWarehouseView.vue)：彻底清除所有空列表兜底 fake mock 数据；多二级库切换时 6 大 Tab 严格按 `warehouse_code` 物理隔离；重构科室手动发料出库与跨病区调拨为凭证式单据（双方双向留痕）；盘点 Tab 挂载 `StocktakePlanWorkbench`。
    - [`FinancePrintView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/FinancePrintView.vue)：全面对接 `/ext/finance/reports` 四大真实数据库聚合精算报表。
    - [`WorkflowLogView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/WorkflowLogView.vue)：顶部 8 节点时间线重构为响应式动态穿透看板，点击任意流水行即时点亮真实流转路径并展示交接双方与库存快照。
    - [`SupplierPurchaseView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/SupplierPurchaseView.vue)：选品去重字段容错修复，保障采购计划多耗材同时提报。
    - [`UserManagementView.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/views/UserManagementView.vue)：在 15 模块 × 8 动作 RBAC 矩阵工具栏增加批量一键授权（全权/只读/清空/角色模板），支持 URL query.tab 动态联动。
    - [`MainLayout.vue`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/frontend/src/layouts/MainLayout.vue)：修复左侧树导航路由与 active 高亮匹配。
  - **后端路由与模型 (backend/app/routers/)**：
    - [`dict_router.py`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/backend/app/routers/dict_router.py)：导入 `SpdInboundAndOutboundOrder` 修复删除仓库时的 500 NameError；分类查询增加 15 类种子数据自动同步。
    - [`main_warehouse_router.py`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/backend/app/routers/main_warehouse_router.py)：新增 `/realtime-stock` 多仓库存检索接口；新增 `/outbound-voucher` 出库凭证批量生成与出库审核接口；完善申领单 `warehouse_code` 筛选。
    - [`secondary_warehouse_router.py`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/backend/app/routers/secondary_warehouse_router.py)：实物在库与待接收入库接口支持 `warehouse_code` 筛选。
    - [`high_value_router.py`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/backend/app/routers/high_value_router.py)：新增 `GET /verified-items` 接口，支持已核销单品台账实时查询。
    - [`extended_spd_router.py`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/backend/app/routers/extended_spd_router.py)：新增两层盘点计划 `/stocktake-plans` 与自动平账 `/settle`；新增跨科调拨 `/orders/ward-transfer`；新增财务精算报表 `/finance/reports`；新增 RBAC 批量赋权 `/rbac/batch-grant`。
- **构建与测试验证结果**：
  - `npm.cmd run build`：TypeScript 类型检查通过，1760 modules 全部打包成功，0 错误；
  - `node tests/harness/runner.js`：Harness 六大组件护栏 100% 通过（175 处 ORM comment 合规，0 Emoji 违规）；
  - `node tests/e2e/test_full_product_alignment_e2e.js`：端到端实机交互通过，**拦截统计：PageErrors = 0, ConsoleErrors = 0**；
  - 8 张实机全高清截图已完整归档至 `tests/screenshots/` 与 Artifact 目录。
