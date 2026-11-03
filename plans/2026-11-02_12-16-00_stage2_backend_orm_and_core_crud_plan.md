# 阶段 2 研发计划：后端存储基建（SQLAlchemy 2.0 ORM 100% 中文注释映射）与 5 套核心业务 CRUD 接口开发

- **计划文档路径**：`plans/2026-11-02_12-16-00_stage2_backend_orm_and_core_crud_plan.md`
- **记录时间戳**：`2026-11-02 12:16:00`
- **当前所处阶段**：阶段 2（后端存储基建与核心业务 CRUD 接口开发）
- **按需挂载项目 Skills**：
  - `Skill 01: sqlalchemy_orm_with_comment`（强制 100% 表级与字段级中文 `comment` 映射）
  - `Skill 02: fastapi_restful_crud_router`（标准 `{code, msg, data}` 与三级角色主科室归口鉴权）
  - `Skill 03: main_to_high_value_split_code`（主库向高值专仓分发时“由量到码”拆包赋唯一 UDI 序列号）
  - `Skill 04: patient_and_user_privacy_desensitize`（患者姓名、手机号、身份证号自动脱敏）
  - `Skill 05: workflow_6w_trace_logger`（8 大流转节点 100% 自动写入 `spd_workflow_log` 6W 台账）

---

## 一、 变更计划与物理文件清单

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_12-16-00_stage2_backend_orm_and_core_crud_plan.md
- 记录时间戳：2026-11-02 12:16:00
- 前端目标文件：无（本阶段严格聚焦 backend/ 与 tests/，严禁跨层污染）
- 后端目标文件：
  1. backend/requirements.txt —— 声明 FastAPI、Uvicorn、SQLAlchemy 2.0、PyMySQL、Cryptography、Redis、Pydantic V2、Python-Dotenv 等依赖清单
  2. backend/.env.example & backend/.env —— 本地 MySQL 8.0 (medical_spd_system)、Redis、Chroma 及 Ollama / 小米 MiMo / Coze 可插拔环境变量配置
  3. backend/app/__init__.py —— 后端应用包初始化
  4. backend/app/core/config.py —— 全局配置读取器与环境变量解析模块
  5. backend/app/core/database.py —— SQLAlchemy 2.0 数据库引擎、会话工厂、自动建库建表（create_all）与 Redis 缓存降级兼容连接器
  6. backend/app/core/security.py —— JWT 令牌签发校验、密码哈希、三级角色鉴权依赖与 Skill 04 患者/人员隐私脱敏工具函数
  7. backend/app/models/__init__.py & backend/app/models/spd_models.py —— 严格对齐 docs/db_schema.md 的 10 张 SQLAlchemy 2.0 声明式 ORM 模型（100% 包含表级与字段级中文 comment 注释）
  8. backend/app/schemas/spd_schemas.py —— Pydantic V2 统一响应模型 ApiResponse[T] 及全模块请求/响应数据契约
  9. backend/app/services/trace_service.py —— Skill 05 封装：全流程 6W 物权交接日志 (spd_workflow_log) 统一埋点写入服务与 Skill 03 高值耗材“由量到码”拆包赋码服务
  10. backend/app/services/seed_service.py —— 医院真实场景种子数据幂等初始化器（6 大科室、三级角色代表账号、双维产品分类与字典、主库批次库存、高值 UDI 单品、二级库库存、全流程 6W 初始台账）
  11. backend/app/routers/auth_router.py —— 登录、注册、当前用户信息、全院人员 CRUD 与科室树接口 (/api/v1/auth, /api/v1/users, /api/v1/departments)
  12. backend/app/routers/dict_router.py —— 核心 CRUD 一：产品字典与“主库房主科室+耗材分类”双维分类管理接口 (/api/v1/dict)
  13. backend/app/routers/main_warehouse_router.py —— 核心 CRUD 二：普通耗材管理（主库全部物资验收入库、批次库存管理、FEFO 排序、按需分发至临床二级库或高值耗材仓库接口 /api/v1/main-warehouse）
  14. backend/app/routers/high_value_router.py —— 核心 CRUD 三：高值耗材专仓一物一码管理与临床患者扫码核销接口 (/api/v1/high-value)
  15. backend/app/routers/secondary_warehouse_router.py —— 核心 CRUD 四：临床二级库库存、主库分发签收/拒收、日常消耗登记、向主库正向申领与逆向退库审批接口 (/api/v1/secondary-warehouse)
  16. backend/app/routers/workflow_log_router.py —— 核心 CRUD 五：全流程业务链路 6W 日志穿透查询、补录、审计复核与清理接口 (/api/v1/workflow-logs)
  17. backend/app/routers/stats_print_router.py —— 全院库存与财务科室消耗统计大盘 + 5 类医院标准四联签字单据结构化打印数据接口 (/api/v1/stats, /api/v1/print)
  18. backend/app/main.py —— FastAPI 应用主入口、CORS 中间件、全局异常拦截、生命周期自动建表与种子数据注入、Swagger 文档挂载及后端健康检查可视化面板 (/api/v1/health/dashboard)
