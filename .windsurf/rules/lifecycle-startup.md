---
description: 生命周期系统与启动脚本设计规则 — 修改 start.py 或 lifecycle.py 时必须遵循
---

# 生命周期系统与启动脚本规则

## 核心原则

**start.py 是薄触发入口，不持有任何业务逻辑。** 所有进程管理、端口检测、健康检查、PID 持久化均由 `lifecycle.py` 负责。

## 运行模式

**启动脚本必须是前台常驻进程。** `python start.py` 执行后：

1. 启动子进程（前端/后端）
2. **实时转发**子进程的 stdout/stderr 到终端，让开发者直观看到服务日志
3. **持续运行**，直到用户按 `Ctrl+C` 手动中断
4. 收到中断信号后，优雅停止所有子进程并清理 PID

### 禁止行为

- ☒ 启动后立即退出（火并忘模式）
- ☒ 将子进程 stdout/stderr 重定向到 DEVNULL（开发模式下）
- ☒ 使用 `CREATE_NEW_PROCESS_GROUP` 完全脱离子进程

## 职责划分

### start.py — 触发层（目标 ≤ 20 行有效代码）

仅允许做以下事情：

1. **解析命令行参数** — `argparse` 定义 `--backend / --frontend / --stop / --status / --install / --no-browser`
2. **调用 lifecycle** — 调用 `cmd_start / cmd_stop / cmd_status / cmd_install`
3. **触发浏览器** — 启动成功后打开 `http://localhost:18902`

**禁止**：
- 在 start.py 中定义服务配置（端口、命令、路径、健康检查 URL）
- 在 start.py 中编写进程等待循环、端口检测
- 在 start.py 中编写依赖安装逻辑（ensure_venv / install_deps）
- 在 start.py 中定义超过 3 个辅助函数

### server/lifecycle.py — 生命周期层

负责全部进程生命周期管理：

| 职责 | 类/函数 | 说明 |
|------|---------|------|
| PID 持久化 | `PidStore` | 读写 `.pids.json`，记录服务→PID 映射 |
| 端口检测 | `is_port_in_use()` | TCP connect 检测端口占用 |
| 健康检查 | `check_health()` | HTTP GET 检测服务是否真正可用 |
| 进程启动 | `ServiceManager.start()` | 启动子进程，记录 PID |
| 进程停止 | `ServiceManager.stop() / stop_all()` | 杀进程树，清理 PID |
| 僵尸清理 | `ServiceManager.cleanup_zombies()` | 清理 PID 文件残留 + 端口占用 |
| 状态查询 | `ServiceManager.status()` | 返回所有服务的运行状态 |
| 依赖安装 | 应归入此层或独立 `setup.py` | venv 创建、pip install、npm install |
| 启动等待 | 应归入此层 | TTS 端口就绪轮询、crash 检测 |

### 服务配置 — 归属 lifecycle 或 config.yaml

服务定义（名称、端口、启动命令、工作目录、健康检查 URL）应在 `server/lifecycle.py` 或 `server/config.yaml` 中集中声明，**不散落在 start.py**。

```python
# ✅ 正确: 配置集中在 lifecycle
SERVICES = {
    "frontend": {"name": "Vite 前端",    "port": 18902, ...},
    "backend":  {"name": "FastAPI 后端", "port": 18900, ...},
}

# ❌ 错误: start.py 中定义路径常量和服务字典
SERVICES = { ... }  # 不应出现在 start.py
```

## 端口规范

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI 后端 | 18900 | 主 API 服务（uvicorn，默认开启 reload） |
| Vite 前端 | 18902 | 开发服务器 |
| GPT-SoVITS TTS | 5005 | **外部独立服务**，不由项目管理 |

## 默认启动行为

