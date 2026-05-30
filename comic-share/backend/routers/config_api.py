"""配置管理路由 — 获取和更新运行时配置。"""

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from core.config import get_config, load_config

router = APIRouter(prefix="/api/v1", tags=["config"])
logger = logging.getLogger(__name__)


class ConfigUpdateRequest(BaseModel):
    """配置更新请求体（部分更新）。"""
    updates: dict[str, Any]


@router.get("/config")
async def get_current_config():
    """获取当前配置（脱敏）。"""
    config = get_config()
    safe_config = _sanitize_config(config)
    return safe_config


@router.put("/config")
async def update_config(req: ConfigUpdateRequest):
    """更新配置（运行时，不持久化到文件）。"""
    config = get_config()
    _deep_merge(config, req.updates)
    logger.info("配置已更新: keys=%s", list(req.updates.keys()))
    return {"status": "ok", "updated_keys": list(req.updates.keys())}


def _sanitize_config(config: dict) -> dict:
    """脱敏处理：隐藏 API Key 等敏感信息。"""
    import copy
    safe = copy.deepcopy(config)

    # 脱敏 LLM provider keys
    providers = safe.get("llm", {}).get("providers", {})
    for _name, provider in providers.items():
        if "api_key" in provider and provider["api_key"]:
            key = provider["api_key"]
            provider["api_key"] = key[:4] + "***" if len(key) > 4 else "***"

    # 脱敏 RunningHub key
    rh = safe.get("services", {}).get("runninghub", {})
    if rh.get("api_key"):
        rh["api_key"] = rh["api_key"][:4] + "***"

    return safe


def _deep_merge(base: dict, override: dict) -> None:
    """深度合并字典（就地修改 base）。"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
