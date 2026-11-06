# 研发实施计划：供应商资质提报弹窗补齐、医院端合规审核与必填驳回理由全链路闭环

- 计划文档路径：`plans/2026-11-06_17-05-00_supplier_qualification_audit_plan.md`
- 记录时间戳：`2026-11-06 17:05:00`
- 关联问题与诉求：
  1. 解决供应商门户中【重新上传资质证照】按钮点击无弹窗响应的假死缺陷；
  2. 落地“方式 A（强引导模式）”，为新建或待审供应商账号提供《医疗器械经营企业资质提报单》弹窗，支持录入企业全称、统一信用代码、许可证号、有效截止日、业务联系人、联系电话及模拟附件上传；
  3. 明确并串联医院端审核入口（【采购管理与准入】->【供应商资质审查】/procurement?tab=suppliers）；
  4. 建立合规驳回闭环：医院端驳回时强制要求填写驳回理由（字数校验），后端持久化保存理由，供应商端在硬拦截警告框中清晰展示驳回意见以供整改。

---

## 1. 变更范围与目标文件

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-06_17-05-00_supplier_qualification_audit_plan.md
- 记录时间戳：[2026-11-06 17:05:00]
- 后端目标文件：
  - backend/app/models/spd_extended_models.py：为 SpdSupplierProfile 增加 audit_remark 字段（持久化保存审核意见与驳回理由）；
  - backend/app/schemas/spd_extended_schemas.py：为 SupplierQualAuditRequest 新增 audit_remark、social_credit_code、contact_person、contact_phone 等字段；
  - backend/app/routers/extended_spd_router.py：完善 post_supplier_qualification_audit 与 list_supplier_qualifications，持久化存储审核/驳回理由并全链路回传。
- 前端目标文件：
  - frontend/src/api/supplierPurchaseApi.ts：更新资质提报与审核接口契约，透传 audit_remark 等字段；
  - frontend/src/views/ExternalSupplierPortalView.vue：补齐资质上传/重新提报弹窗组件，未通过时在告警框中高亮展示院方驳回理由；
  - frontend/src/views/HospitalProcurementView.vue：在 Tab 2 供应商资质审查中，对合规驳回增加非空必填校验，并在列表中清晰展示审核意见。
- 测试与截图文件：
  - tests/e2e/test_supplier_qualification_flow_e2e.js：Playwright E2E 自动化测试脚本；
  - tests/screenshots/2026-11-06_17-05-00_supplier_portal_upload_modal.png：供应商端资质申报弹窗实机截图；
  - tests/screenshots/2026-11-06_17-05-00_hospital_audit_reject_with_reason.png：医院端填写驳回理由弹窗实机截图；
  - tests/screenshots/2026-11-06_17-05-00_supplier_portal_rejected_alert.png：供应商端查看驳回理由警示框实机截图；
  - tests/screenshots/2026-11-06_17-05-00_hospital_audit_approve_unlocked.png：医院端最终通过准入并解锁实机截图。
