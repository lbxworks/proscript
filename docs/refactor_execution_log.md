# 重构执行记录

## 目标

本轮执行聚焦两件事：

1. 把原 [app.py](/Users/bailumac/Developer/my-grad-proj/app.py) 中的关键能力拆成后端服务接口，并先跑通：
   - `POST /scripts/generate`
   - `POST /scripts/review`
   - `GET /trends`
   - `GET /library/health`
2. 搭建前端框架和 5 个一级菜单空页面，并优先接通：
   - 脚本生成
   - 脚本检查
   - 热点探索
   - 图书馆

## 现状核对

### 已完成

- 已新增 FastAPI 后端入口 [backend/main.py](/Users/bailumac/Developer/my-grad-proj/backend/main.py)。
- 已新增脚本服务 [backend/services/scripts.py](/Users/bailumac/Developer/my-grad-proj/backend/services/scripts.py)。
- 已新增趋势服务 [backend/services/trends.py](/Users/bailumac/Developer/my-grad-proj/backend/services/trends.py)。
- 已新增图书馆健康检查服务 [backend/services/library.py](/Users/bailumac/Developer/my-grad-proj/backend/services/library.py)。
- 已新增达人服务 [backend/services/talents.py](/Users/bailumac/Developer/my-grad-proj/backend/services/talents.py)。
- 已新增数据库辅助层 [backend/db.py](/Users/bailumac/Developer/my-grad-proj/backend/db.py)。
- 已补充后端启动说明 [docs/backend_api_quickstart.md](/Users/bailumac/Developer/my-grad-proj/docs/backend_api_quickstart.md)。
- 已验证 5 个后端接口可用。
- 已新增 `frontend/` 前端工程，并采用 Next.js App Router 结构。
- 已完成 5 个一级菜单页面骨架与统一布局。
- 已接通达人管理、脚本生成、脚本检查、热点探索、图书馆 5 个页面与后端 API。
- 已使用 Node 22 + pnpm 完成前端依赖安装与生产构建验证。
- 已补齐 `talent_profiles` 数据表，并从原 `users` 表自动同步基础达人资料。
- 已补齐达人管理的新增、编辑、删除能力。
- 已打通达人管理与脚本生成：达人资料会同步到 `users`，可直接在脚本生成页选择达人。
- 已调整达人删除规则：删除达人时会同时删除对应 `users` 档案，但保留历史 `scripts`，并将其 `user_id` 置空。
- 已补齐脚本生成页的完整参数项：达人、语言、国家、平台、分发方式、品类、品牌 ID、时长、温度、保存开关。
- 已为脚本生成增加一次宽松校验重试，降低 `script_writer` 因格式校验直接失败的概率。
- 已增强脚本审查页：支持达人选择、语言多选、国家/平台/分发方式/品类/品牌配置，并展示证据、规则命中、风险报告和建议改写。
- 已增强热点探索页：接入 Tavily 实时抓取“合适的视频”与“科技 / 视频 / 营销行业信息”，并补齐按模块刷新与缓存回显。
- 已补齐图书馆页：支持文档列表、文件上传、图书馆重建，并在页面中展示资料状态。

### 未完成

- 脚本生成与脚本检查当前为同步提交结果，尚未升级为 SSE / WebSocket 流式体验。
- 飞书同步、语音输入检查能力尚未进入本轮实施范围。
- 当前脚本生成链路仍依赖外部 LLM，虽然已增加宽松重试，但仍可能出现模型侧不稳定。
- 图书馆上传目前默认以“新增资料”方式工作；如果上传同名但不同格式文件，系统会自动生成新的 `source_id` 避免覆盖旧资料。
- 热点探索的首次实时抓取仍然较慢，但现在已支持缓存优先回显；只有点击刷新时才会重新向 Tavily 发起请求。

## 执行步骤

### Step 1. 审查后端拆分状态

- 检查了仓库结构，确认 `backend/` 已存在，且 4 个目标接口已落地。
- 继续扩展达人管理链路，确认库内已有 `users` 表可作为达人基础资料来源。
- 检查了本地环境，确认 Python 虚拟环境正常；前端环境原先无可用的稳定 Node 工作流。

### Step 2. 记录执行路径

- 新建本文档，记录已完成项、未完成项、执行步骤与阻塞点。

### Step 3. 搭建前端骨架

- 新建 `frontend/` 目录。
- 采用 Next.js App Router 结构搭建基础文件：
  - [frontend/package.json](/Users/bailumac/Developer/my-grad-proj/frontend/package.json)
  - [frontend/tsconfig.json](/Users/bailumac/Developer/my-grad-proj/frontend/tsconfig.json)
  - [frontend/next.config.ts](/Users/bailumac/Developer/my-grad-proj/frontend/next.config.ts)
  - [frontend/app/layout.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/app/layout.tsx)
  - [frontend/app/globals.css](/Users/bailumac/Developer/my-grad-proj/frontend/app/globals.css)
