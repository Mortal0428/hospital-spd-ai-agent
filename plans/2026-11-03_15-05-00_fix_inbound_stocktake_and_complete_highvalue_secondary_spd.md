# 医院医疗物资全链路 SPD 系统：入库与盘点缺陷修复、全院单据与选品统一规范（图2/图3）、高值耗材备货审批流与三级权限盘点实施计划

- **计划文档路径**：`plans/2026-11-03_15-05-00_fix_inbound_stocktake_and_complete_highvalue_secondary_spd.md`
- **最新修订时间戳**：2026-11-03 15:20:00
- **当前所处模式**：`[MODE: PLAN]`
- **实施把握度**：99%
- **业务对齐与核心要求**：
  1. **彻底解决入库单保存 500、耗材分类不同步、主库盘点底表 500 报错**。
  2. **高值耗材备货申请与审批下发闭环**：
     - 具备标准图 2 形式的《高值耗材备货申请审批单》，由临床科室填报，归口路由至上级主库（耗材科主库或设备科主库）审批；
     - 上级审批通过后，**直接下发到高值耗材专仓库存**，免去普通耗材二次审批；
     - **普通耗材主库自动生成调拨出库记录与单据**，写入 6W 流转日志（记录经办人、审批人、批次、库存状态），保证数据流转精密无错。
  3. **高值耗材一物一码 UDI 患者核销扣库**：
     - 必须核销对应的高值二维码/条码（包含 UDI 唯一序列号 ID）；
     - 扫码输入患者脱敏信息（姓名、住院号）、主刀医生、手术名称；
     - 核销后单品置为 `USED_VERIFIED`，扣减专柜在库单品，并触发财务科成本记账（`is_billable=1`）。
  4. **全系统杜绝下拉框选耗材，100% 统一为图 2 单据表单与图 3 表格选品规范**：
     - 全系统任何模块严禁出现图 1 式简陋表单或 `<select>` 下拉框选耗材；
     - 统一为**图 2 标准四联单据结构**（单据抬头、多字段网格头部、明细表格、+从产品字典选品按钮、合计栏、操作按钮）；
     - 统一为**图 3 表格多选弹窗**（`SelectProductDictDialog`，支持搜索框、Checkbox 多选、六大列信息展示、导入选中耗材计数按钮）。
     - 覆盖主库入库、主库盘点增补、高值备货申请、高值退货出库、高值独立盘点、二级库申领、二级库接收入库、二级库手动出库、二级库调拨、二级库盘点。
  5. **盘点业务与仓库管辖层级三级权限区分**：
     - **信息科系统管理员（sys_admin）**：穿透模式，管辖信息科仓库以及全院下方所有仓库（耗材主库、设备主库、总务主库、高值专仓、全部临床二级库）。
     - **主库科室（dept_manager，耗材科/设备科）**：管理本科室主库及管辖下方的子病区二级库（如耗材科管辖骨科、心内科二级库的耗材台账与盘点）。
     - **临床二级库（secondary_user）**：仅可查看并盘点自己当前病区/病室的在库库存。

---

## 一、变更计划与目标文件清单

### 1. 后端目标文件 (backend/)
- `backend/app/routers/main_warehouse_router.py`
  - **变更理由**：
    1. 修复 `POST /api/v1/main-warehouse/purchase-inbound` 中 `SpdMainInventory` 实例化字段匹配问题（移除不存在的 `sterilization_batch`、`supplier_name`，补全 `initial_qty`、`production_date`、`inbound_order_no`、`shelf_location` 等），彻底解决图 1 的 500 报错。
    2. 修复 `GET /api/v1/main-warehouse/stocktake-inventory` 中访问不存在属性 `inv.supplier_name` 导致的 `AttributeError` 500 报错（图 3）。
    3. 支持基于用户角色和当前仓库上下文的层级过滤：`sys_admin` 穿透全院所有仓库；`dept_manager` 过滤耗材科/设备科主库及下属二级库。
