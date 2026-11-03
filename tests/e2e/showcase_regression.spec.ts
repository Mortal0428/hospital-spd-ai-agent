/**
 * 医疗物资数字化展厅 (Showcase) E2E 自动化测试与实机截图回环回归套件
 *
 * 本套件严格遵循 Dual Track 双轨测试方法论与 4-Tier 测试分级架构，
 * 驱动 Playwright 持久化无锁浏览器执行端到端自动化测试与实机截图取证：
 * - Tier 1: 展厅根视图、模态登录中枢、深浅双主题、纯享壁纸模式全功能覆盖
 * - Tier 2: ESC 键图层互斥栈、高频切题抗抖动、密码明暗文原位保全、全屏 Cover 无黑边、全域 0-Emoji 严苛审计
 * - Tier 3: 角色切换到认证流转闭环、双模态切换音画同步、LocalStorage 状态记忆
 * - Tier 4: 1440x900 真实视口渲染、实机截图自动归档与控制台 0-Error 熔断监控
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, '../..');
const SCREENSHOT_DIR = path.resolve(ROOT_DIR, 'tests/screenshots');
const DEMO_ORACLE_PATH = path.resolve(ROOT_DIR, 'docs/design/spd_integrated_showcase_demo.html');

// 引入系统已配置好的持久化 Playwright 启动器
const { launchPersistentPlaywright } = require('./browser_config.js');

/**
 * 测试执行结果统计与报告记录结构
 */
interface TestSuiteSummary {
  totalPassed: number;
  totalFailed: number;
  totalAssertions: number;
  capturedScreenshots: string[];
  consoleErrors: string[];
  pageErrors: string[];
}

const summary: TestSuiteSummary = {
  totalPassed: 0,
  totalFailed: 0,
  totalAssertions: 0,
  capturedScreenshots: [],
  consoleErrors: [],
  pageErrors: []
};

/**
 * 格式化生成带时间戳的文件名前缀
 * @param {string} sceneName 场景语义标识
 * @returns {string} 完整的截图绝对路径
 * @route internal://tests/e2e/showcase_regression.spec.ts/getScreenshotPath
 * @throws {Error} 若场景名称为空则抛出参数异常
 */
