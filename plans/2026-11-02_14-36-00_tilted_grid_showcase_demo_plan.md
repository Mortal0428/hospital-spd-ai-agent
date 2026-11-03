# 研发计划：医院医疗物资全链路 SPD 3D 弧面圆柱流光全景展厅原型 Demo (Tilted Grid Hero)

- **计划文档路径**：`plans/2026-11-02_14-36-00_tilted_grid_showcase_demo_plan.md`
- **记录时间戳**：`2026-11-02 14:36:00`
- **当前所处阶段**：前端展示主题原型开发（3D 弧面圆柱切片流光全景展厅落地）
- **按需挂载全局 Skills**：
  - `emil-design-eng`（微切片缝隙消隐、`:active` 物理缩放微触感、去 AI 廉价发光感）
  - `apple-design`（毛玻璃景深透视、Design Tokens 亮暗主题自适应、通透克制审美）
  - `animate` 与 `animation-performance`（严格保持在合成层 `transform` 运动、`will-change` 正确使用、杜绝重排）
  - `break-ui`（卡片文字自适应、极端长文本防破框截断保护）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_14-36-00_tilted_grid_showcase_demo_plan.md
- 记录时间戳：2026-11-02 14:36:00
- 前端目标文件：
  docs/design/spd_tilted_grid_hero_demo.html —— 医院医疗物资全链路 3D 弧面圆柱流光全景展厅原型 Demo（原生高精度实现 21st.dev 规范：SLICES=16 垂直微切片圆柱几何面逼近算法、透视摄像机 CAMERA=1.6、圆柱弧度曲率半径计算、横向右至左无限无缝流光带、两端弯曲渐隐、中央正视平整面、中央通透悬浮主舞台、亮暗双色主题无级自适应）
- 后端目标文件：无（后端服务保持只读隔离，不改动任何源码）
- 测试与截图文件：
  1. tests/harness/verify_tilted_grid_demo.js —— 驱动 Playwright 验证 3D 弧面圆柱切片结构、无 Emoji 静态审计、主题切换、CTA 按钮响应并截屏归档
  2. tests/screenshots/2026-11-02_14-36-00_tilted_grid_hero_light.png —— 亮色实机全景验证图
  3. tests/screenshots/2026-11-02_14-36-00_tilted_grid_hero_dark.png —— 暗色大屏沉浸式验证图
```

---

## 二、 核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`98%`
- **潜在技术风险与预案**：
  - **风险点 1（16 微切片切面微缝与白边瑕疵）**：原生 CSS 3D 在切片分面拼接时，由于 GPU 浮点渲染取整，可能在相邻切片之间产生 0.5px 发丝级白色微缝。**应对策略**：切片宽度严格遵循 `calc(u(share) + 1px)` 进行像素微重叠，消除拼缝白线；最右末端切片不加重叠，保证卡片外轮廓规整；
  - **风险点 2（圆柱曲率与摄像机参数精度）**：摄像机距离 `CAMERA = 1.6`，半径公式 `r = (CAMERA - 1 + cosθ) / (2 * CAMERA * sinθ)`。**应对策略**：使用 JavaScript/CSS 动态计算容器尺寸与极坐标变换，确保切片在不同屏幕宽度下弯曲弧度一致且两端自然淡出；
  - **风险点 3（全域禁用 Emoji 铁律）**：医疗卡片及展厅所有按钮严禁出现 Emoji。**应对策略**：全部采用统一的纯矢量内联 SVG 细线图标。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：提供极具未来感的 IMAX 环幕胶卷流光视效，物料带犹如流动的生命线，中央主舞台提供清晰明了的业务切入点与指标概览；
- **开发者体验（DX）**：完全遵循组件化思维，后续可无缝转译为 shadcn 标准组件规范（`/components/ui/tilted-grid-hero.tsx`）；
- **AI 代理体验（AX）**：DOM 结构具有严密的 `tgh-tile`、`tgh-slice` 语义类名，自动化测试脚本能够精准探测动画状态与计算几何尺寸；
- **存量功能零破坏**：文件独立存放在 `docs/design/` 下，与已交付的 `spd_orbital_hero_demo.html` 和 `spd_frontend_design_variants.html` 保持零耦合互通。

### 3. Playwright 自动化回环测试与截图验证方案
- **验证脚本**：`tests/harness/verify_tilted_grid_demo.js`
- **自动化测试断言链路**：
  1. 静态扫描 `docs/design/spd_tilted_grid_hero_demo.html`，断言 100% 零 Emoji 违规；
  2. 启动 Playwright 无锁浏览器加载页面，断言 3D 圆柱体流光容器存在且已挂载医疗物料卡片；
  3. 检验切片节点（`.tgh-slice`）是否正确生成且应用 3D 变换；
  4. 验证中央主舞台、徽标、CTA 按钮完整可见；
  5. 触发亮暗主题双向切换；
  6. 校验 Console Error = 0，分别截取亮色与暗色高清实机验证图保存至 `tests/screenshots/`。

---

## 三、 技术与 UI 细节规范

### 1. 3D 弧面圆柱流光带 10 大医疗物料资产卡片
1. `#01`：**产品字典双维档案**（UDI 编码标准化 · 耗材/设备主库双归口）
2. `#02`：**主库验收入库**（冷链与有效期限硬风控 · 注册证资质智能比对）
3. `#03`：**院内按需流转分发**（近效期先出 FEFO 原则 · 移库不计费）
4. `#04`：**高值专柜一物一码**（拆包由量到码赋唯一 SN · 智能柜锁定）
5. `#05`：**临床二级库定数包**（病区安全水位监测 · 自动低库存补货预警）
6. `#06`：**患者扫码脱敏核销**（手术记账脱敏保护 · 临床消耗即结算）
7. `#07`：**6W 物权交接流转台账**（人/物/时间/流向完整快照 · 100%审计穿透）
8. `#08`：**医院法定四联签字单**（制单/主库/领用/财务责任闭环签章）
9. `#09`：**Agent 02 补货智能体**（多库房水位扫描 · LangGraph 自动下发调拨）
10. `#10`：**Agent 04 逆向召回智能体**（不良事件穿透追溯 · 一键批次全局冻结）

### 2. 视觉质感与主题规范
- **Light 模式**：背景高雅柔和 `#f8fafc`，卡片采用半透明瓷白与超细微边框，文字为高对比深灰蓝 `#0f172a`；
- **Dark 模式**：背景深邃黑 `#080c14`，卡片采用深色太空玻璃与青蓝冷光微边框，文字为冰蓝白 `#f8fafc`；
- **两端曲面遮罩（Fade Mask）**：`linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent)`，使卡片在两端弯曲靠近视点时自然渐隐进背景。

---

## 四、 强制性原子实施清单

```markdown
实施清单（全部完成）：
1. [已完成] [docs/design/] 创建 docs/design/spd_tilted_grid_hero_demo.html，实现 16-切片圆柱 3D 曲面计算、横向无缝流光带、中央通透主舞台、三级角色工作台跳转按钮、亮暗主题切换。
2. [已完成] [tests/] 编写 tests/harness/verify_tilted_grid_demo.js，配置 Playwright 自动化测试脚本，执行静态无 Emoji 审计、切片节点存在性与控制台 0 报错断言。
3. [已完成] [tests/ | plans/] 运行 node tests/harness/verify_tilted_grid_demo.js，捕获亮暗两套实机高清截图归档至 tests/screenshots/。
4. [已完成] [plans/] 更新 plans/ 台账记录，向用户输出对比审阅报告。
```
