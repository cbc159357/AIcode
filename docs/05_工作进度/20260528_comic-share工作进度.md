# comic-share 重构工作进度

> 最后更新: 2026-05-28
> 关联计划: [20260528_comic-share重构计划.md](../01_项目管理/20260528_comic-share重构计划.md)
> 跨越会话: "Frontend Skeleton Implementation" → "Persistent Startup Script" → "Refactor Workflow Registry" → "Workflow Parameter Grouping" → "Refactor Param Display"

---

## 总体进度

| Phase | 名称 | 状态 | 完成度 |
|-------|------|------|--------|
| Phase 1 | 基础骨架 | ✅ 已完成 | 100% |
| Phase 2 | 配置与 LLM | ✅ 已完成 | 100% |
| Phase 3 | 生图引擎 | ✅ 已完成 | 100% |
| Phase 4 | TTS + 视频渲染 | ✅ 已完成 | 100% |
| Phase 5 | 流水线调度 + 批量 | ✅ 已完成 | 100% |
| Phase 6 | UI 组件化 + Arco 升级 | ✅ 已完成 | 100% |
| Lifecycle | 前台常驻启动 | ✅ 已完成 | 100% |
| UI 重构 | 布局重构 + 路由化 | ✅ 已完成 | 100% |
| 工作流注册表 | 前后端分离重构 | ✅ 已完成 | 100% |
| 引擎模式升级 | activeWorkflowId → activeEngine | ✅ 已完成 | 100% |
| 任务媒体管理 | 归档 + 子任务 + 媒体画廊 | ✅ 已完成 | 100% |
| 工作流 RH 集成 | RunningHub 实际调用去占位 | ✅ 已完成 | 100% |

---

## Phase 1 已完成内容

### 后端 (`backend/`)

- `main.py` — FastAPI 入口 + CORS + 异常处理 + lifespan，已注册全部 7 个 router（27 路由）
- `config.yaml` — 服务配置（LLM/ComfyUI/TTS/FFmpeg）
- `requirements.txt` — Python 依赖（fastapi, uvicorn, pyyaml, httpx, pydantic, python-multipart）
- `Dockerfile` — 容器镜像
- `core/config.py` — 配置加载（Pydantic Settings，热重载）
- `core/logging_config.py` — 日志系统（Dev/Prod 双模式）
- `core/exceptions.py` — 统一异常处理（AppError + 通用 handler）
- `routers/health.py` — 健康检查 + 外部服务状态（ComfyUI/TTS）
- `routers/config_api.py` — 配置 CRUD（脱敏 api_key）
- `data/workflows/` — ComfyUI 工作流存放目录

### 前端 (`frontend/`)

- Vite + Vue 3 + TypeScript + TailwindCSS + Arco Design Vue + Pinia 初始化
- `src/utils/logger.ts` — 日志工具（遵循 logging-standards.md）
- `src/utils/helpers.ts` — 通用工具函数
- `src/types/index.ts` — 全局类型定义（Shot, Character 等）
- `src/config/constants.ts` — 常量（13 风格 / 24 时代 / 8 尺寸 / 模型预设）
- `src/services/api.ts` — Axios 实例 + 拦截器 + BASE_URL
- `src/stores/app.ts` — 全局状态（服务状态/日志/进度）
- `src/stores/project.ts` — 项目状态（shots/characters/progress）+ setShots/setFinalVideo
- `src/views/WorkStation.vue` — 主工作台（三栏布局 + 分镜板/LLM Tab）
- `src/views/Settings.vue` — 设置页占位
- `src/components/layout/TopBar.vue` — 顶栏 + 服务状态灯
- `src/components/layout/LeftPanel.vue` — 左侧面板（故事输入 + 流程控制 + 配置Tab）
- `src/components/layout/RightPanel.vue` — 右侧面板（视频预览 + 进度条 + 日志）

### 基础设施

- `start.py` — 启动入口（薄触发，~29行）
- `lifecycle.py` — 生命周期管理（PID/端口/清理/日志转发）
- `docker-compose.yml` — 一键 Docker 启动
- `.gitignore` / `.env.example` / `README.md`

---

## Phase 2 已完成内容 — 配置与 LLM

### 后端新增