- `backend/app/routers/high_value_router.py`
  - **变更理由**：
    1. 完善高值耗材备货申请单创建 `POST /api/v1/high-value/prep-order`（图 2 单据规范）。
    2. 完善高值备货审批通过接口 `POST /api/v1/high-value/prep-approve/{order_id}`：
       - 根据归口科室（`CONSUMABLE_DEPT` 或 `EQUIP_DEPT`）路由审批；
       - 审批通过后，自动在普通耗材主库生成一条状态为 `DISPATCHED` 的调拨出库记录（`SpdDistributionOrder`），出库记录真实存在；
       - 直接下发生成高值耗材专仓库存单品（`SpdHighValueItem`），分配 UDI 唯一码与货位；
       - 写入全流程 6W 物流流转日志（节点 `3_MAIN_DISPATCH` 与 `4_HIGH_VALUE_CODE`）。
    3. 完善一物一码扫码核销接口 `POST /api/v1/high-value/qr-verify`：
       - 校验 UDI 条码与二维码 payload；
       - 扣减高值专柜在库单品，状态变更为 `USED_VERIFIED`；
       - 绑定患者脱敏住院号与姓名，触发财务记账（`is_billable=1`）。
    4. 完善高值退货出库单接口 `POST /api/v1/high-value/return-order` 与两阶段锁定接口 `POST /api/v1/high-value/return-lock/{order_id}`（图 2 单据规范，二次确认后置 `is_irreversible_locked=1` 永久不可逆）。
    5. 完善高值独立盘点接口 `GET /api/v1/high-value/stocktake-inventory` 与 `POST /api/v1/high-value/stocktake-submit`。
- `backend/app/routers/secondary_warehouse_router.py`
  - **变更理由**：
    1. 完善二级库接收入库接口 `GET /api/v1/secondary-warehouse/pending-receives` 与 `POST /api/v1/secondary-warehouse/receive/{dist_id}`。
    2. 完善二级库手动发料出库接口 `POST /api/v1/secondary-warehouse/manual-outbound`（图 2 规范出库单，出库后立即消减二级库库存，正式计入本科室耗材成本）。
    3. 完善跨病区调拨接口 `POST /api/v1/secondary-warehouse/transfer`。
    4. 完善二级库盘点底表接口 `GET /api/v1/secondary-warehouse/stocktake-inventory`（按登录人所属二级科室严格隔离）。

### 2. 前端目标文件 (frontend/)
- `frontend/src/components/SelectProductDictDialog.vue` (全局公共组件)
  - **变更理由**：实现高质感图 3 表格选品弹窗（搜索框、表格多选 Checkbox、物料代码/品名/规格/单位/基准单价/生产厂家列、导入选中按钮、高频防抖与防文本选中）。
- `frontend/src/components/SelectHighValueItemDialog.vue` (高值单品专选弹窗)
  - **变更理由**：为高值退货出库单等业务提供高值在库单品表格多选弹窗（UDI 序列号、品名、规格型号、批号、效期、在库专柜货位），彻底替换图 1 的简陋单行输入。
- `frontend/src/views/ProductDictView.vue`
  - **变更理由**：重构 `categoryList` 为基于 `categories.value` 的响应式计算属性，分类维护弹窗新增 `0189 哈哈哈哈` 后左侧树秒级同步（解决图 2 缺陷）。
- `frontend/src/layouts/MainLayout.vue`
  - **变更理由**：完善高值专仓 5 大菜单与二级库 5 大菜单的路由与 `tab` 查询参数映射。
- `frontend/src/views/GeneralMaterialView.vue`
  - **变更理由**：主库盘点增补漏账耗材全面替换为 `SelectProductDictDialog` 表格选品，移除图 4 的 `<select>` 下拉框。
