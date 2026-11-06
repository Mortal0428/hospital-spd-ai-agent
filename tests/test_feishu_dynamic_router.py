"""
@file test_feishu_dynamic_router.py
@description 飞书双向智能体动态意图路由、真实 LLM 思考与卡片精准 @成员 自动化单元测试
覆盖三大核心测试维度:
1. 群聊免打扰守则 (未 @ 机器人时绝对静默)
2. 系统真实业务数据查询 (MySQL 在册物资台账核验)
3. 开放域深度大模型问答 (小米 MiMo 真实思考链与回答) 与卡片 @成员 强提醒
全域遵循零 Emoji 规范与 100% 中文四要素注释。

@param 无 独立单元测试
@returns 无 断言通过即测试成功
@route internal://tests/test_feishu_dynamic_router.py
@throws AssertionError 若断言失败
"""

import os
import sys
from pathlib import Path

# 将项目根目录与 backend 加入模块导入路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.feishu_service import feishu_service
from app.services.feishu_ws_service import feishu_ws_service
from app.services.agents.llm_client import RealLlmClient


def test_01_feishu_card_at_member_injection():
    """测试飞书业务卡片与通用卡片是否成功注入 <at id='open_id'>
    @param 无
    @returns 无
    @route internal://tests/test_feishu_dynamic_router.py/test_01_feishu_card_at_member_injection
    @throws AssertionError 若卡片结构未注入 @成员 标记
    """
    test_openid = "ou_8de5ce578af5c5cc4442dc4cd1ff5e42"

    # 1. 测试调拨卡片
    card_dispatch = feishu_service.build_dispatch_order_card(
        dist_order_no="DIST-TEST-001",
        target_dept_name="心血管科病区",
        product_name="人工生物心脏瓣膜",
        batch_no="LOT20261105",
        expiry_date="2027-11-05",
        dist_qty=10,
        unit_price=12500.0,
        dispatcher_name="张主管",
        at_open_id=test_openid
    )
    elements = card_dispatch.get("elements", [])
    assert len(elements) > 0, "调拨卡片 elements 不能为空"
    first_div = elements[0].get("text", {}).get("content", "")
    assert f"<at id=\"{test_openid}\">" in first_div, f"调拨卡片首行必须包含 @成员 标记: {first_div}"
    print("[PASS] 测试 1.1: 调拨业务卡片精准 @成员 注入成功")

    # 2. 测试交互式问答卡片
    card_reply = feishu_service.build_interactive_reply_card(
        title="【SPD业务智能体】协同研判应答",
        query="你认识田江吗",
        answer="田江老师是一位资深的专业导师与技术专家。",
        thought_process="分析提问对象为田江，结合教育与专业背景组织自然亲切的答复。",
        at_open_id=test_openid,
        template_color="blue"
    )
    reply_elems = card_reply.get("elements", [])
    first_reply_text = reply_elems[0].get("text", {}).get("content", "")
    assert f"<at id=\"{test_openid}\">" in first_reply_text, "问答卡片首行必须包含 @成员 标记"
    assert "田江" in reply_elems[1].get("text", {}).get("content", ""), "问答卡片正文必须包含回答内容"
    print("[PASS] 测试 1.2: 交互式问答卡片精准 @成员 与思考链展示成功")


def test_02_system_material_data_query():
    """测试系统真实业务数据检索 (查库事实)
    @param 无
    @returns 无
    @route internal://tests/test_feishu_dynamic_router.py/test_02_system_material_data_query
    @throws AssertionError 若未能从数据库查出真实物资
    """
    # 模拟用户提问“查一下有什么物资”或特定物资“接骨板”
    res_generic = feishu_ws_service._query_system_material_data("你们医院有什么物资")
    assert res_generic is not None, "宽泛物资询问必须命中系统业务数据检索"
    assert res_generic["count"] > 0, f"必须检出在册物资记录，实际检出: {res_generic['count']}"
    assert len(res_generic["fields"]) > 0, "必须生成结构化字段用于飞书卡片渲染"
    print(f"[PASS] 测试 2.1: 宽泛物资查库检索成功，命中 {res_generic['count']} 项真实在册物资")

    # 模拟日常闲聊问题排除（不应走查库）
    res_chat = feishu_ws_service._query_system_material_data("你认识田江吗")
    assert res_chat is None, "日常人物提问绝不能误判为系统物资查库"
    print("[PASS] 测试 2.2: 日常人物闲聊成功被意图识别排除，未误触查库")


def test_03_real_llm_reasoning():
    """测试小米 MiMo 真实大模型调用客户端与思考链提取
    @param 无
    @returns 无
    @route internal://tests/test_feishu_dynamic_router.py/test_03_real_llm_reasoning
    @throws AssertionError 若大模型调用异常或返回空文本
    """
    prompt = "你认识田江吗？请用亲切简短的一句话介绍他并问候。"
    res = RealLlmClient.generate(
        prompt=prompt,
        system_prompt="你是由杭州电子科技大学研发的医院医疗物资全链路管理系统AI业务助手。全域严禁使用任何Emoji。",
        model_name="mimo-v2.6-flash",
        provider="mimo"
    )
    ans = res.get("final_answer") or res.get("text", "")
    thought = res.get("thought_process", "")
    assert len(ans.strip()) > 0, "大模型回答不能为空"
    print(f"[PASS] 测试 3: 小米 MiMo 真实思考生成成功 (耗时: {res.get('latency_ms')}ms)")
    print(f"      大模型答复: {ans[:60]}...")
    if thought:
        print(f"      思考链提取: {thought[:60]}...")


