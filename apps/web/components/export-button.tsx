"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileDown, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEntitlements } from "@/lib/entitlements";
import { trackPaywallEvent } from "@/lib/paywall-tracking";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/** Real CSV export for Pro, a real (tracked) paywall for Free — no more "links to /pro either way." */
export function ExportButton({
  eventId,
  label = "Export CSV",
  querySuffix = "",
}: {
  eventId: string;
  label?: string;
  querySuffix?: string;
}) {
  const { isPro, email, loading } = useEntitlements();
  const [downloading, setDownloading] = useState(false);
  const unlocked = !loading && isPro && email;

  useEffect(() => {
    if (!loading && !unlocked) {
      trackPaywallEvent("export", "shown", { email, context: eventId });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, unlocked]);

  if (unlocked) {
    return (
      <Button
        variant="outline"
        size="sm"
        className="border-rule-strong text-ink-soft hover:text-ink"
        disabled={downloading}
        onClick={async () => {
          setDownloading(true);
          try {
            const resp = await fetch(
              `${API_BASE_URL}/claims/export?event_id=${encodeURIComponent(eventId)}&email=${encodeURIComponent(email!)}&format=csv`,
            );
            if (!resp.ok) throw new Error(`export failed: ${resp.status}`);
            const blob = await resp.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `claims_${eventId}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
          } catch {
            // Honest failure state: nothing downloads rather than a fake success.
          } finally {
            setDownloading(false);
          }
        }}
      >
        <FileDown className="size-3.5" aria-hidden /> {downloading ? "Preparing…" : label}
      </Button>
    );
  }

  return (
    <Button
      asChild
      variant="outline"
      size="sm"
      className="border-rule-strong text-ink-soft hover:text-ink"
      title="Export is a Pro feature"
      onClick={() => trackPaywallEvent("export", "clicked", { email, context: eventId })}
    >
      <Link href={`/pro${querySuffix}`}>
        <FileDown className="size-3.5" aria-hidden /> {label}
        <Lock className="size-3 text-ink-faint" aria-hidden />
      </Link>
    </Button>
  );
}
