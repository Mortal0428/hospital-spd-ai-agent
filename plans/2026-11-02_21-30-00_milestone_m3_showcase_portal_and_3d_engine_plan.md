# Milestone M3 计划文档：数字化展厅双模态全景门户与胶囊导航

- 计划文档路径：plans/2026-11-02_21-30-00_milestone_m3_showcase_portal_and_3d_engine_plan.md
- 记录时间戳：2026-11-02 21:30:00
- 目标目录与文件范围：
  - 前端目标文件：
    - `frontend/src/stores/showcaseStore.ts` (展厅双模态、纯享态、壁纸工坊、音频状态及本地持久化 Pinia 状态库)
    - `frontend/src/components/showcase/DesktopClock.vue` (极简防抖数字时钟小部件，tabular-nums)
    - `frontend/src/components/showcase/ZenControlBar.vue` (纯享模式右上角浮动控制微条，音乐开关与退出按钮)
    - `frontend/src/components/showcase/TopFloatNav.vue` (顶部悬浮通透胶囊导航栏、品牌徽标、双模态切换胶囊、音量滑动弹层、壁纸工坊计数、医慧通行及工作台跳转)
    - `frontend/src/components/showcase/HeroSection.vue` (中央毛玻璃 Hero 核心舱、流体笔刷核心入口按钮、三大医疗合规指标卡)
    - `frontend/src/components/showcase/OrbitalGallery.vue` (360° 环形轨道拓扑系统、极坐标布局与反向自转卡片)
    - `frontend/src/components/showcase/TiltedGrid.vue` (3D 弧面圆柱多切片 60FPS 流光卡片系统)
    - `frontend/src/components/showcase/WallpaperDrawer.vue` (41 款壁纸工坊底部抽屉、分类筛选、搜索框、时钟开关与本地文件选择)
    - `frontend/src/views/ShowcaseView.vue` (主展厅门户视图，整合 Layer 0 媒体层、调光层、拖拽映入遮罩、双模态引擎、Hero 核心及模态登录弹窗)
    - `frontend/src/router/index.ts` (配置 `/showcase` 路由并放行免登录访问，默认根路由优雅适配)
  - 测试与截图范围：
    - TypeScript 类型编译与 Vite 生产打包验证：`npm --prefix frontend run build`
    - 全域 0 Emoji 检查

---

## 核心评估指标

- **可行性与把握度评估**：100%。权威原型 `docs/design/spd_integrated_showcase_demo.html` 提供了完备的 DOM 结构、CSS 关键帧及数学极坐标/切片算法，所有变量与微动效已在 M1 的 `frontend/src/styles/theme.css` 中就绪；登录模态框已在 M2 的 `HealthcareAuthModal.vue` 就绪。
- **存量功能与三方体验影响分析**：
  - UX：1:1 复现权威原型双模态全景展厅质感，支持 4K 原生动态视频无缝播放、360° 轨道拓扑与 3D 弧面流光平滑切换，提供纯享壁纸态与 ESC 分层退出，交互极致流畅。
  - DX：全模块组件化封装，清晰解耦导航、核心舱、两大 3D 引擎与壁纸抽屉，函数 100% 配备规范的中文 4 要素注释，符合 Vue 3 + TypeScript 工业级规范。
  - AX：状态集中托管在 Pinia `showcaseStore` 中，支持双模态互斥休眠（未激活视图 `display: none` 并暂停动画，0 冗余 GPU 负载）。
- **权限与工作台跳转对齐**：
  - 点击“进入三级角色工作台”或卡片时，已登录用户依据当前 RBAC 角色直达匹配模块（信息科/耗材科 -> `/dict`，二级库 -> `/secondary`，财务 -> `/finance`，供应商 -> `/procurement`）；未登录用户平滑弹出 `HealthcareAuthModal`。
- **验收标准**：
  - `npm --prefix frontend run build` 0 error, 0 warning 编译通过。
  - 全域代码 100% 严禁任何 Emoji 表情字符。
  - 所有组件与方法均具备标准化中文四要素注释。

---

## 原子实施清单

1. 创建 `frontend/src/stores/showcaseStore.ts`：定义双模态、纯享模式、壁纸清单、音频增益与时钟开关等核心状态与 Actions。
2. 创建 `frontend/src/components/showcase/DesktopClock.vue`：实现等宽防抖实时数字时钟小部件。
3. 创建 `frontend/src/components/showcase/ZenControlBar.vue`：实现纯享模式右上角浮动控制条与快捷退出。
4. 创建 `frontend/src/components/showcase/TopFloatNav.vue`：实现顶部固定悬浮胶囊导航栏、模态切换胶囊及操作集合。
5. 创建 `frontend/src/components/showcase/HeroSection.vue`：实现中央毛玻璃 Hero 核心舱、流体笔刷按钮与三大法定合规指标。
6. 创建 `frontend/src/components/showcase/OrbitalGallery.vue`：实现 360° 环形轨道拓扑与反向自转医疗资产卡片。
7. 创建 `frontend/src/components/showcase/TiltedGrid.vue`：实现 3D 弧面圆柱 8/16 切片轻量流光系统。
8. 创建 `frontend/src/components/showcase/WallpaperDrawer.vue`：实现 41 款壁纸工坊抽屉、分类筛选与搜索。
9. 创建 `frontend/src/views/ShowcaseView.vue`：组装 Layer 0/1、双模态引擎、全屏拖拽及登录模态联动。
10. 更新 `frontend/src/router/index.ts`：挂载 `/showcase` 路由并放行免认证访问，调整根路径导航。
11. 运行 `npm --prefix frontend run build` 验证 TypeScript 严格类型与打包构建。
12. 检查 0 Emoji 规范并编制 `handoff.md`。
