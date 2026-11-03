> [STATUS: ARCHIVED] 本历史阶段文档已完成使命并降权归档至 `plans/archive/`，最新基线请查阅 `plans/2026-11-02_10-41-00_master_project_plan_and_confirmed_baseline.md`。

# 研发计划：全局技能/MCP部署与医疗物资系统初始化

[变更计划]
- 计划文档路径：plans/2026-10-29_18-52-01_install_skills_mcp_and_init_project.md
- 记录时间戳：2026-10-29 18:58:15
- 全局技能目标：C:\Users\27705\.gemini\config\skills\edu-pm-workflow (已完成部署与校验)
- 全局 MCP 目标：C:\Users\27705\.gemini\config\mcp_config.json (已增量注入 xerj，保护现有 playwright)
- 前端目标文件：frontend/ (根据用户指示，医疗物资系统工程初始化本阶段暂缓执行)
- 后端目标文件：backend/ (根据用户指示，医疗物资系统工程初始化本阶段暂缓执行)
- 测试与截图文件：tests/ (暂缓执行)

---

## 1. 核心评估指标

### 可行性与把握度评估
- **把握度**：100%
- **实施结果**：
  1. `edu-pm-workflow` 技能已完整部署至用户全局技能目录，核心 `SKILL.md`、模板与校验脚本均就绪。
  2. `xerj v1.0.0-rc.100` 已成功安装至 `C:\Users\27705\AppData\Local\Programs\xerj\xerj.exe` 并写入用户 PATH。
  3. `mcp_config.json` 严格实施增量更新，`playwright` 与 `xerj` 双服务共存完好。

### 存量功能与三方体验影响分析
- **存量功能保护（零回归）**：`playwright` MCP 配置完整保留，未发生破坏性覆盖。
- **三方体验协同**：
  - **DX（开发者体验）**：全局技能和 MCP 一次性部署完毕，无需反复手动配置。
  - **AX（AI 代理体验）**：AI 具备调用 `edu-pm-workflow` 的结构化交付能力，随时可通过 MCP 挂载本地代码语义检索。

---

## 2. 原子实施清单与执行状态

实施清单：
1. [已完成] [全局技能部署] 将 edu-pm-workflow 部署至 C:\Users\27705\.gemini\config\skills\edu-pm-workflow 与 C:\Users\27705\.gemini\skills\edu-pm-workflow，校验文件完整性通过。
2. [已完成] [全局 MCP 部署] 执行安装 xerj.exe 至本地目录 C:\Users\27705\AppData\Local\Programs\xerj\xerj.exe，校验执行版本 (v1.0.0-rc.100) 通过。
3. [已完成] [全局 MCP 配置] 增量合并 C:\Users\27705\.gemini\config\mcp_config.json，安全接入 xerj 并保护 playwright 节点完好。
4. [暂缓] [工程目录拓扑构建] 用户指令先不进行医疗物资系统工程初始化。
5. [暂缓] [医疗物资系统需求与原型规划] 用户指令先不进行医疗物资系统工程初始化。
6. [暂缓] [前端基础工程与组件实现] 用户指令先不进行医疗物资系统工程初始化。
7. [暂缓] [编写自动化测试脚本] 用户指令先不进行医疗物资系统工程初始化。
8. [暂缓] [运行 Playwright 回环验证与截图] 用户指令先不进行医疗物资系统工程初始化。
