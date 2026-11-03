# 研发实施计划：全量 SPD 业务模块扩充、信息科 8 项解耦权限、两阶段二次确认状态机与供应商采购闭环

> 计划归档时间戳：2026-11-02 19:15:00  
> 任务标识符：`stage2_plus_full_spd_business_and_rbac_plan`  
> 关联协议：增强型 RIPER-5 代理执行协议（阶段 3：[MODE: PLAN]）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_19-15-00_stage2_plus_full_spd_business_and_rbac_plan.md
- 记录时间戳：2026-11-02 19:15:00
- 架构与 Harness 契约同步文件：
  - AGENTS.md（补充外部供应商角色 supplier_user 与离线数据清洗智能体 data_cleaning_agent 契约）
  - SKILL.md（新增沉淀 Skill 07 两阶段二次确认状态机技能与 Skill 08 细粒度8动作权限解耦技能）
- 后端目标文件 (backend/)：
  - backend/app/models/spd_extended_models.py（新增 7 张核心业务扩展 ORM 表，100% 携带表级与字段级中文 comment 注释）
  - backend/app/models/__init__.py（统一导出全部 17 张 SQLAlchemy 2.0 ORM 模型类）
  - backend/app/schemas/spd_extended_schemas.py（新增 Pydantic V2 强类型请求/响应校验模型）
  - backend/app/services/rbac_and_confirm_service.py（封装 8 项细粒度权限校验器、两阶段二次确认/取消提交状态机及跨单据自动联动引擎）
  - backend/app/routers/extended_spd_router.py（提供细粒度权限矩阵、产品字典深度扩展、普耗期初一次性锁定/退货/请领自动出库、高值备货/退货锁死/二维码核销、多级采购与供应商资质准入/接单/拣货/发货全套 RESTful 接口）
  - backend/app/services/seed_service.py（扩充五大角色 8 项权限矩阵、多仓库/分类树、供应商资质、期初数据、盘点单、高值二维码与多级采购种子数据）
  - backend/app/main.py（挂载扩展业务路由并升级后端健康监控大盘至 17 张 ORM 表全景展示）
- 测试与截图文件 (tests/)：
  - tests/harness/verify_full_spd_business.js（Playwright 全链路自动化回环验证脚本，覆盖 12 项核心业务与状态机强断言）
  - tests/screenshots/2026-11-02_19-15-00_full_spd_backend_and_matrix_verify.png（实机验证截图）
