"use client";

import { startTransition, useEffect, useState } from "react";

import { getLibraryDocuments, getLibraryHealth, rebuildLibrary, uploadLibraryDocument } from "@/lib/api";
import {
  LIBRARY_CATEGORY_OPTIONS,
  LIBRARY_LANGUAGE_OPTIONS,
  LIBRARY_PRIORITY_OPTIONS,
  LIBRARY_REGION_OPTIONS,
  MARKET_OPTIONS,
  PLATFORM_OPTIONS,
} from "@/lib/constants";
import type {
  LibraryDocument,
  LibraryDocumentsResponse,
  LibraryHealthResponse,
  LibraryRebuildResponse,
} from "@/lib/schemas";


const libraryPlatformOptions = [{ value: "all", label: "All Platforms" }, ...PLATFORM_OPTIONS];

const defaultUploadForm = {
  title: "",
  category: "platform_policy",
  market: "GLOBAL",
  region: "GLOBAL",
  platform: "all",
  language: "en",
  source_url: "",
  notes: "",
  priority: "P2",
};

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

function getStatusLabel(status: string) {
  if (status === "indexed") {
    return "已入库";
  }
  if (status === "pending_rebuild") {
    return "待重建";
  }
  return status || "未知";
}

function getStatusClass(status: string) {
  if (status === "indexed") {
    return "library-status-ready";
  }
  if (status === "pending_rebuild") {
    return "library-status-pending";
  }
  return "library-status-neutral";
}

