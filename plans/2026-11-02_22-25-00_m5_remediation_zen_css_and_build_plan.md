# Milestone M5 缺陷返工与专项修复实施计划 (Remediation Plan)

- 计划文档路径：plans/2026-11-02_22-25-00_m5_remediation_zen_css_and_build_plan.md
- 记录时间戳：2026-11-02 22:25:00
- 责任 Agent：teamwork_worker (Fix & Remediation Worker)
- 前端目标文件：
  - `frontend/src/styles/theme.css`：新增全局纯享模式（`body.zen-pure-mode`）DOM 隐藏与显式控制规则，包含退出微胶囊保活
  - `frontend/src/components/showcase/TopFloatNav.vue`：清理引发 Vue SFC 误编译为 `body.zen-pure-mode { display: none !important; }` 的 Scoped CSS 规则
  - `frontend/src/components/showcase/HeroSection.vue`：清理 Scoped CSS 中的 `:global(body.zen-pure-mode)`
  - `frontend/src/components/showcase/WallpaperDrawer.vue`：清理 Scoped CSS 中的 `:global(body.zen-pure-mode)`
  - `frontend/src/components/showcase/TiltedGrid.vue`：清理 Scoped CSS 中的 `:global(body.zen-pure-mode)`
  - `frontend/src/components/showcase/DesktopClock.vue`：清理 Scoped CSS 中的 `:global(body.zen-pure-mode)`
  - `frontend/src/views/ShowcaseView.vue`：清理 Scoped CSS 中的 `:global(body.zen-pure-mode)`，补充 `handleLoginSuccess` 回调函数与标准中文四要素注释
  - `frontend/vite.config.ts`：配置 `build.rollupOptions.output.manualChunks` 与 `build.chunkSizeWarningLimit: 1500`，彻底消除大包告警
- 测试与截图目标：
  - `tests/e2e/showcase_regression.spec.ts`：执行真实 Vite 服务回归测试，通过 Tier 1 ~ 4 全部断言并保留实机截图
  - `tests/e2e/m4_business_views_rbac.js`：执行 7 大业务视图与 RBAC 权限隔离测试，确保零回归
  - `tests/screenshots/showcase_zen_pure_mode.png`：生成纯净壁纸态实机截图

---

## 1. 核心评估指标

### 1.1 可行性与把握度评估
- **把握度**：100%
- **技术风险点与攻关措施**：
  - 风险点：Vue SFC 的 Scoped CSS 编译器在解析 `:global(body.zen-pure-mode) .selector` 时，部分版本会将选择器截断，使得编译出的 CSS 变成 `body.zen-pure-mode { display: none !important; }`，直接将 `<body>` 隐藏导致全白屏死锁。
  - 攻关措施：彻底从各 SFC 的 `<style scoped>` 中移除所有 `:global(body.zen-pure-mode)` 规则，将纯享模式规则统一定义于全局根样式文件 `frontend/src/styles/theme.css` 中，采用标准的全局选择器，确保没有任何 Scoped 篡改风险。

### 1.2 存量功能与三方体验影响分析
- **UX (用户体验)**：修复后，进入纯享模式时，前景卡片（导航栏、中央 Hero、轨道卡片、抽屉）平滑隐藏，右上方“退出纯享 (ESC)”与“环境音效开关”微胶囊清晰呈现且可点击；按 ESC 或点击退出按钮可毫秒级恢复全景展厅。
- **DX (开发者体验)**：样式集中管控，杜绝隐蔽的 Scoped 污染；补齐 `ShowcaseView.vue` 缺失的 `@success` 响应函数；消除打包告警使 CI/CD 流畅。
- **AX (Agent 上下文)**：消除测试用例超时崩溃，为后续系统集成与审计提供明确的无锁回环验证依据。
- **零破坏性底线**：所有业务视图、RBAC 抽屉、本地壁纸流与音效系统保持 100% 正常运行。

---

## 2. 技术与 UI 细节规范

