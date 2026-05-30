# comic-share 重构计划

> 将 `漫画分享` 单体 HTML+Flask 项目重构为符合代码规范的前后端分离项目。
> 创建日期: 2026-05-28

---

## 一、决策摘要

| 决策项 | 结论 |
|--------|------|
| 新项目位置 | `d:\AI生成动漫\comic-share\` |
| 前端框架 | Vue 3 + Vite + TypeScript + TailwindCSS + Pinia + Arco Design Vue |
| 后端框架 | FastAPI + Uvicorn + Pydantic |
| 功能范围 | 全部保留，1:1 重构 |
| UI 设计 | 完全重新设计（实施前提供多方案选择） |
| 图片引擎 | 本地 ComfyUI + RunningHub 双模式 |
| TTS 服务 | CosyVoice（保持现有） |
| 工作流存储 | 后端 `data/workflows/` + API 管理 |
| LLM 配置 | 后端 `config.yaml` 统一管理 |
| 环境部署 | Docker Compose |
| 参考来源 | 仅复现 `漫画分享` 功能，不参考主项目架构 |

---

## 二、技术栈详情

### 前端

| 类别 | 选型 | 版本 |
|------|------|------|
| 框架 | Vue 3 (Composition API) | ^3.4 |
| 构建 | Vite | ^5.x |
| 语言 | TypeScript (strict) | ^5.x |
| 样式 | TailwindCSS | ^3.4 |
| 组件库 | Arco Design Vue | ^2.x |
| 状态管理 | Pinia | ^2.x |
| 路由 | Vue Router | ^4.x |
| HTTP | Axios | ^1.x |
| 图标 | @iconify/vue (Lucide) | latest |

### 后端

| 类别 | 选型 | 版本 |
|------|------|------|
| 框架 | FastAPI | ^0.110 |
| 运行时 | Uvicorn | ^0.29 |
| 数据校验 | Pydantic v2 | ^2.x |
| 配置管理 | PyYAML | ^6.x |
| 跨域 | fastapi CORS middleware | 内置 |
| 子进程 | asyncio subprocess | 标准库 |
| HTTP 客户端 | httpx | ^0.27 |

### 基础设施

| 类别 | 选型 |
|------|------|
| 容器化 | Docker + Docker Compose |
| FFmpeg | 镜像内预装 |
| 开发端口 | 前端 5173, 后端 8080 |

---

## 三、目录结构

```
comic-share/
├── docker-compose.yml          # 一键启动
├── .env.example                # 环境变量模板
├── README.md                   # 项目说明
│
├── frontend/                   # 前端 (Vue 3)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── .env                    # VITE_API_BASE_URL 等
│   ├── index.html
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── router/
│       │   └── index.ts
│       ├── stores/
│       │   ├── app.ts          # 全局状态(服务状态、日志)
│       │   ├── config.ts       # 配置状态(LLM/TTS/ComfyUI URL)
│       │   ├── project.ts      # 项目状态(shots/characters/progress)
│       │   └── pipeline.ts     # 流水线状态(当前步骤/进度)
│       ├── services/
│       │   ├── api.ts          # Axios 实例 + BASE_URL
│       │   ├── llm.ts          # LLM 流式调用
│       │   ├── comfyui.ts      # ComfyUI WebSocket 执行
│       │   ├── runninghub.ts   # RunningHub API
│       │   ├── tts.ts          # CosyVoice API
│       │   ├── compose.ts      # 合成服务 API
│       │   └── project.ts      # 项目导入/导出
│       ├── composables/
│       │   ├── useServiceCheck.ts   # 服务状态检测
│       │   ├── usePipeline.ts       # 四步流水线调度
│       │   └── useLogger.ts         # 日志系统
│       ├── views/
│       │   ├── WorkStation.vue      # 主工作台（三栏布局）
│       │   └── Settings.vue         # 设置页
│       ├── components/
│       │   ├── layout/
│       │   │   ├── TopBar.vue       # 顶部导航 + 服务状态
│       │   │   ├── LeftPanel.vue    # 左侧配置面板容器
│       │   │   └── RightPanel.vue   # 右侧预览/日志容器
│       │   ├── config/
│       │   │   ├── LLMConfig.vue        # LLM 提供者/模型选择
│       │   │   ├── StyleConfig.vue      # 风格+时代预设
│       │   │   ├── ImageConfig.vue      # 图片尺寸+生图模型
│       │   │   ├── AudioConfig.vue      # BGM+字幕
│       │   │   └── TTSConfig.vue        # TTS 设置
│       │   ├── pipeline/
│       │   │   ├── StepButtons.vue      # 四步走按钮组
│       │   │   ├── ProgressBar.vue      # 进度条
│       │   │   ├── BatchControl.vue     # 批量模式控制
│       │   │   └── ModeToggles.vue      # 低显存/改图模式
│       │   ├── shots/
│       │   │   ├── ShotGrid.vue         # 分镜网格容器
│       │   │   ├── ShotCard.vue         # 单个分镜卡片
│       │   │   └── ShotEditModal.vue    # 图片修正模态框
│       │   ├── preview/
│       │   │   ├── VideoPlayer.vue      # 视频预览
│       │   │   ├── LLMOutput.vue        # LLM 流式输出
│       │   │   └── LogPanel.vue         # 运行日志
│       │   └── common/
│       │       ├── StatusDot.vue        # 状态圆点
│       │       └── StoryInput.vue       # 故事文本输入
│       ├── config/
│       │   └── constants.ts     # 常量(风格预设、时代预设、图片尺寸等)
│       ├── types/
│       │   └── index.ts         # 全局类型定义
│       └── utils/
│           └── helpers.ts       # 工具函数
│
├── backend/                    # 后端 (FastAPI)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── main.py                 # FastAPI 入口
│   ├── config.yaml             # 服务配置
│   ├── core/
│   │   ├── config.py           # 配置加载(Pydantic Settings)
│   │   └── exceptions.py       # 统一异常处理
│   ├── routers/
│   │   ├── health.py           # GET /api/health
│   │   ├── config_api.py       # GET/PUT /api/config
│   │   ├── llm.py              # POST /api/llm/models, POST /api/llm/generate
│   │   ├── comfyui.py          # POST /api/comfyui/execute, POST /api/comfyui/upload
│   │   ├── runninghub.py       # RunningHub 代理 API
│   │   ├── tts.py              # POST /api/tts/synthesize, GET /api/tts/audios
│   │   ├── project.py          # 项目数据 CRUD (save/render)
│   │   └── batch.py            # 批量模式 API
│   ├── services/
│   │   ├── llm_service.py      # LLM 流式调用逻辑
│   │   ├── comfyui_service.py  # ComfyUI WebSocket 客户端
│   │   ├── rh_service.py       # RunningHub 客户端
│   │   ├── tts_service.py      # CosyVoice 调用逻辑
│   │   ├── render_service.py   # FFmpeg 视频渲染
│   │   └── project_service.py  # 项目文件管理
│   └── data/
│       ├── workflows/          # ComfyUI 工作流 JSON
│       │   ├── t2i_nunchaku_qwen.json
│       │   ├── t2i_z_image_turbo.json
│       │   ├── t2i_z_image_turbo_a.json
│       │   ├── t2i_z_image_gguf.json
│       │   ├── i2v_wan21.json
│       │   └── edit_qwen.json
│       └── output/             # 项目产物输出
│           ├── batch_input/
│           └── batch_output/
│
└── ffmpeg/                     # FFmpeg 二进制(或 Docker 内置)
    ├── ffmpeg.exe
    ├── ffprobe.exe
    └── font.ttf
