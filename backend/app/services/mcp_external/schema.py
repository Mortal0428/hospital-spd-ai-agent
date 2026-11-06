"""
@file schema.py
@description 外部解耦式 MCP 工具强类型入参出参契约模型
严格遵循 Pydantic V2 规范，定义外部联网检索、法规溯源与医疗效期计算的强类型模型，
杜绝入参出参为空字典或格式错乱。

@param 无
@returns Pydantic V2 输入与输出模型
@route internal://backend/app/services/mcp_external/schema.py
@throws 字段校验失败时触发 ValidationError
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.services.mcp_tools.schema import BaseToolInput


class ExternalSearchInput(BaseToolInput):
    """外部医学知识与国家药监局标准联网检索入参模型"""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    keyword: str = Field(default="", description="检索关键词(如耗材品名、器械分类、国家执行标准号或集采通知)")
    query_keyword: Optional[str] = Field(default=None, description="检索词别名字段")
    max_results: int = Field(default=3, ge=1, le=10, description="最大返回外部权威知识条目数")
    category: Optional[str] = Field(default="STANDARD", description="检索分类: STANDARD-国家药监局与国标规范, RECALL-召回与不良事件, GENERAL-权威医药文献")


class SearchResultItem(BaseModel):
    """单条外部检索结果结构化实体"""
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    title: str = Field(..., description="标准文献或法规条目标题")
    source: str = Field(..., description="发布机构或数据来源(如: 国家药品监督管理局/国家标准化管理委员会/中国医药信息网)")
    standard_no: Optional[str] = Field(default=None, description="标准代号或批准文号(如: GB 19082-2009 / 国械注准20223140567)")
    summary: str = Field(..., description="核心摘要与适用范围说明")
    publish_date: Optional[str] = Field(default=None, description="发布或实施日期")
    verification_status: str = Field(default="VERIFIED", description="核验证照状态: VERIFIED-官方权威收录, ACTIVE-现行有效")
    category: Optional[str] = Field(default="国家行业标准", description="类别")
    authority: Optional[str] = Field(default="国家药品监督管理局", description="发布机构")
    applicable_departments: List[str] = Field(default_factory=lambda: ["耗材科", "设备科", "临床科室"], description="适用科室")


class ExternalSearchOutput(BaseModel):
    """外部医学知识检索统一出参实体"""
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    query: str = Field(..., description="用户检索查询词")
    results: List[SearchResultItem] = Field(default_factory=list, description="检索到的权威条目列表")
    items: Optional[List[Dict[str, Any]]] = Field(default=None, description="检索条目别名列表")
    total_found: int = Field(default=0, description="匹配到的知识总数")
    search_latency_ms: int = Field(default=0, description="外部检索耗时(毫秒)")
    data_source_provider: str = Field(default="NMPA_OPEN_STANDARDS", description="外部 MCP 数据提供方")


class FefoCalcInput(BaseToolInput):
    """医疗物资效期与近效期先出 (FEFO) 推算入参模型"""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    production_date: str = Field(..., description="物资生产日期 (格式: YYYY-MM-DD)")
    validity_years: Optional[float] = Field(default=None, description="灭菌有效保质年数 (如: 2.0 或 3.0)")
    validity_months: Optional[int] = Field(default=None, description="有效保质月数 (如: 24 或 36)")
    batch_no: Optional[str] = Field(default=None, description="耗材出厂批号 (如: BATCH-20261101)")
    product_name: Optional[str] = Field(default=None, description="耗材物资品名")
    material_name: Optional[str] = Field(default=None, description="物资品名别名")


class FefoCalcOutput(BaseModel):
    """医疗物资效期与 FEFO 推算结果实体"""
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    production_date: str = Field(..., description="起始生产日期")
    calculated_expiry_date: str = Field(..., description="推算得出的灭菌到期日 (YYYY-MM-DD)")
    expiry_date: Optional[str] = Field(default=None, description="到期日别名")
    days_to_expiry: int = Field(..., description="距离到期剩余天数 (负数表示已过期)")
    days_remaining: Optional[int] = Field(default=None, description="剩余天数别名")
    validity_months: Optional[int] = Field(default=24, description="有效时长月数")
    fefo_status: str = Field(..., description="FEFO 状态: NORMAL-效期充沛, NEAR_EXPIRY-近效期预警(<=180天), CRITICAL-极度濒危(<=60天), EXPIRED-已过期熔断")
    shelf_life_status: Optional[str] = Field(default=None, description="状态别名")
    dispatch_priority: str = Field(..., description="调拨优先级: URGENT-紧急优先分发出库, PRIORITY-优先消耗, ROUTINE-常规流转")
    fefo_priority: Optional[str] = Field(default=None, description="优先级别名")
    suggestion: str = Field(..., description="面向科室与主库的操作建议")
    recommendation: Optional[str] = Field(default=None, description="操作建议别名")
    progress_pct: Optional[float] = Field(default=0.0, description="生命周期消耗百分比")