- 新增统一布局组件：
  - [frontend/components/layout/sidebar.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/layout/sidebar.tsx)
  - [frontend/components/layout/topbar.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/layout/topbar.tsx)

### Step 4. 建立 5 个一级菜单页

- 已新增页面：
  - [frontend/app/(dashboard)/talents/page.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/app/(dashboard)/talents/page.tsx)
  - [frontend/app/(dashboard)/scripts/generate/page.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/app/(dashboard)/scripts/generate/page.tsx)
  - [frontend/app/(dashboard)/scripts/review/page.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/app/(dashboard)/scripts/review/page.tsx)
  - [frontend/app/(dashboard)/trends/page.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/app/(dashboard)/trends/page.tsx)
  - [frontend/app/(dashboard)/library/page.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/app/(dashboard)/library/page.tsx)

### Step 5. 接前端到后端接口

- 已新增前端 API 封装：
  - [frontend/lib/constants.ts](/Users/bailumac/Developer/my-grad-proj/frontend/lib/constants.ts)
  - [frontend/lib/schemas.ts](/Users/bailumac/Developer/my-grad-proj/frontend/lib/schemas.ts)
  - [frontend/lib/api.ts](/Users/bailumac/Developer/my-grad-proj/frontend/lib/api.ts)
- 已新增页面工作区组件：
  - [frontend/components/talents/talent-table.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/talents/talent-table.tsx)
  - [frontend/components/scripts/generate-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/scripts/generate-workspace.tsx)
  - [frontend/components/scripts/review-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/scripts/review-workspace.tsx)
  - [frontend/components/trends/trends-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/trends/trends-workspace.tsx)
  - [frontend/components/library/library-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/library/library-workspace.tsx)

### Step 5.1. 补齐达人管理数据库与接口

- 在 [backend/db.py](/Users/bailumac/Developer/my-grad-proj/backend/db.py) 中新增 `talent_profiles` 表初始化与同步逻辑。
- 在 [data/init_db.py](/Users/bailumac/Developer/my-grad-proj/data/init_db.py) 中补充全新数据库初始化时的达人表建表 SQL。
- 在 [backend/main.py](/Users/bailumac/Developer/my-grad-proj/backend/main.py) 中新增 `GET /talents`。
- 在 [backend/services/talents.py](/Users/bailumac/Developer/my-grad-proj/backend/services/talents.py) 中封装达人列表服务。
- 已验证现有 `users` 会自动同步为达人资料，字段覆盖：
  - 达人ID
  - 平台
  - 邮箱
  - 近期视频链接
  - 达人备注描述
  - 合作进度

### Step 5.2. 将达人管理页替换为真实表格

- 用 [frontend/components/talents/talent-table.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/talents/talent-table.tsx) 替换原占位组件。
- 达人管理页现在展示真实表格与统计卡片，并直接消费 `GET /talents` 返回结果。

### Step 5.3. 补齐达人资料 CRUD

- 在 [backend/main.py](/Users/bailumac/Developer/my-grad-proj/backend/main.py) 中新增：
  - `POST /talents`
  - `PATCH /talents/{talent_id}`
  - `DELETE /talents/{talent_id}`
- 在 [frontend/components/talents/talent-table.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/talents/talent-table.tsx) 中新增达人资料表单与表格操作列。
- 当前达人页已支持：
  - 新增达人
  - 编辑达人
  - 删除达人

### Step 5.4. 打通达人管理与脚本生成

- 在 [backend/db.py](/Users/bailumac/Developer/my-grad-proj/backend/db.py) 中补充达人资料与 `users` 的同步逻辑。
- 新增达人时会自动创建对应的 `users` 记录，编辑达人时会同步更新 `users.name` 与 `users.style_prompt`。
- 达人管理中的“备注描述”会作为脚本生成读取到的人设 / 风格提示词。

### Step 5.5. 完善脚本生成控制台

- 在 [frontend/components/scripts/generate-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/scripts/generate-workspace.tsx) 中补齐完整配置项：
  - 达人选择
  - 输出语言
  - 国家
  - 平台
  - 分发方式
  - 品类
  - 品牌 ID
  - 视频时长
  - 温度 / Creativity
  - 是否保存脚本记录
- 脚本生成页现在直接读取达人列表，不再要求用户手工输入达人 ID。
- 在 [core/agents/writer.py](/Users/bailumac/Developer/my-grad-proj/core/agents/writer.py) 中增加宽松校验重试，优先保证能回收可读脚本内容。

### Step 5.6. 完善达人删除联动规则

- 在 [backend/db.py](/Users/bailumac/Developer/my-grad-proj/backend/db.py) 中调整 `delete_talent_profile`：
  - 删除达人资料时同步删除对应 `users` 档案。
  - 历史 `scripts` 不删除，仅将 `scripts.user_id` 置空，保留历史记录。
- 已通过数据库实测验证以上行为成立。

### Step 5.7. 完善脚本审查页

