const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function ingestVideos(urlA, urlB) {
  const res = await fetch(`${BACKEND_URL}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url_a: urlA, url_b: urlB })
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Ingest failed (${res.status})`);
  }

  return res.json();
}

export function streamQuery(sessionId, query, onToken, onDone) {
  const params = new URLSearchParams({ session_id: sessionId, query });
  const es = new EventSource(`${BACKEND_URL}/stream?${params.toString()}`);

  es.onmessage = (evt) => {
    const data = evt.data;
    if (data === "[DONE]") {
      es.close();
      onDone?.();
      return;
    }

    if (data?.startsWith?.("[ERROR]")) {
      onToken?.(`\n\n${data}`);
      es.close();
      onDone?.();
      return;
    }

    onToken?.(data);
  };

  es.onerror = () => {
    // SSE failures can be caused by backend restarts, network blips, or proxies.
    // We close aggressively to prevent runaway reconnection loops in the browser.
    es.close();
    onToken?.("\n\n[ERROR] Connection lost. Please retry.");
    onDone?.();
  };

  return () => es.close();
}

// Commit message suggestion:
//   "Add frontend API client for ingestion and SSE chat streaming"
