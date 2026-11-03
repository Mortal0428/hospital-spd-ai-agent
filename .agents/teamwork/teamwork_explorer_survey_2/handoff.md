# 前端代码库盘点与数字化展厅重构差距分析报告 (handoff.md)

- 报告编写者: teamwork_explorer_survey_2 (Frontend Codebase Explorer)
- 关联任务: ORIGINAL_REQUEST.md
- 报告时间: 2026-11-02T12:55:00Z
- 审查基准: docs/design/spd_integrated_showcase_demo.html

---

## 1. 观察结论 (Observation)

### 1.1 项目配置与工程架构 (Project Configuration & Architecture)
- **文件位置**: `frontend/package.json` (第 1-26 行), `frontend/vite.config.ts` (第 1-34 行), `frontend/tsconfig.json` (第 1-25 行), `frontend/src/main.ts` (第 1-30 行)
- **技术栈现状**:
  - 运行时框架: `vue`: `^3.5.13`
  - 路由与状态: `vue-router`: `^4.5.0`, `pinia`: `^2.3.0`
  - UI 与组件库: `element-plus`: `^2.9.1`, `@element-plus/icons-vue`: `^2.3.1`, `axios`: `^1.7.9`
  - 构建与工具链: `vite`: `^5.4.11`, `vue-tsc`: `^2.2.0`, `typescript`: `^5.7.2`, `@vitejs/plugin-vue`: `^5.2.1`
  - 样式预处理器: **未安装 Sass/SCSS/Less/Tailwind/UnoCSS**，纯粹依靠原生 CSS (`main.css` + `theme.css`)。
- **构建结果观察**:
  - 执行 `npm --prefix frontend run build`，控制台输出 `vue-tsc && vite build`，在 13.01 秒内完成。
  - TypeScript 类型检查 0 错误、0 警告。
  - 生产构建警告: `(!) Some chunks are larger than 500 kB after minification: dist/assets/index-HLJreH03.js is 1,149.05 kB`，因未配置 Rollup `manualChunks` 将 Element Plus 与 Vue 核心拆包所致。
- **入口挂载观察**:
  - `frontend/src/main.ts` 第 18-27 行 `bootstrap()` 依次挂载 `pinia`, `router`, `ElementPlus`，并引入 `element-plus/dist/index.css`、`./styles/theme.css`、`./styles/main.css`。
  - `frontend/src/App.vue` 第 13-18 行监听 `onMounted`，从 `localStorage` 读取 `spd_theme` 并设置 `document.documentElement.setAttribute('data-theme', savedTheme)`。

### 1.2 路由架构与鉴权守卫 (Routing Architecture)
- **文件位置**: `frontend/src/router/index.ts` (第 1-87 行)
- **路由清单与重定向**:
  - `/login`: 映射 `LoginView.vue` (meta: `医慧通行 · 身份认证与权限协同中枢`)
  - `/`: 映射 `MainLayout.vue`，默认重定向至 `/dict`
  - `/dict`: `ProductDictView.vue` (1. 产品字典管理 双维分类)
  - `/general`: `GeneralMaterialView.vue` (2. 普通耗材管理 主库按需分发)
  - `/high-value`: `HighValueView.vue` (3. 高值耗材管理 一物一码专仓)
  - `/secondary`: `SecondaryWarehouseView.vue` (4. 二级库管理 临床科室库房)
  - `/logs`: `WorkflowLogView.vue` (5. 全流程业务链路日志 6W)
  - `/finance`: `FinancePrintView.vue` (6. 统计查询与单据打印中心)
  - `/procurement`: `SupplierPurchaseView.vue` (7. 多级采购与供应商协同)
- **导航守卫观察**:
  - `frontend/src/router/index.ts` 第 69-84 行:
    ```typescript
    router.beforeEach((to, _from, next) => {
      const userStore = useUserStore();
      if (!userStore.isLoggedIn && to.path !== '/login') {
        next({ path: '/login' });
      } else if (userStore.isLoggedIn && to.path === '/login') {
        next({ path: '/dict' });
      } else {
        next();
      }
    });
    ```
  - **核心脱节观察**: 路由守卫强行将所有未认证流量拦截并踢往独立的 `/login` 全屏页面，而不是像原型 `spd_integrated_showcase_demo.html` 那样将展厅作为默认公共底座，并在未登录时以优雅模态弹窗（Modal Auth Card）浮层呈现。

