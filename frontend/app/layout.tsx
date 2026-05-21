import type { Metadata } from "next";
import localFont from "next/font/local";

import "./globals.css";

const headingFont = localFont({
  src: "./fonts/SpaceGrotesk-Variable.woff2",
  variable: "--font-heading",
  display: "swap",
});

const bodyFont = localFont({
  src: "./fonts/IBMPlexSans-Variable.woff2",
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "内容中台",
  description: "脚本生成、脚本检查、热点探索与知识库管理后台。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={`${headingFont.variable} ${bodyFont.variable}`}>{children}</body>
    </html>
  );
}
