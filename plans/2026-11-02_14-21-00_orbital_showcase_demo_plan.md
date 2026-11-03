# 研发计划：医院医疗物资全链路 SPD 轨道画廊数字化展示大屏原型 Demo (Orbital Gallery Hero)

- **计划文档路径**：`plans/2026-11-02_14-21-00_orbital_showcase_demo_plan.md`
- **记录时间戳**：`2026-11-02 14:21:00`
- **当前所处阶段**：前端展示大屏主题原型开发（Orbital Gallery Hero 医疗业务实装）
- **按需挂载全局 Skills**：
  - `emil-design-eng`（微动效控制、反向自转抵消、`:active` 缩放反馈、严禁 `transition: all`）
  - `apple-design`（毛玻璃景深、深浅色模式自适应、非模板化高质感审美）
  - `animate`（帧率性能守卫、仅动画合成层属性 `transform`/`opacity`、35s 匀速环绕公转）
  - `break-ui`（卡片文字极端自适应与防折行崩溃设计）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_14-21-00_orbital_showcase_demo_plan.md
- 记录时间戳：2026-11-02 14:21:00
- 前端目标文件：
  docs/design/spd_orbital_hero_demo.html —— 医院医疗物资全链路数字化全景展厅 / 轨道画廊英雄原型 Demo（原生高精度实现 21st.dev 规范：10 张医疗物资全链路核心卡片环绕轨道匀速公转、内层卡片反向自转抵消确保内容水平正向、中央悬浮发光主舞台、微呼吸状态徽标、主次 CTA 按钮、底部三列法定内控指标网格、亮暗双色主题自适应）
- 后端目标文件：无（后端服务保持只读隔离，不改动任何源码）
- 测试与截图文件：
  1. tests/harness/verify_orbital_demo.js —— 驱动 Playwright 验证轨道画廊 DOM 完整性、动画运行状态、暗黑模式切换、按钮交互并截屏归档
  2. tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_verify.png —— 原型实机验证截图
```

---

## 二、 核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`99%`
- **潜在技术风险与预案**：
  - **风险点 1（环形卡片反向旋转数学公式精度）**：公转时卡片若无精确的反向抵消，卡片文字在旋转到顶部时会倒立。**应对策略**：外层轨道容器执行 `transform: rotate(360deg)`，内层卡片同步执行 `transform: rotate(-360deg)`，旋转周期统一设定为 35s 线性无缝循环（`linear infinite`），保证卡片无论公转到任何角度均垂直正向；
  - **风险点 2（60fps 帧率预算与 GPU 消耗）**：10 张卡片连续旋转可能引发掉帧。**应对策略**：遵循 `animation-performance` 技能规范，动画严格限制在 `transform` 合成层执行，启用 `will-change: transform`，严禁触发重排（Reflow）。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：带来极其震撼的智慧医院数字化全景视效，将枯燥的耗材管理升华为主流科技感大屏，同时支持一键切入真实业务工作台；
- **开发者体验（DX）**：完全遵循组件化设计，DOM 结构清晰，后续可 100% 零成本转译为 React / Vue 3 组件；
- **AI 代理体验（AX）**：具备清晰的语义类名与状态属性，Playwright 可精准检测动画帧与交互响应；
- **存量保护**：文件存放在 `docs/design/` 下，绝不破坏现有 `frontend/`、`backend/` 任何已有代码。

### 3. Playwright 自动化回环测试与截图验证方案
- **验证脚本**：`tests/harness/verify_orbital_demo.js`
- **自动化测试断言链路**：
  1. 静态扫描 `docs/design/spd_orbital_hero_demo.html`，断言 100% 零 Emoji 违规；
  2. 启动 Playwright 浏览器加载页面，断言轨道容器与 10 张环绕医疗业务卡片渲染就绪；
  3. 检验 10 张卡片的角度极坐标偏移计算（`cos/sin` 坐标分布均匀）；
  4. 触发亮暗主题切换，校验 Design Tokens 颜色自适应；
  5. 校验中央主舞台标题、徽标、CTA 按钮与底部三列指标可见；
  6. 断言控制台 Console Error = 0，截取高清实机验证图保存至 `tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_verify.png`。

---

## 三、 技术与 UI 细节规范

### 1. 轨道 10 大医疗卡片资产分布表
1. `卡片 01`：**产品字典双维分类**（耗材科/设备科归口 · 药监局UDI）
2. `卡片 02`：**主库全部物资管理**（总仓集中验收入库 · 效期硬风控）
3. `卡片 03`：**主库按需分发调拨**（院内流转调拨 · FEFO近效期优先）
4. `卡片 04`：**高值耗材一物一码**（专仓由量到码拆包 · 智能柜锁定）
5. `卡片 05`：**临床二级库房台账**（病区定数包管理 · 低位智能补货）
6. `卡片 06`：**患者扫码脱敏核销**（临床诊疗绑定 · 消耗即结算记账）
7. `卡片 07`：**全流程 6W 物权台账**（责任人全流程穿透 · 100%合规审计）
8. `卡片 08`：**医院法定四联单据**（标准法定格式 · 四联责任签字栏）
9. `卡片 09`：**Agent 02 智能调拨**（LangGraph 工作流 · 自动水位监测）
10. `卡片 10`：**Agent 04 溯源召回**（不良事件监测 · 一键批次全局冻结）

### 2. 纯矢量 SVG 图标与审美铁律
- 全域严禁输出任何 Emoji；
- 采用 Element Plus / Lucide 风格的细线纯矢量 SVG 医疗徽标；
- 界面风格为 Apple 科技白（Light）与太空深邃黑（Dark），搭配医疗品牌色钛青蓝 `#0284c7`。

---

## 四、 强制性原子实施清单

```markdown
实施清单（全部完成）：
1. [已完成] [docs/design/] 创建 docs/design/spd_orbital_hero_demo.html，完整实现 21st.dev 规范的 360 度匀速轨道公转、内层卡片反向自转抵消、中央悬浮主舞台、三级角色与亮暗模式切换、10 大医疗业务卡片真实渲染。
2. [已完成] [tests/] 编写 tests/harness/verify_orbital_demo.js，配置 Playwright 自动化测试脚本，执行静态无 Emoji 审计、DOM 节点渲染与动画稳定性校验。
3. [已完成] [tests/ | plans/] 运行 node tests/harness/verify_orbital_demo.js，确保控制台 0 报错，已生成亮色实机截图 tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_light.png 与暗色实机截图 tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_dark.png。
4. [已完成] [plans/] 更新 plans/ 记忆台账，将本地实机链接与高清截图交付给用户审阅。
```