### 1.3 现有布局与壳层结构 (Layout & Shell)
- **文件位置**: `frontend/src/layouts/MainLayout.vue` (第 1-441 行)
- **结构现状**:
  - 顶部导航栏 (`.app-header`, 第 4-74 行): 包含系统标识、角色切换下拉框 (`select.role-selector`)、细粒度 RBAC 抽屉按钮、标准四联单据按钮、亮暗主题切换按钮、退出登录按钮，以及一个 crude 按钮:
    ```typescript
    // 第 279-281 行
    function handleJumpShowcase() {
      window.open('/docs/design/spd_integrated_showcase_demo.html', '_blank');
    }
    ```
  - 左侧侧边栏 (`aside.sidebar`, 第 79-180 行): 7 个菜单项（序号 1 至 7），底部挂载当前登录人员工号与科室徽标。
  - 右侧主工作区 (`main.main-workspace`, 第 183-196 行): 顶部固定一段 `.role-banner` 权限上下文横幅，下方直接插入 `<router-view />`。
- **与 Demo 原型的巨大质感差距**:
  - 当前布局为极其传统的 ERP 左右分栏灰白方块盒模型。
  - 原型 `spd_integrated_showcase_demo.html` 的核心视觉是通透悬浮导航栏 (`.top-float-nav`)、居中双模态书签切换胶囊 (`.mode-segmented-pill`)、Layer 0 全屏 Wallpaper Engine 视频与场景媒体层 (`.wallpaper-media-layer`)、Layer 1 极轻量调光层 (`.wallpaper-dimmer-layer`)、Layer 0.8 实时数字时钟小部件、以及纯享模式 (`zen-pure-mode`)。
  - 目前的前端布局完全缺失了上述一切数字化展厅的现代化沉浸式元素，把展厅当成了外部静态 HTML 进行外链弹窗跳转。

### 1.4 登录视图现状与模态重构差距 (Login View & Healthcare Modal Auth Card)
- **文件位置**: `frontend/src/views/LoginView.vue` (第 1-277 行)
- **结构现状**:
  - 静态铺满屏幕的独立页面容器 (`.spd-auth-container`)，背景带有两个粗糙的径向渐变背景块 (`.spd-auth-bg-decor`)。
  - 使用了 Element Plus 的 `el-tabs` 分割为【账号登录】与【医护人员注册】两个标签页。
  - 表单内使用了 `el-form`, `el-form-item`, `el-input`，样式为生硬的白底蓝框。
  - 底部配有 4 大角色网格 (`.spd-role-fast-grid`, 4 个 `.spd-role-btn`)。
- **与 Demo 原型对比差距**:
  - Demo 中为 **浮动模态遮罩与卡片** (`.spd-auth-backdrop` / `.spd-auth-card`，第 1530-1794 行与第 2066-2130 行):
    - 高斯模糊背景: `background: rgba(15, 23, 42, 0.70); backdrop-filter: blur(20px);`
    - 精致圆角卡片: `width: 440px; border-radius: 20px; border: 1px solid var(--border-card);`
    - 医疗 Logo + 标题 + 副标题 + 关闭按钮 (`.spd-auth-close`)。
    - 纯内联原生 SVG 图标输入框 (`.spd-auth-input-wrap` + `.spd-auth-input`)，配备密码明暗文切换按钮 (`.spd-pwd-toggle`) 与记住会话复选框。
    - 流体高质感提交按钮 (`.spd-auth-submit`)，悬停微提亮，点击 scale(0.98)。
    - 分割线与 3-4 个演示角色一键免密卡片 (`.spd-role-btn`)。
  - 现存 `LoginView.vue` 风格割裂、未采用模态化，且无法在展厅中即开即关。

### 1.5 现有 7 大业务视图全量盘点 (Business Views Inventory)
通过深入审查 `frontend/src/views/` 下的所有业务视图，盘点出当前结构、样式与与 Demo 原型的差距如下:

