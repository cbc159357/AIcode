"""归档管理路由 — 归档 CRUD + 子任务 + 媒体文件服务。"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services import archive_service

router = APIRouter(prefix="/api/v1/archives", tags=["Archives"])


# ─── 请求模型 ────────────────────────────────────────────────


class ArchiveCreateRequest(BaseModel):
    name: str


class ArchiveRenameRequest(BaseModel):
    name: str


class TaskCreateRequest(BaseModel):
    pipeline_config: dict | None = None


class TaskStatusRequest(BaseModel):
    status: str


# ─── Archive 端点 ────────────────────────────────────────────


@router.get("")
async def list_archives():
    """列出所有归档。"""
    return {"archives": archive_service.list_archives()}


@router.post("")
async def create_archive(req: ArchiveCreateRequest):
    """新建归档。"""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="归档名称不能为空")
    return archive_service.create_archive(req.name.strip())


@router.put("/{archive_id}")
async def rename_archive(archive_id: str, req: ArchiveRenameRequest):
    """重命名归档。"""
    result = archive_service.rename_archive(archive_id, req.name.strip())
    if not result:
        raise HTTPException(status_code=404, detail="归档不存在")
    return result


@router.delete("/{archive_id}")
async def delete_archive(archive_id: str):
    """删除归档。"""
    if not archive_service.delete_archive(archive_id):
        raise HTTPException(status_code=404, detail="归档不存在")
    return {"ok": True}


# ─── Task 端点 ───────────────────────────────────────────────


@router.get("/{archive_id}/tasks")
async def list_tasks(archive_id: str):
    """列出归档下所有子任务。"""
    return {"tasks": archive_service.list_tasks(archive_id)}


@router.post("/{archive_id}/tasks")
async def create_task(archive_id: str, req: TaskCreateRequest):
    """创建子任务（pipeline 开始时调用）。"""
    meta = archive_service.get_archive(archive_id)
    if not meta:
        raise HTTPException(status_code=404, detail="归档不存在")
    return archive_service.create_task(archive_id, req.pipeline_config)


@router.put("/{archive_id}/tasks/{task_id}/status")
async def update_task_status(archive_id: str, task_id: str, req: TaskStatusRequest):
    """更新子任务状态。"""
    if not archive_service.update_task_status(archive_id, task_id, req.status):
        raise HTTPException(status_code=404, detail="子任务不存在")
    return {"ok": True}


@router.delete("/{archive_id}/tasks/{task_id}")
async def delete_task(archive_id: str, task_id: str):
    """删除子任务。"""
    if not archive_service.delete_task(archive_id, task_id):
        raise HTTPException(status_code=404, detail="子任务不存在")
    return {"ok": True}


# ─── Media 端点 ──────────────────────────────────────────────


@router.get("/{archive_id}/tasks/{task_id}/media")
async def list_media(archive_id: str, task_id: str):
    """列出子任务下所有媒体文件。"""
    return {"media": archive_service.list_media(archive_id, task_id)}


@router.get("/media/{file_path:path}")
async def serve_media(file_path: str):
    """静态文件服务（图片/音频/视频）。"""
    abs_path = archive_service.get_media_abs_path(file_path)
    if not abs_path:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(abs_path)
