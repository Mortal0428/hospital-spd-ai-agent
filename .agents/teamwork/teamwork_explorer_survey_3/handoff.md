# 前端数据流、API 契约、状态管理与高韧性展厅数据策略调研报告 (handoff.md)

- 报告作者: teamwork_explorer_survey_3 (Dataflow & API Contract Explorer)
- 关联任务: ORIGINAL_REQUEST.md
- 报告时间: 2026-11-02T13:00:00Z
- 调查对象: 前端 API 模块、Pinia 状态中枢、后端 8 大路由、认证流转机制与 3D 展厅数据对接

---

## 1. 观察记录 (Observation)

### 1.1 API 架构与 Axios 客户端实现 (`frontend/src/api/request.ts`)
- **文件位置**: `frontend/src/api/request.ts` (共 81 行)
- **BaseURL 与网络配置**:
  - 第 16-22 行：
    ```typescript
    const service: AxiosInstance = axios.create({
      baseURL: '/api/v1',
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    ```
  - `frontend/vite.config.ts` 第 16-21 行配置了开发服务器反向代理：
    ```typescript
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
    ```
- **请求拦截器观察**:
  - 第 25-35 行：
    ```typescript
    service.interceptors.request.use(
      (config) => {
        // 注入当前用户账号或角色标记（便于后端审计与细粒度权限校验）
        const activeUser = localStorage.getItem('spd_active_username') || 'admin';
        config.headers['X-Operator-User'] = encodeURIComponent(activeUser);
        return config;
      },
      (error) => Promise.reject(error)
    );
    ```
  - **严重缺陷 1（键名不一致导致恒为 admin）**：`userStore.ts` 中持久化存储用户信息使用的键是 `spd_active_user`（序列化 JSON 对象），而 `request.ts` 读取的键却是 `spd_active_username`。整个前端源码中从未向 `localStorage` 写入过 `spd_active_username`，导致 `activeUser` 恒为 null，永远回退为字符串 `'admin'`。
  - **严重缺陷 2（缺失 Authorization Bearer Token 头部注入）**：前端生成或存储的 `spd_token` 从未被拦截器注入到 HTTP 头部中；没有发送标准的 `Authorization: Bearer <token>`。
  - **严重缺陷 3（与后端演示请求头脱节）**：后端 `backend/app/core/security.py` 第 171-195 行声明的演示快速鉴权请求头为 `X-Mock-User` 与 `X-Mock-Role`，而前端注入的是 `X-Operator-User`。后端在未收到 `X-Mock-User` 且未收到 Bearer Token 时，直接在第 210 行强制默认兜底为 `admin`（赵振华，信息科）。因此，**前端此前无论在 UI 上切换何种角色，发出的所有 HTTP 请求在后端均以系统管理员权限被执行**。
- **响应拦截器与方法封装观察**:
  - 第 38-52 行：响应拦截器校验 `res.code && res.code !== 200`，若失败通过 `ElMessage.error` 弹窗并调用 `Promise.reject`。
  - 第 62-78 行：仅封装了 `httpGet<T>` 与 `httpPost<T>`，**未封装 `httpPut`、`httpDelete`、`httpPatch` 工具函数**。导致视图中需要执行 PUT 或 DELETE 时（例如更新产品、删除日志、审批申领单），不得不绕道或无法直接利用解包器。

---

### 1.2 前端 API 模块与后端路由映射盘点

前端当前在 `frontend/src/api/` 下存在 7 个文件，而后端在 `backend/app/routers/` 存在 8 个路由文件。盘点对照表如下：

