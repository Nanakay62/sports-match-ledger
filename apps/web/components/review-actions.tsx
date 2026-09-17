"use client";

import { useState } from "react";
import { CheckCircle2, AlertTriangle, FileEdit } from "lucide-react";
import { resolveAdminReviewItem } from "@/lib/api";

export function ReviewActionButtons({
  claimId,
  initialStatus,
}: {
  claimId: string;
  initialStatus: string;
}) {
  const [resolvedStatus, setResolvedStatus] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const handleAction = async (action: "confirm" | "dispute" | "correct") => {
    if (loadingAction || resolvedStatus) return;

    let defaultNote = "Verified by editorial review desk";
    if (action === "dispute") defaultNote = "Contradictory assertions and denials confirmed on record";
    if (action === "correct") defaultNote = "Reporting superseded after verification";

    const notes = prompt(`Editorial note for ${action.toUpperCase()}:`, defaultNote);
    if (notes === null) return;

    setLoadingAction(action);
    try {
      const res = await resolveAdminReviewItem(claimId, action, notes || defaultNote);
      if (res.status === "success") {
        setResolvedStatus(action);
      }
    } finally {
      setLoadingAction(null);
    }
  };

  if (resolvedStatus) {
    return (
      <div className="flex items-center gap-2">
        <span
          className={`rounded px-2.5 py-1 font-mono text-[11px] font-semibold uppercase tracking-wider ${
            resolvedStatus === "confirm"
              ? "bg-emerald-100 text-emerald-800"
              : resolvedStatus === "dispute"
              ? "bg-amber-100 text-amber-800"
              : "bg-rose-100 text-rose-800"
          }`}
        >
          Decision Logged: {resolvedStatus}
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2 font-mono text-[11.5px]">
      <span className="mr-1 text-ink-faint">One-click decision:</span>
      <button
        type="button"
        disabled={loadingAction !== null}
        onClick={() => handleAction("confirm")}
        className="inline-flex items-center gap-1 rounded border border-emerald-300 bg-emerald-50 px-2.5 py-1 font-medium text-emerald-800 transition-colors hover:bg-emerald-100 disabled:opacity-50"
        title="Confirm as verified fact"
      >
        <CheckCircle2 className="size-3" />
        {loadingAction === "confirm" ? "..." : "Confirm"}
      </button>

      <button
        type="button"
        disabled={loadingAction !== null}
        onClick={() => handleAction("dispute")}
        className="inline-flex items-center gap-1 rounded border border-amber-300 bg-amber-50 px-2.5 py-1 font-medium text-amber-900 transition-colors hover:bg-amber-100 disabled:opacity-50"
        title="Ratify Disputed status"
      >
        <AlertTriangle className="size-3" />
        {loadingAction === "dispute" ? "..." : "Dispute"}
      </button>

      <button
        type="button"
        disabled={loadingAction !== null}
        onClick={() => handleAction("correct")}
        className="inline-flex items-center gap-1 rounded border border-rose-300 bg-rose-50 px-2.5 py-1 font-medium text-rose-800 transition-colors hover:bg-rose-100 disabled:opacity-50"
        title="Supersede and mark as Corrected"
      >
        <FileEdit className="size-3" />
        {loadingAction === "correct" ? "..." : "Correct"}
      </button>
    </div>
  );
}