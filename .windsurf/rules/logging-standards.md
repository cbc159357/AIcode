---
description: 日志系统设计规则 — 新建模块或修改日志相关代码时必须遵循
---

# 日志系统设计规则

## 核心原则

**日志必须分级分环境，开发阶段详尽输出，生产模式静默安全。** 前端绝不暴露调试信息给终端用户，后端按严重程度分层过滤，生命周期脚本随运行模式自动调节日志冗余度。

---

## 一、运行模式定义

| 模式 | 标识 | 场景 | 日志行为 |
|------|------|------|----------|
| **Development** | `NODE_ENV=development` / `ENV=dev` | 本地开发、调试、测试 | 全量输出，含 DEBUG/TRACE |
| **Production** | `NODE_ENV=production` / `ENV=prod` | 用户使用、部署上线 | 仅 WARN + ERROR，前端零 console |

### 模式检测（统一方式）

- **前端**: 通过 `import.meta.env.MODE` 或 `import.meta.env.DEV` 判断
- **后端**: 通过 `config.yaml` 中 `env: dev | prod` 或环境变量 `ENV` 判断
- **生命周期脚本**: 通过 `--verbose / -v` 参数或 `ENV` 环境变量判断

---

## 二、日志级别标准

### 2.1 级别定义（通用）

| 级别 | 数值 | 含义 | Dev 模式 | Prod 模式 |
|------|------|------|----------|-----------|
| TRACE | 0 | 极度详细（循环体内、逐字段变化） | ✅ 可选开启 | ❌ 绝对禁止 |
| DEBUG | 1 | 内部状态、变量值、分支进入 | ✅ 默认输出 | ❌ 禁止 |
| INFO | 2 | 关键流程节点（启动、连接、完成） | ✅ 输出 | ⚠️ 精简输出 |
| WARN | 3 | 异常但可恢复（超时重试、降级） | ✅ 输出 | ✅ 输出 |
| ERROR | 4 | 功能失败（API 报错、文件缺失） | ✅ 输出 | ✅ 输出 + 上报 |
| FATAL | 5 | 系统崩溃（进程退出） | ✅ 输出 | ✅ 输出 + 上报 + 告警 |

### 2.2 前端日志级别

```typescript
// ✅ 正确: 使用封装的 logger，自动按环境过滤
import { logger } from '@/utils/logger'

logger.debug('LLM stream chunk received:', chunk)  // Dev only
logger.info('Step 1 completed, shots:', count)      // Dev only in prod
logger.warn('TTS fallback to silent audio')         // Always
logger.error('ComfyUI connection failed:', err)     // Always

// ❌ 错误: 直接使用 console
console.log('debug info')      // 禁止裸露 console
console.error('something')     // 必须经过 logger 封装
```

### 2.3 后端日志级别

```python
# ✅ 正确: 使用标准 logging 模块
import logging
logger = logging.getLogger(__name__)

logger.debug("Request payload: %s", payload)   # Dev only
logger.info("Video render started: %s", path)  # Prod: 精简
logger.warning("FFmpeg timeout, retrying...")   # Always
logger.error("Render failed: %s", str(e))      # Always
```

---

## 三、前端日志规范

### 3.1 Logger 封装要求

必须提供统一的 `logger` 工具模块，禁止直接使用 `console.*`。

```typescript
// src/utils/logger.ts
const isDev = import.meta.env.DEV

export const logger = {
  trace: (...args: unknown[]) => { if (isDev) console.debug('[TRACE]', ...args) },
  debug: (...args: unknown[]) => { if (isDev) console.debug('[DEBUG]', ...args) },
  info:  (...args: unknown[]) => { if (isDev) console.info('[INFO]', ...args) },
  warn:  (...args: unknown[]) => { console.warn('[WARN]', ...args) },
  error: (...args: unknown[]) => { console.error('[ERROR]', ...args) },

  // 分组日志（复杂流程追踪）
  group: (label: string) => { if (isDev) console.group(label) },
  groupEnd: () => { if (isDev) console.groupEnd() },

  // 性能计时
  time: (label: string) => { if (isDev) console.time(label) },
  timeEnd: (label: string) => { if (isDev) console.timeEnd(label) },

  // 表格数据（调试复杂对象）
  table: (data: unknown) => { if (isDev) console.table(data) },
}
```

