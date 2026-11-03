# Harness 熵管理：历史计划文档降权归档区 (Archive)

## 1. 归档区定位（Harness 组件⑥：熵管理）
本目录用于存放**已完成全部历史使命、已被最新总体计划书合并覆盖、或不再具备当前直接执行价值**的历史计划文档。
通过将陈旧文档移入 `plans/archive/`，可显著降低活跃工作区（`plans/` 根目录）的信息熵，防止 AI Agent 在跨会话恢复上下文时被过期的过渡方案干扰，确保上下文高信噪比。

## 2. 降权与归档触发准则
1. **阶段已结项**：文档内的原子实施清单已 100% 执行完毕且验证通过；
2. **基线已合并**：早期探索阶段的零散计划已被最新的总体基线计划书完整吸收；
3. **需求已迭代**：因业务规则升级，早期草案中的局部设想已被新规范取代。

## 3. 已归档历史文档台账

| 归档文档文件名 | 原始创建时间 | 归档原因说明 | 当前状态 |
| :--- | :--- | :--- | :--- |
| `2026-10-29_18-52-01_install_skills_mcp_and_init_project.md` | 2026-10-29 18:52:01 | 全局 PM 技能 (`edu-pm-workflow`) 与 `xerj` MCP 已部署完毕，阶段使命完结 | `[ARCHIVED]` |
| `2026-10-29_20-05-51_spd_architecture_and_drawio.md` | 2026-10-29 20:05:51 | 持久化浏览器配置 (`browser_config.js`) 已跑通，早期架构已升级并合入最新总体计划书 | `[ARCHIVED]` |
| `2026-11-02_09-52-00_harness_lifecycle_spec_and_entropy_management.md` | 2026-11-02 09:52:00 | 过渡期规范草案，已完整融入《项目总体计划书 (`2026-11-02_10-41-00`)》 | `[ARCHIVED]` |
| `2026-11-03_09-56-00_product_dict_and_warehouse_rbac_refactor.md` | 2026-11-03 09:56:00 | 字典与仓库树初期重构已完成验证并并入后续计划 | `[ARCHIVED]` |
| `2026-11-03_11-25-00_hospital_spd_full_business_and_sidebar_refactor.md` | 2026-11-03 11:25:00 | 侧边栏与全业务框架重构已完成并并入后续计划 | `[ARCHIVED]` |
| `2026-11-03_14-06-00_independent_subviews_and_backend_reload_fix.md` | 2026-11-03 14:06:00 | 独立子视图解耦与热重载排查已完成验证 | `[ARCHIVED]` |
| `2026-11-03_15-05-00_fix_inbound_stocktake_and_complete_highvalue_secondary_spd.md` | 2026-11-03 15:05:00 | 入库单与高值/二级库初期对齐已完成 | `[ARCHIVED]` |
| `2026-11-03_15-30-00_spd_full_business_and_audit_rbac_master_plan.md` | 2026-11-03 15:30:00 | 上一阶段全业务与审计权限总体计划已完成，现由 17:20:02 最新对齐计划全面接管 | `[ARCHIVED]` |
