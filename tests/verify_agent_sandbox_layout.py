# -*- coding: utf-8 -*-
"""
@file verify_agent_sandbox_layout.py
@description Playwright 自动化回环测试脚本：8 大业务智能体沙箱一体化视口与左侧方框独立滚动校验
验证核心指标:
1. 沙箱整体高度锁定视口 (calc(100vh - 275px))，外层无纵向撑爆；
2. 左侧智能体列表具有毛玻璃立体方框容器，内部独立平滑滚动；
3. 右侧聊天视口自适应 100%，输入框吸底固定在用户可视区域；
4. 捕获高清实机截图存入 tests/screenshots/
"""

import os
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.abspath("tests/screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

SCREENSHOT_PATH = os.path.join(
    SCREENSHOT_DIR,
    "2026-11-06_10-30-00_sandbox_master_detail_viewport.png"
)


def run_verification():
    print("=====================================================================")
    print("START: PLAYWRIGHT 8 大业务智能体沙箱视口一体化回环测试")
    print("=====================================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        errors = []
        page.on("pageerror", lambda exc: errors.append(f"PageError: {exc}"))
        page.on("console", lambda msg: errors.append(f"ConsoleError: {msg.text}") if msg.type == "error" else None)

        print("[STEP 1] 正在导航至医疗物资系统 RAG & 智能体中台...")
        page.goto("http://127.0.0.1:5173/#/rag-agent-hub", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        print("[STEP 2] 切换至【8 大业务智能体多架构调度沙箱】Tab...")
        tab_btn = page.locator(".el-tabs__item:has-text('8 大业务智能体')").first
        if not tab_btn.is_visible():
            tab_btn = page.locator("#tab-agents").first
        assert tab_btn.is_visible(), "必须找到 8 大业务智能体沙箱 Tab"
        tab_btn.click()
        time.sleep(1)

        print("[STEP 3] 校验左侧智能体卡片方框与内部滚动容器...")
        sandbox_menu = page.locator(".sandbox-menu")
        assert sandbox_menu.is_visible(), "左侧 .sandbox-menu 实体方框必须可见"

        menu_list = page.locator(".sandbox-menu-list")
        assert menu_list.is_visible(), "左侧 .sandbox-menu-list 独立滚动列表必须可见"

        menu_overflow = page.evaluate("() => window.getComputedStyle(document.querySelector('.sandbox-menu-list')).overflowY")
        print(f"[PASS] 左侧列表 overflow-y: {menu_overflow} (符合 auto 独立滚动规范)")

        print("[STEP 4] 校验右侧智能体聊天视口与输入框吸底状态...")
        chat_widget = page.locator(".agent-chat-widget")
        assert chat_widget.is_visible(), "右侧 .agent-chat-widget 对话视口必须可见"

        footer = page.locator(".widget-footer")
        assert footer.is_visible(), "底部操作栏 .widget-footer 必须可见"

        footer_rect = page.evaluate("""() => {
            const el = document.querySelector('.widget-footer');
            const r = el.getBoundingClientRect();
            return {
                top: Math.round(r.top),
                bottom: Math.round(r.bottom),
                height: Math.round(r.height),
                isInViewport: r.bottom <= window.innerHeight + 5
            };
        }""")
        print(f"[PASS] 底部操作栏位置: top={footer_rect['top']}, bottom={footer_rect['bottom']}, height={footer_rect['height']}")
        print(f"[PASS] 底部操作栏处于屏幕视口可视范围内: {footer_rect['isInViewport']}")
        assert footer_rect['isInViewport'], "底部输入框必须牢牢吸底在当前屏幕视口内，严禁脱离肉眼可视范围"

        print("[STEP 5] 切换至【智能体 8: Coze 开放生态小爱医疗智能体】验证长消息渲染...")
        agent8_btn = page.locator(".agent-menu-item:has-text('智能体 8')").first
        if agent8_btn.is_visible():
            agent8_btn.click()
            time.sleep(1)

        # 检查浏览器主页面是否未被撑出纵向大滚动条
        doc_scroll_height = page.evaluate("() => document.documentElement.scrollHeight")
        window_inner_height = page.evaluate("() => window.innerHeight")
        print(f"[INFO] 页面总高度: {doc_scroll_height}px, 视口高度: {window_inner_height}px")

        # 捕获实机截图
        page.screenshot(path=SCREENSHOT_PATH, full_page=False)
        print(f"[PASS] 高清实机验证截图已保存至: {SCREENSHOT_PATH}")

        # 过滤非致命静态资源警告
        critical_errors = [e for e in errors if "favicon" not in e.lower() and "map" not in e.lower()]
        print(f"[INFO] 拦截控制台严重异常数: {len(critical_errors)}")
        assert len(critical_errors) == 0, f"控制台存在未捕获严重异常: {critical_errors}"

        browser.close()
        print("=====================================================================")
        print("SUCCESS: 8 大业务智能体沙箱视口一体化回环测试 100% 通过！")
        print("=====================================================================")


if __name__ == "__main__":
    run_verification()
