"""工作流注册表服务 — 读取配置、统一执行分发、统一状态查询。"""

import logging
from typing import Any

from core.config import get_config
from services import comfyui_service, rh_service

logger = logging.getLogger(__name__)


def get_registry() -> list[dict[str, Any]]:
    """返回所有注册的工作流。"""
    config = get_config()
    return config.get("workflows", {}).get("registry", [])


def get_enabled_workflows(category: str | None = None) -> list[dict[str, Any]]:
    """返回所有已启用的工作流（可选按类别过滤）。"""
    return [
        w for w in get_registry()
        if w.get("enabled", False) and (category is None or w.get("category") == category)
    ]


def get_workflow_by_id(workflow_id: str) -> dict[str, Any] | None:
    """根据 ID 查找工作流。"""
    for w in get_registry():
        if w.get("id") == workflow_id:
            return w
    return None


def get_engines() -> dict[str, dict[str, Any]]:
    """返回所有引擎模式定义。"""
    config = get_config()
    return config.get("workflows", {}).get("engines", {})


def get_default_engine() -> str:
    """返回默认引擎模式 ID。"""
    config = get_config()
    return config.get("workflows", {}).get("default_engine", "runninghub")


def resolve_workflow_id(engine: str) -> str:
    """根据引擎模式找到该引擎的默认工作流 ID。"""
    engines = get_engines()
    engine_cfg = engines.get(engine, {})
    wf_id = engine_cfg.get("default_workflow", "")
    if not wf_id:
        # 降级：找 registry 中该引擎的第一个已启用工作流
        for w in get_enabled_workflows():
            if w.get("engine") == engine:
                return w["id"]
    return wf_id


def get_default_workflow_id() -> str:
    """返回默认引擎的默认工作流 ID。"""
    return resolve_workflow_id(get_default_engine())


async def execute(workflow_id: str, prompt: str, width: int, height: int) -> dict[str, Any]:
    """
    统一执行入口。
    根据注册表中的 engine 类型分发到 comfyui_service 或 rh_service。
    前端不需要知道分发细节。
    返回 { task_id: str, engine: str }
    """
    wf = get_workflow_by_id(workflow_id)
    if not wf:
        raise ValueError(f"工作流不存在: {workflow_id}")
    if not wf.get("enabled"):
        raise ValueError(f"工作流已禁用: {workflow_id}")

    engine = wf.get("engine", "")

    if engine == "comfyui_local":
        return await _execute_comfyui(wf, prompt, width, height)
    elif engine == "runninghub":
        return await _execute_runninghub(wf, prompt, width, height)
    else:
        raise ValueError(f"未知引擎类型: {engine}")


async def get_task_status(task_id: str, engine: str) -> dict[str, Any]:
    """
    统一状态查询。
    前端只需传 task_id + engine（execute 返回值），无需了解引擎细节。
    返回归一化结构: { status, progress?, output? }
    """
    if engine == "comfyui_local":
        return await _get_comfyui_status(task_id)
    elif engine == "runninghub":
        return await _get_rh_status(task_id)
    else:
        return {"status": "error", "error": f"未知引擎: {engine}"}


async def _execute_comfyui(wf: dict, prompt: str, width: int, height: int) -> dict[str, Any]:
    """ComfyUI 本地执行。"""
    comfyui_id = wf.get("comfyui_workflow_id", "")
    workflow_json = await comfyui_service.get_workflow(comfyui_id)
    if not workflow_json:
        raise ValueError(f"ComfyUI 工作流文件不存在: {comfyui_id}")
    result = await comfyui_service.execute_workflow(
        workflow_json,
        {"prompt": prompt, "width": str(width), "height": str(height)},
    )
    logger.info("ComfyUI 工作流已提交: workflow=%s, prompt_id=%s", comfyui_id, result.get("prompt_id"))
    return {"task_id": result["prompt_id"], "engine": "comfyui_local"}


async def _execute_runninghub(wf: dict, prompt: str, width: int, height: int) -> dict[str, Any]:
    """RunningHub 云端执行。"""
    rh_id = wf.get("rh_workflow_id", "")
    if not rh_id:
        raise ValueError(f"RunningHub 工作流 ID 未配置: {wf.get('id')}")
    mapping = wf.get("rh_node_mapping", {})

    node_params = []
    if "prompt" in mapping:
        m = mapping["prompt"]
        node_params.append({"nodeId": m["node_id"], "fieldName": m["field_name"], "fieldValue": prompt})
    if "width" in mapping:
        m = mapping["width"]
        node_params.append({"nodeId": m["node_id"], "fieldName": m["field_name"], "fieldValue": str(width)})
    if "height" in mapping:
        m = mapping["height"]
        node_params.append({"nodeId": m["node_id"], "fieldName": m["field_name"], "fieldValue": str(height)})

    result = await rh_service.create_task(rh_id, node_params)
    logger.info("RunningHub 工作流已提交: workflow=%s, task_id=%s", wf.get("id"), result.get("task_id"))
    return {"task_id": result["task_id"], "engine": "runninghub"}


async def _get_comfyui_status(prompt_id: str) -> dict[str, Any]:
    """查询 ComfyUI 任务状态，归一化为统一结构。"""
    try:
        url = comfyui_service._get_comfyui_url()
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{url}/history/{prompt_id}")
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    history = data[prompt_id]
                    status_info = history.get("status", {})
                    if status_info.get("completed", False):
                        # 提取输出图片 URL
                        outputs = history.get("outputs", {})
                        images = []
                        for node_output in outputs.values():
                            for img in node_output.get("images", []):
                                filename = img.get("filename", "")
                                subfolder = img.get("subfolder", "")
                                images.append(f"{url}/view?filename={filename}&subfolder={subfolder}&type=output")
                        return {"status": "completed", "output": images}
                    if status_info.get("status_str") == "error":
                        return {"status": "failed", "error": str(status_info.get("messages", []))}
                # 任务存在但未完成
                return {"status": "running"}
            # 任务尚未出现在 history 中
            return {"status": "running"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _get_rh_status(task_id: str) -> dict[str, Any]:
    """查询 RunningHub 任务状态，归一化为统一结构。"""
    result = await rh_service.get_task_status(task_id)
    raw_status = result.get("status", "")

    # 归一化 RunningHub 状态
    if raw_status == "COMPLETED":
        return {"status": "completed", "output": result.get("output", []), "progress": 100}
    elif raw_status in ("FAILED", "CANCELLED"):
        return {"status": "failed", "error": result.get("error", raw_status)}
    elif raw_status == "error":
        return {"status": "error", "error": result.get("error", "")}
    else:
        return {"status": "running", "progress": result.get("progress", 0)}
