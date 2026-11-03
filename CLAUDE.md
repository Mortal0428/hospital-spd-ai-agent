# CLAUDE.md

本文件为【医院医疗物资全链路管理系统（SPD + 多智能体协同）】的跨平台标准工程指令与架构约束基线（承载 **Harness 组件① 上下文工程入口** 与 **组件④ 架构约束硬护栏**）。

---

## 1. 项目总览与技术栈基线 (Project Overview & Tech Stack)

- **业务定位**：面向医院信息科（系统管理员）、职能管理科室（耗材科、设备科、财务科）与临床各科室（二级库人员）的医疗物资全生命周期管理系统，涵盖产品字典双维分类、主库全部物资管理与按需分发、高值耗材一物一码专仓、临床二级库管理、6W 全流程流转日志、统计查询、标准医疗单据打印及 5 大业务智能体。
- **技术栈架构**：
  - **前端 (`frontend/`)**：Vue 3 + TypeScript + Element Plus + Vite + Pinia
  - **后端 (`backend/`)**：FastAPI + Python 3.13 + Pydantic V2 + SQLAlchemy 2.0 ORM + Alembic
  - **数据存储**：本地 MySQL 8.0 (`medical_spd_system`) + 本地 Redis 缓存 + 本地 Chroma 向量数据库
  - **智能体与大模型**：LangChain + LangGraph + MCP (Model Context Protocol) + 本地 Ollama / 云端小米 MiMo 接口 + 可选 Coze 智能体协同
  - **自动化验证 (`tests/`)**：Playwright 持久化无锁浏览器测试台架

---

## 2. 本地宿主环境与常用命令 (Environment & Commands)

- **Python 解释器路径**：`E:\python\python.exe` (Python 3.13.9)
- **Ollama 运行路径**：`E:\Ollam\ollama.exe`
- **本地服务名称**：MySQL 服务名 `MySQL80`；Redis 服务名 `redis`
- **常用开发与验证指令**：
  ```bash
  # 运行 Harness 工程规范与 Playwright 浏览器闭环自检
  node tests/harness/runner.js

  # 启动后端 FastAPI 服务 (位于 backend/ 目录)
  E:\python\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

  # 启动前端 Vite 开发服务 (位于 frontend/ 目录)
  npm run dev
  ```

---

## 3. 全局工程目录拓扑规范 (Directory Topology & Isolation)

所有新建与重构文件必须严格遵循物理目录隔离规范，严禁在项目根目录随意散落业务源码、测试脚本或临时文件：

1. **`frontend/`（前端目录）**：集中存放所有前端源码（视图页面、UI 组件、Pinia 状态管理、路由、CSS 变量及静态资源），严禁混入后端逻辑。
2. **`backend/`（后端目录）**：集中存放所有后端源码（FastAPI 路由控制器、业务服务层、SQLAlchemy 2.0 ORM 模型、MCP 工具集、LangGraph 智能体工作流与 Chroma RAG 模块）。
3. **`tests/`（测试与运行台目录）**：集中存放 Harness 闭环运行器（`tests/harness/`）、Playwright 端到端测试脚本（`tests/e2e/`）及带时间戳的实机验证截图归档（`tests/screenshots/`）。
4. **`plans/`（持久化记忆与计划目录）**：集中存放带精确时间戳的研发计划与进度台账（格式：`plans/[YYYY-MM-DD_HH-MM-SS]_[TASK_IDENTIFIER].md`）；已完成或过期的历史文档统一降权归档至 `plans/archive/`。
5. **`docs/`（业务与数据契约目录）**：集中存放供按需渐进加载的业务需求、ORM 数据库模型契约与接口规范文档。其中 `docs/design/*.html` 仅作为产品经理（PM）确认业务流转与功能模块的交互线框图（Wireframe），**严禁将其简易线框样式直接照搬至 `frontend/` 生产代码中**；真正开发 `frontend/` 生产界面时必须按 `@SKILL.md` 规定按需加载全局前端精雕与动效 Skills。

---

## 4. 核心工程原则与三方体验协同 (Engineering Principles)

### 4.1 四维工程思维
- **系统思维**：从全局架构、目录拓扑、模块边界与数据流向深入到具体函数实现，评估变更的涟漪效应。
- **辩证思维**：权衡多种技术路径的利弊（性能 vs. 可维护性、理论优雅 vs. 落地成本）。
- **创新思维**：在受限条件下寻求更优的算法、架构解耦或交互实现方案。
- **批判性思维**：从边界条件、异常捕获、状态同步与跨环境兼容性角度审视方案。

### 4.2 三方体验协同与非破坏性迭代铁律
1. **用户体验（UX）**：界面交互保持现代、通透、克制的视觉质感；响应迅速、过渡自然、亮暗主题无缝自适应；严禁因代码迭代导致存量交互退化、布局偏移或视觉割裂。
2. **开发者体验（DX）**：物理目录清晰分明、模块高内聚低耦合、命名语义化；所有函数与数据库字段均具备完整的标准化中文注释；代码易于阅读、调试与二次扩展。
3. **AI 代理体验（AX）**：保持可预测的目录拓扑、显式的类型/接口契约、结构化的时间戳计划文档与高信噪比日志，确保跨轮次检索与增量迭代时零幻觉、零上下文污染。
4. **存量保护与零回归底线**：迭代时优先采用增量扩展（符合开闭原则 OCP 与单一职责原则 SRP）而非破坏性重写；严格保障存量 API 签名、组件 Props 与全局状态契约的向后兼容性，严禁在实际写入的代码中留下未实现的 `TODO` 占位符或残缺逻辑。

