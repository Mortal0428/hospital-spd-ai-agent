const path = require('path');
const fs = require('fs');

/**
 * 解析并引入系统可用的 Playwright 核心对象
 * @returns {object} Playwright 核心对象
 * @throws {Error} 若未找到任何 Playwright 模块则抛出异常
 */
function resolvePlaywright() {
  try {
    return require('playwright');
  } catch (err) {
    const fallbackPath = 'C:/Users/27705/.gemini/config/mcp-playwright/node_modules/playwright';
    return require(fallbackPath);
  }
}

const { chromium } = resolvePlaywright();

/**
 * 启动并获取系统浏览器的持久化上下文实例（方案 A：持久化 Profile 模式）
 * 采用独立的数据存储目录，支持持久化保存 Cookie 与会话状态，且不与用户正在运行的浏览器发生文件锁冲突
 *
 * @param {object} [options={}] 启动参数选项
 * @param {boolean} [options.headless=true] 是否无头运行，默认 true
 * @param {string} [options.channel='msedge'] 调用浏览器通道，默认使用系统内置的 Chromium / Edge 内核
 * @param {string} [options.profileDir] 持久化存储目录，默认配置为系统级专用 AutomationProfile
 * @returns {Promise<{context: import('playwright').BrowserContext, page: import('playwright').Page}>} 返回持久化上下文与页面实例
 * @route internal://tests/e2e/browser_config.js/launchPersistentPlaywright
 * @throws {Error} 启动失败时抛出格式化错误信息并附带环境排查建议
 */
async function launchPersistentPlaywright(options = {}) {
  const defaultProfileDir = path.resolve('C:/Users/27705/AppData/Local/Citro Labs/ego lite/User Data/AutomationProfile');
  const profileDir = options.profileDir || defaultProfileDir;
  const isHeadless = options.headless !== undefined ? options.headless : true;
  const channel = options.channel || 'msedge';

  if (!fs.existsSync(profileDir)) {
    fs.mkdirSync(profileDir, { recursive: true });
  }

  try {
    const context = await chromium.launchPersistentContext(profileDir, {
      channel,
      headless: isHeadless,
      viewport: { width: 1440, height: 900 },
      args: [
        '--no-default-browser-check',
        '--no-first-run',
        '--disable-blink-features=AutomationControlled'
      ]
    });

    const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();
    return { context, page };
  } catch (error) {
    throw new Error(
      `[BrowserConfigError] 启动持久化浏览器上下文失败: ${error.message}。\n` +
      `排查建议: 请确认目录 ${profileDir} 具备读写权限。`
    );
  }
}

/**
 * 获取本地 Ego 浏览器协同驱动配置信息
 * @returns {{cliPath: string, appPath: string, userDataDir: string}} Ego 浏览器各核心路径对象
 * @route internal://tests/e2e/browser_config.js/getEgoDriverInfo
 */
function getEgoDriverInfo() {
  return {
    cliPath: 'C:\\Users\\27705\\.local\\share\\ego\\active_version_dir\\ego-browser.exe',
    appPath: 'C:\\Program Files\\Citro Labs\\ego lite\\Application\\ego.exe',
    userDataDir: 'C:\\Users\\27705\\AppData\\Local\\Citro Labs\\ego lite\\User Data'
  };
}

module.exports = {
  launchPersistentPlaywright,
  getEgoDriverInfo
};