| 模块类别 | 前端 API 文件 | 前端暴露函数与路由 | 后端对应路由文件 | 后端挂载路径 (FastAPI) | 联调状态与差异 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **认证与人员** | **缺失独立 api 文件**<br>(分散在 userStore) | 无独立 api 导出，直接写在 store | `auth_router.py` | `POST /api/v1/auth/login`<br>`GET /api/v1/users/me`<br>`GET /api/v1/departments`<br>`GET /api/v1/users`<br>`POST /api/v1/users` | **脱节**：前端登录未调用 `POST /auth/login`，而是纯客户端伪造 token |
| **产品字典** | `dictApi.ts` | `getDictOverview`<br>`copyProductToWarehouse`<br>`adjustProductPrice` | `extended_spd_router.py`<br>`dict_router.py` | `GET /api/v1/ext/dict/overview`<br>`POST /api/v1/ext/dict/copy-warehouse`<br>`POST /api/v1/ext/dict/adjust-price`<br>`GET/POST /api/v1/products`<br>`GET/POST /api/v1/categories` | **部分连通**：`overview`、`copy`、`adjust` 连通扩展路由，但基础 CRUD（增删查改分类与单品）未封装 |
| **普通耗材主库** | `orderApi.ts` | `listInboundOutboundOrders`<br>`createInboundOutboundOrder`<br>`executeOrderTwoStepAction`<br>`approveRequisitionAutoOutbound` | `extended_spd_router.py`<br>`main_warehouse_router.py` | `GET/POST /api/v1/ext/orders/inbound-outbound`<br>`POST /api/v1/ext/orders/two-step-action`<br>`POST /api/v1/ext/orders/requisition-auto-outbound/{id}`<br>`GET /api/v1/main-warehouse/inventory`<br>`POST /api/v1/main-warehouse/inbound`<br>`GET/POST /api/v1/main-warehouse/distributions` | **部分连通**：扩展单据连通，但主库核心在库台账 (`/main-warehouse/inventory`) 与按需分发订单 (`/distributions`) 前端未对接 |
| **高值耗材专仓** | `highValueApi.ts` | `listHighValueLifecycleOrders`<br>`createHighValueLifecycleOrder`<br>`executeHighValueTwoStepAction`<br>`verifyHighValueQrScan`<br>`listVerifiedHighValueItems` | `extended_spd_router.py`<br>`high_value_router.py` | `GET/POST /api/v1/ext/high-value/lifecycle`<br>`POST /api/v1/ext/high-value/two-step-action`<br>`POST /api/v1/ext/high-value/qr-verify`<br>`GET /api/v1/ext/high-value/verified-list`<br>`GET /api/v1/high-value/items`<br>`PUT /api/v1/high-value/items/{id}/verify` | **部分连通**：扩展生命周期单据连通，但单品在库台账主接口 (`/high-value/items`) 前端未对接 |
| **二级库管理** | `stocktakeTransferApi.ts` | `listStocktakeTransferOrders`<br>`createStocktakeOrTransferOrder` | `extended_spd_router.py`<br>`secondary_warehouse_router.py` | `GET/POST /api/v1/ext/orders/stocktake-transfer`<br>`GET /api/v1/secondary-warehouse/inventory`<br>`POST /api/v1/secondary-warehouse/receive/{id}`<br>`POST /api/v1/secondary-warehouse/consume`<br>`GET/POST /api/v1/secondary-warehouse/requisitions` | **严重断层**：二级库盘点与调拨连通扩展路由，但二级库主库存台账、分发签收入库、临床消耗出库及申领单查询全被前端页面写死为 mock |
| **6W 流转日志** | **缺失独立 api 文件**<br>(View 内生写 httpGet) | 仅在 `WorkflowLogView.vue` 第 79 行生写 `httpGet('/workflow-logs')` | `workflow_log_router.py` | `GET /api/v1/workflow-logs`<br>`POST /api/v1/workflow-logs`<br>`PUT /api/v1/workflow-logs/{id}`<br>`DELETE /api/v1/workflow-logs/{id}` | **连通但未模块化**：后端实测能返回 18 条真实 6W 日志，但前端未定义接口函数与 DTO 类型 |
| **统计与单据打印** | **缺失独立 api 文件**<br>(View 内全部 hardcode) | 前端无任何 api 封装，`FinancePrintView.vue` 内指标、科室排行与单据全部硬编码 | `stats_print_router.py` | `GET /api/v1/stats/overview`<br>`GET /api/v1/stats/dept-consumption`<br>`GET /api/v1/print/voucher/{voucher_type}/{order_no}` | **完全空置**：后端已具备完整精算与四联打印数据生成能力，前端却因未对接而使用假数据展示 |
| **细粒度 RBAC** | `rbacApi.ts` | `getRbacMatrix`<br>`toggleUserPermission` | `extended_spd_router.py` | `GET /api/v1/ext/rbac/matrix`<br>`POST /api/v1/ext/rbac/toggle` | **完全连通**：15 模块 x 8 动作开关与查询正常交互 |
| **供应商与采购** | `supplierPurchaseApi.ts` | `listSupplierPurchaseOrders`<br>`auditSupplierQualification`<br>`flowSupplierPurchaseAction` | `extended_spd_router.py` | `GET /api/v1/ext/supplier-purchase/list`<br>`POST /api/v1/ext/supplier-purchase/qual-audit`<br>`POST /api/v1/ext/supplier-purchase/flow` | **完全连通**：资质准入审核与采购流转正常交互 |

