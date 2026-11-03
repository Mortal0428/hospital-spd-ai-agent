# 研发实施计划：四大核心微交互与现代医疗登录模态中枢深度集成规范

> 计划归档时间戳：2026-11-02 17:51:00  
> 任务标识符：`micro_interactions_and_login_modal`  
> 关联协议：增强型 RIPER-5 代理执行协议（阶段 3：[MODE: PLAN]）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_17-51-00_micro_interactions_and_login_modal_plan.md
- 记录时间戳：2026-11-02 17:51:00
- 目标交互设计文件：
  - docs/design/spd_integrated_showcase_demo.html（装配流体流动笔刷按钮、双环脉冲 Spinner、动态底线搜索框与现代医疗登录模态弹窗）
- 目标自动化测试文件：
  - tests/harness/verify_integrated_showcase.js（扩充断言 14 与断言 15，执行全流程回环测试与实机截图）
- 产出截图路径：
  - tests/screenshots/2026-11-02_17-51-00_fluid_button_and_search.png
  - tests/screenshots/2026-11-02_17-51-00_login_modal_showcase.png
```

---

## 二、 核心评估指标（强制）

### 1. 可行性与把握度评估
- **把握度：99%**
- **技术风险与应对策略**：
  - *风险点 1：流体流动笔刷关键帧 `@keyframes drow1~5` 与现有 CSS 命名冲突*。
    - **应对**：使用统一前缀 `.spd-fluid-btn`、`.spd-fluid-drow1/2`、`@keyframes spdFluidDrow1~5`，形成严格样式隔离。
  - *风险点 2：动态搜索框清空按钮在浏览器原生样式下的异常显示*。
    - **应对**：通过 CSS `appearance: none; -webkit-appearance: none;` 清除浏览器默认清除小叉号，100% 采用语义化内联 SVG。
  - *风险点 3：键盘 ESC 键冲突（纯享模式退出 vs 登录模态框关闭）*。
    - **应对**：在键盘监听事件中实现层级判断——若登录模态窗处于打开状态，ESC 优先关闭登录弹窗；仅当登录弹窗关闭且处于全屏纯享模式时，ESC 才触发退出纯享模式，两者严密互斥。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：
  - 中央 CTA 按钮由扁平按钮升级为流体笔触边缘、悬浮字符拉宽的呼吸感交互；
  - 壁纸检索具备聚焦平滑展开底线与即时清空按钮，交互细腻；
  - 医疗认证模态弹窗采用细腻毛玻璃（`-webkit-backdrop-filter: blur(24px)`），全面适配深色/浅色模式，去除了廉价 AI 发光感；
  - 全域 100% 禁用 Emoji，统一采用医疗科技语义化纯矢量 SVG 图标。
- **开发者体验（DX）**：
  - 变量与现有 Design Tokens 完全对齐（`--accent-primary`、`--bg-card`、`--border-card` 等）；
  - 所有新增函数均具备标准化四要素中文注释（`@param`、`@returns`、`@route`、`@throws`）。
- **AI 代理协作体验（AX）**：
  - DOM 节点具备唯一的 ID 与类名契约（如 `#btn-open-login`、`#spd-login-modal`、`#spd-search-input`、`#btn-enter-workbench` 等），便于 Playwright 快速精确定位。
- **存量功能保护**：
  - 100% 保障已通过的 13 项强断言（双模态切换、4K 视频 Cover、7K/2K 超清原画铺满、音频解包与自由开关、持久化记忆）零回归、零退化。

### 3. Playwright 自动化回环测试与截图验证方案
- **自测路径**：
  1. 访问集成原型并校验静态无 Emoji 违规；
  2. 断言 14：验证中央 CTA 流体流动按钮渲染与悬浮样式计算；验证抽屉动态底线搜索框的聚焦展开、字符输入与一键重置清除；验证全局双环脉冲 Loading 容器；
  3. 断言 15：点击顶部“医慧通行”按钮，验证模态弹窗平滑呼出、密码显隐切换（`text <-> password`）、三级角色一键体验卡片交互，并截取高精度实机图归档。
- **断言条件与保存路径**：
  - `tests/screenshots/2026-11-02_17-51-00_fluid_button_and_search.png`
  - `tests/screenshots/2026-11-02_17-51-00_login_modal_showcase.png`

---

## 三、 技术与 UI 细节规范

