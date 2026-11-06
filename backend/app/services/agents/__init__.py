"""
@file __init__.py
@description 医疗物资全链路 8 大异构业务智能体独立物理服务包
集中导出各个基于真实大模型与 MCP 协议的业务智能体架构类：
- Agent 1: PlanAndExecuteDictAgent (规划执行)
- Agent 2: AdvancedSkillRouter (路由技能)
- Agent 3: LangGraphSecondaryAgent (状态图 + HITL)
- Agent 4: ReActHighValueTraceAgent (ReAct 循环流式推理)
- Agent 5: BlackboardFinanceAuditAgent (中央黑板多专家)
- Agent 6: AgenticRagSupervisorAgent (多子智能体 + Modular RAG)
- Agent 7: FeishuSyncAgent (飞书协同推送与群聊互动 Webhook+OpenAPI 双轨)
- Agent 8: CozeCloudAgent (Coze 开放生态小爱医疗智能体 豆包 1.5 Pro)
- RealLlmClient: 真实大语言模型统一驱动内核
"""

from app.services.agents.llm_client import RealLlmClient
from app.services.agents.agent_1_plan_execute import PlanAndExecuteDictAgent
from app.services.agents.agent_2_router_skill import AdvancedSkillRouter
from app.services.agents.agent_3_langgraph import LangGraphSecondaryAgent
from app.services.agents.agent_4_react import ReActHighValueTraceAgent
from app.services.agents.agent_5_blackboard import BlackboardFinanceAuditAgent
from app.services.agents.agent_6_supervisor import AgenticRagSupervisorAgent
from app.services.agents.agent_7_feishu import FeishuSyncAgent
from app.services.agents.agent_8_coze import CozeCloudAgent

__all__ = [
    "RealLlmClient",
    "PlanAndExecuteDictAgent",
    "AdvancedSkillRouter",
    "LangGraphSecondaryAgent",
    "ReActHighValueTraceAgent",
    "BlackboardFinanceAuditAgent",
    "AgenticRagSupervisorAgent",
    "FeishuSyncAgent",
    "CozeCloudAgent"
]