---

### 1.3 状态管理现状 (`frontend/src/stores/userStore.ts`)
- **文件位置**: `frontend/src/stores/userStore.ts` (共 254 行)
- **单 Store 臃肿现状**: 当前 `frontend/src/stores/` 目录下**仅有唯一一个 `userStore.ts`**，它同时承担了以下 5 项完全异构的职责：
  1. 用户认证状态与 Token 持久化 (`isLoggedIn`, `token`, `currentUser`)；
  2. 4 大核心预设演示人员定义 (`PRESET_USERS`)；
  3. 细粒度 RBAC 15 模块 x 8 动作权限列表、权限 Map 计算与 `canAction` 鉴权方法；
  4. 角色权限横幅文案描述 (`roleDescription`)；
  5. 全局亮暗主题状态 (`theme: 'light' | 'dark'`) 与 DOM 属性切换 (`toggleTheme`)。
- **业务领域 Store 严重缺失**:
  - 无 `showcaseStore`（用于管理 3D 双模态展厅模式 Orbital/Tilted、壁纸工坊媒体索引、选屏播放状态、10 大医疗卡片动态指标）；
  - 无 `inventoryStore`（用于缓存主库库存、各二级库库存水位及 FEFO 近效期预警）；
  - 无 `voucherPrintStore`（用于缓存四联法定打印单据结构化数据）；
  - 无 `themeStore`（主题被侵入式耦合在用户 Store 中）。

---

### 1.4 身份认证流转与 4 大演示角色不一致性审计

#### 1.4.1 前端预设人员 vs. 后端数据库实际种子数据
检查 `frontend/src/stores/userStore.ts` 第 19-60 行定义的 `PRESET_USERS` 与后端 `backend/app/services/seed_service.py` 及真实 MySQL `sys_user` 数据，发现显著冲突：

| 角色中文名称 | 用户需求与 Demo 预期 (ORIGINAL_REQUEST.md) | 前端 `userStore.ts` 当前预设 | 后端 MySQL 真实账号 (`sys_user`) | 差异性质与影响 |
| :--- | :--- | :--- | :--- | :--- |
| **耗材科管理员** | 耗材科主管 (王建国，主库管辖) | `username: 'mat_mgr'`<br>`deptCode: 'CONSUMABLE_DEPT'` | `username: 'mgr_consumable'`<br>`deptCode: 'CONSUMABLE_DEPT'` | **账号名不匹配**：前端向真实后端登录将抛 400（用户名不正确） |
| **设备科管理员** | 设备科主管 (周天海，设备专库) | **完全缺失！**<br>(未在 PRESET_USERS 中收录) | `username: 'mgr_equip'`<br>`deptCode: 'EQUIP_DEPT'` | **角色遗漏**：用户明确要求的 4 大演示角色之一在前端缺失，无法一键切换为设备科视角 |
| **临床二级库** | 临床护士 (李晓琳/陈雅文，二级库管辖) | `username: 'cardio_nurse'`<br>`deptCode: 'SEC_CARDIO'` | `username: 'nurse_ortho'` (骨科)<br>`username: 'nurse_cardio'` (心内科) | **账号名不匹配**：前端用户名与后端不一致 |
| **财务合规审计** | 财务科审计 (孙丽娟，成本与单据) | `username: 'finance_auditor'`<br>`deptCode: 'FINANCE_DEPT'` | `username: 'mgr_finance'`<br>`deptCode: 'FINANCE_DEPT'` | **账号名不匹配**：前端用户名与后端不一致 |
| **信息科管理员** | 系统管理员 (赵振华，最大权限) | `username: 'admin'`<br>`deptCode: 'INFO_DEPT'` | `username: 'admin'`<br>`deptCode: 'INFO_DEPT'` | **一致** |
| **供应商代表** | 供应商代表 (张明远，协同端) | `username: 'supplier_rep'` | `username: 'supplier_wego'` | **账号名不匹配** |

