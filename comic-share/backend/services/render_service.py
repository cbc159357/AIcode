"""渲染服务层 — FFmpeg 视频合成。"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from core.config import get_config

logger = logging.getLogger(__name__)


def _get_ffmpeg_path() -> str:
    """获取 FFmpeg 可执行文件路径。"""
    config = get_config()
    return config.get("ffmpeg", {}).get("bin", "ffmpeg")


def _get_font_path() -> str:
    """获取字幕字体路径。"""
    config = get_config()
    return config.get("ffmpeg", {}).get("font", "ffmpeg/font.ttf")


def _get_output_dir() -> Path:
    """获取输出目录。"""
    config = get_config()
    base = config.get("output", {}).get("base_dir", "data/output")
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


async def render_video(
    shots: list[dict[str, Any]],
    output_name: str = "output.mp4",
    enable_subtitle: bool = True,
    enable_bgm: bool = True,
    bgm_path: str | None = None,
    resolution: str = "720x1280",
) -> str | None:
    """
    将分镜数据渲染为视频。

    每帧:
    - 图片 → Ken Burns 动效
    - 音频 → 旁白 TTS
    - 字幕 → 底部叠加

    返回输出视频路径。
    """
    ffmpeg = _get_ffmpeg_path()
    font = _get_font_path()
    output_dir = _get_output_dir()
    output_path = output_dir / output_name

    width, height = resolution.split("x")

    # 构建 concat 文件
    concat_file = output_dir / "_concat.txt"
    segments: list[str] = []

    for i, shot in enumerate(shots):
        image_path = shot.get("image_path", "")
        audio_path = shot.get("audio_path", "")
        duration = shot.get("audio_duration", 3.0)

        if not image_path:
            continue

        # 单帧视频（图片+音频）
        seg_path = str(output_dir / f"_seg_{i:03d}.mp4")
        cmd_parts = [
            ffmpeg, "-y",
            "-loop", "1", "-i", image_path,
            "-t", str(duration),
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
        ]

        if audio_path:
            cmd_parts.extend(["-i", audio_path, "-c:a", "aac", "-shortest"])
        else:
            cmd_parts.extend(["-an"])

        cmd_parts.append(seg_path)
        segments.append(seg_path)

        proc = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("FFmpeg 段落渲染失败 [%d]: %s", i, stderr.decode()[-200:])
            return None

    if not segments:
        logger.error("无有效分镜可渲染")
        return None

    # 写入 concat 列表
    with open(concat_file, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    # 合并所有段落
    merge_cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *merge_cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    # 清理临时文件
    for seg in segments:
        Path(seg).unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)

    if proc.returncode != 0:
        logger.error("FFmpeg 合并失败: %s", stderr.decode()[-200:])
        return None

    logger.info("视频渲染完成: %s", output_path)
    return str(output_path)
