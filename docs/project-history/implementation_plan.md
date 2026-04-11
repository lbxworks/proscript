# PRD v2：多智能体工作流进度可视化增强

## 1. 背景与目标

### 1.1 问题描述
当前系统在"脚本生成"和"Villy 热点搜索"两个核心场景中，后端需执行多步 AI Agent 串行处理，耗时通常在 30~120 秒。在此期间，前端界面完全静止（仅显示"生成中..."或"刷新中..."），导致：
- 用户无法判断系统是否正常运行，产生焦虑甚至误以为"卡死"
- 小白用户完全不了解产品背后的 AI 工作原理，无法感知产品价值
- 异常发生时（网络超时、模型限流）用户只能看到一行冷冰冰的错误文字，无法自助恢复

### 1.2 目标
通过"流程节点进度条"实时展示后台多 Agent 的运行状态，让用户在等待过程中始终拥有掌控感与信任感。

### 1.3 成功指标

| 指标 | 基线（当前） | 目标 |
|:---|:---|:---|
| 生成过程中用户主动离开/关闭页面的比率 | 需埋点采集 | 降低 30%+ |
| 异常场景下用户成功自助恢复比率（点击重试/跳过） | 0%（当前无按钮） | ≥ 60% |
| 用户对等待过程的"可接受度"主观评分 | 无数据 | ≥ 3.5/5 |

---

## 2. 覆盖范围：三个场景

本次需求覆盖系统中**所有存在长耗时等待**的功能入口：

| 场景 | 入口 | 后端接口 | 当前体验 |
|:---|:---|:---|:---|
| **A. 脚本生成** | 脚本生成控制台 → "运行" 按钮 | `POST /scripts/generate` | 按钮变为"生成中..."，界面冻结 |
| **B. 热点探索** | 热点探索 → "刷新行业情报" 按钮 | `GET /trends` | 按钮变为"刷新中..."，界面冻结 |
| **C. 脚本合规审核** | 脚本审核控制台 → "审核" 按钮 | `POST /scripts/review` | 按钮变为"审核中..."，界面冻结 |

---

## 3. 节点映射设计

### 3.1 场景 A：脚本生成（8 步 → 5 节点）

> [!NOTE]
> 后端 `core/workflow.py` 实际执行 8 个 LangGraph 节点：
> `Profiler` → `TrendHunter` → `ScriptWriter` → `ComplianceScopeResolver` → `ComplianceRetriever` → `ComplianceRuleEngine` → `ComplianceReviewer` → `ComplianceRewriter`。
> 将 4 个合规 Agent 合并为一个用户可理解的"合规审查"步骤，降低认知负担。

| 后端节点 | 前端节点 (深色加粗) | 虚拟动态文案 (浅灰滚动) | 事件标识 |
|:---|:---|:---|:---|
| `Profiler` | **步骤 1：深度分析受众画像** | "正在扫描社交网络用户习惯..."、"构建目标受众人格模型..." | `profiler` |
| `TrendHunter` | **步骤 2：Villy 全网热点追踪** | "连接头条与推特数据源..."、"深度挖掘今日爆款话题..." | `trend_hunter` |
| `ScriptWriter` | **步骤 3：AI 大脑初稿创作** | "头脑风暴剧本结构..."、"匹配网感金句与悬念..."、"生成镜头脚本..." | `script_writer` |
| 4 个 Compliance Agent | **步骤 4：全球平台合规审查** | "检索 TikTok/小红书投放政策..."、"执行广告法敏感词扫描..."、"确保文案合规不封号..." | `compliance` |
| `ComplianceRewriter` | **步骤 5：内容优化与最终定稿** | "打磨文案张力..."、"生成最终交付格式..." | `rewriter` |

### 3.2 场景 B：热点探索（独立节点设计）

> [!NOTE]
> 后端 `backend/services/trends.py` 的 `explore_trends()` 函数依次执行：
> 1. 搜索对标视频（`search_viral_video_benchmarks`）
> 2. 搜索科技/视频/营销三类行业情报（`_search_industry_category` × 3）
> 3. 主题趋势摘要（`run_trend_hunter`）

