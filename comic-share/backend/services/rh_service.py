"""RunningHub 服务层 — HTTP 轮询客户端。"""

import asyncio
import logging
from typing import Any

import httpx

from core.config import get_config

logger = logging.getLogger(__name__)

RH_BASE_URL = "https://www.runninghub.cn/api"


def _get_rh_config() -> dict[str, Any]:
    """获取 RunningHub 配置。"""
    config = get_config()
    return config.get("services", {}).get("runninghub", {})


def _get_client_kwargs() -> dict[str, Any]:
    """构建 httpx 客户端参数（含代理）。"""
    rh_config = _get_rh_config()
    kwargs: dict[str, Any] = {"timeout": 30}
    proxy = rh_config.get("proxy", "")
    if proxy:
        kwargs["proxy"] = proxy
    return kwargs


async def check_health() -> bool:
    """检查 RunningHub API 是否可达。"""
    rh_config = _get_rh_config()
    api_key = rh_config.get("api_key", "")
    if not api_key:
        return False
    try:
        async with httpx.AsyncClient(**_get_client_kwargs()) as client:
            resp = await client.post(
                f"{RH_BASE_URL}/user/info",
                json={"apiKey": api_key},
            )
            return resp.status_code == 200
    except httpx.HTTPError:
        return False


async def create_task(
    workflow_id: str,
    node_params: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """创建 RunningHub 任务。"""
    rh_config = _get_rh_config()
    api_key = rh_config.get("api_key", "")
    if not api_key:
        raise RuntimeError("RunningHub API Key 未配置")

    payload: dict[str, Any] = {
        "apiKey": api_key,
        "workflowId": workflow_id,
    }
    if node_params:
        payload["nodeInfoList"] = node_params

    try:
        async with httpx.AsyncClient(**_get_client_kwargs()) as client:
            resp = await client.post(f"{RH_BASE_URL}/task/create", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"RunningHub 错误: {data.get('msg', 'unknown')}")
            task_id = data.get("data", {}).get("taskId", "")
            logger.info("RunningHub 任务已创建: task_id=%s", task_id)
            return {"task_id": task_id, "status": "queued"}
    except httpx.HTTPError as e:
        logger.error("RunningHub 任务创建失败: %s", str(e))
        raise RuntimeError(f"RunningHub 任务创建失败: {e}") from e


async def get_task_status(task_id: str) -> dict[str, Any]:
    """查询任务状态。"""
    rh_config = _get_rh_config()
    api_key = rh_config.get("api_key", "")

    try:
        async with httpx.AsyncClient(**_get_client_kwargs()) as client:
            resp = await client.post(
                f"{RH_BASE_URL}/task/status",
                json={"apiKey": api_key, "taskId": task_id},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                return {"status": "error", "error": data.get("msg", "")}
            task_data = data.get("data", {})
            return {
                "status": task_data.get("taskStatus", "unknown"),
                "progress": task_data.get("progress", 0),
                "output": task_data.get("outputList", []),
            }
    except httpx.HTTPError as e:
        return {"status": "error", "error": str(e)}


async def poll_task(task_id: str, timeout: int = 600, interval: int = 3) -> dict[str, Any]:
    """轮询任务直到完成。"""
    elapsed = 0
    while elapsed < timeout:
        result = await get_task_status(task_id)
        status = result.get("status", "")

        if status == "COMPLETED":
            return result
        if status in ("FAILED", "CANCELLED", "error"):
            return result

        await asyncio.sleep(interval)
        elapsed += interval

    return {"status": "timeout"}


async def cancel_task(task_id: str) -> bool:
    """取消任务。"""
    rh_config = _get_rh_config()
    api_key = rh_config.get("api_key", "")

    try:
        async with httpx.AsyncClient(**_get_client_kwargs()) as client:
            resp = await client.post(
                f"{RH_BASE_URL}/task/cancel",
                json={"apiKey": api_key, "taskId": task_id},
            )
            return resp.status_code == 200
    except httpx.HTTPError:
        return False