- `services/llm_service.py` — 多 Provider 流式调用（Ollama/vLLM/DeepSeek/OpenAI 兼容），SSE 透传
- `routers/llm.py` — `POST /api/v1/llm/models` + `POST /api/v1/llm/generate`（SSE 流式）

### 前端新增

- `stores/config.ts` — 全局配置状态（LLM provider/model/apiKey/temperature/maxTokens, image engine/model/size, tts url/voice, audio bgm/subtitle）
- `services/llm.ts` — SSE 流式客户端（EventSource fetch + onChunk/onDone/onError 回调）
- `components/config/LLMConfig.vue` — LLM 提供者/模型选择面板
- `components/config/StyleConfig.vue` — 画风 + 时代预设选择（a-select）
- `components/config/ImageConfig.vue` — 图片尺寸 + 生图模型选择
- `components/config/TTSConfig.vue` — TTS 服务地址 + 音色选择
- `components/config/AudioConfig.vue` — BGM + 字幕开关
- `components/preview/LLMOutput.vue` — 流式文本渲染（auto-scroll + 光标闪烁）

---

## Phase 3 已完成内容 — 生图引擎

### 后端新增

- `services/comfyui_service.py` — WebSocket 客户端 + 工作流管理 + 任务提交/轮询/输出提取（5018B）
- `services/rh_service.py` — RunningHub HTTP 轮询客户端（4338B）
- `routers/comfyui.py` — execute/upload/status/workflows/output 端点（3047B）
- `routers/runninghub.py` — RunningHub 创建任务 / 查询状态代理（1398B）

### 前端新增

- `services/comfyui.ts` — ComfyUI WebSocket 执行封装（executeWorkflow/getTaskStatus）
- `services/runninghub.ts` — RunningHub API 调用（createTask/getTaskStatus）
- `components/shots/ShotCard.vue` — 单张分镜卡片（图片 + 旁白 + 编辑/重生按钮）
- `components/shots/ShotGrid.vue` — 分镜网格容器（2-5列响应式）

---

## Phase 4 已完成内容 — TTS + 视频渲染

### 后端新增

- `services/tts_service.py` — CosyVoice API 调用（2146B）
- `services/render_service.py` — FFmpeg 视频渲染服务（动效 + 字幕 + BGM 合成，3722B）
- `routers/tts.py` — `POST /api/v1/tts/synthesize` + 参考音频列表（1180B）
- `routers/project.py` — save/render/export/import 端点（2556B）

### 前端新增

- `services/tts.ts` — TTS API 调用（synthesize）
- `services/compose.ts` — 渲染 API 调用（renderVideo/getOutput）

---

## Phase 5 已完成内容 — 流水线调度

### 前端新增

- `composables/usePipeline.ts` — 四步完整调度 composable（~227行）
  - Step 1: LLM 流式 → 解析 JSON → setShots
  - Step 2: ComfyUI/RunningHub 批量生图 → 轮询状态
  - Step 3: TTS 逐帧合成
  - Step 4: FFmpeg 渲染 → setFinalVideo
  - 统一状态管理: `idle | running | done | error`
- `composables/useServiceCheck.ts` — 服务健康轮询（30s 间隔，GET /health）

### WorkStation.vue 集成

- usePipeline composable 注入主视图
- 分镜板 + LLM 输出双 Tab 切换
- LeftPanel 接收 stepStatuses / storyText / runStep 事件

---

## Phase 6 已完成内容 — UI 组件化 + Arco Design

### Arco Design 升级

- 全部原生 `<select>` → `<a-select>`
- `<input type="range">` → `<a-slider>`
- `<input type="checkbox">` → `<a-checkbox>`
- `<textarea>` → `<a-textarea>`（auto-size）
- 步骤按钮 → `<a-button>`（loading/status/disabled 联动）
- 配置 Tab → `<a-radio-group type="button">`

### 主题

- Arco Design 暗色主题启用：`document.body.setAttribute('arco-theme', 'dark')`
- 自定义暗色滚动条 CSS（`main.css`）

---

## Lifecycle 前台常驻启动（本轮新增）

### 变更前

- `lifecycle.py` 使用 `CREATE_NEW_PROCESS_GROUP` 后台守护
- `stdout/stderr` 设为 `DEVNULL`（静默模式）
- 启动后 start.py 立即退出

### 变更后

