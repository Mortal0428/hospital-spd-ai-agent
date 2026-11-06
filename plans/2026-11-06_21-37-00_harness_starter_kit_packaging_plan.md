# 通用化 AI 研发质量护栏套件 (harness_starter_kit) 独立解耦与打包计划书

## 1. 计划归档与变更范围

- 计划文档路径：`plans/2026-11-06_21-37-00_harness_starter_kit_packaging_plan.md`
- 记录时间戳：`2026-11-06 21:37:00`
- 目标目录拓扑：`harness_starter_kit/`
- 拟生成的目标文件清单：
  1. `harness_starter_kit/README.md`：脚手架全景说明、在新项目中 3 分钟引入与配置指南；
  2. `harness_starter_kit/GEMINI.md`：通用 AI 代理 6 大核心执行铁律与防错契约（零 Emoji、零硬编码密钥、真智能体、物理鉴权隔离、零回归、严格状态机）；
  3. `harness_starter_kit/AGENTS.md`：5 大研发子 Agent 专业化分工与契约模版（Orchestrator, DB & ORM, Backend & AI, Frontend UI, QA & Harness）；
  4. `harness_starter_kit/HARNESS_PITFALLS_AND_LESSONS.md`：全栈防踩坑高危反模式与防退化军规手册；
  5. `harness_starter_kit/package.json`：独立 NPM 依赖、启动脚本与命令映射；
  6. `harness_starter_kit/config/harness.config.js`：通用配置中心，支持外部灵活覆盖目标目录、开启/关闭指定扫描规则；
  7. `harness_starter_kit/core/guardrails.js`：合规扫描引擎（包含零 Emoji 扫描、API Key 敏感密钥扫描、ORM 100% 注释扫描、目录分层扫描）；
  8. `harness_starter_kit/core/browser.js`：自适应无锁持久化 Playwright 浏览器驱动，解决环境端口冲突与用户配置文件占用；
  9. `harness_starter_kit/core/runner.js`：主校验执行引擎，执行规范校验、生成现代化暗亮色自适应自检视图，截取实机存根并拦截 Console Error；
  10. `harness_starter_kit/templates/.env.example`：通用环境变量脱敏模版；
  11. `harness_starter_kit/templates/pre-commit.sample`：Git Pre-commit 钩子示例，在提交时自动运行 Guardrails。

---

## 2. 核心评估指标

- **可行性与把握度评估**：`把握度：100%`。当前系统中所有底层脚本均已在生产级项目中多次实操检验，解耦为可配置模块不涉及复杂依赖，成功把握度极高。
- **存量功能与三方体验影响分析**：
  - **用户体验（UX）**：所有生成的报告与视图延续高质感现代设计，CSS 变量自适应，全域禁用 Emoji；
  - **开发者体验（DX）**：结构清晰明了，通过 `harness.config.js` 即可在新项目中一键调整路径，无需改动核心运行代码；
  - **AI 代理体验（AX）**：提供显式契约、标准规范清单，新 Agent 入驻新项目时能快速理解护栏边界；
  - **存量功能保护**：所有新增文件均放置于全新的独立目录 `harness_starter_kit/` 下，对当前医疗物资主工程的前后端业务、测试与生产运行零侵入、零破坏。
- **回环测试与自检方案**：
  - 在 `harness_starter_kit/` 生成完毕后，直接调用 `node harness_starter_kit/core/runner.js` 针对该 starter kit 进行自测；
  - 验证其 Guardrails 能够自检通过，且 Playwright 成功调起浏览器生成自检核验截图 `harness_starter_kit/screenshots/starter_kit_verify.png`。

---

## 3. 技术规范与模块解耦设计

### 3.1 规则控制中枢设计 (`harness.config.js`)
通过配置化抽离，让未来所有新项目可定制：
```javascript
module.exports = {
  projectRoot: path.resolve(__dirname, '../..'),
  guardrails: {
    noEmoji: true,
    noSecrets: true,
    ormComments: false, // 仅在含数据库项目中开启
    architectureIsolation: true
  },
  directories: {
    frontend: 'frontend',
    backend: 'backend',
    tests: 'tests',
    plans: 'plans',
    screenshots: 'tests/screenshots'
  }
};
```

### 3.2 敏感凭证扫描规则强化 (`guardrails.js`)
集成正向扫描规则：
- `sk-[a-zA-Z0-9]{20,}` (OpenAI / 兼容平台 API Key)
- `lsv2_pt_[a-zA-Z0-9_]{20,}` (LangSmith Token)
- `pat_[a-zA-Z0-9]{20,}` (Coze / GitHub 个人访问令牌)
- `ghp_[a-zA-Z0-9]{20,}` (GitHub Token)
- 飞书 App Secret / 钉钉 Secret 等模式识别。

### 3.3 注释与代码规范
- 所有 JS / Markdown 文件 100% 严禁出现 Emoji 表情符号；
- 所有 JS 函数编写规范的 JSDoc 中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。

---

## 4. 原子实施清单

```markdown
实施清单：
1. [已完成] [harness_starter_kit/] 创建目录拓扑架构 (config/, core/, templates/, screenshots/)
2. [已完成] [harness_starter_kit/] 编写 GEMINI.md 核心守则契约与 AGENTS.md 研发子 Agent 分工契约
3. [已完成] [harness_starter_kit/] 编写 HARNESS_PITFALLS_AND_LESSONS.md 军规手册与 README.md 使用指南
4. [已完成] [harness_starter_kit/] 编写 config/harness.config.js 通用配置文件与 package.json
5. [已完成] [harness_starter_kit/] 编写 core/browser.js 无锁持久化 Playwright 驱动模块
6. [已完成] [harness_starter_kit/] 编写 core/guardrails.js 规则静态扫描引擎 (强化零密钥扫描)
7. [已完成] [harness_starter_kit/] 编写 core/runner.js 核心回环校验执行引擎
8. [已完成] [harness_starter_kit/] 编写 templates/.env.example 与 templates/pre-commit.sample 模版文件
9. [已完成] [harness_starter_kit/] 执行 node harness_starter_kit/core/runner.js 自校验并通过 (生成 screenshots/starter_kit_verify.png)
10. [已完成] [git/] 确认工作区与自检状态，输出交付汇报
```
