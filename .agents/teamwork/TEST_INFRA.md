# E2E 自动化测试体系与 Playwright 实机截图回环工程基础设施规范 (TEST_INFRA.md)

本文档定义“医院医疗物资全链路数字化展厅（Showcase）与高质感全域业务视图”的端到端（E2E）自动化测试规范。体系严格遵循 **双轨方法论（Dual Track Methodology）** 与 **四层测试分级架构（4-Tier Hierarchy）**，确保前端交付物具备 100% 视觉对齐、零控制台报错、平滑微交互与实机截图留存能力。

---

## 一、双轨自动化测试方法论 (Dual Track Methodology)

为了在工程迭代中平衡“规范基准对齐”与“真实浏览器运行态验证”，测试体系分为两条互为印证的测试轨道：

### 轨道 A：权威规范契约核验轨 (Specification & Design Token Track)
- **基准来源 (Oracle)**：`docs/design/spd_integrated_showcase_demo.html`（权威原型）、`PROJECT.md` 与 `ORIGINAL_REQUEST.md`。
- **核验目标**：
  1. **全局 Design Tokens 契约**：深空暗色（`:root`）与极简白瓷（`[data-theme="light"]`）的 CSS 变量取值、毛玻璃滤镜（`backdrop-filter: blur(...)`）、微边框（`--border-card`）、流光渐变（`--accent-gradient`）；
  2. **全域 0 Emoji 铁律**：严禁在 DOM 节点、按钮、文本、标签中渲染任何 Emoji 字符，100% 采用纯矢量内联 SVG 或原生图标；
  3. **标准选择器与 DOM 结构契约**：确保顶部悬浮导航、分段胶囊、中央 Hero 核心舱、模态登录卡片及 4 大角色网格等关键类名和 ID 严格一致。

### 轨道 B：Playwright 浏览器真实渲染与截图回环轨 (Playwright Visual & Interaction Track)
- **驱动引擎**：基于 `tests/e2e/browser_config.js` 的持久化无锁浏览器实例（方案 A：持久化 Profile 模式，规避单实例文件锁冲突）。
- **核验目标**：
  1. **零未捕获异常 (Zero Console & Page Errors)**：在页面导航、模态呼出、快速切题、纯享切换全生命周期中，拦截并断言 `Console Error` 与 `PageError` 计数恒为 0；
  2. **毫秒级微交互链路**：双模态 360° 环形轨道与 3D 弧面切片流光平滑交替、密码明暗文切换、4 大角色一键免密带入与双环脉冲微加载指示器调度；
  3. **实机截图证据链交付**：全流程自动截取 1440x900 真实渲染大图，按照 `tests/screenshots/[timestamp]_[page_name].png` 规范持久化归档。

---

## 二、四层测试金字塔架构 (4-Tier Hierarchy)

测试用例严格划分为以下 4 个层级，由浅入深层层递进：

### Tier 1：核心功能全覆盖 (Feature Coverage - Happy Path)
覆盖系统四大核心功能模块的标准业务链路：
1. **展厅门户根视图加载 (T1.1)**：
   - 验证根路由访问成功，页面标题规范；
   - 顶部通透悬浮胶囊导航栏（`.top-float-nav` / `#top-nav`）可见且居顶固定；
   - 中央毛玻璃 Hero 核心舱（`.hero-stage` / `#hero-main-stage`）加载完整，包含“智慧医疗 物资全链”核心文案与 3 大特性徽章（100% 审计穿透、一物一码单品、移库不计费）；
   - 双模态切换胶囊（`#mode-segmented-pill`）存在，支持在 360° 全域轨道拓扑（`#orbital-container`）与 3D 弧面全链流光（`#tilted-container`）之间交替激活。
2. **医慧通行现代医疗安全模态登录中枢 (T1.2)**：
   - 点击“医慧通行”或“进入三级角色工作台”按钮，成功唤出 440px 磨砂毛玻璃模态弹窗（`.spd-auth-backdrop` + `.spd-auth-card` / `#spd-login-modal`）；
   - 包含工号输入框、密码输入框、记住会话复选框；
   - 密码框明暗文小眼睛按钮（`#btn-toggle-pwd` / `.spd-pwd-toggle`）点击后，输入框 `type` 属性在 `password` 与 `text` 间准确切换；
   - 4 大演示角色一键免密通道（耗材科主管、设备科主管、临床二级库、财务合规审计）网格可见，点击任意角色卡片自动填充对应工号。
3. **极简双主题自适应切换 (T1.3)**：
   - 触发主题切换开关（`#theme-toggle-btn` / `.theme-toggle`）；
   - 验证 `document.documentElement`（或 `body`）的 `data-theme` 属性在 `dark`（深色深空）与 `light`（极简白瓷）间顺畅切换；
   - 校验主题切换后背景色与卡片边框色平滑自适应，无视觉撕裂。
4. **纯享壁纸模式与复原链路 (T1.4)**：
   - 点击“纯享模式”按钮（`#btn-enter-zen`），进入纯净壁纸态；
   - 断言 `body` 激活 `zen-pure-mode`，中央主舞台、轨道卡片流、导航栏等前景卡片彻底隐去；
   - 右上角微控制条（`.zen-control-bar`）可见，包含退出微胶囊（`#btn-exit-zen`）；
   - 点击退出微胶囊或按下键盘 ESC 键，前景卡片与工作台 100% 完整复原。

