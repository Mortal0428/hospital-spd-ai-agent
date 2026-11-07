# CLAUDE.md

> 本文件为基于 AI 辅助研发的全栈软件工程跨平台标准指令与架构约束基线（承载 **Harness 组件① 上下文工程统一入口** 与 **组件④ 架构约束硬护栏**），适用于 Claude Code、Claude Desktop 及通用大模型代理工具。

---

## 1. 项目总览与技术栈基线 (Project Overview & Tech Stack)

在将本套件引入新工程后，请在此处简要说明新项目的技术选型：
- **前端应用**：Vue 3 / React + TypeScript + 现代组件库 + 状态管理
- **后端服务**：FastAPI / Flask / Spring Boot / Go Gin + 异步 RESTful API
- **数据持久化**：MySQL / PostgreSQL + 声明式 ORM + 缓存中间件
- **智能体与大模型**：LangChain / LangGraph / MCP (Model Context Protocol)
- **自动化测试**：Playwright 无锁持久化浏览器 + Harness 质量自检套件

---

## 2. 常用开发与验证指令 (Environment & Commands)

```bash
# 1. 运行 Harness 质量自检与 Playwright 浏览器闭环实机验证
node harness_starter_kit/core/runner.js

# 2. 仅运行代码静态规则扫描（零 Emoji + 零明文密钥）
npm run guardrails --prefix harness_starter_kit

# 3. 启动后端开发服务
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 4. 启动前端开发服务
npm run dev
```

---

## 3. 全局工程物理目录隔离拓扑 (Directory Topology & Isolation)

所有工程文件必须严格遵循物理目录隔离规范，严禁在项目根目录随意散落业务源码、测试脚本或临时文档：

1. **`frontend/`（前端目录）**：集中存放所有前端源码（视图页面、UI 组件、状态管理、前端路由、样式变量及静态资源），严禁混入后端业务逻辑。
2. **`backend/`（后端目录）**：集中存放所有后端源码（路由控制器、业务服务层、ORM 数据模型、中间件、MCP 工具与智能体工作流）。
3. **`tests/`（测试与自检目录）**：集中存放质量护栏引擎（`tests/harness/` 或 `harness_starter_kit/`）、Playwright 端到端脚本（`tests/e2e/`）及实机验证截图归档（`tests/screenshots/`）。
4. **`plans/`（长效记忆与计划目录）**：集中存放带精确时间戳的研发计划与进度台账（格式：`plans/[YYYY-MM-DD_HH-MM-SS]_[TASK].md`）；已完成的历史计划统一降权归档至 `plans/archive/`。
5. **`docs/`（业务需求与数据契约目录）**：集中存放供按需渐进加载的业务需求文档、ORM 数据库模型契约与接口规范文档。

---

## 4. 核心工程原则与三方体验协同 (Engineering Principles)

### 4.1 四维工程思维
- **系统思维**：从全局拓扑、模块边界与数据流向深入具体实现，严密评估改动的涟漪效应。
- **辩证思维**：权衡技术路径利弊（性能 vs. 可维护性、理论优雅 vs. 落地成本）。
- **创新思维**：在受限条件下寻求更优的算法、解耦机制或交互实现方案。
- **批判性思维**：从边界条件、异常捕获、并发锁、状态同步与跨平台兼容性角度审视方案。

### 4.2 三方体验协同与非破坏性迭代铁律
1. **用户体验（UX）**：界面交互保持现代、通透、克制的质感；过渡自然、亮暗主题无缝自适应；严禁因代码迭代导致存量交互退化或视觉割裂。
2. **开发者体验（DX）**：物理目录清晰分明、模块高内聚低耦合；所有函数与数据模型均具备完整的标准化中文注释；代码易于人类阅读与调试。
3. **AI 代理体验（AX）**：保持可预测的目录结构、显式的类型契约、时间戳计划与高信噪比日志，确保跨轮次协作时零幻觉、零上下文污染。
4. **存量保护与零回归底线**：增量迭代必须严格遵守开闭原则（OCP）与单一职责原则（SRP），保障存量 API 签名、组件 Props 与数据库向后兼容性，严禁留下未实现的 `TODO` 占位符。

