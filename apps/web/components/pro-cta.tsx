"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function ProCta({ label }: { label: string }) {
  const [clicked, setClicked] = useState(false);
  return (
    <div>
      <Button
        onClick={() => setClicked(true)}
        className="w-full bg-ink text-paper hover:bg-ledger-deep"
      >
        {label}
      </Button>
      {clicked && (
        <p className="mt-2 border border-dashed border-rule-strong bg-paper-deep/60 px-3 py-2 text-[12px] leading-relaxed text-ink-soft">
          Demo build: no billing is wired up. In production this opens checkout; nothing about the
          free ledger would change.
        </p>
      )}
    </div>
  );
}