### 2.1 全局样式定义 (`frontend/src/styles/theme.css`)
```css
/* =========================================================================
   纯享壁纸模式 (Zen Mode) 全局视图调度控制规则
   ========================================================================= */
body.zen-pure-mode .top-float-nav {
  opacity: 0 !important;
  pointer-events: none !important;
  transform: translateY(-20px) !important;
}

body.zen-pure-mode .hero-stage-center,
body.zen-pure-mode #hero-main-stage,
body.zen-pure-mode .hero-stage-wrapper {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

body.zen-pure-mode .stage-orbital-view,
body.zen-pure-mode #orbital-container {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

body.zen-pure-mode .stage-tilted-view,
body.zen-pure-mode #tilted-container {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

body.zen-pure-mode .wallpaper-dimmer-layer {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

body.zen-pure-mode .wallpaper-drawer-panel {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

body.zen-pure-mode .desktop-clock-widget.zen-show {
  display: block !important;
  opacity: 0.95;
  top: 50px;
}
```

### 2.2 `ShowcaseView.vue` 中 `handleLoginSuccess` 规范
```ts
/**
 * 处理医慧通行模态登录成功回调并跳转对应工作台
 * @param {any} [userInfo] 登录成功返回的用户身份信息对象
 * @returns {void}
 * @route internal://ShowcaseView/handleLoginSuccess
 * @throws {Error} 捕获路由跳转异常并进行安全降级提示
 */
function handleLoginSuccess(userInfo?: any): void {
  showcaseStore.isLoginModalOpen = false;
  router.push('/dict').catch((err: Error) => {
    console.error('登录成功后工作台路由跳转失败:', err);
  });
}
```

### 2.3 `frontend/vite.config.ts` 打包分块配置
```ts
  build: {
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-element': ['element-plus', '@element-plus/icons-vue'],
          'vendor-http': ['axios']
        }
      }
    }
  }
```

---

## 3. 原子实施清单

1. [原子行动 1 - frontend/src/styles/theme.css]：添加全局 `body.zen-pure-mode` 控制规则与保活规范。
2. [原子行动 2 - frontend/src/components/showcase/TopFloatNav.vue]：移除 `<style scoped>` 中的 `:global(body.zen-pure-mode) .top-float-nav`。
3. [原子行动 3 - frontend/src/components/showcase/HeroSection.vue]：移除 `<style scoped>` 中的 `:global(body.zen-pure-mode) .hero-stage-center`。
4. [原子行动 4 - frontend/src/components/showcase/WallpaperDrawer.vue]：移除 `<style scoped>` 中的 `:global(body.zen-pure-mode) .wallpaper-drawer-panel`。
5. [原子行动 5 - frontend/src/components/showcase/TiltedGrid.vue]：移除 `<style scoped>` 中的 `:global(body.zen-pure-mode) .stage-tilted-view`。
6. [原子行动 6 - frontend/src/components/showcase/DesktopClock.vue]：移除 `<style scoped>` 中的 `:global(body.zen-pure-mode) .desktop-clock-widget.zen-show`。
7. [原子行动 7 - frontend/src/views/ShowcaseView.vue]：移除 `<style scoped>` 中的 `:global(body.zen-pure-mode) .wallpaper-dimmer-layer`，在 `<script setup>` 中实现 `handleLoginSuccess` 函数并添加四要素中文注释。
8. [原子行动 8 - frontend/vite.config.ts]：配置 `build.chunkSizeWarningLimit: 1500` 与 `manualChunks`。
9. [原子行动 9 - 验证]：运行 `npm --prefix frontend run build`，核验 0 errors 0 warnings。
10. [原子行动 10 - 验证]：运行 `node tests/e2e/showcase_regression.spec.ts`，验证 Tier 1 ~ 4 全部断言通过并生成实机截图。
11. [原子行动 11 - 验证]：运行 `node tests/e2e/m4_business_views_rbac.js`，验证全量业务视图与 RBAC 隔离通过，零回归。
12. [原子行动 12 - 交付]：撰写 handoff.md 报告并通过 send_message 向 orchestrator 汇报。
