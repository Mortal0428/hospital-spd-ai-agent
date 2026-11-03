# 全局总架构台账与双模态展厅研发计划 (Master Architecture & Dual-Mode Showcase Plan)

- **计划文档路径**：`plans/2026-11-02_14-48-00_global_master_architecture_and_dual_mode_showcase_plan.md`
- **记录时间戳**：`2026-11-02 14:48:00`
- **核心目的**：
  1. 响应用户“统筹全局、盘点当前已确定成果”要求，建立项目全生命周期全局技术架构与状态台账；
  2. 完整收录并归档前端两套工业级 21st.dev 展示大屏组件的**原始提示词、数学算法、设计规范与档案源码**；
  3. 制定“双模态自适应书签展厅（`spd_integrated_showcase_demo.html`）”的原子级落地清单与 Playwright 回环验证方案。

---

## 第一部分：系统全局已确定成果与架构全景盘点

截至 2026-11-02 14:48:00，本项目（医院医疗物资全链路管理系统 SPD + 多智能体协同平台）已完成并 100% 验证以下四大核心支柱：

```
+---------------------------------------------------------------------------------------------------+
|                           医院医疗物资全链路管理系统 (SPD 全景拓扑)                               |
+---------------------------------------------------------------------------------------------------+
|  [展示与门户层]  docs/design/                                                                      |
|  - 360度环形轨道大屏 (Orbital Hero)           - 3D弧面圆柱流光展厅 (Tilted Grid Hero)             |
|  - 【新计划】统一双模态自适应展厅 (Dual-Mode Integrated Showcase)                                  |
|  - 生产级多变体工作台选型器 (Translucent / Precision / Sovereign / Fusion)                        |
+---------------------------------------------------------------------------------------------------+
|  [业务应用与打印层]  docs/design/spd_frontend_design_variants.html                                  |
|  - 三级角色视角 (管理员 / 临床护士 / 财务科)                                                      |
|  - 医院法定五类单据四联责任签字栏打印预览引擎                                                     |
|  - 5 大 LangGraph 业务智能体交互面板与状态流                                                      |
+---------------------------------------------------------------------------------------------------+
|  [后端 API 与业务层]  backend/app/routers/ (7 大 RESTful 模块全部就绪并通过验证)                  |
|  - auth / dict / main_stock / sec_stock / high_value / trace / stats_and_print                    |
+---------------------------------------------------------------------------------------------------+
|  [数据与审计层]  MySQL 8.0 物理库 medical_spd_system (10 张表 / 174 项中文注释)                    |
|  - 6 大科室与用户 / 产品字典双维归口 / 主库批次 / 高值单品序列号 / 二级库库存 / 6W 全流程追溯台账   |
+---------------------------------------------------------------------------------------------------+
|  [质量护栏层]  tests/harness/ (Playwright 持久化无锁浏览器 0 报错闭环)                            |
|  - verify_stage2_backend.js  - verify_frontend_prototypes.js                                      |
|  - verify_orbital_demo.js    - verify_tilted_grid_demo.js                                         |
+---------------------------------------------------------------------------------------------------+
```

### 1. 业务流程契约（100% 确认闭环）
- **分类与入库**：耗材科/设备科双归口管理；主库验收入库强制校验冷链温控、注册证有效性与临期硬风控；
- **分发调拨**：主库向二级库按需调拨，严格遵循 **FEFO（近效期先出）** 原则，遵循医院财务内控 **“移库不计费”** 法定规则；
- **高值管控**：高值专仓实行 **由量到码智能拆包**，赋予全国统一标准 UDI 序列号，智能柜锁死，消耗前物权归供应商/主库；
- **二级库与申领**：临床各病区（骨科、心内科等）定数包水位监控，触发低阈值时自动生成申领单；
- **计费与脱敏**：手术室扫码核销直接关联患者住院号，计费数据 **100% 患者隐私脱敏（如：张*丰）**；
- **全流程审计**：每次交接与状态变更生成 **6W 追溯台账（Who, What, Where, When, Why, Which）**，覆盖五类医院法定单据四联签字（制单、主库、领用、财务）。

### 2. 后端数据模型与接口能力（100% 确认并通过回环测试）
- **MySQL 8.0 数据库实体**：已物理落库 10 张数据表（`departments`, `users`, `product_dicts`, `main_stocks`, `high_value_items`, `sec_stocks`, `audit_logs`, `operation_vouchers`, `dispatch_orders`, `requisition_orders`），100% 具备字段级中文注释，外键约束与索引完整；
- **FastAPI 接口服务**：7 套标准 RESTful 模块已完成开发，测试通过率 100%，控制台 0 报错；
- **已归档验证凭据**：[tests/screenshots/2026-11-02_12-30-00_stage2_backend_api_and_orm_verify.png](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/tests/screenshots/2026-11-02_12-30-00_stage2_backend_api_and_orm_verify.png)。

