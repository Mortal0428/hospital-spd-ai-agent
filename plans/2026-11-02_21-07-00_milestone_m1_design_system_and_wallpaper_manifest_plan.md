# 研发计划：Milestone M1 全局设计系统与壁纸引擎基础设施

- **计划文档路径**：`plans/2026-11-02_21-07-00_milestone_m1_design_system_and_wallpaper_manifest_plan.md`
- **记录时间戳**：`2026-11-02 21:07:00`
- **当前阶段**：Milestone M1 基础设施落地
- **负责执行者**：`worker_m1` (Design System & Wallpaper Infrastructure Worker)

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_21-07-00_milestone_m1_design_system_and_wallpaper_manifest_plan.md
- 记录时间戳：2026-11-02 21:07:00
- 前端目标文件：
  1. frontend/src/styles/theme.css —— 全量注入 demo 原型 Design Tokens（深空 :root 与极简白瓷 [data-theme="light"]）、流体笔刷关键帧 (spdDrow1~5)、双环脉冲微加载 (spdSpin, spdPulsePing)、动态下划线、毛玻璃与微边框实用类，同时向下兼容现有业务类的 CSS 变量契约。
  2. frontend/src/styles/main.css —— 注入现代优雅滚动条、排版重置、tabular-nums 防抖等宽数字类、防误触高频点击优化与 SVG 通用样式规范。
  3. frontend/public/wallpapers_manifest.js —— 建立与 docs/design/wallpapers_manifest.js 严格对齐的 41 款（2款系统预设+39款工坊壁纸）全量清单，同时暴露 window.WALLPAPERS_MANIFEST 与 window.__WALLPAPERS_MANIFEST__，并配备 src、thumb 兼容别名。
  4. frontend/src/components/common/SvgIcon.vue —— 纯矢量 100% 0-Emoji SVG 图标组件，涵盖原型全部 27+ 核心图标及常用状态图标（共 35 种矢量路径），支持动态尺寸、颜色跟随与 strokeWidth 调节，函数级中文四要素注释全覆盖。
- 测试与验证：
  1. 运行 npm --prefix frontend run build 确保 0 error 0 warning 打包构建通过。
  2. 运行 Emoji 检测命令确保全域无任何 Emoji 表情字符。
```

---

## 二、 核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`100%`。
  - **样式与 Tokens**：直接来源于已通过验收验证的 `docs/design/spd_integrated_showcase_demo.html:12-53` 与 `1097-1530`，经过充分测试，完全与系统架构一致。
  - **壁纸清单**：`docs/design/wallpapers_manifest.js` 数据结构清晰，包含 39 款本地工坊项目及 2 款预设方案，经格式规整镜像至 `frontend/public/`，可被全局即时读取。
  - **矢量图标库**：基于 handoff.md 梳理的 27+ 权威路径，全部采用 `viewBox="0 0 24 24"` 标准绘制，严禁 Emoji。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：提供深浅色平滑自适应、流体笔刷动效、高保真毛玻璃卡片与无抖动数字排版；
- **开发者体验（DX）**：统一样式变量命名，提供类型安全的 `<SvgIcon name="..." />` 组件，消除零散内联 SVG；
- **AI 代理体验（AX）**：清晰的 Tokens 拓扑、纯净的清单与显式契约，便于后续 M2~M5 子 Agent 增量调用；
- **存量功能保护（零回归）**：在 `theme.css` 中完整保留 `--spd-*` 与 `--bg-surface` 等存量映射，确保既有页面视图在构建时不发生断裂。

---

## 三、 强制性原子实施清单

```markdown
实施清单：
1. [frontend/src/styles/theme.css] 重构 theme.css：
   - 注入 :root (深空暗色) 与 [data-theme="light"] (极简白瓷) 权威 Tokens (--bg-page, --bg-card, --accent-gradient, --orbit-* 等)；
   - 补充存量兼容变量映射 (--spd-bg-app, --bg-surface, --brand-primary, --status-ok 等)；
   - 注入流体笔刷核心关键帧 (spdDrow1 ~ spdDrow5)；
   - 注入双环脉冲与外环旋转关键帧 (spdSpin, spdPulsePing, fadeInPill)；
   - 注入动态底线下划线与毛玻璃卡片工具类 (.spd-glass-card, .spd-auth-* 等)。
2. [frontend/src/styles/main.css] 重构 main.css：
   - 优化现代半透明滚动条 (::-webkit-scrollbar)；
   - 规范排版重置与 user-select: none 防双击高频误选；
   - 增加 .spd-tabular-nums 与 .spd-mono 防抖等宽数字字体类；
   - 规范 .svg-icon 矢量图标通用样式与 .spd-ellipsis 防溢出截断。
3. [frontend/public/wallpapers_manifest.js] 创建 public/wallpapers_manifest.js：
   - 整合 2 款系统预设 (深空钛青、极简白瓷) 与 39 款工坊壁纸（合计 41 款）；
   - 标准化输出 window.WALLPAPERS_MANIFEST 与 window.__WALLPAPERS_MANIFEST__；
   - 配备规范的 src 与 thumb 属性映射，兼容 CommonJS / ES 环境。
4. [frontend/src/components/common/SvgIcon.vue] 编写纯矢量 SvgIcon.vue 组件：
   - 实现 35 种无 Emoji 纯矢量 SVG 路径；
   - 支持 name、size、color、strokeWidth、customClass 等属性；
   - 100% 覆盖标准化中文四要素文档注释 (@param, @returns, @route, @throws)。
5. [tests & build] 构建与合规验证：
   - 运行 npm --prefix frontend run build 校验 0 error 0 warning；
   - 扫描 frontend/src 下所有文件，校验绝对 0 Emoji；
   - 编写 handoff.md 汇报并向父 Agent 发送完成消息。
```
