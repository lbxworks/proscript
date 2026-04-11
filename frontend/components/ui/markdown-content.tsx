"use client";

import rehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
  emptyText?: string;
};

function normalizeMarkdown(content: string): string {
  return content.replace(/\r\n/g, "\n").trim();
}

const markdownSchema = {
  ...defaultSchema,
  tagNames: [...(defaultSchema.tagNames || []), "br", "b", "i", "u", "span"],
};

export function MarkdownContent({
  content,
  emptyText = "暂无内容。",
}: MarkdownContentProps) {
  const normalizedContent = normalizeMarkdown(content);

  if (!normalizedContent) {
    return <p className="muted-copy markdown-empty">{emptyText}</p>;
  }

  return (
    <div className="markdown-renderer">
      <ReactMarkdown
        components={{
          a: ({ children, href }) => (
            <a className="markdown-link" href={href} rel="noreferrer" target="_blank">
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="markdown-table-wrap">
              <table>{children}</table>
            </div>
          ),
        }}
        rehypePlugins={[rehypeRaw, [rehypeSanitize, markdownSchema]]}
        remarkPlugins={[remarkGfm, remarkBreaks]}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
}
