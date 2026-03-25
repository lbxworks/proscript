# Scoped Knowledge Base

Put local compliance documents in this folder when you want the `ComplianceRAGAgent` to review scripts with evidence.

Supported file types for the current MVP:

- `.md`
- `.txt`

Each file can optionally start with simple front matter.

Example:

```md
---
doc_id: law_br_beauty_claims_001
source_title: Brazil Beauty Marketing Rules
source_type: law
source_url: https://example.com/br-law
platform:
distribution_mode: branded_content
country_code: BR
region_pack: LATAM
language: pt-BR
brand_id: default
effective_from: 2025-01-01
effective_to:
page_num: 12
heading_path: Capitulo 5 > Artigo 12 > Paragrafo 2
block_id: p12_b04
is_global_fallback: false
---

Avoid absolute or guaranteed outcome claims such as "7 days to remove wrinkles completely".
```

Recommended source types:

- `law`
- `platform_policy`
- `brand_brief`
- `campaign_history`

How scoping works:

- `law` documents only match the selected `country_code`
- `platform_policy` and `brand_brief` documents may be global if `country_code` is empty or `GLOBAL`
- `distribution_mode` should usually be `organic`, `branded_content`, or `paid_ads`

If this folder is empty, the compliance reviewer will still run but will return `insufficient_evidence`.
