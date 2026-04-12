# 数据库变更操作手册

这份文档专门写给第一次开始维护 PostgreSQL + Alembic 的同学。

先提醒一句：

- `.env.example` 是模板
- `.env` 是你的真实本地配置
- 不要用 `cp .env.example .env` 去覆盖一个已经存在的 `.env`

如果你以后要：

- 给表新增字段
- 删除字段
- 修改字段类型
- 新增一张业务表

都优先按这份文档来做，不要直接在 Navicat 里手改线上结构，也不要手写一堆 SQL 到处跑。

## 先记住 3 句话

### 1. PostgreSQL 是唯一业务库

业务数据都在 PostgreSQL：

- `users`
- `scripts`
- `talent_profiles`
- `trend_snapshots`

### 2. 表结构变更统一走 Alembic

以后改表结构，不再直接改数据库。

正确顺序是：

1. 先改 [backend/models.py](/Users/bailumac/Developer/my-grad-proj/backend/models.py)
2. 再生成 Alembic migration
3. 再执行 `alembic upgrade head`

### 3. Qdrant 不走这套流程

Qdrant 只是知识库向量检索层，不是业务关系库。

所以这份文档只管 PostgreSQL，不管 Qdrant。

## 你每次改数据库前，先做这 4 个检查

在项目根目录执行：

```bash
cd /Users/bailumac/Developer/my-grad-proj
source venv/bin/activate
```

然后检查：

```bash
alembic current
```

如果能看到类似：

```bash
20260411_0001 (head)
```

说明当前数据库已经被 Alembic 接管，可以继续。

再确认后端能启动：

```bash
./scripts/start_backend.sh
```

如果后端能正常起来，再按下面流程改库。

## 标准流程：以后每次改数据库，都按这 7 步走

## 第 1 步：先想清楚你到底要改什么

先把需求写成一句话。

例如：

- 给 `talent_profiles` 新增 `phone` 字段
- 给 `scripts` 新增 `review_status` 字段
- 新增一张 `brands` 表

不要一上来就改数据库。

## 第 2 步：先改 SQLAlchemy Model

业务表结构定义在：

[backend/models.py](/Users/bailumac/Developer/my-grad-proj/backend/models.py)

比如，你要给 `TalentProfile` 增加手机号字段，就先在对应类里加一列。

示意写法：

```python
phone: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
```

注意：

- 老表里已经有数据时，新增字段最好先给默认值
- 如果你还不确定默认值，就先允许 `nullable=True`
- 不要随便把老表字段直接改成 `nullable=False`，很容易因为旧数据为空而失败

## 第 3 步：生成迁移文件

在项目根目录执行：

```bash
cd /Users/bailumac/Developer/my-grad-proj
source venv/bin/activate
alembic revision --autogenerate -m "add phone to talent_profiles"
```

执行后，Alembic 会在下面生成一个新文件：

[alembic/versions](/Users/bailumac/Developer/my-grad-proj/alembic/versions)

文件名一般会长这样：

```bash
20260411_xxxx_add_phone_to_talent_profiles.py
```

## 第 4 步：打开迁移文件，检查是不是你想要的

这是非常重要的一步，不要跳过。

重点检查 4 件事：

- `upgrade()` 里是不是你要的变更
- `downgrade()` 里是不是能回滚
- 有没有误删别的表或字段
- 默认值、类型、是否可空，和你想的一不一样

如果只是简单新增字段，通常会看到类似：

```python
op.add_column(
    "talent_profiles",
    sa.Column("phone", sa.Text(), nullable=False, server_default=sa.text("''")),
)
```

如果 Alembic 自动生成得不对，可以手动改这个 migration 文件。

这很正常，不用怕。

## 第 5 步：执行迁移

确认 migration 文件没问题后，执行：

```bash
cd /Users/bailumac/Developer/my-grad-proj
source venv/bin/activate
alembic upgrade head
```

这一步会把 PostgreSQL 更新到最新表结构。

## 第 6 步：验证数据库真的改成功了

先看 Alembic 版本：

```bash
alembic current
```

再启动后端：

```bash
./scripts/start_backend.sh
```

再测试相关接口。

比如你改的是达人表，就应该至少确认：

- `GET /talents` 正常
- 新增 / 编辑达人不报错
- 前端页面能正常显示

