"use client";

import { startTransition, useEffect, useMemo, useRef, useState } from "react";

import { MarkdownContent } from "@/components/ui/markdown-content";
import {
  WorkflowStepper,
  applyWorkflowProgress,
  createWorkflowSteps,
  markActiveWorkflowStepError,
  type WorkflowStepDefinition,
  type WorkflowStepState,
} from "@/components/shared/workflow-stepper";
import { getTalents, streamGenerateScript, WorkflowStreamAbortedError, WorkflowStreamTimeoutError } from "@/lib/api";
import {
  DISTRIBUTION_OPTIONS,
  DURATION_OPTIONS,
  LANGUAGE_OPTIONS,
  MARKET_OPTIONS,
  PLATFORM_OPTIONS,
  PRODUCT_OPTIONS,
} from "@/lib/constants";
import type { ComplianceReport, GenerateScriptRequest, GenerateScriptResponse, TalentProfile } from "@/lib/schemas";

const defaultForm: GenerateScriptRequest = {
  user_id: 1,
  topic: "为什么年轻人不爱换手机了",
  target_languages: ["English"],
  video_duration: "60s (Immersive)",
  target_platform: "tiktok",
  target_country: "US",
  distribution_mode: "branded_content",
  product_category: "electronics",
  brand_id: "default",
  creativity: 0.8,
  persist_result: false,
};

const GENERATE_STEP_DEFINITIONS: WorkflowStepDefinition[] = [
  {
    key: "profiler",
    title: "步骤 1：深度分析受众画像",
    messages: ["正在扫描社交网络用户习惯...", "构建目标受众人格模型..."],
  },
  {
    key: "trend_hunter",
    title: "步骤 2：Villy 全网热点追踪",
    messages: ["连接热点数据源...", "深度挖掘近期爆款话题..."],
  },
  {
    key: "script_writer",
    title: "步骤 3：AI 大脑初稿创作",
    messages: ["头脑风暴剧本结构...", "匹配网感金句与悬念...", "生成镜头脚本..."],
  },
  {
    key: "compliance",
    title: "步骤 4：全球平台合规审查",
    messages: ["检索投放政策与广告法...", "执行敏感词和风险规则扫描..."],
  },
  {
    key: "rewriter",
    title: "步骤 5：内容优化与最终定稿",
    messages: ["打磨文案张力...", "生成最终交付格式..."],
  },
];

function renderReport(report?: ComplianceReport) {
  if (!report) {
    return <p className="muted-copy">还没有合规报告。</p>;
  }

  return (
    <div className="stack-list">
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
      <article className="note-card">
        <h4>{report.headline}</h4>
        <p>{report.overall_commentary}</p>
      </article>
      {report.issues.map((issue, index) => (
        <article key={`${issue.issue_type}-${index}`} className="issue-card">
          <div className="issue-topline">
            <strong>{issue.issue_type}</strong>
            <span className={`risk-tag risk-${issue.risk_level.toLowerCase()}`}>{issue.risk_level}</span>
          </div>
          <p className="issue-excerpt">{issue.excerpt}</p>
          <p>{issue.reason}</p>
          <p className="muted-copy">建议：{issue.suggested_fix}</p>
        </article>
      ))}
    </div>
  );
}

