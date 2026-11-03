# Project: 医院医疗物资数字化展厅（Showcase）与高质感全域业务视图全面重构

## Architecture
- **Framework**: Vue 3.5.13 + Vite 5.4.11 + TypeScript 5.7.2 + Pinia 2.3.0 + Element Plus 2.9.1
- **Visual Design Standard**: 严格对齐 `docs/design/spd_integrated_showcase_demo.html` 权威原型规范：
  - 双主题 Design Tokens（`:root` 深空暗色 `--bg-page: #080c14`, `--bg-card: rgba(15, 23, 42, 0.85)`; `[data-theme="light"]` 极简白瓷 `--bg-page: #f1f5f9`, `--bg-card: rgba(255, 255, 255, 0.90)`）
  - 全屏 4K 动态壁纸引擎（直连 `wallpapers_manifest.js` 41款本地壁纸）+ Layer 1 `--wp-dim` 调光与 `--wp-blur` 高斯模糊
  - 顶部悬浮胶囊导航栏（`.top-float-nav`）：双模态徽标、全域轨道拓扑/3D弧面流光切换胶囊、环境音效控制、壁纸工坊抽屉、纯享模式、医慧通行模态中枢入口、工作台原型跳转、深浅主题切换
  - 极简桌面数字时钟（`.desktop-clock-widget`，`tabular-nums` 防抖）
  - 中央毛玻璃 Hero 核心舱（智慧医疗全链穿透、流体笔刷核心入口按钮 `.spd-fluid-btn`、三大合规金色/蓝色徽标）
  - 医慧通行现代医疗安全模态登录中枢（`.spd-auth-backdrop` + `.spd-auth-card`）：440px 磨砂玻璃卡片、工号/密码双重校验、密码明暗文切换、会话记忆、4大演示角色一键免密通道、CA认证双环脉冲微加载指示器
  - 3D 弧面立体卡片流（#01 ~ #08 业务流向卡片 + 3 大合规指标卡片）与 360° 全域轨道拓扑系统
  - 全域统一业务视图延展：所有 7 大业务视图（产品字典、普通耗材、高值专仓、二级库、6W日志、财务打印、采购协同）作为 Demo 设计语言的自然延展，彻底推翻白底灰边传统模板，全域应用毛玻璃微边框卡片、胶囊控件与 Monospace 医疗数据排版