| 后端步骤 | 前端节点 (深色加粗) | 虚拟动态文案 (浅灰滚动) | 事件标识 |
|:---|:---|:---|:---|
| `search_viral_video_benchmarks` | **步骤 1：全球热门视频搜索** | "连接 Tavily 数据网络..."、"扫描 TikTok/YouTube 爆款对标视频..." | `video_search` |
| 3× `_search_industry_category` | **步骤 2：三大行业情报扫描** | "获取科技行业最新动态..."、"追踪视频行业变化..."、"分析营销行业趋势..." | `industry_scan` |
| `run_trend_hunter` (TrendHunter Agent) | **步骤 3：Villy 深度趋势解读** | "AI 正在阅读并提炼所有情报..."、"生成可执行的趋势洞察..." | `trend_summary` |

### 3.3 场景 C：脚本合规审核（5 步 → 2 节点）

> [!NOTE]
> 后端 `backend/services/scripts.py` 的 `review_script()` 依次执行 5 个合规 Agent。
> 对用户来说只需感知两个阶段："检查"和"修改"。

| 后端步骤 | 前端节点 (深色加粗) | 虚拟动态文案 (浅灰滚动) | 事件标识 |
|:---|:---|:---|:---|
| ScopeResolver + Retriever + RuleEngine + Reviewer | **步骤 1：全面合规扫描与问题诊断** | "定位适用法律法规..."、"检索合规知识库..."、"逐条对比政策红线..." | `compliance_scan` |
| ComplianceRewriter | **步骤 2：智能合规修订** | "正在修正风险表述..."、"优化敏感词替换..." | `compliance_fix` |

---

## 4. 节点状态机定义

每个进度节点具备以下 **5 种互斥视觉状态**：

| 状态 | 英文标识 | 圆形图标 | 标题文字 | 虚拟文案区 | 连接线 |
|:---|:---|:---|:---|:---|:---|
| **未开始** | `pending` | 灰色空心圆 `#D1D5DB` | 浅灰色 `#9CA3AF` | 不显示 | 灰色虚线 |
| **进行中** | `active` | 主题色实心圆 + 呼吸灯脉动动效 | 深色加粗 `#111827` | 浅灰打字机滚动 `#9CA3AF` | 主题色实线（已完成部分） |
| **已完成** | `completed` | 主题色实心圆 + 白色 ✓ 勾号 | 深色 `#111827` | 隐藏（或显示最终耗时） | 主题色实线 |
| **失败** | `error` | 红色实心圆 `#EF4444` + 白色 ✕ | 红色 `#EF4444` | 替换为错误卡片 + 操作按钮 | 红色实线（到此为止） |
| **已跳过** | `skipped` | 灰色虚线圆 | 灰色删除线文字 `#9CA3AF` | "已跳过" | 灰色虚线 |

### 呼吸灯动效规格
```css
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(主题色, 0.4); }
  50%       { box-shadow: 0 0 0 10px rgba(主题色, 0); }
}
/* 周期：2s，infinite */
```

### 虚拟文案打字机规格
- 每条虚拟文案以打字机效果逐字显示（30ms/字）
- 显示完毕后停留 1.5s，淡出切换到下一条
- 循环播放直到该节点完成

---

## 5. UI 布局方案

### 5.1 进度面板出现位置
- 点击"生成/刷新/审核"按钮后，**结果面板区域**替换为全幅进度可视化面板
- 左侧控制面板降低透明度（`opacity: 0.5`）并禁用所有输入，防止重复提交
- 生成完成后，进度面板播放收缩动画（300ms），过渡到结果展示面板

### 5.2 Stepper 方向
- **桌面端（≥768px）**：水平 Stepper（横向从左到右）
- **移动端（<768px）**：垂直 Stepper（纵向从上到下）

### 5.3 虚实文案视觉分级（用户明确要求）
- **真实进度标题**：粗体、深色 `#111827`（或暗色模式下 `#F9FAFB`），字号 16px
- **虚拟渲染文案**：常规字重、浅灰 `#9CA3AF`，字号 13px，带打字机动效

### 5.4 始终可见元素
进度面板中始终显示以下两个控件：
1. **整体进度百分比**：如"3/5 步骤"或环形进度条
2. **`[取消生成]` 按钮**：位于进度面板右上角，浅灰文字按钮

---

## 6. 异常处理方案