- `python start.py`（无参数）→ 启动 **Frontend + Backend**
- `python start.py --backend` → 仅启动后端
- `python start.py --frontend` → 仅启动前端
- TTS 已改为外部独立服务（端口 5005，位于 `E:\videos\GPT-SoVITS\`），不由 `start.py` 管理
- 启动顺序：Frontend（最快）→ Backend，前端先就绪先打开浏览器

## 后端热更新（Auto-Reload）

后端使用 uvicorn `reload=True` 模式运行（见 `server/main.py`），**代码修改后自动重载，无需手动重启**。

### 规则

1. `server/main.py` 的 `uvicorn.run()` 必须使用字符串导入 `"main:app"` + `reload=True`
2. lifecycle.py 中后端启动命令为 `[VENV_PYTHON, "main.py"]`，由 main.py 内部的 uvicorn 负责 reload
3. 修改 `server/` 下的 `.py` 文件后，uvicorn 自动检测变更并重载，**无需重启进程或 lifecycle**
4. 修改 `server/config.yaml` 后配置自动生效（通过 `load_config()` 重新读取），无需重启
5. 仅当修改了 `server/main.py` 中 uvicorn 启动参数本身或 `server/lifecycle.py` 时，才需要 `python start.py --stop && python start.py`

### 注意事项

- reload 模式下 uvicorn 会 watch 整个 `server/` 目录，**避免在该目录下频繁写入临时文件**（会触发无意义重载）
- `output/` 目录已在 `server/` 外部，不会触发 reload
- 如需关闭 reload（生产部署），在 `config.yaml` 或启动参数中设置 `reload: false`
- **必须设置 `reload_delay=1.0`**：Windows 上 WatchFiles reloader 在检测到新文件创建时会立即触发 reload，此时文件可能尚未写入完成，导致 import 失败后 reloader 进程直接退出。增加 delay 给文件写入留出时间，避免此问题。

## 进程清理规则

1. `stop_all()` 必须使用 `taskkill /F /T /PID`（Windows）确保杀掉整个进程树
2. 启动前始终调用 `cleanup_zombies()`：先清 PID 文件残留，再清端口占用
3. PID 文件位于 `server/logs/.pids.json`，格式 `{"service_name": pid}`

## .env 预加载

`server/main.py` 在所有配置之前从项目根目录 `.env` 加载环境变量（`VOLCENGINE_AK`、`VOLCENGINE_SK` 等）。

- 加载顺序：`server/.env` → 项目根 `.env`（先找到的生效）
- 使用 `os.environ.setdefault()`，不覆盖已有系统环境变量
- `.env` 已在 `.gitignore` 中排除

## start.py 当前形态

```python
"""AI动态漫 · 启动脚本（薄触发入口）"""
import argparse
from server.lifecycle import cmd_start, cmd_stop, cmd_status, cmd_install

p = argparse.ArgumentParser(description="AI动态漫")
p.add_argument("--backend", action="store_true")
p.add_argument("--frontend", action="store_true")
p.add_argument("--install", action="store_true")
p.add_argument("--status", action="store_true")
p.add_argument("--stop", action="store_true")
p.add_argument("--no-browser", action="store_true")
args = p.parse_args()

if args.stop:     cmd_stop()
elif args.status: cmd_status()
elif args.install: cmd_install()
else:
    targets = []
    if args.backend:  targets.append("backend")
    if args.frontend: targets.append("frontend")
    if not targets:   targets = ["frontend", "backend"]
    cmd_start(targets, open_browser=not args.no_browser)
```

## 前端视口锁定规则

全页应用（SPA）必须防止浏览器窗口级滚动，所有滚动仅发生在内部容器中。

### 根样式要求

```css
/* html + body + #app 三层锁死 */
html, body { height: 100%; overflow: hidden; }
#app { height: 100%; overflow: hidden; }
```

- **禁止** `body` 使用 `min-height: 100vh`（会让 body 可滚动）
- **禁止** `body` 出现 `overflow: auto` 或 `overflow: visible`

### Arco Design 弹出层容器

Arco Design 的弹出组件（`a-select`、`a-popconfirm`、`a-tooltip`、`a-modal` 等）默认 teleport 到 `document.body`。这会导致：

1. 弹出层渲染到 body 末尾 → body 高度变化 → 浏览器触发滚动
2. 切换窗口时弹出层关闭 → body 高度缩回 → **页面跳到顶部**

**解决方案**：在 `main.ts` 中全局配置 `popupContainer: '#app'`：

```typescript
app.use(ArcoVue, {
  componentConfig: {
    select: { popupContainer: '#app' },
    popconfirm: { popupContainer: '#app' },
    tooltip: { popupContainer: '#app' },
    popover: { popupContainer: '#app' },
    dropdown: { popupContainer: '#app' },
    modal: { popupContainer: '#app' },
  },
})
```

### 新增弹出组件时的检查

- 使用 Arco 弹出类组件时，确认已在全局配置中声明 `popupContainer`
- 如使用非 Arco 的第三方弹出层，手动指定 `teleport="#app"`
- **禁止** 在组件中使用 `teleport="body"`

## 变更检查清单

修改 start.py 或 lifecycle.py 时，确认：

- [ ] start.py 有效代码是否仍在 20 行以内？
- [ ] 是否有进程管理逻辑泄漏到 start.py？
- [ ] 服务配置是否集中在一处？
- [ ] 后端是否保持 `reload=True`（开发模式）？
- [ ] 端口冲突是否有预清理？
- [ ] PID 文件是否在启停时正确维护？
- [ ] `.env` 是否在配置加载前预读？
- [ ] 启动后是否保持前台常驻（非火并忘）？
- [ ] 子进程日志是否实时转发到终端？
- [ ] Ctrl+C 是否能优雅停止所有子进程？
