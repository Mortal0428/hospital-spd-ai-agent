# 医疗物资系统前端数字化展厅（Showcase）与模态登录中枢规格挖掘报告 (Specification Mining Handoff Report)

## 1. 观察记录 (Observation)

### 1.1 权威参考原型与代码源观测
本报告所依托的权威视觉与技术规范来自以下本地原型源码：
- **主要权威原型**：`docs/design/spd_integrated_showcase_demo.html`（共 3,120 行，121,993 字节）
- **多变体选型与生产级原型**：`docs/design/spd_frontend_design_variants.html`（共 1,470 行，69,600 字节）
- **高保真可交互业务原型**：`docs/design/spd_interactive_prototype.html`（共 1,098 行，49,008 字节）
- **现有前端待重构文件**：`frontend/src/views/LoginView.vue`、`frontend/src/layouts/MainLayout.vue`、`frontend/src/views/*.vue`

### 1.2 全局设计系统 Tokens 逐行观察 (`docs/design/spd_integrated_showcase_demo.html:12-53`)
原型在 `:root`（深色深空模式）与 `[data-theme="light"]`（极简白瓷模式）中定义了完整的工业级 Design Tokens：

```css
:root {
    --bg-page: #080c14;
    --bg-card: rgba(15, 23, 42, 0.85);
    --bg-card-hover: rgba(30, 41, 59, 0.95);
    --border-card: rgba(255, 255, 255, 0.14);
    --border-divider: rgba(255, 255, 255, 0.08);
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --accent-primary: #38bdf8;
    --accent-gradient: linear-gradient(135deg, #38bdf8 0%, #22d3ee 50%, #60a5fa 100%);
    --shadow-card: 0 20px 48px -6px rgba(0, 0, 0, 0.65), 0 4px 16px -2px rgba(0, 0, 0, 0.4);
    --radius-card: 20px;
    --radius-pill: 9999px;
    --tile-bg: rgba(15, 23, 42, 0.88);
    --tile-border: rgba(255, 255, 255, 0.16);

    /* 壁纸调光与模糊变量 */
    --wp-dim: 0.55;
    --wp-blur: 8px;
    --orbit-size: 1040px;
    --orbit-radius: 520px;
    --orbit-duration: 38s;
}

[data-theme="light"] {
    --bg-page: #f1f5f9;
    --bg-card: rgba(255, 255, 255, 0.90);
    --bg-card-hover: rgba(255, 255, 255, 0.98);
    --border-card: rgba(203, 213, 225, 0.9);
    --border-divider: rgba(226, 232, 240, 0.8);
    --text-primary: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --accent-primary: #0284c7;
    --accent-gradient: linear-gradient(135deg, #0284c7 0%, #06b6d4 50%, #2563eb 100%);
    --shadow-card: 0 20px 48px -8px rgba(15, 23, 42, 0.12), 0 4px 12px -2px rgba(15, 23, 42, 0.06);
    --tile-bg: rgba(255, 255, 255, 0.94);
    --tile-border: rgba(203, 213, 225, 0.95);
    --wp-dim: 0.35;
    --wp-blur: 10px;
}
```

此外，在生产级工作台变体原型 `spd_frontend_design_variants.html:12-54` 中补充了针对业务表单、工作台网格与警示标签的语义 Tokens：
- `--bg-surface`: 浅色 `#ffffff`，深色 `#0f172a`
- `--bg-surface-elevated`: 浅色 `#ffffff`，深色 `#1e293b`
- `--bg-glass`: 浅色 `rgba(255, 255, 255, 0.78)`，深色 `rgba(15, 23, 42, 0.78)`
- `--color-success`: `#10b981` (浅色文本 `#059669`, 浅底 `rgba(16, 185, 129, 0.12)`)
- `--color-warning`: `#f59e0b` (浅色文本 `#d97706`, 浅底 `rgba(245, 158, 11, 0.12)`)
- `--color-danger`: `#ef4444` (浅色文本 `#dc2626`, 浅底 `rgba(239, 68, 68, 0.12)`)
- `--shadow-sm`: `0 1px 3px rgba(15, 23, 42, 0.04)`（深色 `rgba(0, 0, 0, 0.3)`）
- `--shadow-md`: `0 4px 16px -2px rgba(15, 23, 42, 0.06)`（深色 `rgba(0, 0, 0, 0.4)`）
- `--shadow-glass`: `0 8px 32px 0 rgba(15, 23, 42, 0.08)`（深色 `rgba(0, 0, 0, 0.5)`）
- `--radius-sm`: `6px`，`--radius-md`: `10px`，`--radius-lg`: `16px`
- `--ease-out`: `cubic-bezier(0.23, 1, 0.32, 1)`