| 文件路径 | 视图功能 | 内部主要组件与 Tab 结构 | 当前样式与实现手段 | 与数字化展厅 (Showcase) 的差距分析 |
| :--- | :--- | :--- | :--- | :--- |
| `frontend/src/views/ProductDictView.vue` (551行) | 1. 产品字典管理 (双维分类) | 4 宫格 KPI 卡片大盘、高级工具栏 (检索/调价/复制/导出)、左侧双树 (`.dual-tree-panel`: 仓库树+分类树)、右侧 `el-table` | 基础类名 + Element Plus 表格与按钮，灰白卡片边框 | 缺少毛玻璃半透明容器背景 (`--bg-card`)、微边框荧光与悬停流光质感，表格分页与行操作过于死板。 |
| `frontend/src/views/GeneralMaterialView.vue` (687行) | 2. 普通耗材管理 (主库按需分发) | 4 宫格 KPI、5 个 Tab 页 (`el-tabs type="border-card"`: 请领受理、耗材入库、耗材出库、耗材盘点、期初数据) | 依赖 `type="border-card"`，灰色硬质边框，多套普通 `el-table` 与两阶段确认弹窗 | `border-card` 的标签页生硬厚重，缺乏通透感；KPI 与操作栏未采用毛玻璃自适应卡片。 |
| `frontend/src/views/HighValueView.vue` (485行) | 3. 高值耗材管理 (一物一码专仓) | 4 宫格 KPI、4 个 Tab 页 (备货管理、科室退货出库、高值库存查询、高值核销查询)、二维码载荷徽标 | 原生 Element Plus 表格与状态徽标，挂载扫码核销弹窗 | 未融合展厅中的高科技感医疗器械透视卡片；表格缺乏动态底线与流畅行高微交互。 |
| `frontend/src/views/SecondaryWarehouseView.vue` (248行) | 4. 二级库管理 (临床科室库房) | 4 宫格 KPI、管辖科室切换胶囊、2 个 Tab 页 (接收入库与发料出库、库存调拨与跨院调拨) | 顶部 `.kpi-overview-bar` + `el-tabs` + 普通表格 | 缺少病区科室专属医疗状态指示灯 (`pulse-mini-dot`)，页面整体仍为低信息密度的传统表单。 |
| `frontend/src/views/WorkflowLogView.vue` (105行) | 5. 全流程业务链路日志 (6W) | 顶部审计说明卡片、单张全量 6W 流水表格 (`el-table`: 流水号/单号/动作/From/To/数量/金额/审计状态) | 单一数据表格，无分页与时间轴视效 | 缺乏图谱式或时间轴式流转溯源视觉，文字密集且黑白对比呆板。 |
| `frontend/src/views/FinancePrintView.vue` (190行) | 6. 统计查询与单据打印中心 | 4 宫格 KPI、四联单据快速发射面板、临床核算科室表格 (耗占比/金额) | 网格卡片 + 普通表格 + 打印弹窗挂载 | 缺少现代数据大屏图表或动态进度柱状微动效；打印预览样式在暗色模式下对比度未完全隔离。 |
| `frontend/src/views/SupplierPurchaseView.vue` (310行) | 7. 多级采购与供应商协同 | 供应商资质核验横幅 (`.qual-banner`)、采购订单协同表格 (订单/供应商/品名/拣货批号/阶段/操作) | 顶部准入警告框 + 表格 + 发货弹窗 | 缺乏协同链路状态流程指示微交互，整体视觉割裂。 |