- 测试与截图文件：
  1. tests/harness/verify_stage2_backend.js —— 阶段 2 后端 ORM 注释合规扫描 + 全套 CRUD 接口 E2E 闭环联调 + Playwright 实机渲染后端健康与数据库注释看板验证脚本
  2. tests/screenshots/2026-11-02_[HH-MM-SS]_stage2_backend_api_and_orm_verify.png —— 阶段 2 后端接口与 MySQL ORM 建表实机验证截图
```

---

## 二、 核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`98%`
- **潜在风险点与预案**：
  - **风险点 1（本地 MySQL root 密码差异）**：不同开发机上本地 `MySQL80` 服务的 `root` 密码可能为常见密码（如 `123456`、`root`、空密码等）或需读取环境变量。**应对策略**：在 `backend/app/core/database.py` 中优先读取 `.env` 中的 `MYSQL_PASSWORD`，同时支持自动探测本地常见开发口令并自动执行 `CREATE DATABASE IF NOT EXISTS medical_spd_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`；若本地 MySQL 端口临时受限，提供无缝的 SQLite 内存/文件级兜底并输出明确告警，确保开发测试 100% 不中断。
  - **风险点 2（ORM `comment` 静态扫描守卫）**：`tests/harness/guardrails.js` 会扫描 `backend/app/models/` 下所有 `.py` 文件的 `mapped_column` 是否 100% 携带 `comment="..."`。**应对策略**：编写 `spd_models.py` 时严格复用 `docs/db_schema.md` 中已通过校验的 175 处 `comment` 定义。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：提供毫秒级响应的 RESTful 接口与清晰的中文业务阻断提示（如“该物资批次已过期，禁止分发”、“该产品在主库仍有库存，禁止删除字典”），并提供直观的后端 ORM 表结构与接口自检看板供实时预览。
- **开发者体验（DX）**：所有模块严格按 `core / models / schemas / services / routers` 分层；100% 覆盖函数级 `@param`, `@returns`, `@route`, `@throws` 中文四要素注释；通过 ORM 自动完成建表与种子数据幂等初始化，开箱即用。
- **AI 代理体验（AX）**：MySQL 表结构与 SQLAlchemy 模型 100% 带有业务级中文 `comment`，在下一阶段（阶段 3）接入 MCP 数据库工具时，大模型可直接读取 `INFORMATION_SCHEMA.COLUMNS` 中的 `COLUMN_COMMENT` 零幻觉生成精准查询。
- **存量保护**：对阶段 1 已落盘的 `CLAUDE.md`、`AGENTS.md`、`SKILL.md`、`docs/` 零破坏。

### 3. Playwright 自动化回环测试与截图验证方案
- **验证脚本**：`tests/harness/verify_stage2_backend.js`
- **自动化验证链路**：
  1. 调用 `tests/harness/guardrails.js` 对 `backend/` 全部新增 Python 源码执行 **Emoji 零容忍扫描** 与 **`backend/app/models/spd_models.py` 全字段中文 `comment` 100% 覆盖率扫描**；
  2. 启动 FastAPI 后端服务，依次执行端到端业务 API 闭环断言：
     - **断言 1（三级角色登录与科室树）**：验证信息科 `admin`、耗材科 `mgr_consumable`、设备科 `mgr_equip`、财务科 `mgr_finance`、骨科二级库 `nurse_ortho` 登录及 `/api/v1/departments` 返回完整科室树；
     - **断言 2（产品字典双维分类 CRUD）**：验证新增产品字典自动归属主库房下主科室（耗材科/设备科）并自动写入 `1_DICT_CREATE` 6W 流转日志；
     - **断言 3（主库入库与按需分发双通道）**：验证主库验收入库（节点 `2_MAIN_INBOUND`）-> 按需分发至骨科二级库（节点 `3_MAIN_DISPATCH`，移库不计费 `is_billable=0`）-> 按需分发至高值专仓自动触发“由量到码”生成唯一 UDI 序列号（节点 `4_HIGH_VALUE_CODE`）；
     - **断言 4（高值耗材患者扫码脱敏核销）**：验证临床对高值 UDI 绑定患者姓名与手机号核销后，患者姓名自动脱敏（如 `张*丰`），触发财务记账（`is_billable=1`）并写入节点 `7_CLINICAL_CONSUME`；
     - **断言 5（二级库签收、申领与逆向退库回路）**：验证临床二级库签收主库分发单（节点 `5_SEC_RECEIVE`）、发起申领与耗材科审批（节点 `6_SEC_APPLY`）；
     - **断言 6（全流程 6W 日志与五类四联签字打印接口）**：验证 `/api/v1/workflow-logs` 完整记录交出人、接收人、前后库存快照，且 `/api/v1/print/voucher/...` 返回包含四联签字栏的结构化打印数据；
  3. 驱动持久化无锁 Playwright 浏览器访问后端实时自检与 ORM 注释全景看板（`http://127.0.0.1:8000/api/v1/health/dashboard`），校验 Console Error = 0，并截取高清实机验证图保存至 `tests/screenshots/`。

