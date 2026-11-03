# [MODE: PLAN] 技术规范与原子级实施计划

- **计划文档路径**：`plans/2026-11-03_09-56-00_product_dict_and_warehouse_rbac_refactor.md`
- **记录时间戳**：2026-11-03 09:56:00
- **当前模式**：`[MODE: PLAN]`

---

## 1. 变更计划与目标文件范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-03_09-56-00_product_dict_and_warehouse_rbac_refactor.md
- 记录时间戳：2026-11-03 09:56:00
- 前端目标文件：
  - frontend/src/layouts/MainLayout.vue (侧边栏移除所有 1. 2. 3. 序号，规范深浅色主题文字 Token)
  - frontend/src/styles/theme.css (补齐并锁定暗色高对比度与浅色石板灰字体阶梯)
  - frontend/src/views/ShowcaseView.vue (主舞台包裹器平滑左移让位 translateX(-220px)，取消暗黑全屏遮罩)
  - frontend/src/components/auth/HealthcareAuthModal.vue (重塑为右侧悬浮通透毛玻璃卡片，支持呼吸边距与关闭联动)
  - frontend/src/views/ProductDictView.vue (1:1 重构为图 4 标准四栏三树 SPD 结构，实现品名/供应商双 Tab、新增品名弹窗图 3、新增规格弹窗图 5、批量调价与权限过滤)
  - frontend/src/api/dictApi.ts (扩展品名、规格、供应商、仓库权限与批量调价请求接口)
- 后端目标文件：
  - backend/app/models/spd_models.py (补充大品名与型号规格级联关系、用户仓库细粒度授权表)
  - backend/app/models/spd_extended_models.py (补充独立供应商档案表与调价历史快照表)
  - backend/app/routers/dict_router.py (提供大品名 CRUD、规格型号 CRUD、供应商 CRUD、仓库与权限绑定、批量调价接口)
- 测试与截图文件：
  - tests/e2e/test_product_dict_and_rbac_flow.js (Playwright 端到端全景与业务回归脚本)
  - tests/screenshots/2026-11-03_09-56-00_01_showcase_shift_left_login.png
  - tests/screenshots/2026-11-03_09-56-00_02_workbench_sidebar_no_numbers.png
  - tests/screenshots/2026-11-03_09-56-00_03_product_dict_three_tree_workspace.png
  - tests/screenshots/2026-11-03_09-56-00_04_product_dict_batch_price_adjust.png
