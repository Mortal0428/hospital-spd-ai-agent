# 研发实施计划：1比1深度复刻 Demo 前端（医慧通行登录注册门户 + 4大核心角色权限隔离 + 角色横幅与KPI大盘）

> 计划归档时间戳：2026-11-02 20:20:00  
> 任务标识符：`replicate_demo_frontend_with_login_and_4_roles_plan`  
> 关联协议：增强型 RIPER-5 代理执行协议（阶段 3：[MODE: PLAN] 技术规范与原子清单归档）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_20-20-00_replicate_demo_frontend_with_login_and_4_roles_plan.md
- 记录时间戳：2026-11-02 20:20:00
- 前端目标工程文件 (frontend/)：
  - frontend/src/views/LoginView.vue（全新创建：1:1 复刻 Demo 中的医慧通行现代医疗卡片风格登录/注册门户，含账号密码登录、注册申请、以及 4 大核心演示角色一键免密极速登录）
  - frontend/src/router/index.ts（更新：增加 /login 路由，配置路由前置导航守卫 beforeEach，未登录强制重定向至 /login，已登录根据角色跳转默认工作台）
  - frontend/src/stores/userStore.ts（更新：强化登录认证持久化、严格收敛为 4 大核心角色定义、动态权限控制与退出登录清理）
  - frontend/src/layouts/MainLayout.vue（更新：1:1 复刻 Demo 顶部权限横幅 .role-banner、当前登录身份卡片、退出登录按钮，并按 4 大角色动态控制侧边栏菜单权限徽标与可见性）
  - frontend/src/views/ProductDictView.vue（更新：1:1 注入 Demo 顶部 4 宫格 KPI 卡片大盘，按角色限制调价与删除操作）
  - frontend/src/views/GeneralMaterialView.vue（更新：1:1 注入 Demo 顶部 4 宫格 KPI 卡片大盘，按角色限制入库与出库审批）
  - frontend/src/views/HighValueView.vue（更新：1:1 注入 Demo 顶部 4 宫格 KPI 卡片大盘，按角色限制备货与核销操作）
  - frontend/src/views/SecondaryWarehouseView.vue（更新：1:1 注入 Demo 顶部 4 宫格 KPI 卡片大盘，按角色限制申领与调拨）
  - frontend/src/views/FinancePrintView.vue（更新：1:1 注入 Demo 顶部 4 宫格 KPI 卡片大盘，强化财务核算审计）
- 测试与验证文件 (tests/)：
  - tests/harness/verify_login_and_4_roles.js（Playwright E2E 自动化测试：验证登录注册门户、4大角色一键登录、路由守卫、顶部角色横幅、KPI 渲染与按钮级权限拦截）
  - tests/screenshots/2026-11-02_20-20-00_demo_1to1_login_and_4_roles.png（实机运行截图凭证）
