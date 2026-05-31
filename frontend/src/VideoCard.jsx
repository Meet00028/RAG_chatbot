import React from "react";

function badgeColor(rate) {
  if (rate > 5) return "#16a34a"; // green
  if (rate >= 2) return "#ca8a04"; // yellow
  return "#dc2626"; // red
}

export default function VideoCard({ video }) {
  if (!video) return null;

  const rate = Number(video.engagement_rate || 0);
  const color = badgeColor(rate);

  const statStyle = { display: "flex", gap: 10, flexWrap: "wrap", color: "#111827" };
  const pillStyle = {
    display: "inline-block",
    padding: "4px 8px",
    borderRadius: 999,
    background: "#f3f4f6",
    border: "1px solid #e5e7eb",
    fontSize: 12,
    marginRight: 6,
    marginTop: 6
  };

  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 12,
        padding: 14,
        background: "#ffffff",
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)"
      }}
    >
      <div style={{ display: "flex", gap: 12 }}>
        <div style={{ flex: "0 0 140px" }}>
          {video.thumbnail ? (
            <img
              src={video.thumbnail}
              alt={video.title}
              style={{
                width: 140,
                height: 78,
                objectFit: "cover",
                borderRadius: 10,
                border: "1px solid #e5e7eb"
              }}
            />
          ) : (
            <div
              style={{
                width: 140,
                height: 78,
                borderRadius: 10,
                border: "1px dashed #d1d5db",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#6b7280",
                fontSize: 12
              }}
            >
              No thumbnail
            </div>
          )}
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
            <h3 style={{ margin: 0, fontSize: 16, color: "#111827" }}>{video.title}</h3>
            <span style={{ color: "#6b7280", fontSize: 13 }}>{video.creator}</span>
          </div>

          <div style={{ marginTop: 10, ...statStyle }}>
            <span>
              <strong>Views:</strong> {Number(video.views || 0).toLocaleString()}
            </span>
            <span>
              <strong>Likes:</strong> {Number(video.likes || 0).toLocaleString()}
            </span>
            <span>
              <strong>Comments:</strong> {Number(video.comments || 0).toLocaleString()}
            </span>
            <span
              style={{
                marginLeft: "auto",
                padding: "4px 10px",
                borderRadius: 999,
                background: color,
                color: "white",
                fontWeight: 700,
                fontSize: 12
              }}
              title="(likes + comments) / views * 100"
            >
              Engagement: {rate.toFixed(4)}%
            </span>
          </div>

          <div style={{ marginTop: 10, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <span style={{ color: "#374151", fontSize: 13 }}>
              <strong>Duration:</strong> {video.duration ?? "N/A"}s
            </span>
            <span style={{ color: "#374151", fontSize: 13 }}>
              <strong>Upload Date:</strong> {video.upload_date ?? "N/A"}
            </span>
            <span style={{ color: "#374151", fontSize: 13 }}>
              <strong>Follower Count:</strong>{" "}
              {video.follower_count == null ? "N/A" : Number(video.follower_count).toLocaleString()}
            </span>
          </div>

          {Array.isArray(video.hashtags) && video.hashtags.length > 0 ? (
            <div style={{ marginTop: 10 }}>
              {video.hashtags.map((t) => (
                <span key={t} style={pillStyle}>
                  #{t.replace(/^#/, "")}
                </span>
              ))}
            </div>
          ) : (
            <div style={{ marginTop: 10, color: "#6b7280", fontSize: 12 }}>No hashtags found</div>
          )}
        </div>
      </div>
    </div>
  );
}

// Commit message suggestion:
//   "Add VideoCard component with engagement badge and hashtag pills"
