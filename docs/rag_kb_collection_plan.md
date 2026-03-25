# RAG 知识库采集总方案

## 1. 这份文档的目的

这份文档用于指导当前项目的 `发布合规 Agent` 建设阶段，告诉我们：

1. 需要收集哪些知识库内容。
2. 为什么要收集这些内容。
3. 这些内容分别来自哪里。
4. 哪些可以自动爬取，哪些必须人工补齐。
5. 这些内容进入 `RAGFlow` 之前应该如何组织。

本方案与已有技术路线文档 [compliance_rag_agent_guide.md](/Users/bailumac/Developer/my-grad-proj/docs/compliance_rag_agent_guide.md) 保持一致。

---

## 2. 目标与边界

这个知识库不是为了做泛知识问答，而是为了让营销文案在交付 KOL 之前完成：

- 当地广告合规检查
- 平台规则检查
- 品牌调性检查
- 可验证引文输出
- 修改建议生成

因此，知识库内容必须围绕下面 4 类核心来源建设：

1. `当地广告法与消费者保护规则`
2. `平台社区规范、广告政策、branded content 规则`
3. `品牌内部历史 Campaign Brief 与品牌语气规范`
4. `技术参考文档（RAGFlow、自身 ingestion 规范、引文结构）`

---

## 3. 市场范围

### 3.1 美洲

需要覆盖：

- 英语区：美国、加拿大
- 西语区：墨西哥、阿根廷、智利、哥伦比亚、秘鲁，后续可继续扩展乌拉圭等
- 葡语区：巴西
- 法语区：加拿大法语资料优先，后续视业务扩展法语加勒比

### 3.2 欧洲

需要覆盖：

- 英语区：英国、爱尔兰
- 法语区：法国
- 德语区：德国
- 意语区：意大利
- 西语区：西班牙
- 葡语区：葡萄牙
- 北欧：瑞典、芬兰、丹麦、挪威、冰岛

### 3.3 中东

建议第一批覆盖：

- 阿联酋
- 沙特阿拉伯

后续人工补齐：

- 卡塔尔
- 科威特
- 巴林
- 阿曼
- 埃及
- 约旦
- 黎巴嫩

---

## 4. 平台范围

本项目需要覆盖：

- TikTok
- Instagram
- YouTube
- X
- Reddit
- Discord

每个平台至少要采集 3 类文档：

1. `Community / Safety / Content Policy`
2. `Ads / Branded Content / Sponsored Content Policy`
3. `Platform-specific disclosure or monetization guidance`

---

## 5. 必收信息清单

下面这些信息都应该进入知识库，缺一不可。

### 5.1 当地法律与监管信息

每个国家或地区至少要收集：

- 广告法、消费者保护法、反不正当竞争相关条文
- 社交媒体 / influencer disclosure 要求
- 误导性宣传、虚假宣传、隐性广告规则
- 抽奖、赠品、促销与 giveaway 规则
- 价格声明、折扣、限时优惠的合规要求
- 儿童、未成年人、健康、药品、保健品、化妆品等敏感品类规则
- 电子营销、垃圾短信、telemarketing、opt-in/opt-out 规则

### 5.2 平台政策信息

每个平台至少要收集：

- 社区规范
- 商业内容 / branded content 规则
- 广告政策
- 广告落地页质量要求
- 受限行业与禁投类目
- AI 内容、合成媒体、伪造内容标签要求
- spam / deceptive behavior / fake engagement 规则

### 5.3 品牌内部资料

这些资料往往不能公开爬取，只能人工整理：

- 历史 Campaign Brief
- 品牌语气手册
- Approved copy examples
- Rejected copy examples
- 法务已批准 claim 列表
- 高风险禁用说法
- 产品资料、功效证据、实验或认证摘要
- KOL 合作披露模板

### 5.4 其他强烈建议收集的资料

这些不是用户明确要求的，但对最终效果很重要：

- 监管机构执法案例
- 平台透明度报告
- 品类专项规则，如 supplements、cosmetics、financial products、alcohol、gambling
- 各市场的语言术语表
- 国家 / 区域 / 平台 / 品类四维 taxonomy

