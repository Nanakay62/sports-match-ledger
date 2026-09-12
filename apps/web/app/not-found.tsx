import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-24 text-center">
      <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-ink-faint">Entry not found</p>
      <h1 className="mt-3 font-display text-4xl font-medium tracking-tight">No such entry in the ledger.</h1>
      <p className="mx-auto mt-3 max-w-md text-[14px] leading-relaxed text-ink-soft">
        The page you asked for isn't on record. Entries are never deleted: check the address, or go
        back to the feed.
      </p>
      <Link
        href="/"
        className="mt-6 inline-block border border-ink px-4 py-2 text-[13px] font-medium transition-colors hover:bg-ink hover:text-paper"
      >
        Back to the ledger
      </Link>
    </main>
  );
}