```

---

## 2. 核心评估指标

1. **可行性与把握度评估**：
   - **把握度：98%**；
   - **潜在技术风险与规避方案**：
     - *品名与规格的父子数据一致性*：大品名被删除或停用时，必须级联校验其下属规格是否有在库库存，有库存则刚性拦截删除，仅允许“停用”；
     - *仓库动作权限过滤效率*：通过在前端 Store 中缓存当前用户的 `warehousePermissions: Record<warehouseCode, Actions>`，并在页面渲染时通过统一辅助函数 `canWarehouseAction(whCode, action)` 秒级计算，无权按钮直接不渲染；
     - *批量调价并发与锁表*：批量调价在后端单事务中原子提交，并同步写入调价历史表，避免长事务锁表。
2. **存量功能与三方体验影响分析**：
   - **用户体验（UX）**：侧边栏彻底告别生硬序号，深色与浅色文字清晰易读；展厅唤起登录时整体平滑左移，右侧悬浮卡片自然展开，无暗黑遮罩阻挡壁纸；产品字典还原真实医院 SPD 三树四栏高效操作体验；
   - **开发者体验（DX）**：前后端模型清晰划分“大品名”与“规格单品”，接口统一返回 `{code, msg, data}`，所有新增函数 100% 覆盖标准化中文四要素注释；
   - **AI 协作体验（AX）**：结构化的仓库权限矩阵与高内聚的字典数据契约，杜绝 AI 跨轮次理解幻觉。
3. **Playwright 自动化回环测试与截图验证方案**：
   - 自测用例 1：访问 `/showcase?login=1`，断言主舞台元素携带左移样式（`translateX`），断言右侧登录卡片可见且无全屏黑雾遮罩，截图归档；
   - 自测用例 2：以管理员登录进入工作台，断言侧边栏无任何“1.”、“2.”等数字，断言深浅主题切换下文字对比度达标，截图归档；
   - 自测用例 3：进入产品字典，断言左侧仓库树、分类树、中栏品名/供应商双 Tab、右栏规格明细表全部正常渲染，截图归档；
   - 自测用例 4：勾选多个规格触发【集中带量调价管理】，断言批量调价向导正常弹出并可成功提交，截图归档。

---

## 3. 技术与 UI 细节规范

### 3.1 数据库 ORM 模型设计 (`backend/app/models/`)
1. **产品大品名表 (`spd_product_spn`)**：
   - `id`: BigInteger 主键
   - `spn_code`: String(32), 唯一品名代码 (如 `936010100024`)
   - `spn_name`: String(128), 品名名称 (如 `医用氧气123`)
   - `category_code`: String(32), 关联耗材分类 (如 `0101`)
   - `common_name`: String(128), 通用名
   - `pinyin_code`: String(64), 拼音码
   - `is_chargeable`: SmallInteger, 是否收费 (1/0)
   - `is_high_value`: SmallInteger, 是否高值 (1/0)
   - `is_central_proc`: SmallInteger, 是否集采 (1/0)
   - `contract_no`: String(64), 合同编号
2. **产品规格型号表 (`spd_product_spec`)**：
   - `id`: BigInteger 主键
   - `spn_id`: BigInteger, 关联大品名 ID
   - `spec_code`: String(64), 唯一产品规格编码 (如 `936010100024055517`)
   - `spec_name`: String(128), 规格名称 (如 `40L 钢瓶装`)
   - `model_name`: String(128), 型号 (如 `TWLB`)
   - `manufacturer`: String(128), 生产厂商
   - `unit_price`: Decimal(12, 4), 基准单价
   - `pricing_unit`: String(32), 计价单位 (瓶/支/盒)
   - `package_unit`: String(32), 包装单位 (箱)
   - `conversion_ratio`: Decimal(10, 2), 大小包装转换比 (如 50)
   - `register_card_no`: String(128), 医疗器械注册证号
   - `register_expiry_date`: Date, 注册证有效期
   - `storage_condition`: String(64), 储存条件
   - `default_supplier_id`: BigInteger, 默认供应商 ID
   - `status`: String(32), 状态 (ACTIVE / DISABLED)
3. **用户-仓库细粒度权限表 (`sys_user_warehouse_perm`)**：
   - `user_id`: BigInteger
   - `warehouse_code`: String(32)
   - `can_view`: SmallInteger (查看物资)
   - `can_apply`: SmallInteger (科室申领)
   - `can_inbound`: SmallInteger (验收入库)
   - `can_outbound`: SmallInteger (发料出库)
   - `can_stocktake`: SmallInteger (盘点维护)
   - `can_transfer`: SmallInteger (跨仓调拨)
4. **调价历史记录表 (`spd_price_adjust_log`)**：
   - `spec_id`: BigInteger, 关联规格
   - `old_price`: Decimal(12, 4), 原单价
   - `new_price`: Decimal(12, 4), 调整后单价
   - `adjust_reason`: String(128), 调价原因
   - `adjust_doc_no`: String(128), 调价文件依据文号
   - `operator_id`: BigInteger, 操作人员
   - `effective_time`: DateTime, 生效时间

### 3.2 批量调价 API 接口契约 (`backend/app/routers/dict_router.py`)
- `@route POST /api/dict/batch-adjust-price`
- `@param {BatchAdjustPriceRequest} payload` (包含 `spec_ids: int[]`, `adjust_type: 'FIXED_PRICE' | 'PERCENT_DISCOUNT' | 'FIXED_OFFSET'`, `adjust_value: float`, `reason: string`, `doc_no: string`)
- `@returns {ApiResponse<{ affected_count: number, logs: PriceAdjustLogItem[] }>}`
- `@throws 400 参数非法, 403 权限不足, 500 事务异常`

---

## 4. 原子实施清单

```markdown
实施清单：
1. [x] [后端 backend/] 更新 `spd_models.py` 与 `spd_extended_models.py`，新增/完善大品名表、规格型号表、用户仓库细粒度权限表、独立供应商表与调价历史表，并初始化真实模拟种子数据。
2. [x] [后端 backend/] 更新 `dict_router.py`，实现大品名 CRUD、规格型号 CRUD、批量调价、供应商管理与用户仓库细粒度权限查询与配置接口。
3. [x] [前端 frontend/] 修改 `src/styles/theme.css`，加固深色高对比度与浅色高对比度文字色阶 Tokens，严禁任何颜色硬编码。
4. [x] [前端 frontend/] 修改 `src/layouts/MainLayout.vue`，彻底消除侧边栏所有“1. 2. 3.”数字序号，恢复为纯语义化标签与微型徽标。
5. [x] [前端 frontend/] 修改 `src/views/ShowcaseView.vue` 与 `HealthcareAuthModal.vue`，实现展厅主舞台在唤起登录时 GPU 加速自适应左平移让位（`translateX(-240px)`），右侧渲染通透悬浮毛玻璃登录卡片，移除全屏黑雾遮罩。
6. [x] [前端 frontend/] 重构 `src/views/ProductDictView.vue`，对齐图 4 还原四栏三树专业工作台：
   - 左栏：仓库树（绑定数据隔离）与分类树；
   - 中栏：产品大品名与供应商双 Tab 切换；
   - 右栏：规格型号明细表格（代码、规格、型号、厂商、价格、注册证、供应商）；
   - 工具栏与弹窗：新增/编辑品名对话框（图 3）、新增/编辑规格对话框（图 5）、集中带量批量调价对话框与按钮级 RBAC 过滤。