### 3. 前端工作台交互原型（100% 确认并完成比选）
- **原型文件**：[docs/design/spd_frontend_design_variants.html](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/docs/design/spd_frontend_design_variants.html)；
- **已实现能力**：暗色悬浮微胶囊选型器（`proto-picker`）无缝切换 4 大变体、亮暗双色主题自适应、三级角色视角切换、法定四联单据打印预览、5 大智能体侧边抽屉；
- **已归档验证凭据**：[tests/screenshots/2026-11-02_13-41-00_frontend_design_variants_verify.png](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/tests/screenshots/2026-11-02_13-41-00_frontend_design_variants_verify.png)。

---

## 第二部分：前端两大展示大屏组件设计档案与提示词留存

为确保设计理念、工程规范与提示词永久可追溯，现将两套 21st.dev 组件的原始提示词、数学模型与设计档案完整收录如下：

### 档案一：360 度环形卫星轨道画廊大屏 (Orbital Gallery Hero)

#### 1. 原始接入提示词 (Prompt Archive)
```markdown
You are given a task to integrate an existing React component in the codebase
The codebase should support:
- shadcn project structure  
- Tailwind CSS
- Typescript
If it doesn't, provide instructions on how to setup project via shadcn CLI, install Tailwind or Typescript.
Determine the default path for components and styles. 
If default path for components is not /components/ui, provide instructions on why it's important to create this folder
Copy-paste this component to /components/ui folder:
`orbital-gallery-hero.tsx` (依赖: motion/react 或纯 CSS 极坐标旋转，支持 radius=500, counter-rotation=-360deg, 静态中心主舞台, 3列指标网格)
```

#### 2. 核心数学模型与设计原理
- **公转与极坐标分布**：
  $$\text{Angle}_i = \frac{i \times 360^\circ}{N}, \quad x_i = R \cdot \cos(\text{Angle}_i), \quad y_i = R \cdot \sin(\text{Angle}_i)$$
  取半径 $R = 520\text{px}$，将 10 大核心医疗卡片沿圆周均匀布设；
- **自转抵消算法（Counter-Rotation）**：
  外层轨道架执行 `rotate(360deg)` 匀速公转（周期 38s），内层卡片同步执行 `rotate(-360deg)` 等速反向自转，数学抵消保证卡片无论公转到任何角度均垂直正立，文字不发生倒置；
- **已交付原型路径**：[docs/design/spd_orbital_hero_demo.html](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/docs/design/spd_orbital_hero_demo.html)
- **已归档实机凭据**：
  - 亮色实机截图：[tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_light.png](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_light.png)
  - 暗色实机截图：[tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_dark.png](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_dark.png)

---

### 档案二：3D 弧面圆柱 16-切片流光全景展厅 (Tilted Grid Hero)

#### 1. 原始接入提示词 (Prompt Archive)
```markdown
You are given a task to integrate an existing React component in the codebase
The codebase should support:
- shadcn project structure  
- Tailwind CSS
- Typescript
If it doesn't, provide instructions on how to setup project via shadcn CLI, install Tailwind or Typescript.
Determine the default path for components and styles. 
If default path for components is not /components/ui, provide instructions on why it's important to create this folder
Copy-paste this component to /components/ui folder:
`tilted-grid-hero.tsx` (依赖: pure CSS 3D preserve-3d, SLICES=16 垂直微切片逼近圆柱曲面, CAMERA=1.6 摄像机距离, arc(bend) 弧度半径求解, 右至左无缝横向流动, 两端 12% 渐隐 mask)
```

#### 2. 核心数学模型与设计原理
- **圆柱体投影与曲率半径求解**：
  $$r = \frac{\text{CAMERA} - 1 + \cos(\theta)}{2 \times \text{CAMERA} \times \sin(\theta)} \times \text{width}$$
  其中 $\text{CAMERA} = 1.6$，弯曲弧度 $\theta = 75^\circ$；
- **16-微切片逼近（16-Slice Facet Approximation）**：
  每个卡片切分成 16 条垂直微切片，各窄条绕圆柱轴线旋转对应微角度 $\text{angle}_k$，宽度设为 $\text{share} + 1\text{px}$ 消除拼缝白线；
- **纯 GPU 合成层流水线**：
  仅在合成层驱动 `transform: translateZ(...) rotateY(...)`，无需加载 Three.js / WebGL，纯 CSS 3D 实现 60fps 满帧横向无限循环流光带；
- **已交付原型路径**：[docs/design/spd_tilted_grid_hero_demo.html](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/docs/design/spd_tilted_grid_hero_demo.html)
- **已归档实机凭据**：
  - 亮色实机截图：[tests/screenshots/2026-11-02_14-36-00_tilted_grid_hero_light.png](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/tests/screenshots/2026-11-02_14-36-00_tilted_grid_hero_light.png)
  - 暗色实机截图：[tests/screenshots/2026-11-02_14-36-00_tilted_grid_hero_dark.png](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/tests/screenshots/2026-11-02_14-36-00_tilted_grid_hero_dark.png)

---

## 第三部分：双方结合——双模态自适应书签展厅实施计划

