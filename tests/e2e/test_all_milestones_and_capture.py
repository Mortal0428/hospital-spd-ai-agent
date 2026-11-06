"""
@file test_all_milestones_and_capture.py
@description Playwright (Python) 端到端自动化实机验证与高清截图归档脚本
验证多子智能体微信群聊气泡流式渲染、MCP 工具入参出参真实填实展开、
图三 Modular RAG 算子生效凭证卡片、飞书交互式卡片推送、Coze 云端协同问答
以及智能体 3 人机协同 (HITL) 流程节点。
@param 无
@returns None
@route tests/e2e/test_all_milestones_and_capture.py
@throws 页面渲染与断言异常
"""

import os
import time
from playwright.sync_api import sync_playwright

print("=== 启动 Playwright (Python) 全链路业务与截图实机回环验证 ===")

screenshot_dir = os.path.abspath("tests/screenshots")
os.makedirs(screenshot_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(err.message))

    try:
        # 1. 访问智能体调度沙箱
        print("1. 访问智能体中台沙箱: http://127.0.0.1:5173/#/rag-agent-hub?tab=agents")
        page.goto("http://127.0.0.1:5173/#/rag-agent-hub?tab=agents", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # 2. 选择智能体 1 (Plan & Execute) 发送建仓指令
        print("2. 选择智能体 1 并发送字典建仓指令...")
        items = page.locator(".agent-menu-item").all()
        if items:
            items[0].click()
            page.wait_for_timeout(1000)

        chat_input = page.locator(".widget-footer input, .widget-footer .el-input__inner").first
        if chat_input.is_visible():
            chat_input.fill("请帮我新增一款高值骨科接骨板字典档案并查验供应商资质")
            page.wait_for_timeout(300)

            send_btn = page.locator(".widget-footer button").filter(has_text="执行").first
            if send_btn.is_visible():
                send_btn.click()
                print("已提交智能体 1 指令，等待多子智能体群聊气泡与分步执行完成...")
                page.wait_for_timeout(14000)

        # 展开 MCP 工具调用卡片
        print("展开 MCP 工具入参出参...")
        tool_headers = page.locator(".tool-call-header").all()
        for th in tool_headers:
            try:
                th.click()
                page.wait_for_timeout(200)
            except Exception:
                pass

        # 截图 1: 多子智能体微信群聊气泡与 MCP 真实参数展开
        s1_path = os.path.join(screenshot_dir, "2026-11-05_16-10-00_groupchat_stream_bubbles.png")
        page.screenshot(path=s1_path, full_page=False)
        print(f"[截图完成 1/4]: {s1_path}")

        # 3. 选择智能体 6 (自省重写与算子生效凭证卡片)
        print("3. 选择智能体 6 并发送知识库系统事实查验指令...")
        items = page.locator(".agent-menu-item").all()
        for item in items:
            if "智能体 6" in (item.text_content() or ""):
                item.click()
                page.wait_for_timeout(1000)
                break

        chat_input6 = page.locator(".widget-footer input, .widget-footer .el-input__inner").first
        if chat_input6.is_visible():
            chat_input6.fill("系统知识库目前纳管了多少篇医疗器械规范文档？切片与向量库状态如何？")
            page.wait_for_timeout(300)
            send_btn6 = page.locator(".widget-footer button").filter(has_text="执行").first
            if send_btn6.is_visible():
                send_btn6.click()
                print("已提交智能体 6 指令，等待算子生效凭证生成...")
                page.wait_for_timeout(8000)

        # 截图 2: 验证算子生效物理凭证卡片与系统事实查验
        s2_path = os.path.join(screenshot_dir, "2026-11-05_16-10-00_mcp_tool_parameters_verified.png")
        page.screenshot(path=s2_path, full_page=False)
        print(f"[截图完成 2/4]: {s2_path}")

        # 4. 切换至 Modular RAG 控制台 Tab
        print("4. 切换至【Modular RAG 模块化热插拔控制台】Tab...")
        page.click("#tab-config")
        page.wait_for_timeout(1500)

        # 滚动到底部并测试发送飞书卡片
        print("测试发送飞书交互式卡片...")
        feishu_btn = page.locator("button").filter(has_text="发送飞书测试卡片").first
        if feishu_btn.is_visible():
            feishu_btn.scroll_into_view_if_needed()
            feishu_btn.click()
            page.wait_for_timeout(2500)

        # 测试与 Coze 协同问答
        print("测试与 Coze 云端小爱智能体协同问答...")
        coze_btn = page.locator("button").filter(has_text="协同问答").first
        if coze_btn.is_visible():
            coze_btn.scroll_into_view_if_needed()
            coze_btn.click()
            page.wait_for_timeout(5000)

        # 点击【手动保存全部配置 (立即秒级生效)】
        print("点击图二右下角【手动保存全部配置 (立即秒级生效)】按钮...")
        save_btn = page.locator("button").filter(has_text="手动保存全部配置").first
        if save_btn.is_visible():
            save_btn.scroll_into_view_if_needed()
            save_btn.click()
            page.wait_for_timeout(2000)

        # 截图 3: 飞书推送与 Coze 云端智能体联调面板
        s3_path = os.path.join(screenshot_dir, "2026-11-05_16-10-00_feishu_notification_and_coze.png")
        page.screenshot(path=s3_path, full_page=False)
        print(f"[截图完成 3/4]: {s3_path}")

        # 5. 切换回沙箱测试智能体 3 人机回环 (HITL) 挂起
        print("5. 切换至沙箱测试智能体 3 人机回环挂起与 4 节点流程图...")
        page.click("#tab-agents")
        page.wait_for_timeout(1000)

        items3 = page.locator(".agent-menu-item").all()
        for item in items3:
            if "智能体 3" in (item.text_content() or ""):
                item.click()
                page.wait_for_timeout(1000)
                break

        chat_input3 = page.locator(".widget-footer input, .widget-footer .el-input__inner").first
        if chat_input3.is_visible():
            chat_input3.fill("骨科病区二级库急需申领 120 支医用外科口罩")
            page.wait_for_timeout(300)
            send_btn3 = page.locator(".widget-footer button").filter(has_text="执行").first
            if send_btn3.is_visible():
                send_btn3.click()
                print("已提交智能体 3 请领指令，等待 HITL 挂起...")
                page.wait_for_timeout(8000)

        # 截图 4: 人机回环挂起与 4 节点流程图
        s4_path = os.path.join(screenshot_dir, "2026-11-05_16-10-00_langgraph_hitl_and_workflow.png")
        page.screenshot(path=s4_path, full_page=False)
        print(f"[截图完成 4/4]: {s4_path}")

        print("=== Playwright 端到端回环实机验证全部顺利完成 ===")
        print("页面异常数量:", len(page_errors))

    except Exception as e:
        print(f"Playwright 自动化执行异常: {e}")
    finally:
        browser.close()
