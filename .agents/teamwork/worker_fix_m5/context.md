# Context for worker_fix_m5
- Task: Remediation of M5 Reviewer Findings (Zen Scoped CSS mistranslation, ShowcaseView missing handleLoginSuccess, Vite manualChunks)
- Reviewer Report: .agents/teamwork/teamwork_reviewer_m5/handoff.md
- Scope:
  1. `frontend/src/styles/theme.css` / `frontend/src/styles/main.css`: Add global clean rules for `body.zen-pure-mode`
  2. `frontend/src/components/showcase/TopFloatNav.vue`: Remove broken scoped `:global(body.zen-pure-mode)`
  3. `frontend/src/components/showcase/HeroSection.vue`: Remove broken scoped `:global(body.zen-pure-mode)`
  4. `frontend/src/components/showcase/WallpaperDrawer.vue`: Remove broken scoped `:global(body.zen-pure-mode)`
  5. `frontend/src/views/ShowcaseView.vue`: Remove broken scoped `:global(body.zen-pure-mode)`, implement `handleLoginSuccess`
  6. `frontend/vite.config.ts`: Add `manualChunks` or increase `chunkSizeWarningLimit` to eliminate chunk warning
  7. Run `npm --prefix frontend run build` to verify 0 errors, 0 warnings
  8. Run `node tests/e2e/showcase_regression.spec.ts` to verify Tier 1-4 passes in real Vite mode
  9. Run `node tests/e2e/m4_business_views_rbac.js` to ensure 0 regression