- 在 [frontend/components/scripts/review-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/scripts/review-workspace.tsx) 中补齐审查页控制台：
  - 达人选择
  - 语言多选
  - 国家
  - 平台
  - 分发方式
  - 品类
  - 品牌 ID
  - 脚本文本输入
- 新增审查结果视图：
  - 合规风险报告
  - 建议改写
  - 检索证据
  - 规则命中列表
- 审查页现在可直接读取达人资料作为上下文输入，和脚本生成页保持一致的配置方式。

### Step 5.8. 完善热点探索页

- 在 [backend/db.py](/Users/bailumac/Developer/my-grad-proj/backend/db.py) 中新增 `trend_snapshots` 缓存表，用于保存热点模块的上一次结果。
- 在 [backend/services/trends.py](/Users/bailumac/Developer/my-grad-proj/backend/services/trends.py) 中将热点探索拆成两个模块：
  - `videos`：使用 Tavily 实时抓取与当前筛选条件匹配的参考视频
  - `industry`：使用 Tavily 实时抓取科技、视频、营销三类行业信息
- 在 [utils/tavily_client.py](/Users/bailumac/Developer/my-grad-proj/utils/tavily_client.py) 中补充：
  - 热点视频查询按主题 / 品类 / 分发方式动态生成查询词
  - `cache_buster` 参数，支持手动刷新时绕过进程内缓存
  - 视频结果兜底策略，避免因缺少明确播放量而整块为空
- 在 [frontend/components/trends/trends-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/trends/trends-workspace.tsx) 中重构热点页：
  - 默认读取缓存结果
  - “刷新热点视频”只刷新视频模块
  - “刷新行业情报”只刷新行业模块
  - 展示最近更新时间、缓存状态、失败回退状态
  - 行业信息按科技 / 视频 / 营销三块卡片展示

### Step 5.9. 完善图书馆页

- 在 [backend/services/library.py](/Users/bailumac/Developer/my-grad-proj/backend/services/library.py) 中补齐图书馆服务：
  - `GET /library/documents`
  - `POST /library/upload`
  - `POST /library/rebuild`
- 上传逻辑支持两类资料：
  - `pdf/html` 写入 `data/knowledge_base/raw/`，并自动登记 `source_catalog.json`
  - `md/txt` 直接生成带元数据的 `processed/*.md`
- 文档列表会根据当前索引构建时间与资料时间，自动判定：
  - `indexed`
  - `pending_rebuild`
- 在 [frontend/components/library/library-workspace.tsx](/Users/bailumac/Developer/my-grad-proj/frontend/components/library/library-workspace.tsx) 中重构图书馆页：
  - 健康状态卡
  - 上传表单
  - 重建按钮
  - 文档列表表格
  - 上传结果与重建结果提示

### Step 6. 处理前端运行时环境并验证构建

- 先尝试使用系统默认 `node 25 / npm 11` 安装依赖，但安装过程未能稳定完成链接。
- 通过 Homebrew 安装了 [node@22]，并改用 Node 22 自带 `corepack` 激活 `pnpm`。
- 在 `frontend/` 下完成 `pnpm install`，生成依赖锁文件并完成依赖解析。
- 执行 `pnpm build`，确认以下页面已成功构建：
  - `/talents`
  - `/scripts/generate`
  - `/scripts/review`
  - `/trends`
  - `/library`
- 调用 `POST /scripts/review`，确认审查接口可返回风险报告、检索证据、规则命中和改写建议。
- 实测删除达人后：
  - `talent_profiles` 记录已删除
  - 对应 `users` 记录已删除
  - 历史 `scripts` 记录保留，且 `user_id` 已置空
- 执行 `GET /trends`：
  - 首次请求成功写入缓存
  - `refresh_videos=true` 可单独刷新视频模块
  - 不带刷新参数再次请求时，会直接返回 `from_cache: true` 的上一次内容
- 图书馆验收：
  - `POST /library/upload` 成功写入测试资料
  - `GET /library/documents` 能返回新增资料，且初始状态为 `pending_rebuild`
  - `POST /library/rebuild` 成功执行后，新增资料状态变为 `indexed`
  - 验收后已清理测试资料并重新重建，恢复当前正式数据状态

## 当前结果

- 后端：
  - 已跑通并验证 5 个目标接口。
- 前端：
  - 已完成目录骨架、统一布局、左侧菜单、顶部导航。
  - 已完成 5 个一级菜单页。
  - 已接通 5 个可用接口对应页面。
  - 已完成生产构建校验。
  - 达人管理已切换为真实表格页。

## 阻塞点

- 当前前端已验证可构建，但运行依赖于 Node 22 + pnpm。
- 系统默认 `node 25 / npm 11` 在这台机器上安装依赖时表现不稳定，因此后续建议统一使用 `pnpm`。

## 下一步建议

1. 为达人管理补充新增、编辑、飞书同步能力。
2. 为达人管理补充飞书同步能力，并考虑拆分“备注描述”与“达人风格提示词”。
3. 将脚本生成和脚本检查升级为 SSE 流式接口。
4. 为图书馆补充文档列表、上传和重建接口。