### 1.3 现代医疗模态登录中枢观测 (`docs/design/spd_integrated_showcase_demo.html:1533-1795 & 2067-2130 & 3016-3114`)
原型的登录界面不是传统单调页面，而是通过全屏毛玻璃模态弹窗（Healthcare Modal Auth Card）与全景数字展厅紧密联动：
1. **DOM 层级结构**：
   - `.spd-auth-backdrop` (遮罩背景，全屏固定，`background: rgba(15, 23, 42, 0.70)`, `backdrop-filter: blur(20px)`)
     - `.spd-auth-card` (卡片容器，定宽 440px，padding 28px，radius 20px，`border: 1px solid var(--border-card)`, `backdrop-filter: blur(24px)`)
       - `.spd-auth-header`:
         - `.spd-auth-brand`: 医疗十字 Logo 矢量 SVG (28x28px)，主标题 `医慧通行 · 统一安全接入中枢` (15px/700)，副标题 `医院 SPD 医疗物资全链管理与智能体协同平台` (11px/var(--text-muted))
         - `.spd-auth-close`: 圆形关闭按钮 (28x28px)，内含关闭叉号 SVG，hover 变为警示红底
       - `.spd-auth-form` (表单区域):
         - 字段 1：工号输入框（标签 `医护工号 / 登录账号`，前缀 User 图标，占位符 `请输入医护人员工号 (如 SPD-ADMIN-01)`）
         - 字段 2：密钥输入框（标签 `系统访问密钥`，前缀 Lock 图标，后缀 Eye 图标切换按钮 `#btn-toggle-pwd`，实现 `type="password"` 与 `type="text"` 的无刷新切换）
         - 操作行：记住工作台会话复选框（`#login-remember`，`accent-color: #38bdf8`）与 `安全证书协助` 链接
         - 提交按钮：`#btn-submit-login` (全宽 46px，背景 `var(--accent-primary)`，圆角 10px，阴影 `0 4px 14px rgba(2, 132, 199, 0.4)`)，点击触发全屏双环脉冲微加载指示器
       - `.spd-auth-divider` (横向分割线，中间文字 `或选择演示角色一键免密体验`)
       - `.spd-role-fast-grid` (角色一键免密网格):
         - 耗材科管理 (`consumable`): 工号 `SPD-CONSUMABLE-01`，图标物资立方体 Package
         - 临床二级库 (`nurse`): 工号 `SPD-NURSE-06`，图标心电脉冲 Activity
         - 财务合规审计 (`finance`): 工号 `SPD-AUDIT-08`，图标财务天平 Balance
         - 在系统完整角色体系中，还涵盖信息科管理员 (`admin` / `sys_admin`，工号 `SPD-ADMIN-01`，最高全院权限) 与设备科管理 (`equip`，工号 `SPD-EQUIP-02`)

### 1.4 全局展厅外壳与导航栏观测 (`docs/design/spd_integrated_showcase_demo.html:155-300 & 1821-1884`)
1. **顶部通透悬浮导航栏 (`.top-float-nav`)**：
   - 物理定位：`position: fixed; top: 20px; left: 28px; right: 28px; z-index: 100`
   - 左侧品牌徽章 (`.brand-badge`)：内置 24x24 渐变蓝 Logo 与标题 `医院医疗物资全链路管理系统 · 统一双模态展厅`
   - 中间分段胶囊切换器 (`.mode-segmented-pill`)：`360° 全域轨道拓扑` (`#btn-mode-orbital`) 与 `3D 弧面全链流光` (`#btn-mode-tilted`)
   - 右侧操作胶囊区 (`.nav-actions`)：
     - 背景音乐开关与音量滑动弹出层 (`.nav-audio-group`)：快捷键 `M` 联动，支持音量 `0.0 ~ 1.0` 调节
     - 壁纸工坊抽屉开关 (`#btn-toggle-wallpaper`)：动态计数展示 `壁纸工坊 (39)`
     - 纯享模式开关 (`#btn-enter-zen`)：一键隐藏全部前景卡片，进入 100% 纯净壁纸态
     - 医慧通行登录入口 (`#btn-open-login`)：唤起认证模态弹窗
     - 工作台跳转链接 (`#btn-back-variants`)：直连生产级工作台视图
     - 亮暗主题切换圆形按钮 (`#theme-toggle-btn`)
