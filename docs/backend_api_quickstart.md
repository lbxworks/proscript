# Backend API Quickstart

## 启动方式

在项目根目录运行：

```bash
uvicorn backend.main:app --reload
```

启动后默认地址：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## 已实现的接口

- `POST /scripts/generate`
- `POST /scripts/review`
- `GET /trends`
- `GET /library/health`

## 示例

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

### 图书馆健康状态

```bash
curl "http://127.0.0.1:8000/library/health"
```
