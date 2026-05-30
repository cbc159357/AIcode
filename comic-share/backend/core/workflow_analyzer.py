"""
ComfyUI 工作流分析引擎 — 节点参数规则解析、功能分组、模型联动组、元数据注入。

所有函数均为纯函数（无 I/O），可独立测试。
"""

from typing import Any

# ── 节点类型映射表 ────────────────────────────────────────

NODE_TYPE_MAP: dict[str, dict[str, dict]] = {
    "CLIPTextEncode": {
        "text": {"label": "提示词", "type": "text", "priority": "high"},
    },
    "KSampler": {
        "seed":    {"label": "随机种子", "type": "number", "priority": "medium",
                    "min": 0, "max": 999999999999999},
        "steps":   {"label": "采样步数", "type": "number", "priority": "medium",
                    "min": 1, "max": 100},
        "cfg":     {"label": "CFG 引导强度", "type": "number", "priority": "medium",
                    "min": 1, "max": 30, "step": 0.5},
        "denoise": {"label": "去噪强度", "type": "number", "priority": "medium",
                    "min": 0, "max": 1, "step": 0.05},
    },
    "KSamplerAdvanced": {
        "noise_seed": {"label": "随机种子", "type": "number", "priority": "medium",
                       "min": 0, "max": 999999999999999},
        "steps":      {"label": "采样步数", "type": "number", "priority": "medium",
                       "min": 1, "max": 100},
        "cfg":        {"label": "CFG 引导强度", "type": "number", "priority": "medium",
                       "min": 1, "max": 30, "step": 0.5},
    },
    "SamplerCustom": {
        "noise_seed": {"label": "随机种子", "type": "number", "priority": "medium",
                       "min": 0, "max": 999999999999999},
    },
    "EmptyLatentImage": {
        "width":      {"label": "宽度",   "type": "number", "priority": "medium",
                       "min": 64, "max": 4096, "step": 64},
        "height":     {"label": "高度",   "type": "number", "priority": "medium",
                       "min": 64, "max": 4096, "step": 64},
        "batch_size": {"label": "批次大小", "type": "number", "priority": "low",
                       "min": 1, "max": 16},
    },
    "EmptySD3LatentImage": {
        "width":  {"label": "宽度", "type": "number", "priority": "medium",
                   "min": 64, "max": 4096, "step": 64},
        "height": {"label": "高度", "type": "number", "priority": "medium",
                   "min": 64, "max": 4096, "step": 64},
    },
    "LoadImage": {
        "image": {"label": "输入图片", "type": "image", "priority": "high"},
    },
    "LoadImageFromUrl": {
        "image": {"label": "图片URL", "type": "text", "priority": "high"},
    },
    "LoraLoader": {
        "lora_name":      {"label": "LoRA 模型", "type": "text", "priority": "medium"},
        "strength_model": {"label": "LoRA 强度(模型)", "type": "number",
                           "priority": "medium", "min": -2, "max": 2, "step": 0.05},
    },
    "Seed (rgthree)": {
        "seed": {"label": "随机种子", "type": "number", "priority": "medium",
                 "min": -1, "max": 999999999999999},
    },
    "CR Prompt Text": {
        "prompt": {"label": "提示词", "type": "text", "priority": "high"},
    },
    "PrimitiveStringMultiline": {
        "value": {"label": "文本", "type": "text", "priority": "medium"},
    },
    "SaveImage": {
        "filename_prefix": {"label": "输出文件名", "type": "text", "priority": "low"},
    },
    "TTResolutionSelector": {
        "resolution": {"label": "分辨率", "type": "text", "priority": "medium"},
    },
}

_SKIP_CLASS_TYPES: set[str] = {
    "ShowText|pysssss", "PreviewAny", "easy showAnything",
    "ImpactConditionalBranch", "Any Switch (rgthree)",
    "CR Text Concatenate", "CR Text Replace",
}

