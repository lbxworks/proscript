"use client";

import type { CSSProperties } from "react";
import { useMemo, useState } from "react";

import type { TalentProfile } from "@/lib/schemas";
import {
  TALENT_BOARD_COLUMNS,
  resolveTalentStageKey,
  type TalentStageKey,
} from "@/components/talents/talent-board-utils";

type TalentKanbanProps = {
  talents: TalentProfile[];
  draggingDisabled?: boolean;
  movingId?: number | null;
  onEdit: (talent: TalentProfile) => void;
  onMove: (talent: TalentProfile, targetStage: TalentStageKey) => void;
};

export function TalentKanban({
  talents,
  draggingDisabled = false,
  movingId = null,
  onEdit,
  onMove,
}: TalentKanbanProps) {
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [hoverColumn, setHoverColumn] = useState<TalentStageKey | null>(null);

  const groupedTalents = useMemo(() => {
    const groups = new Map<TalentStageKey, TalentProfile[]>();
    for (const column of TALENT_BOARD_COLUMNS) {
      groups.set(column.key, []);
    }

    for (const talent of talents) {
      const stageKey = resolveTalentStageKey(talent.collaboration_progress);
      groups.get(stageKey)?.push(talent);
    }

    return groups;
  }, [talents]);

  function handleDrop(targetStage: TalentStageKey) {
    if (draggingDisabled || draggingId === null) {
      setHoverColumn(null);
      return;
    }

    const talent = talents.find((item) => item.id === draggingId);
    setDraggingId(null);
    setHoverColumn(null);

    if (!talent) {
      return;
    }

    if (resolveTalentStageKey(talent.collaboration_progress) === targetStage) {
      return;
    }

    onMove(talent, targetStage);
  }

  return (
    <section className="talent-kanban-shell">
      <div className="section-header">
        <div>
          <p className="section-kicker">Kanban Board</p>
          <h3>达人合作看板</h3>
        </div>
      </div>

      <div className="talent-kanban-scroll">
        <div className="talent-kanban-grid">
          {TALENT_BOARD_COLUMNS.map((column) => {
            const items = groupedTalents.get(column.key) || [];
            const isHovering = hoverColumn === column.key;

            return (
              <article
                key={column.key}
                className={`talent-kanban-column ${isHovering ? "is-hovering" : ""}`}
                onDragOver={(event) => {
                  if (draggingDisabled) {
                    return;
                  }
                  event.preventDefault();
                  setHoverColumn(column.key);
                }}
                onDragLeave={() => {
                  if (hoverColumn === column.key) {
                    setHoverColumn(null);
                  }
                }}
                onDrop={(event) => {
                  event.preventDefault();
                  handleDrop(column.key);
                }}
                style={{ "--kanban-accent": column.color } as CSSProperties}
              >
                <header className="talent-kanban-column-head">
                  <div className="talent-kanban-column-title">
                    <span className="talent-kanban-column-dot" />
                    <h4>{column.title}</h4>
                  </div>
                  <span className="talent-kanban-count">{items.length}</span>
                </header>

                <div className="talent-kanban-dropzone">
                  {items.length ? (
                    items.map((talent) => {
                      return (
                        <article
                          key={talent.id}
                          className={`talent-kanban-card ${
                            draggingId === talent.id ? "is-dragging" : ""
                          } ${movingId === talent.id ? "is-updating" : ""}`}
                          draggable={!draggingDisabled}
                          onDragStart={(event) => {
                            if (draggingDisabled) {
                              return;
                            }
                            event.dataTransfer.effectAllowed = "move";
                            event.dataTransfer.setData("text/plain", String(talent.id));
                            setDraggingId(talent.id);
                          }}
                          onDragEnd={() => {
                            setDraggingId(null);
                            setHoverColumn(null);
                          }}
                        >
                          <div className="talent-kanban-card-topline">
                            <div className="talent-kanban-card-head">
                              <h5>{talent.name}</h5>
                              <span className="talent-kanban-platform">{talent.platform || "未设置"}</span>
                            </div>
                            <button className="table-button" onClick={() => onEdit(talent)} type="button">
                              编辑
                            </button>
                          </div>

                          {talent.email ? <p className="talent-kanban-email">{talent.email}</p> : null}

                          <div className="talent-kanban-card-foot">
                            <span className="talent-kanban-progress-tag">
                              {talent.collaboration_progress || column.defaultProgress}
                            </span>
                          </div>
                        </article>
                      );
                    })
                  ) : (
                    <div className="talent-kanban-empty">
                      <p>这一列暂时没有达人，拖拽卡片到这里即可更新阶段。</p>
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