- `lifecycle.py` 启动后 **前台常驻**，主线程 `while` 循环监控子进程
- 子进程 `stdout=PIPE` + `stderr=STDOUT`，独立线程实时转发日志到终端
- ANSI 颜色前缀：`[frontend]` cyan / `[backend]` yellow
- `signal.SIGINT` (Ctrl+C) → `_graceful_shutdown()` 优雅停止全部子进程
- 子进程异常退出自动检测并打印 warning
- 全部子进程退出后主进程自动结束
- PID 文件在 shutdown 时清空

### 关键代码改动

| 文件 | 改动 |
|------|------|
| `lifecycle.py` | 新增 `_stream_output()`, `_graceful_shutdown()`, signal 注册, 前台常驻循环 |
| `lifecycle.py` | Popen 参数: `text=True`, `bufsize=1`, `encoding="utf-8"`, `errors="replace"` |
| `lifecycle.py` | 移除 `CREATE_NEW_PROCESS_GROUP` — 不再需要后台守护 |
| `start.py` | 无变化（薄触发不受影响） |

---

## 验证结果

- ✅ `vue-tsc --noEmit` 零错误
- ✅ `vite build` 成功
- ✅ `python -c "from main import app; print(f'Routes: {len(app.routes)}')"` → 27 routes
- ✅ 前端 `localhost:5173` 运行正常
- ✅ 后端 `localhost:8080` 运行正常
- ✅ `python start.py` 前台常驻，Ctrl+C 优雅退出
- ✅ 日志实时转发，带颜色前缀

---

## 当前文件清单

### 后端 `backend/`

```
main.py, config.yaml, requirements.txt, Dockerfile
core/   config.py, logging_config.py, exceptions.py
routers/ health.py, config_api.py, llm.py, comfyui.py, runninghub.py, tts.py, project.py
services/ llm_service.py, comfyui_service.py, rh_service.py, tts_service.py, render_service.py
data/workflows/
```

### 前端 `frontend/src/`

```
main.ts, App.vue
views/       WorkStation.vue (弃用), AppLayout.vue, Settings.vue
stores/      app.ts, config.ts, project.ts
services/    api.ts, llm.ts, comfyui.ts, runninghub.ts, tts.ts, compose.ts
composables/ usePipeline.ts, useServiceCheck.ts
config/      constants.ts
types/       index.ts
utils/       logger.ts, helpers.ts
styles/      main.css
components/
  layout/    TopBar.vue, IconSidebar.vue, PreviewDrawer.vue, LeftPanel.vue, RightPanel.vue
  workspace/ WorkspaceView.vue
  workflow/  WorkflowManager.vue
  settings/  SettingsView.vue
  config/    LLMConfig.vue, StyleConfig.vue, ImageConfig.vue, TTSConfig.vue, AudioConfig.vue
  preview/   LLMOutput.vue
  shots/     ShotGrid.vue, ShotCard.vue
```

### 基础设施

```
start.py, lifecycle.py, docker-compose.yml
.gitignore, .env.example, README.md
```

---

## 待迁移数据（来自旧项目 `漫画分享/静态漫.html`）

### Prompt 模板

- `PROMPTS.ROLE_EXTRACT` — 角色提取
- `PROMPTS.REWRITE` — 故事改写
- `PROMPTS.SPLIT_SENTENCES` — 镜头拆分
- `PROMPTS.IMAGE_GEN_FUNC` — GACE Antigravity 导演 Prompt
- `ANTIGRAVITY_RULES` — 物理法则/角色锁/运镜法则
- 5 种快捷修正 system prompt

### ComfyUI 工作流

- T2I: nunchaku_qwen, z_image_turbo, z_image_turbo_a, z_image_gguf
- I2V: Wan2.1 (i2v_workflow_wan)
- Edit: Qwen Edit (qwen_edit_workflow)

### 风格/时代预设

- 13 种风格预设（已迁移到 `constants.ts`）
- 24 种时代背景预设（已迁移到 `constants.ts`）
- 8 种图片尺寸（已迁移到 `constants.ts`）
- 4 种视频分辨率

---

## UI 布局重构（本轮完成）

> 会话: "Refactor Workflow Registry"

### 设计方案

