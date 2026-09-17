"use client";

import { useState } from "react";
import { AlertOctagon, Pause, Play } from "lucide-react";
import { blockAdminSource, pauseAdminSource, resumeAdminSource } from "@/lib/api";

export function SourceActions({
  registryId,
  initialStatus,
}: {
  registryId: string;
  initialStatus: string;
}) {
  const [status, setStatus] = useState(initialStatus);
  const [loading, setLoading] = useState(false);

  const handlePause = async () => {
    const reason = prompt("Enter pause reason (e.g., source downtime, rate limiting):") || "Admin operator paused ingestion";
    setLoading(true);
    try {
      const res = await pauseAdminSource(registryId, reason);
      if (res.status === "paused") {
        setStatus("paused");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    setLoading(true);
    try {
      const res = await resumeAdminSource(registryId);
      if (res.status === "resumed") {
        setStatus("approved");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBlock = async () => {
    const reason = prompt("Enter block reason (e.g., terms of service violation, copyright notice):");
    if (!reason) return;
    setLoading(true);
    try {
      const res = await blockAdminSource(registryId, reason);
      if (res.status === "blocked") {
        setStatus("blocked");
      }
    } finally {
      setLoading(false);
    }
  };

  if (status === "blocked") {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-rose-100 px-2 py-0.5 font-mono text-[10.5px] font-semibold text-rose-800">
        <AlertOctagon className="size-3" /> Blocked
      </span>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      {status === "approved" && (
        <button
          onClick={handlePause}
          disabled={loading}
          className="inline-flex items-center gap-1 rounded border border-amber-300 bg-amber-50 px-2 py-0.5 font-mono text-[11px] font-medium text-amber-900 transition-colors hover:bg-amber-100 disabled:opacity-50"
          title="Pause polling"
        >
          <Pause className="size-3" />
          {loading ? "..." : "Pause"}
        </button>
      )}

      {status === "paused" && (
        <button
          onClick={handleResume}
          disabled={loading}
          className="inline-flex items-center gap-1 rounded border border-emerald-300 bg-emerald-50 px-2 py-0.5 font-mono text-[11px] font-medium text-emerald-900 transition-colors hover:bg-emerald-100 disabled:opacity-50"
          title="Resume ingestion"
        >
          <Play className="size-3" />
          {loading ? "..." : "Resume"}
        </button>
      )}

      <button
        onClick={handleBlock}
        disabled={loading}
        className="inline-flex items-center gap-1 rounded border border-rose-200 bg-paper px-2 py-0.5 font-mono text-[11px] font-medium text-rose-700 transition-colors hover:bg-rose-50 disabled:opacity-50"
        title="Block source permanently or under legal review"
      >
        <AlertOctagon className="size-3" />
        Block
      </button>
    </div>
  );
}