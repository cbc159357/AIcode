"""健康检查路由 — 返回后端状态及外部服务连接状态。"""

import httpx
from fastapi import APIRouter

from core.config import get_config

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check():
    """
    健康检查端点。
    返回后端状态 + 各外部服务的连接状态。
    """
    config = get_config()
    services_config = config.get("services", {})

    status = {
        "status": "ok",
        "services": {},
    }

    checks = [
        ("comfyui", services_config.get("comfyui", {}).get("url", ""), "/system_stats"),
        ("cosyvoice", services_config.get("cosyvoice", {}).get("url", ""), "/"),
    ]

    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, base_url, path in checks:
            if not base_url:
                status["services"][name] = "not_configured"
                continue
            try:
                resp = await client.get(f"{base_url}{path}")
                connected = resp.status_code < 500
                status["services"][name] = "connected" if connected else "error"
            except Exception:
                status["services"][name] = "disconnected"

    return status