_SKIP_FIELD_NAMES: set[str] = {"class_type", "control_after_generate", "group"}

_MAX_UNKNOWN_STR_LEN = 200

# ── 模型联动组常量 ─────────────────────────────────────────

_SAMPLER_CLASS_TYPES: set[str] = {
    "KSampler", "KSamplerAdvanced", "SamplerCustom",
    "BasicGuider", "CFGGuider",
}

_LOADER_KEYWORDS: tuple[str, ...] = (
    "loader", "checkpoint", "lora", "controlnet", "ipadapter",
)

MODEL_FIELD_KEYWORDS: tuple[str, ...] = ("name", "path", "ckpt", "lora")

# ── 参数功能分组定义 ──────────────────────────────────────

_GROUP_DEFINITIONS: list[tuple[str, str, bool, set[str]]] = [
    ("prompt", "提示词", False, {
        "CLIPTextEncode", "JjkText", "CR Prompt Text", "PrimitiveStringMultiline",
    }),
    ("llm", "AI 模型调用", True, {
        "RH_LLMAPI_Pro_Node", "RH_LLMAPI_Node",
    }),
    ("sampling", "采样控制", False, {
        "KSampler", "KSamplerAdvanced", "SamplerCustom",
        "Seed (rgthree)", "FluxGuidance",
    }),
    ("resolution", "分辨率", False, {
        "EmptyLatentImage", "EmptySD3LatentImage", "TTResolutionSelector",
    }),
    ("model", "模型配置", True, {
        "UNETLoader", "CLIPLoader", "VAELoader",
        "CheckpointLoaderSimple", "LoraLoader", "LoraLoaderModelOnly",
        "DualCLIPLoader", "TripleCLIPLoader",
    }),
    ("output", "输出设置", True, {
        "SaveImage", "PreviewImage", "VHS_VideoCombine", "easy imageColorMatch",
    }),
]


# ── 公开 API ──────────────────────────────────────────────


def analyze_nodes_by_rules(nodes_json: dict) -> list[dict]:
    """基于规则映射表解析节点 JSON，提取可调参数。"""
    params: list[dict] = []
    if not nodes_json or not isinstance(nodes_json, dict):
        return params

    for node_id, node_data in nodes_json.items():
        if not isinstance(node_data, dict):
            continue
        class_type = node_data.get("class_type", "")
        inputs = node_data.get("inputs", {})
        meta_info = node_data.get("_meta", {})
        node_title = meta_info.get("title", "") if isinstance(meta_info, dict) else ""
        if not isinstance(inputs, dict) or class_type in _SKIP_CLASS_TYPES:
            continue

        type_map = NODE_TYPE_MAP.get(class_type, {})
        for field_name, field_value in inputs.items():
            if isinstance(field_value, list) and len(field_value) == 2:
                continue
            meta = type_map.get(field_name)
            if meta:
                params.append({
                    "nodeId": str(node_id),
                    "fieldName": field_name,
                    "label": meta["label"],
                    "nodeTitle": node_title or class_type,
                    "type": meta["type"],
                    "currentValue": field_value,
                    "description": f"{class_type}.{field_name}",
                    "priority": meta["priority"],
                    "constraints": {k: meta[k] for k in ("min", "max", "step") if k in meta},
                })
            elif field_name not in _SKIP_FIELD_NAMES:
                _try_add_fallback(params, node_id, class_type, node_title,
                                  field_name, field_value)

    priority_order = {"high": 0, "medium": 1, "low": 2}
    params.sort(key=lambda p: priority_order.get(p["priority"], 9))
    return params


