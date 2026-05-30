"""LLM 服务层 — 多 Provider 流式调用，统一 SSE 输出。"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from core.config import get_config

logger = logging.getLogger(__name__)

# 支持 OpenAI 兼容 API 的 Provider 列表
OPENAI_COMPATIBLE = {"ollama", "lmstudio", "vllm", "remote-vllm", "deepseek", "custom"}


def _get_provider_config(provider: str | None = None) -> dict[str, Any]:
    """获取指定 Provider 配置，默认使用 config 中 default_provider。"""
    config = get_config()
    llm_config = config.get("llm", {})
    provider_name = provider or llm_config.get("default_provider", "ollama")
    providers = llm_config.get("providers", {})
    if provider_name not in providers:
        raise ValueError(f"未知 LLM Provider: {provider_name}")
    return {"name": provider_name, **providers[provider_name]}


async def list_models(provider: str | None = None) -> list[dict[str, str]]:
    """获取指定 Provider 的模型列表。"""
    prov = _get_provider_config(provider)
    base_url = prov["url"].rstrip("/")

    # Ollama 用自己的 API
    if prov["name"] == "ollama":
        url = f"{base_url}/api/tags"
    else:
        url = f"{base_url}/models"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        if prov["name"] == "ollama":
            models = data.get("models", [])
            return [{"id": m["name"], "name": m["name"]} for m in models]
        else:
            models = data.get("data", [])
            return [{"id": m["id"], "name": m.get("id", "")} for m in models]
    except httpx.HTTPError as e:
        logger.warning("获取模型列表失败 [%s]: %s", prov["name"], str(e))
        return []


async def generate_stream(
    prompt: str,
    system_prompt: str = "",
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """流式生成文本，yield 每个 chunk 的 content 字符串。"""
    prov = _get_provider_config(provider)
    base_url = prov["url"].rstrip("/")
    prov_name = prov["name"]

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Ollama 使用 /api/chat
    if prov_name == "ollama":
        url = f"{base_url}/api/chat"
        payload = {
            "model": model or "qwen2.5:7b",
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
    else:
        url = f"{base_url}/chat/completions"
        payload = {
            "model": model or "",
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    logger.debug("LLM 请求: provider=%s, model=%s, url=%s", prov_name, model, url)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    chunk = _parse_stream_line(line, prov_name)
                    if chunk is not None:
                        yield chunk
    except httpx.HTTPError as e:
        logger.error("LLM 流式调用失败: %s", str(e))
        raise RuntimeError(f"LLM 调用失败: {e}") from e


def _parse_stream_line(line: str, provider: str) -> str | None:
    """解析流式响应行，返回 content 文本或 None。"""
    import json

    if not line.strip():
        return None

    if provider == "ollama":
        try:
            data = json.loads(line)
            if data.get("done"):
                return None
            return data.get("message", {}).get("content", "")
        except json.JSONDecodeError:
            return None
    else:
        # OpenAI 兼容格式: data: {...}
        if line.startswith("data: "):
            line = line[6:]
        if line.strip() == "[DONE]":
            return None
        try:
            data = json.loads(line)
            choices = data.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content", "")
        except json.JSONDecodeError:
            return None
    return None
