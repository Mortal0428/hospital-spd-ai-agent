# Harness Starter Kit - AI 研发质量护栏与工程防退化套件

> 一套适用于任何全栈 Web 工程、Python 后端或大模型 AI 应用的**工业级研发质量护栏脚手架**。通过规则化约束、静态代码扫描（Guardrails）与 Playwright 真实浏览器回环验证（E2E Runner），彻底杜绝 AI 代理在开发过程中的急躁乱写、Emoji 泛滥、密钥泄露、伪鉴权以及破坏存量功能的坏味道。

---

## 一、为什么需要这套 Harness 脚手架？

在使用 AI 编码助手（如 Gemini、Claude、Cursor 等）进行中大型工程迭代时，AI 往往具有以下固有弊端：
1. **急躁与擅自重构**：未经充分摸底与规划，擅自大改存量代码，导致老功能无声息崩溃；
2. **生成惯性与装饰泛滥**：喜欢在前端界面、日志中无节制堆砌 Emoji 表情符号，破坏生产级 UI 质感；
3. **安全意识淡薄**：喜欢把各种 API Key、Token 直接硬编码在代码或测试脚本中，造成严重泄露；
4. **形式主义与伪隔离**：喜欢用简单的假数据 Mock 或前端 `v-if` 做表面文章，缺乏真正的全栈物理鉴权。

**Harness Starter Kit 就是用来给 AI 研发装上“安全带与刹车系统”的标准化护栏。**

---

## 二、Harness 六大组件核心特性 100% 对齐矩阵

本套件严格 100% 落实软件工程治理的 **Harness 六大核心特性**，开箱即用：

| Harness 核心特性 | 承载文件/模块 | 对应工程职能与落地机制 |
| :--- | :--- | :--- |
| **组件①：上下文工程与渐进式信息披露** | `GEMINI.md` / `CLAUDE.md`<br>`templates/docs/` | 建立统一入口与渐进式披露索引，避免单次会话 Token 过载，按需加载需求、数据库与 API 契约 |
| **组件②：研发子 Agent 专业化分工契约** | `AGENTS.md` | 单一职责原则（SRP），将研发划分为 Orchestrator, DB, Backend, Frontend, QA 5 大窄角色 |
| **组件③：持久化记忆与结构化进度台账** | `templates/plans/`<br>`TASK_PLAN.sample.md` | 带精确时间戳的实施计划与原子行动清单，作为 AI 跨轮次迭代的长效记忆基线 |
| **组件④：架构约束与静态合规硬护栏** | `core/guardrails.js`<br>`core/runner.js`<br>`core/browser.js` | 静态扫描（全域零 Emoji、零明文密钥、ORM 注释、目录隔离）+ Playwright 真实浏览器实机渲染自检 |
| **组件⑤：反馈循环与防错自进化技能库** | `SKILL.md`<br>`HARNESS_PITFALLS_AND_LESSONS.md` | 沉淀 8 大典型高危反模式踩坑军规，支持根据排错经验动态扩充可复用的通用工程技能库 |
| **组件⑥：工程熵管理与历史计划归档治理** | `templates/plans/archive/`<br>`archive/README.md` | 阶段性结案计划定期降权归档与工作区瘦身，防止无序增生导致的上下文污染 |

---

## 三、目录拓扑与核心组件

```
harness_starter_kit/
├── README.md                          # 本套件全景使用与接入指南
├── GEMINI.md                          # Gemini AI 代理核心执行铁律与防错契约 (组件①&④)
├── CLAUDE.md                          # Claude 跨平台标准指令与架构约束基线 (组件①&④)
├── AGENTS.md                          # 5 大研发子 Agent 专业化分工契约标准模版 (组件②)
├── SKILL.md                           # 全栈通用自进化技能库与按需路由规约 (组件①&⑤)
├── HARNESS_PITFALLS_AND_LESSONS.md    # 8 大全栈高危反模式与防退化军规手册 (组件⑤)
├── package.json                       # 独立 NPM 脚本与 Playwright 依赖定义
├── config/
│   └── harness.config.js              # 规则控制中枢（支持新项目自定义目录与开关）
├── core/
│   ├── runner.js                      # 质量自检引擎（规范断言、自检视图渲染与截图取证）
│   ├── guardrails.js                  # 静态合规扫描器（零 Emoji、零密钥、ORM 注释、目录隔离）
│   └── browser.js                     # 无锁持久化 Playwright 浏览器驱动
├── screenshots/
│   └── starter_kit_verify.png         # Playwright 实机回环自检生成的全息报告截图
└── templates/
    ├── .env.example                   # 通用环境变量脱敏模版
    ├── pre-commit.sample              # Git 提交前门禁 Hook 脚本
    ├── docs/                          # 渐进式业务与技术规范模版 (组件①)
    │   ├── requirements.sample.md     # 业务需求与角色用例模版
    │   ├── db_schema.sample.md        # 数据库 ORM 建模与 100% 注释契约模版
    │   └── api_spec.sample.md         # RESTful 接口与统一响应体模版
    └── plans/                         # 结构化计划与熵管理模版 (组件③&⑥)
        ├── TASK_PLAN.sample.md        # 带时间戳的原子实施计划样板
        └── archive/
            └── README.md              # 历史计划降权归档台账样板
```

---

## 四、在新项目中 3 分钟极速套用指南

### 第一步：将套件拷贝至新项目根目录
直接将 `harness_starter_kit` 文件夹拷贝到你新项目的根目录下（可重命名为 `harness`）。

### 第二步：根据新项目结构微调配置 (`config/harness.config.js`)
打开 `config/harness.config.js`，根据新项目的物理目录修改映射：
```javascript
module.exports = {
  // 指定项目根目录
  projectRoot: path.resolve(__dirname, '..'),

  // 按需开启/关闭规则
  guardrails: {
    noEmoji: true,              // 零 Emoji 扫描
    noSecrets: true,            // 零敏感密钥扫描
    ormComments: true,          // 若新项目含数据库则开启
    architectureIsolation: true // 物理目录隔离校验
  },

  // 映射新项目的实际目录
  directories: {
    frontend: 'frontend',
    backend: 'backend',
    tests: 'tests',
    plans: 'plans'
  }
};
```

### 第三步：按需建立业务契约与计划（渐进式信息披露）
- 将 `templates/docs/*.sample.md` 拷贝到新项目的 `docs/` 目录下，填入新项目的需求与表结构；
- 开发新功能时，基于 `templates/plans/TASK_PLAN.sample.md` 在 `plans/` 下创建带有时间戳的实施清单；
- 研发阶段完结后，将结案计划移动到 `plans/archive/` 进行熵管理归档。

### 第四步：安装依赖并运行自检
```bash
# 1. 切换至护栏套件目录
cd harness_starter_kit

# 2. 安装 Playwright 核心依赖
npm install

# 3. 运行静态规则扫描
npm run guardrails

# 4. 运行全链路回环自检并生成实机自检报告截图
npm test
```

---

## 五、Git Pre-commit 自动化挂载（可选）

若希望在本地执行 `git commit` 时由系统自动运行 Guardrails 静态检查：
```bash
# 在项目根目录下，将 sample 脚本写入 Git Hook
cp harness_starter_kit/templates/pre-commit.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
挂载后，一旦代码中出现未移除的 Emoji 或硬编码 API Key，Git 将直接拒绝提交并输出违规文件路径与行号。
