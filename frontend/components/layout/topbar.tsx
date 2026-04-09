"use client";

import { usePathname } from "next/navigation";

import { API_BASE_URL } from "@/lib/constants";

const titleMap: Record<string, string> = {
  "/talents": "达人管理",
  "/scripts/generate": "脚本生成",
  "/scripts/review": "脚本检查",
  "/trends": "热点探索",
  "/library": "图书馆",
};

export function Topbar() {
  const pathname = usePathname();
  const title = titleMap[pathname] || "内容中台";

  return (
    <header className="topbar-shell">
      <div>
        <p className="topbar-eyebrow">Control Room</p>
        <h2>{title}</h2>
      </div>
      <div className="topbar-meta">
        <div className="topbar-chip">
          <span className="status-dot" />
          <span>FastAPI</span>
        </div>
        <div className="topbar-chip topbar-chip-muted">{API_BASE_URL}</div>
      </div>
    </header>
  );
}
