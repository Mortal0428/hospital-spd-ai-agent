# Context for worker_audit_fix
- Task: Implement Forensic Audit Remediation for Milestone M5
- Target: `frontend/src/views/ShowcaseView.vue`
- Guidance:
  1. Read .agents/teamwork/teamwork_explorer_audit_remediation/handoff.md
  2. Implement recommended fix in `mediaLayerStyle`:
     Change all branches (gradient, video, image, fallback) to strictly use non-shorthand `backgroundImage`, and explicitly set `backgroundSize: 'cover'` and `backgroundPosition: 'center center'`.
  3. Run `npm --prefix frontend run build` (verify 0 errors, 0 warnings).
  4. Run `node tests/e2e/showcase_regression.spec.ts` and capture real console output showing exit code 0.
  5. Run `node tests/e2e/m4_business_views_rbac.js` to ensure 0 regression.
  6. Deliver report to `.agents/teamwork/worker_audit_fix/handoff.md`.
