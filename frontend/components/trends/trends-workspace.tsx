"use client";

import { useEffect, useRef, useState } from "react";

import { MarkdownContent } from "@/components/ui/markdown-content";
import {
  WorkflowStepper,
  applyWorkflowProgress,
  createWorkflowSteps,
  markActiveWorkflowStepError,
  type WorkflowStepDefinition,
  type WorkflowStepState,
} from "@/components/shared/workflow-stepper";
import { streamTrends, WorkflowStreamAbortedError, WorkflowStreamTimeoutError } from "@/lib/api";
import {
  DISTRIBUTION_OPTIONS,
  LANGUAGE_OPTIONS,
  MARKET_OPTIONS,
  PLATFORM_OPTIONS,
  PRODUCT_OPTIONS,
} from "@/lib/constants";
import type { IndustryInsight, TrendBenchmark, TrendModuleMeta, TrendsResponse } from "@/lib/schemas";

const defaultFilters = {
  topic: "",
  target_country: "US",
  target_platform: "tiktok",
  distribution_mode: "branded_content",
  product_category: "general",
  target_languages: ["English"],
};

type LoadMode = "cache" | "videos" | "industry";

const TREND_STEP_DEFINITIONS: WorkflowStepDefinition[] = [
  {
    key: "video_search",
    title: "步骤 1：全球热门视频搜索",
    messages: ["连接 Tavily 数据网络...", "扫描平台爆款对标视频..."],
  },
  {
    key: "industry_scan",
    title: "步骤 2：三大行业情报扫描",
    messages: ["获取科技行业最新动态...", "追踪视频行业变化...", "分析营销行业趋势..."],
  },
  {
    key: "trend_summary",
    title: "步骤 3：Villy 深度趋势解读",
    messages: ["AI 正在阅读并提炼所有情报...", "生成可执行的趋势洞察..."],
  },
];

