# Pro Script AI

面向达人协作、脚本生成、脚本审查、热点探索和资料库管理的内容工作台。

## 当前技术栈

- 前端：Next.js 16 + React 19
- 后端：FastAPI
- 业务数据库：PostgreSQL
- 向量检索：Qdrant

## 数据库约定

- PostgreSQL 是唯一业务库，负责保存 `users`、`scripts`、`talent_profiles`、`trend_snapshots`
- Qdrant 只负责图书馆 / 合规知识库的向量索引，不承载业务主数据
- 业务表结构变更统一通过 Alembic 管理，不再手写 SQL 迁移

## 快速开始

### 1. 准备环境变量

在项目根目录：

```bash
cp -n .env.example .env
```

在前端目录：

```bash
cp -n frontend/.env.local.example frontend/.env.local
```

如果你本来就已经有 `.env` 或 `frontend/.env.local`，不要覆盖它们，只补缺少的字段。

### 2. 确认 PostgreSQL 可用

默认业务库地址：

```bash
postgresql+psycopg2:///pro_script_ai
```

如果你已经按前面的步骤在本机创建了 `pro_script_ai`，可以直接继续。

### 3. 启动后端

```bash
./scripts/start_backend.sh
```

这个脚本会自动做三件事：

1. 进入项目 `venv`
2. 对 PostgreSQL 执行 Alembic 迁移 / 首次接管
3. 启动 FastAPI 服务

默认地址：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

### 4. 启动前端

新开一个终端窗口：

```bash
./scripts/start_frontend.sh
```

默认地址：

- `http://127.0.0.1:3000`

## 常用命令

### 首次接管现有 PostgreSQL

如果你的 PostgreSQL 里已经有这些业务表，但还没有 `alembic_version`：

```bash
source venv/bin/activate
python scripts/prepare_postgres.py
```

### 日常应用数据库迁移

```bash
source venv/bin/activate
alembic upgrade head
```

### 生成新迁移

```bash
source venv/bin/activate
alembic revision --autogenerate -m "describe your schema change"
```

### 从旧 SQLite 导入历史数据

```bash
source venv/bin/activate
python scripts/migrate_sqlite_to_postgres.py
```

## 目录说明

- `backend/`：FastAPI、SQLAlchemy 数据访问层、接口服务
- `frontend/`：Next.js 控制台前端
- `alembic/`：数据库迁移版本
- `scripts/`：部署、迁移、知识库构建脚本
- `docs/`：按主题分组的项目文档（界面、部署、知识库、测试、项目过程）

## 推荐阅读

- `docs/README.md`
- `docs/operations/postgresql_deployment_guide.md`
- `docs/operations/database_change_workflow.md`
- `docs/operations/backend_api_quickstart.md`
