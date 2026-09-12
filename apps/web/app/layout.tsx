import type { Metadata } from "next";
import { Archivo, Fraunces, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { Masthead } from "@/components/masthead";
import { SiteFooter } from "@/components/site-footer";

const display = Fraunces({ subsets: ["latin"], variable: "--font-fraunces", style: ["normal", "italic"] });
const sans = Archivo({ subsets: ["latin"], variable: "--font-archivo" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-plex-mono" });

export const metadata: Metadata = {
  title: { default: "Matchday Ledger: every claim on record", template: "%s · Matchday Ledger" },
  description:
    "An accountability ledger for transfer reporting: every rumour tracked to its outcome, every source scored in public. Statuses are always free.",
  other: {
    google: "notranslate",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      translate="no"
      suppressHydrationWarning
      className={`notranslate ${display.variable} ${sans.variable} ${mono.variable}`}
    >
      <body className="flex min-h-screen flex-col" suppressHydrationWarning>
        <Masthead />
        <div className="flex-1">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}