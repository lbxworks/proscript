# Backend API Quickstart

## 数据库前提

- 当前后端默认使用 PostgreSQL 作为唯一业务库
- 建议先运行 `./scripts/start_backend.sh`
- 如果你手动启动后端，请先执行 `alembic upgrade head`

## 启动方式

在项目根目录运行：

```bash
./scripts/start_backend.sh
```

或手动执行：

```bash
source venv/bin/activate
alembic upgrade head
uvicorn backend.main:app --reload
```

启动后默认地址：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## 已实现的接口

- `GET /talents`
- `POST /talents`
- `PATCH /talents/{talent_id}`
- `DELETE /talents/{talent_id}`
- `POST /scripts/generate`
- `POST /scripts/review`
- `GET /trends`
- `GET /library/health`
- `GET /library/documents`
- `POST /library/upload`
- `POST /library/rebuild`

`GET /trends` 支持两个模块级刷新参数：

- `refresh_videos=true`：仅刷新“合适的视频”模块
- `refresh_industry=true`：仅刷新“行业情报”模块

如果不传刷新参数，接口会优先返回同一组筛选条件下的上一次缓存结果。

## 示例

### 达人管理

```bash
curl "http://127.0.0.1:8000/talents"
```

```bash
curl -X POST http://127.0.0.1:8000/talents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新达人",
    "platform": "TikTok",
    "email": "creator@example.com",
    "recent_video_link": "https://www.tiktok.com/@creator/video/123",
    "notes": "主打数码开箱与测评",
    "collaboration_progress": "初步对接"
  }'
```

说明：

- 新增达人时，系统会自动同步一份 `users` 资料，用于脚本生成模块读取达人风格。
- 达人管理中的“备注描述”会作为脚本生成的人设 / 风格提示词来源。
- 删除达人时，会同步删除对应 `users` 档案，但会保留已有 `scripts` 历史记录。

### 生成脚本

```bash
curl -X POST http://127.0.0.1:8000/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "topic": "为什么年轻人不爱换手机了",
    "target_languages": ["English"],
    "target_platform": "tiktok",
    "target_country": "US"
  }'
```

### 检查脚本

```bash
curl -X POST http://127.0.0.1:8000/scripts/review \
  -H "Content-Type: application/json" \
  -d '{
    "script": "This is the best phone ever. Guaranteed to change your life.",
    "target_platform": "tiktok",
    "target_country": "US",
    "distribution_mode": "branded_content",
    "product_category": "electronics"
  }'
```

### 热点探索

```bash
curl "http://127.0.0.1:8000/trends?target_country=US&target_platform=tiktok"
```

```bash
curl "http://127.0.0.1:8000/trends?topic=AI%20glasses&target_country=US&target_platform=tiktok&distribution_mode=branded_content&product_category=electronics&target_languages=English&refresh_videos=true"
```

### 图书馆健康状态

```bash
curl "http://127.0.0.1:8000/library/health"
```

### 图书馆文档列表

```bash
curl "http://127.0.0.1:8000/library/documents"
```

### 上传图书馆资料

```bash
curl -X POST http://127.0.0.1:8000/library/upload \
  -F "file=@/absolute/path/to/policy.pdf" \
  -F "title=TikTok US Policy" \
  -F "category=platform_policy" \
  -F "market=US" \
  -F "region=AMER" \
  -F "platform=tiktok" \
  -F "language=en" \
  -F "source_url=https://example.com/policy" \
  -F "notes=用于 TikTok 美国市场合规审查" \
  -F "priority=P1"
```

说明：

- `pdf/html` 会写入 `raw/`，并登记到 `source_catalog.json`
- `md/txt` 会直接生成带元数据的 `processed/*.md`
- 上传后通常状态为“待重建”，点重建后才会进入最新索引

### 重建图书馆

```bash
curl -X POST "http://127.0.0.1:8000/library/rebuild"
```