> [!WARNING]
> 严禁向用户展示原始技术错误信息（如 `Exception: RateLimitExceeded`、`ConnectionTimeout`）。
> 所有异常必须经过产品话术翻译后展示。

### 6.1 节点级异常（特定步骤失败）

#### 异常 A：热点搜索失败
- **触发节点**：TrendHunter / video_search / industry_scan
- **后台原因**：Tavily API 超时、新闻源为空、搜索配额耗尽
- **用户看到**：该节点变为 `error` 状态，弹出错误卡片
- **话术**："😕 网络数据源暂时开小差了，Villy 本次没有捕获到热点。"
- **操作按钮**：`[重试本步骤]`  `[跳过热点，继续创作]`

#### 异常 B：合规拦截
- **触发节点**：compliance / compliance_scan
- **后台原因**：脚本严重违反多平台政策，多次重写仍不通过
- **用户看到**：该节点变为 `error` 状态
- **话术**："🛡️ 为了保护您的账号安全，系统拦截了本次内容。创作需求触碰了平台合规红线。"
- **操作按钮**：`[查看违规详情并修改需求]`

#### 异常 C：大模型服务拥堵
- **触发节点**：任意调用 LLM 的节点（ScriptWriter、ComplianceReviewer 等）
- **后台原因**：API 限流（Rate Limit）、服务端拥塞、连接断开
- **用户看到**：该节点变为 `error` 状态
- **话术**："🔥 当前 AI 服务繁忙，Villy 暂时排不上队了～"
- **操作按钮**：`[重新排队]`

### 6.2 全局超时兜底

> [!IMPORTANT]
> 如果任意节点超过 **120 秒**无状态更新（SSE 心跳中断或无新事件），前端自动触发兜底逻辑。

- **话术**："⏰ Villy 思考了太久，可能遇到了意外情况。"
- **操作按钮**：`[重新开始]`  `[联系技术支持]`
- **技术机制**：前端维护一个 120s 倒计时定时器，每次收到 SSE 事件时重置

### 6.3 用户主动取消

用户可随时点击 `[取消生成]`，触发以下行为：
1. 前端立即关闭 SSE 连接
2. 进度面板显示"已取消"，所有未完成节点变为 `pending`
3. 恢复左侧控制面板的可交互状态
4. 后端收到连接中断后停止后续 Agent 执行（最佳努力，不强制）

---

## 7. 技术方案：后端改造说明

> [!IMPORTANT]
> 这是本次需求**最大的技术改动点**。当前后端所有长耗时接口均为同步请求/响应模式，需改造为流式事件推送。

### 7.1 通信机制选型：SSE（Server-Sent Events）

**选择理由**：
- 后端是标准 FastAPI，原生支持 `StreamingResponse`
- 进度推送是单向的（服务端 → 客户端），不需要 WebSocket 的双向能力
- 前端通过标准 `EventSource` API 即可消费，实现成本最低
- 自动重连机制内置

### 7.2 SSE 事件格式定义

```
event: progress
data: {"step": "profiler", "status": "active", "message": "正在分析受众画像"}

event: progress
data: {"step": "profiler", "status": "completed", "message": "受众画像分析完成", "duration_ms": 3200}

event: progress
data: {"step": "trend_hunter", "status": "active", "message": "正在搜索全网热点"}

event: error
data: {"step": "trend_hunter", "status": "error", "error_type": "search_timeout", "message": "搜索引擎响应超时"}

event: heartbeat
data: {"timestamp": "2026-04-11T21:00:00Z"}

event: complete
data: {"result": { ... 完整的最终结果 JSON ... }}
```

- `heartbeat` 事件每 **15 秒**发送一次，用于前端超时检测
- `complete` 事件携带完整结果，与当前同步接口的返回格式一致

### 7.3 后端改造要点

#### 场景 A：脚本生成
- 将 `generate_script()` 中的 `build_workflow().invoke(initial_state)` 改为 LangGraph 的 **`astream_events()`** 或在每个 Agent 函数入口/出口手动 yield 事件
- 新增 SSE 端点：`GET /scripts/generate/stream`（参数通过 query string 传递）
- 保留原有 `POST /scripts/generate` 同步接口不变，确保向后兼容

