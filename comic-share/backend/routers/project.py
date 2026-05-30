"""项目路由 — 保存/渲染/导入/导出。"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.config import get_config
from services import render_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/project", tags=["Project"])


class SaveRequest(BaseModel):
    project_name: str
    shots: list[dict]


class RenderRequest(BaseModel):
    project_name: str
    shots: list[dict]
    resolution: str = "720x1280"
    enable_subtitle: bool = True
    enable_bgm: bool = True
    bgm_path: str | None = None


def _get_output_dir() -> Path:
    config = get_config()
    base = config.get("output", {}).get("base_dir", "data/output")
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("/save")
async def save_project(req: SaveRequest):
    """保存项目 JSON。"""
    output_dir = _get_output_dir()
    filepath = output_dir / f"{req.project_name}.json"
    filepath.write_text(
        json.dumps({"project_name": req.project_name, "shots": req.shots}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"path": str(filepath)}


@router.post("/render")
async def render(req: RenderRequest):
    """渲染视频。"""
    output_name = f"{req.project_name}.mp4"
    result = await render_service.render_video(
        shots=req.shots,
        output_name=output_name,
        enable_subtitle=req.enable_subtitle,
        enable_bgm=req.enable_bgm,
        bgm_path=req.bgm_path,
        resolution=req.resolution,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="视频渲染失败")
    return {"path": result}


@router.get("/output/{filename}")
async def get_output(filename: str):
    """下载产物文件。"""
    output_dir = _get_output_dir()
    filepath = output_dir / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(filepath))


@router.post("/export")
async def export_project(req: SaveRequest):
    """导出项目为 JSON。"""
    return {"project_name": req.project_name, "shots": req.shots}


@router.post("/import")
async def import_project(data: dict):
    """导入项目 JSON。"""
    if "shots" not in data:
        raise HTTPException(status_code=400, detail="缺少 shots 字段")
    return {"project_name": data.get("project_name", "imported"), "shots": data["shots"]}