2. **纯享模式退出微条 (`.zen-control-bar`)**：
   - 定位：`position: fixed; top: 24px; right: 24px; z-index: 1000`
   - 包含独立音乐切换微胶囊与 `退出纯享 (ESC)` 微胶囊
   - 全屏点击除微条外的任意空白区域均可瞬时退出
3. **桌面极简数字时钟 (`.desktop-clock-widget`)**：
   - 定位：顶部居中 `top: 76px; left: 50%; transform: translateX(-50%)`
   - 时间文字：`54px; font-weight: 200; font-variant-numeric: tabular-nums`，消除数字跳动造成的抖动；日期显示：`YYYY年M月D日 星期X`
4. **全屏文件拖拽即映入 (`.drag-drop-overlay`)**：
   - 监测 `dragenter` / `dragleave` / `dragover` / `drop`，支持把用户本地视频或图片即时映入展厅背景

### 1.5 核心微动效组件观测
1. **流体笔刷核心入口按钮 (`.spd-fluid-btn`)**：
   - 尺寸：`width: 250px; height: 54px; font-weight: 700; letter-spacing: 1.5px`
   - 内部由两组半圆弧线 (`.spd-fluid-line`) 与两组笔刷流体块 (`.spd-fluid-drow1`, `.spd-fluid-drow2`) 构成
   - hover 时文字字间距扩展至 `4px`，四个边角的笔刷关键帧动画按毫秒级时序交错流动 (`spdDrow1` ~ `spdDrow5`)，极具现代设计冲击力
2. **双环脉冲微加载指示器 (`.spd-spinner-box`)**：
   - 外环 `.spd-spinner-outer-ring`: 64x64px，`border-top-color: #38bdf8`，以 `0.9s` 线性匀速旋转
   - 内核脉冲 `.spd-spinner-inner-pulse`: 承载矢量星标，以 `1.6s` 缓动循环缩放，配合状态文字提示当前业务阶段（如 `正在以 [耗材科管理员] 身份建立双向通道...`、`正在核验 CA 数字证书与安全令牌...`）
3. **动态底线微交互搜索框 (`.spd-search-form`)**：
   - 采用 `:before` 伪元素实现从中心向两侧展开的动态下划线（`transform: scaleX(0)` 到 `scaleX(1)`）
   - 当输入框有内容时，通过 CSS 选择器 `:not(:placeholder-shown) ~ .spd-search-reset` 自动浮现一键清空按钮

### 1.6 业务视图与工作台组件观测
在 `spd_interactive_prototype.html` 与 `spd_frontend_design_variants.html` 中，完整定义了各业务视图的 DOM 结构、数据表头、统计指标与操作链路：
1. **产品字典管理视图 (`ProductDictView`)**：
   - 顶部 KPI 卡片网格（4 列）：全院在用产品字典总数（1,284种）、耗材科主库归口物资（860种）、设备科主库归口物资（424种）、注册证临期预警（3种）
   - 双维树形过滤栏：
     - 维度一（主库房主科室）：全部 (1284)、耗材科主库 (860)、设备科主库 (424)
     - 维度二（耗材分类）：普通耗材 (批次管理)、高值耗材 (一物一码专仓)、医疗设备配件
   - 数据表格字段：产品编码、产品名称/规格型号、UDI-DI 基准码、归口主科室、耗材分类、医疗器械注册证号 (到期日)、基准单价、安全库存
2. **普通耗材主库与按需分发视图 (`GeneralMaterialView`)**：
   - 表头包含：入库单号、产品名称、归口主科室、生产批号/有效期至 (标注 FEFO 近效期先出排序)、主库可用余量、主库货位编码、批次效期状态标签、按需分发操作
   - 核心业务按钮：打印主库验收入库单、按需分发至【临床二级库】、转入【高值耗材专仓】(触发拆包赋码锁定)、过期批次硬风控阻断标签
3. **高值耗材专仓一物一码视图 (`HighValueView`)**：
   - 核心字段：高值单品 UDI 唯一序列号 (SN，格式如 `(01)...(17)...(10)...(21)SN...`)、产品名称/规格、来源主库分发单号、批号/有效期、当前专柜位置、单品生命周期状态标签、绑定使用患者(已脱敏)/手术信息
   - 单品状态机：`IN_HIGH_VALUE_WH` (专仓在库) -> `LOCKED` (智能柜锁定) -> `USED_VERIFIED` (已绑定患者核销) -> `RECALLED` (召回冻结)
