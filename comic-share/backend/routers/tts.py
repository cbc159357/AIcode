"""TTS 路由 — 语音合成 + 参考音频列表。"""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from services import tts_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tts", tags=["TTS"])


class SynthesizeRequest(BaseModel):
    text: str
    ref_audio: str = ""
    speed: float = 1.0


@router.get("/health")
async def health():
    """检查 TTS 服务状态。"""
    online = await tts_service.check_health()
    return {"status": "connected" if online else "disconnected"}


@router.get("/audios")
async def list_audios():
    """列出可用参考音频。"""
    audios = await tts_service.list_ref_audios()
    return {"audios": audios}


@router.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    """合成语音，返回 WAV 音频。"""
    audio = await tts_service.synthesize(
        text=req.text,
        ref_audio=req.ref_audio,
        speed=req.speed,
    )
    if audio is None:
        raise HTTPException(status_code=502, detail="TTS 合成失败")
    return Response(content=audio, media_type="audio/wav")
