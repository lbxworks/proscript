"use client";

import { startTransition, useEffect, useMemo, useState } from "react";

import { getTalents, reviewScript } from "@/lib/api";
import {
  DISTRIBUTION_OPTIONS,
  LANGUAGE_OPTIONS,
  MARKET_OPTIONS,
  PLATFORM_OPTIONS,
  PRODUCT_OPTIONS,
} from "@/lib/constants";
import type {
  ComplianceCitation,
  ComplianceIssue,
  ComplianceReport,
  ReviewScriptRequest,
  ReviewScriptResponse,
  TalentProfile,
} from "@/lib/schemas";

const defaultForm: ReviewScriptRequest = {
  script: "This is the best phone ever. Guaranteed to change your life.",
  topic: "smartphone review ad",
  user_id: 1,
  target_languages: ["English"],
  target_platform: "tiktok",
  target_country: "US",
  distribution_mode: "branded_content",
  product_category: "electronics",
  brand_id: "default",
  style_prompt: "",
};

function CitationList({ citations }: { citations: ComplianceCitation[] }) {
  if (!citations.length) {
    return <p className="muted-copy">暂无引用证据。</p>;
  }

  return (
    <div className="stack-list">
      {citations.map((citation, index) => (
        <article key={`${citation.block_id}-${index}`} className="note-card">
          <h4>{citation.source_title}</h4>
          <p className="muted-copy">
            {citation.country_code} · {citation.heading_path || "未提供标题路径"}
          </p>
          <a className="table-link" href={citation.source_url} rel="noreferrer" target="_blank">
            打开原始来源
          </a>
        </article>
      ))}
    </div>
  );
}

function IssueList({ issues }: { issues: ComplianceIssue[] }) {
  if (!issues.length) {
    return <p className="muted-copy">当前没有规则命中。</p>;
  }

  return (
    <div className="stack-list">
      {issues.map((issue, index) => (
        <article key={`${issue.issue_type}-${index}`} className="issue-card">
          <div className="issue-topline">
            <strong>{issue.issue_type}</strong>
            <span className={`risk-tag risk-${issue.risk_level.toLowerCase()}`}>{issue.risk_level}</span>
          </div>
          <p className="issue-excerpt">{issue.excerpt}</p>
          <p>{issue.reason}</p>
          <p className="muted-copy">建议：{issue.suggested_fix}</p>
          {issue.citations.length ? <CitationList citations={issue.citations} /> : null}
        </article>
      ))}
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: Array<Record<string, unknown>> }) {
  if (!evidence.length) {
    return <p className="muted-copy">本次审查没有返回额外证据块。</p>;
  }

  return (
    <div className="stack-list">
      {evidence.map((item, index) => (
        <article key={`${String(item.block_id || item.doc_id || index)}`} className="note-card">
          <h4>{String(item.source_title || item.doc_id || `Evidence ${index + 1}`)}</h4>
          <p className="muted-copy">
            {String(item.country_code || "GLOBAL")} · {String(item.platform || "all")} ·{" "}
            {String(item.distribution_mode || "all")}
          </p>
          <p>{String(item.excerpt || "")}</p>
        </article>
      ))}
    </div>
  );
}

function ReportView({ report }: { report?: ComplianceReport }) {
  if (!report) {
    return <p className="muted-copy">提交脚本后，这里会显示风险判定结果。</p>;
  }

  return (
    <div className="stack-list">
      <article className="note-card">
        <h4>{report.headline}</h4>
        <p>{report.overall_commentary}</p>
      </article>
      <div className="metric-grid">
        <article className="metric-card">
          <span>状态</span>
          <strong>{report.overall_status}</strong>
        </article>
        <article className="metric-card">
          <span>风险</span>
          <strong>{report.overall_risk}</strong>
        </article>
        <article className="metric-card">
          <span>问题数</span>
          <strong>{report.issues.length}</strong>
        </article>
      </div>
      <IssueList issues={report.issues} />
    </div>
  );
}