4. **临床二级库管理视图 (`SecondaryWarehouseView`)**：
   - 涵盖科室：骨科二级库、心内科二级库、手术室二级库
   - 核心字段：所属临床二级库、物资名称、定向归口主科室 (自动分单判定：耗材科/设备科)、批次号/有效期、二级库当前余量、本科室已消耗结算金额、二级库安全库存状态预警（低于下限触发自动申领）
5. **全流程业务链路 6W 物权交接日志视图 (`WorkflowLogView`)**：
   - 8 大业务流转节点时间轴：`1_DICT_REGISTER` -> `2_MAIN_INBOUND` -> `3_MAIN_DISPATCH` -> `4_HIGH_VALUE_CODE` -> `5_SEC_RECEIVE` -> `6_SEC_APPLY` -> `7_CLINICAL_CONSUME` -> `8_FINANCE_AUDIT`
   - 日志表格 6W 要素：Who (交出责任人 -> 接收责任人)、What (物资编码与批次/UDI)、Where (源科室 -> 目标科室)、When (精确时间戳)、Why (流转类型)、Which (财务记账标识：移库不计费 vs 消耗即结算)
6. **财务合规审计与单据打印中心 (`FinancePrintView`)**：
   - KPI 统计指标：本月主库按需分发调拨总额、本月临床二级库实际消耗结算总额、普通耗材 vs 高值耗材消耗占比、耗占比考核达标率 (96.5%)
   - 5 类医院法定四联单据打印模态框：
     - 单据 1：《医院主库采购验收入库单》
     - 单据 2：《医院主库向二级库/高值仓按需分发调拨单》
     - 单据 3：《医院高值耗材一物一码跟台使用核销单》
     - 单据 4：《医院临床二级库物资申领与退库单》
     - 单据 5：《医院财务科月度各科室耗材成本结算汇总单》
   - 核心法定四联责任签字栏：【一联】制单操作人、【二联】主库科室主管、【三联】二级库领用人、【四联】财务科复核（支持背景防伪水印与 `@media print` 样式）

---

## 2. 逻辑推导链 (Logic Chain)

1. **从全局 Tokens 到页面质感的推导**：
   - 原型中采用 `--bg-page: #080c14`、`--bg-card: rgba(15, 23, 42, 0.85)` 及 `--accent-gradient`，配合 `-webkit-backdrop-filter: blur(24px)`，打破了传统 ERP 系统的纯白机械呆板布局。
   - 浅色模式下采用 `--bg-page: #f1f5f9`、`--bg-card: rgba(255, 255, 255, 0.90)` 与天青主色 `--accent-primary: #0284c7`，保持现代医疗设备的高洁通透质感。
   - 推导结论：前端重构必须将此套 CSS 变量完整注入全局样式，任何硬编码色彩（如 `#ffffff`、`#000000`）均会导致主题切换时样式断裂。

2. **从模态登录架构到用户认证流向的推导**：
   - 原型将登录入口做成展厅的模态弹窗（Modal Auth Card），并提供 4 大角色的快捷一键登录通道与工号/密码标准表单。
   - 现有 `frontend/src/views/LoginView.vue` 是一个脱离了展厅背景的旧式全屏居中表单，且集成了与业务不符的用户注册选项卡（医疗系统通常由信息科统一分发工号，不可自由注册）。
   - 推导结论：必须将 `LoginView.vue` 彻底推翻重构为高质感模态卡片结构，并提供可直接无缝嵌入展厅底层的架构，支持 4 大角色一键快速带入对应角色凭证与会话状态。

3. **从业务原型到 Vue 3 组件架构的推导**：
   - 原型中的 7 大业务视图均包含“指标 KPI 卡片”、“状态过滤栏”、“精细化数据表格”与“操作动作抽屉”。
   - 现有 `frontend/src/views/` 下的代码充斥着简易默认 Element Plus 表格，缺乏毛玻璃质感、微边框、分层投影与规范的 SVG 图标。
   - 推导结论：必须按照 `spd_frontend_design_variants.html` 的 Fusion 推荐生产版结构重构各页面，保持统一的卡片面板、操作工具栏与四联单据打印引擎。

4. **从全域禁用 Emoji 到纯矢量 SVG 图标体系的推导**：
   - 原型中所有的图标均定义为 `<svg class="svg-icon" viewBox="0 0 24 24">`，无一处使用 Emoji 字符。
   - 推导结论：在重构代码中，必须建立专门的 SVG 图标库或统一内联 SVG 模板，严格执行 0-Emoji 规范。

