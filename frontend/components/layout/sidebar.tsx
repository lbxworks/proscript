"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/talents", label: "达人管理", badge: "Lark-ready" },
  { href: "/scripts/generate", label: "脚本生成", badge: "Live" },
  { href: "/scripts/review", label: "脚本检查", badge: "Risk" },
  { href: "/trends", label: "热点探索", badge: "Tavily" },
  { href: "/library", label: "图书馆", badge: "KB" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar-shell">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">PG</div>
        <div>
          <p className="sidebar-eyebrow">Grad Project</p>
          <h1>内容中台</h1>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} className={`sidebar-link${active ? " is-active" : ""}`}>
              <span>{item.label}</span>
              <span className="sidebar-badge">{item.badge}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-voice-card">
        <p className="sidebar-voice-title">语音入口预留</p>
        <p className="sidebar-voice-copy">后续可在这里挂载口述脚本和语音指令入口。</p>
      </div>
    </aside>
  );
}
