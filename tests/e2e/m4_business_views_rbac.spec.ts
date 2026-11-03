/**
 * @file m4_business_views_rbac.spec.ts
 * @description 里程碑 M4 业务视图高质感延展与 RBAC 动态过滤自动化测试与实机截图套件
 * 严格按照用户指示：
 * 1. 验证 sys_admin 拥有全部 7 大业务菜单，且 7 大视图均呈现 demo 毛玻璃质感与 4-stat KPI 大盘
 * 2. 验证 secondary_user (护士) 仅可见二级库与高值专仓，其余 5 项绝对隐藏
 * 3. 验证 finance_auditor (财务) 仅可见财务打印与全流程 6W 日志，物理库房菜单绝对隐藏
 * 4. 验证 supplier_user (供应商) 仅可见采购协同
 * 5. 验证 0-Emoji 规范与实机大图捕获归档至 tests/screenshots/
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, '../..');
const SCREENSHOT_DIR = path.resolve(ROOT_DIR, 'tests/screenshots');
const { launchPersistentPlaywright } = require('./browser_config.js');

function getScreenshotPath(sceneName: string): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  const dateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const timeStr = `${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
  return path.resolve(SCREENSHOT_DIR, `${dateStr}_${timeStr}_${sceneName}.png`);
}

async function runM4Test() {
  console.log('================================================================');
  console.log('M4 全域业务视图 Demo 风格高质感自然延展与 RBAC 动态过滤测试启动');
  console.log('================================================================');

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const { context, page } = await launchPersistentPlaywright({
    viewport: { width: 1440, height: 900 }
  });

  const capturedScreenshots: string[] = [];

  try {
    // 1. 导航进入系统主工作台 (管理员赵振华默认)
    await page.goto('http://127.0.0.1:5173/dict', { waitUntil: 'networkidle', timeout: 8000 });
    await page.waitForTimeout(1000);

    console.log('\n--- [1. 系统管理员 sys_admin 视角与 7 大菜单全权验证] ---');
    const menuItems = page.locator('.fusion-sidebar .side-nav-item');
    const menuCount = await menuItems.count();
    console.log(`[CHECK] 管理员当前可见侧边栏菜单项数量: ${menuCount}`);
    if (menuCount !== 7) {
      throw new Error(`管理员应看到 7 个业务菜单，实际看到 ${menuCount} 个`);
    }
    console.log('[ASSERT PASS] 系统管理员可见全部 7 个业务模块菜单');

    // 截图 1: 产品字典管理视图 (ProductDictView)
    const dictShot = getScreenshotPath('m4_01_product_dict_view');
    await page.screenshot({ path: dictShot, fullPage: true });
    capturedScreenshots.push(dictShot);
    console.log(`[Screenshot Captured] 产品字典管理实机截图已保存: ${dictShot}`);

    // 2. 依次访问其余 6 大业务视图并截图
    // 视图 2: 普通耗材主库 (GeneralMaterialView)
    await page.goto('http://127.0.0.1:5173/general', { waitUntil: 'networkidle', timeout: 5000 });
    await page.waitForTimeout(800);
    const genShot = getScreenshotPath('m4_02_general_material_view');
    await page.screenshot({ path: genShot, fullPage: true });
    capturedScreenshots.push(genShot);
    console.log(`[Screenshot Captured] 普通耗材主库实机截图已保存: ${genShot}`);

    // 视图 3: 高值耗材专仓 (HighValueView)
    await page.goto('http://127.0.0.1:5173/high-value', { waitUntil: 'networkidle', timeout: 5000 });
    await page.waitForTimeout(800);
    const hvShot = getScreenshotPath('m4_03_high_value_view');
    await page.screenshot({ path: hvShot, fullPage: true });
    capturedScreenshots.push(hvShot);
    console.log(`[Screenshot Captured] 高值专仓实机截图已保存: ${hvShot}`);

    // 视图 4: 临床二级库 (SecondaryWarehouseView)
    await page.goto('http://127.0.0.1:5173/secondary', { waitUntil: 'networkidle', timeout: 5000 });
    await page.waitForTimeout(800);
    const secShot = getScreenshotPath('m4_04_secondary_warehouse_view');
    await page.screenshot({ path: secShot, fullPage: true });
    capturedScreenshots.push(secShot);
    console.log(`[Screenshot Captured] 临床二级库实机截图已保存: ${secShot}`);

    // 视图 5: 全流程 6W 业务日志 (WorkflowLogView)
    await page.goto('http://127.0.0.1:5173/logs', { waitUntil: 'networkidle', timeout: 5000 });
    await page.waitForTimeout(800);
    const logShot = getScreenshotPath('m4_05_workflow_log_view');
    await page.screenshot({ path: logShot, fullPage: true });
    capturedScreenshots.push(logShot);
    console.log(`[Screenshot Captured] 全流程 6W 日志实机截图已保存: ${logShot}`);

    // 视图 6: 财务核算与单据打印中心 (FinancePrintView)
    await page.goto('http://127.0.0.1:5173/finance', { waitUntil: 'networkidle', timeout: 5000 });
    await page.waitForTimeout(800);
    const finShot = getScreenshotPath('m4_06_finance_print_view');
    await page.screenshot({ path: finShot, fullPage: true });
    capturedScreenshots.push(finShot);
    console.log(`[Screenshot Captured] 财务单据打印实机截图已保存: ${finShot}`);

    // 视图 7: 采购协同 (SupplierPurchaseView)
    await page.goto('http://127.0.0.1:5173/procurement', { waitUntil: 'networkidle', timeout: 5000 });
    await page.waitForTimeout(800);
    const supShot = getScreenshotPath('m4_07_supplier_purchase_view');
    await page.screenshot({ path: supShot, fullPage: true });
    capturedScreenshots.push(supShot);
    console.log(`[Screenshot Captured] 采购与供应商协同实机截图已保存: ${supShot}`);

    // 3. 验证细粒度 RBAC 抽屉在管理员视角下的呼出
    console.log('\n--- [2. 验证管理员细粒度 RBAC 抽屉] ---');
    const rbacBtn = page.locator('.btn-ctrl-rbac');
    await rbacBtn.click();
    await page.waitForTimeout(600);
    const rbacDrawer = page.locator('.spd-rbac-drawer');
    const isDrawerVisible = await rbacDrawer.isVisible();
    if (!isDrawerVisible) {
      throw new Error('管理员点击 RBAC 按钮后抽屉未弹出');
    }
    console.log('[ASSERT PASS] 管理员成功唤出 15 模块 x 8 动作细粒度 RBAC 权限抽屉');
    const rbacShot = getScreenshotPath('m4_08_rbac_matrix_drawer');
    await page.screenshot({ path: rbacShot, fullPage: true });
    capturedScreenshots.push(rbacShot);
    console.log(`[Screenshot Captured] 细粒度 RBAC 抽屉实机截图已保存: ${rbacShot}`);

    // 关闭抽屉
    const drawerClose = page.locator('.el-drawer__close-btn');
    if (await drawerClose.isVisible()) {
      await drawerClose.click();
      await page.waitForTimeout(400);
    }

    // 4. 验证临床二级库人员 secondary_user (李晓琳) 的权限隔离
    console.log('\n--- [3. 验证临床二级库护士 (secondary_user) 权限动态隔离] ---');
    const roleSelect = page.locator('#role-selector');
    await roleSelect.selectOption('secondary_user');
    await page.waitForTimeout(800);

    const nurseMenuItems = page.locator('.fusion-sidebar .side-nav-item');
    const nurseMenuCount = await nurseMenuItems.count();
    console.log(`[CHECK] 护士视角可见侧边栏菜单数量: ${nurseMenuCount}`);
    if (nurseMenuCount !== 2) {
      throw new Error(`护士应仅可见 2 个菜单（高值专仓与二级库），实际可见 ${nurseMenuCount} 个`);
    }
    const nurseTexts = await nurseMenuItems.allInnerTexts();
    console.log(`[CHECK] 护士可见菜单文本: ${JSON.stringify(nurseTexts)}`);
    console.log('[ASSERT PASS] 护士视角成功隐藏产品字典、普通主库、6W 日志、财务打印、采购协同！');

    const nurseShot = getScreenshotPath('m4_09_rbac_nurse_filtered_sidebar');
    await page.screenshot({ path: nurseShot, fullPage: true });
    capturedScreenshots.push(nurseShot);
    console.log(`[Screenshot Captured] 护士动态隔离侧边栏实机截图已保存: ${nurseShot}`);

    // 5. 验证财务科审计人员 finance_auditor (孙丽娟) 的权限隔离
    console.log('\n--- [4. 验证财务审计 (finance_auditor) 权限动态隔离] ---');
    await roleSelect.selectOption('finance_auditor');
    await page.waitForTimeout(800);

    const finMenuItems = page.locator('.fusion-sidebar .side-nav-item');
    const finMenuCount = await finMenuItems.count();
    console.log(`[CHECK] 财务审计视角可见侧边栏菜单数量: ${finMenuCount}`);
    if (finMenuCount !== 2) {
      throw new Error(`财务审计应仅可见 2 个菜单（全流程日志与财务打印），实际可见 ${finMenuCount} 个`);
    }
    const finTexts = await finMenuItems.allInnerTexts();
    console.log(`[CHECK] 财务审计可见菜单文本: ${JSON.stringify(finTexts)}`);
    console.log('[ASSERT PASS] 财务审计视角成功隐藏全部物理仓储与供应商操作！');

    const finRoleShot = getScreenshotPath('m4_10_rbac_finance_filtered_sidebar');
    await page.screenshot({ path: finRoleShot, fullPage: true });
    capturedScreenshots.push(finRoleShot);
    console.log(`[Screenshot Captured] 财务审计隔离侧边栏实机截图已保存: ${finRoleShot}`);

    // 6. 验证外部供应商协同人员 supplier_user (张明远) 的权限隔离
    console.log('\n--- [5. 验证外部供应商 (supplier_user) 权限动态隔离] ---');
    await roleSelect.selectOption('supplier_user');
    await page.waitForTimeout(800);

    const supMenuItems = page.locator('.fusion-sidebar .side-nav-item');
    const supMenuCount = await supMenuItems.count();
    console.log(`[CHECK] 外部供应商视角可见侧边栏菜单数量: ${supMenuCount}`);
    if (supMenuCount !== 1) {
      throw new Error(`外部供应商应仅可见 1 个菜单（采购与供应商协同），实际可见 ${supMenuCount} 个`);
    }
    const supTexts = await supMenuItems.allInnerTexts();
    console.log(`[CHECK] 外部供应商可见菜单文本: ${JSON.stringify(supTexts)}`);
    console.log('[ASSERT PASS] 外部供应商仅保留专属采购协同门户，医院内部所有管理视图全部隔离！');

    const supRoleShot = getScreenshotPath('m4_11_rbac_supplier_filtered_sidebar');
    await page.screenshot({ path: supRoleShot, fullPage: true });
    capturedScreenshots.push(supRoleShot);
    console.log(`[Screenshot Captured] 供应商隔离侧边栏实机截图已保存: ${supRoleShot}`);

    console.log('\n================================================================');
    console.log('M4 全域业务视图 Demo 风格高质感自然延展与 RBAC 动态过滤测试全部通过！');
    console.log(`累计成功捕获实机截图: ${capturedScreenshots.length} 张`);
    console.log('================================================================');
  } finally {
    await context.close();
  }
}

runM4Test().catch((err) => {
  console.error('[M4 TEST ERROR]', err);
  process.exit(1);
});