---

## 3. 局限与注意事项 (Caveats)

1. **Wallpaper Engine 本地动态壁纸依赖**：
   原型中的 Layer 0 底层直接引用了用户本地的 Steam 动态视频与壁纸图片（如 `E:/SteamLibrary/...`）。在前端无本地 Steam 环境运行时，必须提供高质感的 CSS 渐变光晕背景（`radial-gradient(ellipse at center, #0c4a6e 0%, #080c14 70%)`）作为优雅兜底，确保离线或无视频环境下视觉体验不降级。
2. **三级工作台与展厅的路由跳转关系**：
   原型中展厅展示与工作台多变体通过外部链接（如 `location.href='spd_frontend_design_variants.html'`）跳转。在 Vue 3 单页应用中，应整合为标准 Vue Router 路由切换，支持 `/showcase` 与 `/dict`、`/general` 等工作台视图的平滑切换。
3. **打印样式的浏览器兼容性**：
   四联单据打印组件依赖 `@media print` 规则，需要确保打印时不输出页面背景、操作按钮与侧边栏，仅输出白底黑字的法定四联单据。

---

## 4. 结论 (Conclusion)

通过对 `spd_integrated_showcase_demo.html` 及其关联原型的地毯式排查，现已完全提取：
1. **完整的 Design Tokens 变量体系**（深浅双模态、毛玻璃卡片、边框、分层投影、模糊滤镜）；
2. **医慧通行现代医疗模态登录中枢架构**（440px 模态卡片、工号密码双重验证、密码明暗文切换、4 大角色一键通道、CA 认证双环加载动效）；
3. **全局展厅导航与外壳架构**（顶部浮动胶囊导航、双模态拓扑切换、纯享模式、桌面数字时钟、本地工坊抽屉、背景音乐控制）；
4. **全套业务视图布局规范**（产品字典双维分类、普通耗材主库按需分发、高值专仓一物一码、临床二级库定数申领、6W 物权交接日志流向、财务多科室精算与四联单据打印中心）；
5. **纯矢量 SVG 图标全量清单**（全域 100% 纯矢量 SVG，彻底杜绝 Emoji）。

所有技术指标与设计资产已完全具备向前端实施工程师（Frontend UI Agent）移交并启动逐页面无损重构的标准。

---

## 5. 独立验证方法 (Verification Method)

1. **样式与 Design Tokens 核对**：
   - 打开 `docs/design/spd_integrated_showcase_demo.html` 与 `docs/design/spd_frontend_design_variants.html`；
   - 在浏览器 DevTools 中检查 `:root` 与 `[data-theme="light"]` 的 CSS 变量取值，确认重构后的前端 `src/styles/variables.css` 100% 对应一致。
2. **登录模态中枢功能核对**：
   - 点击顶部导航 `医慧通行` 按钮，弹出 440px 磨砂模态弹窗；
   - 点击眼睛图标，输入框类型在 `password` 与 `text` 之间切换，图标 SVG 同步切换；
   - 点击 4 大角色任意一键通道，输入框即时带入角色工号，触发双环脉冲微加载指示器，并在 600ms 后自动关闭弹窗。
3. **展厅双模态与纯享模式核对**：
   - 点击 `360° 全域轨道拓扑` 与 `3D 弧面全链流光` 胶囊，对应动画与布局平滑切换，未激活的引擎自动 `display: none` 并暂停动画；
   - 点击 `纯享模式` 或按下快捷键 `ESC`，验证前景卡片全部隐去；再次按 `ESC` 或点击空白处顺利退出纯享。
4. **SVG 图标与 0-Emoji 核对**：
   - 在项目源码根目录执行命令搜索：
     ```powershell
     Get-ChildItem -Path "frontend/src" -Recurse -Include *.vue,*.ts,*.css | Select-String -Pattern "[\uD83C-\uDBFF\uDC00-\uDFFF]"
     ```
   - 验证输出为空，证明无任何 Emoji 表情字符。
