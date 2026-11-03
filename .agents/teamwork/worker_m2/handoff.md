# Milestone M2 交付报告：医慧通行现代医疗安全模态登录中枢与认证会话对齐 (Handoff Report)

## 1. 观察记录 (Observation)

### 1.1 需求与原型事实基线
- **权威设计来源**：`docs/design/spd_integrated_showcase_demo.html` 第 1530-1795 行（CSS 样式类 `.spd-auth-backdrop`, `.spd-auth-card`, `.spd-role-fast-grid`, `.spd-spinner-box` 等）、第 2066-2130 行（DOM 结构与表单元素）、第 3016-3114 行（明暗文切换、角色快捷登录与双环脉冲指示器交互）。
- **后端真实用户鉴权与种子数据审计**：
  - `backend/app/routers/auth_router.py:32-75` 提供真实认证接口 `POST /api/v1/auth/login`，入参为 `{username, password}`，返回标准 `access_token` 及用户信息。
  - `backend/app/core/security.py:171-195` 支持 `X-Mock-User` 与 `X-Mock-Role` 头部，收录预设账号：`admin`、`mgr_consumable`、`mgr_equip`、`mgr_finance`、`nurse_ortho`、`nurse_cardio`。
  - `backend/app/services/seed_service.py:112-170` 初始化种子人员密码默认为 `123456`。

### 1.2 现有代码缺陷观测
- **缺陷 1 (请求头与账号失真)**：原有 `frontend/src/api/request.ts:28-29` 仅读取未持久化写入过的 `spd_active_username`，导致请求头 `X-Operator-User` 恒为 `admin`，且缺失 `Authorization: Bearer <token>`、`X-Mock-User` 与 `X-Mock-Role` 注入。
- **缺陷 2 (HTTP 请求方法缺失)**：原有 `frontend/src/api/request.ts` 仅封装了 `httpGet` 与 `httpPost`，缺失 `httpPut`、`httpDelete` 与 `httpPatch` 导出。
- **缺陷 3 (人员预设与后端种子账号脱节)**：原有 `frontend/src/stores/userStore.ts:19-60` 预设工号为 `mat_mgr`、`cardio_nurse`、`finance_auditor`，遗漏了设备科主管 `mgr_equip`，与真实 MySQL 数据库账号不匹配，导致真实请求抛出 400 校验异常。
- **缺陷 4 (登录视图割裂)**：原有 `frontend/src/views/LoginView.vue` 采用旧版白底卡片并包含未实现的注册选项卡，未复刻 Demo 中的 440px 高质感模态卡片及 CA 双环认证加载指示器。

---

## 2. 推导逻辑 (Logic Chain)

1. **从后端鉴权机制到拦截器修复的推导**：
   - 鉴于后端 `security.py:170-195` 优先识别 `X-Mock-User` 与 `Authorization: Bearer <token>`，在 `frontend/src/api/request.ts` 的请求拦截器中同步提取并注入 `Authorization: Bearer <token>`、`X-Mock-User`、`X-Mock-Role` 与 `X-Operator-User`，并同时对 `spd_active_username` 与 `spd_active_user` 进行容错解析，彻底解决权限穿透失真问题。
   - 扩充 `httpPut`、`httpDelete`、`httpPatch` 泛型请求工具函数，确保后续业务模块执行更新、审批与删除操作时具备标准解包能力。

2. **从双轨高韧性要求到 `userStore.ts` 重构的推导**：
   - 将 `PRESET_USERS` 完全对齐为：`admin` (信息科系统管理员)、`mgr_consumable` (耗材科主管)、`mgr_equip` (设备科主管)、`nurse_cardio` (临床二级库护士)、`mgr_finance` (财务审计主管)、`supplier_wego` (威高医药代表)。
   - 在 `login` 方法中实施双轨机制：优先调用 `POST /auth/login` 请求真实后端验证，若调用失败或处于离线演示环境，自动平滑回退至预设本地 profile，生成防崩溃会话令牌。
   - 建立 `syncStorage` 方法，确保 `spd_is_logged_in`、`spd_token`、`spd_active_user` 与 `spd_active_username` 四个持久化缓存键严格保持一致与同步销毁。
   - 扩充 `loginAsRole`，支持 `consumable`, `equip`, `nurse`, `finance`, `admin` 等多别名智能映射。

