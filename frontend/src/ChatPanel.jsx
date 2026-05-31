import React, { useEffect, useMemo, useRef, useState } from "react";
import DOMPurify from "dompurify";
import { marked } from "marked";

import { streamQuery } from "./api";

function sanitizeAndRenderMarkdown(markdown) {
  // We render markdown as HTML for better readability, but sanitize aggressively
  // because LLM output must never be treated as trusted input in production.
  const withCitations = (markdown || "").replace(
    /\[Video (A|B) \| Chunk (\d+)\]/g,
    (m) => `<span class="citation-tag">${m}</span>`
  );

  const html = marked.parse(withCitations, { breaks: true, gfm: true });
  return DOMPurify.sanitize(html);
}

export default function ChatPanel({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const endRef = useRef(null);

  const styles = useMemo(
    () => ({
      wrapper: {
        border: "1px solid #e5e7eb",
        borderRadius: 12,
        background: "#ffffff",
        padding: 14
      },
      history: {
        height: 360,
        overflowY: "auto",
        padding: 10,
        background: "#f9fafb",
        borderRadius: 10,
        border: "1px solid #e5e7eb"
      },
      row: { display: "flex", marginBottom: 10 },
      userBubble: {
        marginLeft: "auto",
        maxWidth: "78%",
        background: "#111827",
        color: "white",
        padding: "10px 12px",
        borderRadius: 12,
        whiteSpace: "pre-wrap"
      },
      botBubble: {
        marginRight: "auto",
        maxWidth: "78%",
        background: "white",
        color: "#111827",
        padding: "10px 12px",
        borderRadius: 12,
        border: "1px solid #e5e7eb"
      },
      inputRow: { display: "flex", gap: 10, marginTop: 12 },
      input: {
        flex: 1,
        padding: "10px 12px",
        borderRadius: 10,
        border: "1px solid #d1d5db",
        outline: "none"
      },
      button: {
        padding: "10px 12px",
        borderRadius: 10,
        border: "1px solid #111827",
        background: isStreaming ? "#6b7280" : "#111827",
        color: "white",
        cursor: isStreaming ? "not-allowed" : "pointer"
      },
      hint: { marginTop: 8, color: "#6b7280", fontSize: 12 }
    }),
    [isStreaming]
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  async function handleSend() {
    const q = inputValue.trim();
    if (!q || isStreaming) return;

    setInputValue("");
    setIsStreaming(true);

    setMessages((prev) => [...prev, { role: "user", content: q }, { role: "assistant", content: "" }]);

    let closed = false;
    const close = streamQuery(
      sessionId,
      q,
      (token) => {
        if (closed) return;
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (!last || last.role !== "assistant") {
            next.push({ role: "assistant", content: token });
            return next;
          }
          last.content += token;
          return next;
        });
      },
      () => {
        closed = true;
        setIsStreaming(false);
      }
    );

    // If the user navigates away mid-stream, close the EventSource.
    return () => close?.();
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div style={styles.wrapper}>
      <style>{`
        .citation-tag {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 999px;
          border: 1px solid #c7d2fe;
          background: #eef2ff;
          color: #3730a3;
          font-size: 12px;
          font-weight: 600;
          margin: 0 2px;
          white-space: nowrap;
        }
        .chat-md p { margin: 0 0 10px 0; }
        .chat-md ul { margin: 0 0 10px 18px; }
        .chat-md code {
          background: #f3f4f6;
          padding: 1px 4px;
          border-radius: 6px;
          border: 1px solid #e5e7eb;
        }
      `}</style>

      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <h3 style={{ margin: 0, color: "#111827" }}>Chat</h3>
        <span style={{ color: "#6b7280", fontSize: 12 }}>
          Streaming: {isStreaming ? "on" : "off"}
        </span>
      </div>

      <div style={{ marginTop: 12, ...styles.history }}>
        {messages.map((m, idx) => (
          <div key={idx} style={styles.row}>
            {m.role === "user" ? (
              <div style={styles.userBubble}>{m.content}</div>
            ) : (
              <div style={styles.botBubble}>
                <div
                  className="chat-md"
                  dangerouslySetInnerHTML={{ __html: sanitizeAndRenderMarkdown(m.content) }}
                />
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a comparative question (e.g., 'Which video has a stronger hook and why?')"
          disabled={isStreaming}
        />
        <button style={styles.button} onClick={handleSend} disabled={isStreaming}>
          Send
        </button>
      </div>

      <div style={styles.hint}>
        Tip: Ask about hooks (early chunks), content structure, CTA style, or why engagement differs.
      </div>
    </div>
  );
}

// Commit message suggestion:
//   "Add ChatPanel with SSE streaming, markdown rendering, and citation highlighting"