---

### Tier 2：边界条件与恶劣输入防错 (Boundary & Corner Conditions)
深入验证极限场景与非预期输入的鲁棒性：
1. **ESC 键多层级互斥优先级栈 (T2.1)**：
   - 当登录模态弹窗处于打开状态时，按下 ESC 键仅关闭登录弹窗，不应错误触发其他图层退出；
   - 当处于纯享模式时，按下 ESC 键精准退出纯享态；
   - 遵循严格的 UI 浮层退出优先级栈，杜绝一键误关多个容器。
2. **高频连续主题切换抗抖动 (T2.2)**：
   - 毫秒级连续多次点击主题切换按钮，验证 CSS 变量切换无竞态冲突、无闪烁、无残留旧主题样式。
3. **密码明暗文原位保留与无刷新 (T2.3)**：
   - 在密码框输入长文本后多次切换显隐，断言文本内容保持完好、光标位置稳定，无刷新或清空。
4. **全屏壁纸比例自适应与杜绝黑边 (T2.4)**：
   - 校验背景媒体层（视频/原画）强制施加 `object-fit: cover !important` 与 `background-size: cover`，在任何屏幕分辨率下满铺，杜绝上下或左右黑边。
5. **全域零 Emoji 地毯式字符拦截 (T2.5)**：
   - 对当前页面呈现的所有文字内容、按钮文本、属性及 SVG 内部文本进行 Unicode 字符过滤，确保无任何 Emoji 字符泄漏。

---

### Tier 3：跨模块协同与状态流转 (Cross-Feature Integration)
验证各模块之间的联动与会话生命周期：
1. **快速角色选择到认证闭环流转 (T3.1)**：
   - 点击演示角色卡片（如临床二级库护士），填充账号后触发登录动作；
   - 断言双环脉冲微加载指示器调度，验证认证流程顺畅并安全关闭模态框。
2. **双模态切换与音视频状态协同 (T3.2)**：
   - 切换 360° 轨道与 3D 弧面流光时，后台不活跃视图自动暂停或隐藏，确保 GPU 负载清零；
   - 动态壁纸播放状态与音频控制保持同步，不因模态切换而中断。
3. **LocalStorage 会话记忆与刷新复原 (T3.3)**：
   - 记录用户选择的主题、壁纸偏好与角色记忆至 LocalStorage；
   - 执行页面软刷新（Reload），断言自动恢复用户上次配置，不重置为默认态。

---

### Tier 4：真实生产负载与全景视觉凭证 (Real-World Workload & Visual Evidence)
在标准生产分辨率下捕获实机截图作为权威交付证据：
1. **1440x900 标准工作台视口渲染 (T4.1)**：
   - 在真实浏览器环境中执行测试，杜绝任何 Mock 假数据伪造或静态 Facade 欺骗。
2. **多节点实机大图归档规范 (T4.2)**：
   - 截图保存路径：`tests/screenshots/[YYYY-MM-DD_HH-mm-ss]_[SCENE_NAME].png`；
   - 必须捕获的关键场景节点：
     - `showcase_orbital_dark.png`：深色模式 360° 全域轨道拓扑全景；
     - `showcase_tilted_dark.png`：深色模式 3D 弧面切片全链流光；
     - `auth_modal_dark.png`：医慧通行现代医疗安全模态登录中枢；
     - `auth_modal_role_selected.png`：快速切换演示角色与密码明文显示状态；
     - `showcase_light_theme.png`：极简白瓷浅色主题全景；
     - `showcase_zen_pure_mode.png`：100% 绝对纯净纯享壁纸态；
     - `showcase_zen_restored.png`：退出纯享模式后完整复原态。
3. **全域零未捕获异常监控 (T4.3)**：
   - 挂载 `page.on('console')` 与 `page.on('pageerror')`，非致命警告记录日志，严重错误立即熔断测试。

---

## 三、测试套件代码规范与执行命令

### 3.1 测试文件物理归属
- **E2E 回环测试套件**：`tests/e2e/showcase_regression.spec.ts`
- **截图凭证归档目录**：`tests/screenshots/`
- **测试设施规范文档**：`.agents/teamwork/TEST_INFRA.md`
- **测试就绪确认报告**：`.agents/teamwork/TEST_READY.md`

### 3.2 编码与注释规范
- 严格遵循全域禁用 Emoji 铁律；
- 所有新增或重构的测试函数必须配备标准中文四要素注释：
  - `@param`：参数说明
  - `@returns`：返回值说明
  - `@route`：所属模块与调用链路
  - `@throws`：断言失败与异常说明

### 3.3 测试套件独立执行命令
在项目根目录下通过 Node 25 直接运行 TypeScript 测试脚本：
```powershell
node --experimental-strip-types tests/e2e/showcase_regression.spec.ts
```

---
*本规范由 teamwork_test_writer_e2e 于 2026-11-02 制定并生效。*
