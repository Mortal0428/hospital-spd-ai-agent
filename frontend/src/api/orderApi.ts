import { httpGet, httpPost } from './request';

/**
 * 通用出入库与期初建账单据模型契约
 */
export interface InboundOutboundOrder {
  id: number;
  order_no: string;
  order_type: string;
  warehouse_code: string;
  dept_code: string;
  target_dept_or_supplier: string;
  product_code: string;
  product_name: string;
  batch_no: string;
  quantity: number;
  total_amount: number;
  source_ref_order_no: string | null;
  confirm_stage: 'PENDING_CONFIRM' | 'SUBMITTED';
  is_irreversible_locked: number;
  created_by: string;
  second_confirmed_by: string | null;
  remark: string | null;
}

/**
 * 查询通用出入库、退供应商红字单及期初建账单据列表
 * @param params 可选单据类型过滤参数（order_type）
 * @returns Promise<InboundOutboundOrder[]> 单据列表
 * @route GET /ext/orders/inbound-outbound
 * @throws Error 当请求异常时向外抛出
 */
export function listInboundOutboundOrders(params?: { order_type?: string }): Promise<InboundOutboundOrder[]> {
  return httpGet('/ext/orders/inbound-outbound', params);
}

/**
 * 填单页第 1 次提交创建通用出入库单、退给供应商红字单或期初建账单
 * @param data 填单请求载荷
 * @returns Promise<{ order_no: string; order_type: string; quantity: number; confirm_stage: string; is_irreversible_locked: number }>
 * @route POST /ext/orders/inbound-outbound
 * @throws Error 当期初数据已二次确认锁定尝试重复填报时抛出拦截
 */
export function createInboundOutboundOrder(data: {
  order_type: string;
  warehouse_code: string;
  dept_code: string;
  target_dept_or_supplier: string;
  product_id: number;
  batch_no?: string;
  quantity: number;
  created_by: string;
  remark?: string;
}): Promise<{ order_no: string; order_type: string; quantity: number; confirm_stage: string; is_irreversible_locked: number }> {
  return httpPost('/ext/orders/inbound-outbound', data);
}

/**
 * 执行外层二次确认、取消提交或修改备注两阶段状态机动作
 * @param data 包含 order_no, action, operator_name, new_remark 的操作载荷
 * @returns Promise 包含更新后的 confirm_stage 与 is_irreversible_locked
 * @route POST /ext/orders/two-step-action
 * @throws Error 当违反锁死规则或期初不可逆规则时抛出拦截异常
 */
export function executeOrderTwoStepAction(data: {
  order_no: string;
  action: 'SECOND_CONFIRM' | 'CANCEL_SUBMIT' | 'EDIT_REMARK' | 'DELETE_ORDER';
  operator_name: string;
  new_remark?: string;
}): Promise<any> {
  return httpPost('/ext/orders/two-step-action', data);
}

/**
 * 审核批准二级库请领单并自动在耗材出库模块生成审核出库记录
 * @param reqId 请领单主键 ID
 * @param auditorName 审核人姓名
 * @returns Promise 自动生成的出库单单号与状态
 * @route POST /ext/orders/requisition-auto-outbound/{req_id}
 * @throws Error 当请领单不存在或已审批时抛出异常
 */
export function approveRequisitionAutoOutbound(
  reqId: number,
  auditorName: string
): Promise<{ auto_outbound_order_no: string; source_ref_order_no: string; quantity: number; confirm_stage: string }> {
  return httpPost(`/ext/orders/requisition-auto-outbound/${reqId}?auditor_name=${encodeURIComponent(auditorName)}`);
}