#### 1.4.2 认证登录函数内幕 (`userStore.ts:143-165`)
```typescript
async login(account: string, _password?: string): Promise<boolean> {
  const matched = PRESET_USERS.find((u) => u.username === account.trim()) || PRESET_USERS[0];
  this.currentUser = matched;
  this.isLoggedIn = true;
  this.token = `spd_token_${matched.username}_${Date.now()}`;
  localStorage.setItem('spd_is_logged_in', 'true');
  localStorage.setItem('spd_token', this.token);
  localStorage.setItem('spd_active_user', JSON.stringify(matched));
  await this.fetchPermissions();
  return true;
}
```
- 前端 `login` 与 `loginAsRole` 完全没有发起 HTTP 请求至 `POST /api/v1/auth/login`；
- 它仅仅生成了一个纯客户端时间戳字符串作为 Token，因此无法从后端获得签名的 JWT Access Token。
- 但由于 `fetchPermissions()` 内包装了 `try...catch` 降级逻辑，在后端离线时也不会崩溃，这为构建高韧性自适应策略提供了极佳的基础。

---

### 1.5 数字化展厅视图与后端真实接口对齐分析

分析 `docs/design/spd_integrated_showcase_demo.html` 中呈现的 10 大医疗卡片与 3 大法定合规指标，其与后端真实端点的映射能力完全完备：

| 展厅卡片序号与标签 | 原型标题与业务含义 | 原型展示状态数据 | 后端可对接的真实端点与数据字段 | 真实端点实测返回值 |
| :--- | :--- | :--- | :--- | :--- |
| **卡片 01** [药监局UDI] | 产品字典双维档案 (耗材/设备主库双归口) | 已建档 25 项标准物资 | `GET /api/v1/ext/dict/overview`<br>`data.products.length` | 真实返回：当前已建档 7 项核心标准物资 (可动态计算) |
| **卡片 02** [效期硬风控] | 主库集中验收入库 (冷链温控/资质比对) | 主库在库 1,870 件 | `GET /api/v1/stats/overview`<br>`data.main_warehouse_total_qty` | 真实返回：`1443` 件 (金额 `85,530.00` 元) |
| **卡片 03** [FEFO优先] | 主库按需分发调拨 (近效期先出/移库不计费) | 已下发调拨单 200 支 | `GET /api/v1/main-warehouse/distributions`<br>数量汇总与状态统计 | 真实返回：包含已发往骨科/心内科调拨单据 |
| **卡片 04** [一物一码SN] | 高值专仓智能柜 (由量到码智能拆包赋码锁定) | 专柜锁定 37 套 | `GET /api/v1/stats/overview`<br>`data.high_value_wh_total_items`<br>`GET /api/v1/high-value/items` | 真实返回：高值专柜在库单品 `4` 件 (金额 `6,240.00` 元) |
| **卡片 05** [定数包补货] | 临床二级库房管理 (骨科/心内科安全水位预警) | 低库存自动申领就绪 | `GET /api/v1/stats/overview`<br>`data.secondary_total_qty`<br>`data.low_stock_warning_count` | 真实返回：二级库在库 `300` 件，预警 `0` 种 |
| **卡片 06** [消耗即结算] | 患者扫码脱敏核销 (手术消耗绑定住院号) | 已脱敏核销: 张*华 | `GET /api/v1/high-value/items?item_status=USED_VERIFIED`<br>提取首条记录的 `patient_name_masked` | 真实返回：已脱敏核销患者为 `张*丰`，住院号 `ZY202611020088` |
| **卡片 07** [100%穿透] | 全流程 6W 物权台账 (人/物/时间/流向快照) | 审计合规率 100% | `GET /api/v1/workflow-logs`<br>`data.length` | 真实返回：全院 18 条 6W 流转闭环凭据，合规率 100% |
| **卡片 08** [法定单据] | 医院四联签字单据 (制单/主库/领用/财务签章) | 符合三甲内控规范 | `GET /api/v1/print/voucher/MAIN_INBOUND/INB-20261015-001`<br>`data.signatures` | 真实返回：4 联完整责任签章（王建国/孙丽娟/李晓琳） |
| **卡片 09** [智能调拨] | Agent 02 补货智能体 (多库房水位扫描) | 毫秒级调度就绪 | 挂载 LangGraph 工作流或调拨建议 API | 预备状态：就绪 |
| **卡片 10** [逆向召回] | Agent 04 溯源与召回 (UDI穿透溯源/批次冻结) | 全链路闭环就绪 | `GET /api/v1/workflow-logs?biz_order_no=...` | 预备状态：全链路闭环就绪 |
| **指标 01** | 100% 审计穿透 (6W物权交接) | 满足医保与卫健委飞检要求 | `GET /api/v1/workflow-logs` | 状态合规 |
| **指标 02** | 一物一码单品 (高值专仓拆包赋唯一UDI) | 扫码核销绑定住院号合规脱敏 | `GET /api/v1/high-value/items` | 状态合规 |
| **指标 03** | 移库不计费 (院内科室调拨不计入成本) | 临床实际消耗即结算，理顺内控 | `GET /api/v1/stats/dept-consumption` | 真实返回：已结算金额 461.50 元 |