### 1.6 全局样式体系与设计 Tokens 审计 (Styles & Theme Tokens)
- **文件位置**: `frontend/src/styles/theme.css` (第 1-363 行), `frontend/src/styles/main.css` (第 1-110 行)
- **现状分析**:
  - `theme.css` 中定义了 `--spd-bg-app`, `--spd-bg-surface`, `--spd-bg-glass`, `--spd-primary`, 并附带了浅色与暗色模式的简单映射。
  - **核心缺陷**:
    1. Demo 原型中的核心壁纸渲染与流光变量在 `theme.css` 中**完全缺失**，例如:
       `--bg-card: rgba(15, 23, 42, 0.85);`
       `--bg-card-hover: rgba(30, 41, 59, 0.95);`
       `--border-card: rgba(255, 255, 255, 0.14);`
       `--border-divider: rgba(255, 255, 255, 0.08);`
       `--accent-gradient: linear-gradient(135deg, #38bdf8 0%, #22d3ee 50%, #60a5fa 100%);`
       `--wp-dim: 0.55; --wp-blur: 8px; --orbit-size: 1040px; --orbit-radius: 520px;`
    2. 缺少 Demo 原型中的核心微动效样式:
       - `.spd-fluid-btn`: 流体流动笔刷核心入口按钮 (Brush Fluid Stroke Button)
       - `.spd-spinner-backdrop`: 双环脉冲微加载指示器 (Dual-ring Pulsing Spinner)
       - `.spd-search-form`: 动态底线微交互搜索框 (Animated Underline Search Input)
       - `.stage-orbital-view`: 360 度环形轨道系统 (Orbital Gallery Engine)
       - `.stage-tilted-view`: 3D 弧面圆柱 16-切片流光系统 (Tilted Grid Engine)
       - `.wallpaper-drawer-panel`: 全量 39 款壁纸工坊抽屉面板 (分类/筛选/自由拖拽)

### 1.7 全域 Emoji 字符审计 (Emoji Audit)
- **执行方式**: 编写 Node.js 专用脚本，对 `frontend/src/` 及 `frontend/index.html` 下的所有 `.vue`, `.ts`, `.css`, `.html` 文件，使用标准 Unicode 正则表达式 (`/[\u{1F000}-\u{1FFFF}]|[\u{2600}-\u{27BF}]|[\u{2300}-\u{23FF}]|[\u{2B50}-\u{2B55}]/u`) 进行逐行全量穿透扫描。
- **扫描结果**:
  - 扫描文件数: 23 个源码文件
  - **违规 Emoji 数量: 0**
  - **结论**: 存量前端代码在图标设计上保持了高度克制，100% 采用了内联矢量 `<svg>` 或 Element Plus 字体图标，没有任何 Emoji 字符。这一规范需在后续重构中 100% 继续严格保持。

### 1.8 TypeScript 类型与编译构建健康度 (Sanity Check)
- **编译测试**: `npm --prefix frontend run build` (内部调用 `vue-tsc && vite build`)
- **执行结果**:
  - `vue-tsc` 严格类型检查完全通过，0 错误、0 警告。
  - Vite 打包构建成功，生成 `dist/index.html` (0.73 kB) 及相关资源。
- **潜在风险点**:
  - 单包体积超标: `dist/assets/index-HLJreH03.js` 达到了 1,149.05 kB。建议在 `vite.config.ts` 中配置 `rollupOptions.output.manualChunks` 拆分 vendor。
  - 缺少 `wallpapers_manifest.json` 与工坊静态媒体资源在前端 `public/` 下的映射。

---

## 2. 逻辑推导链 (Logic Chain)

