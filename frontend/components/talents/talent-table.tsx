"use client";

import { startTransition, useEffect, useState } from "react";

import { createTalent, deleteTalent, getTalents, updateTalent } from "@/lib/api";
import type { TalentMutationRequest, TalentProfile } from "@/lib/schemas";
import { TalentKanban } from "@/components/talents/talent-kanban";
import { TalentTodos } from "@/components/talents/talent-todos";
import {
  buildTalentMutationPayload,
  getTalentBoardColumn,
  resolveTalentStageKey,
  type TalentStageKey,
} from "@/components/talents/talent-board-utils";

const emptyForm: TalentMutationRequest = {
  name: "",
  platform: "TikTok",
  email: "",
  recent_video_link: "",
  notes: "",
  collaboration_progress: "待沟通",
};

function getProgressTone(progress: string) {
  if (progress.includes("已合作") || progress.includes("完成") || progress.includes("交付")) {
    return "risk-low";
  }
  if (
    progress.includes("跟进") ||
    progress.includes("推进") ||
    progress.includes("对接") ||
    progress.includes("沟通") ||
    progress.includes("签约") ||
    progress.includes("制作") ||
    progress.includes("拍摄") ||
    progress.includes("创作")
  ) {
    return "risk-medium";
  }
  return "topbar-chip-muted";
}

function renderRecentLink(url: string) {
  const trimmed = url.trim();
  if (!trimmed) {
    return <span className="muted-copy">未填写</span>;
  }

  return (
    <a className="table-link" href={trimmed} rel="noreferrer" target="_blank">
      查看视频
    </a>
  );
}

