# SKILL.md - 医疗物资全链路管理系统全栈开发与自进化技能库

> **定位**：承载 **Harness 组件①（渐进式技能披露与按需路由）**、**组件⑤（反馈循环资产沉淀）** 与 **组件⑥（熵管理与技能治理）**，遵循开放技能标准。
> **核心铁律**：
> 1. **原型与生产样式物理隔离**：`docs/design/*.html` 仅作为产品经理（PM）用于对齐业务流转逻辑、字段契约与页面功能块划分的交互线框图（Wireframe），**绝对禁止将其简易线框样式直接照搬至生产级 `frontend/` 源码中**。
> 2. **按需渐进加载（Progressive Disclosure）**：严禁一次性将所有全局 Skills 塞入上下文；必须严格按照下方《全局已安装 Skills 分类图谱与按需触发矩阵》，在对应研发阶段按需读取指定路径的 `SKILL.md`。

---

## 一、 项目专属核心业务与防错技能清单 (Project Domain Skills)

### Skill 01: `sqlalchemy_orm_with_comment`
- **【描述】**：生成符合 MySQL 8.0 规范的 SQLAlchemy 2.0 声明式 ORM 模型代码，强制 100% 注入表级与字段级中文 `comment` 注释。
- **【入参】**：业务表名、实体类名、字段定义清单、索引与枚举状态说明。
- **【出参】**：位于 `backend/app/models/` 下的标准 Python ORM 类代码。
- **【硬性约束】**：
  1. 必须包含 `__table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "comment": "..."}`；
  2. 每一个 `mapped_column(...)` 必须显式包含非空的 `comment="..."` 参数，写明业务含义与状态枚举值（直接供 MCP 数据库工具读取）；
  3. 严禁手写无注释裸 SQL 脚本。

### Skill 02: `fastapi_restful_crud_router`
- **【描述】**：生成标准 FastAPI 模块化路由接口，配套 Pydantic V2 入参/出参 Schema、三级角色权限校验与四要素中文文档注释。
- **【入参】**：模块前缀、ORM 模型类、允许访问的角色列表（`sys_admin` / `dept_manager` / `secondary_user`）。
- **【出参】**：Router 接口代码 + Pydantic Schema + 标准 `{code, msg, data}` 响应封装。
- **【硬性约束】**：
  1. 每个函数必须 100% 包含 `@param`、`@returns`、`@route`、`@throws` 中文四要素注释；
  2. 涉及产品字典与申领流转时，必须校验 `main_dept_code`（耗材科 `CONSUMABLE_DEPT` vs 设备科 `EQUIP_DEPT`）归口权限。

### Skill 03: `main_to_high_value_split_code`
- **【描述】**：主库总仓向高值耗材专仓按需分发时的“由量到码（批次拆包赋一物一码）”转换技能。
- **【入参】**：主库批次库存记录 (`spd_main_inventory`)、分发数量 `dist_qty`、目标高值专仓货柜编码。
- **【出参】**：扣减主库可用数量 + 生成 `dist_qty` 条独立的 `spd_high_value_item` 单品 UDI 唯一序列号记录 + 写入 `spd_workflow_log` 节点 `4_HIGH_VALUE_CODE`。
- **【硬性约束】**：高值耗材入专仓后必须按单品唯一序列号 (`udi_sn`) 独立流转，临床核销时必须绑定患者住院号并触发财务记账 (`is_billable=1`)。

### Skill 04: `patient_and_user_privacy_desensitize`
- **【描述】**：医疗患者与院内人员敏感信息自动脱敏技能（由反馈循环重点强化的合规护栏技能）。
- **【入参】**：包含患者姓名、住院号、身份证号或手机号的原始字典/ORM 对象。
- **【出参】**：脱敏后的安全传输对象。
- **【硬性约束】**：
  1. 患者姓名脱敏规则：保留首尾或首字（如 `张*丰`、`李*`）；
  2. 手机号脱敏规则：保留前 3 后 4（如 `138****5678`）；
  3. 身份证脱敏规则：保留前 6 后 4（如 `330101********1234`）。

