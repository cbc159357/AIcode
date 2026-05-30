"""comic-share 后端入口 — FastAPI 应用初始化。"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_config, load_config
from core.exceptions import AppError, app_error_handler, generic_error_handler
from core.logging_config import setup_logging
from routers import archives, comfyui, config_api, health, llm, project, runninghub, tts, workflow

# 加载配置
config = load_config()
env = config.get("env", "dev")

# 初始化日志系统
log_dir = config.get("logging", {}).get("dir", "logs")
setup_logging(env=env, log_dir=log_dir)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期管理。"""
    logger.info("comic-share 后端启动: env=%s, port=%d", env, config["server"]["port"])
    yield
    logger.info("comic-share 后端关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="comic-share API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if env == "dev" else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理器
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# 注册路由
app.include_router(health.router)
app.include_router(config_api.router)
app.include_router(llm.router)
app.include_router(comfyui.router)
app.include_router(runninghub.router)
app.include_router(tts.router)
app.include_router(project.router)
app.include_router(workflow.router)
app.include_router(archives.router)


# 开发模式启动
if __name__ == "__main__":
    server_config = get_config().get("server", {})
    uvicorn.run(
        "main:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8080),
        reload=server_config.get("reload", True),
        reload_delay=1.0,
    )
