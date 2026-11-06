"""SQLAlchemy 2.0 ORM 数据模型包定义（含核心 10 张表 + 深度扩展 7 张表，共 17 张物理表）"""

from app.models.spd_models import (
    SysDepartment,
    SysUser,
    SpdCategory,
    SpdProductDict,
    SpdMainInventory,
    SpdDistributionOrder,
    SpdHighValueItem,
    SpdSecondaryInventory,
    SpdRequisitionOrder,
    SpdWorkflowLog
)
from app.models.spd_extended_models import (
    SysUserModulePermission,
    SpdWarehouseNode,
    SpdProductDictExt,
    SpdInboundAndOutboundOrder,
    SpdStocktakeAndTransferOrder,
    SpdHighValueLifecycleOrder,
    SpdSupplierAndPurchaseOrder,
    SpdProductSpn,
    SpdProductSpec,
    SpdSupplierProfile,
    SysUserWarehousePerm,
    SpdPriceAdjustLog,
    SpdRecallPatientFollowUp
)
from app.models.rag_agent_models import (
    SpdRagCategoryTree,
    SpdRagDocument,
    SpdRagChunk,
    SpdModularRagConfig,
    SpdAgentExecutionTrace,
    SpdAgentModelConfig,
    SpdAgentChatMessage
)

__all__ = [
    "SysDepartment",
    "SysUser",
    "SpdCategory",
    "SpdProductDict",
    "SpdMainInventory",
    "SpdDistributionOrder",
    "SpdHighValueItem",
    "SpdSecondaryInventory",
    "SpdRequisitionOrder",
    "SpdWorkflowLog",
    "SysUserModulePermission",
    "SpdWarehouseNode",
    "SpdProductDictExt",
    "SpdInboundAndOutboundOrder",
    "SpdStocktakeAndTransferOrder",
    "SpdHighValueLifecycleOrder",
    "SpdSupplierAndPurchaseOrder",
    "SpdProductSpn",
    "SpdProductSpec",
    "SpdSupplierProfile",
    "SysUserWarehousePerm",
    "SpdPriceAdjustLog",
    "SpdRecallPatientFollowUp",
    "SpdRagCategoryTree",
    "SpdRagDocument",
    "SpdRagChunk",
    "SpdModularRagConfig",
    "SpdAgentExecutionTrace",
    "SpdAgentModelConfig",
    "SpdAgentChatMessage"
]