5. **构建与测试验证**：
   - 进入 `frontend/` 目录运行 `npm run build`，确保 TypeScript 检查 0 错误、0 警告打包成功。

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Design System | CSS Variable Tokens | 定义深色深空与极简白瓷双主题色彩、毛玻璃背景、边框、分层投影与轨道半径 | 页面主题属性 `data-theme` | 全局 CSS 变量即时生效 | 缺失时兜底到 `:root` 深色变量 | `spd_integrated_showcase_demo.html:12-53` |
| 2 | Design System | Fluid Stroke Button | 流体流动笔刷核心入口按钮，支持多段 SVG 笔刷关键帧按序流动 | hover / active 事件 | 边框流动扩展、字间距变宽至 4px | 降级为常规圆角按钮 | `spd_integrated_showcase_demo.html:1097-1354` |
| 3 | Design System | Dual-ring Pulsing Spinner | 全屏双环脉冲微加载指示器，外环旋转内核星标脉冲 | `showSpdSpinner(text)` | 全屏遮罩与带文案的脉冲框 | `hideSpdSpinner()` 强制隐藏 | `spd_integrated_showcase_demo.html:1358-1425` |
| 4 | Design System | Dynamic Underline Search | 动态底线微交互搜索框，光标聚焦时底线下划线从中心向两侧铺开 | focus / input 事件 | 边框变色、下划线展开、清除叉号浮现 | 输入为空时叉号自动隐藏 | `spd_integrated_showcase_demo.html:1429-1529` |
| 5 | Auth Card | Healthcare Modal Auth Card | 医慧通行现代医疗模态登录中枢，440px 毛玻璃卡片 | 用户点击 `医慧通行` 或按需弹出 | 模态浮窗居中展现 | 点击背景遮罩或 ESC 自动退出 | `spd_integrated_showcase_demo.html:1533-1795` |
| 6 | Auth Card | Password Visibility Toggle | 密码输入框明暗文一键无刷新切换 | 点击 `#btn-toggle-pwd` | `type` 在 `password` 与 `text` 切换，SVG 眼睛图标切换 | 无 | `spd_integrated_showcase_demo.html:2096-2099` |
| 7 | Auth Card | Fast Role Access Channel | 院内 4 大角色一键免密接入通道 (耗材科/设备科/二级库/财务科) | 点击对应角色卡片 | 自动填充工号、触发微加载动画并登入 | 未知角色回退到常规表单 | `spd_integrated_showcase_demo.html:2114-2127` |
| 8 | Showcase Shell | Segmented View Switcher | 双模态书签切换胶囊 (360° 轨道 vs 3D 弧面圆柱) | 点击对应模式胶囊按钮 | 切换活动视图，暂停非活动视图 CSS 动画 | 默认回退至 `orbital` 模式 | `spd_integrated_showcase_demo.html:1830-1839` |
| 9 | Showcase Shell | Zen Pure Mode | 纯享壁纸态，彻底隐藏所有前景卡片，仅留右上角控制条 | 点击 `纯享模式` 或快捷键 ESC | `body.zen-pure-mode` 激活 | 再次按 ESC 或点击屏幕任意空白退出 | `spd_integrated_showcase_demo.html:2731-2785` |
| 10 | Showcase Shell | Synchronized Audio Controller | 动态壁纸原生 MP4 音频与场景外挂音频互斥同步播放 | 快捷键 `M`、音量滑块输入 | 开启/静音音轨、调节系统增益音量 | 浏览器自动播放拦截时静默等待交互 | `spd_integrated_showcase_demo.html:2801-2935` |
| 11 | Showcase Shell | Desktop Digital Clock | 桌面极简实时数字时钟小部件，精确同步本地时间 | 定时器每 1000ms 刷新 | 时间（时分秒）与年月日星期展示 | 无 | `spd_integrated_showcase_demo.html:2937-2979` |
| 12 | Showcase Shell | Wallpaper Workshop Drawer | 本地 39 款壁纸工坊底部抽屉，支持分类与动态搜索过滤 | 点击工坊按钮、输入搜索词、分类Tab | 网格渲染壁纸缩略图与分辨率角标 | 搜索无结果时展现空状态 | `spd_integrated_showcase_demo.html:1998-2050` |
| 13 | Showcase Shell | Media Drag & Drop Overlay | 全屏媒体文件拖拽即映入全屏壁纸 | 拖拽文件到浏览器窗口 | 蓝色虚线遮罩展开，释放后立即满铺播放 | 非媒体文件忽略不处理 | `spd_integrated_showcase_demo.html:2668-2724` |
| 14 | Business View | Product Dict Double Dimension | 产品字典双维分类（主库房主科室 + 耗材属性分类） | 点击维度树叶子节点 | 联动筛选字典列表，展示注册证到期日 | 筛选无结果表格显示暂无数据 | `spd_interactive_prototype.html:498-584` |
| 15 | Business View | Main Stock & FEFO Dispatch | 普通耗材主库批次管理与按需分发，FEFO 近效期先出排序 | 点击按需分发、调拨出库 | 生成调拨单据，扣减主库余量（移库不计费） | 过期批次显示硬锁定禁止分发 | `spd_interactive_prototype.html:587-643` |
| 16 | Business View | High-Value UDI Serialization | 高值专仓一物一码单品管控，拆包赋码与智能柜锁定 | 扫入单品唯一 UDI 序列号 | 追踪由量到码流向，绑定患者脱敏信息 | 已召回批次展示冻结标签阻断使用 | `spd_interactive_prototype.html:646-694` |
| 17 | Business View | Secondary Warehouse Requisition | 临床二级库管理，定数包补货与自然语言问答极速申领 | 点击申领、输入申领数量 | 自动判定归口主科室分单审批 | 余量低于安全下限触发黄色告警 | `spd_interactive_prototype.html:698-741` |
| 18 | Business View | 6W Traceability Logs | 全流程 6W 物权交接流转台账（8大标准业务节点穿透） | 筛选流转节点或关键字 | 穿透展示人/物/时间/流向及记账状态 | 异常流转日志触发合规审计预警 | `spd_interactive_prototype.html:744-806` |
| 19 | Business View | Four-Part Medical Voucher Print | 医院标准 5 类法定四联责任签字单据打印预览 | 点击打印单据按钮 | 弹出带四联责任人签字栏与防伪水印弹窗 | 打印模式下自动隐藏操作外壳 | `spd_frontend_design_variants.html:1219-1291` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Zen Pure Mode & ESC Key | 用户同时打开壁纸工坊抽屉与登录模态框时按下 ESC 键 | 遵循优先级栈严格单层退出：首选关闭登录模态框；再次按 ESC 关闭壁纸抽屉；最后按 ESC 退出纯享模式，避免一键误关多个图层 |
| 2 | 3D Cylinder GPU Load | 切换到 360° 轨道模式时，3D 弧面圆柱处于隐藏状态 | 必须施加 `display: none !important` 且其动画类必须强制 `animation-play-state: paused !important`，杜绝后台切片在 GPU 复合层空转消耗显存 |
| 3 | Audio Auto-play Policy | 用户首次打开页面未与 DOM 产生交互时尝试播放背景音乐 | 原型在 `.play()` 上捕获 `.catch(e => console.log("Waiting interaction"))`，静默等待用户首次点击任意按钮后自动恢复播放 |
| 4 | Drag & Drop Hierarchy | 鼠标拖拽文件在窗口内部元素（如文本、按钮）之间划过 | 原型设置了 `dragCounter` 计数器，`dragenter` 自增，`dragleave` 自减，仅当 `dragCounter <= 0` 时关闭遮罩，彻底杜绝遮罩闪烁跳动 |
| 5 | Dynamic Underline Input Reset | 在搜索框输入长文本后点击右侧清空叉号按钮 | 叉号按钮在 `:placeholder-shown` 时 `opacity: 0; visibility: hidden`，有输入时显现；点击后重置 `value = ""`，重新计算网格，并自动保持输入焦点 `focus()` |
| 6 | Clock Tabular Numbers | 时钟从 `11:59:59` 跳动到 `12:00:00` | 字体使用 `font-variant-numeric: tabular-nums`，确保等宽数字排版，避免不同数字宽度变动导致时钟外框微小横向抖动 |
| 7 | Multi-theme Card Borders | 在暗黑模式切换到纯白明亮模式时 | 边框从半透明白 `rgba(255, 255, 255, 0.14)` 平滑过渡到浅灰青 `rgba(203, 213, 225, 0.9)`，文字层级保持与背景超过 7:1 的 WCAG AAA 对比度 |
| 8 | Password Input Toggle | 切换明文时输入框已有长文本 | 仅变更 DOM 的 `type` 属性，光标与文本内容保持原位不刷新，尾部 eye 图标即时替换为带斜划线的睁眼/闭眼矢量路径 |
| 9 | Wallpaper Aspect Ratio | 选取超宽 21:9 视频或 4:3 老旧显示器屏幕 | 强制设置 `object-fit: cover !important; object-position: center center !important`，确保无论何种视口比例均 100% 满铺消除黑边 |
| 10 | Strict Emoji Prevention | 用户或接口返回带有 Emoji 的物料描述文本 | 页面各层级 CSS 与渲染代码全域禁用 Emoji，所有状态和类型统一采用 Element Plus 语义化 Tag 与矢量 SVG 渲染 |

