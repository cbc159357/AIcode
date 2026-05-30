---
description: 代码设计规范 — 所有代码变更必须遵循
trigger: always_on
---
# 代码设计规范 (Code Standards)

所有代码变更（新增、修改、重构）必须遵循以下规则。

## 架构

- **单一职责**：每个模块/类/函数只做一件事。
- **关注点分离**：视图层不含业务逻辑，服务层不持有UI状态，路由层不含算法。
- **依赖倒置**：高层模块通过接口通信，不直接依赖低层实现。
- **最少知识**：不链式访问深层属性（如 `a.b.c.d`）。

## 前后端分离

前端（`static-comic/`）与后端（`server/`）是物理隔离的两个进程，只通过 HTTP API + WebSocket 通信。

- **前端禁止包含后端逻辑**：不在 `.vue` / `.ts` 文件中执行文件系统操作、进程管理、数据库读写、系统命令调用或直接访问 `server/` 下的模块。
- **后端禁止包含前端逻辑**：不在 `.py` 文件中操作 DOM、管理 UI 状态、拼接 HTML/CSS 或直接导入前端代码。
- **数据交换唯一通道**：所有前后端数据流经 API 端点（`/api/v1/...`）或 WebSocket 消息，不通过共享文件、全局变量或内存传递。
- **路径/URL 构造归属**：文件系统绝对路径只在后端构造和使用；前端仅使用 API 返回的相对 URL（如 `/api/v1/files/{pid}/images/{filename}`）。
- **配置隔离**：后端配置在 `server/config.yaml`，前端配置在 `.env` + `import.meta.env`，不交叉引用。
- **Vue SFC 中禁止出现**：`import ... from '@/../../server/...'`、`fs`/`path`/`child_process` 等 Node.js 内置模块、`subprocess` 等 Python 模块。

## 文件与函数行数

- Vue SFC: ≤ 150 行(建议) / 300 行(硬限)
- TypeScript / JavaScript: ≤ 200 行(建议) / 400 行(硬限)
- Python 模块: ≤ 200 行(建议) / 400 行(硬限)
- CSS 样式: ≤ 300 行(建议) / 500 行(硬限)
- **单个函数体 ≤ 40 行**（不含空行和注释），超过必须拆分。

## DRY — 禁止重复

- 相同逻辑出现 ≥ 2 次必须提取为公共函数/组件/工具类。
- 前端提取到 `utils/`、`composables/` 或公共组件。
- 后端提取到 `core/`、`utils/` 或 service 层。

## 配置外置

- 禁止硬编码魔法数字、URL、端口。
- 前端使用 `.env` + `import.meta.env`。
- 后端使用 `config.yaml` 或环境变量。

## 命名

- Vue 组件文件: PascalCase (`ShotCard.vue`)
- TS/JS 变量/函数: camelCase; 类/类型: PascalCase
- Python 变量/函数: snake_case; 类: PascalCase
- 常量: UPPER_SNAKE_CASE
- CSS 工具类: kebab-case

## 导入顺序

1. 标准库 → 2. 第三方库 → 3. 项目内部模块，各组间空一行。

- **禁止在文件中部 import**。

## 类型安全

- TypeScript 使用 `strict: true`，禁止 `any`。
- Python 关键函数必须有类型注解。
- Vue props 使用 `defineProps<T>()` 泛型。

## 错误处理

- 不静默吞异常：`catch` 必须日志或上抛。
- 用户可见错误通过 toast/通知展示，不用 `alert()`。
- 后端统一错误格式 `{ error, detail? }`。

## 注释

- 写 Why 不写 What。
- 公共函数/类必须有 docstring (Python) 或 JSDoc (TS)。
- 不写废话注释。

## 版本控制

- Commit message: `<type>: <summary>` (feat/fix/refactor/style/docs/chore/test)
- 不提交 node_modules、.venv、__pycache__、.env。
