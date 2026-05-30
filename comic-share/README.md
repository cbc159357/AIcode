# comic-share

> AI 漫画短片生成器 — 从故事文本到短视频的一站式工具。

## 技术栈

- **前端**: Vue 3 + Vite + TypeScript + TailwindCSS + Arco Design + Pinia
- **后端**: FastAPI + Uvicorn + Pydantic
- **容器化**: Docker Compose

## 快速开始

### 本地开发（推荐）

```bash
# 1. 安装前端依赖
cd frontend && npm install

# 2. 安装后端依赖
cd backend && pip install -r requirements.txt

# 3. 启动（使用生命周期脚本）
python start.py

# 或分别启动
python start.py --backend    # 仅后端 (port 8080)
python start.py --frontend   # 仅前端 (port 5173)
```

### Docker 方式

```bash
docker-compose up --build
```

### 命令说明

```bash
python start.py             # 启动前后端，自动打开浏览器
python start.py --verbose   # 详细日志模式
python start.py --stop      # 停止所有服务
python start.py --status    # 查看服务状态
```

## 目录结构

```
comic-share/
├── start.py              # 启动入口
├── lifecycle.py          # 生命周期管理
├── docker-compose.yml    # Docker 编排
├── frontend/             # Vue 3 前端
│   └── src/
│       ├── views/        # 页面
│       ├── components/   # 组件
│       ├── stores/       # 状态管理
│       ├── services/     # API 调用
│       ├── types/        # 类型定义
│       └── utils/        # 工具函数
└── backend/              # FastAPI 后端
    ├── main.py           # 应用入口
    ├── config.yaml       # 配置文件
    ├── core/             # 核心模块
    ├── routers/          # API 路由
    ├── services/         # 业务逻辑
    └── data/             # 数据存储
        └── workflows/    # ComfyUI 工作流
```

## 端口

| 服务 | 端口 |
|------|------|
| 前端 (Vite) | 5173 |
| 后端 (FastAPI) | 8080 |