- 文档: [20260528_comic-share布局重构方案.md](../03_设计规范/20260528_comic-share布局重构方案.md)
- 布局: 图标侧栏 (w-14 / w-48 展开) + 路由主区域 + 右抽屉 (默认收起)
- 三模式: 工作台 `/` / 工作流 `/workflow` / 设置 `/settings`

### 新建文件

| 文件 | 说明 |
|------|------|
| `views/AppLayout.vue` | 全局布局壳（TopBar + IconSidebar + router-view + PreviewDrawer） |
| `components/layout/IconSidebar.vue` | 图标侧栏（router-link + 展开/收起切换） |
| `components/layout/PreviewDrawer.vue` | 右抽屉（a-drawer，含视频预览+进度+日志） |
| `components/workspace/WorkspaceView.vue` | 工作台模式（故事输入 + 4步流程 + 分镜/LLM Tab） |
| `components/workflow/WorkflowManager.vue` | 工作流模式（卡片网格 + 详情展开） |
| `components/settings/SettingsView.vue` | 设置模式（5个Config组件展开为独立卡片） |

### 修改文件

| 文件 | 改动 |
|------|------|
| `router/index.ts` | `/` → AppLayout 嵌套路由（workspace / workflow / settings） |
| `stores/app.ts` | 新增 `sidebarExpanded`，保留 `sidebarMode`/`previewDrawerOpen` |
| `components/layout/TopBar.vue` | 设置按钮 → 预览抽屉按钮 |
| `views/WorkStation.vue` | 弃用（布局迁移到 AppLayout.vue，路由已断开） |

### 验证

- ✅ `vue-tsc --noEmit` 零错误
- ✅ `vite build` 成功

---

## 工作流注册表实现（本轮完成）

> 会话: "Refactor Workflow Registry"
> 设计文档: [20260528_工作流注册表方案.md](../03_设计规范/20260528_工作流注册表方案.md)

### 核心改动

- 前端不再知道 RunningHub `nodeId`/`fieldName` 或 ComfyUI `replacements` 格式
- `imageEngine` + `imageModel` → `activeWorkflowId` → `activeEngine`（引擎模式）
- 用户选择**引擎模式**（runninghub / comfyui_local / direct_api），后端自动解析默认工作流
- 新增工作流 = 在 `config.yaml` 加一段配置，零代码改动

### 后端新增

| 文件 | 说明 |
|------|------|
| `config.yaml` workflows 节 | 4 条注册表记录（rh_t2i_default, comfyui_nunchaku_qwen, comfyui_z_image_turbo, rh_i2v_wan21） |
| `services/workflow_service.py` | 注册表读取 + execute 分发 + 统一状态查询（归一化响应） |
| `routers/workflow.py` | 薄路由（list/active/execute/task-status） |
| `main.py` | 注册 workflow router（31 路由） |

### 前端新增/修改

| 文件 | 说明 |
|------|------|
| `services/workflow.ts` | 新建 — listEngines / listWorkflows / executeWorkflow / getTaskStatus |
| `stores/config.ts` | `imageEngine`+`imageModel` → `activeEngine`（引擎模式） |
| `composables/usePipeline.ts` | runStep2 传 configStore.activeEngine，调统一 workflow API |
| `components/workflow/WorkflowManager.vue` | 引擎下拉 + 工作流列表 + 引擎图标/默认标签 |
| `components/config/ImageConfig.vue` | 引擎模式下拉选择器 |
| `config/constants.ts` | 删除 `T2I_MODELS`、`IMAGE_ENGINE_MODES` |

---

## 验证结果

- ✅ `vue-tsc --noEmit` 零错误
- ✅ `vite build` 成功
- ✅ 后端加载 32 路由（含 engines API，3 个已启用工作流，默认引擎 runninghub）
- ✅ 前端无 `imageEngine`/`imageModel`/`activeWorkflowId` 残留引用

---

## 任务媒体管理（本轮完成）

> 会话: "Fixing Window Minimize Bug"

### 后端新增

| 文件 | 说明 |
|------|------|
| `services/archive_service.py` | 归档 + 子任务文件系统 CRUD（list/create/rename/delete/media 扫描） |
| `routers/archives.py` | 10 个端点 `/api/v1/archives/...` + 静态文件服务 |
| `main.py` | 注册 archives router（42 路由） |

### 前端新增