### Skill 05: `workflow_6w_trace_logger`
- **【描述】**：全流程业务链路日志（6W 物权交接台账）统一埋点写入技能。
- **【入参】**：关联单据号 `biz_order_no`、8 大节点类型 `node_action`、物资信息、交出方科室与操作人、接收方科室与责任人、变动数量与前后库存快照、是否计费 `is_billable`。
- **【出参】**：写入 `spd_workflow_log` 表的完整持久化记录。
- **【硬性约束】**：主库入库、主库按需分发、高值赋码、二级库签收、二级库申领、临床消耗核销、逆向退库/报损、财务审核 8 大节点必须 100% 触发本技能留痕。

### Skill 06: `medical_voucher_print_engine`
- **【描述】**：Vue 3 + Element Plus 医院标准 5 类法定单据四联签字打印组件构建技能。
- **【入参】**：单据类型（入库单/按需分发单/高值核销单/二级库申领单/财务结算单）、单据头信息、批次效期明细列表、签字人信息。
- **【出参】**：具备 `@media print` 专用打印样式、一维码/二维码展示区、状态水印及票尾【制单人 / 主库科室主管 / 二级库接收人 / 财务科复核】四联签字栏的 Vue 组件。
- **【硬性约束】**：全域禁用 Emoji，统一采用矢量 SVG 图标与 CSS 主题变量。

### Skill 07: `two_step_confirm_state_machine`
- **【描述】**：全业务单据通用“两阶段二次确认 + 取消提交 + 特例永久锁死”状态机技能。
- **【入参】**：业务单据 ORM 实例、操作动作（`FIRST_SUBMIT` / `SECOND_CONFIRM` / `CANCEL_SUBMIT`）、操作人及细粒度权限凭证。
- **【出参】**：更新后的单据状态（`DRAFT` -> `PENDING_CONFIRM` -> `SUBMITTED`）、联动生成的下游单据（如请领审核自动生成出库单、供应商发货自动生成医院待验收入库单）及 6W 审计日志。
- **【硬性约束】**：
  1. 第 1 次在填单页点【提交】进入 `PENDING_CONFIRM（待外层二次确认）`，此时单据仍允许修改或删除；
  2. 第 2 次在外层列表页点【确认提交】进入 `SUBMITTED（已正式提交）`，此时单据锁死不可直接修改或删除，并触发库存变动或下游单据自动生成；
  3. 对已进入 `SUBMITTED` 的普通单据，必须先执行 `CANCEL_SUBMIT（取消提交）` 退回 `PENDING_CONFIRM` 后方可修改或删除；
  4. **不可逆锁死特例**：`HV_DEPT_RETURN（高值耗材-科室退货出库单）` 与 `INIT_STOCK（各科室仓库期初数据建账单）` 一旦完成第 2 次确认提交进入 `SUBMITTED`，`is_irreversible_locked=1`，永久锁定只读，严禁执行 `CANCEL_SUBMIT`、修改或删除。

### Skill 08: `decoupled_8_action_rbac`
- **【描述】**：信息科解耦式 15 模块 × 8 动作细粒度权限矩阵鉴权与动态开关技能。
- **【入参】**：目标用户 `user_id`、业务模块编码 `module_code`、原子动作编码 `action_code`（`can_view` / `can_create` / `can_edit` / `can_delete` / `can_second_confirm` / `can_cancel_submit` / `can_approve` / `can_print`）。
- **【出参】**：布尔鉴权结果或更新后的用户权限矩阵配置。
- **【硬性约束】**：支持五大角色（`sys_admin` / `dept_manager` / `secondary_user` / `finance_auditor` / `supplier_user`）默认模板初始化，且允许信息科管理员针对任意具体人员账号独立开启或关闭任意模块下的 8 项原子操作权限。

---

## 二、 全局已安装 Skills 分类图谱与按需渐进加载规范 (Global Skills Registry & On-Demand Routing)

