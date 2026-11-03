## 2026-11-02T13:25:58Z
You are worker_m3, working as Showcase Portal & 3D Dual-Mode Engine Worker.
Your working directory is: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\worker_m3
You MUST read ORIGINAL_REQUEST.md first at: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\ORIGINAL_REQUEST.md
Also read PROJECT.md at: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\orchestrator\PROJECT.md
Also read DISPATCH.md at: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\orchestrator\DISPATCH.md
Read the authoritative spec miner handoff at: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\teamwork_spec_miner_survey_1\handoff.md
Read the prototype source: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\docs\design\spd_integrated_showcase_demo.html

Mission:
Implement Milestone M3: 数字化展厅双模态全景门户与胶囊导航 (ShowcaseView, TopFloatNav, HeroSection, OrbitalGallery, TiltedGrid, WallpaperDrawer, DesktopClock, ZenControlBar, showcaseStore, router configuration).

File Ownership:
- frontend/src/views/ShowcaseView.vue
- frontend/src/components/showcase/TopFloatNav.vue
- frontend/src/components/showcase/HeroSection.vue
- frontend/src/components/showcase/OrbitalGallery.vue
- frontend/src/components/showcase/TiltedGrid.vue
- frontend/src/components/showcase/WallpaperDrawer.vue
- frontend/src/components/showcase/DesktopClock.vue
- frontend/src/components/showcase/ZenControlBar.vue
- frontend/src/stores/showcaseStore.ts
- frontend/src/router/index.ts

Detailed Requirements:
1. frontend/src/stores/showcaseStore.ts:
   - State: currentMode ('orbital' | 'tilted'), isZenMode, isLoginModalOpen, isWallpaperDrawerOpen, activeWallpaper (id, title, src, type, thumb), isAudioPlaying, audioVolume, wallpapers (loaded from window.WALLPAPERS_MANIFEST or /wallpapers_manifest.js).
   - Actions: toggleMode, setZenMode, openLoginModal, closeLoginModal, toggleWallpaperDrawer, selectWallpaper, toggleAudio, setAudioVolume.
2. Components in frontend/src/components/showcase/:
   - TopFloatNav.vue:
     * Fixed top capsule navigation: Left brand logo SvgIcon + title "医院医疗物资全链路管理系统 · 统一双模态展厅".
     * Center segmented capsule pill (#mode-segmented-pill): "#btn-mode-orbital" (360° 全域轨道拓扑) and "#btn-mode-tilted" (3D 弧面全链流光).
     * Right actions: Audio button + volume popup, Wallpaper workshop button "壁纸工坊 (41)", Pure zen mode button "#btn-enter-zen", Healthcare auth button "#btn-open-login" (triggers showcaseStore.openLoginModal), Workbench link "#btn-back-variants", Theme toggle "#theme-toggle-btn".
   - HeroSection.vue:
     * Glassmorphism central hero core: Subtitle "智慧医疗 物资全链", Title "数字展厅 · 全景穿透", 3 compliance badges (100% 审计穿透, 一物一码单品, 移库不计费).
     * Action buttons: Fluid brush button .spd-fluid-btn ("进入三级角色工作台 ENTRY"), "进入纯享壁纸态", "选图换视频" (opens wallpaper drawer).
   - OrbitalGallery.vue:
     * 360° circular orbital topology system with rotating cards, smooth CSS transform animations, card hover glow and click handlers.
   - TiltedGrid.vue:
     * 3D arc-curved tilted card stream with #01 ~ #08 business cards + 3 compliance cards.
   - WallpaperDrawer.vue:
     * Right slide-in drawer with 41 wallpapers, category filter tabs (医疗极简, 赛博光影, 自然沉思, 深空星河), thumbnail cards, click to change wallpaper immediately.
   - DesktopClock.vue:
     * Tabular-nums font-mono time (HH:mm:ss) and date (YYYY年M月D日 星期X) anti-jitter clock.
   - ZenControlBar.vue:
     * Minimal floating bar at top-right in zen mode: audio toggle, exit button (ESC).
3. frontend/src/views/ShowcaseView.vue:
   - Orchestrates Layer 0 (wallpaper/video), Layer 1 (dimmer with --wp-dim and --wp-blur), DesktopClock, TopFloatNav, HeroSection, OrbitalGallery (v-show="currentMode === 'orbital'"), TiltedGrid (v-show="currentMode === 'tilted'"), WallpaperDrawer, ZenControlBar, and HealthcareAuthModal (v-model="showcaseStore.isLoginModalOpen").
   - ESC key handler: if login modal is open, close login modal; else if zen mode, exit zen mode; else if wallpaper drawer is open, close drawer.
4. frontend/src/router/index.ts:
   - Add route `/showcase` -> `ShowcaseView.vue`.
   - Update navigation guard so that `/showcase` is accessible without login redirection (default public showcase portal).
   - Make `/` redirect to `/showcase` or allow smooth navigation to `/dict`.
5. Build Verification:
   - Run `npm --prefix frontend run build` to confirm 0 error, 0 warning.
   - Verify 0 Emoji.
   - All functions 100% covered with standardized Chinese comments (@param, @returns, @route, @throws).


## 2026-11-02T13:28:32Z
Context: 收到用户关于 RBAC 细粒度角色权限隔离的最高业务铁律
Content: 用户严厉指示：各角色进入系统后，菜单和功能绝对不能全部一样！
1. 侧边栏/导航菜单必须根据 RBAC can_view 严格动态过滤：
   - sys_admin (信息科): 拥有全模块全权；
   - secondary_user (临床二级库): 仅能看到【二级库管理】与【高值耗材扫码核销】，字典、主库、财务、日志严格隐藏；
   - finance_auditor (财务科): 仅能看到【统计查询与打印中心】与【全流程日志】，物理库房操作严格隐藏；
   - supplier_user (供应商): 仅能看到【采购与供应商协同】；
   - 耗材科主管 / 设备科主管: 分别管辖各自归口的主库与产品字典等。
2. 页面内“新增、修改、删除、审核、二次确认、打印”等操作按钮必须严格绑定 userStore.canAction(moduleCode, actionKey) 显隐。
3. 展厅中的“进入工作台”跳转及各角色视角必须严格对齐上述隔离规则。
Action: 请在你的 M3 架构设计与实现中，确保对齐此权限过滤机制。