| 文件 | 说明 |
|------|------|
| `services/archives.ts` | 归档/任务/媒体 API 调用层 |
| `types/index.ts` | Archive / Task / MediaItem 类型 |
| `views/TaskManager.vue` | `/tasks` 路由页面（归档选择 + 子任务列表 + 媒体画廊） |
| `components/tasks/ArchiveBar.vue` | 归档选择栏（后移入工作台左侧面板） |
| `components/tasks/MediaGallery.vue` | 媒体网格画廊 + 下拉筛选（全部/图片/音频/视频） |
| `components/layout/IconSidebar.vue` | 侧栏新增「任务」入口 |
| `router/index.ts` | 新增 `/tasks` 路由 |

### 布局调整

- 工作台页面归档选择器移入 aside 左侧面板顶部
- 媒体筛选从 Tab 按钮改为 `a-select` 下拉框（顶栏右侧）

---

## 工作流 RunningHub 集成（本轮完成）

> 会话: "Fixing Window Minimize Bug"
> 设计文档: [20260528_工作流页面实现计划.md](../02_技术文档/前端/20260528_工作流页面实现计划.md)

### 后端新增

| 文件 | 说明 |
|------|------|
| `core/runninghub_client.py` | RH API 客户端（迁移自 Old/server/core/），含 NODE_TYPE_MAP 规则解析 |
| `routers/runninghub.py` | 12 端点：连接测试/工作流拉取分析/任务调度/配置管理 |
| `config.yaml` | 新增 `runninghub:` 配置节（keys/proxy/active_key_type） |

### 前端新增/重构

| 文件 | 说明 |
|------|------|
| `services/runninghub.ts` | 完整 RH API 层（test/fetch/analyze/task/config/workflow CRUD） |
| `components/workflow/RHConfigCard.vue` | API Key + 代理配置卡片 |
| `components/workflow/WorkflowCard.vue` | 工作流卡片（展开/收起 + 参数编辑 + 任务执行） |
| `components/workflow/ParamEditor.vue` | 可调参数编辑器（text/number 类型 + 优先级颜色） |
| `components/workflow/TaskRunner.vue` | 任务提交/轮询/取消/输出预览 |
| `components/workflow/WorkflowManager.vue` | 去占位重构：RH 配置 + 添加工作流 + 工作流列表 |

### 核心能力

- **添加工作流**: 输入 RunningHub 工作流 ID → 自动拉取 JSON → 规则解析可调参数 → 保存
- **参数编辑**: 展开卡片编辑各节点参数（提示词/种子/步数/尺寸等）
- **任务执行**: 提交 → 3s 轮询 → 状态显示（排队/运行/完成/失败） → 输出预览
- **配置管理**: API Key（个人版/企业版）+ 代理 + 连通性测试

---

## 当前文件清单（更新）

### 后端 `backend/`

```
main.py, config.yaml, requirements.txt, Dockerfile
core/   config.py, logging_config.py, exceptions.py, runninghub_client.py
routers/ health.py, config_api.py, llm.py, comfyui.py, runninghub.py, tts.py, project.py, workflow.py, archives.py
services/ llm_service.py, comfyui_service.py, rh_service.py, tts_service.py, render_service.py, workflow_service.py, archive_service.py
data/    workflows/, runninghub/workflows/, archives/
```

### 前端 `frontend/src/`

```
main.ts, App.vue
views/       AppLayout.vue, Settings.vue, TaskManager.vue
stores/      app.ts, config.ts, project.ts
services/    api.ts, llm.ts, comfyui.ts, runninghub.ts, tts.ts, compose.ts, workflow.ts, archives.ts
composables/ usePipeline.ts, useServiceCheck.ts
config/      constants.ts
types/       index.ts
utils/       logger.ts, helpers.ts
styles/      main.css
components/
  layout/    TopBar.vue, IconSidebar.vue, PreviewDrawer.vue
  workspace/ WorkspaceView.vue
  workflow/  WorkflowManager.vue, RHConfigCard.vue, WorkflowCard.vue, ParamEditor.vue, TaskRunner.vue
  settings/  SettingsView.vue
  config/    LLMConfig.vue, StyleConfig.vue, ImageConfig.vue, TTSConfig.vue, AudioConfig.vue
  preview/   LLMOutput.vue
  shots/     ShotGrid.vue, ShotCard.vue
  tasks/     MediaGallery.vue
```

---

## 验证结果（更新）

