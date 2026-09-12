"use client";

import { Suspense, useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

const LANGUAGES = [
  { code: "en", label: "EN" },
  { code: "it", label: "IT" },
  { code: "es", label: "ES" },
  { code: "de", label: "DE" },
  { code: "fr", label: "FR" },
];

function LanguageSelectorContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentLang = searchParams?.get("lang") || "en";

  useEffect(() => {
    const explicitLang = searchParams?.get("lang");
    if (!explicitLang && typeof window !== "undefined") {
      const savedLang = localStorage.getItem("preferred_lang");
      if (savedLang && LANGUAGES.some((l) => l.code === savedLang) && savedLang !== "en") {
        const params = new URLSearchParams(searchParams?.toString() || "");
        params.set("lang", savedLang);
        router.replace(`${pathname}?${params.toString()}`);
        return;
      }
      if (window.navigator?.language) {
        const sysLang = window.navigator.language.split("-")[0].toLowerCase();
        if (LANGUAGES.some((l) => l.code === sysLang) && sysLang !== "en") {
          const params = new URLSearchParams(searchParams?.toString() || "");
          params.set("lang", sysLang);
          router.replace(`${pathname}?${params.toString()}`);
        }
      }
    }
  }, [searchParams, pathname, router]);

  function handleSelect(code: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("preferred_lang", code);
    }
    const params = new URLSearchParams(searchParams?.toString() || "");
    if (code === "en") {
      params.delete("lang");
    } else {
      params.set("lang", code);
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    router.push(`${pathname}${query}`);
  }

  return (
    <div
      translate="no"
      className="notranslate flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider text-ink-faint"
      aria-label="Language selector"
    >
      <span className="hidden sm:inline text-ink-faint">Lang:</span>
      <div className="flex items-center rounded border border-rule bg-paper">
        {LANGUAGES.map((l) => {
          const isActive = currentLang === l.code;
          return (
            <button
              key={l.code}
              type="button"
              translate="no"
              onClick={() => handleSelect(l.code)}
              className={`notranslate px-1.5 py-0.5 transition-colors cursor-pointer ${
                isActive
                  ? "bg-ink font-semibold text-paper"
                  : "text-ink-soft hover:bg-rule/40 hover:text-ink"
              }`}
            >
              {l.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function LanguageSelector() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider text-ink-faint">
          <span className="hidden sm:inline text-ink-faint">Lang:</span>
          <div className="flex items-center rounded border border-rule bg-paper">
            <span className="px-1.5 py-0.5 bg-ink font-semibold text-paper">EN</span>
          </div>
        </div>
      }
    >
      <LanguageSelectorContent />
    </Suspense>
  );
}
