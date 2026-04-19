import React from "react";

/** Renders `**bold**` segments inside a string. */
function renderInline(text) {
  if (!text) return null;
  return text.split("**").map((part, j) =>
    j % 2 === 1 ? (
      <strong key={j} className="font-semibold text-slate-900">
        {part}
      </strong>
    ) : (
      <span key={j}>{part}</span>
    )
  );
}

/**
 * Turns assistant plain text into readable blocks: paragraphs, markdown-style
 * headings (##), bullets (- / * / •), numbered lists, blockquotes, rules.
 */
export default function FormattedAssistantReply({ content }) {
  if (content == null || !String(content).trim()) return null;

  const normalized = String(content).replace(/\r\n/g, "\n").replace(/\t/g, "  ");
  const rawLines = normalized.split("\n");

  const blocks = [];
  let paraLines = [];
  let listBuf = null; // { type: 'ul'|'ol', items: string[] }

  const flushPara = () => {
    if (paraLines.length) {
      blocks.push({ kind: "p", lines: [...paraLines] });
      paraLines = [];
    }
  };

  const flushList = () => {
    if (listBuf) {
      blocks.push({ kind: listBuf.type, items: [...listBuf.items] });
      listBuf = null;
    }
  };

  for (const line of rawLines) {
    const t = line.trim();
    const hr = /^([-*_])\1{2,}$/.test(t);
    if (hr) {
      flushList();
      flushPara();
      blocks.push({ kind: "hr" });
      continue;
    }

    if (!t) {
      flushList();
      flushPara();
      continue;
    }

    const quote = t.match(/^>\s+(.+)$/);
    if (quote) {
      flushList();
      flushPara();
      blocks.push({ kind: "quote", text: quote[1] });
      continue;
    }

    const h = t.match(/^#{1,3}\s+(.+)$/);
    if (h) {
      flushList();
      flushPara();
      const level = t.match(/^#+/)[0].length;
      blocks.push({ kind: "h", level: Math.min(level, 3), text: h[1] });
      continue;
    }

    const ul = t.match(/^[-*•]\s+(.+)$/);
    if (ul) {
      flushPara();
      if (!listBuf || listBuf.type !== "ul") {
        flushList();
        listBuf = { type: "ul", items: [] };
      }
      listBuf.items.push(ul[1]);
      continue;
    }

    const ol = t.match(/^(\d+)[.)]\s+(.+)$/);
    if (ol) {
      flushPara();
      if (!listBuf || listBuf.type !== "ol") {
        flushList();
        listBuf = { type: "ol", items: [] };
      }
      listBuf.items.push(ol[2]);
      continue;
    }

    flushList();
    paraLines.push(t);
  }
  flushList();
  flushPara();

  return (
    <div className="assistant-rich space-y-3 text-[15px] leading-relaxed text-slate-700">
      {blocks.map((b, i) => {
        if (b.kind === "hr") {
          return <hr key={i} className="my-2 border-0 border-t border-slate-200" />;
        }
        if (b.kind === "quote") {
          return (
            <blockquote
              key={i}
              className="border-l-4 border-tartan/40 bg-slate-50/90 py-2 pl-3 pr-2 text-slate-600 italic"
            >
              {renderInline(b.text)}
            </blockquote>
          );
        }
        if (b.kind === "h") {
          const isBig = b.level <= 2;
          return (
            <h3
              key={i}
              className={
                isBig
                  ? "text-base font-semibold tracking-tight text-tartan-ink"
                  : "text-xs font-semibold uppercase tracking-wide text-slate-600"
              }
            >
              {renderInline(b.text)}
            </h3>
          );
        }
        if (b.kind === "p") {
          return (
            <p key={i} className="whitespace-pre-wrap first:mt-0">
              {b.lines.map((ln, li) => (
                <React.Fragment key={li}>
                  {li > 0 ? <br /> : null}
                  {renderInline(ln)}
                </React.Fragment>
              ))}
            </p>
          );
        }
        if (b.kind === "ul") {
          return (
            <ul
              key={i}
              className="list-outside list-disc space-y-1.5 pl-5 text-slate-700 marker:text-tartan"
            >
              {b.items.map((item, ii) => (
                <li key={ii} className="pl-0.5">
                  {renderInline(item)}
                </li>
              ))}
            </ul>
          );
        }
        if (b.kind === "ol") {
          return (
            <ol
              key={i}
              className="list-outside list-decimal space-y-1.5 pl-5 text-slate-700 marker:font-medium marker:text-tartan"
            >
              {b.items.map((item, ii) => (
                <li key={ii} className="pl-0.5">
                  {renderInline(item)}
                </li>
              ))}
            </ol>
          );
        }
        return null;
      })}
    </div>
  );
}