---

## 6. 采集优先级

### P0 必须先收集

- 平台官方政策
- 美国 FTC、加拿大、巴西、法国、德国、英国、阿联酋、沙特的核心合规来源
- 内部品牌 brief
- 内部 tone of voice
- 内部已批准 / 已驳回案例

### P1 第二阶段收集

- 墨西哥、阿根廷、西班牙、意大利、北欧市场
- 监管机构的执法案例和 FAQ
- 品类专项规则

### P2 可选增强

- 平台透明度报告
- 行业自律组织规范
- 研究报告或风险监测报告

---

## 7. RAGFlow 入库前的数据组织规范

为了适配 `RAGFlow` 的检索、分块和可验证引文功能，所有文档都要带 metadata。

建议至少保留：

```json
{
  "doc_id": "law_fr_influencer_guide_001",
  "source_title": "Guide de bonne conduite des influenceurs",
  "source_type": "market_law",
  "platform": "instagram",
  "distribution_mode": "branded_content",
  "country_code": "FR",
  "region_pack": "EU",
  "language": "fr",
  "effective_from": "2023-06-09",
  "effective_to": null,
  "is_global_fallback": false,
  "source_url": "https://...",
  "page_num": 4,
  "heading_path": "Chapitre 2 > Publicite > Influenceurs",
  "block_id": "p4_b2",
  "source_hash": "sha256:..."
}
```

---

## 8. 目录建议

建议把采集结果放到下面这些目录：

```text
data/
  knowledge_base/
    source_catalog.json
    crawl_status.json
    raw/
docs/
  rag_kb_collection_plan.md
  rag_kb_collection_status.md
scripts/
  crawl_rag_sources.py
```

---

## 9. 自动采集与人工补录的分工

### 9.1 自动采集

适合自动采集的内容：

- 官方 HTML 页面
- 官方 PDF 指南
- 官方政策中心 / FAQ 页面
- 官方透明度报告

### 9.2 人工补录

必须人工补录的内容：

- 品牌内部 Brief
- 客户法务口径
- Notion / Drive / Slack / 邮件里的历史 campaign 文件
- 登录后才能访问的平台管理后台规则
- 无公开固定入口的本地监管文件

### 9.3 自动采集失败时的处理原则

如果站点：

- 有反爬
- 强依赖 JavaScript
- 需要登录
- 返回 403 / 401 / 429

则不强行突破，而是在状态文档中标为：

- `blocked`
- `failed`
- `manual_required`

---

## 10. 当前已建立的采集机制

本仓库现已包含：

- 来源清单：[source_catalog.json](/Users/bailumac/Developer/my-grad-proj/data/knowledge_base/source_catalog.json)
- 爬虫脚本：[crawl_rag_sources.py](/Users/bailumac/Developer/my-grad-proj/scripts/crawl_rag_sources.py)
- 采集状态文档：[rag_kb_collection_status.md](/Users/bailumac/Developer/my-grad-proj/docs/rag_kb_collection_status.md)

---

## 11. 当前清单之外，仍建议后续扩展的市场

虽然第一批已经覆盖了大量核心市场，但以下市场建议作为后续人工研究队列持续补入：

- 智利
- 哥伦比亚
- 秘鲁
- 爱尔兰
- 葡萄牙
- 挪威
- 冰岛
- 比利时
- 瑞士
- 奥地利
- 卡塔尔
- 科威特
- 巴林
- 阿曼
- 埃及
- 约旦
- 黎巴嫩

---

## 12. 最终结论

你的知识库建设不能只收“平台规则”，也不能只收“广告法”。

真正可用的合规知识库一定要同时包含：

- 市场法律
- 平台政策
- 品牌内部资料
- 品类专项限制
- 可验证引文元数据

这也是为什么采集任务必须分成：

`自动抓取公开官方来源 + 人工补录内部品牌资料 + 持续扩充本地监管文档`

后续只要继续维护 `source_catalog.json`，就可以用同一套脚本持续追加新的官方来源。
