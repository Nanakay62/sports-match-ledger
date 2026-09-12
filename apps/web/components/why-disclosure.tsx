"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { ReasoningBullet } from "@/lib/evidence";
import { ReasonBullet } from "./why-bullet";

export function WhyDisclosure({
  reasoning,
  defaultOpen = false,
}: {
  reasoning: ReasoningBullet[];
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-ledger transition-colors hover:text-ledger-deep"
      >
        Why this status?
        <ChevronDown
          className={`size-3.5 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          aria-hidden
        />
      </button>
      <div
        className={`grid transition-[grid-template-rows] duration-300 ease-out ${
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="overflow-hidden">
          <ul className="space-y-2.5 pt-3">
            {reasoning.map((r, i) => (
              <ReasonBullet key={i} bullet={r} />
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}