export function GenerateWorkspace() {
  const [form, setForm] = useState(defaultForm);
  const [pending, setPending] = useState(false);
  const [talentsPending, setTalentsPending] = useState(false);
  const [result, setResult] = useState<GenerateScriptResponse | null>(null);
  const [error, setError] = useState("");
  const [talents, setTalents] = useState<TalentProfile[]>([]);
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStepState[] | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

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

  async function runWorkflow() {
    setError("");
    setPending(true);
    setWorkflowSteps(createWorkflowSteps(GENERATE_STEP_DEFINITIONS));

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await streamGenerateScript(form, {
        signal: controller.signal,
        onProgress: (event) => {
          setWorkflowSteps((current) => applyWorkflowProgress(current || createWorkflowSteps(GENERATE_STEP_DEFINITIONS), event));
        },
        onError: (event) => {
          setWorkflowSteps((current) =>
            applyWorkflowProgress(current || createWorkflowSteps(GENERATE_STEP_DEFINITIONS), {
              step: event.step,
              status: "error",
              message: event.message,
            }),
          );
        },
      });

      window.setTimeout(() => {
        setResult(response);
        setWorkflowSteps(null);
        setPending(false);
      }, 300);
    } catch (requestError) {
      setPending(false);

      if (requestError instanceof WorkflowStreamAbortedError) {
        setWorkflowSteps(null);
        setError("本次生成已取消。");
      } else if (requestError instanceof WorkflowStreamTimeoutError) {
        setWorkflowSteps((current) =>
          current ? markActiveWorkflowStepError(current, "Villy 思考了太久，可能遇到了意外情况。") : current,
        );
        setError("Villy 思考了太久，可能遇到了意外情况。请重新开始。");
      } else {
        setError(requestError instanceof Error ? requestError.message : "生成失败");
      }
    } finally {
      abortControllerRef.current = null;
    }
  }

  function submit() {
    void runWorkflow();
  }

  function cancelWorkflow() {
    abortControllerRef.current?.abort();
  }

  return (
    <div className="dashboard-grid">
      <section className={`panel-card panel-card-tight ${pending ? "panel-card-disabled" : ""}`}>
        <div className="section-header">
          <div>
            <p className="section-kicker">Workflow</p>
            <h3>脚本生成控制台</h3>
          </div>
        </div>

        <label className="field">
          <span>达人选择</span>
          <select
            disabled={pending}
            value={selectedTalent?.user_id ?? form.user_id}
            onChange={(event) => setForm({ ...form, user_id: Number(event.target.value) || 0 })}
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
            <p>{talentsPending ? "正在加载达人列表..." : "当前没有可用于脚本生成的达人，请先到达人管理中新增达人。"}</p>
          </article>
        )}

        <label className="field">
          <span>主题</span>
          <textarea
            disabled={pending}
            value={form.topic}
            onChange={(event) => setForm({ ...form, topic: event.target.value })}
            rows={6}
          />
        </label>

        <div className="field">
          <span>输出语言</span>
          <div className="checkbox-grid">
            {LANGUAGE_OPTIONS.map((language) => (
              <label key={language} className="check-card">
                <input
                  checked={form.target_languages.includes(language)}
                  disabled={pending}
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
              disabled={pending}
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
              disabled={pending}
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
              disabled={pending}
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
              disabled={pending}
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
            <span>视频时长</span>
            <select
              disabled={pending}
              value={form.video_duration}
              onChange={(event) => setForm({ ...form, video_duration: event.target.value })}
            >
              {DURATION_OPTIONS.map((duration) => (
                <option key={duration} value={duration}>
                  {duration}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>品牌 ID</span>
            <input
              disabled={pending}
              value={form.brand_id}
              onChange={(event) => setForm({ ...form, brand_id: event.target.value })}
            />
          </label>
          <label className="field">
            <span>是否保存脚本记录</span>
            <select
              disabled={pending}
              value={form.persist_result ? "yes" : "no"}
              onChange={(event) => setForm({ ...form, persist_result: event.target.value === "yes" })}
            >
              <option value="no">否，仅试运行</option>
              <option value="yes">是，写入脚本记录</option>
            </select>
          </label>
        </div>

        <label className="field">
          <span>温度 / Creativity: {form.creativity.toFixed(1)}</span>
          <input
            disabled={pending}
            max={1}
            min={0.1}
            onChange={(event) => setForm({ ...form, creativity: Number(event.target.value) || 0.1 })}
            step={0.1}
            type="range"
            value={form.creativity}
          />
        </label>

        <button
          className="primary-button"
          disabled={pending || !form.topic.trim() || !selectedTalent?.user_id}
          onClick={submit}
          type="button"
        >
          {pending ? "生成中..." : "运行 /scripts/generate"}
        </button>
        {error ? <p className="error-copy">{error}</p> : null}
      </section>

      {workflowSteps ? (
        <section className="panel-card full-span">
          <WorkflowStepper
            caption="结果区会在每个关键节点完成后实时推进。"
            cancelLabel="取消生成"
            onCancel={cancelWorkflow}
            onRetry={submit}
            steps={workflowSteps}
            title="脚本生成实时进度"
          />
        </section>
      ) : (
        <>
          <section className="panel-card">
            <div className="section-header">
              <div>
                <p className="section-kicker">Output</p>
                <h3>脚本结果</h3>
              </div>
            </div>

            {result ? (
              <div className="stack-list">
                <div className="metric-grid">
                  <article className="metric-card">
                    <span>达人</span>
                    <strong>{selectedTalent?.name || `ID ${form.user_id}`}</strong>
                  </article>
                  <article className="metric-card">
                    <span>平台 / 时长</span>
                    <strong>
                      {form.target_platform} · {form.video_duration}
                    </strong>
                  </article>
                  <article className="metric-card">
                    <span>品牌 / 温度</span>
                    <strong>
                      {form.brand_id} · {form.creativity.toFixed(1)}
                    </strong>
                  </article>
                </div>
                <article className="note-card">
                  <h4>模型信息</h4>
                  <p>
                    {String(result.final_state.script_model_provider || "unknown")} ·{" "}
                    {String(result.final_state.script_model_name || "unknown")}
                  </p>
                </article>
                <article className="code-panel">
                  <h4>生成稿</h4>
                  <div className="code-panel-body">
                    <MarkdownContent content={String(result.final_state.final_script || "")} emptyText="生成稿为空。" />
                  </div>
                </article>
                <article className="code-panel">
                  <h4>修订稿</h4>
                  <div className="code-panel-body">
                    <MarkdownContent content={String(result.final_state.approved_script || "")} emptyText="修订稿为空。" />
                  </div>
                </article>
              </div>
            ) : (
              <p className="muted-copy">这里会显示脚本生成结果与修订稿。</p>
            )}
          </section>

          <section className="panel-card full-span">
            <div className="section-header">
              <div>
                <p className="section-kicker">Compliance</p>
                <h3>合规报告</h3>
              </div>
            </div>
            {renderReport(result?.final_state.compliance_report)}
          </section>
        </>
      )}
    </div>
  );
}
