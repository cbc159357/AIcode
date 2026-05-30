"""ComfyUI 路由 — 工作流管理 + 任务执行。"""

import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services import comfyui_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/comfyui", tags=["ComfyUI"])


class ExecuteRequest(BaseModel):
    workflow_id: str
    replacements: dict | None = None


class StatusResponse(BaseModel):
    status: str
    outputs: dict | None = None
    error: str | None = None


@router.get("/health")
async def health():
    """检查 ComfyUI 连接状态。"""
    online = await comfyui_service.check_health()
    return {"status": "connected" if online else "disconnected"}


@router.get("/workflows")
async def list_workflows():
    """列出可用工作流。"""
    workflows = await comfyui_service.list_workflows()
    return {"workflows": workflows}


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """获取工作流详情。"""
    wf = await comfyui_service.get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"workflow": wf}


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """上传图片到 ComfyUI。"""
    data = await file.read()
    filename = file.filename or "upload.png"
    result = await comfyui_service.upload_image(data, filename)
    if result is None:
        raise HTTPException(status_code=502, detail="上传失败")
    return {"filename": result}


@router.post("/execute")
async def execute(req: ExecuteRequest):
    """提交工作流执行。"""
    workflow = await comfyui_service.get_workflow(req.workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="工作流不存在")
    try:
        result = await comfyui_service.execute_workflow(workflow, req.replacements)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/status/{prompt_id}")
async def get_status(prompt_id: str):
    """查询任务状态（非阻塞轮询一次）。"""
    url = comfyui_service._get_comfyui_url()
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{url}/history/{prompt_id}")
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    history = data[prompt_id]
                    status_info = history.get("status", {})
                    if status_info.get("completed", False):
                        return {"status": "completed", "outputs": history.get("outputs", {})}
                    if status_info.get("status_str") == "error":
                        return {"status": "error"}
                return {"status": "running"}
            return {"status": "unknown"}
    except httpx.HTTPError:
        return {"status": "error", "error": "无法连接 ComfyUI"}