---

## 5. 代码质量与工程红线 (Strict Guardrails)

1. **语言与全域禁用 Emoji 铁律**：
   - 所有常规分析、沟通与代码注释统一使用**简体中文**；代码块、文件路径与提交信息保持标准英文。
   - **全域禁用 Emoji**：无论在日常响应、前端界面代码（HTML/Vue/React 模板、CSS `content`、按钮、空状态、通知提示）、注释、日志还是 Git 提交信息中，**绝对禁止输出任何 Emoji 表情符号**。
2. **函数级标准化中文四要素注释（强制 100% 覆盖）**：
   - 所有新增或修改的方法必须编写清晰的中文四要素注释：
     - `@param`：入参名称、类型及业务含义
     - `@returns`：返回值类型及数据结构说明
     - `@route`：若为接口层/前端路由函数，注明绑定的 HTTP 方法与路由路径；纯内部函数注明所属模块调用链路
     - `@throws`：可能触发的异常场景、边界条件及错误兜底处理方式
3. **数据库 ORM 映射与 100% `comment` 注释铁律**：
   - 严禁手写无注释裸 SQL，必须通过声明式 ORM 模型映射；
   - 每个数据表必须包含表级业务中文说明；每一个字段必须显式声明中文 `comment` 注释，说明业务规则与状态枚举值。
4. **UI 矢量图标与防硬编码标准**：
   - 优先使用原生 UI 组件库图标，或使用内联精简矢量 `<svg>`（标准 `viewBox="0 0 24 24"` 并使用 `fill="currentColor"` 或 `stroke="currentColor"`）；
   - 严禁绝对硬编码字体颜色与背景色，必须严格复用 CSS 变量与 Design Tokens，确保深浅色模式平滑切换。
5. **零敏感凭证与环境变量隔离**：
   - 严禁在代码、配置文件默认值或测试脚本中硬编码 API Key 或 Secret；
   - 统一使用 `os.environ.get()` 或 `process.env` 读取，私钥仅保存在本地 `.env`，仓库只提交 `.env.example` 模版。
6. **服务进程平替与端口防冲突**：
   - 本地重启开发服务器前，必须先释放旧进程，避免 `EADDRINUSE` 端口占用；
7. **Playwright 真实浏览器回环验证**：
   - 核心链路修改后必须运行自动化测试，确保无 `console.error` 与 `pageerror` 报错，并保存实机截图。

---

## 6. 渐进式上下文披露索引 (Progressive Context Disclosure Index)

为避免一次性灌入全量上下文导致大模型遗忘，AI Agent 在执行具体任务时，必须按需索引读取对应文档：

- **研发角色分工与协作契约**：[`AGENTS.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/AGENTS.md)
- **高危反模式与防踩坑军规**：[`HARNESS_PITFALLS_AND_LESSONS.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/HARNESS_PITFALLS_AND_LESSONS.md)
- **自进化技能库定义与扩充**：[`SKILL.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/SKILL.md)
- **业务需求与用户故事定义**：`docs/requirements.md` (模版参考 `templates/docs/requirements.sample.md`)
- **数据表建模与 ORM 注释契约**：`docs/db_schema.md` (模版参考 `templates/docs/db_schema.sample.md`)
- **RESTful API 契约与统一响应**：`docs/api_spec.md` (模版参考 `templates/docs/api_spec.sample.md`)
- **时间戳实施清单与任务规划**：`plans/` (模版参考 `templates/plans/TASK_PLAN.sample.md`)
- **历史计划归档与熵管理治理**：`plans/archive/` (模版参考 `templates/plans/archive/README.md`)
- **自动化测试引擎与浏览器驱动**：[`core/runner.js`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/core/runner.js) 与 [`core/browser.js`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/core/browser.js)
