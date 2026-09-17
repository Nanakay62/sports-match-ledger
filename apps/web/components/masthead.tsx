"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LanguageSelector } from "./language-selector";
import { getDictionary } from "@/lib/i18n";

function MastheadContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const lang = searchParams?.get("lang") || "en";
  const t = getDictionary(lang);

  // If user is inside the admin desk, suppress the consumer reader masthead
  if (pathname.startsWith("/admin")) {
    return null;
  }

  const localeMap: Record<string, string> = {
    en: "en-GB",
    it: "it-IT",
    es: "es-ES",
    de: "de-DE",
    fr: "fr-FR",
  };
  const activeLocale = localeMap[lang] || "en-GB";

  const today = new Date().toLocaleDateString(activeLocale, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";

  const links = [
    { href: `/${querySuffix}`, label: t.navLedger, activeMatch: "/" },
    { href: `/reliability${querySuffix}`, label: t.navReliability, activeMatch: "/reliability" },
    { href: `/corrections${querySuffix}`, label: t.navCorrections, activeMatch: "/corrections" },
  ];

  return (
    <header className="border-b border-ink bg-paper">
      <div className="mx-auto max-w-6xl px-4 md:px-6">
        <div className="flex items-center justify-between border-b border-rule py-2 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint">
          <span>{t.subHeaderAudit}</span>
          <div className="flex items-center gap-3">
            <LanguageSelector />
            <span aria-hidden className="hidden sm:inline">·</span>
            <span suppressHydrationWarning>{today}</span>
          </div>
        </div>
        <div className="py-7 text-center">
          <Link href={`/${querySuffix}`} className="inline-block">
            <span className="block font-display text-[2.5rem] font-semibold leading-none tracking-tight md:text-5xl">
              {t.siteTitle}
            </span>
            <span className="mt-2 block font-display text-[13px] italic text-ink-faint">
              {t.siteTagline}
            </span>
          </Link>
        </div>
      </div>
      <nav className="border-t border-ink" aria-label="Primary">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-2 md:px-6">
          <div className="flex items-center gap-5 text-[13px]">
            {links.map((l) => (
              <Link
                key={l.activeMatch}
                href={l.href}
                className={`py-1 transition-colors hover:text-ink ${
                  pathname === l.activeMatch
                    ? "font-semibold text-ink underline decoration-2 underline-offset-[6px]"
                    : "text-ink-soft"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Button asChild size="sm" className="bg-ink font-medium text-paper hover:bg-ledger-deep">
              <Link href={`/pro${querySuffix}`}>{t.navUpgrade}</Link>
            </Button>
          </div>
        </div>
      </nav>
    </header>
  );
}

export function Masthead() {
  return (
    <Suspense
      fallback={
        <header className="border-b border-ink bg-paper">
          <div className="mx-auto max-w-6xl px-4 py-6 md:px-6 text-center">
            <span className="font-display text-4xl font-semibold">Matchday Ledger</span>
          </div>
        </header>
      }
    >
      <MastheadContent />
    </Suspense>
  );
}