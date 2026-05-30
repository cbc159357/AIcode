"""归档 + 子任务管理服务 — 文件系统 CRUD。"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from core.config import get_config

logger = logging.getLogger(__name__)

MEDIA_EXTENSIONS = {
    "image": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"},
    "audio": {".wav", ".mp3", ".flac", ".ogg", ".m4a"},
    "video": {".mp4", ".webm", ".avi", ".mov", ".mkv"},
}


def _data_dir() -> Path:
    """归档数据根目录。"""
    config = get_config()
    base = config.get("data_dir", "data")
    return Path(base) / "archives"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─── Archive CRUD ────────────────────────────────────────────


def list_archives() -> list[dict[str, Any]]:
    """列出所有归档，按更新时间倒序。"""
    root = _data_dir()
    if not root.exists():
        return []
    archives = []
    for d in root.iterdir():
        if not d.is_dir():
            continue
        meta_file = d / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            meta["task_count"] = _count_tasks(d)
            archives.append(meta)
    archives.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return archives


def get_archive(archive_id: str) -> dict[str, Any] | None:
    """获取单个归档元数据。"""
    meta_file = _data_dir() / archive_id / "meta.json"
    if not meta_file.exists():
        return None
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    meta["task_count"] = _count_tasks(_data_dir() / archive_id)
    return meta


def create_archive(name: str) -> dict[str, Any]:
    """创建归档，返回元数据。"""
    archive_id = f"arc_{int(time.time() * 1000)}"
    archive_dir = _data_dir() / archive_id
    _ensure_dir(archive_dir / "tasks")
    now = _now_iso()
    meta = {
        "id": archive_id,
        "name": name,
        "created_at": now,
        "updated_at": now,
    }
    (archive_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("创建归档: id=%s, name=%s", archive_id, name)
    return {**meta, "task_count": 0}


def rename_archive(archive_id: str, name: str) -> dict[str, Any] | None:
    """重命名归档。"""
    meta_file = _data_dir() / archive_id / "meta.json"
    if not meta_file.exists():
        return None
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    meta["name"] = name
    meta["updated_at"] = _now_iso()
    meta_file.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def delete_archive(archive_id: str) -> bool:
    """删除归档及其所有子任务。"""
    import shutil
    archive_dir = _data_dir() / archive_id
    if not archive_dir.exists():
        return False
    shutil.rmtree(archive_dir)
    logger.info("删除归档: id=%s", archive_id)
    return True


# ─── Task CRUD ───────────────────────────────────────────────


def list_tasks(archive_id: str) -> list[dict[str, Any]]:
    """列出归档下所有子任务，按时间倒序。"""
    tasks_dir = _data_dir() / archive_id / "tasks"
    if not tasks_dir.exists():
        return []
    tasks = []
    for d in tasks_dir.iterdir():
        if not d.is_dir():
            continue
        meta_file = d / "meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            meta["media_count"] = _count_media(d)
            tasks.append(meta)
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return tasks


def create_task(archive_id: str, config_snapshot: dict | None = None) -> dict[str, Any]:
    """创建子任务目录，返回元数据。"""
    from datetime import datetime
    now = datetime.now()
    task_id = f"task_{now.strftime('%Y%m%d_%H%M%S')}"
    task_dir = _data_dir() / archive_id / "tasks" / task_id
    _ensure_dir(task_dir / "images")
    _ensure_dir(task_dir / "audio")
    _ensure_dir(task_dir / "video")
    meta = {
        "id": task_id,
        "created_at": _now_iso(),
        "status": "running",
        "pipeline_config": config_snapshot or {},
    }
    (task_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 更新归档的 updated_at
    _touch_archive(archive_id)
    logger.info("创建子任务: archive=%s, task=%s", archive_id, task_id)
    return {**meta, "media_count": {"image": 0, "audio": 0, "video": 0}}


def update_task_status(archive_id: str, task_id: str, status: str) -> bool:
    """更新子任务状态。"""
    meta_file = _data_dir() / archive_id / "tasks" / task_id / "meta.json"
    if not meta_file.exists():
        return False
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    meta["status"] = status
    meta_file.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return True


def delete_task(archive_id: str, task_id: str) -> bool:
    """删除子任务。"""
    import shutil
    task_dir = _data_dir() / archive_id / "tasks" / task_id
    if not task_dir.exists():
        return False
    shutil.rmtree(task_dir)
    _touch_archive(archive_id)
    logger.info("删除子任务: archive=%s, task=%s", archive_id, task_id)
    return True


# ─── Media 查询 ──────────────────────────────────────────────


def list_media(archive_id: str, task_id: str) -> list[dict[str, Any]]:
    """列出子任务下所有媒体文件。"""
    task_dir = _data_dir() / archive_id / "tasks" / task_id
    if not task_dir.exists():
        return []
    media_items = []
    for subdir in ("images", "audio", "video"):
        dir_path = task_dir / subdir
        if not dir_path.exists():
            continue
        media_type = _dir_to_type(subdir)
        for f in sorted(dir_path.iterdir()):
            if f.is_file() and _get_media_type(f.suffix) == media_type:
                media_items.append({
                    "type": media_type,
                    "filename": f.name,
                    "path": f"{archive_id}/tasks/{task_id}/{subdir}/{f.name}",
                    "size": f.stat().st_size,
                })
    return media_items


def get_media_abs_path(relative_path: str) -> Path | None:
    """将相对路径转为绝对路径（安全检查）。"""
    abs_path = (_data_dir() / relative_path).resolve()
    # 防止路径穿越
    if not str(abs_path).startswith(str(_data_dir().resolve())):
        return None
    if not abs_path.exists() or not abs_path.is_file():
        return None
    return abs_path


# ─── 内部工具 ────────────────────────────────────────────────


def _count_tasks(archive_dir: Path) -> int:
    tasks_dir = archive_dir / "tasks"
    if not tasks_dir.exists():
        return 0
    return sum(1 for d in tasks_dir.iterdir() if d.is_dir())


def _count_media(task_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {"image": 0, "audio": 0, "video": 0}
    for subdir, media_type in [("images", "image"), ("audio", "audio"), ("video", "video")]:
        dir_path = task_dir / subdir
        if dir_path.exists():
            counts[media_type] = sum(
                1 for f in dir_path.iterdir()
                if f.is_file() and _get_media_type(f.suffix) == media_type
            )
    return counts


def _get_media_type(suffix: str) -> str:
    s = suffix.lower()
    for media_type, exts in MEDIA_EXTENSIONS.items():
        if s in exts:
            return media_type
    return "unknown"


def _dir_to_type(subdir: str) -> str:
    return {"images": "image", "audio": "audio", "video": "video"}.get(subdir, "unknown")


def _touch_archive(archive_id: str) -> None:
    meta_file = _data_dir() / archive_id / "meta.json"
    if meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta["updated_at"] = _now_iso()
        meta_file.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
