"""
WorkflowStore — RunningHub 工作流本地 JSON CRUD。

封装所有文件系统操作，路由层只调用此服务，不直接接触路径与 JSON 序列化。
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from core import workflow_analyzer as wa
from core import image_inferrer as ii
from services import model_cache_service

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data" / "runninghub" / "workflows"


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _path(workflow_id: str) -> Path:
    return _DATA_DIR / f"{workflow_id}.json"


def _read(workflow_id: str) -> dict:
    p = _path(workflow_id)
    if not p.exists():
        raise FileNotFoundError(workflow_id)
    return json.loads(p.read_text(encoding="utf-8"))


def _write(workflow_id: str, data: dict) -> None:
    _ensure_dir()
    _path(workflow_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── 公开 API ──────────────────────────────────────────────


def list_workflows() -> list[dict]:
    """列出所有已保存的工作流摘要。"""
    _ensure_dir()
    items = []
    for f in sorted(_DATA_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            image_inputs = data.get("imageInputs", [])
            visible_inputs = [i for i in image_inputs if i.get("role") != "internal"]
            items.append({
                "workflowId": data.get("workflowId", f.stem),
                "name": data.get("name", f.stem),
                "description": data.get("description", ""),
                "group": data.get("group", ""),
                "fetchedAt": data.get("fetchedAt", ""),
                "paramCount": len(data.get("analyzedParams", [])),
                "nodeCount": len(data.get("rawNodes", {})),
                "imageInputCount": len(visible_inputs),
                "imageInputsAnnotated": data.get("imageInputsAnnotated", False),
            })
        except Exception:
            continue
    return items


def get_workflow(workflow_id: str) -> dict:
    """获取工作流完整数据，不存在则抛 FileNotFoundError。"""
    return _read(workflow_id)


def save_workflow(
    workflow_id: str,
    name: str,
    description: str = "",
    group: str = "",
    raw_nodes: dict[str, Any] | None = None,
    analyzed_params: list[dict] | None = None,
) -> None:
    """保存/更新工作流配置，raw_nodes 传入时重新分析所有参数。"""
    existing: dict = {}
    try:
        existing = _read(workflow_id)
    except FileNotFoundError:
        pass

    existing.update({"workflowId": workflow_id, "name": name,
                      "description": description, "group": group})

    if raw_nodes is not None:
        existing["rawNodes"] = raw_nodes
        analyzed = wa.analyze_nodes_by_rules(raw_nodes)
        existing["analyzedParams"] = analyzed
        existing["paramCount"] = len(analyzed)
        existing["imageInputs"] = ii.infer_image_inputs(raw_nodes)
        existing["imageInputsAnnotated"] = False
        img_node_ids = {i["nodeId"] for i in existing["imageInputs"]}
        existing["paramGroups"] = wa.group_params_by_function(
            raw_nodes, analyzed, img_node_ids)
        existing["modelGroups"] = wa.find_model_groups(raw_nodes)
        by_filename = model_cache_service.load_cache().get("byFileName", {})
        if by_filename:
            wa.annotate_params_with_meta(analyzed, by_filename)
        logger.info("[imageInputs] %d 个, [paramGroups] %d 组, [modelGroups] %d 组",
                    len(existing["imageInputs"]), len(existing["paramGroups"]),
                    len(existing["modelGroups"]))
    elif analyzed_params is not None:
        existing["analyzedParams"] = analyzed_params

    existing["fetchedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(workflow_id, existing)
    logger.info("工作流已保存: %s", workflow_id)


def update_image_inputs(workflow_id: str, image_inputs: list[dict]) -> None:
    """保存用户确认的图片输入语义标注。"""
    data = _read(workflow_id)
    data["imageInputs"] = image_inputs
    data["imageInputsAnnotated"] = True
    _write(workflow_id, data)
    logger.info("[imageInputs] 标注已保存: %s, %d 个", workflow_id, len(image_inputs))


def apply_model_overrides(
    workflow_id: str,
    overrides: list[dict],
) -> int:
    """将模型替换应用到 analyzedParams，重新附加 modelMeta，返回实际替换条数。"""
    data = _read(workflow_id)
    index = {f"{o['nodeId']}::{o['fieldName']}": o["value"] for o in overrides}
    for param in data.get("analyzedParams", []):
        key = f"{param.get('nodeId')}::{param.get('fieldName')}"
        if key in index:
            param["currentValue"] = index[key]
    by_filename = model_cache_service.load_cache().get("byFileName", {})
    if by_filename:
        wa.annotate_params_with_meta(data["analyzedParams"], by_filename)
    _write(workflow_id, data)
    logger.info("[model-override] 已应用 %d 条替换: %s", len(overrides), workflow_id)
    return len(overrides)


def delete_workflow(workflow_id: str) -> None:
    """删除工作流，文件不存在时静默跳过。"""
    p = _path(workflow_id)
    if p.exists():
        p.unlink()