- `frontend/src/views/HighValueView.vue`
  - **变更理由**：
    1. 双向监听 `route.query.tab`，响应 5 大独立子视图：`inbound`（备货申请与审批）、`stock`（专柜智能台账）、`coding`（一物一码赋码）、`return`（退货出库锁定）、`stocktake`（高值独立盘点）。
    2. 备货申请单全面升级为图 2 规范标准单据，明细使用 `SelectProductDictDialog` 选品导入，支持归口路由至耗材科或设备科审批；
    3. 退货出库单全面升级为图 2 规范标准单据，明细使用 `SelectHighValueItemDialog` 导入，消除图 1 简陋输入；
    4. 一物一码赋码面板支持条码解析与标签打印；
    5. 扫码核销面板强化 UDI 扫描与脱敏患者信息录入；
    6. 高值独立盘点底表加载、图 3 表格选品增补、平账提交。
- `frontend/src/views/SecondaryWarehouseView.vue`
  - **变更理由**：
    1. 双向监听 `route.query.tab`，完善 6 大独立业务面板：`requisition`（申领）、`receive`（接收入库）、`stock`（在库台账）、`manual-out`（手动发料出库）、`transfer`（跨病区调拨）、`stocktake`（科室独立盘点）。
    2. 申领单、手动出库单、调拨单全部采用图 2 标准单据架构；
    3. 选品全部采用图 3 `SelectProductDictDialog` 表格选品弹窗；
    4. 手动出库单严格扣减本科室在库库存，并在台账中体现累计消耗与科室计费。

### 3. 测试与截图文件 (tests/)
- `tests/e2e/test_all_warehouse_complete_flows.js`
  - **变更理由**：端到端自动化测试脚本，全面覆盖入库单保存、分类同步、主库盘点、高值备货审批与普通主库出库记录联动、高值退货单据锁定、二级库手动出库消减库存、三级权限盘点视图等，无报错并截图归档。
- `tests/screenshots/[时间戳]_*.png`
  - 归档实机运行截图。

---

## 二、核心评估指标

1. **可行性与把握度评估**：
   - **把握度：99%**
   - **技术风险点与保障措施**：
     - 高值备货审批联动时，需在事务中同时写入 `SpdDistributionOrder`（普通耗材主库出库单）、`SpdHighValueItem`（高值库存单品）与 `SpdWorkflowLog`（全流程流转日志），使用统一数据库事务 `db.commit()` 确保强一致性，任何一步异常立即回滚。
     - 二级库手动发料出库时，需按批次校验可用库存，出库数量不可超过在库数量，出库后立即原子扣减 `current_qty` 并累加 `consumed_qty`。
     - 弹窗与单据样式严格遵守图 2 与图 3 规范，深浅主题自适应，无 Emoji。

2. **存量功能与三方体验影响分析**：
   - **用户体验 (UX)**：全系统彻底杜绝简陋输入框与 `<select>` 下拉框选耗材，全院操作界面全部统一为三甲医院正规单据（图 2）与带搜索多选表格（图 3），操作手感极为专业、流畅、统一。
   - **开发者体验 (DX)**：公共组件解耦抽离，后端接口 100% 具备中文四要素注释（`@param`、`@returns`、`@route`、`@throws`），数据流向清晰。
   - **AI 代理体验 (AX)**：目录拓扑严格物理隔离，单据编号、UDI 码、批次与流转节点完全契约化。
   - **存量功能保护**：完全兼容已有的 RBAC 权限矩阵（15 模块 × 8 动作）、数据大屏看板、3D 展厅与报表导出。

3. **Playwright 自动化回环测试与截图验证方案**：
   - 用例 1：采购入库保存验证，断言 HTTP 200，入库成功且主库库存增加。
   - 用例 2：分类新增动态同步验证，维护弹窗添加分类后，断言左侧树即刻渲染。
   - 用例 3：主库独立盘点底表加载与表格选品增补验证，断言图 3 弹窗弹出并导入成功。
   - 用例 4：高值备货申请单填制（图 2 形式）、提交审批、耗材科/设备科审批通过验证，断言高值专仓库存生成、普通耗材主库出库单生成、流转日志记录生成。
   - 用例 5：高值退货出库单二次确认锁定验证，断言 `is_irreversible_locked=1`。
   - 用例 6：二级库手动发料出库单填制验证，断言在库库存即刻减少、科室成本正确记账。
   - 用例 7：三级盘点权限隔离验证（信息科全院穿透 vs 耗材科管辖二级库 vs 临床二级库单病区）。
   - 截图保存至 `tests/screenshots/`。