export function ReviewWorkspace() {
  const [form, setForm] = useState(defaultForm);
  const [pending, setPending] = useState(false);
  const [talentsPending, setTalentsPending] = useState(false);
  const [result, setResult] = useState<ReviewScriptResponse | null>(null);
  const [error, setError] = useState("");
  const [talents, setTalents] = useState<TalentProfile[]>([]);

  const selectedTalent = useMemo(
    () => talents.find((talent) => talent.user_id === form.user_id) || talents[0] || null,
    [form.user_id, talents],
  );

  function toggleLanguage(language: string) {
    const nextLanguages = form.target_languages.includes(language)
      ? form.target_languages.filter((item) => item !== language)
      : [...form.target_languages, language];

    if (nextLanguages.length === 0) {
      return;
    }

    setForm({ ...form, target_languages: nextLanguages });
  }

  function loadTalents() {
    setTalentsPending(true);
    startTransition(async () => {
      try {
        const response = await getTalents();
        setTalents(response.items);
        if (response.items.length > 0) {
          const firstUserId = response.items[0].user_id ?? 0;
          setForm((current) => {
            const currentExists = response.items.some((item) => item.user_id === current.user_id);
            return currentExists ? current : { ...current, user_id: firstUserId };
          });
        }
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "获取达人列表失败");
      } finally {
        setTalentsPending(false);
      }
    });
  }

  useEffect(() => {
    loadTalents();
  }, []);

  function submit() {
    setError("");
    setPending(true);
    startTransition(async () => {
      try {
        const response = await reviewScript(form);
        setResult(response);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "检查失败");
      } finally {
        setPending(false);
      }
    });
  }

  return (
    <div className="dashboard-grid">
      <section className="panel-card panel-card-tight">
        <div className="section-header">
          <div>
            <p className="section-kicker">Review</p>
            <h3>脚本检查台</h3>
          </div>
        </div>

        <label className="field">
          <span>达人选择</span>
          <select
            value={selectedTalent?.user_id ?? form.user_id ?? 0}
            onChange={(event) => setForm({ ...form, user_id: Number(event.target.value) || undefined })}
          >
            {talents.map((talent) => (
              <option key={talent.id} value={talent.user_id ?? 0}>
                {talent.name} · {talent.platform || "未设置"} · {talent.collaboration_progress}
              </option>
            ))}
          </select>
        </label>

        {selectedTalent ? (
          <article className="note-card">
            <h4>达人档案</h4>
            <p>{selectedTalent.notes || "当前达人还没有备注描述。"}</p>
            <p className="muted-copy">
              user_id: {selectedTalent.user_id ?? "-"} · 邮箱: {selectedTalent.email || "未填写"} · 平台:{" "}
              {selectedTalent.platform || "未设置"}
            </p>
          </article>
        ) : (
          <article className="note-card">
            <h4>达人档案</h4>
            <p>{talentsPending ? "正在加载达人列表..." : "当前没有可用于脚本审查的达人，请先到达人管理中新增达人。"}</p>
          </article>
        )}

        <label className="field">
          <span>审查主题</span>
          <input value={form.topic || ""} onChange={(event) => setForm({ ...form, topic: event.target.value })} />
        </label>

        <label className="field">
          <span>脚本内容</span>
          <textarea
            value={form.script}
            onChange={(event) => setForm({ ...form, script: event.target.value })}
            rows={12}
          />
        </label>

        <div className="field">
          <span>目标语言</span>
          <div className="checkbox-grid">
            {LANGUAGE_OPTIONS.map((language) => (
              <label key={language} className="check-card">
                <input
                  checked={form.target_languages.includes(language)}
                  onChange={() => toggleLanguage(language)}
                  type="checkbox"
                />
                <span>{language}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="two-column-fields">
          <label className="field">
            <span>国家</span>
            <select
              value={form.target_country}
              onChange={(event) => setForm({ ...form, target_country: event.target.value })}
            >
              {MARKET_OPTIONS.map((market) => (
                <option key={market.code} value={market.code}>
                  {market.label} ({market.code})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>平台</span>
            <select
              value={form.target_platform}
              onChange={(event) => setForm({ ...form, target_platform: event.target.value })}
            >
              {PLATFORM_OPTIONS.map((platform) => (
                <option key={platform.value} value={platform.value}>
                  {platform.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>分发方式</span>
            <select
              value={form.distribution_mode}
              onChange={(event) => setForm({ ...form, distribution_mode: event.target.value })}
            >
              {DISTRIBUTION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>品类</span>
            <select
              value={form.product_category}
              onChange={(event) => setForm({ ...form, product_category: event.target.value })}
            >
              {PRODUCT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>品牌 ID</span>
            <input
              value={form.brand_id}
              onChange={(event) => setForm({ ...form, brand_id: event.target.value })}
            />
          </label>
        </div>

        <button className="primary-button" disabled={pending || !form.script.trim()} onClick={submit} type="button">
          {pending ? "检查中..." : "运行 /scripts/review"}
        </button>
        {error ? <p className="error-copy">{error}</p> : null}
      </section>

      <section className="panel-card">
        <div className="section-header">
          <div>
            <p className="section-kicker">Report</p>
            <h3>风险报告</h3>
          </div>
        </div>
        <ReportView report={result?.final_state.compliance_report} />
      </section>

      <section className="panel-card full-span">
        <div className="section-header">
          <div>
            <p className="section-kicker">Rewrite</p>
            <h3>建议修订稿</h3>
          </div>
        </div>
        <article className="code-panel">
          <pre>{String(result?.final_state.approved_script || "")}</pre>
        </article>
      </section>

      <section className="panel-card full-span">
        <div className="section-header">
          <div>
            <p className="section-kicker">Evidence</p>
            <h3>命中证据</h3>
          </div>
        </div>
        <EvidenceList evidence={result?.final_state.retrieved_evidence || []} />
      </section>

      <section className="panel-card full-span">
        <div className="section-header">
          <div>
            <p className="section-kicker">Rule Hits</p>
            <h3>规则命中</h3>
          </div>
        </div>
        <IssueList issues={result?.final_state.rule_issues || []} />
      </section>
    </div>
  );
}
