# [2026-11-03 22:56:30] 医疗物资全链路单据视觉体系规范化与财务动态打印引擎实施计划

## 1. 计划归档与变更范围
[变更计划]
- 计划文档路径：plans/2026-11-03_22-56-30_STANDARDIZE_VOUCHER_FORMS_AND_DYNAMIC_PRINT_ENGINE_PLAN.md
- 记录时间戳：2026-11-03 22:56:30
- 前端目标文件：
  - `frontend/src/views/GeneralMaterialView.vue` (修复采购入库输入框超出，将分发出库单重构为现代单据样式并保留 FEFO 熔断)
  - `frontend/src/components/PrintVoucherDialog.vue` (重构明细为动态数组循环，内置标准汉字大写金额转换引擎)
  - `frontend/src/views/FinancePrintView.vue` (重构 5 大法定单据为真实丰富耗材数据，表格行打印真实穿透)
- 后端目标文件：无（纯前端视图、单据规范与打印载体数据流重构，后端 API 完全满足需求）
- 测试与截图文件：
  - `tests/e2e/test_voucher_standard_and_print_engine.js` (自动化回环验证脚本)
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_01_inbound_voucher_input_fit_verified.png`
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_02_outbound_voucher_unified_style_verified.png`
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_03_outbound_fefo_fuse_retained_verified.png`
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_04_finance_print_dynamic_multi_items_verified.png`
  - `tests/screenshots/[YYYY-MM-DD_HH-MM-SS]_05_finance_table_row_penetrate_print_verified.png`

---

## 2. 核心评估指标
- **可行性与把握度评估**：把握度 98%。各项单据组件层级与数据流清晰，金额大写算法与 CSS 响应式网格技术成熟，无底层架构阻塞。
- **存量功能与三方体验影响分析**：
  - **UX（用户体验）**：消除输入框超出弹窗边界的截断问题；出库业务与入库业务界面视觉规范达到 100% 统一；财务单据打印由虚假单行数据升级为真实业务丰富多行与动态大写，审计质感大幅跃升。
  - **DX（开发维护成本）**：单据设计系统统一，消除陈旧的仿纸质私有类名，降低样式维护负担。
  - **AX（Agent 协作体验）**：规范的 DOM 结构与标准的打印数据契约让后续 Agent 回环测试与数据解析极其稳健。
  - **存量保护底线**：出库单的 FEFO 30 天临期硬熔断拦截、草稿箱暂存机制、单据保存后自动审核下发等存量逻辑 100% 继承，零破坏。
- **Playwright 自动化回环测试方案**：
  编写端到端自动化测试脚本，顺序覆盖：
  1. 验证《采购入库单》弹窗右侧第 4 列输入框不发生截断且无水平溢出；
  2. 验证《主库按需分发出库单》已成功升级为现代卡片式单据样式（统一标签与控件）；
  3. 验证出库单在输入临期物资时依然能够坚固触发三甲 FEFO 30 天临期硬阻断；
  4. 验证财务模块点击《主库采购验收入库单》与《高值耗材一物一码核销单》呈现多行真实耗材与动态金额大写；
  5. 验证财务对账表格行点击“打印凭证”，打印单据与当前行的实际科室、调拨总额精确对齐；
  6. 全程拦截控制台报错，确保 Console Error 与 PageError 为 0，实机截图归档。

---

## 3. 技术与 UI 细节规范

### 3.1 采购入库单右侧输入框尺寸修复 (`GeneralMaterialView.vue`)
- 将 `.purchase-header-grid` 设置为：
  ```css
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px 14px;
  box-sizing: border-box;
  width: 100%;
  ```
- 为 `.form-item-inline` 和 `.spd-input, .spd-select` 声明 `min-width: 0; box-sizing: border-box; width: 100%;`；
- 将 `label` 标签宽度优化为 `width: 66px; flex-shrink: 0; text-align: right;`，彻底杜绝第 4 列超出。

### 3.2 主库按需分发出库单现代样式重构 (`GeneralMaterialView.vue`)
- 淘汰旧纸质私有类（`.bill-paper-container`、`.bill-form-meta-grid`、`.meta-row`、`.meta-col`、`.bill-inline-input`、`.bill-native-table`）；
- 统一使用 `.hospital-bill-container`，单头使用现代 4 列卡片网格；
- 输入框统一采用 `.spd-input` 与 `.spd-select`；
- 明细表格采用 `.bill-detail-table.edit-table`，保留字典选品、删除行、明细合计行；
- 保留 FEFO 30 天临期硬阻断拦截校验与自动下发逻辑。