7. [x] [测试 tests/] 编写并执行自动化测试脚本 `tests/e2e/test_product_dict_and_rbac_flow.js`，运行 Playwright 验证侧边栏无数字、展厅左移让位、产品字典三树联动及批量调价交互。
8. [x] [验证 tests/] 捕获带时间戳实机截图归档至 `tests/screenshots/` 并向用户提交汇报。
```

---

## 5. 执行完成记录与实机证据归档

- **执行完成时间戳**：2026-11-03 10:28:00
- **当前执行状态**：全部 8 项原子任务 100% 执行完毕并通过 Playwright 端到端无头浏览器回环自测
- **交付实机截图清单**：
  1. `tests/screenshots/2026-11-03_10-26-30_01_showcase_shift_left_login.png`：展厅主舞台 GPU 硬件加速平滑左移 240px，右侧悬浮通透登录卡片，无暗黑全屏遮罩；
  2. `tests/screenshots/2026-11-03_10-26-30_02_workbench_sidebar_no_numbers.png`：进入三级角色工作台，侧边栏彻底去除“1. 2. 3.”数字序号，恢复为纯语义化菜单与微型徽标；
  3. `tests/screenshots/2026-11-03_10-26-30_03_product_dict_three_tree_workspace.png`：产品字典四栏三树专业工作台，完整呈现仓库树、分类树、品名树与规格型号明细表；
  4. `tests/screenshots/2026-11-03_10-26-30_04_product_dict_batch_price_adjust.png`：集中带量采购批量调价向导模态框，勾选物料后即时预览调价后新单价并录入调价依据；
  5. `tests/screenshots/2026-11-03_10-26-30_05_nurse_warehouse_rbac_isolated.png`：临床护士角色行级仓库隔离生效，左侧仓库树仅展示授权科室仓，增改删操作按钮级权限阻断隐藏；
  6. `tests/screenshots/2026-11-03_10-26-30_06_product_dict_dark_mode_high_contrast.png`：深色暗空模式全局对比度加固，Element Plus 表格文字与边框完全适配，达到医疗软件级清晰视觉标准。