---

### 1.6 TypeScript 接口与类型定义分布现状
- **现状观察**: `frontend/src/` 下**不存在 `types/` 目录**。
- **分散定义**:
  - `ApiResponse<T>`: 定义在 `frontend/src/api/request.ts:7-11`；
  - `WarehouseNode`, `CategoryNode`, `ProductDictItem`: 定义在 `frontend/src/api/dictApi.ts:6-46`；
  - `HighValueLifecycleOrder`: 定义在 `frontend/src/api/highValueApi.ts:6-21`；
  - `InboundOutboundOrder`: 定义在 `frontend/src/api/orderApi.ts:6-24`；
  - `UserModulePermissionItem`: 定义在 `frontend/src/api/rbacApi.ts:6-22`；
  - `StocktakeTransferOrder`: 定义在 `frontend/src/api/stocktakeTransferApi.ts:6-19`；
  - `SupplierPurchaseOrder`: 定义在 `frontend/src/api/supplierPurchaseApi.ts:6-20`；
  - `UserProfile`: 定义在 `frontend/src/stores/userStore.ts:7-14`。
- **缺失的后端 DTO 契约类型**:
  - 缺少 `StatsOverviewResponse`、`DeptConsumptionResponse`、`VoucherPrintResponse`（统计与打印）；
  - 缺少 `MainInventoryItem`、`DistributionOrderItem`（主库批次库存与分发）；
  - 缺少 `SecondaryInventoryItem`、`RequisitionOrderItem`（二级库台账与请领单）；
  - 缺少 `WorkflowLogItem`（6W 审计日志）；
  - 缺少 `ShowcaseCardItem`、`WallpaperManifestItem`（3D 展厅与壁纸联动契约）。

---

## 2. 推导逻辑 (Logic Chain)