---

## 6. 全量矢量 SVG 图标清单 (SVG Icon Inventory)

> **铁律检验**：全域 100% 采用纯矢量内联 `<svg>`，严禁任何 Emoji 表情字符。所有 SVG 图标统一遵循 `viewBox="0 0 24 24"`、`fill="none"`、`stroke="currentColor"`、`stroke-width="1.8"`、`stroke-linecap="round"`、`stroke-linejoin="round"`。

1. **医疗系统品牌 Logo 图标 (Medical Cross Brand)**：
   `viewBox="0 0 24 24"` -> `<path d="M12 2v20M2 12h20M7 7l10 10M17 7L7 17"></path>`
2. **360° 轨道拓扑模式图标 (Orbital Mode)**：
   `viewBox="0 0 24 24"` -> `<circle cx="12" cy="12" r="9"></circle><path d="M12 3a9 9 0 0 1 9 9M3 12a9 9 0 0 1 9-9"></path>`
3. **3D 弧面圆柱流光模式图标 (Tilted Grid Mode)**：
   `viewBox="0 0 24 24"` -> `<rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M3 9h18M3 15h18M9 3v18M15 3v18"></path>`
4. **音频开启图标 (Audio On)**：
   `viewBox="0 0 24 24"` -> `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>`
5. **音频静音图标 (Audio Muted)**：
   `viewBox="0 0 24 24"` -> `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line>`
