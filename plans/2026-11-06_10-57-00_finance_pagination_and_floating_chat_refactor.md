# 研发实施规划：财务模块四大台账分页/分类/检索与全局浮动聊天窗口头部重构

- **计划文档路径**：`plans/2026-11-06_10-57-00_finance_pagination_and_floating_chat_refactor.md`
- **记录时间戳**：`2026-11-06 10:57:00`
- **前端目标文件**：
  - `frontend/src/views/FinancePrintView.vue`（构建四大核算台账的分页、分类与多维检索筛选器）
  - `frontend/src/components/AgentChatWidget.vue`（重构浮动聊天窗口头部为高质感双层结构，彻底消灭字符断行与推挤挤压）
- **测试与截图文件**：
  - `tests/screenshots/2026-11-06_11-15-00_finance_pagination_and_filtering.png`
  - `tests/screenshots/2026-11-06_11-15-00_floating_chat_uncompressed_header.png`

---

## 一、核心评估指标

1. **可行性与把握度评估**：
   - **把握度：99%**。
   - 前端采用 Vue 3 响应式 `computed` 驱动的筛选与分页体系，针对毫秒级即时检索（单号、代码、品名、科室）与分类联动，无需重复发起额外网络请求，顶部的指标卡聚合（`totalDispatchAmount`、`totalConsumptionAmount`）保持全量基数精准无误；
   - 浮动窗口采用 Apple / Emil Kowalski 双层结构卡片设计，主标题栏与次级能力工具栏各司其职，宽度从 `440px` 微调至舒适的 `470px`，完全消灭文字挤压折行。

2. **存量功能与三方体验（UX/DX/AX）影响分析**：
   - **用户体验（UX）**：财务人员面对海量对账明细时，可快速通过主库归口、科室名称或单号模糊过滤，并支持每页 10/20/50 条分页翻阅；浮动窗口无论在哪个业务页面打开，标题与开关均呼吸感十足、通透明晰。
   - **开发者体验（DX）**：使用标准化命名与中文注释；计算属性逻辑高内聚、低耦合；保留原有打印穿透与行级展开事件契约。
   - **AI 代理体验（AX）**：属性与方法契约清晰，无动态黑盒逻辑，易于跨轮次定位与维护。
   - **存量功能保护**：Tab 2 物料级懒加载穿透子表（`handleDeptExpandChange`）、四联单据打印引擎（`PrintVoucherDialog.vue`）、RBAC 打印权限判定（`canAction`）100% 保持零破坏。

3. **Playwright 自动化回环测试与截图验证方案**：
   - 编写/调用自动化测试脚本，导航至 `/finance` 视图：
     - **断言 1**：Tab 1、Tab 2、Tab 3 底部各成功渲染 `.el-pagination` 分页组件，页码切换与每页条数切换正常生效；
     - **断言 2**：在 Tab 1 输入模糊关键字（如 `DIST` 或 `骨科`），表格行数实时精准过滤，且底部分页器条目数同步联动；
     - **断言 3**：切换分类下拉（如选择“卫材主库”或“在途待签收”），表格精准呈现对应子集；
     - **断言 4**：点击唤起右下角浮动聊天窗口，测量头部文字无竖向折行，开关与收起按钮排布清晰整齐，控制台 0 报错；
     - **断言 5**：生成实机实测截图归档至 `tests/screenshots/`。

---

## 二、技术与 UI 细节规范

### 1. 财务模块分页、分类与检索设计 (`FinancePrintView.vue`)

#### Tab 1: 四大主库发料流向对账
- **状态变量**：
  - `mainWarehouseFilter`: 归口主库分类（`ALL` | `卫材主库` | `设备主库` | `总务主库` | `信息主库`）
  - `reconcileStatusFilter`: 对账状态分类（`ALL` | `已接收验收入账` | `在途待签收` | `差异拒收退库`）
  - `mainSearchKeyword`: 搜索关键词（支持单号 `order_no`、代码 `product_code`、科室 `target_dept`、品名 `product_name`）
  - `mainCurrentPage`: 当前页码（默认 1）
  - `mainPageSize`: 每页条数（默认 10，选项 `[10, 20, 50, 100]`）
- **计算属性**：
  - `filteredMainDispatchList`: 响应式多重过滤后的数据清单
  - `paginatedMainDispatchList`: 当前页切片子集 `filteredMainDispatchList.slice((page-1)*size, page*size)`

#### Tab 2: 科室领用与消耗支出对账
- **状态变量**：
  - `deptRiskFilter`: 耗占比合规等级分类（`ALL` | `合规达标` | `预警关注`）
  - `deptSearchKeyword`: 科室搜索关键词（科室名称 `dept_name` 或编码 `dept_code`）
  - `deptCurrentPage`: 当前页码（默认 1）
  - `deptPageSize`: 每页条数（默认 10，选项 `[10, 20, 50]`）
- **计算属性**：
  - `filteredDeptCostList` 与 `paginatedDeptCostList`

#### Tab 3: 全院进销存收发存月度平衡表
- **状态变量**：
  - `balanceWarehouseFilter`: 仓库类型分类（`ALL` | `MAIN` 主库总仓 | `SEC` 病区二级库）
  - `balanceStatusFilter`: 平衡状态分类（`ALL` | `严格平账` | `差异预警`）
  - `balanceSearchKeyword`: 仓库搜索关键词（`warehouse_name` | `warehouse_code`）
  - `balanceCurrentPage`: 当前页码（默认 1）
  - `balancePageSize`: 每页条数（默认 10，选项 `[10, 20, 50]`）
