"""
comic-share 生命周期管理 — 进程启动/停止/状态查询。

遵循 lifecycle-startup.md + logging-standards.md 规范:
- 启动后保持前台常驻，实时转发子进程日志
- Ctrl+C 优雅停止所有子进程
- 日志按 verbose 模式切换详细程度
- PID 持久化到 .pids.json
"""

import json
import logging
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
PID_FILE = PROJECT_ROOT / ".pids.json"

SERVICES = {
    "frontend": {
        "name": "Vite 前端",
        "port": 5173,
        "cwd": str(FRONTEND_DIR),
        "cmd": ["npm.cmd", "run", "dev", "--", "--host"] if sys.platform == "win32" else ["npm", "run", "dev", "--", "--host"],
        "health_url": "http://localhost:5173",
    },
    "backend": {
        "name": "FastAPI 后端",
        "port": 8080,
        "cwd": str(BACKEND_DIR),
        "cmd": [sys.executable, "main.py"],
        "health_url": "http://localhost:8080/api/v1/health",
    },
}

# 服务日志前缀颜色（ANSI）
_COLORS = {
    "frontend": "\033[36m",  # cyan
    "backend": "\033[33m",   # yellow
}
_RESET = "\033[0m"

logger = logging.getLogger("lifecycle")

# 全局进程引用，用于 Ctrl+C 时清理
_processes: dict[str, subprocess.Popen] = {}
_shutting_down = False


def _setup_logger(verbose: bool = False) -> None:
    """配置生命周期日志级别。"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def _is_port_in_use(port: int) -> bool:
    """检测端口是否被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _load_pids() -> dict:
    """读取 PID 文件。"""
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_pids(pids: dict) -> None:
    """保存 PID 文件。"""
    PID_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")


def _kill_pid(pid: int) -> bool:
    """终止进程树 (Windows)。"""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                stdin=subprocess.DEVNULL,
            )
        else:
            os.kill(pid, 9)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _cleanup_port(port: int) -> None:
    """清理占用指定端口的进程。"""
    if not _is_port_in_use(port):
        return
    logger.debug("端口 %d 被占用，尝试清理...", port)
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = int(parts[-1])
                    _kill_pid(pid)
                    logger.debug("已清理端口 %d 占用进程 PID=%d", port, pid)
        except (subprocess.SubprocessError, ValueError):
            pass


def _wait_for_service(url: str, timeout: int = 30) -> bool:
    """等待服务就绪（HTTP 健康检查）。"""
    import urllib.request
    import urllib.error

    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    return False


def _stream_output(proc: subprocess.Popen, svc_key: str) -> None:
    """在独立线程中读取子进程输出并转发到终端（带服务前缀）。"""
    color = _COLORS.get(svc_key, "")
    prefix = f"{color}[{svc_key}]{_RESET} "
    stream = proc.stdout
    if stream is None:
        return
    try:
        for line in iter(stream.readline, ""):
            if _shutting_down:
                break
            if line:
                sys.stdout.write(f"{prefix}{line}")
                sys.stdout.flush()
    except (ValueError, OSError):
        pass


def _graceful_shutdown() -> None:
    """优雅停止所有子进程。"""
    global _shutting_down
    if _shutting_down:
        return
    _shutting_down = True

    print()  # 换行避免 ^C 黏连
    logger.info("收到停止信号，正在关闭服务...")

    for svc_key, proc in _processes.items():
        svc = SERVICES.get(svc_key, {})
        name = svc.get("name", svc_key)
        try:
            if proc.poll() is None:
                _kill_pid(proc.pid)
                logger.info("✓ %s 已停止 (PID: %d)", name, proc.pid)
        except (OSError, subprocess.SubprocessError):
            pass

    _save_pids({})
    logger.info("所有服务已停止")