- **Icon Standard**: 全域严格禁用 Emoji，100% 采用内联矢量 SVG 或原生图标组件。
- **Data Flow & Fault Tolerance**: 前端状态由 Pinia（`userStore`, `showcaseStore`, `themeStore`）统一调度，通过 Axios 拦截器注入规范的 `X-Mock-User`、`X-Mock-Role` 与 `Authorization: Bearer <token>` 请求头。连接后端真实 FastAPI 端点，同时内置健壮的本地结构化 Mock 兜底，确保在离线或单机演示时 100% 不崩溃。
- **Testing & Verification**: Playwright 端到端无头浏览器测试脚本自动截取实机大图归档至 `tests/screenshots/[timestamp]_[page_name].png`，确保 0 控制台未捕获报错，TypeScript 编译 0 错误 0 警告。

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Global Design System & Tokens | 导入深空/极简白瓷双主题变量、毛玻璃(--bg-card)、微边框、分层阴影、流体笔刷、双环脉冲微动效，全域 0 Emoji | M1 | spd_integrated_showcase_demo.html |
| 2 | Wallpaper Engine & 41 Manifest | 动态壁纸图库(wallpapers_manifest.js 41款)、调光模糊、环境背景音效控制、全屏文件拖拽即映入 | M1 | demo layer 0 & 1 |
| 3 | Healthcare Modal Auth Card | 医慧通行 440px 模态登录卡片、工号密码表单、密码明暗文切换、记住会话、CA双环认证加载、4大角色免密一键登入 | M2 | demo auth card |
| 4 | Auth Session & Backend Alignment | 对齐后端真实种子账号(mgr_consumable, mgr_equip, nurse_cardio, mgr_finance)，修复请求头注入与 Token 机制 | M2 | backend seed audit |
| 5 | Top Floating Capsule Nav & Clock | 顶部悬浮胶囊导航栏、品牌徽标、全域轨道/3D弧面切换胶囊、音乐控制、壁纸工坊(41)、纯享模式、桌面数字时钟 | M3 | demo top-float-nav |
| 6 | Central Glassmorphism Hero Core | 智慧医疗全链穿透、流体笔刷按钮(.spd-fluid-btn)、进入纯享壁纸态、三大医疗合规徽标卡片 | M3 | demo hero section |
| 7 | Dual-Mode 3D Card Engine | 360° 全域轨道拓扑系统与 3D 弧面立体 16-切片卡片流(#01 ~ #08 业务卡片 + 3 大合规指标) | M3 | demo orbital & tilted |
| 8 | Product Dict View Refactor | 产品字典管理视图毛玻璃重构、KPI指标卡片、双树面板(仓库树+分类树)、表格动态行高与操作抽屉 | M4 | demo & variants |
| 9 | General Material View Refactor | 普通耗材主库管理毛玻璃重构、FEFO近效期排序先出、按需分发调拨、两阶段确认弹窗 | M4 | demo & variants |
| 10 | High Value Warehouse Refactor | 高值专仓一物一码单品管理毛玻璃重构、智能柜拆包赋码锁定、扫码核销绑定住院号脱敏展示 | M4 | demo & variants |
| 11 | Secondary Warehouse View Refactor | 临床二级库毛玻璃重构、骨科/心内科病区切换、安全水位预警、定数包自动申领与调拨 | M4 | demo & variants |
| 12 | Workflow 6W Log Timeline Refactor | 8大流转节点时间轴图谱、6W要素表格(Who/What/Where/When/Why/Which)、100%穿透溯源 | M4 | demo & variants |
| 13 | Finance Print & Audit View Refactor | 多科室耗材精算大盘、耗占比考核、5类医院法定四联签字单据打印引擎(@media print) | M4 | demo & variants |
| 14 | Supplier Purchase View Refactor | 供应商资质准入横幅、采购订单协同流向、发货与验收入库流转 | M4 | demo & variants |
| 15 | Playwright E2E & Screenshot Capture | 编写并运行自动化测试，逐页面捕获无头浏览器全屏高保真截图存入 tests/screenshots/，验证 0 Console Error | M5 | QA & Harness |
| 16 | TypeScript & Production Build Check | 严格类型检查与 Vite 生产打包验证(npm run build)，确保 0 error 0 warning，消除单包超标警告 | M5 | QA & Harness |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | 全局设计系统与壁纸引擎基础设施 | `frontend/src/styles/theme.css`, `frontend/src/styles/main.css`, `frontend/public/wallpapers_manifest.js`, 全域 SVG 图标体系 | none | DONE |
| M2 | 医慧通行现代医疗安全模态登录中枢 | `frontend/src/components/auth/HealthcareAuthModal.vue`, `frontend/src/stores/userStore.ts`, `frontend/src/api/request.ts` | M1 | DONE |
| M3 | 数字化展厅双模态全景门户与胶囊导航 | `frontend/src/views/ShowcaseView.vue`, `frontend/src/components/showcase/*` (顶部悬浮导航, 3D弧面切片, 360轨道, Hero核心舱, 壁纸工坊抽屉) | M1, M2 | DONE |
| M4 | 全域业务视图 Demo 风格高质感自然延展与 RBAC 动态过滤 | 重构 `MainLayout.vue`, `ProductDictView.vue`, `GeneralMaterialView.vue`, `HighValueView.vue`, `SecondaryWarehouseView.vue`, `WorkflowLogView.vue`, `FinancePrintView.vue`, `SupplierPurchaseView.vue` | M1, M2, M3 | DONE |
| M5 | 编译构建压测、Playwright 自动化截图与验收交付 | `tests/e2e/showcase_regression.spec.ts`, `tests/e2e/m4_business_views_rbac.js`, `tests/screenshots/*`, 生产打包构建 `npm run build` | M1, M2, M3, M4 | IN_PROGRESS |

---

## Interface Contracts

### 1. `HealthcareAuthModal.vue` ↔ `userStore.ts`
- **Method**: `userStore.loginAsRole(roleKey: 'consumable' | 'equip' | 'nurse' | 'finance' | 'admin') => Promise<boolean>`
- **Method**: `userStore.login(username: string, password?: string) => Promise<boolean>`
- **State**: `userStore.isLoggedIn: boolean`, `userStore.currentUser: UserProfile`, `userStore.token: string`
- **Events**: `@success`: 登录成功触发，展示 CA 认证脉冲微动效后平滑隐藏模态框并跳转目标视图。

### 2. `ShowcaseView.vue` ↔ `showcaseStore.ts`
- **State**:
  - `currentMode: 'orbital' | 'tilted'` (360° 环形轨道 vs. 3D 弧面立体切片)
  - `isZenMode: boolean` (纯享壁纸态，隐藏一切前景卡片)
  - `activeWallpaperId: string` (当前选中的 41 款壁纸索引)
  - `isWallpaperDrawerOpen: boolean` (壁纸工坊抽屉开关)
  - `isAudioPlaying: boolean`, `audioVolume: number` (环境音效控制)
- **Actions**:
  - `toggleMode()`: 双模态平滑切换
  - `setZenMode(val: boolean)`: 切换纯享壁纸态
  - `changeWallpaper(wpItem: WallpaperItem)`: 即时更替全屏背景

### 3. Business Views ↔ Backend API & High-Resilience Fallback
- **Contract Format**: `{ code: 200, msg: string, data: T }`
- **Headers Injection**:
  - `Authorization: Bearer <token>`
  - `X-Mock-User: <username>`
  - `X-Mock-Role: <role>`
- **Fallback**: 若真实 API 请求异常或超时（15s），自动回退至本地完整结构化 Mock 业务数据，确保 UI 在任何环境下 100% 稳健展现。

---

## Code Layout
- `frontend/src/styles/theme.css`: 全量 Design Tokens（包含深空与极简白瓷双主题、壁纸调光滤镜、卡片与边框变量、微动效关键帧）
- `frontend/src/styles/main.css`: 全局重置与排版规范，Monospace 数字字体类
- `frontend/src/components/common/SvgIcon.vue`: 统一纯矢量内联 SVG 图标组件
- `frontend/src/components/auth/HealthcareAuthModal.vue`: 440px 医慧通行现代医疗模态登录卡片与角色一键接入网格
- `frontend/src/components/showcase/`:
  - `TopFloatNav.vue`: 顶部悬浮胶囊导航栏
  - `HeroSection.vue`: 中央毛玻璃 Hero 核心舱与流体笔刷按钮
  - `OrbitalGallery.vue`: 360° 全域轨道拓扑组件
  - `TiltedGrid.vue`: 3D 弧面立体切片卡片流
  - `WallpaperDrawer.vue`: 41 款壁纸工坊抽屉面板
  - `DesktopClock.vue`: 极简桌面数字时钟小部件
  - `ZenControlBar.vue`: 纯享模式控制微条
- `frontend/src/views/ShowcaseView.vue`: 数字化展厅主门户视图（整合上述展厅全量组件）
- `frontend/src/views/`: 各重构后的业务视图文件，包含全毛玻璃卡片与统一微边框设计
- `tests/e2e/showcase_regression.spec.ts`: Playwright 自动化回环测试脚本
- `tests/screenshots/`: 归档所有页面在深色/浅色、登录模态、展厅与各业务视图的实机截图凭据
