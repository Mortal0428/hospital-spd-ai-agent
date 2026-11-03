# 研发计划：前端生产级三级工作台高质感设计原型图与多变体选型器

- **计划文档路径**：`plans/2026-11-02_13-41-00_frontend_design_prototypes_and_variants_plan.md`
- **记录时间戳**：`2026-11-02 13:41:00`
- **当前所处阶段**：阶段 4 前置设计定型（前端生产级三级工作台多变体原型与视觉基准设计）
- **按需挂载全局 Skills**：
  - `emil-design-eng`（Emil Kowalski 精雕哲学：微交互质感、无形细节、`:active` 缩放反馈、严禁 `transition: all`）
  - `apple-design`（Apple HIG 视觉规范：半透明材质 Liquid Glass、毛玻璃景深、亮暗主题无缝自适应）
  - `prototype`（多变体发散选型器规范：底部浮动暗色玻璃胶囊切换器、独立轴向比选、无损生产代码）
  - `animate`（动画决策框架：入场 `ease-out`、低于 240ms 帧预算、高频键盘操作零动画）
  - `break-ui`（极端恶劣医疗器械数据抗压排版设计）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_13-41-00_frontend_design_prototypes_and_variants_plan.md
- 记录时间戳：2026-11-02 13:41:00
- 前端目标文件：
  docs/design/spd_frontend_design_variants.html —— 前端生产级高质感三级角色工作台原型设计选型器（包含 3 种独立设计方向 + 1 种推荐融合生产视图、暗色玻璃选型胶囊、亮暗色主题自适应、三级角色视角切换、5 类法定单据四联签字打印预览弹窗、5 大 LangGraph 业务智能体侧边浮窗舱）
- 后端目标文件：无（后端已在阶段 2 获得完全验证并在 8000 端口稳定就绪，本阶段保持只读物理隔离）
- 测试与截图文件：
  1. tests/harness/verify_frontend_prototypes.js —— 驱动 Playwright 对原型选型器执行多变体切换、暗黑模式切换、单据弹窗与智能体浮窗全交互链路校验脚本
  2. tests/screenshots/2026-11-02_13-41-00_frontend_design_variants_verify.png —— 原型选型器实机验证截图
```

---

## 二、 核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`99%`
- **潜在技术风险与预案**：
  - **风险点 1（字体与高分辨率屏幕抗锯齿）**：不同操作系统默认字体渲染差异。**应对策略**：采用 `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", sans-serif` 高质量跨平台字体栈，并开启 `-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;`；
  - **风险点 2（毛玻璃性能与背景穿透）**：部分显示器或低版本系统可能对 `backdrop-filter` 兼容不良。**应对策略**：配置带半透明回退色彩的 Design Tokens（如 `rgba(255, 255, 255, 0.85)` / `rgba(15, 23, 42, 0.85)`），确保无滤镜时依然保持清晰层级。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：在正式编写 Vue 3 组件前，让用户能够在浏览器中通过底部悬浮胶囊一键对比 3 种设计语言与 1 种推荐融合方案，并体验真实的亮暗模式切换、角色工作台视图与四联打印单据效果，所见即所得；
- **开发者体验（DX）**：建立完整的 CSS 变量体系（Design Tokens），将颜色、边框、毛玻璃模糊度、间距与圆角统一为标准化变量，后续直接迁移至 `frontend/src/styles/tokens.css`；
- **AI 代理体验（AX）**：每个组件与功能块具备明确的 `data-testid` 与语义化 Class，Playwright 可精准定位；
- **存量保护与零破坏**：所有原型设计代码严格集中于 `docs/design/` 下，绝不提前向 `frontend/src/` 散落临时代码。