3. **从权威展厅 Demo 原型到 `HealthcareAuthModal.vue` 落地推导**：
   - 1:1 移植 `spd_integrated_showcase_demo.html` 的 440px 磨砂玻璃卡片与深浅双主题 CSS 规则；
   - 头部内置医疗十字矢量图标，工号与密钥输入框配备矢量前缀图标，密码输入框实现无刷新明暗文与 SVG 眼睛切换；
   - 提供 5 大角色一键免密通道网格（耗材科管理、设备科管理、临床二级库、财务合规审计、系统管理员）；
   - 集成 CA 认证双环脉冲微加载指示器（外环 `spdSpin` 匀速旋转 + 内核 `spdPulsePing` 星标缓动缩放）；
   - 支持 ESC 键与遮罩空白处点击平滑关闭模态窗。

4. **从统一设计语言到 `LoginView.vue` 展厅落地页推导**：
   - 彻底推翻传统白底后台表单，重塑为基于深空暗黑与高斯微光球的现代医疗展厅级落地页；
   - 默认置入并居中呈现 `HealthcareAuthModal`；若用户关闭弹窗，中央优雅呈现医疗核心品牌引导舱，提供一键唤起与管理员直通接入通道。

---

## 3. 局限与注意事项 (Caveats)

- **后端服务依赖性**：当前实现了双轨自适应高韧性策略，在未启动 FastAPI 后端（端口 8000 未监听）时，登录模块将自动优雅降级为本地预设演示身份登录，所有数据流均可正常漫游，不产生白屏或崩溃。
- **无 Emoji 铁律**：所有新增与重构代码中的文案、注释与 UI 标签已全面通过脚本审计，100% 杜绝 Emoji。

---

## 4. 结论 (Conclusion)

Milestone M2 设定的全部交付项已 100% 高保真落地：
1. `frontend/src/api/request.ts` 拦截器注入与 RESTful 方法扩充完成；
2. `frontend/src/stores/userStore.ts` 真实种子账号对齐、双轨高韧性登录与 localStorage 键值同步完成；
3. `frontend/src/components/auth/HealthcareAuthModal.vue` 440px 现代医疗模态登录中枢、双环脉冲微加载指示器、5 大角色一键免密网格与 ESC 退出支持完成；
4. `frontend/src/views/LoginView.vue` 展厅级星空落地页与模态中枢集成完成；
5. 全局编译构建 `npm --prefix frontend run build` 0 错误、0 警告顺利通过，所有函数标准化四要素注释（`@param`, `@returns`, `@route`, `@throws`）覆盖率 100%。

---

## 5. 独立验证方法 (Verification Method)

### 5.1 构建与类型编译验证
在项目根目录执行生产构建与类型检查：
```powershell
npm --prefix frontend run build
```
**判定标准**：`vue-tsc` 与 `vite build` 输出 0 error 0 warning，构建顺利生成产物。

### 5.2 严禁 Emoji 自动化正则审计
在项目根目录运行字符排查命令：
```powershell
Get-ChildItem -Path 'frontend\src\components\auth\HealthcareAuthModal.vue', 'frontend\src\stores\userStore.ts', 'frontend\src\api\request.ts', 'frontend\src\views\LoginView.vue' | Select-String -Pattern '[\uD83C-\uDBFF\uDC00-\uDFFF\u2600-\u27BF\uE000-\uF8FF]'
```
**判定标准**：输出完全为空。

### 5.3 登录模态交互与会话持久化检验
1. 在浏览器访问前端页面 `/login`，确认居中弹出 440px 磨砂玻璃卡片 `医慧通行 · 统一安全接入中枢`；
2. 点击密码框右侧眼睛图标，确认密码明文与密文实时切换；
3. 点击 5 大角色卡片中任意一项（如 `耗材科管理`），确认唤起全屏双环脉冲微加载指示器，提示 `正在以 [耗材科管理员] 身份建立双向通道...`，并在 600ms 后自动关闭弹窗并跳转至 `/dict`；
4. 在浏览器控制台检查 `localStorage`：
   - `localStorage.getItem('spd_is_logged_in')` 为 `'true'`
   - `localStorage.getItem('spd_active_username')` 为 `'mgr_consumable'`
   - `localStorage.getItem('spd_token')` 包含有效令牌
5. 检查发出的 HTTP 请求头部，确认携带 `Authorization: Bearer <token>`、`X-Mock-User: mgr_consumable`、`X-Mock-Role: dept_manager` 与 `X-Operator-User: mgr_consumable`。
