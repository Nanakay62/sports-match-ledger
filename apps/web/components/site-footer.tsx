"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function SiteFooter() {
  const pathname = usePathname();

  if (pathname.startsWith("/admin")) {
    return (
      <footer className="border-t border-ink bg-stone-100 py-6 text-ink-faint font-mono text-[11px]">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 md:px-6">
          <span>Matchday Ledger Editorial Control Plane · Confidential & Internal Only</span>
          <span>Append-Only Ledger · Strict Data Integrity</span>
        </div>
      </footer>
    );
  }

  return (
    <footer className="border-t-2 border-ink">
      <div className="mx-auto max-w-6xl px-4 py-10 md:px-6">
        <div className="grid gap-8 md:grid-cols-[1fr_auto] md:items-start">
          <div className="max-w-xl">
            <div className="font-display text-xl font-semibold">Matchday Ledger</div>
            <p className="mt-2 text-[13px] leading-relaxed text-ink-soft">
              An accountability layer over transfer reporting. Every claim is timestamped and
              attributed; when the record settles, it is marked correct or incorrect. Current
              statuses are free, always; Pro deepens the archive.
            </p>
            <p className="mt-3 text-[11.5px] text-ink-faint">
              Demo build: every outlet, reporter, player, deal and figure on this site is a fictional
              fixture. No real reporting is implied.
            </p>
          </div>
          <nav className="flex flex-col gap-2 font-mono text-[11.5px] uppercase tracking-[0.1em] text-ink-soft" aria-label="Footer">
            <Link className="hover:text-ink" href="/">The Ledger</Link>
            <Link className="hover:text-ink" href="/reliability">Reliability desk</Link>
            <Link className="hover:text-ink" href="/methodology">Methodology</Link>
            <Link className="hover:text-ink" href="/corrections">Corrections</Link>
            <Link className="hover:text-ink" href="/pro">Upgrade</Link>
            <Link className="hover:text-ink text-stone-950 font-semibold" href="/admin">Editorial Desk (Admin)</Link>
          </nav>
        </div>
        <div className="mt-8 flex flex-wrap justify-between gap-2 border-t border-rule pt-3 font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
          <span>© {new Date().getFullYear()} Matchday Ledger</span>
          <span>Corrections are permanent · Scores publish at 10+ resolved claims</span>
        </div>
      </div>
    </footer>
  );
}