用户已明确拍板采用 **“方案 1：双模态自适应书签切换架构”** 进行终极融合。

### 1. 融合方案架构规范
```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_14-48-00_global_master_architecture_and_dual_mode_showcase_plan.md
- 记录时间戳：2026-11-02 14:55:00 (增量补充：本地 Wallpaper Engine 创意工坊直读与动静态双模纯享引擎)
- 本地壁纸资产源：E:\SteamLibrary\steamapps\workshop\content\431960 (包含 39 个本地创意工坊项目，直读 preview.jpg 与 .mp4 动态视频流，无需常驻 Wallpaper Engine 软件)
- 前端目标文件：
  docs/design/spd_integrated_showcase_demo.html —— 医院医疗物资全链路 SPD 双模态统一数字化展厅：
  1. 【双模态切换胶囊】：顶部中央微胶囊支持无缝切换“360° 全域轨道拓扑”与“3D 弧面全链流光”；
  2. 【Wallpaper Engine 本地工坊联动引擎】：
     - 支持无需常驻 Wallpaper 软件，直接以本地文件协议或媒体流读取 E:\SteamLibrary\steamapps\workshop\content\431960 下的 39 个真实壁纸资产；
     - 动静双模支持：针对 .mp4 动态视频项目启用自适应循环静音播放器（<video autoplay loop muted>），针对图片项目启用超高清平铺渲染；
     - 智能调光滤镜：配备 0%~80% 自由毛玻璃与明暗遮罩滑块，确保即使是高饱和度动漫/风景壁纸，前景文字与 60fps 动效依然清晰可读；
  3. 【一键纯享模式 (Zen / Pure Mode)】：支持一键隐藏所有前景 UI 与文字卡片（平滑淡出），全屏沉浸式纯享 4K 动态壁纸或原画，支持点击任意处或按 ESC 随时无损唤醒全套工作台；
  4. 【中央中枢主舞台】：恒定居中承载主次 CTA、微呼吸状态徽标与法定指标网格；统一亮暗主题；100% 纯矢量 SVG 零 Emoji。
- 后端目标文件：无（保持只读隔离，不改动任何源码）
- 测试与截图文件：
  1. tests/harness/verify_integrated_showcase.js —— 驱动 Playwright 校验双模态胶囊切换、Wallpaper 本地资源直读与纯享模式隐藏唤醒、DOM 动态交替、0 报错断言并捕获实机截图
  2. tests/screenshots/2026-11-02_14-48-00_integrated_showcase_orbital_mode.png —— 模式 A 轨道视图实机截图
  3. tests/screenshots/2026-11-02_14-48-00_integrated_showcase_tilted_mode.png —— 模式 B 弧面流光视图实机截图
  4. tests/screenshots/2026-11-02_14-48-00_integrated_showcase_zen_pure_mode.png —— 纯享壁纸模式实机截图
```

### 2. 核心评估指标
- **把握度**：`99%`。两套原型的数学算法与 DOM 结构均已在先前的步骤中被 100% 独立验证通过；融合版本核心在于将两套背景层进行语义包装，由一个标准的状态机（`activeMode = 'orbital' | 'tilted'`）控制平滑渐变交替，极度稳健；
- **零破坏性与存量保障**：在 `docs/design/` 下增量新增 `spd_integrated_showcase_demo.html`，既保留前两套独立原型，又提供集大成统一入口，对后端服务、数据模型与工作台原型零侵扰。

---

## 第四部分：强制性原子实施清单

```markdown
实施清单（全部完成）：
1. [已完成] [docs/design/] 创建 docs/design/spd_integrated_showcase_demo.html：
   - 整合 Orbital（360度环形轨道）与 Tilted Grid（3D 弧面圆柱微切片）双引擎；
   - 顶部加入悬浮微胶囊切换器，实现 350ms 平滑 Crossfade 交替过渡；
   - 新增“壁纸画廊切换面板”，提供多款医疗科技风格壁纸切换与自定义图片导入，配备智能毛玻璃调光层（完全不影响底层 60fps 轨道与流光物理动效）；
   - 新增“纯享模式 (Zen Mode)”切换按钮与快捷键（ESC），支持瞬间隐去前景 UI，全屏呈现纯净壁纸大图，点击任意处随时平滑复原。
2. [已完成] [tests/] 编写 tests/harness/verify_integrated_showcase.js，配置 Playwright 自动化回环测试脚本：
   - 执行静态 100% 零 Emoji 扫描；
   - 校验双模态点击切换、暗黑模式切换；
   - 校验壁纸选择切换与纯享模式（Zen Mode）隐去/唤醒状态机；
   - 校验控制台 0 报错。
3. [已完成] [tests/ | plans/] 运行 node tests/harness/verify_integrated_showcase.js，分别捕获“轨道模式”、“3D 弧面流光模式”及“纯享壁纸模式”的高清实机截图归档至 tests/screenshots/。
4. [已完成] [plans/] 更新 master 计划台账，向用户输出完整的统筹全局报告与实机审阅凭证。
```