### 1. 流体流动笔刷按钮（Brush Fluid Stroke Button）
- **类名规范**：`.spd-fluid-btn`、`.spd-fluid-line`、`.spd-fluid-text`、`.spd-fluid-drow1`、`.spd-fluid-drow2`
- **颜色绑定**：
  - `--line_color`: 动态绑定 `var(--accent-primary, #0284c7)`；
  - `--back_color`: 动态绑定 `rgba(2, 132, 199, 0.16)`（亮色）与 `rgba(56, 189, 248, 0.22)`（暗色）；
- **动画细节**：悬停时触发 5 阶段流动关键帧展开，文字间距由 `1.5px` 平滑过渡至 `4.5px`，保留微触觉缩放反馈。

### 2. 双环脉冲微加载器（Dual-ring Pulsing Spinner）
- **容器与结构**：`#spd-global-spinner`，内含 `.spd-spinner-outer-ring`（360度顺滑旋转 `animate-spin`）与 `.spd-spinner-inner-pulse`（核心矢量图标呼吸 `animate-ping`）。
- **调度函数**：
  - `window.showSpdSpinner(text)`: 激活全屏半透明毛玻璃遮罩并显示当前操作提示；
  - `window.hideSpdSpinner()`: 平滑淡出隐藏。

### 3. 动态底线微交互搜索框（Animated Underline Search Input）
- **容器与结构**：`#spd-wallpaper-search-form`，内含 `#spd-search-input` 与 `#spd-search-reset`。
- **CSS 伪元素**：`:focus-within:before` 实现从中心向两侧横向展开下划线动画（`scaleX(0) -> scaleX(1)`）；
- **重置清除**：输入内容后重置按钮可见，点击清空输入内容并自动重置壁纸列表筛选。

### 4. 现代医疗卡片风格登录认证中枢（Healthcare Modal Auth Card）
- **模态容器**：`#spd-login-modal`，高斯模糊毛玻璃背景遮罩；
- **表单内容**：
  - 工号/医疗邮箱输入框（默认填充演示工号 `SPD-ADMIN-01`）；
  - 密码输入框（带 `#btn-toggle-pwd` 小眼睛明暗文切换）；
  - 记住认证凭证复选框与找回密码链接；
  - 主登录提交按钮 `#btn-submit-login`；
  - 三级角色免密一键体验按钮组：
    - `[data-role="consumable"]`：耗材科管理员
    - `[data-role="nurse"]`：临床二级库护士
    - `[data-role="finance"]`：财务合规审计科长

---

## 四、 强制性原子实施清单

```markdown
实施清单：
1. [已完成] [docs/design/] 优化 docs/design/spd_integrated_showcase_demo.html：
   - 注入流体流动笔刷按钮（Brush Fluid Stroke Button）样式与 DOM 结构，升级中央主舞台 CTA 按钮；
   - 注入双环脉冲微加载器（Dual-ring Pulsing Spinner）样式与全局调度函数（showSpdSpinner / hideSpdSpinner）；
   - 注入动态底线微交互搜索框（Animated Underline Search Input）样式与重置逻辑，替换工坊侧边栏搜索框；
   - 在顶部导航栏新增“医慧通行”登录入口胶囊，部署现代医疗卡片风格登录模态弹窗（含密码显隐、三级角色一键体验、ESC/遮罩退出联动）。
2. [已完成] [tests/] 升级 tests/harness/verify_integrated_showcase.js 自动化测试脚本：
   - 扩充断言 14：检验流体笔刷按钮渲染计算样式、动态底线搜索框聚焦/输入/重置逻辑、以及微加载器调度；
   - 扩充断言 15：检验登录模态弹窗呼出、密码显隐切换、角色卡片点击响应，并截取高清实机图；
   - 确保全量 15 项强断言完整无缝覆盖。
3. [已完成] [tests/] 启动 Playwright 执行 15 项全量强断言自动化回环测试，校验全部通过。
4. [已完成] [tests/ | plans/] 将生成的实机截图归档至 tests/screenshots/ 并同步到 Artifacts 目录。
5. [已完成] [plans/] 更新计划进度台账，向用户交付实机截图与验证结果。
```

---

## 五、 执行与回环验收结果

- **验收时间戳**: `2026-11-02 18:18:15`
- **自动化测试结果**: 15 项强断言 100% 全部通过，0 错误，0 Emoji 违规。
- **实机截图归档**:
  1. `tests/screenshots/2026-11-02_17-51-00_fluid_button_and_search.png`
  2. `tests/screenshots/2026-11-02_17-51-00_login_modal_showcase.png`
- **当前状态**: 已圆满完成交付。
