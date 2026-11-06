"""
@file __init__.py
@description MCP 独立工具注册中心统一对外导出与执行调度网关
提供工具自省、Pydantic V2 参数强校验与统一执行派发，
彻底消除智能体调用入参为空字典 {} 的假执行现象，
支持由 FastAPI 依赖注入或独立脚本通过 SessionLocal 调度。

@param name: str 工具唯一标识
@param arguments: Dict[str, Any] 工具调用入参字典
@param db: Optional[Session] 数据库会话
@returns ToolResult 统一封装结果
@route internal://backend/app/services/mcp_tools
@throws 统一捕获参数校验异常与数据库异常并安全包裹至 ToolResult
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.mcp_tools.schema import BaseToolInput, ToolResult

# 导入各类原子工具函数与 Schema
from app.services.mcp_tools.dict_tools import (
    CheckSupplierCertInput,
    CreateProductDictInput,
    QueryProductDictInput,
    mcp_check_supplier_cert,
    mcp_create_product_dict,
    mcp_query_product_dict
)
from app.services.mcp_tools.dispatch_tools import (
    CreateDispatchOrderInput,
    QueryPendingRequisitionsInput,
    ScanStockInput,
    mcp_create_dispatch_order,
    mcp_query_pending_requisitions,
    mcp_scan_main_and_sec_stock
)
from app.services.mcp_tools.requisition_tools import (
    CheckMainAvailableInput,
    QuerySurgeryPackSpecsInput,
    SubmitRequisitionInput,
    mcp_check_main_available,
    mcp_query_surgery_pack_specs,
    mcp_submit_sec_requisition
)
from app.services.mcp_tools.high_value_tools import (
    FreezeProblemBatchInput,
    TraceUdiInput,
    mcp_freeze_problem_batch,
    mcp_trace_udi_full_logs
)
from app.services.mcp_tools.finance_tools import (
    AggregateDeptCostInput,
    ScanAbnormalLogsInput,
    mcp_aggregate_dept_cost,
    mcp_scan_abnormal_flow_logs
)
from app.services.mcp_tools.rag_tools import (
    ChromaRetrievalInput,
    QueryKnowledgeStatsInput,
    WriteGraphTriplesInput,
    mcp_chroma_global_retrieval,
    mcp_query_knowledge_stats,
    mcp_write_knowledge_graph_triples
)
from app.services.mcp_tools.feishu_tools import (
    FeishuPushCardInput,
    FeishuCheckStatusInput,
    mcp_feishu_push_card,
    mcp_feishu_check_status
)

logger = logging.getLogger("spd.mcp_tools.registry")

# 全局工具注册表
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_tool(
    name: str,
    schema_cls: Type[BaseToolInput],
    func: Callable,
    description: str,
    category: str
) -> None:
    """向全局 MCP 工具注册中心登记工具

    @param name: str 工具唯一调用标识
    @param schema_cls: Type[BaseToolInput] Pydantic V2 强类型参数模型
    @param func: Callable 核心执行函数
    @param description: str 工具功能中文说明
    @param category: str 工具所属大类
    @returns None 内部全局注册表更新，无返回值
    @route internal://backend/app/services/mcp_tools/register_tool
    @throws 无
    """
    _TOOL_REGISTRY[name] = {
        "name": name,
        "schema": schema_cls,
        "func": func,
        "description": description,
        "category": category
    }


# =========================================================================
# 注册全员 15 项标准 MCP 工具
# =========================================================================
# 1. 字典审查与建档 (Agent 01)
register_tool(
    name="mcp_query_product_dict",
    schema_cls=QueryProductDictInput,
    func=mcp_query_product_dict,
    description="医疗物资产品字典多维条件组合检索",
    category="DICT"
)
register_tool(
    name="mcp_check_supplier_cert",
    schema_cls=CheckSupplierCertInput,
    func=mcp_check_supplier_cert,
    description="供应商经营资质与医疗器械注册证合规查验",
    category="DICT"
)
register_tool(
    name="mcp_create_product_dict",
    schema_cls=CreateProductDictInput,
    func=mcp_create_product_dict,
    description="在产品字典中建立新物资档案并联动记录 6W 审计日志",
    category="DICT"
)

# 2. 按需分发与库存扫描 (Agent 02)
register_tool(
    name="mcp_scan_main_and_sec_stock",
    schema_cls=ScanStockInput,
    func=mcp_scan_main_and_sec_stock,
    description="穿透扫描主库批次库存(FEFO排序)与临床二级库库存水位",
    category="DISPATCH"
)
register_tool(
    name="mcp_create_dispatch_order",
    schema_cls=CreateDispatchOrderInput,
    func=mcp_create_dispatch_order,
    description="主库按需创建分发调拨单，物理核减库存并联动 6W 日志",
    category="DISPATCH"
)
register_tool(
    name="mcp_query_pending_requisitions",
    schema_cls=QueryPendingRequisitionsInput,
    func=mcp_query_pending_requisitions,
    description="查询临床二级库发起的待主库审批申领单清单",
    category="DISPATCH"
)

# 3. 临床申领与定数包 (Agent 03)
register_tool(
    name="mcp_check_main_available",
    schema_cls=CheckMainAvailableInput,
    func=mcp_check_main_available,
    description="申领前核验主库可用总余量与 FEFO 优先批次",
    category="REQUISITION"
)
register_tool(
    name="mcp_submit_sec_requisition",
    schema_cls=SubmitRequisitionInput,
    func=mcp_submit_sec_requisition,
    description="临床二级库发起自然语言申领单，落盘并联动 6W 日志",
    category="REQUISITION"
)
register_tool(
    name="mcp_query_surgery_pack_specs",
    schema_cls=QuerySurgeryPackSpecsInput,
    func=mcp_query_surgery_pack_specs,
    description="查询临床手术定数包标准规范与主库物资库存匹配度",
    category="REQUISITION"
)

# 4. 高值溯源与紧急冻结 (Agent 04)
register_tool(
    name="mcp_trace_udi_full_logs",
    schema_cls=TraceUdiInput,
    func=mcp_trace_udi_full_logs,
    description="输入 UDI 码或批号，穿透还原高值耗材流转链与 6W 人物时间轴",
    category="HIGH_VALUE"
)
register_tool(
    name="mcp_freeze_problem_batch",
    schema_cls=FreezeProblemBatchInput,
    func=mcp_freeze_problem_batch,
    description="质量抽检不合格或不良事件时，对高值单品或批次库存执行物理冻结并留痕",
    category="HIGH_VALUE"
)

# 5. 财务精算与 6W 审计 (Agent 05)
register_tool(
    name="mcp_aggregate_dept_cost",
    schema_cls=AggregateDeptCostInput,
    func=mcp_aggregate_dept_cost,
    description="聚合统计临床各二级库普通与高值耗材消耗金额与耗占比",
    category="FINANCE"
)
register_tool(
    name="mcp_scan_abnormal_flow_logs",
    schema_cls=ScanAbnormalLogsInput,
    func=mcp_scan_abnormal_flow_logs,
    description="穿透扫描 6W 业务日志排查异常流转、逆向退库与风控标记",
    category="FINANCE"
)

# 6. Chroma 全局检索与知识工程 (Agent 06)
register_tool(
    name="mcp_chroma_global_retrieval",
    schema_cls=ChromaRetrievalInput,
    func=mcp_chroma_global_retrieval,
    description="基于本地 ChromaDB HNSW 索引执行全库全局稠密向量检索(废除 limit(10))",
    category="RAG"
)
# 别名注册，确保兼容性
register_tool(
    name="mcp_chroma_hnsw_search",
    schema_cls=ChromaRetrievalInput,
    func=mcp_chroma_global_retrieval,
    description="ChromaDB HNSW 全局稠密向量检索(别名)",
    category="RAG"
)
register_tool(
    name="mcp_write_knowledge_graph_triples",
    schema_cls=WriteGraphTriplesInput,
    func=mcp_write_knowledge_graph_triples,
    description="将文档清洗抽取的实体关系三元组结构化持久化至图谱元数据",
    category="RAG"
)
register_tool(
    name="mcp_query_knowledge_stats",
    schema_cls=QueryKnowledgeStatsInput,
    func=mcp_query_knowledge_stats,
    description="查询知识工程整体资产概况(文档、切片、实体数与 Chroma 就绪状态)",
    category="RAG"
)

# 7. 飞书开放平台与群机器人协同推送 (Agent 07)
register_tool(
    name="mcp_feishu_push_card",
    schema_cls=FeishuPushCardInput,
    func=mcp_feishu_push_card,
    description="向飞书群机器人 Webhook 或企业自建应用精准推送标准医疗交互式卡片",
    category="FEISHU"
)
register_tool(
    name="mcp_feishu_check_status",
    schema_cls=FeishuCheckStatusInput,
    func=mcp_feishu_check_status,
    description="探测飞书开放平台鉴权与群机器人通道健康状态",
    category="FEISHU"
)

# 8. 外部解耦式 MCP 协议扩展工具 (免 Key 联网医学知识检索与高精度效期推算)
from app.services.mcp_external.schema import ExternalSearchInput, FefoCalcInput
from app.services.mcp_external.search_tools import mcp_external_medical_search
from app.services.mcp_external.datetime_calc_tools import mcp_datetime_and_fefo_calc

register_tool(
    name="mcp_external_medical_search",
    schema_cls=ExternalSearchInput,
    func=mcp_external_medical_search,
    description="免 API Key 外部医学知识与国家药监局标准联网检索(NMPA/GB/YY)",
    category="EXTERNAL_MCP"
)
register_tool(
    name="mcp_datetime_and_fefo_calc",
    schema_cls=FefoCalcInput,
    func=mcp_datetime_and_fefo_calc,
    description="医疗耗材灭菌保质期、效期倒计时与近效期先出(FEFO)精确推算",
    category="EXTERNAL_MCP"
)



def list_mcp_tools() -> List[Dict[str, Any]]:
    """获取系统已注册的全部 MCP 工具清单及参数 Schema

    @param 无 该函数无入参
    @returns List[Dict[str, Any]] 工具元数据列表
    @route internal://backend/app/services/mcp_tools/list_mcp_tools
    @throws 无
    """
    tools = []
    for name, item in _TOOL_REGISTRY.items():
        schema_cls = item["schema"]
        schema_json = {}
        if hasattr(schema_cls, "model_json_schema"):
            schema_json = schema_cls.model_json_schema()

        tools.append({
            "name": name,
            "description": item["description"],
            "category": item["category"],
            "parameters": schema_json
        })
    return tools


def get_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    """根据名称查找已注册的 MCP 工具

    @param tool_name: str 工具标识
    @returns Optional[Dict[str, Any]] 工具定义对象
    @route internal://backend/app/services/mcp_tools/get_tool
    @throws 无
    """
    return _TOOL_REGISTRY.get(tool_name)


def execute_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    db: Optional[Session] = None
) -> ToolResult:
    """MCP 独立工具中心统一执行调度网关
    自动完成 Schema 校验、数据库会话绑定、执行耗时测算，
    原样回显入参 input_args，杜绝假执行。

    @param tool_name: str 工具注册唯一标识
    @param arguments: Dict[str, Any] 调用入参字典
    @param db: Optional[Session] 可选外部传入数据库会话(空则自动获取会话)
    @returns ToolResult 统一执行结果
    @route internal://backend/app/services/mcp_tools/execute_mcp_tool
    @throws 内部捕获校验异常与执行异常并安全封装
    """
    t0 = time.time()
    tool_def = get_tool(tool_name)

    # 1. 拦截未注册工具
    if not tool_def:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name=tool_name,
            input_args=arguments or {},
            error="TOOL_NOT_FOUND",
            message=f"未找到已注册的 MCP 工具: {tool_name}",
            execution_time_ms=execution_time_ms
        )

    schema_cls = tool_def["schema"]
    tool_func = tool_def["func"]

    # 2. Pydantic V2 参数强类型校验
    try:
        validated_input = schema_cls.model_validate(arguments or {})
    except ValidationError as val_err:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name=tool_name,
            input_args=arguments or {},
            error="INVALID_ARGUMENTS",
            message=f"MCP 工具入参格式校验失败: {str(val_err)}",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        execution_time_ms = int((time.time() - t0) * 1000)
        return ToolResult(
            success=False,
            tool_name=tool_name,
            input_args=arguments or {},
            error="PARAM_PARSING_ERROR",
            message=f"参数解析异常: {str(e)}",
            execution_time_ms=execution_time_ms
        )

    # 3. 会话注入与真实函数执行
    if db is not None:
        result = tool_func(validated_input, db)
    else:
        with SessionLocal() as local_db:
            result = tool_func(validated_input, local_db)

    # 4. 确保 input_args 完整填充，避免空入参逃逸
    if not result.input_args and arguments:
        result.input_args = arguments

    return result


# 统一快捷导出别名
execute_tool = execute_mcp_tool