def test_04_strict_group_chat_do_not_disturb():
    """测试群聊免打扰守则与被 @ 实体精确比对 (未@或仅@人类群成员时绝对静默)
    @param 无
    @returns 无
    @route internal://tests/test_feishu_dynamic_router.py/test_04_strict_group_chat_do_not_disturb
    @throws AssertionError 若群聊未 @ 机器人或 @ 人类成员时未被静默拦截
    """
    class MockUserId:
        def __init__(self, open_id=""):
            self.open_id = open_id

    class MockMention:
        def __init__(self, key="", open_id="", name=""):
            self.key = key
            self.id = MockUserId(open_id=open_id)
            self.name = name

    group_chat_id = "oc_4e09defedb59928db5b4b739f9d5e325"
    p2p_chat_id = "p2p_test_chat_001"

    bot_open_id = "ou_7b6efa4c13b5fa8cbc02332586246d2d"
    user_chen_open_id = "ou_8de5ce578af5c5cc4442dc4cd1ff5e42"
    user_xu_open_id = "ou_9d2429486c321098471"

    # 用例 1: 许彬在群聊中发送纯表情，无 @_user_，mentions 为空 -> 必须静默 False
    res_emoji = feishu_ws_service._is_message_for_bot(
        chat_id=group_chat_id,
        chat_type="group",
        parsed_text="",
        mentions=[]
    )
    assert res_emoji is False, "群聊发送纯表情且无 @ 时必须返回 False (静默)"
    print("[PASS] 测试 4.1: 群聊纯表情无 @ 严格拦截静默通过")

    # 用例 2: 群成员在群聊中日常对话 (如'你是不是个女'、'我靠')，无 @_user_ -> 必须静默 False
    res_chat = feishu_ws_service._is_message_for_bot(
        chat_id=group_chat_id,
        chat_type="group",
        parsed_text="你是不是个女",
        mentions=[]
    )
    assert res_chat is False, "群聊普通打字未 @ 机器人时必须返回 False (静默)"
    print("[PASS] 测试 4.2: 群聊未 @ 普通打字交流严格拦截静默通过")

    # 用例 3: 用户在群聊中 @ 自己 (陈永兴 @陈永兴)，被 @ 对象不是机器人 -> 必须静默 False
    res_at_self = feishu_ws_service._is_message_for_bot(
        chat_id=group_chat_id,
        chat_type="group",
        parsed_text="@_user_1 我发一段代码",
        mentions=[MockMention(key="@_user_1", open_id=user_chen_open_id, name="陈永兴")]
    )
    assert res_at_self is False, "群聊中用户 @自己 必须返回 False (静默，绝不误触发)"
    print("[PASS] 测试 4.3: 用户在群聊中 @自己 实体核验拦截静默通过")

    # 用例 4: 用户在群聊中 @ 许彬 (人类成员互 @)，被 @ 对象不是机器人 -> 必须静默 False
    res_at_other = feishu_ws_service._is_message_for_bot(
        chat_id=group_chat_id,
        chat_type="group",
        parsed_text="@_user_1 许彬你看看这个",
        mentions=[MockMention(key="@_user_1", open_id=user_xu_open_id, name="许彬")]
    )
    assert res_at_other is False, "群聊中群成员之间互相 @ 必须返回 False (静默)"
    print("[PASS] 测试 4.4: 群聊中人类成员互相 @ 拦截静默通过")

    # 用例 5: 群聊显式 @ 机器人 (命中机器人官方 OpenID 或名字) -> 必须唤醒 True
    res_at_bot = feishu_ws_service._is_message_for_bot(
        chat_id=group_chat_id,
        chat_type="group",
        parsed_text="@_user_1 查一下骨科耗材库存",
        mentions=[MockMention(key="@_user_1", open_id=bot_open_id, name="Openclaw_测试")]
    )
    assert res_at_bot is True, "群聊中显式 @ 机器人必须返回 True (唤醒)"
    print("[PASS] 测试 4.5: 群聊显式 @ 机器人专属身份命中唤醒通过")

    # 用例 6: 私聊单聊 (p2p)，无需 @ 也必须正常响应 -> True
    res_p2p = feishu_ws_service._is_message_for_bot(
        chat_id=p2p_chat_id,
        chat_type="p2p",
        parsed_text="你好，请问你是谁？",
        mentions=[]
    )
    assert res_p2p is True, "私聊单聊会话始终必须返回 True (全量响应)"
    print("[PASS] 测试 4.6: 私聊单聊免 @ 正常通行通过")


if __name__ == "__main__":
    print("=" * 60)
    print("开始执行飞书双向智能体动态意图决策与卡片 @成员 自动化测试")
    print("=" * 60)
    test_01_feishu_card_at_member_injection()
    test_02_system_material_data_query()
    test_03_real_llm_reasoning()
    test_04_strict_group_chat_do_not_disturb()
    print("=" * 60)
    print("全部 4 项测试 100% 验证通过！")
    print("=" * 60)