def group_params_by_function(
    nodes_json: dict,
    analyzed_params: list[dict],
    image_node_ids: set[str] | None = None,
) -> list[dict]:
    """将 analyzedParams 按 class_type 启发式分配到预定义功能组。"""
    if not nodes_json or not analyzed_params:
        return []
    exclude_ids = image_node_ids or set()
    param_node_ids = {p["nodeId"] for p in analyzed_params if p["nodeId"] not in exclude_ids}
    node_class: dict[str, str] = {
        nid: (nodes_json.get(nid, {}).get("class_type", "")
              if isinstance(nodes_json.get(nid), dict) else "")
        for nid in param_node_ids
    }
    assigned: set[str] = set()
    groups: list[dict] = []
    for gid, title, collapsed, class_set in _GROUP_DEFINITIONS:
        matched = [nid for nid in param_node_ids
                   if node_class.get(nid, "") in class_set and nid not in assigned]
        if not matched:
            continue
        assigned.update(matched)
        groups.append({"groupId": gid, "title": title,
                        "defaultCollapsed": collapsed, "nodeIds": sorted(matched)})
    remaining = sorted(param_node_ids - assigned)
    if remaining:
        groups.append({"groupId": "other", "title": "其他参数",
                        "defaultCollapsed": False, "nodeIds": remaining})
    return groups


def find_model_groups(nodes_json: dict) -> list[dict]:
    """BFS 从每个采样器节点向上找所有 Loader 节点，归为联动模型组。"""
    if not nodes_json:
        return []
    upstream_map = _build_upstream_map(nodes_json)
    groups: list[dict] = []
    for node_id, node_data in nodes_json.items():
        if not isinstance(node_data, dict):
            continue
        if node_data.get("class_type") not in _SAMPLER_CLASS_TYPES:
            continue
        visited: set[str] = {str(node_id)}
        queue: list[str] = list(upstream_map.get(str(node_id), []))
        loaders: list[str] = []
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            nd = nodes_json.get(nid, {})
            ct = nd.get("class_type", "").lower() if isinstance(nd, dict) else ""
            if any(k in ct for k in _LOADER_KEYWORDS):
                loaders.append(nid)
            queue.extend(upstream_map.get(nid, []))
        if loaders:
            groups.append({
                "groupName": f"采样模型组 #{node_id}",
                "samplerNodeId": str(node_id),
                "modelNodeIds": sorted(set(loaders)),
            })
    return groups


def annotate_params_with_meta(params: list[dict], by_filename: dict) -> None:
    """原地修改 params：标记模型字段（isModelField），命中缓存时附加 modelMeta。

    即使模型不在缓存里也打上 isModelField=True，使前端无需重复维护字段关键词正则。
    """
    for p in params:
        if not any(k in p.get("fieldName", "") for k in MODEL_FIELD_KEYWORDS):
            continue
        p["isModelField"] = True
        meta = by_filename.get(str(p.get("currentValue", "")))
        if meta:
            p["modelMeta"] = meta


# ── 内部辅助 ──────────────────────────────────────────────


def _build_upstream_map(nodes_json: dict) -> dict[str, list[str]]:
    upstream: dict[str, list[str]] = {}
    for node_id, node_data in nodes_json.items():
        if not isinstance(node_data, dict):
            continue
        for v in node_data.get("inputs", {}).values():
            if isinstance(v, list) and len(v) >= 2:
                upstream.setdefault(str(node_id), []).append(str(v[0]))
    return upstream


def _try_add_fallback(
    params: list, node_id: str, class_type: str,
    node_title: str, field_name: str, field_value: Any,
) -> None:
    fallback_label = f"{node_title or class_type}.{field_name}"
    base = {"nodeId": str(node_id), "fieldName": field_name, "label": fallback_label,
            "nodeTitle": node_title or class_type, "description": f"{class_type}.{field_name}",
            "priority": "low", "constraints": {}}
    if isinstance(field_value, str) and 0 < len(field_value) <= _MAX_UNKNOWN_STR_LEN:
        params.append({**base, "type": "text", "currentValue": field_value})
    elif isinstance(field_value, (int, float)) and not isinstance(field_value, bool):
        params.append({**base, "type": "number", "currentValue": field_value})
