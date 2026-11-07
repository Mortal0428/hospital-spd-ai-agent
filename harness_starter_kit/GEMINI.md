# GEMINI.md - 核心交付红线与防错契约 (Zero-Tolerance Rules)

> 本文件是所有参与工程开发的 AI Agent 必须 100% 遵守的核心契约（承载 **Harness 组件① 上下文工程统一入口** 与 **组件④ 架构硬约束**）。任何违反本契约的代码变更、交互输出或提交，均视为不可接受的工程违规，将被本地 Harness 护栏与自动化测试直接熔断阻断。

---

## 铁律 1：全域零 Emoji 绝对红线 (Zero Emoji Law)
1. **全场景禁用**：严禁在前端代码模板（Vue/React/HTML）、样式（CSS `content`）、对话响应文本、中文注释、系统日志、自动化 Mock 数据、测试断言及 Git Commit 信息中输出任何 Emoji 表情符号（如火箭、包裹、灯泡、勾叉、笑脸等 Unicode 字符）；
2. **图标工程规范**：前端视觉图标必须 100% 采用项目已集成的原生 UI 组件库图标（如 Element Plus、Lucide、Ant Design），或使用内联精简矢量 `<svg>`；
3. **SVG 格式标准**：内联 SVG 必须显式声明 `viewBox="0 0 24 24"`，且必须使用 `fill="currentColor"` 或 `stroke="currentColor"` 绑定颜色，确保自动跟随父级文字颜色与亮/暗色主题平滑过渡，严禁硬编码颜色值。

---

## 铁律 2：零敏感凭证与环境变量隔离铁律 (Zero Hardcoded Secrets Law)
1. **严禁明文落地**：严禁在业务源码、类属性默认值（如 `DEFAULT_APP_SECRET`）、配置文件默认参数（如 `config.py`）、测试用例脚本或研发计划（`plans/`）文档中硬编码任何真实的 API Key、Token、Password 或 Secret；
2. **支持匹配规则**：包括但不限于 OpenAI 格式 Key（`sk-...`）、LangSmith Token（`lsv2_pt_...`）、Coze / GitHub PAT（`pat_...` / `ghp_...`）、飞书 App Secret 等常见敏感凭证；
3. **统一读取范式**：所有敏感参数必须通过系统环境变量（如 `os.environ.get("KEY", "")` 或 `process.env.KEY`）安全读取；
4. **开源安全基线**：真实密钥仅允许保存在本地被 `.gitignore` 排除的 `.env` 文件中，代码仓库只提交脱敏的 `.env.example` 模版，杜绝推送时被 GitHub / Gitee 的 Secret Protection 阻断；
5. **本地缓存防提交**：所有运行期生成的无头浏览器配置缓存（如 `.automation_profile/`）、本地向量数据库及临时数据库文件（如 `*.db`, `*.sqlite3`）必须严格纳入 `.gitignore` 排除名单，严禁提交到远程仓库。

---

## 铁律 3：真大模型推理与动态工具调度铁律 (Genuine AI Reasoning Law)
1. **杜绝形式主义**：严禁为了迎合测试通过率而编写死关键词匹配（Regex Router）、静态固定问答或假数据 Mock 冒充智能体；
2. **状态机规范**：所有复杂业务智能体必须通过 LangGraph `StateGraph` 或确定性拓扑状态机编排，由大模型根据自然语言上下文自主分析意图、抽取结构化参数，并安全调度底层的标准工具（MCP 协议工具或业务数据库工具）；
3. **透明化展示**：智能体交互必须支持打字机流式渲染，并将中间思考链路（Reasoning Trace）与工具调用入参结构化呈现给用户；
4. **高韧性异常熔断**：在调用本地 Embedding、大模型或外部工具发生网络波动或超时（如超出 5 秒）时，必须具备秒级兜底熔断机制（如特征哈希向量降级或友好的错误卡片返回），严禁让主线程发生非预期的假死或请求挂起。

---

## 铁律 4：全栈物理级权限解耦与数据隔离铁律 (Physical Authorization Law)
1. **拒绝假防护**：严禁仅靠前端 `v-if` 或隐藏按钮做“视觉伪隔离”；
2. **端到端鉴权链条**：权限校验必须穿透全链路：“前端路由守卫 -> 页面按钮级禁用 (`v-permission`) -> 请求头附带业务凭据与作用域 -> 后端接口依赖注入鉴权 -> 数据库查询物理级隔离”；
3. **作用域与上下文隔离**：涉及多租户、多科室、多库房切换时，切换操作必须同步重置本地缓存与数据源，后端接口必须强制绑定当前授权的作用域编码，严防跨域越权与数据串岗；
4. **会话切换数据清零**：在执行角色切换或重新登录时，必须强制清空上一角色的全局 Pinia/Redux 状态、本地 Token 缓存与分页器上下文（重置为第 1 页），确保新角色的数据视图纯净无污染。

