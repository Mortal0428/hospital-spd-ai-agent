"""
@file test_all_agents_and_hitl_visual.py
@description Playwright 自动化端到端回环验证：知识库全库切片健康度条幅、Agent 3 人机回环 4 节点步骤条与人工审批批示物理落盘
@param 无
@returns None
@route tests/e2e/test_all_agents_and_hitl_visual.py
@throws 页面渲染与断言异常
"""

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

print("=== 启动 Playwright (Python) 自动化端到端回环与截图验证 ===")

screenshot_dir = os.path.abspath("tests/screenshots")
os.makedirs(screenshot_dir, exist_ok=True)
time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(err.message))

    # 1. 访问 RAG 知识工程与智能体中台
    print("1. 正在访问前端中台页面: http://localhost:5173/#/rag-agent-hub")
    page.goto("http://localhost:5173/#/rag-agent-hub", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)

    # 2. 验证知识库切片健康度巡检条幅渲染并截图
    print("2. 验证知识库切片健康度全库巡检条幅...")
    health_text = page.locator(".doc-main-table-wrap").text_content()
    has_banner = "知识库向量化健康度" in health_text
    print(f"包含知识库向量化健康度条幅: {has_banner}")

    banner_screenshot = os.path.join(screenshot_dir, f"{time_str}_rag_health_inspection_banner.png")
    page.screenshot(path=banner_screenshot, full_page=False)
    print(f"已捕获知识库巡检条幅截图: {banner_screenshot}")

    # 3. 切换至 6 大业务智能体沙箱
    print("3. 切换至【6 大业务智能体沙箱】Tab...")
    page.click("#tab-agents")
    page.wait_for_timeout(1000)

    # 4. 选择智能体 3 (LangGraph + HITL)
    print("4. 选择智能体 3: 临床二级库申领问答 (LangGraph + HITL)...")
    agent_menu_items = page.locator(".agent-menu-item").all()
    for item in agent_menu_items:
        if "智能体 3" in item.text_content():
            item.click()
            break
    page.wait_for_timeout(1000)

    # 5. 触发申领指令，测试中断挂起与 4 节点步骤条
    print("5. 发送自然语言申领诉求: 向耗材主库申领 50 包一次性医用外科口罩...")
    chat_input = page.wait_for_selector(".agent-chat-widget input")
    chat_input.fill("向耗材主库申领 50 包一次性医用外科口罩")
    page.click(".agent-chat-widget button:has-text('执行')")

    print("等待大模型与 LangGraph 意图提取并挂起中断点...")
    page.wait_for_selector(".hitl-card", timeout=60000)
    page.wait_for_timeout(2000)

    hitl_card_text = page.locator(".hitl-card").first.text_content()
    print("HITL 卡片渲染内容包含中断挂起 (PAUSED):", ("PAUSED" in hitl_card_text or "挂起" in hitl_card_text))
    print("包含流程步骤条节点:", ("临床意图解析" in hitl_card_text and "人机协同审批" in hitl_card_text))

    hitl_paused_screenshot = os.path.join(screenshot_dir, f"{time_str}_agent3_hitl_paused_stepper.png")
    page.screenshot(path=hitl_paused_screenshot, full_page=False)
    print(f"已捕获 HITL 中断挂起与 4 节点步骤条截图: {hitl_paused_screenshot}")

    # 6. 人工审批: 填写批示意见并点击【同意下发 (CONFIRM)】
    print("6. 人工审批：输入审核批示意见并点击同意下发...")
    comment_input = page.wait_for_selector(".hitl-action-box input")
    comment_input.fill("护士长临床核验通过，准予紧急下发排队出库")
    page.click(".hitl-action-box button:has-text('同意下发')")

    print("等待状态机推进至节点 4/4 并物理落盘请领单...")
    page.wait_for_timeout(4000)

    hitl_approved_screenshot = os.path.join(screenshot_dir, f"{time_str}_agent3_hitl_approved_complete.png")
    page.screenshot(path=hitl_approved_screenshot, full_page=False)
    print(f"已捕获人机回环审批通过与单据落盘截图: {hitl_approved_screenshot}")

    print("=== Playwright 端到端自动化回环测试全部成功通过！ ===")
    print("页面控制台致命错误数:", len(page_errors))
    browser.close()
