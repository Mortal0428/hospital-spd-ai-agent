# Harness Starter Kit 深度复刻本地 RIPER-5 精髓与全栈工程红线计划书

## 1. 计划归档与变更范围

- 计划文档路径：`plans/2026-11-07_10-24-00_replicate_full_riper5_essence_to_harness_plan.md`
- 记录时间戳：`2026-11-07 10:24:00`
- 目标目录：`harness_starter_kit/`
- 变更文件清单：
  1. `harness_starter_kit/GEMINI.md`：完整复刻本地增强型 RIPER-5 执行协议、元指令、四维思维、三方体验协同、四大物理目录拓扑、执行红线（函数四要素注释、SVG 图标规范、色彩防硬编码、克制审美、防泄漏）、标准执行汇报格式模版，并融入本次实战经验（零明文密钥、真智能体 MCP 调度、端口平替防冲突、会话切换清零、渐进式披露索引）；
  2. `harness_starter_kit/CLAUDE.md`：以相同精髓与标准规范，对齐为通用的跨平台 Claude Code / Claude Desktop 架构基线；
  3. `harness_starter_kit/config/harness.config.js`：保持基准核验清单与运行时配置一致。

---

## 2. 核心评估指标

- **可行性与把握度评估**：`把握度：100%`。本次任务是将成熟运行且深度验证的日常执行规范完整复刻至套件中，并剔除多余套话，保证执行力高度聚焦。
- **存量功能与三方体验影响分析**：
  - **用户体验（UX）**：规范强制要求克制审美、亮暗主题自适应、全域禁用 Emoji，UI 质感生产级；
  - **开发者体验（DX）**：新项目无论是使用 Gemini 还是 Claude，均有一比一复刻的高规格工程守则，函数注释、目录拓扑、状态机流转零歧义；
  - **AI 代理体验（AX）与渐进式特性**：保持结构化、可预测的元指令约束，配合末尾的渐进式披露索引，避免上下文污染；
  - **存量功能保护**：仅更新 `harness_starter_kit/` 内部的规范文档与指引，对当前医疗物资系统主业务代码零侵入、零破坏。
- **Playwright 自动化回环自检方案**：
  - 更新完成后，运行 `node harness_starter_kit/core/runner.js`；
  - 自动运行静态合规扫描（零 Emoji、零明文密钥），并通过 Playwright 持久化浏览器自检渲染与截屏归档。

---

## 3. 技术规范与复刻细节大纲

### 3.1 核心复刻章节架构 (GEMINI.md & CLAUDE.md)
1. **角色定义与核心背景**：防范 AI 急躁乱改，严格落实增强型 RIPER-5；
2. **语言与纯净输出基准**：简体中文交互、标准英文标签、全域禁用 Emoji；
3. **元指令：模式声明与工具权限铁律**：
   - 响应首行强制声明 `[MODE: MODE_NAME]`；
   - 默认初始状态为 `[MODE: RESEARCH]`；
   - 严禁未经授权自行跨模式跳转，遇到阻碍主动退回 `[MODE: PLAN]`；
4. **四维工程思维与三方体验协同**：
   - 系统思维、辩证思维、创新思维、批判性思维；
   - UX（用户体验）、DX（开发者体验）、AX（代理体验）、存量保护与零回归底线；
5. **全局工程目录拓扑规范（强制物理隔离）**：
   - `frontend/`, `backend/`, `tests/`, `plans/`, `docs/`；
6. **增强型 RIPER-5 四大模式规范**：
   - `[MODE: RESEARCH]`（只读摸底、依赖核验、识别技术债、严禁输出修改代码）
   - `[MODE: INNOVATE]`（只读探讨、2-3 种方案比选、四维权衡分析、寻求用户反馈）
   - `[MODE: PLAN]`（只读与计划归档、四大强制要素：时间戳路径、把握度/三方体验/Playwright 截图评估、函数与 UI 精确签名、原子实施清单）
   - `[MODE: EXECUTE]`（获批进入、100% 忠实执行、十项全栈代码质量红线）
7. **十项全栈工程质量红线**：
   - 目录整洁与物理隔离
   - 高内聚低耦合与单一职责
   - 函数级标准化中文四要素注释（`@param`, `@returns`, `@route`, `@throws` 100% 覆盖）
   - UI 矢量图标铁律（严禁 Emoji，优先原生组件，次选语义化内联 `<svg>` 绑定 `currentColor`）
   - 色彩防硬编码与主题自适应（严禁绝对写死 `#FFFFFF` 或 `#000000`）
   - 现代克制审美（去 AI 廉价发光与高饱和堆砌）
   - 交互健壮性与生命周期防泄漏（`user-select: none`，防抖节流 Loading 锁，多视图状态隔离，卸载清理）
   - 零敏感凭证与环境变量隔离（`.env.example` 模版与静态扫描）
   - 服务进程平替与端口防冲突（重启前释放旧进程，防 `EADDRINUSE`）
   - 偏差熔断机制（遇阻立即停手并退回 PLAN）
8. **执行后标准进度汇报格式模版**（带时间戳、关联计划、目录修改分类、Playwright 截图、存量零破坏评估）；
9. **渐进式上下文披露索引**（按需加载 `AGENTS.md`, `SKILL.md`, `docs/`, `plans/archive/`）。

---

## 4. 原子实施清单

```markdown
实施清单：
1. [已完成] [harness_starter_kit/] 编写重构 harness_starter_kit/GEMINI.md，一比一深度复刻本地 RIPER-5 精髓、工程红线、汇报模版与实战防错军规
2. [已完成] [harness_starter_kit/] 编写对齐 harness_starter_kit/CLAUDE.md，保持跨平台双核规则一致性
3. [已完成] [harness_starter_kit/] 校验 config/harness.config.js 核验配置与路径映射
4. [已完成] [harness_starter_kit/] 执行 node harness_starter_kit/core/runner.js 实机回环自检，验证 Guardrails 与 Playwright 截屏 (100% 通过)
5. [已完成] [git/] 暂存提交并推送到 GitHub 远程仓库
6. [已完成] [report/] 输出完成报告与交付汇报
```