function formatTimestamp(value?: string) {
  if (!value) {
    return "暂无";
  }

  const normalized = value.includes("T") ? value : `${value.replace(" ", "T")}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

function ModuleMetaBadge({
  meta,
  emptyCopy,
}: {
  meta?: TrendModuleMeta;
  emptyCopy: string;
}) {
  if (!meta) {
    return <span className="topbar-chip topbar-chip-muted">{emptyCopy}</span>;
  }

  if (meta.stale) {
    return <span className="topbar-chip module-chip-warn">刷新失败，已回退到缓存</span>;
  }

  if (meta.from_cache) {
    return <span className="topbar-chip topbar-chip-muted">展示上一次内容</span>;
  }

  return <span className="topbar-chip module-chip-live">已实时刷新</span>;
}

function IndustryCard({ item }: { item: IndustryInsight }) {
  return (
    <article className="industry-card">
      <div className="industry-card-head">
        <div>
          <p className="section-kicker">{item.label}</p>
          <h4>{item.label}动态</h4>
        </div>
      </div>
      <p>{item.summary || "本次未返回可用摘要，建议点击刷新重试。"}</p>
      <div className="industry-query">{item.query}</div>
      <div className="stack-list">
        {item.articles.length ? (
          item.articles.map((article) => (
            <a key={article.url} className="industry-link-card" href={article.url} rel="noreferrer" target="_blank">
              <strong>{article.title}</strong>
              <p>{article.summary || "暂无摘要。"}</p>
              <span className="muted-copy">
                {article.source} · score {article.score.toFixed(2)}
              </span>
            </a>
          ))
        ) : (
          <article className="note-card">
            <p className="muted-copy">当前没有返回可展示的行业文章。</p>
          </article>
        )}
      </div>
    </article>
  );
}

function VideoCard({
  item,
  copied,
  onCopy,
}: {
  item: TrendBenchmark;
  copied: boolean;
  onCopy: (url: string) => void;
}) {
  const heatLabel = item.view_count > 0 ? item.view_count_label : "实时命中";
  const scoreLabel = typeof item.score === "number" ? item.score.toFixed(2) : String(item.score || "");

  return (
    <article className="video-card">
      <a className="video-card-cover" href={item.url} rel="noreferrer" target="_blank">
        {item.image_url ? (
          <img alt={item.title} className="video-card-image" src={item.image_url} />
        ) : (
          <div className="video-card-fallback">
            <span>{item.platform}</span>
            <strong>{heatLabel}</strong>
          </div>
        )}
        <div className="video-card-overlay">
          <span className="video-chip">{item.platform}</span>
          <span className="video-chip video-chip-highlight">{heatLabel}</span>
        </div>
      </a>

      <div className="video-card-body">
        <div className="video-card-meta">
          <span>{item.platform}</span>
          <span>相关度 {scoreLabel}</span>
        </div>
        <h4>{item.title}</h4>
        <p>{item.summary || "Tavily 已命中该视频，但本次没有返回更多摘要。点击卡片查看原始内容。"}</p>
        <div className="video-card-actions">
          <a className="video-action-link" href={item.url} rel="noreferrer" target="_blank">
            查看原视频
          </a>
          <button className="video-action-button" onClick={() => onCopy(item.url)} type="button">
            {copied ? "已复制链接" : "复制链接"}
          </button>
        </div>
      </div>
    </article>
  );
}

export function TrendsWorkspace() {
  const [filters, setFilters] = useState(defaultFilters);
  const [pendingMode, setPendingMode] = useState<LoadMode | null>(null);
  const [lastMode, setLastMode] = useState<LoadMode>("cache");
  const [result, setResult] = useState<TrendsResponse | null>(null);
  const [error, setError] = useState("");
  const [copiedUrl, setCopiedUrl] = useState("");
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStepState[] | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  async function copyVideoLink(url: string) {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedUrl(url);
      window.setTimeout(() => {
        setCopiedUrl((current) => (current === url ? "" : current));
      }, 1800);
    } catch {
      setError("复制链接失败，请稍后重试。");
    }
  }

  function toggleLanguage(language: string) {
    const nextLanguages = filters.target_languages.includes(language)
      ? filters.target_languages.filter((item) => item !== language)
      : [...filters.target_languages, language];

    if (nextLanguages.length === 0) {
      return;
    }

    setFilters({ ...filters, target_languages: nextLanguages });
  }

  async function runWorkflow(mode: LoadMode) {
    setError("");
    setPendingMode(mode);
    setLastMode(mode);
    setWorkflowSteps(createWorkflowSteps(TREND_STEP_DEFINITIONS));

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await streamTrends(
        {
          ...filters,
          refresh_videos: mode === "videos",
          refresh_industry: mode === "industry",
        },
        {
          signal: controller.signal,
          onProgress: (event) => {
            setWorkflowSteps((current) => applyWorkflowProgress(current || createWorkflowSteps(TREND_STEP_DEFINITIONS), event));
          },
          onError: (event) => {
            setWorkflowSteps((current) =>
              applyWorkflowProgress(current || createWorkflowSteps(TREND_STEP_DEFINITIONS), {
                step: event.step,
                status: "error",
                message: event.message,
              }),
            );
          },
        },
      );

      window.setTimeout(() => {
        setResult(response);
        setWorkflowSteps(null);
        setPendingMode(null);
      }, 300);
    } catch (requestError) {
      setPendingMode(null);

      if (requestError instanceof WorkflowStreamAbortedError) {
        setWorkflowSteps(null);
        setError("本次热点探索已取消。");
      } else if (requestError instanceof WorkflowStreamTimeoutError) {
        setWorkflowSteps((current) =>
          current ? markActiveWorkflowStepError(current, "Villy 思考了太久，可能遇到了意外情况。") : current,
        );
        setError("Villy 思考了太久，可能遇到了意外情况。请重新开始。");
      } else {
        setError(requestError instanceof Error ? requestError.message : "获取热点失败");
      }
    } finally {
      abortControllerRef.current = null;
    }
  }

  function fetchData(mode: LoadMode) {
    void runWorkflow(mode);
  }

  useEffect(() => {
    fetchData("cache");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function cancelWorkflow() {
    abortControllerRef.current?.abort();
  }

  return (
    <div className="dashboard-grid">
      <section className={`panel-card panel-card-tight ${pendingMode !== null ? "panel-card-disabled" : ""}`}>
        <div className="section-header">
          <div>
            <p className="section-kicker">Discovery</p>
            <h3>热点探索过滤器</h3>
          </div>
        </div>

        <label className="field">
          <span>主题关键词</span>
          <input
            disabled={pendingMode !== null}
            placeholder="例如：折叠屏、AI 眼镜、跨境美妆"
            value={filters.topic}
            onChange={(event) => setFilters({ ...filters, topic: event.target.value })}
          />
        </label>

        <div className="field">
          <span>目标语言</span>
          <div className="checkbox-grid">
            {LANGUAGE_OPTIONS.map((language) => (
              <label key={language} className="check-card">
                <input
                  checked={filters.target_languages.includes(language)}
                  disabled={pendingMode !== null}
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
              disabled={pendingMode !== null}
              value={filters.target_country}
              onChange={(event) => setFilters({ ...filters, target_country: event.target.value })}
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
              disabled={pendingMode !== null}
              value={filters.target_platform}
              onChange={(event) => setFilters({ ...filters, target_platform: event.target.value })}
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
              disabled={pendingMode !== null}
              value={filters.distribution_mode}
              onChange={(event) => setFilters({ ...filters, distribution_mode: event.target.value })}
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
              disabled={pendingMode !== null}
              value={filters.product_category}
              onChange={(event) => setFilters({ ...filters, product_category: event.target.value })}
            >
              {PRODUCT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-actions">
          <button
            className="primary-button section-button"
            disabled={pendingMode !== null}
            onClick={() => fetchData("cache")}
            type="button"
          >
            {pendingMode === "cache" ? "读取中..." : "读取已缓存内容"}
          </button>
        </div>
        <p className="muted-copy">
          默认优先展示上一次抓取结果，只有点模块刷新按钮时才重新请求 Tavily，避免页面一直等待。
        </p>
        {error ? <p className="error-copy">{error}</p> : null}
      </section>

      {workflowSteps ? (
        <section className="panel-card full-span">
          <WorkflowStepper
            caption="热点视频、行业情报和趋势解读会按阶段依次返回。"
            cancelLabel="取消探索"
            onCancel={cancelWorkflow}
            onRetry={() => fetchData(lastMode)}
            steps={workflowSteps}
            title="热点探索实时进度"
          />
        </section>
      ) : (
        <>
          <section className="panel-card">
            <div className="section-header">
              <div>
                <p className="section-kicker">Industry</p>
                <h3>行业情报摘要</h3>
              </div>
              <div className="module-actions">
                <ModuleMetaBadge meta={result?.industry} emptyCopy="尚未加载" />
                <button
                  className="secondary-button section-button"
                  disabled={pendingMode !== null}
                  onClick={() => fetchData("industry")}
                  type="button"
                >
                  {pendingMode === "industry" ? "刷新中..." : "刷新行业情报"}
                </button>
              </div>
            </div>
            <article className="note-card">
              <h4>主题趋势摘要</h4>
              <p className="muted-copy">
                最近更新时间：{formatTimestamp(result?.industry.cached_at)} {result?.industry.stale ? "· 当前是缓存兜底结果" : ""}
              </p>
              <p>{result?.industry.topic_brief.trend_query || "未填写主题时只展示行业情报与热点视频。"}</p>
            </article>
            <article className="code-panel">
              <div className="code-panel-body">
                <MarkdownContent
                  content={result?.industry.topic_brief.trend_data || ""}
                  emptyText="这里会显示主题趋势摘要。"
                />
              </div>
            </article>
          </section>

          <section className="panel-card full-span">
            <div className="section-header">
              <div>
                <p className="section-kicker">Videos</p>
                <h3>合适的视频</h3>
              </div>
              <div className="module-actions">
                <ModuleMetaBadge meta={result?.videos} emptyCopy="尚未加载" />
                <button
                  className="secondary-button section-button"
                  disabled={pendingMode !== null}
                  onClick={() => fetchData("videos")}
                  type="button"
                >
                  {pendingMode === "videos" ? "刷新中..." : "刷新热点视频"}
                </button>
              </div>
            </div>
            <p className="muted-copy">
              最近更新时间：{formatTimestamp(result?.videos.cached_at)} {result?.videos.stale ? "· 刷新失败时自动保留上一次结果" : ""}
            </p>
            {result?.videos.error ? <p className="error-copy">{result.videos.error}</p> : null}
            <div className="video-grid">
              {(result?.videos.items || []).map((item) => (
                <VideoCard key={item.url} copied={copiedUrl === item.url} item={item} onCopy={copyVideoLink} />
              ))}
            </div>
            {result?.videos.items?.length ? null : (
              <article className="empty-state">
                <p>当前没有返回可展示的视频样本，可以调整主题后再刷新一次。</p>
              </article>
            )}
          </section>

          <section className="panel-card full-span">
            <div className="section-header">
              <div>
                <p className="section-kicker">Industry Signals</p>
                <h3>科技、视频、营销行业信息</h3>
              </div>
            </div>
            {result?.industry.error ? <p className="error-copy">{result.industry.error}</p> : null}
            <div className="industry-grid">
              {(result?.industry.categories || []).map((item) => (
                <IndustryCard key={item.key} item={item} />
              ))}
            </div>
            {result?.industry.categories?.length ? null : (
              <article className="empty-state">
                <p>当前没有缓存到行业情报，点“刷新行业情报”后会实时抓取科技、视频和营销三类内容。</p>
              </article>
            )}
          </section>
        </>
      )}
    </div>
  );
}
