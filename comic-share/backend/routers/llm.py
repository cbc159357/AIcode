"""LLM 路由 — 模型列表 + 流式生成。"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from services.llm_service import generate_stream, list_models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/llm", tags=["LLM"])


class ModelsRequest(BaseModel):
    provider: str | None = None


class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str = ""
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096


@router.post("/models")
async def get_models(req: ModelsRequest):
    """获取指定 Provider 的可用模型列表。"""
    try:
        models = await list_models(req.provider)
        return {"models": models}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("获取模型列表异常: %s", str(e))
        raise HTTPException(status_code=502, detail="无法连接 LLM 服务")


@router.post("/generate")
async def generate(req: GenerateRequest):
    """流式生成文本，SSE 格式输出。"""
    import json

    async def event_generator():
        full_text = ""
        try:
            async for chunk in generate_stream(
                prompt=req.prompt,
                system_prompt=req.system_prompt,
                provider=req.provider,
                model=req.model,
                api_key=req.api_key,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ):
                if chunk:
                    full_text += chunk
                    yield {"event": "chunk", "data": json.dumps({"content": chunk})}
            yield {"event": "done", "data": json.dumps({"full_response": full_text})}
        except RuntimeError as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        except Exception as e:
            logger.error("LLM 生成异常: %s", str(e))
            yield {"event": "error", "data": json.dumps({"error": "内部错误"})}

    return EventSourceResponse(event_generator())
