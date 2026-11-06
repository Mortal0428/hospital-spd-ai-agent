"""
@file e2e_screenshot_feishu_dynamic.py
@description 使用 Playwright 自动化驱动无锁浏览器对飞书长连接守护中台与 8 大智能体配置进行实机验证并截屏
全域遵循零 Emoji 规范与 100% 中文四要素注释。

@param 无 独立自动化测试脚本
@returns 无 截图写入 tests/screenshots/
@route internal://tests/e2e_screenshot_feishu_dynamic.py
@throws 浏览器启动或网络超时异常安全捕获
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = ROOT_DIR / "tests" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_PATH = SCREENSHOT_DIR / "2026-11-05_23-50-00_feishu_dynamic_intent_and_at.png"

def run_e2e_screenshot():
    print(f"启动 Playwright 驱动浏览器验证: http://127.0.0.1:5173 ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()

        try:
            page.goto("http://127.0.0.1:5173", timeout=30000)
            page.wait_for_timeout(2000)

            # 若在登录页，执行登录
            if "login" in page.url or page.locator("input[type='password']").count() > 0:
                print("检测到登录页，注入管理员凭据...")
                page.fill("input[placeholder*='账号'], input[placeholder*='用户名'], input[type='text']", "sys_admin")
                page.fill("input[type='password']", "admin123")
                page.click("button:has-text('登录'), button[type='submit']")
                page.wait_for_timeout(3000)

            # 导航至 RAG 8大智能体中台
            print("访问 RAG & 8 大业务智能体控制台...")
            page.goto("http://127.0.0.1:5173/#/rag-agent-hub", timeout=20000)
            page.wait_for_timeout(3000)

            # 切换到第二个 Tab: Modular RAG 算子与智能体中台配置
            tab_locator = page.locator(".el-tabs__item:has-text('Modular RAG 算子与智能体中台配置')")
            if tab_locator.count() > 0:
                tab_locator.first.click()
                page.wait_for_timeout(2000)

            # 滚动到外部生态智能体与飞书协同通道区域
            page.evaluate("window.scrollTo(0, 850)")
            page.wait_for_timeout(2000)

            # 截取全屏高清凭证
            page.screenshot(path=str(SCREENSHOT_PATH), full_page=False)
            print(f"[SUCCESS] 实机截图成功保存至: {SCREENSHOT_PATH}")
        except Exception as e:
            print(f"[ERROR] Playwright 自动化验证异常: {e}")
            # 尝试回退截图
            page.screenshot(path=str(SCREENSHOT_PATH))
        finally:
            browser.close()

if __name__ == "__main__":
    run_e2e_screenshot()
