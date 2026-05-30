"""
日志系统配置 — 遵循 logging-standards.md 规范。

- dev 模式: DEBUG 全量输出到 stdout + 文件
- prod 模式: stdout 仅 WARN+, 文件保留全量
- error.log 独立文件仅记录 ERROR+
"""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(env: str = "dev", log_dir: str = "logs") -> None:
    """
    根据运行环境配置日志系统。

    Args:
        env: 运行环境 (dev | prod)
        log_dir: 日志目录路径（相对于后端根目录）
    """
    log_path = Path(__file__).parent.parent / log_dir
    log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 清除已有 handler（支持热重载）
    root_logger.handlers.clear()

    # 格式定义
    if env == "dev":
        fmt = "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s"
        date_fmt = "%H:%M:%S"
    else:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        date_fmt = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # === stdout handler ===
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if env == "dev" else logging.WARNING)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # === 主日志文件 (全量, 轮转) ===
    app_log = logging.handlers.RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    app_log.setLevel(logging.DEBUG)
    app_log.setFormatter(formatter)
    root_logger.addHandler(app_log)

    # === 错误日志文件 (仅 ERROR+) ===
    error_log = logging.handlers.RotatingFileHandler(
        log_path / "error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    error_log.setLevel(logging.ERROR)
    error_log.setFormatter(formatter)
    root_logger.addHandler(error_log)

    # 降低第三方库噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)

    # 启动确认
    logger = logging.getLogger("core.logging")
    logger.info("日志系统初始化完成: env=%s, dir=%s", env, log_path)