```
[观察 1.3] 现有 MainLayout.vue 仅是一个普通的左侧菜单+右侧内容的 ERP 模板，展厅入口被降级为一个粗暴的 window.open 外部链接。
    ↓ (推导)
[逻辑节点 A] 当前前端未将 docs/design/spd_integrated_showcase_demo.html 的核心双模态引擎（360 环形轨道 + 3D 弧面切片流光 + 4K 动态壁纸工坊 + 纯享模式）整合进 Vue 3 单页应用中，导致用户无法在 SPA 内部沉浸式体验医疗物资数字化展厅。
    ↓ (推导)
[观察 1.4] 现有 LoginView.vue 是一个必须经由路由跳转的独立全屏路由 /login，使用 Element Plus 基础表单；而 Demo 原型是悬浮在展厅上的 Healthcare Modal Auth Card (模态登录卡片)。
    ↓ (推导)
[逻辑节点 B] 登录机制与页面架构完全脱节。必须将全屏 /login 页面改写为或者并存为受控模态卡片（或以展厅为背景的模态登录中枢），支持 4 大角色一键免密接入、密码明暗文切换、会话记忆与优雅平滑淡入淡出。
    ↓ (推导)
[观察 1.5] 业务视图全部采用厚重的灰色背景、el-tabs type="border-card" 以及原生的 el-table，未采用 Demo 原型中苹果风格的毛玻璃微边框卡片 (--bg-card: rgba(15, 23, 42, 0.85), --border-card: rgba(255, 255, 255, 0.14))。
    ↓ (推导)
[逻辑节点 C] 必须系统性推翻现有生硬的表格与选项卡样式，将 docs/design/spd_integrated_showcase_demo.html 与 spd_frontend_design_variants.html 中定义的设计系统 Tokens 全面导入 theme.css，对 7 大业务视图进行现代克制质感的半透明毛玻璃与微边框重构。
    ↓ (推导)
[观察 1.1 与 1.8] 前端工程构建非常健康（vue-tsc 0 错误），现有 API 与 Pinia 鉴权链路完备，但缺少壁纸工坊数据源映射。
    ↓ (推导)
[核心结论] 前端无需重写后端接口或状态逻辑，重构的核心战场在于：(1) 将双模态数字化展厅引擎直接内置为 Vue 3 核心门户；(2) 将登录重构为现代医疗模态中枢；(3) 全面升级全局 Tokens 并赋予 7 大业务视图高质感毛玻璃微边框与 Apple HIG 交互体验；(4) 保持 100% 零 Emoji 与 TypeScript 严格类型检查。
```

---

## 3. 注意事项与潜在约束 (Caveats)

1. **测试用例向后兼容约束**:
   - `tests/harness/verify_login_and_4_roles.js` 与 `tests/harness/verify_frontend_vue3.js` 中包含大量硬编码选择器（如 `.role-banner`, `.role-selector select`, `.dual-tree-panel`, `.tree-node`, `.kpi-card`, `.kpi-val`, `#tab-init_stock`, `.spd-role-btn`, `.spd-auth-title` 等）。
   - **重构铁律**: 在重构视觉与重构 DOM 结构时，**必须 100% 保留这些关键选择器与类名契约**，确保所有自动化测试与 Harness 回环脚本能够无缝通过，严禁因更改 class 造成存量测试熔断。
2. **壁纸工坊媒体路径在 Vite 开发服务器下的映射**:
   - Demo 中的原生 4K MP4 视频壁纸引用了本地 Steam/本地静态路径。在 Vite 前端开发服务器（5173 端口）下，直接访问 `file:///` 协议可能受到浏览器沙箱安全策略限制。
   - 解决方案: 应在 `frontend/public/` 中建立壁纸清单与示例视频/高清画质的静态静态资源映射，或者通过内联 SVG/Canvas 光晕/渐变预设进行优雅降级支持。
3. **全域禁用 Emoji 铁律**:
   - 任何新增代码、提示文字、组件模板、按钮、日志信息中严禁引入任何 Emoji 表情字符。

---

## 4. 结论与重构执行路线 (Conclusion & Implementation Blueprint)

### 4.1 核心重构落地方案
建议研发团队将重构划分为 4 个高度聚焦的原子阶段：

#### 阶段 A：全局设计系统 Tokens 与数字化展厅底座注入 (Shell & Design Tokens)
1. **注入设计系统 Tokens**: 将 `docs/design/spd_integrated_showcase_demo.html` 的全部 CSS 变量（`--bg-card`, `--border-card`, `--accent-primary`, `--accent-gradient`, `--shadow-card`, `--wp-dim`, `--orbit-size` 等）以及 3 大微动效类（流体笔刷按钮、双环微脉冲加载器、动态底线搜索框）完整引入 `frontend/src/styles/theme.css`。
2. **构建现代化展厅壳层组件 (`frontend/src/views/ShowcaseView.vue` 或整合入主视窗)**:
   - 实现 Layer 0 壁纸媒体层 (`.wallpaper-media-layer`)、Layer 1 极轻量调光层 (`.wallpaper-dimmer-layer`)、Layer 0.8 实时数字时钟部件。
   - 实现顶部悬浮通透导航栏 (`.top-float-nav`) 与双模态书签切换胶囊 (`.mode-segmented-pill`)。
   - 实现 360 度环形轨道卫星拓扑 (`.stage-orbital-view`) 与 3D 弧面圆柱切片流光系统 (`.stage-tilted-view`)。
   - 实现全量壁纸工坊底部抽屉面板 (`.wallpaper-drawer-panel`)。