---

## 铁律 5：存量保护与零破坏性增量扩展 (OCP & Zero Regression Law)
1. **开闭原则（OCP）**：所有新功能必须采用增量扩展方式接入，严格保障存量 API 接口签名、组件 Props 契约、数据库历史表结构的向后兼容性；
2. **零退化底线**：严禁在迭代新模块时以“顺手优化”、“代码重构”为由修改无关的存量代码逻辑，绝不破坏任何已验收的存量功能链路；
3. **服务进程平替与端口防冲突**：在本地重启后端（如 Uvicorn 8000）或前端（如 Vite 5173）服务前，必须先优雅终止旧的孤儿进程，确保网络端口彻底释放，严禁出现 `EADDRINUSE` 端口占用引发的假启动。

---

## 铁律 6：严格状态机模式与无授权禁止写码 (Strict RIPER-5 State Machine)
1. **四阶段严格转换**：AI Agent 必须严格遵循 `[MODE: RESEARCH]`（只读摸底）-> `[MODE: INNOVATE]`（方案探讨）-> `[MODE: PLAN]`（清单归档）-> `[MODE: EXECUTE]`（获批执行）；
2. **权限硬门禁**：在 `RESEARCH`、`INNOVATE` 和 `PLAN` 模式下，Agent 仅具备只读及计划文档归档权限，**严禁调用任何业务文件写入工具提前修改代码**；
3. **授权激活**：仅当用户明确发出批准执行的指令后，方可激活 `[MODE: EXECUTE]` 进入编码实施阶段；遇到计划外技术阻碍时必须主动熔断退回 `PLAN`；
4. **长效记忆与时间戳归档**：所有实施计划必须落盘到 `plans/` 下带精确时间戳的文件中，实施完毕并验证通过后，将历史阶段计划归档至 `plans/archive/`，保持工作区轻量可控。

---

## 7. 渐进式上下文披露索引 (Progressive Context Disclosure Index)

为了防止单次会话塞入过多上下文导致大模型遗忘或产生幻觉，AI Agent 在执行具体任务时，必须按照以下索引**按需读取对应模块的规格文档**：

| 研发场景/任务类型 | 必须渐进读取的对应规范文档路径 | 核心获取信息 |
| :--- | :--- | :--- |
| **任务分工与角色协同** | [`AGENTS.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/AGENTS.md) | 5 大研发专项子 Agent 职责范围与禁止越权红线 |
| **代码审查与反模式防错** | [`HARNESS_PITFALLS_AND_LESSONS.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/HARNESS_PITFALLS_AND_LESSONS.md) | 8 大高危反模式踩坑总结与防御军规 |
| **复杂工程技能与反馈沉淀** | [`SKILL.md`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/SKILL.md) | 模块化可重用技能库定义与自进化沉淀范式 |
| **业务需求与用户故事对齐** | `docs/requirements.md` (参考 `templates/docs/requirements.sample.md`) | 核心业务流转、角色用例与功能清单 |
| **数据库建模与 ORM 契约** | `docs/db_schema.md` (参考 `templates/docs/db_schema.sample.md`) | 实体映射、外键关联与 100% 表级/字段级中文 comment |
| **RESTful 接口开发与联调** | `docs/api_spec.md` (参考 `templates/docs/api_spec.sample.md`) | HTTP 路由方法、Pydantic 入参出参结构与统一响应体 |
| **时间戳实施计划制定** | `plans/` (参考 `templates/plans/TASK_PLAN.sample.md`) | 原子行动清单、可行性指标与 Playwright 截屏验证方案 |
| **历史计划归档与熵管理** | `plans/archive/` (参考 `templates/plans/archive/README.md`) | 历史计划降权归档台账与上下文瘦身准则 |
| **自动化测试与浏览器自检** | [`core/runner.js`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/core/runner.js) 与 [`core/guardrails.js`](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/harness_starter_kit/core/guardrails.js) | 规范断言、静态合规扫描与 Playwright 无锁截屏 |
