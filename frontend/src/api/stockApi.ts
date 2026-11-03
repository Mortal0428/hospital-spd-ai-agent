import { httpGet, httpPost, httpPut, httpDelete } from './request';

/**
 * @file stockApi.ts
 * @description 普通耗材主库采购入库、请领受理闭环、临床二级库申领与手动发料出库、独立仓库盘点与财务对账 API
 */

export interface PurchaseInboundItemDTO {
  spec_code: string;
  product_name: string;
  spec_name?: string;
  model_name?: string;
  unit_name?: string;
  manufacturer?: string;
  unit_price: number;
  quantity: number;
  total_amount: number;
  batch_no: string;
  sterilization_batch?: string;
  produce_date?: string;
  expiry_date?: string;
  register_card_no?: string;
}

export interface PurchaseInboundRequestDTO {
  delivery_order_no?: string;
  inbound_type: string;
  invoice_no?: string;
  invoice_date?: string;
  warehouse_code: string;
  supplier_id: number;
  supplier_name: string;
  delivery_person?: string;
  delivery_phone?: string;
  delivery_id_card?: string;
  purchaser_name?: string;
  handler_name: string;
  auto_approve: boolean;
  remark?: string;
  items: PurchaseInboundItemDTO[];
}

export interface RequisitionBatchItemDTO {
  spec_code: string;
  product_name: string;
  spec_name?: string;
  model_name?: string;
  unit_name?: string;
  manufacturer?: string;
  unit_price: number;
  apply_qty: number;
  remark?: string;
}

export interface RequisitionBatchRequestDTO {
  apply_dept_code: string;
  apply_dept_name: string;
  apply_warehouse_code: string;
  target_main_warehouse_code: string;
  applicant_id: number;
  applicant_name: string;
  urgency_level?: string;
  apply_reason?: string;
  items: RequisitionBatchItemDTO[];
}

export interface ManualOutboundItemDTO {
  spec_code: string;
  batch_no: string;
  quantity: number;
  unit_price: number;
  remark?: string;
}

export interface ManualOutboundRequestDTO {
  warehouse_code: string;
  dept_code: string;
  outbound_type?: string;
  receiver_name: string;
  operator_name: string;
  use_purpose: string;
  items: ManualOutboundItemDTO[];
}

export interface StocktakeItemDTO {
  spec_code: string;
  product_name: string;
  spec_name?: string;
  model_name?: string;
  unit_name?: string;
  manufacturer?: string;
  batch_no: string;
  book_qty: number;
  actual_qty: number;
  diff_qty: number;
  unit_price: number;
  is_new_supplement?: number;
}

export interface StocktakeSubmitRequestDTO {
  warehouse_code: string;
  operator_name: string;
  reason_note?: string;
  items: StocktakeItemDTO[];
}

// 1. 采购验收入库 (图 5)
export function createPurchaseInboundOrder(data: PurchaseInboundRequestDTO): Promise<{
  order_no: string;
  total_items: number;
  total_qty: number;
  total_amount: number;
  status: string;
}> {
  return httpPost('/main-warehouse/purchase-inbound', data);
}

// 2. 主库请领受理看板 (图 3)
export function listMainRequisitions(params?: {
  warehouse_code?: string;
  status_filter?: string;
}): Promise<any[]> {
  return httpGet('/main-warehouse/requisitions', params);
}

export function approveRequisitionAndDispatch(reqId: number): Promise<{
  req_id: number;
  req_order_no: string;
  outbound_order_no: string;
  status: string;
}> {
  return httpPost(`/main-warehouse/requisitions/${reqId}/approve-and-dispatch`);
}

export function rejectRequisition(reqId: number, reason: string): Promise<any> {
  return httpPost(`/main-warehouse/requisitions/${reqId}/reject?reason=${encodeURIComponent(reason)}`);
}

// 3. 临床科室申请单填报 (图 4) 与撤回删除
export function createRequisitionBatch(data: RequisitionBatchRequestDTO): Promise<{
  req_order_no: string;
  total_items: number;
  status: string;
}> {
  return httpPost('/secondary-warehouse/requisitions-batch', data);
}

export function withdrawRequisition(reqId: number): Promise<{ req_id: number; status: string }> {
  return httpPost(`/secondary-warehouse/requisitions/${reqId}/withdraw`);
}

export function deleteRequisition(reqId: number): Promise<{ req_id: number }> {
  return httpDelete(`/secondary-warehouse/requisitions/${reqId}`);
}

// 4. 二级库手动发料出库 (消除在库库存，替代 HIS)
export function createManualOutbound(data: ManualOutboundRequestDTO): Promise<{
  outbound_order_no: string;
  total_items: number;
  total_qty: number;
  total_amount: number;
}> {
  return httpPost('/secondary-warehouse/manual-outbound', data);
}

// 5. 独立仓库盘点与漏账增补
export function getMainStocktakeInventory(): Promise<StocktakeItemDTO[]> {
  return httpGet('/main-warehouse/stocktake-inventory');
}

export function submitMainStocktake(data: StocktakeSubmitRequestDTO): Promise<any> {
  return httpPost('/main-warehouse/stocktake-submit', data);
}

export function getSecondaryStocktakeInventory(deptId?: number): Promise<StocktakeItemDTO[]> {
  return httpGet('/secondary-warehouse/stocktake-inventory', deptId ? { dept_id: deptId } : undefined);
}

export function submitSecondaryStocktake(data: StocktakeSubmitRequestDTO): Promise<any> {
  return httpPost('/secondary-warehouse/stocktake-submit', data);
}

// 6. 财务四大归口主库发料对账与进销存收发存月报
export function getMainDispatchReconciliation(month?: string): Promise<any[]> {
  return httpGet('/stats/main-dispatch-reconciliation', month ? { period_month: month } : undefined);
}

export function getDeptConsumptionReconciliation(): Promise<any[]> {
  return httpGet('/stats/dept-consumption-reconciliation');
}

export function getInventoryBalanceMonthly(month?: string): Promise<any> {
  return httpGet('/stats/inventory-balance-monthly', month ? { period_month: month } : undefined);
}