- **计算属性**：
  - `filteredBalanceList` 与 `paginatedBalanceList`

---

### 2. 浮动聊天窗口头部重构设计 (`AgentChatWidget.vue`)

针对目前单行水平排列导致汉字竖向断行（“流/式”、“深思/度考”）的严重视觉缺陷，重构为双层现代克制卡片头部：

```html
<!-- 浮动模式专用高质感双层头部 -->
<div class="widget-header floating-header-dual">
  <!-- 第一层：主要标识与窗口操作栏 -->
  <div class="header-primary-row">
    <div class="header-agent-identity">
      <span class="agent-avatar-badge font-mono font-bold">{{ agentId.toUpperCase() }}</span>
      <div class="agent-name font-bold">{{ agentTitle }}</div>
      <span class="header-status-indicator" title="AI 在线守护中" />
    </div>
    <div class="header-window-actions">
      <span class="status-chip chip-active">AI 守护中</span>
      <button class="btn-widget-icon" title="收起助手" @click="isFloatingOpen = false">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>
    </div>
  </div>

  <!-- 第二层：架构特征微标签与能力开关工具条 -->
  <div class="header-secondary-toolbar">
    <div class="agent-arch-pill font-mono">
      {{ architectureTag }}
    </div>
    <div class="header-switches-group">
      <div class="switch-item">
        <span class="switch-label">流式</span>
        <el-switch v-model="enableStream" size="small" />
      </div>
      <div class="switch-item">
        <span class="switch-label">深度思考</span>
        <el-switch v-model="enableDeepThinking" size="small" />
      </div>
    </div>
  </div>
</div>
```

- **关键样式规则**：
  - 浮动窗口宽度由 `440px` 微调为 `470px`，高度保持 `580px`，完美适应 1080P/2K 分辨率；
  - 所有开关文本标签强制声明 `white-space: nowrap; user-select: none;`；
  - 架构标签采用轻量级胶囊背景，与流式/深度思考开关左右呼应，横向空间充足，绝无拥挤变形。

---

## 三、原子级实施清单

1. **[frontend/] 重构全局浮动聊天窗口头部与样式**：
   - 修改 `frontend/src/components/AgentChatWidget.vue`；
   - 将 `v-if="floating"` 内的 `.widget-header` 替换为双层结构（`floating-header-dual`）；
   - 增加 `.header-primary-row`、`.header-secondary-toolbar`、`.switch-item` 等 CSS 类；
   - 调整 `.floating-agent-window` 宽度为 `470px` 并添加 `white-space: nowrap` 护栏；
   - 确保全域无 Emoji，使用原生 SVG 与 Element Plus 图标。

2. **[frontend/] 升级财务模块 Tab 1（四大主库发料流向对账）**：
   - 修改 `frontend/src/views/FinancePrintView.vue`；
   - 在 `.pane-action-bar` 中集成归口主库下拉框、对账状态下拉框与关键词搜索框；
   - 声明 `mainWarehouseFilter`、`reconcileStatusFilter`、`mainSearchKeyword`、`mainCurrentPage`、`mainPageSize`；
   - 实现 `filteredMainDispatchList` 与 `paginatedMainDispatchList` 计算属性；
   - 表格 `:data` 绑定到 `paginatedMainDispatchList`；
   - 在表格下方追加 `.pagination-footer` 容器与 `el-pagination` 分页组件。

3. **[frontend/] 升级财务模块 Tab 2（科室领用与消耗支出对账）**：
   - 修改 `frontend/src/views/FinancePrintView.vue`；
   - 增加耗占比合规等级筛选下拉框与科室名称搜索框；
   - 声明 `deptRiskFilter`、`deptSearchKeyword`、`deptCurrentPage`、`deptPageSize`；
   - 实现 `filteredDeptCostList` 与 `paginatedDeptCostList` 计算属性；
   - 表格 `:data` 绑定到 `paginatedDeptCostList` 并追加 `el-pagination` 分页组件。

4. **[frontend/] 升级财务模块 Tab 3（全院进销存月度平衡表）**：
   - 修改 `frontend/src/views/FinancePrintView.vue`；
   - 增加仓库层级分类下拉框、平衡状态下拉框与仓库搜索框；
   - 声明 `balanceWarehouseFilter`、`balanceStatusFilter`、`balanceSearchKeyword`、`balanceCurrentPage`、`balancePageSize`；
   - 实现 `filteredBalanceList` 与 `paginatedBalanceList` 计算属性；
   - 表格 `:data` 绑定到 `paginatedBalanceList` 并追加 `el-pagination` 分页组件。

5. **[frontend/] 统一操作栏与重置筛选交互**：
   - 为 Tab 1、Tab 2、Tab 3 增加“重置筛选”便捷操作，一键清空关键字与下拉选项；
   - 优化 `.pane-action-bar` 的 Flex 换行与响应式自适应布局。

6. **[frontend/] 前端代码质量与打包编译验证**：
   - 运行 `npm run build`（`vue-tsc && vite build`），确保 0 TypeScript 类型错误，0 构建警告。

7. **[tests/] Playwright 自动化回环测试与实机截图**：
   - 执行 Playwright 测试脚本导航至 `http://127.0.0.1:5173/finance`；
   - 验证 Tab 1、Tab 2、Tab 3 的分类筛选、关键词搜索与翻页交互；
   - 点击唤起右下角浮动智能体窗口，验证头部双层布局与无折行效果；
   - 捕获高清实机截图归档至 `tests/screenshots/`。
