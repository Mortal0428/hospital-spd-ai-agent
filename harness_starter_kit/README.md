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

## 二、目录拓扑与核心组件

```
harness_starter_kit/
├── README.md                          # 本套件全景使用与接入指南
├── GEMINI.md                          # AI 代理必须 100% 遵守的 6 大核心执行铁律
├── AGENTS.md                          # 5 大研发子 Agent 专业化分工契约标准模版
├── HARNESS_PITFALLS_AND_LESSONS.md    # 8 大全栈高危反模式与防退化军规手册
├── package.json                       # 独立 NPM 脚本与 Playwright 依赖定义
├── config/
│   └── harness.config.js              # 规则控制中枢（支持新项目自定义目录与开关）
├── core/
│   ├── runner.js                      # 质量自检引擎（规范断言、自检视图渲染与截图取证）
│   ├── guardrails.js                  # 静态合规扫描器（零 Emoji、零密钥、ORM 注释、目录隔离）
│   └── browser.js                     # 无锁持久化 Playwright 浏览器驱动
└── templates/
    ├── .env.example                   # 通用环境变量脱敏模版
    └── pre-commit.sample              # Git 提交前门禁 Hook 脚本
```

---

## 三、在新项目中 3 分钟极速套用指南

### 第一步：将套件拷贝至新项目根目录
直接将 `harness_starter_kit` 文件夹拷贝到你新项目的根目录下（或重命名为 `harness`）。

### 第二步：根据新项目结构微调配置 (`config/harness.config.js`)
打开 `config/harness.config.js`，根据新项目的物理目录修改映射：
```javascript
module.exports = {
  // 指定项目根目录
  projectRoot: path.resolve(__dirname, '../..'),

  // 按需开启/关闭规则
  guardrails: {
    noEmoji: true,              // 零 Emoji 扫描
    noSecrets: true,            // 零敏感密钥扫描
    ormComments: false,         // 若新项目无数据库可设为 false
    architectureIsolation: true // 物理目录隔离校验
  },

  // 映射新项目的实际目录
  directories: {
    frontend: 'src/frontend',   // 对应前端源码目录
    backend: 'src/backend',     // 对应后端源码目录
    tests: 'tests',             // 对应测试脚本目录
    plans: 'plans'              // 对应时间戳计划归档目录
  }
};
```

### 第三步：安装依赖并运行自检
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

## 四、核心防护能力清单

| 防护维度 | 守护脚本 | 触发机制 | 防护效果 |
| :--- | :--- | :--- | :--- |
| **全域零 Emoji** | `core/guardrails.js` | 静态代码扫描 | 递归扫描代码、模板与注释，拦截任何 Unicode Emoji 字符 |
| **零明文密钥** | `core/guardrails.js` | 静态代码扫描 | 正则捕获 `sk-`、`lsv2_pt_`、`pat_`、`ghp_` 等敏感 Token |
| **ORM 100% 注释** | `core/guardrails.js` | 静态代码扫描 | 强制校验所有数据库模型及字段均具备中文注释契约 |
| **控制台零报错** | `core/runner.js` | Playwright 实机 | 拦截页面运行时的 `console.error` 与 `pageerror`，报错即熔断 |
| **Git 门禁自动化** | `templates/pre-commit.sample` | Git Hook | 在每次执行 `git commit` 时自动执行合规检测，违规阻断提交 |

---

## 五、Git Pre-commit 自动化挂载（可选）

若希望在本地执行 `git commit` 时由系统自动运行 Guardrails 静态检查：
```bash
# 在项目根目录下，将 sample 脚本写入 Git Hook
cp harness_starter_kit/templates/pre-commit.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
挂载后，一旦代码中出现未移除的 Emoji 或硬编码 API Key，Git 将直接拒绝提交并输出违规文件路径与行号。
