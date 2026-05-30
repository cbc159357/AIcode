"""ComfyUI 服务层 — WebSocket 客户端 + 任务管理。"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any

import httpx

from core.config import get_config

logger = logging.getLogger(__name__)

WORKFLOWS_DIR = Path(__file__).parent.parent / "data" / "workflows"


def _get_comfyui_url() -> str:
    """获取 ComfyUI 服务地址。"""
    config = get_config()
    return config.get("services", {}).get("comfyui", {}).get("url", "http://127.0.0.1:8188")


async def check_health() -> bool:
    """检查 ComfyUI 是否在线。"""
    url = _get_comfyui_url()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{url}/system_stats")
            return resp.status_code == 200
    except httpx.HTTPError:
        return False


async def list_workflows() -> list[dict[str, str]]:
    """列出本地存储的工作流 JSON 文件。"""
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    workflows = []
    for f in WORKFLOWS_DIR.glob("*.json"):
        workflows.append({"id": f.stem, "name": f.stem, "path": str(f)})
    return workflows


async def get_workflow(workflow_id: str) -> dict[str, Any] | None:
    """读取指定工作流 JSON。"""
    filepath = WORKFLOWS_DIR / f"{workflow_id}.json"
    if not filepath.exists():
        return None
    return json.loads(filepath.read_text(encoding="utf-8"))


async def upload_image(image_data: bytes, filename: str) -> str | None:
    """上传图片到 ComfyUI input 目录。"""
    url = _get_comfyui_url()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{url}/upload/image",
                files={"image": (filename, image_data, "image/png")},
                data={"overwrite": "true"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("name")
    except httpx.HTTPError as e:
        logger.error("ComfyUI 图片上传失败: %s", str(e))
        return None


async def execute_workflow(
    workflow: dict[str, Any],
    replacements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    提交工作流到 ComfyUI 执行。
    返回 {"prompt_id": str, "status": "queued"}
    """
    url = _get_comfyui_url()
    client_id = str(uuid.uuid4())

    # 应用参数替换
    if replacements:
        workflow_str = json.dumps(workflow)
        for key, value in replacements.items():
            workflow_str = workflow_str.replace(f"{{{{{key}}}}}", str(value))
        workflow = json.loads(workflow_str)

    payload = {"prompt": workflow, "client_id": client_id}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{url}/prompt", json=payload)
            resp.raise_for_status()
            data = resp.json()
            prompt_id = data.get("prompt_id", "")
            logger.info("ComfyUI 任务已提交: prompt_id=%s", prompt_id)
            return {"prompt_id": prompt_id, "client_id": client_id, "status": "queued"}
    except httpx.HTTPError as e:
        logger.error("ComfyUI 任务提交失败: %s", str(e))
        raise RuntimeError(f"ComfyUI 任务提交失败: {e}") from e


async def poll_status(prompt_id: str, timeout: int = 300) -> dict[str, Any]:
    """轮询任务状态直到完成或超时。"""
    url = _get_comfyui_url()
    start = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start < timeout:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{url}/history/{prompt_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    if prompt_id in data:
                        history = data[prompt_id]
                        status = history.get("status", {})
                        if status.get("completed", False):
                            outputs = history.get("outputs", {})
                            return {"status": "completed", "outputs": outputs}
                        if status.get("status_str") == "error":
                            return {"status": "error", "error": status.get("messages", [])}
        except httpx.HTTPError:
            pass
        await asyncio.sleep(2)

    return {"status": "timeout"}


async def get_output_images(prompt_id: str) -> list[str]:
    """从完成的任务中提取输出图片 URL。"""
    url = _get_comfyui_url()
    result = await poll_status(prompt_id)
    if result["status"] != "completed":
        return []

    images = []
    for node_output in result.get("outputs", {}).values():
        for img in node_output.get("images", []):
            filename = img.get("filename", "")
            subfolder = img.get("subfolder", "")
            img_url = f"{url}/view?filename={filename}&subfolder={subfolder}&type=output"
            images.append(img_url)
    return images