6. **壁纸工坊画廊图标 (Wallpaper Image Gallery)**：
   `viewBox="0 0 24 24"` -> `<rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline>`
7. **纯享模式眼睛图标 (Zen Pure Eye)**：
   `viewBox="0 0 24 24"` -> `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>`
8. **密码切换闭眼图标 (Password Eye Slash)**：
   `viewBox="0 0 24 24"` -> `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>`
9. **医护工号身份图标 (User Silhouette)**：
   `viewBox="0 0 24 24"` -> `<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>`
10. **安全访问密码锁图标 (Lock Padlock)**：
    `viewBox="0 0 24 24"` -> `<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path>`
11. **关闭与退出叉号图标 (Close Cross)**：
    `viewBox="0 0 24 24"` -> `<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>`
12. **搜索放大镜图标 (Search Magnifier)**：
    `viewBox="0 0 24 24"` -> `<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>`
13. **时钟表盘图标 (Clock Face)**：
    `viewBox="0 0 24 24"` -> `<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>`
14. **本地文件选择与上传图标 (Upload Tray)**：
    `viewBox="0 0 24 24"` -> `<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"></path>`
15. **耗材科管理员角色图标 (Cube Package)**：
    `viewBox="0 0 24 24"` -> `<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>`
16. **临床二级库角色图标 (ECG Heartbeat Pulse)**：
    `viewBox="0 0 24 24"` -> `<path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>`
17. **财务科合规审计角色图标 (Financial Balance Scale)**：
    `viewBox="0 0 24 24"` -> `<line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>`
18. **亮暗主题太阳图标 (Sun Rays)**：
    `viewBox="0 0 24 24"` -> `<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>`
19. **法定单据四联打印机图标 (Printer Voucher)**：
    `viewBox="0 0 24 24"` -> `<polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect>`
20. **智能体协同机器人图标 (Agent Robot)**：
    `viewBox="0 0 24 24"` -> `<rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4M8 16h0.01M16 16h0.01"></path>`
21. **全流程 6W 审计安全盾牌图标 (Security Shield)**：
    `viewBox="0 0 24 24"` -> `<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>`
22. **一物一码日历核销图标 (Calendar Check)**：
    `viewBox="0 0 24 24"` -> `<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>`
23. **产品字典管理书本图标 (Book Dictionary)**：
    `viewBox="0 0 24 24"` -> `<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>`
24. **高值专仓保险箱图标 (High-Value Safe Box)**：
    `viewBox="0 0 24 24"` -> `<rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>`
25. **临床二级库房房屋图标 (Secondary Department Room)**：
    `viewBox="0 0 24 24"` -> `<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>`
26. **流转日志列表图标 (Workflow Log List)**：
    `viewBox="0 0 24 24"` -> `<line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line>`
27. **财务统计柱状图图标 (Stats Bar Chart)**：
    `viewBox="0 0 24 24"` -> `<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>`