---

## 三、技术与 UI 细节规范

### 1. 备货申请单审批通过与主库出库联动技术逻辑
```python
@router.post("/prep-approve/{order_id}", response_model=ApiResponse[dict])
def approve_high_value_prep_order(
    order_id: int,
    db: Session = Depends(get_db),
    user_ctx: CurrentUserContext = Depends(require_roles(["sys_admin", "dept_manager"]))
):
    """高值耗材备货申请上级主库审批下发
    1. 校验单据存在且状态为 PENDING_APPROVAL
    2. 根据备货申请中的物资与归口，自动在普通耗材主库创建一条按需分发出库记录 (SpdDistributionOrder):
       - target_type = "TO_HIGH_VALUE_WH"
       - order_status = "DISPATCHED" (主库已出库)
       - dispatcher_name = user_ctx.real_name (审批人即发料经办人)
    3. 直接在 spd_high_value_item 建立高值耗材单品库存:
       - 生成唯一 UDI-PI 序列号: SN{YYYYMMDD}{random}
       - 生成完整 GS1-128 UDI 编码
       - 分配专仓货位与批号效期
       - item_status = "IN_HIGH_VALUE_WH"
    4. 记录全院物资流转追溯台账 (SpdWorkflowLog):
       - 节点一: 3_MAIN_DISPATCH (主库调拨出库)
       - 节点二: 4_HIGH_VALUE_CODE (高值仓赋码入库)
    5. 提交事务并返回单据状态
    """
```

### 2. 全系统图 2 单据表单与图 3 表格选品统一架构
- **单据表单组件结构 (图 2 规范)**：
  - 容器：大尺寸弹窗 `width="1000px"` 或独立工作台表单。
  - 头部：单据大标题居中加粗，单据编号、关联单号、制单日期、业务类别、出入仓库、经办人、联系电话、备注。
  - 选品栏：右上角配置 `+ 从产品字典选品`（点击唤起 `SelectProductDictDialog` 表格选品弹窗）、`新增空行`、`删除选中行`。
  - 明细表格：序号、物料代码（等宽字体高亮）、品名、规格、型号、单位、生产厂家、数量（数字输入框）、单价、金额（自动计算）、批号、有效期。
  - 合计栏：固定总数量与总金额计算展示。
  - 底部操作栏：取消、保存单据（支持二次确认与打印勾选项）。
- **表格选品弹窗 (图 3 规范)**：
  - `SelectProductDictDialog.vue`：全院产品字典表，带有物料编码/品名/拼音码过滤搜索，表格第一列为 Checkbox，支持全选/多选，底部显示“导入选中耗材 (N)”。

---

## 四、原子实施清单

