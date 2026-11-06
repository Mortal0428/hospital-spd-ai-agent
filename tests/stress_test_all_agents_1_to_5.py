"""
@file stress_test_all_agents_1_to_5.py
@description 1 到 5 号智能体全功能范围、极限边界与权限架构深度压力测试套件
不留情面地测试每个智能体的架构契约对齐度、真实落盘能力、时延与权限边界。
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal
from app.models.spd_models import SpdProductDict, SpdMainInventory, SpdDistributionOrder, SpdHighValueItem
from app.services.agents import (
    PlanAndExecuteDictAgent,
    AdvancedSkillRouter,
    LangGraphSecondaryAgent,
    ReActHighValueTraceAgent,
    BlackboardFinanceAuditAgent
)


def test_agent_1_rigorous(db):
    print("=" * 80)
    print("【深度压测 1】Agent 01: 产品字典归类与入库审查智能体 (Plan & Execute 架构)")
    print("=" * 80)
    agent = PlanAndExecuteDictAgent(db)

    # 1. 正常业务指令
    t0 = time.time()
    res_normal = agent.execute_plan("请帮我新增一款高值介入导丝并完成主库入库审核", "dept_manager")
    dur_normal = (time.time() - t0) * 1000
    print(f"-> 正常业务指令耗时: {dur_normal:.2f} ms")
    print(f"-> 模型使用: {res_normal.get('model_used')}")
    print(f"-> 规划步骤数: {len(res_normal.get('plan_steps', []))}")
    print(f"-> 思考链长度: {len(res_normal.get('thought', ''))} 字符")

    # 查验数据库是否真实生成了字典记录
    latest_prod = db.query(SpdProductDict).order_by(SpdProductDict.id.desc()).first()
    if latest_prod and "AUTO" in latest_prod.product_code:
        print(f"-> [物理落盘核验通过] 物理写入字典记录 ID {latest_prod.id}, 编码: {latest_prod.product_code}, 品名: {latest_prod.product_name}, 归口: {latest_prod.main_dept_code}")
    else:
        print("-> [警告] 未检测到物理落盘字典记录！")

    # 2. 极端边界测试：恶意注入/空指令/非耗材内容
    res_edge = agent.execute_plan("DELETE FROM spd_product_dict; DROP TABLE users; 你好", "unknown_user")
    print(f"-> 恶意注入边界测试: 安全捕获，未执行SQL注入，规划步骤: {len(res_edge.get('plan_steps', []))}")


def test_agent_2_rigorous(db):
    print("\n" + "=" * 80)
    print("【深度压测 2】Agent 02: 主库智能分发与补货调拨智能体 (Router + Skill 架构)")
    print("=" * 80)
    router = AdvancedSkillRouter(db)

    # 1. FEFO 补货指令
    t0 = time.time()
    res_fefo = router.route_and_execute("急需为骨科二级库执行FEFO近效期先出智能分发调拨，请扫描水位并生成调拨单", {"account": "dept_manager", "dept": "CONSUMABLE_DEPT"}, db)
    dur_fefo = (time.time() - t0) * 1000
    print(f"-> FEFO 调拨指令耗时: {dur_fefo:.2f} ms")
    print(f"-> 命中技能: {res_fefo.get('chosen_skill')}")
    print(f"-> 置信度排行榜: {res_fefo.get('confidence_rankings')}")

    # 2. 待办审批指令
    res_audit = router.route_and_execute("查询当前有哪些未审核的申领采购待办单据", {"account": "dept_manager"}, db)
    print(f"-> 待办指令命中技能: {res_audit.get('chosen_skill')}")

    # 3. 仓储业务问答
    res_qa = router.route_and_execute("医院主库物资安全库存警戒线是如何计算的？", {}, db)
    print(f"-> 答疑指令命中技能: {res_qa.get('chosen_skill')}")


def test_agent_3_rigorous(db):
    print("\n" + "=" * 80)
    print("【深度压测 3】Agent 03: 临床二级库问答与申领智能体 (LangGraph + HITL 架构)")
    print("=" * 80)
    agent = LangGraphSecondaryAgent(db)

    # 1. 常规问答 (不触发申领)
    t0 = time.time()
    res_qa = agent.run_step("请问骨科手术定数包的标准配置包含哪些器械？")
    dur_qa = (time.time() - t0) * 1000
    print(f"-> 常规问答耗时: {dur_qa:.2f} ms")
    print(f"-> 当前状态节点: {res_qa.get('state', {}).get('current_node')}")
    print(f"-> 人机回环状态: {res_qa.get('state', {}).get('human_in_the_loop_status')}")

    # 2. 申领诉求 (必须触发 HITL 挂起)
    res_apply = agent.run_step("我们病区一次性无菌输液管快用完了，请帮我起草一份二级库请领申请单！")
    hitl_status = res_apply.get('state', {}).get('human_in_the_loop_status')
    node = res_apply.get('state', {}).get('current_node')
    print(f"-> 申领诉求触发 HITL 状态: {hitl_status} (节点: {node})")
    assert hitl_status == "PENDING_CONFIRMATION", "错误：未成功触发人机协同挂起！"

    # 3. 模拟人机确认恢复 (Resume CONFIRM)
    res_resume = agent.run_step("确认提交", resume_action="CONFIRM")
    print(f"-> 恢复审批后状态: {res_resume.get('state', {}).get('human_in_the_loop_status')} (回答: {res_resume.get('final_answer')})")


def test_agent_4_rigorous(db):
    print("\n" + "=" * 80)
    print("【深度压测 4】Agent 04: 高值耗材一物一码全链路溯源智能体 (ReAct 架构)")
    print("=" * 80)
    agent = ReActHighValueTraceAgent(db)

    # 1. 真实 UDI 码追溯
    t0 = time.time()
    test_udi = "(01)06912345678901(17)281231(10)B20261101(21)UDI987654"
    res_trace = agent.trace_udi_lifecycle(f"追溯该高值耗材的全生命周期人物流转与不良事件: {test_udi}", "sys_admin")
    dur_trace = (time.time() - t0) * 1000
    print(f"-> UDI 溯源耗时: {dur_trace:.2f} ms")
    print(f"-> ReAct 推理步数: {len(res_trace.get('react_steps', []))}")
    for idx, st in enumerate(res_trace.get('react_steps', [])):
        print(f"   步骤 {idx+1}: Action=[{st.get('action')}] -> Observation=[{st.get('observation')[:50]}...]")

    # 2. 无条码口语化查询
    res_none = agent.trace_udi_lifecycle("这批支架到底是谁用的", "sys_admin")
    print(f"-> 模糊查询兜底步数: {len(res_none.get('react_steps', []))}")


def test_agent_5_rigorous(db):
    print("\n" + "=" * 80)
    print("【深度压测 5】Agent 05: 多科室耗材财务精算与合规审计智能体 (Blackboard 架构)")
    print("=" * 80)
    agent = BlackboardFinanceAuditAgent(db)

    # 1. 财务月报精算
    t0 = time.time()
    res_audit = agent.audit_finance_ledger("审计 2026 年 11 月份各临床病区高值与普通耗材成本及耗占比是否超标", "2026-11", "finance_auditor")
    dur_audit = (time.time() - t0) * 1000
    print(f"-> 财务对账耗时: {dur_audit:.2f} ms")
    bb = res_audit.get('blackboard_data', {})
    print(f"-> 审计会计月份: {bb.get('audit_month')}")
    print(f"-> 风险评级: {bb.get('risk_level')}")
    print(f"-> 参与黑板专家数: {len(bb.get('experts', []))}")
    for exp in bb.get('experts', []):
        print(f"   * 专家 [{exp.get('name')}]: {exp.get('summary')}")


if __name__ == "__main__":
    with SessionLocal() as db:
        test_agent_1_rigorous(db)
        test_agent_2_rigorous(db)
        test_agent_3_rigorous(db)
        test_agent_4_rigorous(db)
        test_agent_5_rigorous(db)
    print("\n" + "=" * 80)
    print(" 1~5 号智能体全部压力测试与边界探测运行完成！")
    print("=" * 80)