#### 场景 B：热点探索
- 在 `explore_trends()` 的 `_module_response` / `_search_industry_category` 各步骤前后插入进度事件 yield
- 新增 SSE 端点：`GET /trends/stream`

#### 场景 C：脚本审核
- 在 `review_script()` 的 5 个 Agent `for` 循环中，每步前后 yield 事件
- 新增 SSE 端点：`GET /scripts/review/stream`

### 7.4 并发控制
- 同一用户同时只允许运行 **1 个**生成/审核任务
- 前端：点击按钮后立即禁用，连接关闭后恢复
- 后端：可选——内存级 user_id 锁，重复请求返回 `409 Conflict`

---

## 8. 改动文件清单

| 层 | 文件 | 改动类型 | 改动摘要 |
|:---|:---|:---|:---|
| 后端 | `backend/main.py` | MODIFY | 新增 3 个 SSE 端点 |
| 后端 | `backend/services/scripts.py` | MODIFY | `generate_script` / `review_script` 增加 generator 版本 |
| 后端 | `backend/services/trends.py` | MODIFY | `explore_trends` 增加 generator 版本 |
| 后端 | `core/workflow.py` | MODIFY | 支持流式执行（`astream_events` 或回调注入） |
| 前端 | `components/shared/workflow-stepper.tsx` | **NEW** | 通用进度 Stepper 组件 |
| 前端 | `components/scripts/generate-workspace.tsx` | MODIFY | 集成 Stepper，监听 SSE |
| 前端 | `components/scripts/review-workspace.tsx` | MODIFY | 集成 Stepper，监听 SSE |
| 前端 | `components/trends/trends-workspace.tsx` | MODIFY | 集成 Stepper，监听 SSE |
| 前端 | `lib/api.ts` | MODIFY | 新增 SSE 连接工具函数 |
| 前端 | `app/globals.css` | MODIFY | 新增 Stepper、呼吸灯、打字机动效样式 |

---

## 9. 优先级与排期建议

| 阶段 | 内容 | 预估工作量 | 优先级 |
|:---|:---|:---|:---|
| **P0 - MVP** | 脚本生成（场景 A）的 5 步进度条 + SSE 后端 + 3 种异常处理 | 后端 1.5d + 前端 2d | 🔴 必须 |
| **P1 - 补全** | 热点探索（场景 B）的 3 步进度条 + SSE | 后端 0.5d + 前端 1d | 🟡 重要 |
| **P2 - 增强** | 脚本审核（场景 C）进度 + 取消能力 + 全局超时兜底 | 后端 0.5d + 前端 1d | 🟢 锦上添花 |
| **P3 - 打磨** | 虚拟文案打字机动效 + 每步耗时显示 + 埋点采集成功指标 | 前端 1d | ⚪ 可延后 |

---

## 10. 验收标准（Acceptance Criteria）

### 功能验收
- [ ] 点击"生成"后，≤500ms 内结果面板替换为 Stepper 进度面板
- [ ] 第一个节点立即进入 `active` 状态并显示呼吸灯动效
- [ ] 后端每完成一个 Agent 节点，前端 ≤1s 内切换到下一节点
- [ ] 真实进度标题为深色加粗 `#111827`，虚拟文案为浅灰 `#9CA3AF`
- [ ] 虚拟文案以打字机效果逐字显示，循环播放
- [ ] 所有节点完成后，进度面板自然过渡（300ms 动画）到结果展示

### 异常验收
- [ ] 模拟 Tavily 超时 → TrendHunter 节点变 `error`，显示场景 A 话术与按钮
- [ ] 模拟 LLM Rate Limit → 对应节点变 `error`，显示场景 C 话术与按钮
- [ ] 点击"重试本步骤"→ 从失败节点重新开始执行
- [ ] 点击"跳过"→ 该节点变 `skipped`，流程继续下一步
- [ ] 任意节点 120s 无更新 → 触发全局超时兜底提示
- [ ] 点击"取消生成"→ SSE 关闭，面板恢复，控制台可再次操作

### 兼容性验收
- [ ] 原有同步接口 `POST /scripts/generate` 保持不变，不影响已有调用方
- [ ] 桌面端水平 Stepper、移动端垂直 Stepper 布局正确
