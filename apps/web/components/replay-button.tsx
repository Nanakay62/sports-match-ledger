"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { replayDeadLetterJob } from "@/lib/api";

export function ReplayButton({ deadLetterId, isReplayed }: { deadLetterId: string; isReplayed: boolean }) {
  const [loading, setLoading] = useState(false);
  const [replayed, setReplayed] = useState(isReplayed);

  const handleReplay = async () => {
    if (loading || replayed) return;
    setLoading(true);
    try {
      const res = await replayDeadLetterJob(deadLetterId);
      if (res.status === "replayed") {
        setReplayed(true);
      }
    } finally {
      setLoading(false);
    }
  };

  if (replayed) {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-emerald-100 px-2 py-1 font-mono text-[11px] font-semibold text-emerald-800">
        Replayed
      </span>
    );
  }

  return (
    <button
      onClick={handleReplay}
      disabled={loading}
      className="inline-flex items-center gap-1.5 rounded border border-ink bg-ink px-2.5 py-1 font-mono text-[11px] font-semibold text-paper transition-opacity hover:opacity-90 disabled:opacity-50"
    >
      <RefreshCw className={`size-3 ${loading ? "animate-spin" : ""}`} />
      {loading ? "Re-enqueuing..." : "Replay Job"}
    </button>
  );
}