export function TalentTable() {
  const [talents, setTalents] = useState<TalentProfile[]>([]);
  const [pending, setPending] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [movingId, setMovingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<TalentMutationRequest>(emptyForm);

  function fetchTalents() {
    setError("");
    setPending(true);
    startTransition(async () => {
      try {
        const response = await getTalents();
        setTalents(response.items);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "获取达人列表失败");
      } finally {
        setPending(false);
      }
    });
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
  }

  function beginEdit(talent: TalentProfile) {
    setEditingId(talent.id);
    setForm({
      name: talent.name,
      platform: talent.platform || "未设置",
      email: talent.email || "",
      recent_video_link: talent.recent_video_link || "",
      notes: talent.notes || "",
      collaboration_progress: talent.collaboration_progress || "待沟通",
    });
  }

  function submitForm() {
    if (!form.name.trim()) {
      setError("达人名称不能为空。");
      return;
    }

    setError("");
    setSubmitting(true);
    startTransition(async () => {
      try {
        if (editingId === null) {
          await createTalent(form);
        } else {
          await updateTalent(editingId, form);
        }
        resetForm();
        fetchTalents();
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "保存达人资料失败");
      } finally {
        setSubmitting(false);
      }
    });
  }

  function removeTalentRecord(talent: TalentProfile) {
    const confirmed = window.confirm(`确认删除达人「${talent.name}」吗？删除后不可恢复。`);
    if (!confirmed) {
      return;
    }

    setError("");
    setDeletingId(talent.id);
    startTransition(async () => {
      try {
        await deleteTalent(talent.id);
        if (editingId === talent.id) {
          resetForm();
        }
        fetchTalents();
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "删除达人失败");
      } finally {
        setDeletingId(null);
      }
    });
  }

  function moveTalentToStage(talent: TalentProfile, targetStage: TalentStageKey) {
    const targetColumn = getTalentBoardColumn(targetStage);
    const nextProgress = targetColumn.defaultProgress;

    setError("");
    setMovingId(talent.id);
    setTalents((current) =>
      current.map((item) =>
        item.id === talent.id
          ? {
              ...item,
              collaboration_progress: nextProgress,
            }
          : item,
      ),
    );
    if (editingId === talent.id) {
      setForm((current) => ({ ...current, collaboration_progress: nextProgress }));
    }

    startTransition(async () => {
      try {
        const response = await updateTalent(
          talent.id,
          buildTalentMutationPayload(talent, { collaboration_progress: nextProgress }),
        );
        setTalents((current) => current.map((item) => (item.id === talent.id ? response.item : item)));
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "更新达人阶段失败");
        fetchTalents();
      } finally {
        setMovingId(null);
      }
    });
  }

  useEffect(() => {
    fetchTalents();
  }, []);

  const platformCount = new Set(talents.map((talent) => talent.platform).filter(Boolean)).size;
  const activeCount = talents.filter((talent) => {
    const stage = resolveTalentStageKey(talent.collaboration_progress);
    return stage !== "pending" && stage !== "done";
  }).length;
  const boardBusy = submitting || deletingId !== null || movingId !== null;

  return (
    <div className="content-scroll">
      <div className="dashboard-grid">
        <section className="panel-card panel-card-tight">
          <div className="section-header">
            <div>
              <p className="section-kicker">Talent Editor</p>
              <h3>{editingId === null ? "新增达人资料" : `编辑达人 #${editingId}`}</h3>
            </div>
          </div>

          <div className="stack-list">
            <label className="field">
              <span>达人名称</span>
              <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            </label>

            <div className="two-column-fields">
              <label className="field">
                <span>平台</span>
                <input
                  value={form.platform}
                  onChange={(event) => setForm({ ...form, platform: event.target.value })}
                />
              </label>
              <label className="field">
                <span>合作进度</span>
                <input
                  value={form.collaboration_progress}
                  onChange={(event) => setForm({ ...form, collaboration_progress: event.target.value })}
                />
              </label>
            </div>

            <label className="field">
              <span>邮箱</span>
              <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>

            <label className="field">
              <span>近期视频链接</span>
              <input
                value={form.recent_video_link}
                onChange={(event) => setForm({ ...form, recent_video_link: event.target.value })}
              />
            </label>

            <label className="field">
              <span>备注描述</span>
              <textarea
                rows={6}
                value={form.notes}
                onChange={(event) => setForm({ ...form, notes: event.target.value })}
              />
            </label>

            <div className="form-actions">
              <button className="primary-button section-button" disabled={submitting} onClick={submitForm} type="button">
                {submitting ? "保存中..." : editingId === null ? "新增达人" : "保存修改"}
              </button>
              <button className="secondary-button section-button" disabled={submitting} onClick={resetForm} type="button">
                清空表单
              </button>
            </div>
          </div>
        </section>

        <section className="panel-card">
          <div className="section-header">
            <div>
              <p className="section-kicker">Talent CRM</p>
              <h3>达人管理总览</h3>
            </div>
            <button className="secondary-button section-button" disabled={pending} onClick={fetchTalents} type="button">
              {pending ? "刷新中..." : "刷新达人列表"}
            </button>
          </div>

          <div className="metric-grid">
            <article className="metric-card">
              <span>达人总数</span>
              <strong>{talents.length}</strong>
            </article>
            <article className="metric-card">
              <span>平台数</span>
              <strong>{platformCount}</strong>
            </article>
            <article className="metric-card">
              <span>推进中</span>
              <strong>{activeCount}</strong>
            </article>
          </div>

          <div className="talent-crm-stack">
            <TalentTodos talents={talents} />
            <TalentKanban
              draggingDisabled={boardBusy}
              movingId={movingId}
              onEdit={beginEdit}
              onMove={moveTalentToStage}
              talents={talents}
            />
          </div>
        </section>
      </div>

      <section className="panel-card">
        <div className="section-header">
          <div>
            <p className="section-kicker">Directory</p>
            <h3>达人资料表</h3>
          </div>
        </div>

        {error ? <p className="error-copy">{error}</p> : null}

        {talents.length ? (
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>达人ID</th>
                  <th>名称</th>
                  <th>平台</th>
                  <th>邮箱</th>
                  <th>近期视频链接</th>
                  <th>备注描述</th>
                  <th>合作进度</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {talents.map((talent) => (
                  <tr key={talent.id}>
                    <td>{talent.id}</td>
                    <td>
                      <div className="table-name-block">
                        <strong>{talent.name}</strong>
                        <span className="muted-copy">user_id: {talent.user_id ?? "-"}</span>
                      </div>
                    </td>
                    <td>{talent.platform || "未设置"}</td>
                    <td>{talent.email || "未填写"}</td>
                    <td>{renderRecentLink(talent.recent_video_link)}</td>
                    <td className="table-notes">{talent.notes || "待补充达人备注"}</td>
                    <td>
                      <span className={`risk-tag ${getProgressTone(talent.collaboration_progress)}`}>
                        {talent.collaboration_progress}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button className="table-button" onClick={() => beginEdit(talent)} type="button">
                          编辑
                        </button>
                        <button
                          className="table-button table-button-danger"
                          disabled={deletingId === talent.id}
                          onClick={() => removeTalentRecord(talent)}
                          type="button"
                        >
                          {deletingId === talent.id ? "删除中..." : "删除"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <p>当前还没有达人资料。系统会优先从原有 `users` 表同步基础达人信息到 `talent_profiles`。</p>
          </div>
        )}
      </section>
    </div>
  );
}