```markdown
实施清单：
1. [后端 backend/app/routers/main_warehouse_router.py]
   - 修复 create_purchase_inbound 函数中的 SpdMainInventory 字段匹配（解决采购入库 500）。
   - 修复 get_main_stocktake_inventory 函数中的 supplier_name 属性报错（解决主库盘点 500）。
   - 完善主库盘点底表三级权限过滤（信息科全院穿透 vs 耗材科管辖主库及下属二级库）。

2. [后端 backend/app/routers/high_value_router.py]
   - 编写高值备货申请单创建接口（支持路由至耗材科或设备科）。
   - 编写高值备货申请审批下发接口（联动生成普通耗材主库调拨出库单、高值单品库存与 6W 流转日志）。
   - 编写高值一物一码扫码核销接口（验证 UDI 二维条码、扣减单品库存、记录脱敏患者信息、触发财务记账）。
   - 编写高值退货出库单接口与两阶段不可逆锁定接口（置 is_irreversible_locked=1）。
   - 编写高值独立盘点底表与平账接口。

3. [后端 backend/app/routers/secondary_warehouse_router.py]
   - 完善二级库接收入库接口（主库分发单确认接收入库、增加二级库库存、记日志）。
   - 完善二级库手动发料出库接口（核减二级库库存、计入科室耗材成本、生成出库单与日志）。
   - 完善跨病区调拨接口与二级库独立盘点底表接口（严格限制为当前科室）。

4. [前端组件 frontend/src/components/]
   - 编写 SelectProductDictDialog.vue：全局统一的图 3 表格多选弹窗组件。
   - 编写 SelectHighValueItemDialog.vue：高值在库单品 UDI 表格多选弹窗组件。

5. [前端分类修复 frontend/src/views/ProductDictView.vue]
   - 重构 categoryList 为计算属性 computed(() => categories.value.map(...))，解决图 2 耗材分类不同步缺陷。

6. [前端主库改造 frontend/src/views/GeneralMaterialView.vue]
   - 移除盘点漏账增补中的 <select> 下拉框（图 4），全面替换为 SelectProductDictDialog 表格选品弹窗。

7. [前端高值专仓全流程重构 frontend/src/views/HighValueView.vue & MainLayout.vue]
   - 修正 MainLayout.vue 中高值专仓 5 大菜单的 tab 映射。
   - 在 HighValueView.vue 中监听 route.query.tab，开发 5 大独立业务子视图：
     - inbound（备货申请与审批）：采用图 2 规范单据，明细调用 SelectProductDictDialog，支持归口路由审批与主库出库单联动展示。
     - stock（专柜智能台账）：RFID 智能柜实时在库与状态展示。
     - coding（一物一码赋码）：国家标准 UDI 结构解析与条码标签打印。
     - return（退货出库锁定）：采用图 2 规范单据，明细调用 SelectHighValueItemDialog，两阶段确认强制不可逆锁死（消除图 1 简陋输入）。
     - stocktake（高值独立盘点）：底表加载、SelectProductDictDialog 选品增补、盈亏核算、平账提交。
     - 扫码核销面板：输入单品 UDI / 扫描二维码，录入脱敏患者住院号与姓名，核销扣减库存。

8. [前端二级库房全流程重构 frontend/src/views/SecondaryWarehouseView.vue & MainLayout.vue]
   - 修正 MainLayout.vue 中二级库 5 大菜单映射（修复原有的 transfer 错配）。
   - 在 SecondaryWarehouseView.vue 中监听 route.query.tab，完善 6 大业务视图：
     - requisition（科室申领）：采用图 2 规范单据，明细调用 SelectProductDictDialog。
     - receive（接收入库）：展示主库分发待接收单据，一键验收入库。
     - stock（在库台账）：实时在库批次、消耗量、低水位与近效期预警。
     - manual-out（手动发料出库）：采用图 2 规范出库单，选择在库耗材出库，核减在库库存并计入科室成本。
     - transfer（跨病区调拨）：采用图 2 规范调拨单。
     - stocktake（科室独立盘点）：按当前病区加载底表、SelectProductDictDialog 表格选品增补、平账提交。

9. [构建验证 frontend/]
   - 运行 npm run build 校验 0 错误构建。

10. [自动化回环验证与实机截图 tests/]
    - 编写并运行 tests/e2e/test_all_warehouse_complete_flows.js。
    - 验证入库单保存（图 1 修复）、分类动态同步（图 2 修复）、主库盘点（图 3 修复）、备货申请单审批与主库出库联动、退货出库单据锁定（图 1 升级）、二级库手动出库扣库、三级盘点权限。
    - 捕获关键节点实机截图归档至 tests/screenshots/。
```