- ✅ `vue-tsc --noEmit` 零错误
- ✅ `vite build` 成功
- ✅ 后端 42 路由
- ✅ RunningHub 工作流拉取/分析/任务执行链路完整
- ✅ 任务管理页面归档 CRUD + 媒体画廊可用

---

## 下一步

1. **Settings 页面改造** — RH 配置移入设置页 + 左右布局 + 卡片拖拽排序
2. **填入实际 RunningHub 工作流 ID** — config.yaml 中 `rh_workflow_id` 待填
3. **Prompt 模板迁移** — 从旧项目提取到后端 service
4. **工作流 JSON 迁移** — 从旧项目复制到 `data/workflows/`
5. **端到端联调** — 实际接入 LLM / ComfyUI / TTS 服务测试

---

## 图片输入语义标注 + 参数分组（本轮完成）

> 会话: "Workflow Parameter Grouping"
> 设计文档: [20260528_参数分组显示设计.md](../02_技术文档/前端/20260528_参数分组显示设计.md)
> 术语表: `comic-share/CONTEXT.md`（首次创建）

### 一、图片输入语义标注（imageInputs）

#### 后端新增

| 文件 | 改动 |
|------|------|
| `core/runninghub_client.py` | 新增 `infer_image_inputs()` — BFS 推断引擎（`_build_downstream_map` + `_infer_role_bfs`），`_DOWNSTREAM_ROLE_MAP` 30+ 节点类型 → 7 种语义角色，结果按 reference→face→style→pose→mask→background→internal 排序 |
| `routers/runninghub.py` | `save_workflow` 自动调用 `infer_image_inputs()` 写入 `imageInputs`；新增 `PUT /workflow/{id}/image-inputs`；新增 `POST /upload` 转发图片到 RH 返回 `fileName` |

#### 前端新增/修改

| 文件 | 改动 |
|------|------|
| `services/runninghub.ts` | 新增 `ImageInputRole` / `ImageInput` 类型；新增 `updateImageInputs()` / `uploadImageToRH()` API |
| `components/workflow/ImageInputAnnotator.vue` | **新建** — 标注弹窗，7 种角色切换 + 标签编辑 + PUT 保存 |
| `components/workflow/ParamEditor.vue` | 新增 `excludeNodeIds` prop，过滤掉被 imageInputs 管理的 LoadImage 参数 |
| `components/workflow/WorkflowCard.vue` | 展开区新增「图片输入」区块：角色徽章 + 逐行上传控件 + 「标注语义」按钮 |
| `components/workflow/TaskRunner.vue` | 新增 `extraNodeInfo` prop，提交任务时自动合并图片 fileName |

### 二、工作流 URL 解析优化

- `components/workflow/WorkflowManager.vue` — 新增 `extractWorkflowId()` 函数，支持粘贴 RunningHub 完整 URL 自动提取工作流 ID；输入框宽度 w-48 → w-64，placeholder 更新为「工作流 ID 或完整 URL」

### 三、参数功能分组（paramGroups）

**数据结构**：`ParamGroup { groupId, title, defaultCollapsed, nodeIds[] }`，存入工作流 JSON，与 `analyzedParams` 互补（向后兼容）

**分组规则**（`_GROUP_DEFINITIONS`）：

| groupId | title | defaultCollapsed | 匹配 class_type |
|---------|-------|-----------------|----------------|
| `prompt` | 提示词 | false | CLIPTextEncode, JjkText, CR Prompt Text, PrimitiveStringMultiline |
| `sampling` | 采样控制 | false | KSampler, KSamplerAdvanced, SamplerCustom, Seed (rgthree), FluxGuidance |
| `resolution` | 分辨率 | false | EmptyLatentImage, EmptySD3LatentImage, TTResolutionSelector |
| `model` | 模型配置 | true | *Loader 类（UNETLoader/CLIPLoader/VAELoader 等） |
| `output` | 输出设置 | true | SaveImage, PreviewImage, VHS_VideoCombine |
| `llm_node` | AI 模型调用 | true | RH_LLMAPI_Pro_Node |
| `other` | 其他参数 | false | 以上均不匹配的剩余节点 |

#### 后端改动

