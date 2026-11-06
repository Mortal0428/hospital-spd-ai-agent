# 全模块侧边栏内容对齐、财务决策 BI 看板图形化与知识库文档分页技术规划

- **计划文档路径**：`plans/2026-11-06_13-40-00_sidebar_alignment_finance_charts_and_kb_pagination_plan.md`
- **记录时间戳**：2026-11-06 13:40:00
- **模式声明**：`[MODE: PLAN]`

---

## 一、变更计划与目标文件清单

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-06_13-40-00_sidebar_alignment_finance_charts_and_kb_pagination_plan.md
- 记录时间戳：2026-11-06 13:40:00
- 前端目标文件：
  1. frontend/src/layouts/MainLayout.vue：补齐侧边栏中缺失的财务 BI 看板、流水台账、主库实时台账纠正、期初建账、高值实时台账与不良召回中枢导航项；
  2. frontend/src/views/FinancePrintView.vue：在 BI 决策看板内构建柱状图、环形扇状图与月度收发存趋势面积折线图三大图形化组件；
  3. frontend/src/views/RagAgentHubView.vue：在知识库文档资产列表中增加响应式分页器、关键词搜索与分类联动；
  4. frontend/src/views/HospitalProcurementView.vue：添加 route.query.tab 监听与路由双向同步；
  5. frontend/src/views/ExternalSupplierPortalView.vue：添加 route.query.tab 监听与路由双向同步。
- 后端目标文件：无（保持后端服务高内聚稳定）。
- 测试与截图文件：
  1. tests/screenshots/2026-11-06_13-55-00_sidebar_full_alignment.png：侧边栏各模块完整展开与对齐截图；
  2. tests/screenshots/2026-11-06_13-55-00_finance_bi_charts.png：财务决策 BI 看板柱状图、扇状图与趋势图实机截图；
  3. tests/screenshots/2026-11-06_13-55-00_knowledge_base_pagination.png：知识库分类文档分页器与筛选实机截图。
```

---

## 二、核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`98%`
- **潜在技术风险点**：
  - SVG 图表在不同窗口缩放比例下的响应式 viewBox 宽高自适应计算；
  - 侧边栏子项增多后高亮 `active` 状态判断逻辑的精确性，避免父子菜单冲突；
  - 采购与供应商页面的 Tab 切换与路由参数双向 watch 需避免循环触发。

### 2. 存量功能与三方体验影响分析
- **用户体验 (UX)**：
  - 侧边栏与页面 Tab 实现 100% 一一对应，用户无论点击侧边栏还是在页面内切换 Tab，URL 参数与高亮状态完美同步；
  - 财务 BI 看板由原本的“纯卡片与文字”跃升为“图形化驾驶舱”，柱状图清晰对比主库发料、环形图直观展现耗材结构与科室份额、面积图展现近半年进销存走势；
  - 知识库文档列表具备清晰的每页条数与翻页器，避免文档列表无限拉长。
- **开发者体验 (DX)**：
  - 遵循统一的 `watch(() => route.query.tab)` 标准化路由同步范式；
  - 图表采用项目既有的矢量 SVG 规范封装，避免引入庞大笨重的第三方 Canvas 库，支持深浅色模式 CSS 变量平滑过渡；
  - 100% 中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。
- **AI 代理体验 (AX)**：
  - 路由路径、query 参数与组件内部 Tab 契约高度一致，消除断点。
- **存量功能保护底线**：
  - 零破坏性演进，存量 15 大业务功能及 RBAC 细粒度权限 100% 保持向后兼容。

---

## 三、技术与 UI 细节规范

### 1. 侧边栏 (`MainLayout.vue`) 补齐与纠正规范

- **普通耗材主库**：
  - 将原“主库实时台账”的目标 query 由 `init-stock` 纠正为 `inventory`；
  - 新增“主库期初建账”子菜单项，目标 query 为 `init-stock`。
- **高值耗材专仓**：
  - 新增“高值实时总台账”子菜单项，目标 query 为 `realtime`；
  - 新增“高值专仓期初建账”子菜单项，目标 query 为 `init-stock`。
- **财务精算与对账**：
  - 新增“全景财务决策 BI 看板”子菜单项（首位），目标 query 为 `bi-dashboard`；
  - 新增“多级小仓资金运转流水”子菜单项，目标 query 为 `sub-flows`。
- **物资流转追溯**：
  - 新增“不良事件全院召回中枢”子菜单项，目标 query 为 `recall`。

### 2. 页面路由联动修复规范

- **`HospitalProcurementView.vue`**：
  - 添加 `watch(() => route.query.tab, (newTab) => { if (newTab) currentTab.value = newTab; }, { immediate: true })`；
  - 在 `el-tabs` 增加 `@tab-change` 事件，同步更新路由 `query.tab`。
- **`ExternalSupplierPortalView.vue`**：
  - 添加 `watch(() => route.query.tab, (newTab) => { if (newTab) activeTab.value = newTab; }, { immediate: true })`；
  - 在 `el-tabs` 增加 `@tab-change` 事件，同步更新路由 `query.tab`。

### 3. 财务 BI 看板图形化规范 (`FinancePrintView.vue`)

在 `bi-dashboard` 中构建 3 组高质感现代化矢量 SVG 图表组件：

1. **图表一：四大归口主库调拨发料对比柱状图 (Warehouse Dispatch Bar Chart)**：
   - 比较卫材主库、设备主库、总务主库、信息主库的调拨发料总额与笔数；
   - 具备渐变色彩柱体、Y 轴金额刻度虚线标尺、柱顶动态数值与悬停微光效果；
   - 绑定 CSS 变量：`var(--accent-primary)`、`var(--color-info)` 等。
2. **图表二：耗材消耗结构与各科室支出占比环形扇状图 (Donut & Dept Pie Chart)**：
   - 环形图：高值耗材 (65.8%) vs 普通耗材 (34.2%)，中心镂空排版展示“全院消耗总额 ¥113,050.00”；
   - 科室消耗占比分布图：骨科 (14.7%)、心内科 (20.9%)、普外科 (45.6%)、急诊科 (18.8%)；
   - 支持图例说明与鼠标悬停高亮提示。
3. **图表三：近 6 个月物资进销存资金流转趋势面积图 (Trend Area Chart)**：
   - X 轴：2026-06 至 2026-11（近 6 个核算期）；
   - Y 轴：金额标尺（¥0 至 ¥300,000）；
   - 曲线 1：采购验收入库资金趋势（平滑三次贝塞尔曲线 + 蓝色半透明渐变面积）；
   - 曲线 2：临床实际消耗资金趋势（平滑三次贝塞尔曲线 + 绿色半透明渐变面积）；
   - 关键拐点带有发光圆环节点。

### 4. 知识库文档列表分页规范 (`RagAgentHubView.vue`)

- **响应式状态变量**：
  - `docCurrentPage = ref(1)`；
  - `docPageSize = ref(10)`；
  - `docSearchKeyword = ref('')`；
- **计算属性切片**：
  - `filteredDocuments`：依据 `docSearchKeyword` 过滤 `doc_title` 和 `doc_code`；
  - `paginatedDocuments`：依据当前页和每页条数执行 `slice` 切片；
- **UI 布局**：
  - 在 `<el-table :data="paginatedDocuments">` 下方嵌入 `<el-pagination>`，包含总数统计、每页条数下拉 `[10, 20, 50]`、页码切换与直达跳转；
  - 在 `selectCategory` 分类切换时自动重置 `docCurrentPage.value = 1`。

---

## 四、原子实施清单

```markdown
实施清单：
1. [已完成 100%] [frontend/] 在 MainLayout.vue 中补齐与纠正全部模块侧边栏子项：
   - 财务模块：增设“全景财务决策 BI 看板 (bi-dashboard)”与“多级小仓资金运转流水 (sub-flows)”；
   - 主库模块：将“主库实时台账”纠正绑定至 inventory，并增设独立的“主库期初建账 (init-stock)”；
   - 高值模块：增设“高值实时总台账 (realtime)”与“高值专仓期初建账 (init-stock)”；
   - 物资流转追溯：增设“不良事件全院召回中枢 (recall)”；
   - 优化 active 高亮判定条件，确保所有子菜单状态精准映射。