#### 阶段 B：医慧通行现代医疗模态登录中枢重构 (R2 对齐)
1. 将 `frontend/src/views/LoginView.vue` 全面重构为以数字化展厅为背景的现代医疗模态卡片，或者抽取为全局受控模态弹窗组件 `HealthcareAuthModal.vue`。
2. 完整复刻 Demo 的卡片结构：医疗品牌标识、工号输入框（矢量 SVG 图标）、密码输入框（带明暗文切换眼眸图标）、记住会话复选框、立即验证登录流体按钮。
3. 强化 4 大演示角色一键免密体验通道（系统管理员、耗材科主管、临床二级库、财务科审计），保留 `.spd-role-btn` 与 `.spd-auth-title` 选择器契约。

#### 阶段 C：业务视图全面毛玻璃与现代质感革新 (R3 对齐)
1. 重构 7 大业务视图的外层卡片与选项卡样式：消除 Element Plus 生硬的 `border-card` 边框，应用 `--bg-card` 毛玻璃与 `--border-card` 微边框。
2. 保持各视图的原生业务逻辑、Pinia 鉴权和 API 通信契约不变，对表格行、状态胶囊、KPI 4 宫格卡片实施 Apple HIG 悬停微动效提拉与自然过渡。
3. 按照用户最新指示要求：**每完成一个页面的整改，使用 Playwright 捕获该页面的最新实机截图并归档至 `tests/screenshots/`**。

#### 阶段 D：构建优化与自动化回环测试护栏
1. 在 `vite.config.ts` 中配置 Rollup 分块，优化超大 vendor 包体积。
2. 运行 `tests/harness/verify_frontend_vue3.js` 与 `verify_login_and_4_roles.js`，确保 10 项强断言 100% 全绿，无任何 Console Error / PageError。

---

## 5. 独立验证方法 (Verification Method)

后续 Agent 或开发者可通过执行以下命令独立复现与验证本报告结论:

1. **验证 TypeScript 编译与构建状态**:
   ```bash
   npm --prefix frontend run build
   ```
   *预期结果*: `vue-tsc` 0 错误通过，Vite 成功生成 `dist/`，仅出现 index 单包体积超 500kB 的优化提示。

2. **验证全域零 Emoji 违规**:
   ```bash
   node -e "const fs = require('fs'); const path = require('path'); const emojiRegex = /[\u{1F000}-\u{1FFFF}]|[\u{2600}-\u{27BF}]|[\u{2300}-\u{23FF}]|[\u{2B50}-\u{2B55}]/u; function walk(d) { let res = []; fs.readdirSync(d).forEach(f => { const p = path.join(d, f); if (fs.statSync(p).isDirectory()) { if (f !== 'node_modules' && f !== 'dist') res = res.concat(walk(p)); } else if (/\.(vue|ts|css|html)$/.test(f)) res.push(p); }); return res; } const files = walk('frontend'); let errs = 0; files.forEach(f => { const lines = fs.readFileSync(f, 'utf8').split('\n'); lines.forEach((l, i) => { if (emojiRegex.test(l)) { console.error('Violation:', f, i+1, l); errs++; } }); }); if (errs === 0) console.log('PASS: 100% Zero Emoji Verified.');"
   ```
   *预期结果*: 输出 `PASS: 100% Zero Emoji Verified.`。

3. **验证存量测试选择器契约**:
   检查 `frontend/src/views/LoginView.vue` 中是否存在 `.spd-auth-title` 和至少 4 个 `.spd-role-btn`；检查 `frontend/src/layouts/MainLayout.vue` 中是否存在 `.role-banner` 与 `.role-selector select`。
