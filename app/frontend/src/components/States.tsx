import React from "react";
import type { ApiResult } from "../lib/useApi";

export function Skeleton({ h = 180 }: { h?: number }) {
  return <div className="skeleton-shimmer" style={{ height: h, borderRadius: 12 }} />;
}

export function EmptyState({ title, body, action }: { title: string; body?: string; action?: React.ReactNode }) {
  return (
    <div style={{ textAlign: "center", padding: "38px 20px", color: "#8a9097" }}>
      <div style={{ fontSize: 26, marginBottom: 8 }}>◍</div>
      <div style={{ fontWeight: 800, color: "#394049", fontSize: 14 }}>{title}</div>
      {body && <p style={{ fontSize: 12, maxWidth: 440, margin: "8px auto 0", lineHeight: 1.6 }}>{body}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}

export function ErrorState({ error, retry }: { error: string | null; retry?: () => void }) {
  return (
    <div className="demo-banner" style={{ background: "#fdeeea", borderColor: "#f3cfc8", color: "#b2453f" }}>
      <span style={{ fontSize: 15 }}>⚠</span>
      <div>
        <b>Could not reach the backend.</b> {error}
        <div className="tiny" style={{ marginTop: 4 }}>
          Ensure the API is running (uvicorn on port 8000).{" "}
          {retry && <a onClick={retry} style={{ color: "#6670d2", fontWeight: 700, cursor: "pointer" }}>Retry</a>}
        </div>
      </div>
    </div>
  );
}

/** Render children only when data is ready; otherwise show skeleton/empty/error. */
export function Gate<T>({ r, children, skeletonH, empty }: {
  r: ApiResult<T>; children: (data: T) => React.ReactNode; skeletonH?: number; empty?: React.ReactNode;
}) {
  if (r.state === "loading") return <Skeleton h={skeletonH} />;
  if (r.state === "error") return <ErrorState error={r.error} retry={r.refetch} />;
  if (r.state === "empty") return <>{empty ?? <EmptyState title="No data yet" />}</>;
  return <>{r.data !== null && children(r.data)}</>;
}