---

## 三、 技术与接口实现细节规范

### 1. 核心服务与工具函数签名（100% 中文四要素注释）

- **`backend/app/core/security.py`**
  - `mask_patient_name(name: str) -> str`：患者姓名脱敏（保留首尾或首字）。
  - `mask_phone(phone: str) -> str`：手机号脱敏（前 3 后 4）。
  - `mask_id_card(id_card: str) -> str`：身份证号脱敏（前 6 后 4）。
  - `get_current_user(...) -> SysUser`：解析请求头 `Authorization` 或演示快捷切换 Header `X-Mock-User`，返回当前操作人员实体。
- **`backend/app/services/trace_service.py`**
  - `record_workflow_6w_log(...) -> SpdWorkflowLog`：统一写入 `spd_workflow_log` 6W 物权交接台账。
  - `split_batch_to_high_value_udi(...) -> list[SpdHighValueItem]`：主库批次分发至高值专仓时，按分发数量 `dist_qty` 循环拆包生成全局唯一 `udi_sn` 与 `udi_full_code`。

### 2. 路由模块与权限边界设计

1. **`auth_router.py` (`/api/v1/auth`, `/api/v1/users`, `/api/v1/departments`)**：
   - 支持账号密码登录及前端演示一键切换角色视角（返回三级角色标识与归口科室编码 `dept_code`）。
2. **`dict_router.py` (`/api/v1/dict`)**：
   - 删除字典前强制校验 `SpdMainInventory`、`SpdHighValueItem`、`SpdSecondaryInventory` 中该产品可用库存总和必须为 `0`，否则返回 `code=400` 阻断。