```
[观察事实 1.1: request.ts 注入 X-Operator-User 且键名错误为 null 回退 admin]
   +
[观察事实 1.4: security.py 仅识别 X-Mock-User 与 Authorization Bearer Token]
   ==> [推导结论 1: 权限穿透失真]
       前端切换任何角色在后端均以系统管理员权限执行，无法真实展示二级库、耗材科与财务科之间的细粒度越权拦截。

[观察事实 1.4.1: userStore.ts 的 PRESET_USERS 账号与 MySQL seed_service 账号不一致]
   +
[观察事实 1.4.1: 遗漏设备科主管 mgr_equip 角色]
   ==> [推导结论 2: 登录通道必须重构]
       4 大核心角色通道必须纠正为:
       - 耗材科主管: mgr_consumable
       - 设备科主管: mgr_equip (补齐)
       - 临床二级库: nurse_ortho / nurse_cardio
       - 财务科审计: mgr_finance
       且必须双向支持真实后端 JWT 登录与离线 Mock 免密直通。

[观察事实 1.2: FinancePrintView 与 GeneralMaterialView 存在大量完全写死的 Mock 数据]
   +
[观察事实 1.5: 后端 stats/overview, dept-consumption, voucher print 均有高可用真实数据]
   ==> [推导结论 3: 数据流倒挂需治理]
       视图层必须推翻简陋假数据，直连后端真实聚合接口；同时建立统一 Fallback 仓储层，在后端宕机或 Playwright CI 无后端环境下 100% 自动降级呈现高拟真数据，达成零网络报错与零视觉割裂。

[观察事实 1.6: 类型定义零散分布在各个 api 文件，无 types/ 规范目录]
   +
[观察事实 1.1: 生产构建告警 index.js 单包超 1.1MB]
   ==> [推导结论 4: 架构解耦与类型中心化]
       需创建 frontend/src/types/ 统一纳管所有业务模型与 DTO，并在 vite.config.ts 中通过 manualChunks 拆包。
```

---

## 3. 边界与限制 (Caveats)

1. **调研阶段只读约束**：本报告作为 Stage 0 调研成果，保持严格只读，不擅自修改任何现有业务代码，所有建议作为后续开发依据；
2. **前后端联调网络基线**：当前后端已在 `http://127.0.0.1:8000` 正常运行，Vite 代理能够正常转发 `/api` 请求；
3. **全域严禁 Emoji 铁律**：后续所有新增的数据字典、Mock 数据及通知文案中，必须 100% 杜绝任何 Emoji 字符。

---

## 4. 结论与自适应数据流重构方案 (Conclusion & Strategy)

基于以上调研事实，为全面落地高质感 3D 展厅（Showcase）、医慧通行安全模态登录中枢与各业务工作台，提出以下标准化实施规范：

### 4.1 方案 A：双轨自适应高韧性数据请求策略 (High-Resilience Dual-Engine Strategy)

在 `frontend/src/api/` 引入 **“优先真实后端，优雅平滑降级”** 的高韧性策略：

```
                    [前端视图或 3D 展厅组件发起数据请求]
                                    │
                                    ▼
                     [调用统一 API 函数 (如 fetchStatsOverview)]
                                    │
                         ┌──────────┴──────────┐
                         │ 尝试发起真实 Axios 网络请求 │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
             [请求成功 200]                   [请求失败 / 超时 / 离线]
                    │                               │
                    ▼                               ▼
            [返回 live 后端数据]             [控制台打印 warn (防侵入)]
                    │                               │
                    │                        [提取 fallbackData 拟真资产]
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                      [视图层渲染真实/拟真高质感卡片]
                      (保证自动化测试与演示 100% 不白屏)
```

### 4.2 方案 B：Axios 拦截器修复契约 (`frontend/src/api/request.ts`)
1. **注入有效身份凭证**：
   - 从 `localStorage.getItem('spd_token')` 提取令牌，注入 `config.headers['Authorization'] = 'Bearer ' + token`；
   - 从 `userStore.currentUser.username` 提取当前账号，同时注入 `config.headers['X-Mock-User'] = username` 与 `config.headers['X-Operator-User'] = encodeURIComponent(username)`，实现双端兼容；
2. **扩充请求方法封装**：
   - 增加 `httpPut<T>(url, data)` 与 `httpDelete<T>(url, params)` 标准导出。