| 文件 | 改动 |
|------|------|
| `core/runninghub_client.py` | 新增 `group_params_by_function(nodes_json, analyzed_params, image_node_ids)` — 按 class_type 启发式分组，imageInputs nodeId 互斥排除，空组不生成 |
| `routers/runninghub.py` | `save_workflow` 调用 `group_params_by_function()` 并存储 `paramGroups` 字段 |

#### 前端改动

| 文件 | 改动 |
|------|------|
| `services/runninghub.ts` | 新增 `ParamGroup` interface；`RHWorkflowDetail` 新增 `paramGroups?` 字段 |
| `components/workflow/ParamGroup.vue` | **新建** — 可折叠组件：标题栏（折叠箭头 + 组名 + 参数数 badge）+ 内部参数行（含节点 ID 天蓝色徽章） |
| `components/workflow/ParamEditor.vue` | 重构：有 `paramGroups` → 按组渲染 `ParamGroup` + 未分组区块；无 `paramGroups` → 保持平铺（向后兼容） |
| `components/workflow/WorkflowCard.vue` | 加载 `paramGroups` 并传入 `ParamEditor` |

### 四、Bug 修复：RH_LLMAPI_Pro_Node 误分组

- **问题**：豆包模型名称、temperature、max_tokens 等字段被归入「提示词」组
- **根因**：`RH_LLMAPI_Pro_Node` 是 AI 模型调用节点，不是文本提示节点，不应在 prompt 组
- **修复**：从 prompt 组移出，单独建立「AI 模型调用」组（`llm_node`，默认折叠）
- **生效方式**：重新「拉取 & 保存」工作流即可，已保存的工作流需重新保存一次

### 五、节点 ID 徽章样式统一

三处（`ParamGroup.vue` 组内行、`ParamEditor.vue` 未分组行、平铺模式行）节点 ID 徽章统一为：天蓝色文字 + 深蓝底 + 蓝色边框

---

## 验证结果（更新）

- ✅ `vue-tsc --noEmit` 零错误
- ✅ `vite build` 成功
- ✅ 后端 42 路由
- ✅ RunningHub 工作流拉取/分析/任务执行链路完整
- ✅ 任务管理页面归档 CRUD + 媒体画廊可用
- ✅ 图片输入语义推断 + 标注弹窗完整
- ✅ 参数功能分组渲染（折叠/展开），vue-tsc 零错误，vite build 成功
- ✅ RH_LLMAPI_Pro_Node 独立成「AI 模型调用」组，不再混入提示词

---

## 参数显示重构（本轮完成）

> 会话: "Refactor Param Display"

### 一、参数行 nodeId 合并 + 双布局架构

**问题**：旧实现将同节点多个字段（如 `UNETLoader` 的 `unet_name` + `weight_dtype`）拆成独立多行，语义割裂且溢出。

**方案**：两种布局按字段数量自动切换：

| 场景 | 布局 | 结构 |
|------|------|------|
| 单字段节点 | 传统横向行 | 节点 ID 徽章 + 节点类名 + 字段标签 + 全宽输入框 |
| 多字段节点 | 节点头 + CSS Grid | 节点头（ID + 类名）+ `grid auto-fill minmax(140px,1fr)` 网格，长文本 `col-span-full` |

**共用函数**：
- `toNodeGroups(list)` — 按 nodeId 合并，保留首次出现顺序
- `nodeClass(p)` — 优先用 `p.nodeTitle`，回退到 description 首词
- `fieldFullWidth(param, total)` — 多字段节点中长文本（>50 字符）独占整行

#### 改动文件

| 文件 | 改动 |
|------|------|
| `components/workflow/ParamGroup.vue` | 重构：`nodeGroups` computed（按 nodeId 合并）；组内单字段行 / 多字段节点头 + 网格双布局 |
| `components/workflow/ParamEditor.vue` | 重构：新增 `toNodeGroups()` helper；`ungroupedNodeGroups` + `flatNodeGroups` computed；未分组区 + 平铺模式同步采用双布局 |

### 二、nodeTitle 字段提取

**问题**：`nodeClass()` 原来解析 `description` 字符串的首词，不稳定（含中文/标点时截断错误）。

**方案**：`RHWorkflowParam` 新增可选字段 `nodeTitle?: string`，由后端分析时提取工作流 JSON 中节点的 `_meta.title`（用户自定义节点名），前端 `nodeClass()` 优先使用该字段。

