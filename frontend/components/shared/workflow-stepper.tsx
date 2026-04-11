"use client";

import { useEffect, useMemo, useState } from "react";

import type { WorkflowProgressEvent, WorkflowStepStatus } from "@/lib/schemas";

export type WorkflowStepDefinition = {
  key: string;
  title: string;
  messages: string[];
};

export type WorkflowStepState = WorkflowStepDefinition & {
  status: WorkflowStepStatus;
  durationMs?: number;
  serverMessage?: string;
  errorMessage?: string;
};

export function createWorkflowSteps(definitions: WorkflowStepDefinition[]): WorkflowStepState[] {
  return definitions.map((item) => ({
    ...item,
    status: "pending",
  }));
}

export function applyWorkflowProgress(
  currentSteps: WorkflowStepState[],
  event: WorkflowProgressEvent,
): WorkflowStepState[] {
  const targetIndex = currentSteps.findIndex((item) => item.key === event.step);

  return currentSteps.map((item, index) => {
    if (item.key === event.step) {
      return {
        ...item,
        status: event.status,
        durationMs: event.duration_ms ?? item.durationMs,
        serverMessage: event.message || item.serverMessage,
        errorMessage: event.status === "error" ? event.message : undefined,
      };
    }

    if (event.status === "active" && item.status === "active" && index < targetIndex) {
      return {
        ...item,
        status: "completed",
      };
    }

    return item;
  });
}

export function markActiveWorkflowStepError(
  currentSteps: WorkflowStepState[],
  message: string,
): WorkflowStepState[] {
  const activeIndex = currentSteps.findIndex((item) => item.status === "active");
  const targetIndex = activeIndex >= 0 ? activeIndex : currentSteps.findLastIndex((item) => item.status === "completed") + 1;

  return currentSteps.map((item, index) => {
    if (index === targetIndex && item) {
      return {
        ...item,
        status: "error",
        errorMessage: message,
        serverMessage: message,
      };
    }
    return item;
  });
}

function formatDuration(durationMs?: number) {
  if (!durationMs) {
    return "";
  }

  if (durationMs < 1_000) {
    return `${durationMs}ms`;
  }

  return `${(durationMs / 1_000).toFixed(1)}s`;
}

function StepMessage({ step }: { step: WorkflowStepState }) {
  const messagePool = useMemo(() => {
    const items = step.serverMessage ? [step.serverMessage, ...step.messages] : step.messages;
    return items.length ? items : ["正在处理中..."];
  }, [step.messages, step.serverMessage]);

  const [messageIndex, setMessageIndex] = useState(0);
  const [visibleChars, setVisibleChars] = useState(0);

  useEffect(() => {
    if (step.status !== "active") {
      setMessageIndex(0);
      setVisibleChars(0);
      return;
    }

    let cancelled = false;
    let typingTimer: number | null = null;
    let holdTimer: number | null = null;
    let nextIndex = 0;

    const typeCurrentMessage = () => {
      const message = messagePool[nextIndex] || "正在处理中...";
      setMessageIndex(nextIndex);
      setVisibleChars(0);
      let currentLength = 0;

      typingTimer = window.setInterval(() => {
        currentLength += 1;
        setVisibleChars(Math.min(currentLength, message.length));
        if (currentLength >= message.length) {
          if (typingTimer !== null) {
            window.clearInterval(typingTimer);
          }
          holdTimer = window.setTimeout(() => {
            if (cancelled) {
              return;
            }
            nextIndex = (nextIndex + 1) % messagePool.length;
            typeCurrentMessage();
          }, 1500);
        }
      }, 30);
    };

    typeCurrentMessage();

    return () => {
      cancelled = true;
      if (typingTimer !== null) {
        window.clearInterval(typingTimer);
      }
      if (holdTimer !== null) {
        window.clearTimeout(holdTimer);
      }
    };
  }, [messagePool, step.status]);

  if (step.status === "completed") {
    return <p className="workflow-step-note">已完成 {formatDuration(step.durationMs)}</p>;
  }

  if (step.status === "error") {
    return <p className="workflow-step-error-copy">{step.errorMessage || "这一步没有顺利完成。"}</p>;
  }

  if (step.status !== "active") {
    return null;
  }

  const currentMessage = messagePool[messageIndex] || "正在处理中...";
  return (
    <p className="workflow-step-message">
      {currentMessage.slice(0, visibleChars)}
      <span className="workflow-caret" />
    </p>
  );
}

export function WorkflowStepper({
  title,
  caption,
  steps,
  onCancel,
  onRetry,
  cancelLabel = "取消生成",
}: {
  title: string;
  caption?: string;
  steps: WorkflowStepState[];
  onCancel?: () => void;
  onRetry?: () => void;
  cancelLabel?: string;
}) {
  const completedCount = steps.filter((item) => item.status === "completed").length;
  const errorStep = steps.find((item) => item.status === "error") || null;

  return (
    <section className="workflow-shell">
      <div className="workflow-head">
        <div>
          <p className="section-kicker">Live Workflow</p>
          <h3>{title}</h3>
          {caption ? <p className="workflow-caption">{caption}</p> : null}
        </div>
        <div className="workflow-head-actions">
          <span className="workflow-progress-chip">
            {completedCount}/{steps.length} 步骤
          </span>
          {onCancel ? (
            <button className="workflow-cancel-button" onClick={onCancel} type="button">
              {cancelLabel}
            </button>
          ) : null}
        </div>
      </div>

      <div className="workflow-stepper">
        {steps.map((step, index) => (
          <article
            key={step.key}
            className={`workflow-step workflow-step-${step.status} ${
              index < steps.length - 1 ? "workflow-step-with-line" : ""
            }`}
          >
            <div className="workflow-step-marker">
              <span className="workflow-step-dot">{step.status === "completed" ? "✓" : step.status === "error" ? "×" : ""}</span>
            </div>
            <div className="workflow-step-body">
              <div className="workflow-step-title-row">
                <h4>{step.title}</h4>
                {step.durationMs && step.status === "completed" ? (
                  <span className="workflow-step-duration">{formatDuration(step.durationMs)}</span>
                ) : null}
              </div>
              <StepMessage step={step} />
              {step.status === "skipped" ? <p className="workflow-step-note">已跳过</p> : null}
            </div>
          </article>
        ))}
      </div>

      {errorStep ? (
        <article className="workflow-error-card">
          <h4>这次流程在“{errorStep.title}”停住了</h4>
          <p>{errorStep.errorMessage || "这一步没有顺利完成，请稍后重试。"}</p>
          {onRetry ? (
            <button className="secondary-button" onClick={onRetry} type="button">
              重新开始
            </button>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
