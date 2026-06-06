import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

import { ingestVideos } from "./api";
import VideoCard from "./VideoCard";
import ChatPanel from "./ChatPanel";

function App() {
  const [urlA, setUrlA] = useState("");
  const [urlB, setUrlB] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [videoMetadata, setVideoMetadata] = useState(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [error, setError] = useState(null);

  const isReady = Boolean(sessionId && videoMetadata);

  const styles = useMemo(
    () => ({
      page: {
        minHeight: "100vh",
        background: "#0b1220",
        padding: 20
      },
      container: {
        maxWidth: 1100,
        margin: "0 auto"
      },
      header: {
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between",
        color: "white",
        marginBottom: 16
      },
      title: { margin: 0, fontSize: 20 },
      subtitle: { margin: 0, color: "#cbd5e1", fontSize: 13 },
      panel: {
        background: "#0f172a",
        border: "1px solid rgba(148,163,184,0.18)",
        borderRadius: 14,
        padding: 16,
        marginBottom: 16
      },
      inputs: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 },
      label: { color: "#cbd5e1", fontSize: 12, marginBottom: 6, display: "flex", flexDirection: "column", gap: 6 },
      input: {
        width: "100%",
        padding: "10px 12px",
        borderRadius: 10,
        border: "1px solid rgba(148,163,184,0.3)",
        background: "#0b1220",
        color: "white",
        outline: "none"
      },
      actions: { marginTop: 12, display: "flex", gap: 10, alignItems: "center" },
      button: {
        padding: "10px 12px",
        borderRadius: 10,
        border: "1px solid #22c55e",
        background: isIngesting ? "#14532d" : "#16a34a",
        color: "white",
        fontWeight: 700,
        cursor: isIngesting ? "not-allowed" : "pointer"
      },
      spinner: { color: "#cbd5e1", fontSize: 13 },
      error: {
        marginTop: 10,
        background: "rgba(239, 68, 68, 0.12)",
        border: "1px solid rgba(239, 68, 68, 0.3)",
        color: "#fecaca",
        padding: "10px 12px",
        borderRadius: 10,
        fontSize: 13
      },
      cardsRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }
    }),
    [isIngesting]
  );

  async function handleAnalyze() {
    setError(null);
    setIsIngesting(true);
    setSessionId(null);
    setVideoMetadata(null);

    try {
      const res = await ingestVideos(urlA.trim(), urlB.trim());
      setSessionId(res.session_id);
      setVideoMetadata({ video_a: res.video_a, video_b: res.video_b });
    } catch (e) {
      setError(e?.message || "Failed to ingest videos.");
    } finally {
      setIsIngesting(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>RAG Video Comparator</h1>
            <p style={styles.subtitle}>
              Ingest two videos, then ask comparative questions with transcript citations.
            </p>
          </div>
          <div style={{ color: "#94a3b8", fontSize: 12 }}>
            {isReady ? `Session: ${sessionId}` : "Not ingested"}
          </div>
        </div>

        <div style={styles.panel}>
          <div style={styles.inputs}>
            <div>
              <label style={styles.label}>
                Video A URL (YouTube)
                <input
                  style={styles.input}
                  value={urlA}
                  onChange={(e) => setUrlA(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  disabled={isIngesting}
                />
              </label>
            </div>
            <div>
              <label style={styles.label}>
                Video B URL (Instagram Reel)
                <input
                  style={styles.input}
                  value={urlB}
                  onChange={(e) => setUrlB(e.target.value)}
                  placeholder="https://www.instagram.com/reel/..."
                  disabled={isIngesting}
                />
              </label>
            </div>
          </div>

          <div style={styles.actions}>
            <button style={styles.button} onClick={handleAnalyze} disabled={isIngesting}>
              Analyze Videos
            </button>
            {isIngesting ? <span style={styles.spinner}>Ingesting videos...</span> : null}
          </div>

          {error ? <div style={styles.error}>{error}</div> : null}
        </div>

        {isReady ? (
          <>
            <div style={styles.cardsRow}>
              <VideoCard video={videoMetadata.video_a} />
              <VideoCard video={videoMetadata.video_b} />
            </div>
            <ChatPanel sessionId={sessionId} />
          </>
        ) : null}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);

// Commit message suggestion:
//   "Add main app layout: ingestion form, two VideoCards, and streaming ChatPanel"
