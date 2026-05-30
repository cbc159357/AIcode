"""统一异常处理 — 提供标准化错误响应格式。"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """应用级业务异常基类。"""

    def __init__(self, message: str, status_code: int = 400, detail: str = ""):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class ServiceUnavailableError(AppError):
    """外部服务不可用。"""

    def __init__(self, service: str, detail: str = ""):
        super().__init__(
            message=f"{service} 服务不可用",
            status_code=503,
            detail=detail,
        )


class ConfigError(AppError):
    """配置错误。"""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=500)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """全局 AppError 异常处理器。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail},
    )


async def generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """全局未捕获异常处理器。"""
    return JSONResponse(
        status_code=500,
        content={"error": "内部服务器错误", "detail": str(exc)},
    )