def cmd_start(targets: list[str], open_browser: bool = True, verbose: bool = False) -> None:
    """启动指定服务并保持前台常驻，实时输出日志。"""
    global _shutting_down
    _setup_logger(verbose)
    _shutting_down = False

    # 注册 Ctrl+C 处理
    signal.signal(signal.SIGINT, lambda *_: _graceful_shutdown())
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, lambda *_: _graceful_shutdown())

    pids = {}

    for svc_key in targets:
        svc = SERVICES[svc_key]
        port = svc["port"]

        # 清理残留
        _cleanup_port(port)

        logger.debug("启动命令: %s", svc["cmd"])
        logger.debug("工作目录: %s", svc["cwd"])

        # 检查工作目录
        cwd = Path(svc["cwd"])
        if not cwd.exists():
            logger.error("✗ %s 工作目录不存在: %s", svc["name"], cwd)
            continue

        # 启动进程 — stdout/stderr 实时转发（不静默）
        proc = subprocess.Popen(
            svc["cmd"],
            cwd=svc["cwd"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )

        _processes[svc_key] = proc
        pids[svc_key] = proc.pid
        logger.info("✓ %s 已启动 (PID: %d, Port: %d)", svc["name"], proc.pid, port)

        # 启动日志转发线程
        t = threading.Thread(target=_stream_output, args=(proc, svc_key), daemon=True)
        t.start()

    _save_pids(pids)

    # 等待前端就绪后打开浏览器
    if open_browser and "frontend" in targets:
        def _open_browser():
            frontend_url = SERVICES["frontend"]["health_url"]
            logger.debug("等待前端就绪: %s", frontend_url)
            if _wait_for_service(frontend_url, timeout=20):
                webbrowser.open(frontend_url)
                logger.info("✓ 已打开浏览器: %s", frontend_url)
            else:
                logger.warning("⚠ 前端未在超时时间内就绪，请手动打开浏览器")

        threading.Thread(target=_open_browser, daemon=True).start()

    # 前台常驻：等待所有子进程退出或收到中断信号
    logger.info("─── 服务运行中，按 Ctrl+C 停止 ───")
    try:
        while not _shutting_down:
            # 检查子进程是否意外退出
            all_dead = True
            for svc_key, proc in _processes.items():
                if proc.poll() is None:
                    all_dead = False
                else:
                    rc = proc.returncode
                    if rc and not _shutting_down:
                        svc = SERVICES.get(svc_key, {})
                        logger.warning("⚠ %s 异常退出 (code: %d)", svc.get("name", svc_key), rc)

            if all_dead and not _shutting_down:
                logger.warning("所有服务已退出")
                break

            time.sleep(0.5)
    except KeyboardInterrupt:
        _graceful_shutdown()


def cmd_stop(verbose: bool = False) -> None:
    """停止所有服务（通过 PID 文件）。"""
    _setup_logger(verbose)
    pids = _load_pids()

    if not pids:
        logger.info("没有正在运行的服务")
        return

    for svc_key, pid in pids.items():
        svc = SERVICES.get(svc_key, {})
        name = svc.get("name", svc_key)
        logger.debug("正在停止 %s (PID: %d)...", name, pid)
        _kill_pid(pid)
        logger.info("✓ %s 已停止", name)

    # 清理端口残留
    for svc_key in pids:
        if svc_key in SERVICES:
            _cleanup_port(SERVICES[svc_key]["port"])

    _save_pids({})
    logger.info("所有服务已停止")


def cmd_status() -> None:
    """查看服务状态。"""
    _setup_logger(verbose=False)
    pids = _load_pids()

    print("\n┌─────────────────────────────────────┐")
    print("│      comic-share 服务状态           │")
    print("├──────────┬──────┬────────┬──────────┤")
    print("│ 服务     │ 端口 │ PID    │ 状态     │")
    print("├──────────┼──────┼────────┼──────────┤")

    for svc_key, svc in SERVICES.items():
        pid = pids.get(svc_key, "-")
        port = svc["port"]
        port_active = _is_port_in_use(port)
        status = "🟢 运行中" if port_active else "🔴 已停止"
        print(f"│ {svc['name']:<8} │ {port:<4} │ {str(pid):<6} │ {status:<8} │")

    print("└──────────┴──────┴────────┴──────────┘\n")