### 3.2 前端 Production 模式铁律

1. **零 console 输出** — Production 构建后浏览器控制台不得出现任何 debug/info 日志
2. **仅保留 warn + error** — 指向真实问题的异常信息
3. **不暴露内部结构** — 禁止输出 API URL、token、内部状态结构、请求 payload
4. **不暴露用户数据** — 禁止输出用户输入的文本、图片路径等隐私信息
5. **ESLint 强制** — 配置 `no-console` 规则，仅允许通过 `logger` 调用

```jsonc
// .eslintrc — 推荐配置
{
  "rules": {
    "no-console": ["error", { "allow": [] }]
    // logger.ts 文件单独 disable
  }
}
```

### 3.3 前端 Development 模式建议

- **流式数据**: LLM/SSE 流每 N 个 chunk 输出一次摘要，不逐 chunk 打印
- **API 调用**: 请求发起时打印 method + url，响应时打印 status + 耗时
- **状态变更**: Pinia store 变更时打印 action 名称 + 关键参数
- **组件生命周期**: 仅在排查问题时临时添加 mounted/unmounted 日志，不永久保留

---

## 四、后端日志规范

### 4.1 Logger 配置

```python
# core/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(env: str = "dev", log_dir: Path = None):
    """
    根据运行环境配置日志系统。
    - dev: DEBUG 级别，同时输出到 stdout 和文件
    - prod: INFO 级别，仅 WARN+ 输出到 stdout，全量写入文件
    """
    level = logging.DEBUG if env == "dev" else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_fmt = "%H:%M:%S" if env == "dev" else "%Y-%m-%d %H:%M:%S"

    handlers = []

    # stdout handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if env == "dev" else logging.WARNING)
    console.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    handlers.append(console)

    # file handler (always full)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_h = logging.handlers.RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_h.setLevel(logging.DEBUG)
        file_h.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
        handlers.append(file_h)

    logging.basicConfig(level=level, handlers=handlers, force=True)
```

### 4.2 后端 Production 模式规则

1. **stdout 仅输出 WARN+** — 减少容器日志噪音
2. **文件保留全量** — 方便事后排查
3. **日志轮转** — RotatingFileHandler 防止磁盘爆满
4. **结构化关键信息** — ERROR 日志必须包含: 时间、模块、操作、输入摘要、错误详情
5. **敏感信息脱敏** — API Key 仅显示前 4 位 + `***`，文件路径不暴露绝对系统路径

### 4.3 后端 Development 模式建议

- **请求/响应**: 使用 middleware 自动记录每个请求的 method/path/status/耗时
- **外部调用**: 调用 ComfyUI/LLM/TTS 前后各打一条 DEBUG（入参摘要 + 结果摘要）
- **子进程**: FFmpeg 命令完整打印（DEBUG），执行结果状态打印（INFO）
- **性能标记**: 耗时超过阈值的操作自动升级为 WARN

---

## 五、生命周期脚本日志规范

### 5.1 与 lifecycle-startup.md 联动

生命周期系统（`start.py` → `lifecycle.py`）的日志必须遵循同样的双模式原则。

**关键约束**: 启动脚本是前台常驻进程，子进程的 stdout/stderr 必须实时转发到终端（带服务名前缀），绝不重定向到 DEVNULL。这样开发者可以在一个终端窗口中同时看到前后端的实时日志流。

| 场景 | verbose 模式 | quiet 模式（默认 prod） |
|------|-------------|----------------------|
| 服务启动 | 打印完整命令、PID、工作目录、环境变量 | 仅打印 `✓ 服务名 已启动 (port:XXXX)` |
| 健康检查 | 每次轮询打印状态 | 仅打印最终结果 |
| 端口检测 | 打印扫描过程 | 仅在冲突时输出 |
| 进程停止 | 打印 kill 细节 | 仅打印 `✓ 服务名 已停止` |
| 僵尸清理 | 打印每个清理的 PID | 仅打印清理数量 |
| 依赖安装 | 完整 pip/npm 输出 | 仅打印安装结果摘要 |

### 5.2 实现方式