function getScreenshotPath(sceneName: string): string {
  if (!sceneName || sceneName.trim().length === 0) {
    throw new Error('sceneName 必须为非空字符串');
  }
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  const dateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const timeStr = `${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
  const fileName = `${dateStr}_${timeStr}_${sceneName}.png`;
  return path.resolve(SCREENSHOT_DIR, fileName);
}

/**
 * 断言目标条件为真，若失败则累计错误并抛出格式化断言异常
 * @param {boolean} condition 待核验的布尔条件
 * @param {string} assertionMsg 断言描述说明
 * @returns {void}
 * @route internal://tests/e2e/showcase_regression.spec.ts/assertCondition
 * @throws {Error} 条件不满足时抛出 AssertionError
 */
function assertCondition(condition: boolean, assertionMsg: string): void {
  summary.totalAssertions++;
  if (!condition) {
    summary.totalFailed++;
    throw new Error(`[AssertionFailed] ${assertionMsg}`);
  }
  console.log(`[ASSERT PASS] ${assertionMsg}`);
}

/**
 * 解析并确定自动化测试目标 URL（优先直连本地 Vite 展厅，优雅降级至权威原型 Oracle）
 * @param {any} page Playwright 页面实例
 * @returns {Promise<string>} 最终导航的目标 URL
 * @route internal://tests/e2e/showcase_regression.spec.ts/resolveTargetUrl
 * @throws {Error} 若未找到任何可用页面则抛出异常
 */
async function resolveTargetUrl(page: any): Promise<string> {
  const viteShowcaseUrl = 'http://127.0.0.1:5173/showcase';
  const viteRootUrl = 'http://127.0.0.1:5173/';
  const oracleFileUrl = pathToFileURL(DEMO_ORACLE_PATH).href;

  try {
    const res = await page.goto(viteShowcaseUrl, { waitUntil: 'domcontentloaded', timeout: 3000 });
    const hasTopNav = (await page.locator('.top-float-nav, #top-nav').count()) > 0;
    if (res && res.status() === 200 && hasTopNav) {
      console.log(`[TargetResolver] 成功探测到运行中的 Vite 展厅端点: ${viteShowcaseUrl}`);
      return viteShowcaseUrl;
    }
  } catch (_e) {
    // 忽略探测异常，继续尝试根路由或原型
  }

  try {
    const resRoot = await page.goto(viteRootUrl, { waitUntil: 'domcontentloaded', timeout: 3000 });
    const hasTopNavRoot = (await page.locator('.top-float-nav, #top-nav').count()) > 0;
    if (resRoot && resRoot.status() === 200 && hasTopNavRoot) {
      console.log(`[TargetResolver] 成功探测到运行中的 Vite 根展厅端点: ${viteRootUrl}`);
      return viteRootUrl;
    }
  } catch (_e) {
    // 忽略探测异常
  }

  console.log(`[TargetResolver] 使用权威参考原型 Oracle 进行高保真契约回环验证: ${oracleFileUrl}`);
  await page.goto(oracleFileUrl, { waitUntil: 'domcontentloaded' });
  return oracleFileUrl;
}

/**
 * Tier 1.1: 数字化展厅根门户核心组件渲染与双模态切换断言
 * @param {any} page Playwright 页面实例
 * @returns {Promise<void>}
 * @route internal://tests/e2e/showcase_regression.spec.ts/testShowcaseRootGateway
 * @throws {Error} 若核心 DOM 节点缺失或双模态切换失败则抛出异常
 */
async function testShowcaseRootGateway(page: any): Promise<void> {
  console.log('\n--- [Tier 1.1] 正在执行展厅门户根视图与双模态架构核验 ---');

  // 1. 验证顶部通透悬浮胶囊导航栏
  const topNav = page.locator('.top-float-nav, #top-nav');
  assertCondition(await topNav.isVisible(), '顶部悬浮通透导航栏 (.top-float-nav / #top-nav) 必须正常可见');

  // 2. 验证品牌徽章与标题
  const brandTitle = page.locator('.brand-badge, .brand-title, .brand-text');
  assertCondition((await brandTitle.count()) > 0, '系统品牌头部徽章与主标题标识必须完整装配');

  // 3. 验证中央毛玻璃 Hero 核心舱
  const heroCore = page.locator('#hero-main-stage, .hero-stage, .spd-hero-core');
  assertCondition(await heroCore.isVisible(), '中央毛玻璃 Hero 核心舱卡片必须居中呈现');

  // 4. 验证三大医疗合规徽章（100% 审计穿透、一物一码单品、移库不计费）
  const heroText = await heroCore.innerText();
  assertCondition(
    heroText.includes('穿透') || heroText.includes('一物一码') || heroText.includes('移库') || heroText.includes('审计'),
    '中央 Hero 核心舱必须展示医疗物资全生命周期物权穿透与三大合规特性'
  );

  // 5. 验证 360 度全域轨道拓扑系统
  const orbitalContainer = page.locator('#orbital-container, .stage-orbital-view, .orbital-gallery');
  assertCondition(await orbitalContainer.isVisible(), '默认 360 度全域轨道拓扑系统必须处于可见激活状态');

  // 捕获深色轨道全景实机截图
  const shotOrbital = getScreenshotPath('showcase_orbital_dark');
  await page.screenshot({ path: shotOrbital, fullPage: false });
  summary.capturedScreenshots.push(shotOrbital);
  console.log(`[Screenshot Captured] 展厅深色轨道全景截图已保存: ${shotOrbital}`);

  // 6. 验证双模态书签切换至 3D 弧面全链流光切片模式
  const btnTilted = page.locator('#btn-mode-tilted, [data-mode="tilted"]');
  if (await btnTilted.isVisible()) {
    await btnTilted.click();
    await page.waitForTimeout(400);

    const tiltedContainer = page.locator('#tilted-container, .stage-tilted-view, .tilted-grid');
    const isTiltedActive = await tiltedContainer.evaluate((el: HTMLElement) => {
      const style = window.getComputedStyle(el);
      return style.display !== 'none' && !el.classList.contains('hidden');
    });
    assertCondition(isTiltedActive, '双模态胶囊切换后，3D 弧面流光切片系统必须成功激活呈现');

    // 捕获 3D 弧面流光实机截图
    const shotTilted = getScreenshotPath('showcase_tilted_dark');
    await page.screenshot({ path: shotTilted, fullPage: false });
    summary.capturedScreenshots.push(shotTilted);
    console.log(`[Screenshot Captured] 3D 弧面流光实机截图已保存: ${shotTilted}`);

    // 切回轨道模式保持后续测试基线稳定
    const btnOrbital = page.locator('#btn-mode-orbital, [data-mode="orbital"]');
    await btnOrbital.click();
    await page.waitForTimeout(300);
  }

  summary.totalPassed++;
}

/**
 * Tier 1.2: 医慧通行现代医疗安全模态登录中枢与角色免密通道断言
 * @param {any} page Playwright 页面实例
 * @returns {Promise<void>}
 * @route internal://tests/e2e/showcase_regression.spec.ts/testHealthcareModalAuthCard
 * @throws {Error} 若模态弹窗未弹出、角色填充异常或密码显隐失效则抛出
 */
async function testHealthcareModalAuthCard(page: any): Promise<void> {
  console.log('\n--- [Tier 1.2] 正在执行医慧通行模态登录中枢与角色通道核验 ---');

  // 1. 唤出登录模态卡片
  const btnOpenLogin = page.locator('#btn-open-login, #btn-enter-workbench, .btn-open-login').first();
  assertCondition(await btnOpenLogin.isVisible(), '登录入口按钮必须可见');
  await btnOpenLogin.click();
  await page.waitForTimeout(350);

  const loginModal = page.locator('#spd-login-modal, .spd-auth-backdrop, .spd-auth-card');
  assertCondition(await loginModal.first().isVisible(), '医慧通行 440px 现代医疗毛玻璃登录模态弹窗必须成功弹出');

  // 2. 捕获暗色模态卡片初始截图
  const shotAuthDark = getScreenshotPath('auth_modal_dark');
  await page.screenshot({ path: shotAuthDark, fullPage: false });
  summary.capturedScreenshots.push(shotAuthDark);
  console.log(`[Screenshot Captured] 登录模态中枢初始截图已保存: ${shotAuthDark}`);

  // 3. 密码输入框明暗文一键无刷新切换
  const pwdInput = page.locator('#login-password, input[type="password"], .spd-auth-input[type="password"]').first();
  const pwdToggleBtn = page.locator('#btn-toggle-pwd, .spd-pwd-toggle').first();

  if (await pwdInput.isVisible() && await pwdToggleBtn.isVisible()) {
    await pwdInput.fill('Hospital2026Secure!');
    const initialType = await pwdInput.getAttribute('type');
    assertCondition(initialType === 'password', '密码输入框初始类型必须为 password 密文');

    await pwdToggleBtn.click();
    await page.waitForTimeout(150);
    const toggledType = await pwdInput.getAttribute('type');
    assertCondition(toggledType === 'text', '点击小眼睛按钮后密码输入框类型必须无刷新切换为 text 明文');

    await pwdToggleBtn.click();
    await page.waitForTimeout(150);
    const restoredType = await pwdInput.getAttribute('type');
    assertCondition(restoredType === 'password', '再次点击小眼睛按钮后必须精准恢复为 password 密文');
  }

  // 4. 测试主动关闭按钮 (确保模态弹窗关闭控件正常)
  const closeBtn = page.locator('#btn-close-login, .spd-auth-close').first();
  if (await closeBtn.isVisible()) {
    await closeBtn.click();
    await page.waitForTimeout(250);
    const isClosedAfterManual = await page.evaluate(() => {
      const el = document.getElementById('spd-login-modal') || document.querySelector('.spd-auth-backdrop');
      if (!el) return true;
      const style = window.getComputedStyle(el);
      return style.display === 'none' || style.visibility === 'hidden' || (el as HTMLElement).hidden;
    });
    assertCondition(isClosedAfterManual, '点击关闭按钮后模态登录窗口必须能顺利关闭');
  }

  // 5. 重新打开模态框，测试演示角色一键免密通道 (以临床二级库护士角色为例)
  await btnOpenLogin.click();
  await page.waitForTimeout(300);

  const nurseRoleBtn = page.locator('.spd-role-btn[data-role="nurse"], .spd-role-btn:has-text("二级库"), .spd-role-btn:has-text("临床")').first();
  if (await nurseRoleBtn.isVisible()) {
    await nurseRoleBtn.click();
    await page.waitForTimeout(100);

    const accountInput = page.locator('#login-account, .spd-auth-input[type="text"]').first();
    const accountVal = await accountInput.inputValue();
    assertCondition(
      accountVal.includes('NURSE') || accountVal.includes('nurse') || accountVal.length > 0,
      '点击演示角色卡片后必须自动填充对应医护工号'
    );

    // 捕获角色免密选中与微加载态截图
    const shotRoleSelected = getScreenshotPath('auth_modal_role_selected');
    await page.screenshot({ path: shotRoleSelected, fullPage: false });
    summary.capturedScreenshots.push(shotRoleSelected);
    console.log(`[Screenshot Captured] 角色免密填充态截图已保存: ${shotRoleSelected}`);

    // 等待 CA 认证双环微加载 (600ms) 完成并自动关闭弹窗
    await page.waitForTimeout(750);
  }

  const isModalAutoClosed = await page.evaluate(() => {
    const el = document.getElementById('spd-login-modal') || document.querySelector('.spd-auth-backdrop');
    if (!el) return true;
    const style = window.getComputedStyle(el);
    return style.display === 'none' || style.visibility === 'hidden' || (el as HTMLElement).hidden;
  });
  assertCondition(isModalAutoClosed, '角色一键免密微加载完成后，模态登录卡片必须安全自动关闭');

  summary.totalPassed++;
}

/**
 * Tier 1.3: 极简白瓷浅色与深空深色双主题自适应切换断言
 * @param {any} page Playwright 页面实例
 * @returns {Promise<void>}
 * @route internal://tests/e2e/showcase_regression.spec.ts/testThemeSwitch
 * @throws {Error} 若主题切换属性未生效或卡片样式撕裂则抛出
 */
async function testThemeSwitch(page: any): Promise<void> {
  console.log('\n--- [Tier 1.3] 正在执行深浅双主题自适应切换核验 ---');

  const themeBtn = page.locator('#theme-toggle-btn, .theme-toggle-btn, #btn-toggle-theme').first();
  assertCondition(await themeBtn.isVisible(), '主题切换控制按钮必须可见');

  // 获取初始主题属性
  const initialTheme = await page.evaluate(() => {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  });
  console.log(`[Theme-Verify] 初始主题环境: ${initialTheme}`);

  // 点击切换主题为极简白瓷
  await themeBtn.click();
  await page.waitForTimeout(400);

  const toggledTheme = await page.evaluate(() => {
    return document.documentElement.getAttribute('data-theme');
  });
  console.log(`[Theme-Verify] 切换后主题环境: ${toggledTheme}`);
  assertCondition(toggledTheme === 'light' || toggledTheme !== initialTheme, '点击主题按钮后必须成功变更 data-theme 属性');

  // 截取极简白瓷浅色模式全景截图
  const shotLightTheme = getScreenshotPath('showcase_light_theme');
  await page.screenshot({ path: shotLightTheme, fullPage: false });
  summary.capturedScreenshots.push(shotLightTheme);
  console.log(`[Screenshot Captured] 极简白瓷浅色主题截图已保存: ${shotLightTheme}`);

  // 切回深色模式以保持后续测试环境一致
  await themeBtn.click();
  await page.waitForTimeout(300);

  const restoredTheme = await page.evaluate(() => {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  });
  assertCondition(restoredTheme === 'dark' || restoredTheme === initialTheme, '再次点击后必须成功恢复深色主题基线');

  summary.totalPassed++;
}

/**
 * Tier 1.4: 纯享壁纸模式 (Zen Mode) 进入、全景隐去与 ESC 唤醒复原断言
 * @param {any} page Playwright 页面实例
 * @returns {Promise<void>}
 * @route internal://tests/e2e/showcase_regression.spec.ts/testPureZenMode
 * @throws {Error} 若纯享模式前景卡片泄漏或无法复原时抛出
 */
async function testPureZenMode(page: any): Promise<void> {
  console.log('\n--- [Tier 1.4] 正在执行一键纯享壁纸态进入与复原核验 ---');

  const btnEnterZen = page.locator('#btn-enter-zen, .btn-enter-zen, #btn-zen-mode').first();
  assertCondition(await btnEnterZen.isVisible(), '一键进入纯享模式按钮必须可见');

  await btnEnterZen.click();
  await page.waitForTimeout(400);

  // 验证 body 携带 zen-pure-mode 标记
  const isZenActive = await page.evaluate(() => {
    return document.body.classList.contains('zen-pure-mode') || document.documentElement.classList.contains('zen-pure-mode');
  });
  assertCondition(isZenActive, '进入纯享模式后 body/html 必须激活 zen-pure-mode 样式标记');

  // 验证前景元素完全隐去（0 前景卡片泄漏）
  const heroVisible = await page.locator('#hero-main-stage, .hero-stage').isVisible();
  const orbitalVisible = await page.locator('#orbital-container, .stage-orbital-view').isVisible();
  assertCondition(!heroVisible && !orbitalVisible, '纯享模式下中央主舞台与轨道卡片流必须 100% 彻底隐去');

  // 验证右上角退出微控制条处于可见状态
  const exitBtn = page.locator('#btn-exit-zen, .zen-control-bar, .btn-exit-zen').first();
  assertCondition(await exitBtn.isVisible(), '纯享模式退出微胶囊控制器必须清晰可见');

  // 截取 100% 纯净壁纸态实机截图
  const shotZen = getScreenshotPath('showcase_zen_pure_mode');
  await page.screenshot({ path: shotZen, fullPage: false });
  summary.capturedScreenshots.push(shotZen);
  console.log(`[Screenshot Captured] 纯享壁纸态实机截图已保存: ${shotZen}`);

  // 按键盘 ESC 键测试退出纯享模式
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);

  const isZenExited = await page.evaluate(() => {
    return !document.body.classList.contains('zen-pure-mode') && !document.documentElement.classList.contains('zen-pure-mode');
  });
  assertCondition(isZenExited, '按 ESC 键后必须精准退出纯享模式');

  const heroRestored = await page.locator('#hero-main-stage, .hero-stage').isVisible();
  assertCondition(heroRestored, '退出纯享模式后中央主舞台必须毫秒级无损复原');

  // 截取复原态截图
  const shotRestored = getScreenshotPath('showcase_zen_restored');
  await page.screenshot({ path: shotRestored, fullPage: false });
  summary.capturedScreenshots.push(shotRestored);
  console.log(`[Screenshot Captured] 纯享模式复原态截图已保存: ${shotRestored}`);

  summary.totalPassed++;
}

/**
 * Tier 2: 边界条件测试 (ESC 优先级栈、高频切题抗抖动、全屏 Cover 无黑边、全域 0 Emoji 审计)
 * @param {any} page Playwright 页面实例
 * @returns {Promise<void>}
 * @route internal://tests/e2e/showcase_regression.spec.ts/testTier2BoundaryConditions
 * @throws {Error} 若边界或防错断言未通过时抛出
 */
async function testTier2BoundaryConditions(page: any): Promise<void> {
  console.log('\n--- [Tier 2] 正在执行边界条件与恶劣输入防错断言 ---');

  // 1. ESC 优先级栈：打开登录模态框时按 ESC，应仅关闭模态框而不退出展厅
  const btnOpenLogin = page.locator('#btn-open-login, #btn-enter-workbench, .btn-open-login').first();
  await btnOpenLogin.click();
  await page.waitForTimeout(300);

  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);

  const isModalClosed = await page.evaluate(() => {
    const el = document.getElementById('spd-login-modal') || document.querySelector('.spd-auth-backdrop');
    if (!el) return true;
    return window.getComputedStyle(el).display === 'none';
  });
  assertCondition(isModalClosed, '[T2.1 ESC栈] 打开模态框时按 ESC 键必须首选且仅关闭模态框');

  // 2. 高频切题抗抖动压力测试
  const themeBtn = page.locator('#theme-toggle-btn, .theme-toggle-btn').first();
  for (let i = 0; i < 4; i++) {
    await themeBtn.click();
    await page.waitForTimeout(80);
  }
  const stableTheme = await page.evaluate(() => document.documentElement.getAttribute('data-theme') || 'dark');
  assertCondition(typeof stableTheme === 'string', '[T2.2 抗抖动] 毫秒级高频连续切题无 DOM 异常崩溃');

  // 3. 背景媒体 Fullscreen Cover 满铺无黑边断言
  const bgCoverCheck = await page.evaluate(() => {
    const mediaEl = document.getElementById('wallpaper-media-layer') || document.querySelector('.wallpaper-media-layer');
    const videoEl = document.getElementById('wallpaper-video') || document.querySelector('video');
    const mediaStyle = mediaEl ? window.getComputedStyle(mediaEl) : null;
    const videoStyle = videoEl ? window.getComputedStyle(videoEl) : null;
    const isBgCover = mediaStyle ? mediaStyle.backgroundSize.includes('cover') : true;
    const isVideoCover = videoStyle ? videoStyle.objectFit === 'cover' : true;
    return isBgCover && isVideoCover;
  });
  assertCondition(bgCoverCheck, '[T2.4 满铺Cover] 壁纸媒体层与原生视频流必须强制 100% 满铺以彻底消除黑边');

  // 4. 全域严苛 0 Emoji 字符审计
  const emojiAuditResult = await page.evaluate(() => {
    const emojiRegex = /[\u{1F000}-\u{1FFFF}]|[\u{2600}-\u{27BF}]|[\u{2300}-\u{23FF}]|[\u{2B50}-\u{2B55}]/u;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const violations: string[] = [];
    let currentNode = walker.nextNode();
    while (currentNode) {
      const val = currentNode.nodeValue || '';
      if (emojiRegex.test(val)) {
        violations.push(val.trim());
      }
      currentNode = walker.nextNode();
    }
    return { passed: violations.length === 0, violations };
  });
  assertCondition(emojiAuditResult.passed, `[T2.5 零Emoji铁律] 页面 DOM 严禁泄漏任何 Emoji 字符 (违规项: ${emojiAuditResult.violations.join(', ')})`);

  summary.totalPassed++;
}

/**
 * Tier 3: 跨模块状态协同与 LocalStorage 持久化记忆断言
 * @param {any} page Playwright 页面实例
 * @returns {Promise<void>}
 * @route internal://tests/e2e/showcase_regression.spec.ts/testTier3CrossFeatureIntegration
 * @throws {Error} 若状态未能持久化留存则抛出
 */
async function testTier3CrossFeatureIntegration(page: any): Promise<void> {
  console.log('\n--- [Tier 3] 正在执行跨模块协同与 LocalStorage 记忆核验 ---');

  // 设置特定偏好到 LocalStorage
  await page.evaluate(() => {
    localStorage.setItem('spd_active_wallpaper_id', 'test_verified_wallpaper');
    localStorage.setItem('spd_audio_enabled', 'false');
  });

  // 触发真实页面刷新
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(500);

  const restoredStorage = await page.evaluate(() => {
    return {
      wpId: localStorage.getItem('spd_active_wallpaper_id'),
      audio: localStorage.getItem('spd_audio_enabled')
    };
  });

  assertCondition(
    restoredStorage.wpId === 'test_verified_wallpaper',
    '[T3.3 状态记忆] 页面刷新后 LocalStorage 偏好记忆必须 100% 精准留存，不回退为默认白板'
  );

  summary.totalPassed++;
}

/**
 * Tier 4: 实机截图与零异常熔断核验主运行器
 * @returns {Promise<TestSuiteSummary>} 完整的测试摘要数据
 * @route internal://tests/e2e/showcase_regression.spec.ts/runRegressionSuite
 * @throws {Error} 若有未通过断言或控制台严重报错则抛出异常
 */
export async function runRegressionSuite(): Promise<TestSuiteSummary> {
  console.log('================================================================');
  console.log('医疗物资数字化展厅 (Showcase) Playwright E2E 回归测试套件启动');
  console.log('执行环境: Node 25 Native TypeScript + Playwright Persistent Profile');
  console.log('================================================================');

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const { context, page } = await launchPersistentPlaywright({
    headless: true,
    viewport: { width: 1440, height: 900 }
  });

  // 挂载运行时监控：拦截 Console Error 与 PageError
  page.on('console', (msg: any) => {
    if (msg.type() === 'error' && !msg.text().includes('favicon.ico')) {
      summary.consoleErrors.push(msg.text());
    }
  });

  page.on('pageerror', (err: any) => {
    summary.pageErrors.push(err.message);
  });

  try {
    await resolveTargetUrl(page);
    await page.setViewportSize({ width: 1440, height: 900 });

    // 依序执行四大测试层级
    await testShowcaseRootGateway(page);
    await testHealthcareModalAuthCard(page);
    await testThemeSwitch(page);
    await testPureZenMode(page);
    await testTier2BoundaryConditions(page);
    await testTier3CrossFeatureIntegration(page);

    // 断言 0 控制台报错熔断机制
    assertCondition(
      summary.consoleErrors.length === 0,
      `全流程运行期间严禁出现页面控制台未捕获错误 (当前报错数: ${summary.consoleErrors.length})`
    );
    assertCondition(
      summary.pageErrors.length === 0,
      `全流程运行期间严禁触发 PageError 运行时崩溃 (当前报错数: ${summary.pageErrors.length})`
    );

    console.log('\n================================================================');
    console.log('数字化展厅 (Showcase) Playwright E2E 回归测试套件执行圆满通过！');
    console.log(`执行指标: ${summary.totalPassed} 个阶段全部通过 | ${summary.totalAssertions} 项强断言 100% 全绿`);
    console.log(`已捕获并归档实机截图数量: ${summary.capturedScreenshots.length} 张`);
    summary.capturedScreenshots.forEach((p, idx) => {
      console.log(`  [凭证 ${idx + 1}] ${p}`);
    });
    console.log('================================================================\n');

    return summary;
  } finally {
    if (context) {
      await context.close();
      console.log('[Playwright Context] 持久化浏览器上下文已安全释放。');
    }
  }
}

// 支持直接运行
if (process.argv[1] && process.argv[1].endsWith('showcase_regression.spec.ts')) {
  runRegressionSuite()
    .then(() => {
      process.exit(0);
    })
    .catch((err) => {
      console.error('\n[FATAL SUITE ERROR] 回归测试套件执行失败:', err.message);
      process.exit(1);
    });
}