---

## 5. 代码质量、数据库与 UI 全栈工程红线 (Strict Guardrails)

1. **语言与全域禁用 Emoji 铁律**：
   - 所有常规分析、沟通与注释统一使用**简体中文**；代码块、文件路径及 Git 提交规范保持标准英文格式。
   - **全域禁用 Emoji**：无论在日常响应、前端界面代码（HTML/Vue 模板、CSS `content`、按钮、空状态、通知提示）、代码注释、日志还是 Git 提交信息中，**绝对禁止输出任何 Emoji 表情符号**。
2. **函数级标准化中文四要素注释（强制 100% 覆盖）**：
   - 所有新增或修改的函数/方法必须编写清晰的中文文档注释，明确包含以下四要素：
     - `@param`：入参名称、类型及业务含义
     - `@returns`：返回值类型及数据结构说明
     - `@route`：若为接口层/前端路由函数，注明绑定的 HTTP 方法与路由路径；纯内部函数注明所属模块调用链路
     - `@throws`：可能触发的异常场景、边界条件及错误兜底处理方式
3. **数据库 SQLAlchemy 2.0 ORM 映射与 100% `comment` 注释铁律**：
   - 严禁手写无注释裸 SQL 脚本建表，必须通过 `backend/app/models/` 下的 SQLAlchemy 2.0 声明式 ORM 模型（`DeclarativeBase`、`Mapped`、`mapped_column`）映射并同步至 MySQL 8.0；
   - **表级注释**：每个 ORM 类必须声明 `__table_args__ = {"comment": "表中文业务说明"}`；
   - **字段级注释**：每个 `mapped_column(...)` 必须显式包含 `comment="字段中文名 + 业务规则与枚举值说明"`，赋能数据库自解释与大模型 MCP 工具精准查询。
4. **UI 矢量图标规范（强制原生组件或标准内联 SVG）**：
   - 优先使用项目已集成的 Element Plus 原生图标组件；若无现成图标组件，必须使用精简、语义化的内联 `<svg>` 绘制。
   - 内联 SVG 必须具备标准的 `viewBox="0 0 24 24"`，强制使用 `fill="currentColor"` 或 `stroke="currentColor"` 绑定颜色，设置协调的 `stroke-width`、`stroke-linecap="round"` 与 `stroke-linejoin="round"`，自动跟随父级文本颜色与亮/暗主题平滑切换。
5. **色彩防硬编码与现代克制审美**：
   - 严禁将字体颜色、背景色、边框色、阴影色等视觉属性进行绝对硬编码（如直接写死 `#FFFFFF` 或 `#000000`）；必须严格复用 CSS 变量与 Design Tokens，确保深浅色模式高度统一。
   - 保持干净、通透、克制的现代设计质感（合理留白、细腻半透明毛玻璃、精致微边框与自然过渡），拒绝刺眼高饱和渐变或廉价的 AI 发光装饰。
6. **交互健壮性与生命周期防泄漏**：
   - **高频操作防护**：对按钮、Tab 切换、折叠面板等高频交互元素添加 `user-select: none` 防止双击误选文字；对异步提交或重计算操作实施防抖/节流或 Loading 锁。
   - **状态隔离与生命周期清理**：确保多标签页/多视图切换时状态互不污染；所有定时器、全局监听器、`ResizeObserver`、图表实例必须在组件卸载时完整销毁回收。
7. **医疗合规安全与 Playwright 回环验证红线**：
   - 患者隐私字段（身份证、手机号、姓名）必须执行脱敏展示；过期批次（`EXPIRED`）与召回批次（`RECALLED`）必须在接口层硬性阻断；禁止硬编码数据库密码或大模型 API Key。
   - 涉及页面交互、视觉变更或前后端联调的代码完成后，必须运行 Playwright 自动化脚本校验无 Console Error / Uncaught PageError，并将带时间戳的实机截图归档至 `tests/screenshots/`。

---

## 6. 渐进式上下文披露索引 (Progressive Context Disclosure)

开发具体模块时按需加载对应规格文档，避免一次性全量灌入上下文：

- **角色专业化分工与 5 大业务智能体定义**：[`@AGENTS.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/AGENTS.md)
- **项目专属技能库、全局 26 个 Skills 分类图谱与按需渐进加载路由矩阵**：[`@SKILL.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/SKILL.md)
  - *前端生产界面设计必载技能*：`emil-design-eng`、`apple-design`、`emil-apple-design`、`prototype`、`pick-ui-library`、`ask-sonner`、`mobile-native`
  - *前端动效与 60fps 性能优化必载技能*：`animate`、`animation-performance`、`find-animation-opportunities`、`improve-animations`、`review-animations`
  - *前端极限数据压测与浏览器验证必载技能*：`break-ui`、`ego-browser`
  - *产品规划与最终 Word 演讲逐字稿交付必载技能*：`edu-pm-workflow`、`minimax-docx`、`generative_ui`
- **三级人员权限、PM 六大业务规则、5 套 CRUD 与智能体流程图**：[`@docs/requirements.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/docs/requirements.md)
- **SQLAlchemy 2.0 ORM 模型设计与全字段 `comment` 字典**：[`@docs/db_schema.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/docs/db_schema.md)
- **FastAPI RESTful 接口规范与大模型 `.env` 可插拔配置契约**：[`@docs/api_spec.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/docs/api_spec.md)
- **项目总体计划书与全周期进度记忆台账**：[`@plans/2026-11-02_10-41-00_master_project_plan_and_confirmed_baseline.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/plans/2026-11-02_10-41-00_master_project_plan_and_confirmed_baseline.md)