```

---

## 四、功能模块映射

### 从旧项目到新项目的模块映射

| 旧项目功能 | 新前端组件/服务 | 新后端模块 |
|-----------|---------------|-----------|
| CONFIG 对象 | `stores/config.ts` | `config.yaml` + `routers/config_api.py` |
| STATE 对象 | `stores/project.ts` + `stores/pipeline.ts` | — |
| checkServices() | `composables/useServiceCheck.ts` | `routers/health.py` |
| callLLMStream() | `services/llm.ts` | `routers/llm.py` + `services/llm_service.py` |
| T2I_WORKFLOWS | — | `data/workflows/*.json` + `routers/comfyui.py` |
| executeComfyWorkFlow() | `services/comfyui.ts` | `services/comfyui_service.py` |
| generateTTSAudio() | `services/tts.ts` | `routers/tts.py` + `services/tts_service.py` |
| save_data (Flask) | — | `routers/project.py` + `services/project_service.py` |
| render_video (Flask) | — | `routers/project.py` + `services/render_service.py` |
| PROMPTS 模板 | `config/constants.ts` (仅模板) | `services/llm_service.py` (拼接逻辑) |
| runStep1~4 | `composables/usePipeline.ts` | 后端无状态，前端调度 |
| renderShots() | `components/shots/ShotGrid.vue` | — |
| openReviewModal() | `components/shots/ShotEditModal.vue` | — |
| 批量模式 | `components/pipeline/BatchControl.vue` | `routers/batch.py` |
| 导出/导入 | `services/project.ts` | `routers/project.py` |

---

## 五、API 设计

### 5.1 基础

- 前缀: `/api/v1/`
- 错误格式: `{ "error": "message", "detail": "optional" }`
- 流式响应: SSE (`text/event-stream`)

### 5.2 端点清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 + 各服务状态 |
| GET | `/api/v1/config` | 获取当前配置 |
| PUT | `/api/v1/config` | 更新配置 |
| POST | `/api/v1/llm/models` | 获取 LLM 模型列表 |
| POST | `/api/v1/llm/generate` | 流式生成 (SSE) |
| GET | `/api/v1/workflows` | 列出可用工作流 |
| GET | `/api/v1/workflows/{id}` | 获取工作流详情 |
| POST | `/api/v1/comfyui/execute` | 提交 ComfyUI 任务 |
| POST | `/api/v1/comfyui/upload` | 上传图片到 ComfyUI |
| GET | `/api/v1/comfyui/status/{prompt_id}` | 查询任务状态 |
| POST | `/api/v1/rh/task/create` | RunningHub 创建任务 |
| GET | `/api/v1/rh/task/status/{task_id}` | RunningHub 任务状态 |
| GET | `/api/v1/tts/audios` | TTS 参考音频列表 |
| POST | `/api/v1/tts/synthesize` | TTS 合成 |
| POST | `/api/v1/project/save` | 保存项目数据(图/音/字幕) |
| POST | `/api/v1/project/render` | 视频渲染 |
| GET | `/api/v1/project/output/{path}` | 下载产物 |
| POST | `/api/v1/project/export` | 导出项目 JSON |
| POST | `/api/v1/project/import` | 导入项目 JSON |
| GET | `/api/v1/batch/scan` | 扫描批量输入 |
| POST | `/api/v1/batch/check-role` | 角色复用检查 |

### 5.3 关键 SSE 事件格式

```
event: chunk
data: {"content": "LLM生成的文本片段"}

event: done
data: {"full_response": "完整文本"}

event: error
data: {"error": "错误信息"}
```

---

## 六、前后端交互变更（对比旧项目）

### 旧项目问题

1. **前端直接调 ComfyUI** — 跨域、无鉴权、泄露内网地址
2. **前端直接调 LLM** — 同上
3. **Base64 传文件** — 内存占用大，请求体膨胀
4. **前端硬编码工作流 JSON** — 无法热更新

### 新项目改进

1. **所有 AI 服务调用经后端代理** — 前端只与自己的后端通信
2. **文件传输用 multipart/form-data** — 不再 Base64 编码
3. **LLM 流式经后端 SSE 透传** — 前端 EventSource 接收
4. **工作流由后端管理** — 前端通过 API 获取可用列表

---

## 七、实施阶段

### Phase 1: 基础骨架 (Day 1-2)

- [ ] 创建项目目录结构
- [ ] 初始化前端 (Vite + Vue 3 + TS + Tailwind + Arco)
- [ ] 初始化后端 (FastAPI + 配置加载)
- [ ] Docker Compose 配置
- [ ] 健康检查 API + 前端服务状态组件

### Phase 2: 配置与 LLM (Day 3-4)

- [ ] 后端配置 CRUD API
- [ ] LLM 代理层 (多 Provider 支持 + SSE 流式)
- [ ] 前端配置面板组件 (LLM/Style/Image/TTS)
- [ ] 前端 LLM 流式输出组件

### Phase 3: 生图引擎 (Day 5-6)

- [ ] 后端 ComfyUI 代理 (WebSocket 监听 + 任务管理)
- [ ] 后端 RunningHub 代理 (HTTP 轮询)
- [ ] 工作流 JSON 文件管理 API
- [ ] 前端生图调用 + 分镜卡片渲染

### Phase 4: TTS + 视频渲染 (Day 7-8)

- [ ] 后端 TTS 代理 (CosyVoice)
- [ ] 后端 FFmpeg 渲染服务 (动效 + 字幕 + BGM)
- [ ] 前端 TTS 配置 + 调用
- [ ] 前端视频预览 + 下载

### Phase 5: 流水线调度 + 批量 (Day 9-10)

- [ ] 前端四步流水线 composable
- [ ] 低显存模式 / 改图模式
- [ ] 图片修正模态框 (普通+编辑双模式)
- [ ] 批量模式 (扫描 + 循环执行)
- [ ] 项目导入/导出

### Phase 6: UI 设计实施 + 打磨 (Day 11-12)

- [ ] 提供 2-3 种 UI 方案供选择
- [ ] 实施确认的 UI 方案
- [ ] 响应式适配
- [ ] 构建验证 (vue-tsc + vite build 零错误)

---

## 八、Docker Compose 设计

```yaml
version: "3.8"

services:
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src
    environment:
      - VITE_API_BASE_URL=http://localhost:8080
    command: npm run dev -- --host

  backend:
    build: ./backend
    ports:
      - "8080:8080"
    volumes:
      - ./backend:/app
      - ./ffmpeg:/app/ffmpeg
      - ./backend/data/output:/app/data/output
    environment:
      - CONFIG_PATH=/app/config.yaml
    command: uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

开发阶段可不用 Docker，直接：
- 前端: `cd frontend && npm run dev`
- 后端: `cd backend && uvicorn main:app --reload --port 8080`

---

## 九、代码规范检查清单

基于 `code-standards.md` 的硬性要求：

- [ ] Vue SFC ≤ 300 行（硬限）
- [ ] TS/JS 文件 ≤ 400 行（硬限）
- [ ] Python 模块 ≤ 400 行（硬限）
- [ ] 单函数 ≤ 40 行
- [ ] 无 `any` 类型
- [ ] 无硬编码 URL/端口（全部走 `.env` / `config.yaml`）
- [ ] 无中部 import
- [ ] 统一错误格式
- [ ] 路由层不含业务逻辑（委托 service）
- [ ] 前端不直接访问外部 AI 服务（全部经后端代理）

---

## 十、待 UI 设计阶段确认的事项

以下将在 Phase 6 开始前提供多方案选择：

1. **整体色调与视觉语言** — 暗色/亮色/双主题
2. **三栏布局比例** — 左栏宽度、右栏是否可折叠
3. **分镜卡片样式** — 瀑布流/网格/列表
4. **模态框 vs 侧边抽屉** — 图片修正的交互形式
5. **移动端适配** — 是否需要响应式支持

---

## 十一、从旧项目迁移的核心数据

### Prompt 模板（需迁移到后端 service）

- `PROMPTS.ROLE_EXTRACT` — 角色提取
- `PROMPTS.REWRITE` — 故事改写
- `PROMPTS.SPLIT_SENTENCES` — 镜头拆分
- `PROMPTS.IMAGE_GEN_FUNC` — GACE Antigravity 导演 Prompt
- `ANTIGRAVITY_RULES` — 物理法则/角色锁/运镜法则
- 5 种快捷修正 system prompt (character/environment/era/composition/style)

### ComfyUI 工作流（需迁移到 `data/workflows/`）

- T2I: nunchaku_qwen, z_image_turbo, z_image_turbo_a, z_image_gguf
- I2V: Wan2.1 (i2v_workflow_wan)
- Edit: Qwen Edit (qwen_edit_workflow)

### 风格/时代预设（需迁移到前端 constants）

- 13 种风格预设
- 24 种时代背景预设
- 8 种图片尺寸
- 4 种视频分辨率

---

## 十二、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| ComfyUI WebSocket 在后端代理时可能有超时问题 | 后端异步长连接 + 前端轮询状态 |
| 大文件传输（视频 Blob）| 后端直接写入磁盘，返回 URL |
| LLM SSE 中断 | 后端重试 + 前端断线重连 |
| RunningHub API 不稳定 | 后端轮询 + 超时 fallback 到本地 ComfyUI |
