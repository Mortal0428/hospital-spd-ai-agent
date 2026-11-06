"""
@file schema.py
@description MCP 工具注册中心标准协议与入参出参强类型契约定义
严格遵循 Pydantic V2 规范，统一封装 ToolResult 与标准字段，
坚决消除工具入参为空字典 {} 的假执行现象。

@param 无
@returns Pydantic V2 基础模型与统一返回结构
@route internal://backend/app/services/mcp_tools/schema.py
@throws 字段类型校验失败时触发 ValidationError
"""

import time
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseToolInput(BaseModel):
    """MCP 工具统一基础入参模型
    禁止额外参数注入 (extra='forbid')，支持别名填充与强类型转换
    """
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ToolResult(BaseModel, Generic[T]):
    """MCP 工具统一返回结构体封装
    包含执行状态、工具名称、真实入参字典、业务数据实体、错误信息与执行耗时。
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = Field(..., description="工具执行成功标识: True-成功, False-失败")
    tool_name: str = Field(..., description="被调用的 MCP 工具注册唯一标识")
    input_args: Dict[str, Any] = Field(default_factory=dict, description="执行时真实传入的参数明细(严禁为空字典假执行)")
    data: Optional[T] = Field(default=None, description="工具执行成功产出的结构化业务数据实体")
    error: Optional[str] = Field(default=None, description="错误类型或异常摘要(执行成功时为 None)")
    message: str = Field(default="", description="面向人类或智能体上下文的业务执行结果描述")
    execution_time_ms: int = Field(default=0, description="工具在数据库或向量库中的实际执行耗时(毫秒)")
    trace_no: Optional[str] = Field(default=None, description="联动生成的 6W 流转日志全局唯一追踪号")

    def to_dict(self) -> Dict[str, Any]:
        """将 ToolResult 转换为标准化字典，兼容前端展示契约
        确保 args 与 input_args 同时存在，杜绝前端展示为空对象 {}

        @param 无 实例方法无额外入参
        @returns Dict[str, Any] 格式化字典
        @route internal://backend/app/services/mcp_tools/schema.py/to_dict
        @throws 无
        """
        raw_data = self.data
        if hasattr(raw_data, "model_dump"):
            raw_data = raw_data.model_dump()
        elif isinstance(raw_data, list):
            raw_data = [item.model_dump() if hasattr(item, "model_dump") else item for item in raw_data]

        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "name": self.tool_name,
            "input_args": self.input_args,
            "args": self.input_args,
            "data": raw_data,
            "output": raw_data,
            "result": raw_data,
            "error": self.error,
            "message": self.message,
            "execution_time_ms": self.execution_time_ms,
            "trace_no": self.trace_no
        }
