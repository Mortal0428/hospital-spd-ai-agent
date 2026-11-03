# Milestone M2 计划文档：医慧通行现代医疗安全模态登录中枢与认证会话对齐

- 计划文档路径：plans/2026-11-02_21-18-00_milestone_m2_healthcare_auth_modal_and_session_plan.md
- 记录时间戳：2026-11-02 21:18:00
- 目标目录与范围：
  - 前端目标文件：
    - `frontend/src/api/request.ts` (修复请求头注入 Authorization / X-Mock-User / X-Mock-Role / X-Operator-User，扩充 httpPut / httpDelete / httpPatch)
    - `frontend/src/stores/userStore.ts` (对齐 PRESET_USERS 种子数据，实现双轨自适应登录与 localStorage 键同步)
    - `frontend/src/components/auth/HealthcareAuthModal.vue` (完整实现 440px 现代医疗模态登录卡片、双环脉冲微加载、4大角色+管理员免密通道、ESC 退出)
    - `frontend/src/views/LoginView.vue` (重构为基于数字化展厅质感的高质感登录落地页，默认置入 HealthcareAuthModal)
  - 测试与截图：
    - 构建与类型检查：`npm --prefix frontend run build`
    - 0 Emoji 检验脚本

---

## 核心评估指标

- **可行性与把握度评估**：100%。原型代码位于 `docs/design/spd_integrated_showcase_demo.html` 第 1530-1795、2066-2130 及 3016-3114 行，逻辑与 CSS 完整完备；后端数据结构已在 `backend/app/core/security.py` 及 `backend/app/routers/auth_router.py` 完整审计。
- **存量功能与三方体验影响分析**：
  - UX：彻底消除简陋白底表单，实现 1:1 权威展厅高阶毛玻璃卡片、双环脉冲微动效、密码明暗文流畅切换与免密体验。
  - DX：补齐 `httpPut`、`httpDelete`、`httpPatch` 方法，提供清晰的 4 要素中文注释。
  - AX：规范本地持久化缓存键，消除 `spd_active_username` 为 null 导致的权限穿透失真。
- **回环验证与验收标准**：
  - `npm --prefix frontend run build` 0 error, 0 warning。
  - 源码中严禁任何 Emoji 表情字符。
  - 所有新增或修改函数 100% 覆盖 `@param`, `@returns`, `@route`, `@throws` 4 要素。

---

## 原子实施清单

1. 更新 `frontend/src/api/request.ts`：修复请求拦截器注入规范头，增加 `httpPut`、`httpDelete`、`httpPatch` 封装。
2. 更新 `frontend/src/stores/userStore.ts`：对齐真实种子账号，实现双轨自适应登录与持久化键值同步。
3. 新建 `frontend/src/components/auth/HealthcareAuthModal.vue`：全量复刻 440px 磨砂玻璃模态卡片、工号密码表单、双环微加载及 5 大演示角色通道。
4. 重构 `frontend/src/views/LoginView.vue`：接入 `HealthcareAuthModal` 并构建展厅级暗黑星空背景落地页。
5. 验证前端编译构建与类型系统：执行 `npm --prefix frontend run build`。
6. 检查 0 Emoji 规范并编制 handoff.md 移交报告。