| 文件 | 改动 |
|------|------|
| `services/runninghub.ts` | `RHWorkflowParam` 新增 `nodeTitle?: string` |
| `core/runninghub_client.py` | `analyze_workflow()` 提取 `node_data.get("_meta", {}).get("title")` 写入 param |

### 三、字段排序优化（UNET → VAE → CLIP）

**问题**：同节点多字段展示顺序不符合 ComfyUI 从上到下的习惯（如模型名应在 weight_dtype 之前）。

**方案**：后端 `analyze_workflow()` 按节点在 JSON 中的原始字段顺序生成 params，确保前端网格中左→右对应 ComfyUI 上→下顺序。模型组内节点排序按 `_GROUP_DEFINITIONS` 中的 UNET → VAE → CLIP 顺序分配 nodeId。

### 四、节点类名着色升级

三处（`ParamGroup.vue` 组内 / `ParamEditor.vue` 未分组 / 平铺模式）节点类名从 `text-gray-500` 统一升级为 `text-cyan-300 font-medium`，与节点 ID 天蓝徽章形成视觉关联。

### 五、模型兼容性替换方案探讨文档

探讨当用户修改 UNET 模型时如何处理 CLIP/VAE/LoRA 联动兼容性问题，四方案评审：

| 方案 | 描述 | 结论 |
|------|------|------|
| A — 模型预设包 | 用户手动创建联动字段预设 | Phase 2 实施 |
| B — 架构族推断 + 警告 | 文件名正则推断，跨族修改弹出警告 | Phase 1 简化版 |
| C — 依赖图 BFS | 复用现有 BFS 识别模型联动组 | Phase 1 |
| D — RH 官方模型元数据 API ⭐ | `/openapi/v2/resource/list` 获取 `baseModel` 字段缓存本地 | **推荐，Phase 1** |

文档路径：`docs/02_技术文档/通用/20260528_模型兼容性替换方案.md`（规划中，待创建）

---

## 验证结果（更新）

- ✅ `vue-tsc --noEmit` 零错误
- ✅ `vite build` 成功
- ✅ 后端 42 路由
- ✅ RunningHub 工作流拉取/分析/任务执行链路完整
- ✅ 图片输入语义推断 + 标注弹窗完整
- ✅ 参数功能分组渲染（折叠/展开）
- ✅ 同节点多字段合并行显示，单/多字段双布局正确渲染
- ✅ 节点类名优先显示 nodeTitle，cyan 着色

---

## 当前文件清单（更新）

### 后端 `backend/`

```
main.py, config.yaml, requirements.txt, Dockerfile
core/   config.py, logging_config.py, exceptions.py, runninghub_client.py
routers/ health.py, config_api.py, llm.py, comfyui.py, runninghub.py, tts.py, project.py, workflow.py, archives.py
services/ llm_service.py, comfyui_service.py, rh_service.py, tts_service.py, render_service.py, workflow_service.py, archive_service.py
data/    workflows/, runninghub/workflows/, archives/
```

### 前端 `frontend/src/`

```
main.ts, App.vue
views/       AppLayout.vue, Settings.vue, TaskManager.vue
stores/      app.ts, config.ts, project.ts
services/    api.ts, llm.ts, comfyui.ts, runninghub.ts, tts.ts, compose.ts, workflow.ts, archives.ts
composables/ usePipeline.ts, useServiceCheck.ts
config/      constants.ts
types/       index.ts
utils/       logger.ts, helpers.ts
styles/      main.css
components/
  layout/    TopBar.vue, IconSidebar.vue, PreviewDrawer.vue
  workspace/ WorkspaceView.vue
  workflow/  WorkflowManager.vue, RHConfigCard.vue, WorkflowCard.vue,
             ParamEditor.vue, ParamGroup.vue, TaskRunner.vue,
             ImageInputAnnotator.vue
  settings/  SettingsView.vue
  config/    LLMConfig.vue, StyleConfig.vue, ImageConfig.vue, TTSConfig.vue, AudioConfig.vue
  preview/   LLMOutput.vue
  shots/     ShotGrid.vue, ShotCard.vue
  tasks/     MediaGallery.vue
```

### 文档

```
docs/02_技术文档/前端/20260528_参数分组显示设计.md  ← 新增
comic-share/CONTEXT.md                               ← 新增（术语表）
```
