"""工作流路由 — 列表/详情/执行/状态查询。"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import workflow_service

router = APIRouter(prefix="/api/v1/workflow", tags=["Workflow"])


@router.get("/engines")
async def list_engines():
    """返回引擎模式列表（前端下拉框用）。"""
    engines = workflow_service.get_engines()
    default_engine = workflow_service.get_default_engine()
    items = [
        {
            "id": eid,
            "name": ecfg.get("name", eid),
            "description": ecfg.get("description", ""),
            "has_workflow": bool(ecfg.get("default_workflow")),
        }
        for eid, ecfg in engines.items()
    ]
    return {"engines": items, "default": default_engine}


@router.get("/list")
async def list_workflows(category: str | None = None):
    """列出已启用的工作流（前端用于展示列表）。"""
    workflows = workflow_service.get_enabled_workflows(category)
    default_id = workflow_service.get_default_workflow_id()
    items = [
        {
            "id": w["id"],
            "name": w["name"],
            "category": w.get("category", ""),
            "engine": w.get("engine", ""),
            "default_size": w.get("default_size", ""),
            "description": w.get("description", ""),
        }
        for w in workflows
    ]
    return {"workflows": items, "default": default_id}


@router.get("/active")
async def get_active():
    """返回默认引擎 + 对应工作流。"""
    engine = workflow_service.get_default_engine()
    workflow_id = workflow_service.resolve_workflow_id(engine)
    return {"engine": engine, "workflow_id": workflow_id}


class ExecuteRequest(BaseModel):
    engine: str = ""        # 引擎模式（优先）
    workflow_id: str = ""   # 具体工作流 ID（可选，缺省时用引擎默认）
    prompt: str
    width: int = 720
    height: int = 1280


@router.post("/execute")
async def execute(req: ExecuteRequest):
    """统一执行入口 — 前端传 engine + prompt + 尺寸。"""
    wf_id = req.workflow_id
    if not wf_id and req.engine:
        wf_id = workflow_service.resolve_workflow_id(req.engine)
    if not wf_id:
        wf_id = workflow_service.get_default_workflow_id()
    if not wf_id:
        raise HTTPException(status_code=400, detail="未配置可用的工作流")
    try:
        result = await workflow_service.execute(wf_id, req.prompt, req.width, req.height)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/task/status")
async def task_status(task_id: str, engine: str):
    """统一任务状态查询 — 前端传 task_id + engine（execute 返回值）。"""
    result = await workflow_service.get_task_status(task_id, engine)
    return result