### 4.3 方案 C：4 大核心演示角色契约对齐方案
在 `frontend/src/stores/userStore.ts` 中将预设人员完全对齐后端真实数据库：
```typescript
export const PRESET_USERS: UserProfile[] = [
  {
    id: 1,
    username: 'admin',
    realName: '赵振华 (系统管理员)',
    roleCode: 'sys_admin',
    deptCode: 'INFO_DEPT',
    deptName: '信息科管理中心'
  },
  {
    id: 2,
    username: 'mgr_consumable',
    realName: '王建国 (耗材科主管)',
    roleCode: 'dept_manager',
    deptCode: 'CONSUMABLE_DEPT',
    deptName: '耗材科主库房'
  },
  {
    id: 3,
    username: 'mgr_equip',
    realName: '周天海 (设备科主管)',
    roleCode: 'dept_manager',
    deptCode: 'EQUIP_DEPT',
    deptName: '设备科主库房'
  },
  {
    id: 5,
    username: 'nurse_ortho',
    realName: '李晓琳 (骨科责任护士)',
    roleCode: 'secondary_user',
    deptCode: 'SEC_ORTHO',
    deptName: '骨科病区二级库'
  },
  {
    id: 4,
    username: 'mgr_finance',
    realName: '孙丽娟 (财务审计主管)',
    roleCode: 'finance_auditor',
    deptCode: 'FINANCE_DEPT',
    deptName: '财务科审计室'
  },
  {
    id: 7,
    username: 'supplier_wego',
    realName: '张明远 (威高医药代表)',
    roleCode: 'supplier_user',
    deptCode: 'SUPPLIER_EXT',
    deptName: '威高医疗(供应商协同)'
  }
];
```
登录时：
1. 优先调用后端 `POST /api/v1/auth/login` 进行真实密码验证（默认密码 `123456`）；
2. 若调用成功，将后端返回的真实 JWT Access Token 存入 `spd_token`；
3. 若网络失败或服务未启动，平滑降级为本地免密模拟登录，保障演示与自动化测试无死锁。

### 4.4 方案 D：类型系统物理分层规范 (`frontend/src/types/`)
创建标准化类型契约目录：
- `frontend/src/types/api.ts`: 全局 `ApiResponse<T>`, `PaginationQuery`
- `frontend/src/types/auth.ts`: `UserProfile`, `LoginRequest`, `LoginResponse`, `RoleCode`
- `frontend/src/types/dict.ts`: `WarehouseNode`, `CategoryNode`, `ProductDictItem`, `PriceAdjustDTO`
- `frontend/src/types/order.ts`: `InboundOutboundOrder`, `RequisitionOrder`, `StocktakeTransferOrder`
- `frontend/src/types/highValue.ts`: `HighValueItem`, `HighValueLifecycleOrder`, `HighValueQrVerifyDTO`
- `frontend/src/types/stats.ts`: `StatsOverview`, `DeptConsumption`, `VoucherPrintData`, `VoucherSignatures`
- `frontend/src/types/trace.ts`: `WorkflowLogItem`, `WorkflowNodeAction`
- `frontend/src/types/showcase.ts`: `ShowcaseMedicalAsset`, `ShowcaseLegalMetric`, `ShowcaseWallpaperItem`

---

## 5. 独立验证方法 (Verification Method)

### 5.1 后端各核心端点连通性测试
在终端运行以下命令，验证后端真实数据输出能力：
```bash
# 1. 验证健康检查与版本
curl.exe -s http://127.0.0.1:8000/api/v1/health

# 2. 验证全院库存总盘概况
curl.exe -s http://127.0.0.1:8000/api/v1/stats/overview

# 3. 验证各科室消耗精算排行
curl.exe -s http://127.0.0.1:8000/api/v1/stats/dept-consumption

# 4. 验证真实四联单据打印结构
curl.exe -s http://127.0.0.1:8000/api/v1/print/voucher/MAIN_INBOUND/INB-20261015-001

# 5. 验证全流程 6W 物权交接日志 (当前有 18 条真实流转记录)
curl.exe -s http://127.0.0.1:8000/api/v1/workflow-logs

# 6. 验证高值专仓单品列表
curl.exe -s http://127.0.0.1:8000/api/v1/high-value/items
```

### 5.2 前端代码编译与类型严格检查
在前端目录运行生产构建与 TypeScript 检查：
```bash
npm --prefix frontend run build
```
断言：`vue-tsc` 输出 0 错误、0 警告。
