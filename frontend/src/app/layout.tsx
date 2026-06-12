import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import { Radar } from "lucide-react";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "BidSense — AI Bid & Proposal Response Engine",
  description:
    "Ingest RFPs, extract requirements, match capabilities, score win probability, draft compliant proposals.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen font-sans antialiased">
        <header className="sticky top-0 z-40 border-b border-ink-700/60 bg-ink-950/80 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-600/20 ring-1 ring-accent-500/40">
                <Radar className="h-4.5 w-4.5 text-accent-400" />
              </span>
              <span className="text-[15px] font-semibold tracking-tight text-slate-100">
                BidSense
                <span className="ml-2 rounded-full bg-ink-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                  Bid &amp; Proposal Engine
                </span>
              </span>
            </Link>
            <nav className="flex items-center gap-1 text-sm">
              <Link href="/" className="rounded-md px-3 py-1.5 text-slate-300 hover:bg-ink-800 hover:text-white">
                Workspaces
              </Link>
              <Link href="/validation" className="rounded-md px-3 py-1.5 text-slate-300 hover:bg-ink-800 hover:text-white">
                Validation
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