3. **`main_warehouse_router.py` (`/api/v1/main-warehouse`)**：
   - 入库时校验 `expiry_date <= today` 或 `reg_cert_expiry <= today`，若已过期硬性拦截返回 `400`；
   - 查询主库库存默认按 `expiry_date ASC`（FEFO 近效期先出）排序；
   - 创建按需分发单支持 `TO_SECONDARY_DEPT`（发往临床二级库）与 `TO_HIGH_VALUE_WH`（转入高值专仓并自动调用 `Skill 03` 生成一物一码记录）。
4. **`high_value_router.py` (`/api/v1/high-value`)**：
   - 核销接口强制校验单品状态不为 `EXPIRED` / `RECALLED` / `USED_VERIFIED`，自动调用 `Skill 04` 脱敏患者姓名，并标记 `is_billable=1`。
5. **`secondary_warehouse_router.py` (`/api/v1/secondary-warehouse`)**：
   - 支持正常签收（`RECEIVED`，增加二级库库存）与差异拒收（`REJECTED`，自动将数量退回主库可用库存并记录逆向日志 `8_REVERSE_AUDIT`）；
   - 支持正向申领（`APPLY_FROM_MAIN`）与逆向退库（`RETURN_TO_MAIN`），并根据产品归口主科室（`CONSUMABLE_DEPT` 或 `EQUIP_DEPT`）定向路由审批。
6. **`workflow_log_router.py` (`/api/v1/workflow-logs`)**：
   - 支持按追踪号、单据号、物资编码、源科室/交出人、目标科室/接收人、8 大节点类型与计费标识多维穿透筛选；删除接口仅限 `sys_admin`（信息科人员）调用。
7. **`stats_print_router.py` (`/api/v1/stats`, `/api/v1/print`)**：
   - 提供全院库存总览、各二级库普通/高值消耗金额统计，以及 5 类法定单据（主库入库单、主库按需分发单、高值一物一码核销单、二级库申领/退库单、财务月度结算单）的四联签字结构化打印数据。

---

## 四、 强制性原子实施清单

```markdown
实施清单：
1. [已完成] [backend/] 创建 backend/requirements.txt、backend/.env.example 与 backend/.env，检查并补齐 Python 依赖环境。
2. [已完成] [backend/] 创建 backend/app/core/config.py、backend/app/core/database.py 与 backend/app/core/security.py（含数据库连接池、自动建库逻辑与 Skill 04 隐私脱敏函数）。
3. [已完成] [backend/] 按需应用 Skill 01，创建 backend/app/models/spd_models.py，完整编写 10 张 SQLAlchemy 2.0 声明式 ORM 模型（100% 携带表级与字段级中文 comment 注释，共 174 处）。
4. [已完成] [backend/] 创建 backend/app/schemas/spd_schemas.py，定义 Pydantic V2 统一响应封装与各模块出入参 Schema。
5. [已完成] [backend/] 按需应用 Skill 03 与 Skill 05，创建 backend/app/services/trace_service.py 与 backend/app/services/seed_service.py，实现 6W 全流程日志写入、高值拆码及医院真实场景种子数据幂等初始化。
6. [已完成] [backend/] 按需应用 Skill 02，依次创建 7 个模块化路由文件：auth_router.py、dict_router.py、main_warehouse_router.py、high_value_router.py、secondary_warehouse_router.py、workflow_log_router.py、stats_print_router.py，以及主入口 backend/app/main.py。
7. [已完成] [tests/] 编写 tests/harness/verify_stage2_backend.js，集成静态护栏扫描、全套 5 大 CRUD 业务流 E2E 接口断言与 Playwright 实机看板渲染验证。
8. [已完成] [tests/ | plans/] 启动 FastAPI 后端服务并运行 node tests/harness/verify_stage2_backend.js，校验功能完整性、捕获实机截图至 tests/screenshots/2026-11-02_12-30-00_stage2_backend_api_and_orm_verify.png 并更新 plans/ 进度台账。
```
