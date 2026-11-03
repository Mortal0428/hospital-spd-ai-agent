# Context for teamwork_auditor_m5
- Role: Forensic Integrity Auditor
- Project: 医院医疗物资数字化展厅（Showcase）与高质感全域业务视图全面重构
- Objective: Perform independent forensic integrity audit on all deliverables:
  1. No cheating: no hardcoded test results, no dummy facade implementations, no fake logs.
  2. Genuine implementations of:
     - 41 wallpapers manifest & background engine
     - 360 orbital topology & 3D tilted grid dual-mode
     - HealthcareAuthModal & session store
     - 7 high-glassmorphism business views with 4-stat KPI grids
     - 15 modules x 8 actions RBAC dynamic filtering & drawer
     - Standardized 4-element Chinese comments
     - 100% 0-Emoji rule
  3. Verify clean production build: `npm --prefix frontend run build` (0 error, 0 warning)
  4. Verify test execution:
     - `node tests/e2e/showcase_regression.spec.ts`
     - `node tests/e2e/m4_business_views_rbac.js`
  5. Check `tests/screenshots/` integrity
