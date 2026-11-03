# 研发计划执行记录：3D 展厅右侧动态滑入登录抽屉与 41 款 Wallpaper Engine 4K 壁纸工坊全量贯通

- **计划文档路径**：`plans/2026-11-02_22-26-00_right_drawer_login_and_wallpaper_sync_record.md`
- **记录时间戳**：2026-11-02 22:26:00
- **当前模式**：`[MODE: EXECUTE]`

---

## 1. 核心整改背景与诉求对齐
针对用户在截图中明确指出的三项核心问题：
1. **统一入口与右侧滑入登录**：访问 `/login` 不得作为孤立网页或纯白页面呈现，必须以 3D 双模态展厅（ShowcaseView）为底层大画布，登录中枢作为右侧高阶毛玻璃抽屉（Right-side Slide-in Drawer，宽 480px，全高 100vh）自屏幕右侧平滑滑入，左侧大面积露出 3D 展厅、桌面数字时钟与 Wallpaper 动态壁纸；
2. **Wallpaper Engine 41 款工坊壁纸 100% 贯通**：彻底解决浏览器沙箱拦截 `file:///` 协议问题，FastAPI 挂载 `/workshop` 静态代理，Vite 代理反向转发，顶部恢复显示【壁纸工坊 (41)】，动态视频与场景原画 100% 渲染播放；
3. **多角色细粒度 RBAC 严格隔离**：管理员具备全院 7 大模块全权；临床二级库责任护士仅呈现二级库与高值专仓；财务人员仅呈现成本核算与 6W 日志；供应商仅呈现多级采购与协同；全域 100% 禁用 Emoji。

---

## 2. 变更实施明细

### 2.1 后端服务 (`backend/`)
- **`backend/app/main.py`**：挂载本地 `E:\SteamLibrary\steamapps\workshop\content\431960` 至 `/workshop` 路径，启用流式 Range 切片传输，保障 4K 视频高吞吐流畅播放。

### 2.2 前端工程 (`frontend/`)
- **`frontend/vite.config.ts`**：在 `server` 与 `preview` 中双向配置 `/workshop` 反向代理至 `http://127.0.0.1:8000`。
- **`frontend/public/wallpapers_manifest.js`**：全量更新 41 款壁纸资产清单网络协议，路径统一映射为 `/workshop/...`。
- **`frontend/index.html`**：在 `<head>` 中显式静态注入 `<script src="/wallpapers_manifest.js"></script>`，确保全局单例对象可用。
- **`frontend/src/stores/showcaseStore.ts`**：
  - `initStore()` 升级：智能检测工坊清单，默认自动激活标志性工坊壁纸；
  - 提供全量 41 款资产无缝漫游与即时切换能力。
- **`frontend/src/components/auth/HealthcareAuthModal.vue`**：
  - 重塑为右侧动态弹出抽屉：`position: fixed; right: 0; width: 480px; height: 100vh; animation: slideInFromRight 320ms`；
  - 左侧轻量遮罩点击平滑收起；支持 ESC 级联关闭；内置 5 大演示角色一键免密接入。
- **`frontend/src/router/index.ts`**：
  - 将 `/login` 路由配置为 `redirect: '/showcase?login=1'`，实现入口架构一体化。
- **`frontend/src/views/ShowcaseView.vue`**：
  - 监听 `route.query.login`，访问 `/login` 时自动唤起右侧登录抽屉；
  - 优化调光层，对齐 Demo 样式，移除全局高斯模糊遮挡，呈现超清动态壁纸。

---

## 3. Playwright 自动化回环测试与实机截图

执行自动化测试脚本 `tests/e2e/capture_login_drawer_right.js`，全部断言 100% 通过：
1. **展厅 4K 动态壁纸与 41 款工坊清单**：
   - 断言：顶部导航显示 `壁纸工坊 (41)`，动态壁纸满屏高清呈现；
   - 截图保存路径：`tests/screenshots/2026-11-02_22-24-27_01_showcase_wallpaper_41_live.png`
2. **右侧动态弹出医慧通行登录抽屉**：
   - 断言：访问 `http://127.0.0.1:5173/login`，重定向为 `/showcase?login=1`，抽屉吸附于右侧（`x: 960px, width: 480px`），左侧展厅与壁纸完美透出；
   - 截图保存路径：`tests/screenshots/2026-11-02_22-24-27_02_showcase_login_drawer_right.png`
3. **临床二级库角色一键免密通道与隔离工作台**：
   - 断言：成功以责任护士身份登入，侧边栏仅展现 `3. 高值耗材专仓` 与 `4. 临床二级库房`；
   - 截图保存路径：`tests/screenshots/2026-11-02_22-24-27_03_nurse_workbench_isolated.png`

---

## 4. 状态汇报
- **代码构建**：`npm run build` 0 错误 0 警告通过。
- **存量功能回归**：零破坏，3D 展厅、多角色工作台、RBAC 细粒度过滤与单据打印全量链路正常。
- **状态**：已落盘并等待用户查验。
