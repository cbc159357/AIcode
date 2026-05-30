"""RunningHub 路由 — 连接测试 / 工作流管理 / 任务调度 / 配置。"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from core.config import get_config
from core import runninghub_client as rh
from services import model_cache_service
from services import workflow_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/rh", tags=["RunningHub"])

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


# ── 请求模型 ─────────────────────────────────────────────


class TestKeyRequest(BaseModel):
    api_key: str

class FetchWorkflowRequest(BaseModel):
    workflow_id: str

class AnalyzeRequest(BaseModel):
    workflow_id: str
    nodes_json: dict[str, Any] | None = None

class CreateTaskRequest(BaseModel):
    workflow_id: str
    node_info_list: list[dict] | None = None

class TaskStatusRequest(BaseModel):
    task_id: str

class SaveWorkflowRequest(BaseModel):
    workflow_id: str
    name: str
    description: str = ""
    group: str = ""
    raw_nodes: dict[str, Any] | None = None
    analyzed_params: list[dict] | None = None

class UpdateImageInputsRequest(BaseModel):
    image_inputs: list[dict]

class SaveConfigRequest(BaseModel):
    keys: dict[str, str] | None = None
    active_key_type: str | None = None
    proxy: str | None = None
    proxy_enabled: bool | None = None
    model_cache_strategy: str | None = None  # manual | startup | scheduled
    model_cache_interval_hours: int | None = None


class ModelOverrideItem(BaseModel):
    nodeId: str
    fieldName: str
    value: str


# ── 连接测试 ─────────────────────────────────────────────


@router.post("/test")
async def test_connection(body: TestKeyRequest):
    """测试 API Key 连通性。"""
    return await asyncio.to_thread(rh.test_connection, body.api_key)


# ── 工作流拉取 & 分析 ────────────────────────────────────


@router.post("/workflow/fetch")
async def fetch_workflow(body: FetchWorkflowRequest):
    """获取工作流节点 JSON。"""
    return await asyncio.to_thread(rh.fetch_workflow_json, body.workflow_id)


@router.post("/workflow/analyze")
async def analyze_workflow(body: AnalyzeRequest):
    """规则解析工作流可调参数。"""
    nodes_json = body.nodes_json
    if not nodes_json:
        fetch_result = await asyncio.to_thread(
            rh.fetch_workflow_json, body.workflow_id)
        if not fetch_result.get("ok"):
            return {"ok": False, "params": [],
                    "message": fetch_result.get("message", "获取工作流失败")}
        nodes_json = fetch_result.get("data")
    if not nodes_json:
        return {"ok": False, "params": [], "message": "节点数据为空"}

    params = rh.analyze_nodes_by_rules(nodes_json)
    return {"ok": True, "params": params,
            "nodeCount": len(nodes_json), "paramCount": len(params)}


# ── 任务调度 ─────────────────────────────────────────────


@router.post("/task/create")
async def create_task(body: CreateTaskRequest):
    """提交 RunningHub 任务。"""
    return await asyncio.to_thread(
        rh.create_task, body.workflow_id, body.node_info_list)


@router.post("/task/status")
async def task_status(body: TaskStatusRequest):
    """查询任务状态。"""
    return await asyncio.to_thread(rh.poll_task_status, body.task_id)


@router.post("/task/cancel")
async def cancel_task(body: TaskStatusRequest):
    """取消任务。"""
    return await asyncio.to_thread(rh.cancel_task, body.task_id)


# ── 本地工作流 CRUD ──────────────────────────────────────


@router.get("/workflows")
async def list_saved_workflows():
    """获取本地已保存的工作流配置列表。"""
    items = await asyncio.to_thread(workflow_store.list_workflows)
    return {"ok": True, "items": items}


@router.post("/workflow/save")
async def save_workflow(body: SaveWorkflowRequest):
    """保存/更新工作流配置到本地。"""
    await asyncio.to_thread(
        workflow_store.save_workflow,
        body.workflow_id, body.name, body.description, body.group,
        body.raw_nodes, body.analyzed_params,
    )
    return {"ok": True, "message": "保存成功"}


@router.put("/workflow/{workflow_id}/image-inputs")
async def update_image_inputs(workflow_id: str, body: UpdateImageInputsRequest):
    """保存用户确认后的图片输入语义标注。"""
    try:
        await asyncio.to_thread(workflow_store.update_image_inputs,
                                 workflow_id, body.image_inputs)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"ok": True, "message": "标注已保存"}


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """上传图片到 RunningHub，返回可用于 nodeInfoList 的 fileName。"""
    content = await file.read()
    result = await asyncio.to_thread(
        rh.upload_image, content, file.filename or "upload.png")
    return result


@router.get("/workflow/{workflow_id}")
async def get_saved_workflow(workflow_id: str):
    """获取本地保存的工作流详情。"""
    try:
        data = await asyncio.to_thread(workflow_store.get_workflow, workflow_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"ok": True, "data": data}


@router.delete("/workflow/{workflow_id}")
async def delete_saved_workflow(workflow_id: str):
    """删除本地保存的工作流。"""
    await asyncio.to_thread(workflow_store.delete_workflow, workflow_id)
    return {"ok": True, "message": "已删除"}


@router.patch("/workflows/{workflow_id}/models")
async def apply_model_overrides(
    workflow_id: str, overrides: list[ModelOverrideItem]
):
    """将模型替换应用到工作流参数，并重新附加 modelMeta。"""
    raw = [{"nodeId": o.nodeId, "fieldName": o.fieldName, "value": o.value}
           for o in overrides]
    try:
        count = await asyncio.to_thread(workflow_store.apply_model_overrides,
                                        workflow_id, raw)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"ok": True, "message": f"已应用 {count} 条模型替换"}


# ── 配置管理 ─────────────────────────────────────────────


@router.get("/config")
async def get_rh_config():
    """获取 RH 配置（Key 脱敏）。"""
    cfg = get_config().get("runninghub", {})
    keys_raw = cfg.get("keys", {})
    has_keys = {k: bool(v) for k, v in keys_raw.items()}
    masked = {k: (v[:4] + "****" if len(v) > 4 else "****") if v else ""
              for k, v in keys_raw.items()}
    return {
        "ok": True,
        "config": {
            "active_key_type": cfg.get("active_key_type", "consumer"),
            "keys": masked,
            "has_keys": has_keys,
            "proxy": cfg.get("proxy", ""),
            "proxy_enabled": cfg.get("proxy_enabled", False),
        },
    }


@router.post("/config/save")
async def save_rh_config(body: SaveConfigRequest):
    """保存 RH 配置到 config.yaml。"""
    if not _CONFIG_PATH.exists():
        raise HTTPException(status_code=500, detail="配置文件不存在")

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    rh_cfg = cfg.setdefault("runninghub", {})
    if body.keys is not None:
        existing_keys = rh_cfg.setdefault("keys", {})
        for k, v in body.keys.items():
            if v:
                existing_keys[k] = v
    if body.active_key_type is not None:
        rh_cfg["active_key_type"] = body.active_key_type
    if body.proxy is not None:
        rh_cfg["proxy"] = body.proxy
    if body.proxy_enabled is not None:
        rh_cfg["proxy_enabled"] = body.proxy_enabled
    mc = rh_cfg.setdefault("model_cache", {})
    if body.model_cache_strategy is not None:
        mc["refresh_strategy"] = body.model_cache_strategy
    if body.model_cache_interval_hours is not None:
        mc["refresh_interval_hours"] = body.model_cache_interval_hours

    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False)

    from core.config import load_config
    load_config()

    return {"ok": True, "message": "配置已保存"}


# ── 模型元数据缓存 ────────────────────────────────────────


_refresh_task: asyncio.Task | None = None


@router.get("/model-cache/status")
async def get_model_cache_status():
    """返回模型缓存状态 { exists, totalCount, fetchedAt, refreshing }。"""
    status = model_cache_service.get_cache_status()
    status["refreshing"] = _refresh_task is not None and not _refresh_task.done()
    return status


async def _run_refresh(api_key: str, proxy: str | None) -> None:
    """后台刷新任务体。"""
    try:
        await asyncio.to_thread(model_cache_service.fetch_and_save, api_key, proxy)
        logger.info("[model-cache] 后台刷新完成")
    except Exception as e:
        logger.exception("[model-cache] 后台刷新失败: %s", e)


@router.post("/model-cache/refresh")
async def refresh_model_cache():
    """异步启动模型缓存全量刷新，立即返回，进度通过 /status 查询。"""
    global _refresh_task
    if _refresh_task is not None and not _refresh_task.done():
        return {"ok": False, "message": "刷新任务已在进行中"}
    api_key = rh._get_active_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key 未配置")
    proxy = rh._get_proxy()
    _refresh_task = asyncio.create_task(_run_refresh(api_key, proxy))
    return {"ok": True, "message": "刷新已在后台启动，请通过 /status 查询进度"}


@router.get("/models/search")
async def search_models(
    q: str | None = None,
    base_model: str | None = None,
    resource_type: str | None = None,
    limit: int = 30,
):
    """在缓存中搜索模型，支持 baseModel/resourceType 精确匹配 + 文件名/名称模糊搜索。"""
    items = model_cache_service.search_models(
        base_model=base_model, resource_type=resource_type, q=q, limit=limit)
    return {"ok": True, "items": items}


@router.get("/models/suggest")
async def suggest_compatible_models(
    filename: str,
    resource_type: str | None = None,
):
    """根据文件名查出 baseModel，返回同族同类型的推荐候选列表。"""
    meta = model_cache_service.get_model_meta(filename)
    base_model = meta["baseModel"] if meta else None
    candidates = model_cache_service.search_models(
        base_model=base_model, resource_type=resource_type, limit=30)
    return {
        "ok": True,
        "sourceBaseModel": base_model,
        "sourceMeta": meta,
        "candidates": candidates,
    }
