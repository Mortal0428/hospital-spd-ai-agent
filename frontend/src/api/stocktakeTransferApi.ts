import { httpGet, httpPost } from './request';

/**
 * 盘点与调拨单据模型契约
 */
export interface StocktakeTransferOrder {
  order_no: string;
  biz_category: string;
  from_warehouse_code: string;
  to_warehouse_code: string | null;
  product_code: string;
  product_name: string;
  book_qty: number;
  actual_or_transfer_qty: number;
  diff_qty: number;
  confirm_stage: string;
  operator_name: string;
  reason_note: string | null;
}

/**
 * 查询全院各科室独立仓库盘点单（普耗/高值/二级库）与跨院调拨单
 * @param params 可选业务大类过滤参数 (biz_category)
 * @returns Promise<StocktakeTransferOrder[]> 单据列表
 * @route GET /ext/orders/stocktake-transfer
 * @throws Error 当请求异常时抛出
 */
export function listStocktakeTransferOrders(params?: { biz_category?: string }): Promise<StocktakeTransferOrder[]> {
  return httpGet('/ext/orders/stocktake-transfer', params);
}

/**
 * 创建科室独立仓库盘点单（自动核算账实差额）或跨科/跨院调拨单
 * @param data 盘点或调拨制单请求载荷
 * @returns Promise 创建的盘点调拨单对象
 * @route POST /ext/orders/stocktake-transfer
 * @throws Error 当产品不存在时抛出
 */
export function createStocktakeOrTransferOrder(data: {
  biz_category: string;
  from_warehouse_code: string;
  to_warehouse_code?: string;
  product_id: number;
  book_qty: number;
  actual_or_transfer_qty: number;
  operator_name: string;
  reason_note?: string;
}): Promise<{ order_no: string; biz_category: string; book_qty: number; actual_or_transfer_qty: number; diff_qty: number; confirm_stage: string }> {
  return httpPost('/ext/orders/stocktake-transfer', data);
}