```python
# lifecycle.py 中的日志控制
import logging

logger = logging.getLogger("lifecycle")

def cmd_start(targets, open_browser=True, verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")
    
    # verbose 模式: 详尽输出
    logger.debug(f"启动命令: {cmd}")
    logger.debug(f"工作目录: {cwd}")
    logger.debug(f"环境变量: {env_vars}")
    
    # 两种模式都输出的关键信息
    logger.info(f"✓ {name} 已启动 (PID: {pid}, Port: {port})")
```

### 5.3 start.py 参数扩展

```python
p.add_argument("--verbose", "-v", action="store_true", help="输出详细日志")
```

---

## 六、日志内容规范

### 6.1 必须包含的上下文

每条日志必须让阅读者**无需翻代码**即可理解发生了什么：

```python
# ✅ 有上下文
logger.info("视频渲染完成: project=%s, shots=%d, duration=%.1fs", name, count, time)
logger.error("TTS 合成失败: shot_index=%d, text='%s...', error=%s", idx, text[:20], err)

# ❌ 无上下文
logger.info("完成")
logger.error("失败")
```

### 6.2 日志格式模板

| 场景 | 格式 |
|------|------|
| 流程开始 | `[模块] 开始: {操作}, 参数={关键参数}` |
| 流程结束 | `[模块] 完成: {操作}, 耗时={time}ms, 结果={摘要}` |
| 外部调用 | `[模块] 调用 {服务}: url={url}, payload_size={size}` |
| 外部响应 | `[模块] 响应 {服务}: status={code}, latency={ms}ms` |
| 状态变更 | `[模块] 状态变更: {from} → {to}, 原因={reason}` |
| 错误 | `[模块] 错误: {操作}失败, input={摘要}, error={message}` |
| 重试 | `[模块] 重试: {操作}, attempt={n}/{max}, delay={ms}ms` |

### 6.3 禁止事项

- ❌ **禁止日志中出现完整 API Key / Token / 密码**
- ❌ **禁止日志中出现完整 Base64 字符串**（截断到前 20 字符）
- ❌ **禁止日志中出现大型 JSON 完整 dump**（使用摘要或 key 列表）
- ❌ **禁止在循环体内每次迭代都打 INFO 日志**（用 DEBUG 或 N 次一打）
- ❌ **禁止日志中出现用户绝对文件路径**（Production 模式）

---

## 七、日志文件管理

### 7.1 文件结构

```
logs/
├── app.log              # 后端主日志（轮转）
├── app.log.1            # 轮转备份
├── lifecycle.log        # 启动/停止记录
├── error.log            # 仅 ERROR+ 级别（独立文件便于监控）
└── .pids.json           # PID 文件（非日志，但同目录管理）
```

### 7.2 轮转策略

| 文件 | 最大大小 | 保留数量 | 说明 |
|------|---------|---------|------|
| app.log | 10 MB | 5 份 | 主日志 |
| error.log | 5 MB | 10 份 | 错误日志保留更久 |
| lifecycle.log | 2 MB | 3 份 | 启停记录 |

### 7.3 清理规则

- 日志文件不纳入版本控制（`.gitignore` 包含 `logs/`）
- `--stop` 时不清理日志（保留排查依据）
- 可提供 `--clean-logs` 参数手动清理

---

## 八、运行时日志 UI（前端可选）

开发模式下，前端可提供可视化日志面板：

- **日志面板组件** — 展示运行时日志流（类似原项目的 LogPanel）
- **级别过滤** — 可按 INFO/WARN/ERROR 筛选
- **自动滚动** — 新日志自动滚到底部
- **导出** — 一键复制/下载日志文本
- **Production 模式** — 该面板仅显示 WARN+，或完全隐藏

---

## 九、变更检查清单

修改日志相关代码时，确认：

- [ ] 是否使用了封装的 logger 而非裸 `console` / `print`？
- [ ] DEBUG/TRACE 日志是否仅在 Dev 模式输出？
- [ ] Production 模式下前端控制台是否为零输出（除 warn/error）？
- [ ] 日志是否包含足够上下文（模块名、操作、关键参数）？
- [ ] 是否有敏感信息泄漏（API Key、完整路径、用户数据）？
- [ ] 循环内日志是否使用了 DEBUG 级别或采样输出？
- [ ] 日志文件是否配置了轮转，不会无限增长？
- [ ] 生命周期脚本是否支持 `--verbose` 切换？
- [ ] 新增的 ERROR 日志是否包含操作名称 + 输入摘要 + 错误详情？
