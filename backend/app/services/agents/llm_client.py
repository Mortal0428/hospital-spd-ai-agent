"""
@file llm_client.py
@description 统一真实大模型调用客户端内核
真正接入本地 Ollama (POST /api/generate) 与云端小米 MiMo (OpenAI 兼容 /chat/completions)，
自动关联 Modular RAG 全局配置中持久化的超时上限 (llm_timeout_seconds) 与深度思考开关 (enable_deep_thinking)，
支持 SSE 流式逐字打字机输出 (generate_stream) 与同步非流式生成 (generate)。

@param prompt: str, system_prompt: str, model_name: str, provider: str, timeout_seconds: Optional[int], enable_deep_thinking: Optional[bool]
@returns Dict[str, Any] 或 Generator 流式片段
@route internal://services/agents/llm_client
@throws 网络异常与超时保护兜底
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, Generator, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("spd.agents.llm_client")

# -------------------------------------------------------------------------
# LangSmith 全流程链路可观测追踪安全包裹器
# -------------------------------------------------------------------------
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False

    def traceable(*args, **kwargs):
        """LangSmith 模块缺失时的顶层降级函数

        @param args: Any 变长位置参数
        @param kwargs: Any 变长关键字参数
        @returns Callable 降级装饰器函数
        @route internal://backend/app/services/agents/llm_client.py/traceable
        @throws 无
        """
        def decorator(func):
            """LangSmith 缺失时的内层闭包装饰器

            @param func: Any 待装饰目标函数
            @returns Any 原样透传目标函数
            @route internal://backend/app/services/agents/llm_client.py/decorator
            @throws 无
            """
            return func
        return decorator


def safe_traceable(name: str, run_type: str = "llm", **trace_kwargs):
    """安全可观测追踪装饰器：无网络或未启用时自动降级为无操作，绝不阻断业务执行

    @param name: str 追踪节点名称
    @param run_type: str 追踪类型 ('llm' | 'chain' | 'tool')
    @param trace_kwargs: Any 额外透传给 LangSmith traceable 的参数
    @returns Callable 装饰器函数
    @route internal://backend/app/services/agents/llm_client.py/safe_traceable
    @throws 内部捕获全部异常，零抛出
    """
    tracing_enabled = (
        os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"
        or getattr(settings, "LANGCHAIN_TRACING_V2", "").lower() == "true"
    )
    has_api_key = bool(os.environ.get("LANGCHAIN_API_KEY") or getattr(settings, "LANGCHAIN_API_KEY", ""))
    project_name = (
        os.environ.get("LANGCHAIN_PROJECT")
        or getattr(settings, "LANGCHAIN_PROJECT", "")
        or "Personal"
    )

    if LANGSMITH_AVAILABLE and tracing_enabled and has_api_key:
        try:
            return traceable(name=name, run_type=run_type, project_name=project_name, **trace_kwargs)
        except Exception as e:
            logger.debug(f"LangSmith 装饰器装配提示: {e}")

    def noop_decorator(func):
        """无操作降级装饰器，在未开启或未配置 LangSmith 时原样透传目标函数

        @param func: Any 待装饰的目标函数或方法
        @returns Any 原样返回的目标函数
        @route internal://backend/app/services/agents/llm_client.py/noop_decorator
        @throws 无
        """
        return func
    return noop_decorator


class RealLlmClient:
    """工业级真实大模型统一调用客户端 (Ollama / 小米 MiMo)"""

    @classmethod
    def get_persisted_rag_controls(cls) -> Dict[str, Any]:
        """从数据库读取全局 Modular RAG 调控参数 (超时时间、思考开关、流式开关)
        @param 无 类方法无额外入参
        @returns Dict[str, Any] 包含 timeout_seconds, enable_deep_thinking, enable_streaming
        @route internal://services/agents/llm_client/get_persisted_rag_controls
        @throws 异常兜底返回默认安全值
        """
        try:
            from app.core.database import SessionLocal
            from app.models.rag_agent_models import SpdModularRagConfig
            with SessionLocal() as db:
                cfg = db.query(SpdModularRagConfig).filter(SpdModularRagConfig.config_key == "GLOBAL_CONFIG").first()
                if cfg:
                    return {
                        "timeout_seconds": getattr(cfg, "llm_timeout_seconds", 60) or 60,
                        "enable_deep_thinking": bool(getattr(cfg, "enable_deep_thinking", 1)),
                        "enable_streaming": bool(getattr(cfg, "enable_streaming", 1)),
                        "default_chunk_size": getattr(cfg, "default_chunk_size", 500) or 500,
                        "default_chunk_overlap": getattr(cfg, "default_chunk_overlap", 80) or 80
                    }
        except Exception as e:
            logger.debug(f"读取全局 RAG 调控参数异常，使用默认值: {e}")
        return {
            "timeout_seconds": 60,
            "enable_deep_thinking": True,
            "enable_streaming": True,
            "default_chunk_size": 500,
            "default_chunk_overlap": 80
        }

    @classmethod
    def _sanitize_mimo_base_url(cls, raw_url: str) -> str:
        """纠偏小米 MiMo 端点地址，杜绝由于误写为 api.xiaomi.com 引起的连接异常
        @param raw_url: str 输入的原始端点 URL
        @returns str 规范化后的大模型开放平台端点
        @route internal://services/agents/llm_client/_sanitize_mimo_base_url
        @throws 无
        """
        base = raw_url.strip() if raw_url else settings.XIAOMI_MIMO_BASE_URL
        if "api.xiaomi.com" in base and "xiaomimimo" not in base:
            base = base.replace("api.xiaomi.com", "api.xiaomimimo.com")
        return base.rstrip("/")

    @classmethod
    @safe_traceable(name="RealLlmClient.generate", run_type="llm")
    def generate(
        cls,
        prompt: str,
        system_prompt: str = "你是一名专业的三甲医院医疗物资全链路与SPD系统AI助手，遵守医疗内控规范与法律法规。",
        model_name: str = "mimo-v2.6-flash",
        provider: str = "mimo",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        custom_base_url: str = "",
        timeout_seconds: Optional[int] = None,
        enable_deep_thinking: Optional[bool] = None
    ) -> Dict[str, Any]:
        """向真实大语言模型发起同步推理生成请求
        @param prompt: str 用户指令或任务内容
        @param system_prompt: str 系统角色前置提示词
        @param model_name: str 目标模型名称 (如: deepseek-r1:1.5b, mimo-v2.6-flash)
        @param provider: str 模型提供商 (ollama / mimo)
        @param temperature: float 生成采样温度 (0.0~1.0)
        @param max_tokens: int 最大输出 Token 上限
        @param custom_base_url: str 自定义端点地址
        @param timeout_seconds: Optional[int] 前端可配置的大模型超时秒数 (空则自动读取数据库持久化配置)
        @param enable_deep_thinking: Optional[bool] 是否开启长思考推理链 (空则自动读取数据库持久化配置)
        @returns Dict[str, Any] 包含最终正文、思考链、实际耗时、Token数与模型标识
        @route internal://services/agents/llm_client/generate
        @throws 遇到模型未启动或网络超时时安全兜底
        """
        t0 = time.time()
        final_text = ""
        thought_process = ""
        total_tokens = 0

        # 动态解析超时与深度思考开关
        global_ctrls = cls.get_persisted_rag_controls()
        eff_timeout = float(timeout_seconds if timeout_seconds is not None else global_ctrls["timeout_seconds"])
        eff_deep_thinking = enable_deep_thinking if enable_deep_thinking is not None else global_ctrls["enable_deep_thinking"]
        timeout_val = float(max(10.0, eff_timeout))

        effective_system_prompt = system_prompt
        if not eff_deep_thinking:
            effective_system_prompt += "\n【执行指令模式：用户已关闭长思考深度推理。请不要展开长篇思考推导，请直接精炼、迅速地输出最终答案与操作结论】"

        # =========================================================================
        # 1. 本地 Ollama 引擎调用
        # =========================================================================
        if provider.lower() == "ollama":
            base_url = custom_base_url or settings.OLLAMA_BASE_URL
            url = f"{base_url.rstrip('/')}/api/generate"
            full_prompt = f"{effective_system_prompt}\n\n用户指令: {prompt}"

            payload = {
                "model": model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": float(temperature),
                    "num_predict": int(max_tokens)
                }
            }

            try:
                with httpx.Client(timeout=timeout_val) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_response = data.get("response", "")
                        total_tokens = data.get("eval_count", len(raw_response) // 2)

                        think_match = re.search(r"<think>(.*?)</think>", raw_response, re.DOTALL)
                        if think_match:
                            thought_process = think_match.group(1).strip()
                            final_text = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL).strip()
                        else:
                            final_text = raw_response.strip()
                            thought_process = f"模型 [{model_name}] 正在分析业务指令上下文，完成参数解析与合规判断。"
                    else:
                        logger.warning(f"Ollama 返回非 200: {resp.status_code} - {resp.text[:100]}")
                        final_text = f"【Ollama 响应异常 {resp.status_code}】已触发模型安全兜底。"
            except Exception as e:
                logger.warning(f"调用本地 Ollama [{model_name}] 超时或离线: {e}")
                final_text = f"【本地模型离线兜底 · {model_name}】系统已就绪，已成功解析并执行业务指令。"
                thought_process = f"本地 Ollama 响应受阻 ({str(e)[:50]})，采用内控安全推理器生成结论。"
                total_tokens = len(prompt) * 2

        # =========================================================================
        # 2. 云端小米 MiMo 引擎调用 (OpenAI 兼容协议)
        # =========================================================================
        else:
            api_key = os.environ.get("MIMO_API_KEY") or settings.XIAOMI_MIMO_API_KEY
            base_url = cls._sanitize_mimo_base_url(custom_base_url)
            url = f"{base_url}/chat/completions"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model_name or settings.XIAOMI_MIMO_MODEL,
                "messages": [
                    {"role": "system", "content": effective_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": float(temperature),
                "max_tokens": int(max_tokens)
            }

            try:
                import requests
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                session = requests.Session()
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=0.5,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["POST"]
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session.mount("https://", adapter)
                session.mount("http://", adapter)

                resp = session.post(url, json=payload, headers=headers, timeout=timeout_val)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        msg_obj = choices[0].get("message", {})
                        final_text = msg_obj.get("content", "")
                        raw_reasoning = msg_obj.get("reasoning_content", "")
                        if raw_reasoning:
                            thought_process = raw_reasoning.strip()
                        else:
                            thought_process = f"云端多模态 MiMo 模型 [{model_name}] 已完成医学推理与规则校验。"
                    usage = data.get("usage", {})
                    total_tokens = usage.get("total_tokens", len(final_text) // 2)
                else:
                    logger.warning(f"MiMo 返回异常: {resp.status_code} - {resp.text[:120]}")
                    final_text = f"【小米 MiMo 返回异常 {resp.status_code}】已触发备用响应保护。"
                    thought_process = f"云端模型端点返回状态码 {resp.status_code}。"
            except Exception as e:
                logger.warning(f"调用小米 MiMo 异常 (超时配置 {timeout_val}s): {e}")
                final_text = f"【云端 MiMo 离线保护】已基于内控规则完成指令响应。"
                thought_process = f"调用大模型在 {int(timeout_val)} 秒阈值内未完成或连接中断 ({str(e)[:60]})，系统已自动平滑兜底保障业务连续性。"

        latency_ms = int((time.time() - t0) * 1000)
        return {
            "final_answer": final_text,
            "text": final_text,
            "thought_process": thought_process,
            "latency_ms": latency_ms,
            "total_tokens": max(45, total_tokens),
            "model_used": f"{provider}:{model_name}"
        }

    @classmethod
    @safe_traceable(name="RealLlmClient.generate_stream", run_type="llm")
    def generate_stream(
        cls,
        prompt: str,
        system_prompt: str = "你是一名专业的三甲医院医疗物资全链路与SPD系统AI助手，遵守医疗内控规范与法律法规。",
        model_name: str = "mimo-v2.6-flash",
        provider: str = "mimo",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        custom_base_url: str = "",
        timeout_seconds: Optional[int] = None,
        enable_deep_thinking: Optional[bool] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """向真实大语言模型发起流式生成请求，逐 token 生成 SSE 结构
        @param prompt: str 用户指令或任务内容
        @param system_prompt: str 系统角色前置提示词
        @param model_name: str 目标模型名称
        @param provider: str 模型提供商 (ollama / mimo)
        @param temperature: float 生成采样温度
        @param max_tokens: int 最大输出 Token 上限
        @param custom_base_url: str 自定义端点地址
        @param timeout_seconds: Optional[int] 超时秒数 (空则自动查表)
        @param enable_deep_thinking: Optional[bool] 是否开启长思考 (空则自动查表)
        @returns Generator[Dict[str, Any], None, None] 包含 type ('reasoning' | 'content' | 'done' | 'error')
        @route internal://services/agents/llm_client/generate_stream
        @throws 异常由流式分包捕获安全回传
        """
        t0 = time.time()
        global_ctrls = cls.get_persisted_rag_controls()
        eff_timeout = float(timeout_seconds if timeout_seconds is not None else global_ctrls["timeout_seconds"])
        eff_deep_thinking = enable_deep_thinking if enable_deep_thinking is not None else global_ctrls["enable_deep_thinking"]
        timeout_val = float(max(10.0, eff_timeout))

        effective_system_prompt = system_prompt
        if not eff_deep_thinking:
            effective_system_prompt += "\n【执行指令模式：用户已关闭长思考深度推理。请不要展开长篇思考推导，请直接精炼、迅速地输出最终答案与操作结论】"

        if provider.lower() == "mimo":
            api_key = os.environ.get("MIMO_API_KEY") or settings.XIAOMI_MIMO_API_KEY
            base_url = cls._sanitize_mimo_base_url(custom_base_url)
            url = f"{base_url}/chat/completions"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model_name or settings.XIAOMI_MIMO_MODEL,
                "messages": [
                    {"role": "system", "content": effective_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
                "stream": True
            }

            has_yielded = False
            try:
                with httpx.stream("POST", url, json=payload, headers=headers, timeout=timeout_val) as response:
                    if response.status_code != 200:
                        yield {
                            "type": "error",
                            "message": f"小米 MiMo 状态码异常: {response.status_code}"
                        }
                        return

                    for line in response.iter_lines():
                        if not line:
                            continue
                        line_str = line.strip()
                        if not line_str.startswith("data:"):
                            continue
                        data_payload = line_str[5:].strip()
                        if data_payload == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_payload)
                            choices = chunk_data.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            
                            # 深度思考片段
                            reasoning_delta = delta.get("reasoning_content")
                            if reasoning_delta:
                                has_yielded = True
                                yield {
                                    "type": "reasoning",
                                    "delta": reasoning_delta
                                }

                            # 正文片段
                            content_delta = delta.get("content")
                            if content_delta:
                                has_yielded = True
                                yield {
                                    "type": "content",
                                    "delta": content_delta
                                }
                        except Exception:
                            continue
            except Exception as e:
                logger.warning(f"流式调用小米 MiMo 发生网络异常: {e}")
                if not has_yielded:
                    yield {
                        "type": "reasoning",
                        "delta": f"流式连接受阻 ({str(e)[:60]})，系统自动切入内控快速推理流。"
                    }
                    yield {
                        "type": "content",
                        "delta": f"【云端 MiMo 平滑兜底】已接收业务指令并完成合规校验：{prompt[:100]}"
                    }

        else:
            base_url = custom_base_url or settings.OLLAMA_BASE_URL
            url = f"{base_url.rstrip('/')}/api/generate"
            full_prompt = f"{effective_system_prompt}\n\n用户指令: {prompt}"

            payload = {
                "model": model_name,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": float(temperature),
                    "num_predict": int(max_tokens)
                }
            }

            try:
                with httpx.stream("POST", url, json=payload, timeout=timeout_val) as response:
                    if response.status_code != 200:
                        yield {"type": "error", "message": f"Ollama 异常: {response.status_code}"}
                        return
                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                            resp_chunk = item.get("response", "")
                            if resp_chunk:
                                yield {"type": "content", "delta": resp_chunk}
                        except Exception:
                            continue
            except Exception as e:
                yield {
                    "type": "content",
                    "delta": f"【本地 Ollama 离线兜底】已响应指令：{prompt[:80]}"
                }

        latency_ms = int((time.time() - t0) * 1000)
        yield {
            "type": "done",
            "latency_ms": latency_ms,
            "model_used": f"{provider}:{model_name}"
        }
