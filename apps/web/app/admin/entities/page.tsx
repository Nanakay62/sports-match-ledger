import type { Metadata } from "next";
import { Plus, Search, Tag, Users } from "lucide-react";
import { fetchAdminEntities } from "@/lib/api";

export const metadata: Metadata = {
  title: "Entity Corrections & Graph · Editorial Control Plane",
};

export default async function AdminEntitiesPage() {
  const entities = await fetchAdminEntities();

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          <Users className="size-3.5 text-ledger" />
          <span>Multilingual Knowledge Base · Handbook §15</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          Entity Graph & Alias Curation
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          Maintain canonical entity resolution. Prevent translation drift, enforce localized club
          glossaries, and resolve international reporter bylines.
        </p>
      </header>

      <section className="mt-8" aria-label="Canonical entity list">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          <span>{entities.length} canonical entities on file</span>
          <span>Exact & normalized alias matching</span>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {entities.map((ent) => (
            <div
              key={ent.id}
              className="border border-rule bg-paper p-5 transition-colors hover:border-ink"
            >
              <div className="flex items-center justify-between border-b border-rule/60 pb-2">
                <div>
                  <h2 className="font-display text-lg font-medium">{ent.name}</h2>
                  <span className="font-mono text-[10.5px] text-ink-faint">ID: {ent.id}</span>
                </div>
                <span className="rounded bg-rule px-2 py-0.5 font-mono text-[11px] uppercase font-semibold text-ink-soft">
                  {ent.type}
                </span>
              </div>

              {/* Aliases */}
              <div className="mt-3">
                <div className="font-mono text-[10.5px] uppercase tracking-wider text-ink-faint">
                  Known Aliases ({ent.aliases?.length || 0})
                </div>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {(ent.aliases || []).map((alias: string) => (
                    <span
                      key={alias}
                      className="inline-flex items-center gap-1 rounded border border-rule-strong bg-rule/30 px-2 py-0.5 font-mono text-[11px] text-ink"
                    >
                      <Tag className="size-2.5 text-ink-faint" />
                      {alias}
                    </span>
                  ))}
                </div>
              </div>

              {/* Localized Translations */}
              {ent.localized_names && Object.keys(ent.localized_names).length > 0 && (
                <div className="mt-4 border-t border-rule/60 pt-2">
                  <div className="font-mono text-[10.5px] uppercase tracking-wider text-ink-faint">
                    Canonical Glossary Variants
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-2 text-[12px]">
                    {Object.entries(ent.localized_names).map(([lang, locName]) => (
                      <span key={lang} className="font-mono text-[11px] text-ink-soft">
                        <strong className="text-ink uppercase">{lang}:</strong> {String(locName)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
