## 2026-11-02T13:39:14Z
You are worker_m4, working as High-Glassmorphism Business Views & RBAC Layout Worker.
Your working directory is: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\worker_m4
You MUST read ORIGINAL_REQUEST.md first at: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\ORIGINAL_REQUEST.md
Also read PROJECT.md at: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\orchestrator\PROJECT.md
Also read DISPATCH.md at: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\orchestrator\DISPATCH.md
Read the authoritative prototypes:
- docs/design/spd_integrated_showcase_demo.html
- docs/design/spd_frontend_design_variants.html (lines 100-800 for Fusion workbench layout and business cards)
- docs/design/spd_interactive_prototype.html

Mission:
Implement Milestone M4: 全域业务视图 Demo 风格高质感自然延展与 RBAC 动态过滤.

File Ownership:
- frontend/src/layouts/MainLayout.vue
- frontend/src/views/ProductDictView.vue
- frontend/src/views/GeneralMaterialView.vue
- frontend/src/views/HighValueView.vue
- frontend/src/views/SecondaryWarehouseView.vue
- frontend/src/views/WorkflowLogView.vue
- frontend/src/views/FinancePrintView.vue
- frontend/src/views/SupplierPurchaseView.vue

Detailed Requirements:
1. frontend/src/layouts/MainLayout.vue:
   - Discard the traditional grey ERP box model. Refactor into the modern glassmorphism shell matching docs/design/spd_frontend_design_variants.html (Fusion modern workbench).
   - Glassmorphism backdrop-filter: blur(20px), --bg-card, --border-card, subtle elevation shadows.
   - Dynamic sidebar navigation strictly filtered by RBAC can_view:
     * sys_admin (admin): Sees all 7 menus.
     * secondary_user (nurse): ONLY sees SecondaryWarehouse (二级库管理) and HighValue (高值耗材管理/扫码核销). ProductDict, GeneralMaterial, Logs, Finance, Supplier are HIDDEN!
     * finance_auditor (finance): ONLY sees FinancePrint (统计查询与单据打印中心) and WorkflowLog (全流程业务链路日志 6W). Physical warehouse operations are HIDDEN!
     * supplier_user (supplier): ONLY sees SupplierPurchase (采购与供应商协同).
     * dept_manager (consumable/equip): Sees respective main warehouse and product dict.
   - Header: Brand logo SvgIcon, role switcher dropdown, fine-grained RBAC drawer button, 3D Showcase portal jump button, theme toggle, user badge.
   - RBAC Drawer for sys_admin: Allows toggling permissions across 15 modules x 8 actions with instant reactive effect.
2. All 7 Business Views in frontend/src/views/:
   - Completely refactor styles and templates to be the natural extension of docs/design/spd_integrated_showcase_demo.html and spd_frontend_design_variants.html:
     * ProductDictView.vue: 4-stat KPI grid, glassmorphic dual-tree panel (warehouse tree + category tree), table with hover row illumination, action drawers. Button-level v-if="userStore.canAction('PRODUCT_DICT', 'add/edit/delete')".
     * GeneralMaterialView.vue: 4-stat KPI grid, glassmorphic tabs, FEFO near-expiry sorting, on-demand dispatch modal with two-step confirmation lock. Button-level canAction checks.
     * HighValueView.vue: 4-stat KPI grid, UDI single item smart cabinet, scan-and-verify modal, patient masked binding (张*丰, 住院号 ZY...), canAction checks.
     * SecondaryWarehouseView.vue: 4-stat KPI grid, department switcher pills (骨科 / 心内科), safe stock level warnings, on-demand replenishment apply modal, canAction checks.
     * WorkflowLogView.vue: 8-node timeline graph, 6W elements table (Who, What, Where, When, Why, Which), 100% audit penetration.
     * FinancePrintView.vue: Department cost stats, cost ratio breakdown, 5 legal hospital 4-copy voucher printing modals with @media print clean formatting (制单人, 主库主管, 领用人, 财务复核 4 signatures).
     * SupplierPurchaseView.vue: Qualification audit banner, procurement order flow stages, dispatch & verify modals.
   - Every action button ("新增", "修改", "删除", "审核", "二次确认", "打印") MUST bind to userStore.canAction(moduleCode, actionKey).
   - All numbers use tabular-nums font-mono anti-jitter styling.
   - Strictly 0 Emoji! All icons use SvgIcon or Element Plus vector icons.
3. Build Verification:
   - Run `npm --prefix frontend run build` to confirm 0 errors, 0 warnings.
   - Check that 0 Emoji exist across all modified files.
   - All functions 100% covered with standardized Chinese comments (@param, @returns, @route, @throws).