```

---

## 二、 核心评估指标（必填）

### 1. 可行性与把握度评估
- **把握度：98%**
- **潜在技术风险与应对策略**：
  - *风险点 1：新增 7 张 ORM 扩展表与存量 10 张表的兼容性*。
    - **应对**：严格遵循开闭原则（OCP），存量 `spd_models.py` 的 10 张表结构保持 100% 向后兼容，新增表统一定义在 `spd_extended_models.py` 并共享同一个 `DeclarativeBase`，启动时由 `Base.metadata.create_all(bind=engine)` 幂等创建全部 17 张物理表。
  - *风险点 2：高危单据（高值科室退货出库、科室期初数据）与普通单据在“取消提交”规则上的差异控制*。
    - **应对**：在状态机服务层 `rbac_and_confirm_service.py` 中内置不可逆单据白名单拦截器——普通单据在 `SUBMITTED` 状态下可调用 `cancel-submit` 退回 `PENDING_CONFIRM` 重新修改；但若单据类型为 `INIT_STOCK（期初数据）` 或 `HV_DEPT_RETURN（高值科室退货出库）`，一旦执行二次确认（`second-confirm`），立即将 `is_irreversible_locked` 置为 `1`，硬性阻断任何修改、删除或取消提交操作。
  - *风险点 3：供应商未通过经营许可证审核前越权接单*。
    - **应对**：在供应商接单与拣货发货接口前置校验 `spd_supplier_profile.qual_status == "APPROVED"`，若未上传或未通过耗材科/设备科审核，直接返回 `code: 403` 业务拦截提示。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：所有单据状态流转清晰透明，外层二次确认与取消提交反馈明确；后端监控大盘升级为 17 张表 + 全链路业务状态实时可视化看板，全域 0 Emoji。
- **开发者体验（DX）**：模块按职责清晰解耦，100% 覆盖 SQLAlchemy 中文 `comment` 与函数四要素中文注释（`@param`, `@returns`, `@route`, `@throws`）。
- **AI 代理体验（AX）**：结构化的接口返回 `{code, msg, data}` 与语义化表结构，为后续第二阶段挂载 Agentic RAG + GraphRAG 及 MCP 工具提供自解释的数据契约。
- **存量保护底线**：存量阶段 2 的全部接口与 `tests/harness/verify_stage2_backend.js` 保持 100% 零回归通过。

### 3. Playwright 自动化回环测试与截图验证方案
- **验证脚本**：`tests/harness/verify_full_spd_business.js`
- **12 项核心强断言设计**：
  1. **断言 1（Harness 静态护栏）**：扫描新增后端源码 100% 无 Emoji、100% 具备 ORM 中文 `comment` 与四要素注释；
  2. **断言 2（17 张 ORM 物理表映射）**：验证 MySQL 8.0 中全部 17 张表成功建表且 `information_schema.COLUMNS` 注释覆盖率 100%；
  3. **断言 3（信息科 8 项原子权限解耦）**：验证信息科管理员可针对指定账号动态开启/关闭某模块的 `[查、增、改、删、二次确认、取消提交、审批、打印]` 权限，且被关闭权限后调用对应接口被 403 精准拦截；
  4. **断言 4（产品字典双树与深度扩展）**：验证仓库树、分类树、自动生成拼音码、复制品名/复制规格、产品分配到仓库、变更供应商与调价台账记录；
  5. **断言 5（单据两阶段二次确认 + 取消提交状态机）**：验证单据第 1 次提交进入 `PENDING_CONFIRM`，外层第 2 次确认进入 `SUBMITTED`（此时直接修改被拦截），点击【取消提交】退回 `PENDING_CONFIRM` 后恢复可修改；
  6. **断言 6（科室仓库期初数据一次性锁定铁律）**：验证某科室填报期初数据并完成外层二次确认后，该科室期初建账状态永久锁定为只读，再次尝试填报或修改期初数据被硬性拦截；
  7. **断言 7（请领受理审核自动生成耗材出库单）**：验证主库审批通过请领单后，系统在耗材出库模块自动生成一条关联的审核出库记录；
  8. **断言 8（耗材入库退给供应商 & 各科室独立盘点修正库存）**：验证入库单退货给供应商扣减库存，以及科室盘点单（实盘 vs 账面）二次确认生效后自动修正库存并写入 6W 台账；
  9. **断言 9（高值科室退货出库永久锁死铁律）**：验证高值科室退货出库单在二次确认提交后，尝试修改或取消提交均被 403 永久锁死拦截；
  10. **断言 10（高值一物一码二维码扫码核销与查询过滤）**：验证未扫码核销的高值单品不在“高值核销查询”中显示；执行二维码扫码绑定患者核销后，立即在“高值核销查询”中精准查出；
  11. **断言 11（多级采购审批 + 供应商资质硬拦截 + 拣货发货自动生成医院待验收入库单）**：验证未审核资质的供应商接单被拦截 -> 院方审核通过供应商《经营许可证》 -> 临床科室采购计划经耗材科审批生成采购订单 -> 供应商接单、拣货、二次确认发货 -> 自动在医院端生成《待验收入库单》；
  12. **断言 12（Playwright 实机渲染全景验证大盘并截图归档）**：访问后端全景健康与业务矩阵看板，断言 0 Console Error / PageError，捕获实机截图保存至 `tests/screenshots/2026-11-02_19-15-00_full_spd_backend_and_matrix_verify.png`。

---

## 三、 技术与数据库 ORM 细节规范

### 1. 新增 7 张 SQLAlchemy 2.0 ORM 物理表（位于 `backend/app/models/spd_extended_models.py`）
1. `SysUserModulePermission` (`sys_user_module_permission`)：用户级细粒度模块 8 项动作权限解耦矩阵表；
2. `SpdWarehouseNode` (`spd_warehouse_node`)：全院多级仓库树与期初建账一次性锁定状态表（卫材库、总务仓库、信息仓库、专项库房、后勤仓库、测试仓库、设备库房及各科室二级库）；
3. `SpdProductDictExt` (`spd_product_dict_ext`)：产品字典扩展属性、拼音码、通用名、品牌、组件名、仓库分配映射与调价历史表；
4. `SpdInboundAndOutboundOrder` (`spd_inbound_outbound_order`)：普通耗材与二级库出入库单、退供应商红字单、请领自动出库单及期初建账单表（含两阶段确认状态机）；
5. `SpdStocktakeAndTransferOrder` (`spd_stocktake_transfer_order`)：全院各科室独立盘点单（普耗/高值/二级库账实盈亏）与跨科/跨院调拨单表；
6. `SpdHighValueLifecycleOrder` (`spd_high_value_lifecycle_order`)：高值耗材备货申请、科室接收入库、科室退货出库（提交即锁死）、高值报损与一物一码二维码核销表；
7. `SpdSupplierAndPurchaseOrder` (`spd_supplier_purchase_order`)：供应商经营许可证资质档案、医院绑定、科室多级采购计划单、供应商拣货配货与发货同行单表。

### 2. 核心接口与服务层函数签名规范（100% 覆盖中文四要素注释）
- `verify_user_module_action(db, user_id, module_code, action_key)`：校验指定用户在指定模块是否具备对应原子权限（`can_view` / `can_create` / `can_edit` / `can_delete` / `can_second_confirm` / `can_cancel_submit` / `can_approve` / `can_print`）；
- `transition_order_confirm_stage(db, order_model, order_id, action, operator)`：统一处理 `FIRST_SUBMIT`（进入 `PENDING_CONFIRM`）、`SECOND_CONFIRM`（进入 `SUBMITTED` 并触发下游联动）、`CANCEL_SUBMIT`（退回 `PENDING_CONFIRM`，校验不可逆锁死白名单）。

---

## 四、 强制性最终步骤（原子实施清单）

```markdown
实施清单（已于 2026-11-02 19:32:00 100% 执行完毕并通过 12 项强断言验证）：
1. [已完成] [AGENTS.md | SKILL.md] 同步更新 Harness 规范文档：在 AGENTS.md 补充供应商角色与数据清洗 Agent 契约；在 SKILL.md 沉淀 Skill 07（两阶段二次确认状态机）与 Skill 08（8项细粒度权限解耦）。
2. [已完成] [backend/] 编写 backend/app/models/spd_extended_models.py 并更新 backend/app/models/__init__.py，完整定义新增的 7 张 SQLAlchemy 2.0 ORM 物理表（100% 字段级与表级中文 comment 注释）。
3. [已完成] [backend/] 编写 backend/app/schemas/spd_extended_schemas.py，定义全套 Pydantic V2 入参出参数据契约。
4. [已完成] [backend/] 编写 backend/app/services/rbac_and_confirm_service.py，实现 8 项原子权限解耦校验、两阶段二次确认/取消提交状态机、科室期初一次性锁定、请领审批自动生成出库单、高值二维码核销、供应商发货自动生成待验收入库单逻辑。
5. [已完成] [backend/] 编写 backend/app/routers/extended_spd_router.py，暴露权限矩阵管理、产品字典深度管理（图4）、普通耗材管理（图1）、高值耗材管理（图2）、二级库管理（图3）、多级采购管理与供应商协同门户全套 RESTful 接口。
6. [已完成] [backend/] 更新 backend/app/services/seed_service.py 与 backend/app/main.py，注入全套业务初始种子数据，并将后端健康大盘升级为 17 张 ORM 表与全业务矩阵监控看板。
7. [已完成] [tests/] 编写 tests/harness/verify_full_spd_business.js 自动化测试脚本，覆盖全部 12 项核心业务与状态机强断言。
8. [已完成] [tests/ | plans/] 启动 FastAPI 后端服务并运行 Playwright 回环测试，校验全部 12 项强断言与存量测试 100% 通过，捕获实机截图保存至 tests/screenshots/2026-11-02_19-15-00_full_spd_backend_and_matrix_verify.png 并回传汇报。
```
