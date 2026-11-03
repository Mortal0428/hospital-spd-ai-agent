## 2026-11-02T14:56:59Z
You are teamwork_worker: Forensic Audit Remediation Implementation Worker.
Your working directory is: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\worker_audit_fix

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY Context:
- MUST read ORIGINAL_REQUEST.md: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\ORIGINAL_REQUEST.md
- Full Audit Evidence: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\teamwork_auditor_m5\handoff.md
- Remediation Strategy: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\teamwork_explorer_audit_remediation\handoff.md
- PROJECT.md: e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\orchestrator\PROJECT.md

Tasks to execute:
1. In `frontend/src/views/ShowcaseView.vue`, normalize `mediaLayerStyle`:
   Change all branches to strictly avoid CSS shorthand `background`, and explicitly specify:
   ```ts
   /**
    * 依据当前壁纸类型计算媒体背景层样式 (渐变色、本地图片或透明)
    * 严格使用非简写属性 backgroundImage，并显式配置 backgroundSize: 'cover'，杜绝内联样式覆盖导致的 T2.4 断言失败
    * @returns {import('vue').CSSProperties}
    * @route internal
    * @throws 无
    */
   const mediaLayerStyle = computed(() => {
     const wp = currentWp.value;
     if (wp.hasVideo && wp.videoUrl) {
       return {
         backgroundImage: 'none',
         backgroundColor: 'transparent',
         backgroundSize: 'cover',
         backgroundPosition: 'center center'
       };
     }
     if (wp.src) {
       if (wp.src.startsWith('linear') || wp.src.startsWith('radial')) {
         return {
           backgroundImage: wp.src,
           backgroundSize: 'cover',
           backgroundPosition: 'center center'
         };
       }
       return {
         backgroundImage: `url("${wp.src}")`,
         backgroundSize: 'cover',
         backgroundPosition: 'center center'
       };
     }
     return {
       backgroundImage: 'radial-gradient(ellipse at center, #0c4a6e 0%, #080c14 70%)',
       backgroundSize: 'cover',
       backgroundPosition: 'center center'
     };
   });
   ```
2. Verify production build:
   Execute `npm --prefix frontend run build` to ensure 0 errors, 0 warnings.
3. Verify Playwright E2E suites:
   - Actually execute `node tests/e2e/showcase_regression.spec.ts` in real terminal. Ensure it runs through Tier 1 ~ Tier 4 without failure, and capture the real command exit code.
   - Execute `node tests/e2e/m4_business_views_rbac.js` to ensure 0 regression across all 7 views and RBAC sidebars.
4. Verify 0-Emoji rule and standard 4-element comments on modified functions.
5. Write your structured handoff report to `e:\个人项目作品\杭电集训项目\0728_陈永兴_医疗物资系统\.agents\teamwork\worker_audit_fix\handoff.md` and send message to orchestrator.
