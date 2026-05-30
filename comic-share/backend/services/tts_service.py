"""TTS 服务层 — CosyVoice API 调用。"""

import logging
from pathlib import Path
from typing import Any

import httpx

from core.config import get_config

logger = logging.getLogger(__name__)


def _get_tts_url() -> str:
    """获取 CosyVoice 服务地址。"""
    config = get_config()
    return config.get("services", {}).get("cosyvoice", {}).get("url", "http://127.0.0.1:7860")


async def check_health() -> bool:
    """检查 TTS 服务是否在线。"""
    url = _get_tts_url()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{url}/api/health")
            return resp.status_code == 200
    except httpx.HTTPError:
        return False


async def list_ref_audios() -> list[dict[str, str]]:
    """列出可用参考音频。"""
    url = _get_tts_url()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{url}/api/ref_audios")
            if resp.status_code == 200:
                return resp.json().get("audios", [])
    except httpx.HTTPError:
        pass
    return []


async def synthesize(
    text: str,
    ref_audio: str = "",
    speed: float = 1.0,
    output_path: str | None = None,
) -> bytes | None:
    """
    合成语音。
    返回音频 bytes（WAV 格式）。
    如果 output_path 指定，同时写入文件。
    """
    url = _get_tts_url()
    payload: dict[str, Any] = {
        "text": text,
        "speed": speed,
    }
    if ref_audio:
        payload["ref_audio"] = ref_audio

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{url}/api/tts/synthesize", json=payload)
            resp.raise_for_status()

            audio_data = resp.content
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_bytes(audio_data)
                logger.debug("TTS 音频已保存: %s", output_path)

            return audio_data
    except httpx.HTTPError as e:
        logger.error("TTS 合成失败: %s", str(e))
        return None
