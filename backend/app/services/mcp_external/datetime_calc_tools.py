"""
@file datetime_calc_tools.py
@description 医疗耗材灭菌保质期、效期倒计时与近效期先出 (FEFO) 精确推算 MCP 原子工具
解决大语言模型对于日历算法、闰年与剩余天数计算的天然算力幻觉，
为医院耗材科主管与二级库护士提供精确到日期的近效期预警与调拨优先级决策依据。

@param input_data: FefoCalcInput 生产日期与保质期入参模型
@returns ToolResult[FefoCalcOutput] 包含到期日、剩余天数与 FEFO 优先级的标准结果
@route internal://backend/app/services/mcp_external/datetime_calc_tools.py
@throws 日期格式错误或非法参数时抛出并安全包裹
"""

from datetime import date, datetime, timedelta
import logging
import time
from typing import Any, Optional
from app.services.mcp_tools.schema import ToolResult
from app.services.mcp_external.schema import FefoCalcInput, FefoCalcOutput

logger = logging.getLogger("spd.mcp_external.datetime_calc")


def mcp_datetime_and_fefo_calc(input_data: FefoCalcInput, db: Any = None) -> ToolResult[FefoCalcOutput]:
    """计算医疗物资灭菌有效截止日期与近效期先出 (FEFO) 流转优先级
    @param input_data: FefoCalcInput 包含 production_date 与 validity_years/months
    @param db: Any 可选数据库会话 (外部 MCP 保持解耦无需 db)
    @returns ToolResult[FefoCalcOutput] 结构化效期推算与流转建议
    @route internal://backend/app/services/mcp_external/datetime_calc_tools/mcp_datetime_and_fefo_calc
    @throws 格式异常时包裹在失败 ToolResult
    """
    start_time = time.perf_counter()

    try:
        # 解析生产日期
        prod_dt = datetime.strptime(input_data.production_date.strip(), "%Y-%m-%d").date()

        # 计算灭菌有效月数
        months = 0
        if input_data.validity_years:
            months += int(input_data.validity_years * 12)
        if input_data.validity_months:
            months += int(input_data.validity_months)

        # 默认 24 个月 (2年)
        if months <= 0:
            months = 24

        # 计算到期日 (支持年/月递增)
        new_year = prod_dt.year + (prod_dt.month + months - 1) // 12
        new_month = (prod_dt.month + months - 1) % 12 + 1
        # 日期溢出修正 (如闰年或大月)
        try:
            expiry_dt = date(new_year, new_month, prod_dt.day)
        except ValueError:
            # 如 2月29日 顺延至 2月28日
            import calendar
            last_day = calendar.monthrange(new_year, new_month)[1]
            expiry_dt = date(new_year, new_month, min(prod_dt.day, last_day))

        # 计算剩余天数
        today = date.today()
        days_left = (expiry_dt - today).days

        # FEFO 状态与优先级判定
        if days_left <= 0:
            status = "EXPIRED"
            priority = "FROZEN_RECALL"
            suggestion = f"该批次已超过灭菌有效截止日期 ({expiry_dt.strftime('%Y-%m-%d')})，触发国家医疗器械安全熔断机制，严禁用于临床，请立即冻结下架并启动不良退库流程！"
        elif days_left <= 60:
            status = "CRITICAL"
            priority = "URGENT"
            suggestion = f"极度濒危近效期预警 (仅剩 {days_left} 天到期)！根据 FEFO 规则，必须列为全院最优先级消耗批次，严禁向供应商继续采购同品种！"
        elif days_left <= 180:
            status = "NEAR_EXPIRY"
            priority = "PRIORITY"
            suggestion = f"近效期物资预警 (剩余 {days_left} 天)。建议主库优先分发调拨至手术量高的高周转病区科室加快消耗。"
        else:
            status = "NORMAL"
            priority = "ROUTINE"
            suggestion = f"物资效期充沛 (剩余 {days_left} 天)。符合三甲医院标准库存周期，按正常采购与申领流转即可。"

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        total_days = max(months * 30, 1)
        passed_days = max(total_days - days_left, 0)
        progress = round(min(max(passed_days / total_days * 100, 0), 100), 1)

        output_data = FefoCalcOutput(
            production_date=prod_dt.strftime("%Y-%m-%d"),
            calculated_expiry_date=expiry_dt.strftime("%Y-%m-%d"),
            expiry_date=expiry_dt.strftime("%Y-%m-%d"),
            days_to_expiry=days_left,
            days_remaining=days_left,
            validity_months=months,
            fefo_status=status,
            shelf_life_status=status,
            dispatch_priority=priority,
            fefo_priority=priority,
            suggestion=suggestion,
            recommendation=suggestion,
            progress_pct=progress
        )

        return ToolResult(
            success=True,
            tool_name="mcp_datetime_and_fefo_calc",
            input_args=input_data.model_dump(),
            data=output_data,
            message=f"效期与 FEFO 推算完成: 到期日 {expiry_dt.strftime('%Y-%m-%d')}，剩余 {days_left} 天 ({status})",
            execution_time_ms=max(elapsed_ms, 5)
        )

    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"效期计算异常: {e}", exc_info=True)
        return ToolResult(
            success=False,
            tool_name="mcp_datetime_and_fefo_calc",
            input_args=input_data.model_dump(),
            data=None,
            error=str(e),
            message=f"日期或效期参数格式非法: {str(e)}",
            execution_time_ms=elapsed_ms
        )