经盘点宿主环境（`C:\Users\27705\.gemini\config\skills\`、`C:\Users\27705\.gemini\skills\` 与 `C:\Users\27705\.gemini\antigravity\builtin\skills\`），本地共安装 **26 个全局 Skills**。现将其归类为 **6 大工程象限**，并严格规定在 Harness 工程生命周期中的**按需加载时机（On-Demand Trigger Timing）**：

### 第一类：前端视觉精雕与设计工程类 (Frontend UI Craft & Design Engineering)
> **核心定位**：专供 **Frontend UI Agent** 在编写 `frontend/src/` 真正生产级 Vue 3 页面、Design Tokens、三级工作台、UDI 溯源时间轴与智能体交互舱时按需加载，打造现代、通透、克制的高质感医疗系统界面，彻底脱离 `docs/design/` 原型线框风格。

| 技能名称 (Skill ID) | 全局物理路径 (`SKILL.md`) | 核心能力提炼 | 强制按需加载时机 (When to Load) |
| :--- | :--- | :--- | :--- |
| **`emil-design-eng`** | `C:\Users\27705\.gemini\config\skills\emil-design-eng\SKILL.md` | Emil Kowalski 的 UI 精雕哲学：微交互质感、视觉克制、隐形交互细节（热区扩展、防布局抖动、按下缩放反馈、定制缓动曲线） | **【阶段 4 前端基建与组件精雕】**：在搭建 `frontend/src/styles/` 全局设计变量、封装通用表格/弹窗/抽屉及编写 5 大核心业务视图前**必读加载** |
| **`apple-design`** | `C:\Users\27705\.gemini\config\skills\apple-design\SKILL.md` | Apple HIG 视觉规范与反模板化设计审查：亮暗色主题对比度、毛玻璃半透明材质层级（Liquid Glass / Translucent Materials）、表单与导航清晰度 | **【阶段 4 视觉走查与主题适配】**：在设计三级角色工作台顶部导航、侧边栏、暗黑模式（Dark Mode）切换及高密度医疗数据卡片布局时**按需加载** |
| **`emil-apple-design`** | `C:\Users\27705\.gemini\config\skills\emil-apple-design\SKILL.md` | Apple WWDC 流体界面（Fluid Interfaces）的 Web 端转译：弹簧物理手感、动量传递、可打断交互与克制动效 | **【阶段 4 智能体浮窗与抽屉交互】**：在实现右侧 5 大 LangGraph 智能体滑出面板、高值 UDI 溯源抽屉及角色视角平滑切换时**按需加载** |
| **`prototype`** | `C:\Users\27705\.gemini\config\skills\prototype\SKILL.md` | 在正式定稿复杂页面前，生成多个真正差异化的高质感视觉变体（带实时切换器）供比选 | **【阶段 4 核心看板多方案比选】**：当用户希望对比多种工作台首页布局或统计看板视觉风格时**按需加载** |
| **`pick-ui-library`** | `C:\Users\27705\.gemini\config\skills\pick-ui-library\SKILL.md` | 前端细分功能库选型指南（图表、命令面板 `Cmd+K`、虚拟滚动列表、Toast 通知等） | **【阶段 4 前端 package.json 依赖选型】**：在为统计看板选型图表库、为智能体选型快捷键面板或通知组件时**按需加载** |
| **`ask-sonner`** | `C:\Users\27705\.gemini\config\skills\ask-sonner\SKILL.md` | 现代轻量化 Toast 通知设计（Loading 态异步承諾提示、暗黑模式适配、层级防遮挡） | **【阶段 4 异步操作反馈封装】**：在实现主库入库提交、按需分发调拨、智能体流式调用状态提示时**按需加载** |
| **`mobile-native`** | `C:\Users\27705\.gemini\config\skills\mobile-native\SKILL.md` | 消除 Web 端廉价网页感细节（`user-select: none` 防双击选中文字、`100dvh` 视口稳定、滚动容器防串扰） | **【阶段 4 响应式与触控防抖加固】**：在加固临床二级库护士平板端/PC 端扫码核销台的高频点击体验时**按需加载** |

---

### 第二类：前端动效决策与 60fps 帧率性能优化类 (Web Motion & Animation Performance)
> **核心定位**：专供 **Frontend UI Agent** 在为页面过渡、单据打印预览弹出、LangGraph 智能体节点流转动画编写 CSS/WAAPI 动效时按需加载，确保动画既灵动又严格控制在帧预算（Frame Budget）内。

| 技能名称 (Skill ID) | 全局物理路径 (`SKILL.md`) | 核心能力提炼 | 强制按需加载时机 (When to Load) |
| :--- | :--- | :--- | :--- |
| **`animate`** | `C:\Users\27705\.gemini\config\skills\animate\SKILL.md` | 从零构建动画的完整决策链：是否应该加动画 -> 动画目的 -> CSS/WAAPI 工具选择 -> 缓动曲线与时长 -> 退出与打断处理 | **【阶段 4 新增组件过渡与状态动效】**：在编写 5 大业务智能体 LangGraph 节点高亮流转图、UDI 6W 溯源时间轴展开动画时**按需加载** |
| **`animation-performance`** | `C:\Users\27705\.gemini\config\skills\animation-performance\SKILL.md` | 帧率性能守卫：仅动画合成层属性（`transform`/`opacity`）、避免主线程重排（Layout Thrashing）、合理控制模糊（`backdrop-filter`）与 `will-change` 开销 | **【阶段 4/5 大数据量表格与动画性能调优】**：当全流程日志表或主库库存表伴随抽屉动画出现掉帧卡顿时**按需加载** |
| **`find-animation-opportunities`** | `C:\Users\27705\.gemini\config\skills\find-animation-opportunities\SKILL.md` | 只读扫描现有 UI 代码，识别哪些生硬的显隐切换值得补充微动效，并拒绝无意义的视觉噪音 | **【阶段 4 前端主体功能完成后的体验提亮】**：在 5 套 CRUD 页面静态开发完成后，进行微交互走查时**按需加载** |
| **`improve-animations`** | `C:\Users\27705\.gemini\config\skills\improve-animations\SKILL.md` | 全局动效审计与优化计划生成（统一曲线、修正过慢时长） | **【阶段 5 交付前 UI 动效统一校准】**：当发现不同页面弹窗/切换动效时长不一致时**按需加载** |
| **`review-animations`** | `C:\Users\27705\.gemini\config\skills\review-animations\SKILL.md` | 针对单个组件或 Diff 的动效代码质量评审 | **【阶段 4 复杂交互组件自检】**：完成智能体对话舱与打印预览抽屉后**按需加载** |
| **`animation-vocabulary`** | `C:\Users\27705\.gemini\config\skills\animation-vocabulary\SKILL.md` | 动效专业术语逆向检索词典（将自然语言描述映射为标准动效范式名称） | **【按需检索】**：当需要精确定义某种过渡效果名称时按需查阅 |

---

### 第三类：前端极限数据压测与浏览器自动化探针类 (UI Stress Testing & Browser Harness)
> **核心定位**：专供 **QA & Harness Agent** 与 **Frontend UI Agent** 在阶段 4/5 检验前端界面抗压能力（超长医疗器械名称、极端库存数值、空状态）与浏览器实机回环验证时按需加载。

| 技能名称 (Skill ID) | 全局物理路径 (`SKILL.md`) | 核心能力提炼 | 强制按需加载时机 (When to Load) |
| :--- | :--- | :--- | :--- |
| **`break-ui`** | `C:\Users\27705\.gemini\config\skills\break-ui\SKILL.md` | 使用极端恶劣数据（超长进口耗材注册证名称、百万级库存数量、0 库存、缺失字段、超长批号）注入 UI，暴露文本溢出、挤压变形与折行崩溃问题并逐一修复 | **【阶段 4/5 前端组件抗压测试（强烈推荐）】**：在完成产品字典、主库库存表、6W 日志表与四联打印单组件后**按需加载**，确保极端医疗数据下绝不破版 |
| **`ego-browser`** | `C:\Users\27705\.gemini\config\skills\ego-browser\SKILL.md` | 本地 Ego 浏览器自动化控制与快照交互辅助工具 | **【阶段 5 备用浏览器探针】**：除内置 Playwright `tests/harness/runner.js` 外，如需调用本地 Ego 浏览器 CLI 时**按需加载** |

---

### 第四类：产品需求规划、交互图件与 Word 交付文档生成类 (PM Workflow & Delivery Docs)
> **核心定位**：专供 **Orchestrator Agent** 在阶段 1 需求梳理与 **阶段 5 最终项目路演汇报、5 分钟演讲逐字稿（Word `.docx`）导出**时按需加载。

| 技能名称 (Skill ID) | 全局物理路径 (`SKILL.md`) | 核心能力提炼 | 强制按需加载时机 (When to Load) |
| :--- | :--- | :--- | :--- |
| **`edu-pm-workflow`** | `C:\Users\27705\.gemini\config\skills\edu-pm-workflow\SKILL.md` | 产品经理标准工作流：PRD 文档、业务流程图、功能线框原型、验收清单与数据分析报告生成 | **【阶段 1 需求与业务流梳理（已完成加载）】**：已用于生成 `docs/design/` 下的业务流程图、功能线框图与 PRD 规格说明书 |
| **`minimax-docx`** | `C:\Users\27705\.gemini\skills\minimax-docx\SKILL.md` | 专业级 OpenXML `.docx` Word 文档排版、封面、表格与样式构建引擎 | **【阶段 5 最终交付物打包与 5 分钟演讲逐字稿导出】**：在生成项目答辩演讲逐字稿（含精确到秒的分镜与操作提示 Word 文档）及项目验收报告 `.docx` 时**必读加载** |
| **`generative_ui`** | `C:\Users\27705\.gemini\antigravity\builtin\skills\generative_ui\SKILL.md` | 富交互 HTML 可视化小部件构建规范 | **【按需加载】**：当需要在对话或文档中向用户直观展示动态架构演进或数据沙盘时按需加载 |

---

### 第五类：平台工程、工作流编排与宿主环境治理类 (Platform & DevOps Governance)
> **核心定位**：专供 **Orchestrator Agent** 在配置 MCP 服务、自动化定时任务、Git 版本推送或磁盘清理时按需加载。

| 技能名称 (Skill ID) | 全局物理路径 (`SKILL.md`) | 核心能力提炼 | 强制按需加载时机 (When to Load) |
| :--- | :--- | :--- | :--- |
| **`agy-customizations`** | `C:\Users\27705\.gemini\antigravity\builtin\skills\agy-customizations\SKILL.md` | Antigravity 规则、Skills、MCP 服务器与 Hooks 定制与加载优先级指南 | **【按需加载】**：当需要扩展项目级自定义规则或 MCP 配置时加载 |
| **`antigravity_guide`** | `C:\Users\27705\.gemini\antigravity\builtin\skills\antigravity_guide\SKILL.md` | Antigravity IDE / CLI 官方参考指南 | **【按需加载】**：解答平台特性或快捷键命令时加载 |
| **`automation`** | `C:\Users\27705\.gemini\antigravity\builtin\skills\automation\SKILL.md` | 后台周期性定时调度任务设计指南 | **【按需加载】**：当需要设计效期定时巡检或后台自动归档任务时加载 |
| **`permissioned-github`** | `C:\Users\27705\.gemini\skills\permissioned-github\SKILL.md` | 受控权限下的 GitHub 远程仓库创建、提交与推送流程 | **【阶段 5 Git 远程仓库交付】**：当用户要求将本项目推送至 GitHub 仓库时**按需加载** |
| **`storage-analyzer`** | `C:\Users\27705\.gemini\skills\storage-analyzer\SKILL.md` | 磁盘空间扫描与大文件冗余清理 | **【按需加载】**：当本地环境出现磁盘空间告警或需清理冗余缓存时加载 |
| **`plugin` / `ui-plugin-navigation` / `migrate-workflows` / `run-workflow`** | `C:\Users\27705\.gemini\antigravity\builtin\skills\...` | 插件打包管理与旧版工作流迁移工具 | **【按需加载】**：仅在用户明确提出插件打包或工作流迁移需求时加载 |

---

### 第六类：非 Web 原生跨端专用类 (Out-of-Scope Native Skills - 本项目强制静默隔离)
> **熵管理隔离声明**：以下 2 个全局技能面向移动端 React Native / Expo 与 Apple Swift 原生开发，与本项目（`Vue 3 + FastAPI + MySQL` Web 全栈架构）技术栈无关。为防止上下文污染，**在本项目全周期内标记为 `[DO_NOT_LOAD]`**：
- `animate-expo` (`C:\Users\27705\.gemini\config\skills\animate-expo\SKILL.md`) — React Native / Expo 专用，本项目不加载。
- `write-swift` (`C:\Users\27705\.gemini\config\skills\write-swift\SKILL.md`) — Swift 6 / iOS 原生开发专用，本项目不加载。

---

## 三、 研发阶段 -> Skills 按需加载速查路由表 (Stage-to-Skill Routing Cheat Sheet)

为确保 AI Agent 在进入不同研发阶段时精准按需唤醒对应技能，执行以下路由法则：

1. **当进入【阶段 2：后端 SQLAlchemy 2.0 ORM 建模与 MySQL 建表】时**：
   - 加载项目技能：`Skill 01 (sqlalchemy_orm_with_comment)` + `@docs/db_schema.md`。
2. **当进入【阶段 2/3：FastAPI 5 套 CRUD 接口、MCP 工具与 5 大 LangGraph 智能体编排】时**：
   - 加载项目技能：`Skill 02 (fastapi_restful_crud_router)`、`Skill 03 (main_to_high_value_split_code)`、`Skill 04 (patient_and_user_privacy_desensitize)`、`Skill 05 (workflow_6w_trace_logger)` + `@docs/api_spec.md`。
3. **当进入【阶段 4：前端 `frontend/` 生产级界面设计、组件精雕与四联单据打印】时（严禁抄袭 `docs/design/` 简易线框样式）**：
   - **第一步（设计基座与视觉规范）**：按需加载全局技能 **`emil-design-eng`** + **`apple-design`** + **`pick-ui-library`**，建立现代、通透、克制的亮暗自适应医疗工作台设计系统；
   - **第二步（流式智能体抽屉与节点动效）**：按需加载全局技能 **`emil-apple-design`** + **`animate`** + **`ask-sonner`**，实现丝滑的 5 大智能体对话舱、LangGraph 节点实时高亮与操作反馈；
   - **第三步（法定单据四联打印与极端数据抗压）**：加载项目技能 **`Skill 06 (medical_voucher_print_engine)`** + 全局技能 **`break-ui`** + **`animation-performance`**，检验超长器械名称与高密度表格下的排版稳定性与 60fps 流畅度。
4. **当进入【阶段 5：Playwright 全链路回环验证與 5 分钟演讲逐字稿 `.docx` 交付】时**：
   - 运行 `node tests/harness/runner.js` 执行自动化验证；
   - 按需加载全局技能 **`minimax-docx`** 生成排版精美的项目路演 5 分钟演讲逐字稿与项目验收报告 Word 文档。

---

## 四、 反馈循环自我迭代演进日志 (Feedback Loop Evolution Log)

| 迭代时间 | 触发来源 (探针/阶段) | 捕获的潜在风险或缺陷 | 自我进化沉淀动作 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| `2026-11-02 10:35` | 业务需求审查反馈 | 早期设计未区分主库房下主科室（设备科/耗材科）归口及普通/高值分流规则 | 新增 `Skill 03: main_to_high_value_split_code` 与主科室定向路由校验规范 | `[ACTIVE]` |
| `2026-11-02 11:14` | 数据库可维护性反馈 | 传统裸 SQL 难以迁移且大模型 MCP 无法理解无注释字段含义 | 新增 `Skill 01: sqlalchemy_orm_with_comment`，在 `guardrails.js` 中植入 ORM `comment` 静态扫描 | `[ACTIVE]` |
| `2026-11-02 11:46` | Harness 循环机制自检 | 需确保源码无 Emoji、函数注释完备且异常自动反哺技能库 | 建立 `tests/harness/guardrails.js` 自动扫描器并与 `SKILL.md` 形成闭环联动 | `[ACTIVE]` |
| `2026-11-02 12:10` | 原型与生产样式隔离及全局 Skills 治理 | 需防止将 `docs/design/*.html` 功能线框图样式误作最终前端生产样式，并需将全局 26 个 Skills 纳入 Harness 按需路由 | 在 `SKILL.md` 第二、三章建立全局 26 个 Skills 的 6 大分类矩阵与阶段按需加载路由表，明确生产前端强制加载 `emil-design-eng`、`apple-design`、`animate`、`break-ui` 等高阶设计技能 | `[ACTIVE]` |
| `2026-11-02 19:15` | `/grill-me` 业务深度对齐与权限解耦 | 全院业务单据需支持填单提交与外层二次确认提交两阶段防误触闭环，且高值退货与科室期初数据确认后永久不可逆；权限需支持按具体账号独立开关 8 项动作 | 新增 `Skill 07: two_step_confirm_state_machine` 与 `Skill 08: decoupled_8_action_rbac`，并在扩展 ORM 与服务层 100% 落地 | `[ACTIVE]` |
| `2026-11-03 17:20` | 用户多模块全业务实操反馈排查 | ① 选品组件与消费端字段名(spec_code/product_code)不一致导致多选去重误杀；② 仓库删除500因漏导模型；③ 前端空数组回退假数据掩盖签收状态并阻断二次操作；④ 仓库与盘点缺乏主从树与两层标准 | 新增 `Skill 09: select_dict_contract_consistency`、`Skill 10: two_tier_stocktake_and_wh_tree`、`Skill 11: no_mock_fallback_on_empty` 与 `Skill 12: orm_import_guard`，并在前后端全面落地 | `[ACTIVE]` |
