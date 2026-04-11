# PostgreSQL Deployment Guide

## 目标

本项目已经统一为：

- PostgreSQL：唯一业务库
- Alembic：唯一业务表结构迁移工具
- Qdrant：知识库向量检索层，不存业务主数据

## 当前数据边界

### PostgreSQL 负责

- `users`
- `scripts`
- `talent_profiles`
- `trend_snapshots`

### Qdrant 负责

- 图书馆 / 合规知识库切片索引
- 向量召回
- 检索排序所需的 payload

这意味着：

- 新增字段、删字段、改字段：走 Alembic
- 新增知识库文档、重建索引：走图书馆上传 / rebuild 流程

## 环境变量

根目录 `.env` 至少需要关注这些值：

```env
DATABASE_URL=postgresql+psycopg2:///pro_script_ai
TAVILY_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
```

前端 `frontend/.env.local`：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

如果文件还不存在，可以这样创建模板：

```bash
cp -n .env.example .env
cp -n frontend/.env.local.example frontend/.env.local
```

如果文件已经存在，不要直接覆盖，避免把原有 API Key 清空。

## 本地部署顺序

### 1. 创建并启动 PostgreSQL

确认数据库 `pro_script_ai` 已存在，并且本机能直接连接。

### 2. 启动后端

```bash
./scripts/start_backend.sh
```

这个脚本会自动：

1. 激活 `venv`
2. 检查 PostgreSQL 当前表结构
3. 如果库是空的，执行 `alembic upgrade head`
4. 如果库里已经有完整业务表但还没接入 Alembic，自动 `stamp head`
5. 启动 FastAPI

### 3. 启动前端

```bash
./scripts/start_frontend.sh
```

## Alembic 工作流

### 应用现有迁移

```bash
source venv/bin/activate
alembic upgrade head
```

### 生成迁移

修改 SQLAlchemy model 后执行：

```bash
source venv/bin/activate
alembic revision --autogenerate -m "add xxx column"
```

### 回滚一步

```bash
source venv/bin/activate
alembic downgrade -1
```

## 旧数据迁移

如果你还有原来的 SQLite 数据文件 `data/app.db`，可以导入 PostgreSQL：

```bash
source venv/bin/activate
python scripts/migrate_sqlite_to_postgres.py
```

这个脚本只负责把旧数据搬进 PostgreSQL，不负责后续表结构演进。后续演进统一交给 Alembic。

## 推荐运行方式

以后尽量不要直接裸跑：

```bash
uvicorn backend.main:app --reload
```

更推荐始终使用：

```bash
./scripts/start_backend.sh
```

因为这个入口会先把 PostgreSQL schema 处理到最新，再启动服务。
