"""RunningHub 模型元数据缓存服务。

分页拉取 /openapi/v2/resource/list，构建 byFileName 索引，本地 JSON 持久化。
全部函数均为同步，由 router 通过 asyncio.to_thread() 调用。
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import logging

import httpx

_logger = logging.getLogger(__name__)
_CACHE_PATH = (
    Path(__file__).parent.parent / "data" / "runninghub" / "model_cache.json"
)
_RH_RESOURCE_URL = "https://www.runninghub.cn/openapi/v2/resource/list"
_PAGE_SIZE = 10  # API 默认每页 10 条，不强制传大参数避免被拒弹

_BASE_MODEL_NORMALIZE: dict[str, str] = {
    "Flux2-Klein-9B": "Flux2-Klein",
    "Flux2-Klein": "Flux2-Klein",
    "FLUX.1-dev": "Flux1",
    "FLUX.1-schnell": "Flux1",
    "Flux.1 Dev": "Flux1",
    "Flux1": "Flux1",
    "SDXL 1.0": "SDXL",
    "SDXL": "SDXL",
    "SD 1.5": "SD15",
    "SD1.5": "SD15",
    "Stable Diffusion 1.5": "SD15",
    "HiDream-I1-Full": "HiDream",
    "HiDream-I1-Fast": "HiDream",
    "HiDream": "HiDream",
    "Wan2.1": "Wan2",
    "Wan2.2": "Wan2",
}

_QUANT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"fp8", re.I), "fp8"),
    (re.compile(r"int8", re.I), "int8"),
    (re.compile(r"gguf", re.I), "gguf"),
    (re.compile(r"nf4", re.I), "nf4"),
    (re.compile(r"bf16", re.I), "bf16"),
]

@dataclass
class _RefreshProgress:
    """刷新进度快照。total_pages 为 None 表示尚未拿到首页。"""
    page: int = 0
    total_pages: int | None = None
    count: int = 0


_cache_mem: dict[str, Any] = {}
_progress: _RefreshProgress | None = None  # 仅在刷新进行期间非 None


def normalize_base_model(raw: str) -> str:
    """归一化架构族名（Flux2-Klein-9B → Flux2-Klein）。"""
    return _BASE_MODEL_NORMALIZE.get(raw, raw or "unknown")


def _infer_quantization(filename: str) -> str:
    for pattern, quant in _QUANT_PATTERNS:
        if pattern.search(filename):
            return quant
    return "fp16"


def _parse_record(record: dict) -> tuple[str, dict] | None:
    filename = record.get("nodeModelName", "")
    if not filename:
        return None
    versions = record.get("versions") or []
    ver = versions[0] if versions else {}
    base_raw = ver.get("baseModel", "")
    return filename, {
        "resourceType": record.get("resourceType", ""),
        "baseModel": normalize_base_model(base_raw),
        "baseModelRaw": base_raw,
        "resourceName": record.get("resourceName", ""),
        "quantization": _infer_quantization(filename),
        "tags": [t["name"] for t in (record.get("tags") or []) if isinstance(t, dict)],
        "triggerWords": ver.get("triggerWords", ""),
    }


_MAX_RETRIES = 5
_PAGE_INTERVAL = 3.0   # 正常页间等待（秒），约 20 req/min
_DEFAULT_RETRY_WAIT = 60.0  # 429 时若无 Retry-After 则等待 60s


def _fetch_page_with_retry(client: httpx.Client, headers: dict, page: int) -> dict:
    """带 429 退避重试的单页拉取，最多重试 _MAX_RETRIES 次。
    优先读取 Retry-After header，否则等待 _DEFAULT_RETRY_WAIT 秒。
    """
    for attempt in range(_MAX_RETRIES + 1):
        resp = client.post(
            _RH_RESOURCE_URL,
            headers=headers,
            json={"current": page, "size": _PAGE_SIZE},
        )
        _logger.debug("[model-cache] HTTP %s (attempt %d)", resp.status_code, attempt + 1)
        if resp.status_code == 429 and attempt < _MAX_RETRIES:
            retry_after = resp.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else _DEFAULT_RETRY_WAIT
            _logger.warning("[model-cache] 429 限流，等待 %.0fs 后重试 (attempt %d/%d)",
                            wait, attempt + 1, _MAX_RETRIES)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return {}


def _merge_page_records(data: dict, by_filename: dict[str, dict]) -> None:
    """将单页 records 解析并原地合并进 by_filename。"""
    for record in (data.get("records") or []):
        parsed = _parse_record(record)
        if parsed:
            by_filename[parsed[0]] = parsed[1]


def _persist_cache(by_filename: dict[str, dict]) -> dict:
    """写入缓存文件并刷新内存热缓存，返回摘要。"""
    global _cache_mem
    cache: dict[str, Any] = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "totalCount": len(by_filename),
        "byFileName": by_filename,
    }
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    _cache_mem = cache
    return {"totalCount": cache["totalCount"], "fetchedAt": cache["fetchedAt"]}


def fetch_and_save(api_key: str, proxy: str | None = None) -> dict:
    """同步分页拉取全量模型列表并持久化，返回 { totalCount, fetchedAt }。"""
    global _progress
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    client_kwargs: dict[str, Any] = {"timeout": 60}
    if proxy:
        client_kwargs["proxy"] = proxy

    _logger.info("[model-cache] 开始刷新, proxy=%s", proxy)
    by_filename: dict[str, dict] = {}
    page = 1
    _progress = _RefreshProgress()
    try:
        with httpx.Client(**client_kwargs) as client:
            while True:
                body = _fetch_page_with_retry(client, headers, page)
                if body.get("code") != 0:
                    raise ValueError(f"API error: code={body.get('code')}, msg={body.get('msg')}")
                data = body.get("data") or {}
                _merge_page_records(data, by_filename)
                _progress = _RefreshProgress(page, data.get("pages"), len(by_filename))
                if not data.get("hasNext"):
                    break
                page += 1
                time.sleep(_PAGE_INTERVAL)  # 避免触发 429 限流（约 20 req/min）
        return _persist_cache(by_filename)
    finally:
        _progress = None  # 刷新结束后清空，避免下次打开设置页残留旧进度


def load_cache() -> dict[str, Any]:
    """读取本地缓存（内存热读优先）。"""
    global _cache_mem
    if _cache_mem:
        return _cache_mem
    if _CACHE_PATH.exists():
        try:
            _cache_mem = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            _cache_mem = {}
    return _cache_mem


def get_model_meta(filename: str) -> dict | None:
    """按文件名查询单条模型元数据。"""
    return load_cache().get("byFileName", {}).get(filename)


def get_cache_status() -> dict:
    """返回缓存状态 { exists, totalCount, fetchedAt, progress }。"""
    cache = load_cache()
    progress = None
    if _progress is not None:
        progress = {"page": _progress.page,
                    "totalPages": _progress.total_pages,
                    "count": _progress.count}
    return {
        "exists": bool(cache),
        "totalCount": cache.get("totalCount", 0) if cache else 0,
        "fetchedAt": cache.get("fetchedAt") if cache else None,
        "progress": progress,
    }


def search_models(
    base_model: str | None = None,
    resource_type: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """在缓存中搜索模型。base_model / resource_type 精确匹配，q 模糊搜索文件名或 resourceName。"""
    by_filename = load_cache().get("byFileName", {})
    q_lower = q.lower().strip() if q else None
    rt_upper = resource_type.upper() if resource_type else None
    results: list[dict] = []
    for filename, meta in by_filename.items():
        if base_model and meta.get("baseModel") != base_model:
            continue
        if rt_upper and meta.get("resourceType", "").upper() != rt_upper:
            continue
        if q_lower and q_lower not in filename.lower() \
                and q_lower not in meta.get("resourceName", "").lower():
            continue
        results.append({"filename": filename, **meta})
        if len(results) >= limit:
            break
    return results