```

---

## 二、 核心评估指标（必填）

### 1. 可行性与把握度评估
- **把握度：98%**
- **潜在技术风险与应对策略**：
  - *风险点 1：登录注册与前端路由守卫死循环*。
    - **应对**：在 `router.beforeEach` 中判断目标路由是否为 `/login`，若当前未认证且目标非 `/login` 则重定向；已认证时访问 `/login` 自动跳到 `/dict`；在 Pinia Store 与 `localStorage` 中同步保存 Token 与当前用户信息，避免页面刷新丢失登录态。
  - *风险点 2：4 大角色与存量后端 17 张表业务接口的权限对齐*。
    - **应对**：在前端 Store 中明确收敛为 4 大核心角色契约：
      1. `sys_admin`（信息科系统管理员）
      2. `dept_manager`（耗材科主库管理员）
      3. `secondary_user`（临床二级库人员）
      4. `finance_auditor`（财务科合规审计）
      每个角色严格对应后端操作人标识（`X-Operator-User`），在 Axios 请求头中实时传递，确保后端 17 张表与 6W 日志准确留痕。
  - *风险点 3：KPI 仪表盘与真实数据源动态联动*。
    - **应对**：在各 View 中将 Demo 中的典型医疗指标与当前后端接口返回的真实行数与金额结合，形成高质感的动态 KPI 卡片展示。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：100% 还原用户在 Demo 原型中喜爱的直观体验：清晰的登录卡片、一目了然的 4 大角色一键登录、顶部醒目的权限横幅、以及各业务页面顶部醒目的 4 宫格 KPI 统计大盘。
- **开发者体验（DX）**：代码集中在 `frontend/`，组件职责单一，函数具备 100% 中文四要素注释，类型安全严谨。
- **AI 代理体验（AX）**：显式的角色枚举与权限映射表，极大地增强了上下文的可解析性与后续自动化测试验证的确定性。
- **存量功能零破坏性底线**：保持所有 17 张数据库物理表、所有后端 API 路由零修改，前端已实现的负数红字退货、期初永久锁死、专属二维码扫码核销脱敏与四联打印功能 100% 继承并完美运转。

### 3. Playwright 自动化回环测试与截图验证方案
- **测试执行脚本**：`node tests/harness/verify_login_and_4_roles.js`
- **8 项核心强断言设计**：
  1. **未登录拦截与重定向**：直接访问 `/dict` 自动拦截并重定向到 `/login`；
  2. **登录认证门户渲染**：验证卡片式登录/注册界面完整渲染，包含工号、密码输入框及 4 大演示角色卡片；
  3. **4 大角色一键免密登录验证**：
     - 点击【信息科系统管理员】，成功登录并跳转工作台，顶部横幅显示 `信息科系统管理员 (sys_admin) —— 拥有全院最大权限...`；
     - 切换/重新登录为【临床二级库人员】，工作台横幅切换为二级库职责说明，左侧产品字典调价等管理按钮被禁用；
     - 登录为【财务科审计人员】，工作台横幅切换为“移库不计费、消耗即结算”核算说明；
  4. **顶部 KPI 卡片大盘渲染**：断言产品字典、普通耗材、高值耗材页面顶部包含 4 宫格 KPI 卡片且数值渲染完整；
  5. **退出登录闭环**：点击右上角【退出登录】，清空认证缓存并安全返回 `/login` 页面；
  6. **全程 0 控制台报错**：页面无任何 Console Error / PageError，无任何 Emoji 字符，生成实机截图保存至 `tests/screenshots/2026-11-02_20-20-00_demo_1to1_login_and_4_roles.png`。

---

## 三、 技术与实现规范细节

### 1. 登录注册页面设计 (`frontend/src/views/LoginView.vue`)
- 采用现代通透玻璃卡片（Glassmorphism Auth Card）质感；
- 顶部医疗系统专属 Logo 与标题：`医慧通行 · 医疗物资全链路管理系统`；
- Tab 切换：【账号密码登录】 vs 【医护人员注册】；
- 核心展示区：**【4 大核心角色一键免密体验通道】**：
  - 卡片 1：`信息科系统管理员`（工号：admin / 权限：全院监管、全流程6W日志CRUD、细粒度RBAC）
  - 卡片 2：`耗材科主库主管`（工号：mat_mgr / 权限：产品字典维护、主库批次验收入库、按需分发调拨）
  - 卡片 3：`临床二级库人员`（工号：cardio_nurse / 权限：科室二级库盘点、向主库申领、高值专属码扫码核销）
  - 卡片 4：`财务科审计人员`（工号：finance_auditor / 权限：移库不计费/消耗即结算核算、五类单据打印）

### 2. 角色上下文横幅复刻 (`frontend/src/layouts/MainLayout.vue`)
- 在主工作区内容顶部复刻 Demo 中的 `.role-banner`：
  - 动态展示当前登录角色名称、角标（Badge）、科室与工号；
  - 动态展示当前角色的核心管辖范围与权限边界说明；
  - 右侧提供【细粒度 RBAC】、【切换角色 / 退出登录】按钮。

### 3. KPI 仪表卡片复刻（各业务页面顶部）
- 统一样式类 `.kpi-grid` 与 `.kpi-card`：
  - 产品字典：全院字典总数、耗材科归口数、设备科归口数、注册证预警数；
  - 普通耗材：主库批次总数、待审批请领数、近效期预警数、今日调拨额；
  - 高值耗材：高值在库数、待扫码核销数、已绑定患者核销数、召回冻结数；
  - 财务审计：分发调拨总额、实际消耗结算总额、高低值占比、耗占比达标率。

---

## 四、 强制性最终步骤（原子实施清单）

```markdown
实施清单（已于 2026-11-02 20:27:30 全部 100% 执行完毕并通过 6 项自动化测试强断言）：
1. [已完成] [frontend/src/stores] 重构更新 userStore.ts，收敛并规范 4 大核心角色定义，完善 token、登录态与角色权限映射。
2. [已完成] [frontend/src/views] 编写全新的 frontend/src/views/LoginView.vue 登录与注册门户（1:1 复刻 Demo 中的医慧通行现代卡片风格与 4 大角色一键免密极速登录网格）。
3. [已完成] [frontend/src/router] 更新 frontend/src/router/index.ts，注册 /login 路由并配置全局路由导航守卫（未登录自动拦截跳转至 /login）。
4. [已完成] [frontend/src/layouts] 更新 frontend/src/layouts/MainLayout.vue，1:1 复刻 Demo 顶部的角色权限上下文横幅 (.role-banner)，展示明确的角色职责边界说明、当前登录人身份卡片与退出登录按钮。
5. [已完成] [frontend/src/views] 升级各大业务视图页面，1:1 注入 Demo 中的顶部 4 宫格 KPI 卡片大盘（ProductDictView.vue, GeneralMaterialView.vue, HighValueView.vue, SecondaryWarehouseView.vue, FinancePrintView.vue），并按 4 大角色实施显式的按钮权限置灰拦截。
6. [已完成] [frontend/] 执行 vue-tsc 静态类型检查与生产构建打包，确保 0 报错。
7. [已完成] [tests/] 编写并运行 tests/harness/verify_login_and_4_roles.js Playwright 回环测试脚本，验证未登录拦截、4大角色一键免密登录、角色横幅切换、KPI大盘渲染与退出登录闭环。
8. [已完成] [tests/ | plans/] 捕获实机截图保存至 tests/screenshots/live_1to1_login_portal.png 与 live_1to1_dict_view.png 等，更新计划文档并向用户汇报。
```