```

---

## 2. 核心评估指标

- **可行性与把握度评估**：`把握度：98%`。前后端业务链路清晰，涉及的前端弹窗补齐与后端字段持久化均为高内聚、低耦合的标准增量改动，不存在阻塞性技术难题。
- **存量功能与三方体验影响分析**：
  - **用户体验 (UX)**：彻底解决点击按钮无响应的体验缺陷；供应商提报资质有全套规范表单指引；被驳回时有清晰的理由反馈，知道如何整改；医院端审核时杜绝无理由随意驳回；
  - **开发者体验 (DX)**：后端接口参数与数据库字段语义统一，函数具备 100% 中文四要素注释；
  - **AI 代理体验 (AX)**：状态流转通过清晰的枚举（`QUAL_PENDING` / `QUAL_APPROVED` / `QUAL_REJECTED`）驱动，便于 E2E 自动化精准断言；
  - **存量零破坏底线**：100% 保持既有已准入供应商（如威高集团）的订单流转、拣货发货与四联单据打印功能完好。
- **Playwright 自动化回环测试与截图验证方案**：
  1. 切换至外部供应商代表账号（工号 `cyx01`），点击【重新上传资质证照】打开弹窗，输入完整资质信息并提交，捕获截图 `2026-11-06_17-05-00_supplier_portal_upload_modal.png`；
  2. 切换至耗材科科室主管（工号 `mgr_consumable`），进入【采购管理与准入】->【供应商资质审查】；
  3. 点击待审企业的【合规驳回】，先不填理由验证拦截；再输入详细理由“营业执照副本未加盖鲜章且复印件模糊，请重新上传清晰扫描件”并提交，捕获截图 `2026-11-06_17-05-00_hospital_audit_reject_with_reason.png`；
  4. 切换回供应商代表账号，验证硬拦截告警框中明确呈现院方驳回理由，捕获截图 `2026-11-06_17-05-00_supplier_portal_rejected_alert.png`；
  5. 再次切换至主管账号，点击【审查通过准入】，验证准入通过且接单发货按钮解锁，捕获截图 `2026-11-06_17-05-00_hospital_audit_approve_unlocked.png`。

---

## 3. 技术与 UI 细节规范

### 3.1 供应商资质申报弹窗组件设计 (`ExternalSupplierPortalView.vue`)
- **弹窗标题**：`外部供应商医疗器械经营资质准入申报`
- **表单元素**：
  - 企业全称：`el-input`，必填
  - 统一社会信用代码：`el-input`（18位大写与数字校验）
  - 《医疗器械经营许可证》编号：`el-input`，必填
  - 药监局经营许可有效截止日：`el-date-picker`，必填
  - 法定业务联系人：`el-input`，带入当前登录真实姓名
  - 业务联系手机：`el-input`
  - 证照电子扫描件：内联 SVG 矢量图标 + 模拟上传状态卡片
- **提交逻辑**：调用 `auditSupplierQualification`，传递状态 `QUAL_PENDING`，提交后刷新资质列表，告警卡片切换为待审状态。

### 3.2 驳回理由强制校验与展示体系
1. **医院端审查弹窗 (`HospitalProcurementView.vue`)**：
   - 当 `targetAuditAction === 'QUAL_REJECTED'` 时，审核结论输入框标签显示为“驳回原因与整改要求 (必填)”，未输入或字数小于 2 时弹窗拦截并不予提交；
   - 当 `targetAuditAction === 'QUAL_APPROVED'` 时，标签显示为“准入合规审查结论 (可选)”。
2. **供应商端警示卡片展示**：
   - 当状态为 `QUAL_REJECTED` 时，警告面板新增醒目区域展示：
     `【医院耗材科审核驳回原因】: {{ activeSupplier.audit_remark }}`，并引导点击重新提报。

### 3.3 数据持久化与接口契约
- **后端模型**：`SpdSupplierProfile` 补充 `audit_remark = Column(Text, nullable=True, comment="审核结论或驳回原因说明")`；
- **接口扩展**：`POST /api/v1/ext/supplier-purchase/qual-audit` 同步更新 `SpdSupplierProfile.audit_remark` 与 `SpdSupplierAndPurchaseOrder`；
- **全域严禁 Emoji 铁律**：所有图标均使用系统 `SvgIcon`（如 `shield`、`upload`、`alert`、`check`）或 Element Plus 原生图标。

---

## 4. 原子实施清单 (已全部交付完成)

```markdown
实施清单：
1. [x] [backend/] 在 backend/app/models/spd_extended_models.py 中为 SpdSupplierProfile 增加 audit_remark 字段支持。(完成于 2026-11-06 17:03:00)
2. [x] [backend/] 在 backend/app/schemas/spd_extended_schemas.py 中扩展 SupplierQualAuditRequest，增加 audit_remark、social_credit_code、contact_person、contact_phone 字段。(完成于 2026-11-06 17:03:30)
3. [x] [backend/] 在 backend/app/routers/extended_spd_router.py 中改造 post_supplier_qualification_audit 与 list_supplier_qualifications，持久化保存并回传审核意见与驳回理由。(完成于 2026-11-06 17:04:00)
4. [x] [frontend/] 在 frontend/src/api/supplierPurchaseApi.ts 中更新 auditSupplierQualification 接口出入参契约。(完成于 2026-11-06 17:04:20)
5. [x] [frontend/] 在 frontend/src/views/ExternalSupplierPortalView.vue 中补齐完整资质申报弹窗组件，并在被驳回状态下醒目呈现院方驳回理由。(完成于 2026-11-06 17:06:50)
6. [x] [frontend/] 在 frontend/src/views/HospitalProcurementView.vue 中对合规驳回增加理由非空必填校验，并在审查台账中呈现审核说明。(完成于 2026-11-06 17:08:00)
7. [x] [frontend/] 执行 cd frontend; npm run build 全量 TypeScript 编译，验证 0 警告 0 报错。(完成于 2026-11-06 17:08:35)
8. [x] [backend/] 平替重启后端服务确保新增字段与路由逻辑生效。(完成于 2026-11-06 17:10:20)
9. [x] [tests/] 编写并运行 tests/e2e/test_supplier_qualification_flow_e2e.js，执行 Playwright 全流程闭环测试并捕获实机截图归档至 tests/screenshots/ 与 artifacts/。(完成于 2026-11-06 17:16:50)
```
