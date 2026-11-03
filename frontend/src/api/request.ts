import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios';
import { ElMessage } from 'element-plus';

/**
 * 全局统一 RESTful 响应封包契约
 */
export interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

/**
 * Axios 客户端实例，统一配置超时与基础前缀
 */
const service: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 注入 JWT 鉴权凭据 Authorization: Bearer <token>
    const token = localStorage.getItem('spd_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    // 提取当前操作用户工号与角色标记
    let activeUsername = localStorage.getItem('spd_active_username') || '';
    let activeRole = '';

    const savedUserStr = localStorage.getItem('spd_active_user');
    if (savedUserStr) {
      try {
        const userObj = JSON.parse(savedUserStr);
        if (!activeUsername && userObj.username) {
          activeUsername = userObj.username;
        }
        if (userObj.roleCode) {
          activeRole = userObj.roleCode;
        }
      } catch {
        // 静默处理反序列化异常
      }
    }

    if (!activeUsername) {
      activeUsername = 'admin';
    }
    if (!activeRole) {
      activeRole = 'sys_admin';
    }

    // 同步注入 X-Mock-User, X-Mock-Role 与 X-Operator-User，实现双端兼容
    config.headers['X-Mock-User'] = activeUsername;
    config.headers['X-Mock-Role'] = activeRole;
    config.headers['X-Operator-User'] = encodeURIComponent(activeUsername);

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data;
    if (res.code && res.code !== 200) {
      ElMessage.error(res.msg || '业务操作被拦截');
      return Promise.reject(new Error(res.msg || '业务操作拦截'));
    }
    return response;
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '网络请求异常，请检查后端服务';
    ElMessage.error(message);
    return Promise.reject(error);
  }
);

/**
 * 通用 HTTP GET 请求封装函数
 * @param {string} url 请求目标相对路由路径
 * @param {Record<string, any>} [params] 请求查询参数对象
 * @returns {Promise<T>} 返回解析后的业务数据载荷 data
 * @route internal://src/api/request/httpGet
 * @throws {Error} 当网络异常或业务状态码非 200 时抛出异常
 */
export async function httpGet<T = any>(url: string, params?: Record<string, any>): Promise<T> {
  const resp = await service.get<ApiResponse<T>>(url, { params });
  return resp.data.data;
}

/**
 * 通用 HTTP POST 请求封装函数
 * @param {string} url 请求目标相对路由路径
 * @param {any} [data] 请求体 JSON 载荷
 * @returns {Promise<T>} 返回解析后的业务数据载荷 data
 * @route internal://src/api/request/httpPost
 * @throws {Error} 当网络异常或业务状态码非 200 时抛出异常
 */
export async function httpPost<T = any>(url: string, data?: any): Promise<T> {
  const resp = await service.post<ApiResponse<T>>(url, data);
  return resp.data.data;
}

/**
 * 通用 HTTP PUT 请求封装函数
 * @param {string} url 请求目标相对路由路径
 * @param {any} [data] 请求体 JSON 载荷
 * @returns {Promise<T>} 返回解析后的业务数据载荷 data
 * @route internal://src/api/request/httpPut
 * @throws {Error} 当网络异常或业务状态码非 200 时抛出异常
 */
export async function httpPut<T = any>(url: string, data?: any): Promise<T> {
  const resp = await service.put<ApiResponse<T>>(url, data);
  return resp.data.data;
}

/**
 * 通用 HTTP DELETE 请求封装函数
 * @param {string} url 请求目标相对路由路径
 * @param {Record<string, any>} [params] 请求查询参数对象
 * @returns {Promise<T>} 返回解析后的业务数据载荷 data
 * @route internal://src/api/request/httpDelete
 * @throws {Error} 当网络异常或业务状态码非 200 时抛出异常
 */
export async function httpDelete<T = any>(url: string, params?: Record<string, any>): Promise<T> {
  const resp = await service.delete<ApiResponse<T>>(url, { params });
  return resp.data.data;
}

/**
 * 通用 HTTP PATCH 请求封装函数
 * @param {string} url 请求目标相对路由路径
 * @param {any} [data] 请求体 JSON 载荷
 * @returns {Promise<T>} 返回解析后的业务数据载荷 data
 * @route internal://src/api/request/httpPatch
 * @throws {Error} 当网络异常或业务状态码非 200 时抛出异常
 */
export async function httpPatch<T = any>(url: string, data?: any): Promise<T> {
  const resp = await service.patch<ApiResponse<T>>(url, data);
  return resp.data.data;
}

export default service;