export function LibraryWorkspace() {
  const [healthPending, setHealthPending] = useState(false);
  const [documentsPending, setDocumentsPending] = useState(false);
  const [uploadPending, setUploadPending] = useState(false);
  const [rebuildPending, setRebuildPending] = useState(false);
  const [health, setHealth] = useState<LibraryHealthResponse | null>(null);
  const [documents, setDocuments] = useState<LibraryDocumentsResponse | null>(null);
  const [rebuildResult, setRebuildResult] = useState<LibraryRebuildResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadForm, setUploadForm] = useState(defaultUploadForm);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function fetchHealth(initialize = false) {
    setError("");
    setHealthPending(true);
    startTransition(async () => {
      try {
        const response = await getLibraryHealth(initialize);
        setHealth(response);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "获取图书馆状态失败");
      } finally {
        setHealthPending(false);
      }
    });
  }

  function fetchDocuments() {
    setError("");
    setDocumentsPending(true);
    startTransition(async () => {
      try {
        const response = await getLibraryDocuments();
        setDocuments(response);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "获取图书馆文档失败");
      } finally {
        setDocumentsPending(false);
      }
    });
  }

  function resetUploadForm() {
    setSelectedFile(null);
    setUploadForm(defaultUploadForm);
  }

  function submitUpload() {
    if (!selectedFile) {
      setError("请先选择一个文件。");
      return;
    }

    setError("");
    setNotice("");
    setUploadPending(true);
    startTransition(async () => {
      try {
        const response = await uploadLibraryDocument({
          file: selectedFile,
          title: uploadForm.title || selectedFile.name.replace(/\.[^.]+$/, ""),
          category: uploadForm.category,
          market: uploadForm.market,
          region: uploadForm.region,
          platform: uploadForm.platform,
          language: uploadForm.language,
          source_url: uploadForm.source_url,
          notes: uploadForm.notes,
          priority: uploadForm.priority,
        });
        setNotice(`资料 ${response.item.title} 已上传，当前状态为“${getStatusLabel(response.item.status)}”。`);
        resetUploadForm();
        fetchDocuments();
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "上传资料失败");
      } finally {
        setUploadPending(false);
      }
    });
  }

  function runRebuild() {
    setError("");
    setNotice("");
    setRebuildPending(true);
    startTransition(async () => {
      try {
        const response = await rebuildLibrary();
        setRebuildResult(response);
        setHealth(response.runtime);
        setNotice(
          `重建完成：扫描 ${response.normalized.raw_files} 份原始资料，输出 ${response.normalized.processed_documents} 份规范化文档。`,
        );
        fetchDocuments();
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "重建图书馆失败");
      } finally {
        setRebuildPending(false);
      }
    });
  }

  useEffect(() => {
    fetchHealth(false);
    fetchDocuments();
  }, []);

  return (
    <div className="dashboard-grid">
      <section className="panel-card panel-card-tight">
        <div className="section-header">
          <div>
            <p className="section-kicker">Library Upload</p>
            <h3>添加资料</h3>
          </div>
        </div>

        <label className="field">
          <span>选择文件</span>
          <input
            accept=".pdf,.html,.md,.markdown,.txt"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            type="file"
          />
        </label>

        <label className="field">
          <span>资料标题</span>
          <input
            placeholder="不填则默认使用文件名"
            value={uploadForm.title}
            onChange={(event) => setUploadForm({ ...uploadForm, title: event.target.value })}
          />
        </label>

        <div className="two-column-fields">
          <label className="field">
            <span>资料分类</span>
            <select
              value={uploadForm.category}
              onChange={(event) => setUploadForm({ ...uploadForm, category: event.target.value })}
            >
              {LIBRARY_CATEGORY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>优先级</span>
            <select
              value={uploadForm.priority}
              onChange={(event) => setUploadForm({ ...uploadForm, priority: event.target.value })}
            >
              {LIBRARY_PRIORITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>市场</span>
            <select
              value={uploadForm.market}
              onChange={(event) => setUploadForm({ ...uploadForm, market: event.target.value })}
            >
              <option value="GLOBAL">Global</option>
              {MARKET_OPTIONS.map((option) => (
                <option key={option.code} value={option.code}>
                  {option.label} ({option.code})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>区域包</span>
            <select
              value={uploadForm.region}
              onChange={(event) => setUploadForm({ ...uploadForm, region: event.target.value })}
            >
              {LIBRARY_REGION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>平台</span>
            <select
              value={uploadForm.platform}
              onChange={(event) => setUploadForm({ ...uploadForm, platform: event.target.value })}
            >
              {libraryPlatformOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>语言</span>
            <select
              value={uploadForm.language}
              onChange={(event) => setUploadForm({ ...uploadForm, language: event.target.value })}
            >
              {LIBRARY_LANGUAGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="field">
          <span>原始来源链接</span>
          <input
            placeholder="可选"
            value={uploadForm.source_url}
            onChange={(event) => setUploadForm({ ...uploadForm, source_url: event.target.value })}
          />
        </label>

        <label className="field">
          <span>备注</span>
          <textarea
            placeholder="例如：用于 TikTok 美国市场达人带货合规审查"
            rows={4}
            value={uploadForm.notes}
            onChange={(event) => setUploadForm({ ...uploadForm, notes: event.target.value })}
          />
        </label>

        <div className="form-actions">
          <button className="primary-button section-button" disabled={uploadPending} onClick={submitUpload} type="button">
            {uploadPending ? "上传中..." : "上传资料"}
          </button>
          <button className="secondary-button section-button" disabled={uploadPending} onClick={resetUploadForm} type="button">
            重置表单
          </button>
        </div>

        <p className="muted-copy">
          当前支持 `pdf / html / md / txt`。上传后会进入图书馆清单，状态通常为“待重建”，点右侧按钮后才会进入最新索引。
        </p>
      </section>

      <section className="panel-card">
        <div className="section-header">
          <div>
            <p className="section-kicker">Runtime</p>
            <h3>图书馆状态</h3>
          </div>
          <div className="module-actions">
            <button
              className="secondary-button section-button"
              disabled={healthPending || rebuildPending}
              onClick={() => fetchHealth(false)}
              type="button"
            >
              {healthPending ? "刷新中..." : "刷新状态"}
            </button>
            <button
              className="primary-button section-button"
              disabled={rebuildPending}
              onClick={runRebuild}
              type="button"
            >
              {rebuildPending ? "重建中..." : "刷新 / 重建图书馆"}
            </button>
          </div>
        </div>

        {health ? (
          <div className="stack-list">
            <div className="metric-grid">
              <article className="metric-card">
                <span>状态</span>
                <strong>{health.status}</strong>
              </article>
              <article className="metric-card">
                <span>文档</span>
                <strong>{health.documents}</strong>
              </article>
              <article className="metric-card">
                <span>分块</span>
                <strong>{health.chunks}</strong>
              </article>
            </div>
            <article className="note-card">
              <h4>索引构建时间</h4>
              <p>{formatTimestamp(health.built_at)}</p>
            </article>
            <article className="note-card">
              <h4>Embedding Backend</h4>
              <p>{health.embedding_backend}</p>
            </article>
            <article className="note-card">
              <h4>目录</h4>
              <p>{health.knowledge_base_root}</p>
              <p>{health.raw_root}</p>
              <p>{health.processed_root}</p>
            </article>
            {rebuildResult ? (
              <article className="note-card">
                <h4>最近一次重建</h4>
                <p>扫描原始资料：{rebuildResult.normalized.raw_files}</p>
                <p>输出规范文档：{rebuildResult.normalized.processed_documents}</p>
                <p>{rebuildResult.normalized.manifest_path}</p>
              </article>
            ) : null}
          </div>
        ) : (
          <p className="muted-copy">这里会展示知识库健康状态。</p>
        )}
      </section>

      <section className="panel-card full-span">
        <div className="section-header">
          <div>
            <p className="section-kicker">Documents</p>
            <h3>图书馆资料清单</h3>
          </div>
          <div className="module-actions">
            <span className="topbar-chip topbar-chip-muted">共 {documents?.total ?? 0} 份资料</span>
            <button
              className="secondary-button section-button"
              disabled={documentsPending}
              onClick={fetchDocuments}
              type="button"
            >
              {documentsPending ? "刷新中..." : "刷新文档列表"}
            </button>
          </div>
        </div>

        {notice ? <p className="success-copy">{notice}</p> : null}
        {error ? <p className="error-copy">{error}</p> : null}

        {documents?.items.length ? (
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>资料</th>
                  <th>分类</th>
                  <th>平台 / 市场</th>
                  <th>状态</th>
                  <th>更新时间</th>
                  <th>来源</th>
                  <th>备注</th>
                </tr>
              </thead>
              <tbody>
                {documents.items.map((item: LibraryDocument) => (
                  <tr key={item.source_id}>
                    <td>
                      <div className="table-name-block">
                        <strong>{item.title}</strong>
                        <span className="muted-copy">{item.source_id}</span>
                        <span className="muted-copy">
                          {item.file_origin} {item.raw_suffix ? `· ${item.raw_suffix}` : ""}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className="table-name-block">
                        <strong>{item.category}</strong>
                        <span className="muted-copy">{item.priority}</span>
                      </div>
                    </td>
                    <td>
                      <div className="table-name-block">
                        <strong>{item.platform}</strong>
                        <span className="muted-copy">
                          {item.market} · {item.region} · {item.language}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`topbar-chip ${getStatusClass(item.status)}`}>{getStatusLabel(item.status)}</span>
                    </td>
                    <td>{formatTimestamp(item.updated_at)}</td>
                    <td>
                      {item.source_url ? (
                        <a className="table-link" href={item.source_url} rel="noreferrer" target="_blank">
                          打开来源
                        </a>
                      ) : (
                        <span className="muted-copy">未填写</span>
                      )}
                    </td>
                    <td className="table-notes">{item.notes || <span className="muted-copy">无备注</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <article className="empty-state">
            <p>图书馆里还没有可展示的资料。你可以先上传一份文件，然后点击“刷新 / 重建图书馆”。</p>
          </article>
        )}
      </section>
    </div>
  );
}