### 3.3 打印载体组件重构 (`PrintVoucherDialog.vue`)
- 新增中文金额大写转换算法函数：
  ```typescript
  /**
   * 将阿拉伯数字金额转换为标准中国人民银行财务法定大写金额
   * @param {number} n 金额数值
   * @returns {string} 中文大写金额（如：人民币壹万柒仟伍佰叁拾元零捌分）
   * @route internal://PrintVoucherDialog/digitUppercase
   * @throws 无异常，非法输入自动兜底
   */
  export function digitUppercase(n: number): string
  ```
- 明细表格支持接收 `orderData.items` 数组，使用 `v-for="(item, idx) in displayItems"` 动态渲染：
  - 序号、物资编码、品名规格、生产批号、单位、数量、单价、金额；
- 底部动态计算合计数量与小写金额，并通过 `digitUppercase` 转换为中文大写。

### 3.4 财务模块打印数据真实化与表格穿透 (`FinancePrintView.vue`)
- 定义 5 类法定单据的真实结构化业务明细数据集：
  - 采购入库单：威高集团供货批次、发票号、一次性注射器/留置针等；
  - 主库分发调拨单：卫材主库调拨骨科病区纱布块/高分子夹板等；
  - 高值核销单：冠状动脉支架/球囊导管、UDI 码、患者脱敏住院号（张*华 / ZY202611***）；
  - 二级库申领单：临床病区定数申领包；
  - 月度财务结算单：各科室普通与高值耗材汇总支出；
- 表格行“打印凭证”点击事件重构：
  ```typescript
  /**
   * 打开表格行关联的真实对账打印凭证
   * @param {Record<string, any>} row 当前对账表格行数据
   * @returns {void}
   * @route internal://FinancePrintView/openRowPrint
   * @throws 无异常抛出
   */
  function openRowPrint(row: Record<string, any>): void
  ```
  直接将当前行的 `main_warehouse_name`、`target_dept_name`、`total_amount`、`total_qty` 动态组装为真实单据注入打印预览弹窗。

---

## 4. 实施清单

1. [frontend/ 修复 GeneralMaterialView.vue 中采购入库单 grid 网格与 input 尺寸防溢出]
2. [frontend/ 重构 GeneralMaterialView.vue 中按需分发出库单为统一现代单据样式并保留 FEFO 熔断]
3. [frontend/ 升级 PrintVoucherDialog.vue：内置动态金额大写算法、多行耗材循环与合计]
4. [frontend/ 升级 FinancePrintView.vue：装配 5 类真实业务耗材明细与表格行穿透打印数据流]
5. [frontend/ 执行 npm run build 校验打包产物与类型合规性]
6. [tests/ 编写端到端自动化回环测试脚本 tests/e2e/test_voucher_standard_and_print_engine.js]
7. [tests/ 运行自动化回环测试，校验 0 Console Error / 0 PageError，并捕获归档实机全景截图]
8. [plans/ 更新计划文档执行台账并向用户呈现完整验收汇报]

---

## 5. 执行记录与回环验证台账
- **执行时间戳**：2026-11-03 23:07:04
- **执行状态**：全部清单项实施完成并通过 Playwright 自动化回环验证
- **前端修改文件**：
  - `frontend/src/views/GeneralMaterialView.vue` (采购入库单网格防溢出修复；主库分发出库单升级为统一现代单据样式并保留 FEFO 熔断)
  - `frontend/src/components/PrintVoucherDialog.vue` (明细多行动态数组循环化；内置人民银行标准中文金额大写转换算法；支持数量与金额动态合计)
  - `frontend/src/views/FinancePrintView.vue` (装配 5 类真实医疗耗材明细数据；表格行“打印凭证”穿透真实主库、科室与对账金额)
- **编译打包**：
  - `vue-tsc && vite build` 编译完成，耗时 10.03s，0 错误。
- **Playwright 自动化回环测试**：
  - 脚本：`tests/e2e/test_voucher_standard_and_print_engine.js`
  - 结果：通过 (5/5)，Console Error = 0，PageError = 0。
  - 实机截图归档：
    1. `tests/screenshots/2026-11-03_23-06-45_01_inbound_voucher_input_fit_verified.png`
    2. `tests/screenshots/2026-11-03_23-06-45_02_outbound_voucher_unified_style_verified.png`
    3. `tests/screenshots/2026-11-03_23-06-45_03_outbound_fefo_fuse_retained_verified.png`
    4. `tests/screenshots/2026-11-03_23-06-45_04_finance_print_dynamic_multi_items_verified.png`
    5. `tests/screenshots/2026-11-03_23-06-45_05_finance_table_row_penetrate_print_verified.png`