### 3. Playwright 自动化回环测试与截图验证方案
- **验证脚本**：`tests/harness/verify_frontend_prototypes.js`
- **自动化测试断言链路**：
  1. 静态扫描 `docs/design/spd_frontend_design_variants.html`，断言 100% 零 Emoji 违规；
  2. 启动 Playwright 持久化无锁浏览器加载原型文件；
  3. 依次点击底部胶囊切换栏中的 4 个设计变体标签（`Translucent` 灵动毛玻璃、`Precision` 工致密集、`Sovereign` 法定台账、`Fusion` 推荐融合生产版），断言视图切换无报错、高亮滑块定位准确；
  4. 点击右上角主题切换按钮，切换为暗黑模式（Dark Mode），断言背景色与文字对比度自适应更新；
  5. 切换三级人员视角（系统管理员、耗材科管理员、临床二级库护士、财务科核算员），断言核心工作台指标卡与操作权限实时联动；
  6. 点击“法定四联单据打印预览”按钮，断言模态弹窗平滑浮现，校验票头一维码、明细表格、防伪水印与票尾四联责任签字栏可见；
  7. 点击右侧“智能体协同舱”按钮，断言 LangGraph 5 大智能体侧边抽屉平滑滑出；
  8. 校验 Console Error 计数等于 0，截取高清实机验证图保存至 `tests/screenshots/2026-11-02_13-41-00_frontend_design_variants_verify.png`。

---

## 三、 技术与 UI 细节规范

### 1. 变体轴向与设计规范提炼（基于 `prototype` & `PICKER.md`）

| 变体标识 | 变体名称 | 核心设计轴向 (Axis) | 核心视觉特征 |
| :--- | :--- | :--- | :--- |
| **`translucent`** | Apple 灵动毛玻璃中枢 | **通透度与层次感** | 多层磨砂毛玻璃 (`blur(20px)`)、柔和高光微边框 (`inset 0 0 0 1px rgba(255,255,255,0.15)`)、大圆角与舒展内边距 |
| **`precision`** | Emil 工致密集大盘 | **信息密度与高频操作反馈** | 紧凑行高、纯净 1px 细线边框、按压微缩放 (`scale(0.97)`)、`user-select: none` 防误触、高频操作零动画 |
| **`sovereign`** | 医疗物权法定责任台账 | **权威合规与 6W 审计痕迹** | 醒目的 8 大节点业务流转时间轴、红黄绿三级效期与召回状态印章、强化四联签字栏法定票据卡片 |
| **`fusion`** | 推荐融合生产级工作台 | **综合平衡生产落地基准** | 通透毛玻璃外壳 + 工致紧凑数据表格 + 法定 6W 穿透抽屉与标准四联单据，作为后续 `frontend/` 开发基准 |

### 2. 纯矢量 SVG 图标方案（全域严禁 Emoji）
- 全部图标使用内联 `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">` 绘制；
- 涵盖：医院徽标、主库入库、按需分发、高值 UDI 专仓、二级库申领、全流程日志、财务审计、智能体机器人、亮暗主题切换、四联单据打印、扫码枪枪口等 12 组医疗专属精美矢量图标。

### 3. 法定单据四联签字栏结构规范
- 包含标准四联责任人签字框：
  1. 【制单操作人】（验收入库/发料/申领人）
  2. 【主库科室主管】（耗材科/设备科主管）
  3. 【二级库领用人】（临床科室护士长/技师）
  4. 【财务科复核】（财务科核算员/总会计师）
- 支持 `@media print` 专用打印排版，隐藏无关导航，保留纯净票据。

---

## 四、 强制性原子实施清单

```markdown
实施清单：
1. [已完成] [docs/design/] 创建 docs/design/spd_frontend_design_variants.html，按照 prototype skill 与 PICKER.md 规范实现包含 Translucent、Precision、Sovereign、Fusion 四大变体的高保真前端交互选型原型，内置三级角色切换、亮暗主题切换、四联单据打印弹窗与 5 大智能体侧边浮窗。
2. [已完成] [tests/] 编写 tests/harness/verify_frontend_prototypes.js，驱动 Playwright 浏览器自动化执行变体切换、暗黑模式切换、四联单据打印预览与智能体抽屉交互断言。
3. [已完成] [tests/ | plans/] 运行 node tests/harness/verify_frontend_prototypes.js，校验交互完整性、控制台 0 报错，并将实机验证截图保存至 tests/screenshots/2026-11-02_13-41-00_frontend_design_variants_verify.png。
4. [已完成] [plans/] 更新 plans/ 进度记忆台账，汇报原型设计成果与实机截图，请求用户定夺最终用于生成生产级 frontend/ 的视觉变体。
```