## 第 7 步：同步改代码逻辑和前端

改完表结构，通常还不够。

你通常还需要同步改这些地方：

- [backend/db.py](/Users/bailumac/Developer/my-grad-proj/backend/db.py)
- [backend/schemas.py](/Users/bailumac/Developer/my-grad-proj/backend/schemas.py)
- 对应的 `backend/services/*`
- 前端请求结构和页面表单

也就是说：

- `models.py` 决定表结构
- `alembic/versions/*.py` 负责迁移数据库
- `backend/db.py` 决定数据怎么读写
- `schemas.py` 决定接口收什么字段
- 前端决定用户能不能看到和编辑这些字段

## 最常用的 3 种场景

## 场景 1：新增字段

这是最常见的情况。

推荐顺序：

1. 在 [backend/models.py](/Users/bailumac/Developer/my-grad-proj/backend/models.py) 加字段
2. 给老数据考虑默认值，或者先允许为空
3. 执行 `alembic revision --autogenerate -m "..."` 
4. 检查 migration
5. 执行 `alembic upgrade head`
6. 改接口和前端

## 场景 2：删除字段

删除字段风险更高，因为旧数据会真的丢失。

建议做法：

1. 先确认前后端已经完全不用这个字段
2. 先在代码里停用这个字段
3. 再做 migration 删除字段
4. 执行前先备份数据

如果你只是“暂时不用”，更稳的做法往往不是立刻删字段，而是先停用它。

## 场景 3：重命名字段

这个场景最容易出坑。

不要完全相信 `--autogenerate`。

因为很多时候 Alembic 会把“重命名字段”识别成：

- 先删旧字段
- 再建新字段

这会导致老数据丢失。

更稳的做法是手动写 migration，例如：

```python
op.alter_column("talent_profiles", "notes", new_column_name="description")
```

如果你要做字段重命名，最好先停一下，让我们单独检查 migration 文件。

## 最安全的复制模板

以后你要改数据库，可以直接照着这一段做：

```bash
cd /Users/bailumac/Developer/my-grad-proj
source venv/bin/activate
alembic current
```

先改：

[backend/models.py](/Users/bailumac/Developer/my-grad-proj/backend/models.py)

然后执行：

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
./scripts/start_backend.sh
```

最后再测试相关页面和接口。

## 如果迁移写错了，怎么退回去

先不要慌。

如果你刚执行完最近一次 migration，可以先尝试：

```bash
cd /Users/bailumac/Developer/my-grad-proj
source venv/bin/activate
alembic downgrade -1
```

意思是：回退一步。

然后你可以：

1. 改好 model
2. 改好 migration 文件
3. 再执行 `alembic upgrade head`

注意：

- 如果这次 migration 已经删了真实数据，`downgrade` 不一定能把数据找回来
- 所以删除字段、重命名字段前一定要更谨慎

## 什么时候不要自己直接动

下面这些情况，不建议直接开干：

- 要重命名字段
- 要拆表 / 合表
- 要把字段从可空改成不可空
- 要给已有大表新增唯一约束
- 要删除老字段，而且里面已经有重要历史数据

这些情况最好先做一次代码检查，再决定 migration 怎么写。

## 你以后最常用的命令清单

### 查看当前版本

```bash
source venv/bin/activate
alembic current
```

### 查看最新头版本

```bash
source venv/bin/activate
alembic heads
```

### 生成迁移

```bash
source venv/bin/activate
alembic revision --autogenerate -m "your change message"
```

### 执行迁移

```bash
source venv/bin/activate
alembic upgrade head
```

### 回退一步

```bash
source venv/bin/activate
alembic downgrade -1
```

### 启动后端并自动补齐 schema

```bash
./scripts/start_backend.sh
```

## 建议你形成的习惯

- 不直接在 PostgreSQL 里手改业务表结构
- 先改 model，再生成 migration
- 每次都检查 migration 文件
- 每次迁移后都启动后端测接口
- 每次大改前先备份数据

## 一句话总结

以后改数据库，请把它理解成一套固定动作：

先改 [backend/models.py](/Users/bailumac/Developer/my-grad-proj/backend/models.py) ，再生成 Alembic migration，再执行 `alembic upgrade head`，最后测试前后端。
