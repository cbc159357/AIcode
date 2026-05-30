"""comic-share · 启动脚本（薄触发入口）"""

import argparse

from lifecycle import cmd_start, cmd_stop, cmd_status

p = argparse.ArgumentParser(description="comic-share 启动器")
p.add_argument("--backend", action="store_true", help="仅启动后端")
p.add_argument("--frontend", action="store_true", help="仅启动前端")
p.add_argument("--stop", action="store_true", help="停止所有服务")
p.add_argument("--status", action="store_true", help="查看服务状态")
p.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
p.add_argument("--verbose", "-v", action="store_true", help="输出详细日志")
args = p.parse_args()

if args.stop:
    cmd_stop(verbose=args.verbose)
elif args.status:
    cmd_status()
else:
    targets = []
    if args.backend:
        targets.append("backend")
    if args.frontend:
        targets.append("frontend")
    if not targets:
        targets = ["frontend", "backend"]
    cmd_start(targets, open_browser=not args.no_browser, verbose=args.verbose)