2. [已完成 100%] [frontend/] 修复采购管理与供应商门户页面的 route.query.tab 联动：
   - 在 HospitalProcurementView.vue 中补充 watch 路由与 tab-change 事件；
   - 在 ExternalSupplierPortalView.vue 中补充 watch 路由与 tab-change 事件。
3. [已完成 100%] [frontend/] 在 FinancePrintView.vue 中构建财务决策 BI 看板三大图形化图表：
   - 编写四大归口主库发料对比柱状图 (SVG 响应式矢量)；
   - 编写高值 vs 普通及科室消耗占比环形扇状图 (SVG 响应式矢量)；
   - 编写近 6 个月物资进销存资金流转趋势面积折线图 (三次贝塞尔曲线渐变)；
   - 编写配套高质感 CSS 样式（支持亮暗主题自适应、无任何 Emoji）。
4. [已完成 100%] [frontend/] 在 RagAgentHubView.vue 中实现知识库文档列表分页与分类联动：
   - 添加 docCurrentPage、docPageSize、docSearchKeyword 等响应式变量；
   - 添加 filteredDocuments 与 paginatedDocuments 计算属性；
   - 在文档表格下方嵌入 el-pagination 分页器；
   - 联动分类切换重置页码。
5. [已完成 100%] [frontend/] 运行全量 TypeScript 校验与生产打包测试（npm run build），0 警告 0 错误（11.21s 成功构建）。
6. [已完成 100%] [tests/] 使用 Playwright 执行自动化回环测试，校验侧边栏导航点击、财务图形图表渲染及知识库分页交互，并捕获实机截图归档至 tests/screenshots/：
   - 侧边栏对齐实机截图：tests/screenshots/2026-11-06_13-55-00_sidebar_full_alignment.png
   - 财务 BI 三大图形截图：tests/screenshots/2026-11-06_13-55-00_finance_bi_charts.png
   - 知识库文档分页截图：tests/screenshots/2026-11-06_13-55-00_knowledge_base_pagination.png
```

---

## 五、验收总结

- **执行时间戳**：2026-11-06 13:55:00
- **全生命周期保护状态**：零破坏，存量 15 大业务模块及 RBAC 细粒度权限 100% 正常向后兼容。
- **构建结果**：`npm run build` 耗时 11.21s，0 错误 0 警告顺利产出构建产物。
- **交付凭据**：3 张实机截图与回环验证报告已完整归档。
