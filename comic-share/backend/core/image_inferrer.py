"""
图片输入语义推断 — 通过 BFS 遍历下游节点推断 LoadImage 节点的语义角色。
纯函数，无 I/O，无外部依赖。
"""

from collections import deque

_DOWNSTREAM_ROLE_MAP: dict[str, str] = {
    "IPAdapterFaceID": "face", "IPAdapterFaceIDPlusV2": "face",
    "ReActorFaceSwap": "face", "FaceDetailer": "face",
    "InstantID": "face", "FaceRestore": "face",
    "IPAdapter": "reference", "IPAdapterAdvanced": "reference",
    "IPAdapterTiled": "reference", "StyleAligned": "style",
    "OpenposePreprocessor": "pose", "DWPreprocessor": "pose",
    "CannyEdgePreprocessor": "pose", "DepthAnythingPreprocessor": "pose",
    "MiDaS-DepthMapPreprocessor": "pose", "LineArtPreprocessor": "pose",
    "HEDPreprocessor": "pose", "BinaryPreprocessor": "pose",
    "ScribblePreprocessor": "pose", "TilePreprocessor": "pose",
    "NormalMapSimple": "pose", "ControlNetApply": "pose",
    "ControlNetApplyAdvanced": "pose",
    "VAEEncode": "reference", "VAEEncodeTiled": "reference",
    "WD14Tagger|pysssss": "internal", "WD14Tagger": "internal", "VLM": "internal",
    "ImageToMask": "mask", "MaskComposite": "mask", "GrowMask": "mask",
    "ImageComposite": "background", "ImagePadForOutpaint": "background",
}

_PASS_THROUGH_TYPES: set[str] = {
    "easy setNode", "easy getNode", "Any Switch (rgthree)",
    "ImageResize", "ImageScale", "ImageResizeKJ",
    "CR Image Resize", "CR Image Size", "ImageBatch",
}

_IMAGE_ROLE_ORDER: dict[str, int] = {
    "reference": 0, "face": 1, "style": 2, "pose": 3,
    "mask": 4, "background": 5, "internal": 9,
}


def infer_image_inputs(nodes_json: dict) -> list[dict]:
    """解析 LoadImage 节点，通过下游连接启发式推断每个节点的语义角色。"""
    if not nodes_json or not isinstance(nodes_json, dict):
        return []
    downstream_map = _build_downstream_map(nodes_json)
    image_inputs: list[dict] = []
    for node_id, node_data in nodes_json.items():
        if not isinstance(node_data, dict):
            continue
        if node_data.get("class_type") != "LoadImage":
            continue
        inputs = node_data.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        image_val = inputs.get("image", "")
        if isinstance(image_val, list):
            continue
        meta = node_data.get("_meta", {})
        node_title = meta.get("title", "").strip() if isinstance(meta, dict) else ""
        role = _infer_role_bfs(node_id, downstream_map, nodes_json)
        image_inputs.append({
            "nodeId": str(node_id),
            "fieldName": "image",
            "role": role,
            "label": node_title or f"图片输入 {node_id}",
            "required": role == "reference",
        })
    image_inputs.sort(key=lambda x: _IMAGE_ROLE_ORDER.get(x["role"], 8))
    return image_inputs


# ── 内部辅助 ──────────────────────────────────────────────


def _build_downstream_map(nodes_json: dict) -> dict[str, list[str]]:
    downstream: dict[str, list[str]] = {}
    for node_id, node_data in nodes_json.items():
        if not isinstance(node_data, dict):
            continue
        inputs = node_data.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        for field_value in inputs.values():
            if isinstance(field_value, list) and len(field_value) >= 2:
                downstream.setdefault(str(field_value[0]), []).append(str(node_id))
    return downstream


def _infer_role_bfs(
    start_id: str,
    downstream_map: dict[str, list[str]],
    nodes_json: dict,
    max_depth: int = 4,
) -> str:
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(start_id, 0)])
    while queue:
        current_id, depth = queue.popleft()
        if current_id in visited:
            continue
        visited.add(current_id)
        node = nodes_json.get(current_id, {})
        class_type = node.get("class_type", "") if isinstance(node, dict) else ""
        if current_id != start_id:
            if class_type not in _PASS_THROUGH_TYPES:
                role = _DOWNSTREAM_ROLE_MAP.get(class_type)
                if role is not None:
                    return role
                continue
        if depth < max_depth:
            for child_id in downstream_map.get(current_id, []):
                if child_id not in visited:
                    queue.append((child_id, depth + 1))
    return "reference"
