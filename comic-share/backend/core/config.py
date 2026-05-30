"""配置加载模块 — 读取 config.yaml 并提供类型安全的配置访问。"""

from pathlib import Path
from typing import Any

import yaml

_CONFIG: dict[str, Any] = {}
_CONFIG_PATH: Path = Path(__file__).parent.parent / "config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """加载配置文件，返回配置字典。支持热重载。"""
    global _CONFIG
    config_path = path or _CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        _CONFIG = yaml.safe_load(f) or {}
    return _CONFIG


def get_config() -> dict[str, Any]:
    """获取当前配置。未加载时自动加载。"""
    if not _CONFIG:
        load_config()
    return _CONFIG


def get_env() -> str:
    """获取运行环境: dev | prod"""
    return get_config().get("env", "dev")


def is_dev() -> bool:
    """是否为开发模式。"""
    return get_env() == "dev"
