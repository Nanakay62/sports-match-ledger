import Link from "next/link";
import {
  AlertOctagon,
  Database,
  DollarSign,
  ExternalLink,
  Network,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Users,
} from "lucide-react";

const ADMIN_LINKS = [
  { href: "/admin", label: "Overview", icon: Sliders },
  { href: "/admin/clusters", label: "Cluster Inspection", icon: Network },
  { href: "/admin/sources", label: "Source Registry", icon: Database },
  { href: "/admin/review", label: "Review Queue", icon: ShieldCheck },
  { href: "/admin/entities", label: "Entity Corrections", icon: Users },
  { href: "/admin/cost", label: "Cost Architecture", icon: DollarSign },
  { href: "/admin/quarantine", label: "Quarantine Pool", icon: ShieldAlert },
  { href: "/admin/dead-letters", label: "Dead-Letter Queue", icon: AlertOctagon },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const publicAppUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

  return (
    <div className="min-h-screen bg-paper pb-24">
      {/* Admin Subheader Bar */}
      <div className="border-b border-ink bg-stone-100 py-3">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 md:px-6">
          <div className="flex items-center gap-3">
            <span className="rounded bg-ink px-2 py-0.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-paper">
              Editorial Subdomain
            </span>
            <span className="hidden font-mono text-[11px] text-ink-faint sm:inline">
              Audit level: Staff Editor · Append-only ledger
            </span>
          </div>
          <a
            href={publicAppUrl}
            className="inline-flex items-center gap-1.5 font-mono text-[11px] text-ink-soft hover:text-ink"
          >
            <span>Public Reader Platform</span>
            <ExternalLink className="size-3" />
          </a>
        </div>
      </div>

      {/* Admin Navigation Bar */}
      <div className="border-b border-rule bg-paper">
        <div className="mx-auto flex max-w-6xl overflow-x-auto px-4 md:px-6">
          <nav className="flex space-x-1 py-2 font-mono text-[12px]" aria-label="Admin Navigation">
            {ADMIN_LINKS.map((link) => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="flex items-center gap-2 rounded px-3 py-1.5 text-ink-soft transition-colors hover:bg-rule/40 hover:text-ink"
                >
                  <Icon className="size-3.5" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Admin Content */}
      <div className="mx-auto max-w-6xl px-4 pt-8 md:px-6">{children}</div>
    </div>
  );
}
